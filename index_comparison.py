"""Global Stock Indices — Log Return Visualizer.

Compares cumulative log returns of major world equity indices (plus Bitcoin as a
cross-asset benchmark) over an arbitrary date window, ranked best to worst.

Why log returns: they are additive over time, so a cumulative sum is a true
compounded path, and they make up/down moves symmetric. The chart plots the
cumulative log return; the percentages quoted in labels are converted back to
simple returns via exp(x) - 1, which is what a reader actually recognises.

Important caveat: every index is quoted in its own local currency, so this
measures LOCAL-CURRENCY performance, not the return to a single foreign
investor. A market can lead this chart while a falling currency wipes out the
gain in USD terms. Pass --currency-note to stamp that on the figure.

Usage:
    python index_comparison.py
    python index_comparison.py --start 2026-01-01 --end 2026-11-10
    python index_comparison.py --period ytd --out chart.png --theme light
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

try:
    import yfinance as yf
except ImportError:  # pragma: no cover - dependency guard
    sys.exit("yfinance is not installed. Run: pip install -r requirements.txt")


# --------------------------------------------------------------------------
# Universe
# --------------------------------------------------------------------------
# Each entry is display name -> (Yahoo Finance ticker, region).
# Region drives the colour/line-style encoding, so it is data, not decoration.
#
# Deliberately excluded, do not re-add without changing the data source:
#   MOEX Index (Russia) 'IMOEX.ME'  — Yahoo stopped serving this after the 2022
#       sanctions ("possibly delisted; no price data found").
#   Tadawul All Shares (Saudi) '^TASI.SR' — same symptom, returns zero rows for
#       every window tested. Needs the Tadawul site or another vendor.
# Both would otherwise fail silently into the "failed" list on every run.
INDICES: dict[str, tuple[str, str]] = {
    # Americas
    "S&P 500 (USA)": ("^GSPC", "Americas"),
    "Nasdaq Composite (USA)": ("^IXIC", "Americas"),
    "Dow Jones (USA)": ("^DJI", "Americas"),
    "TSX Composite (Canada)": ("^GSPTSE", "Americas"),
    "Bovespa (Brazil)": ("^BVSP", "Americas"),
    "IPC (Mexico)": ("^MXX", "Americas"),
    # Europe
    "DAX 40 (Germany)": ("^GDAXI", "Europe"),
    "FTSE 100 (UK)": ("^FTSE", "Europe"),
    "CAC 40 (France)": ("^FCHI", "Europe"),
    "Euro Stoxx 50 (Eurozone)": ("^STOXX50E", "Europe"),
    "SMI (Switzerland)": ("^SSMI", "Europe"),
    "IBEX 35 (Spain)": ("^IBEX", "Europe"),
    # Asia
    "Nifty 50 (India)": ("^NSEI", "Asia"),
    "Hang Seng (Hong Kong)": ("^HSI", "Asia"),
    "SSE Composite (China)": ("000001.SS", "Asia"),
    "Nikkei 225 (Japan)": ("^N225", "Asia"),
    "KOSPI (South Korea)": ("^KS11", "Asia"),
    "TAIEX (Taiwan)": ("^TWII", "Asia"),
    "Jakarta Composite (Indonesia)": ("^JKSE", "Asia"),
    "STI (Singapore)": ("^STI", "Asia"),
    "FTSE Bursa KLCI (Malaysia)": ("^KLSE", "Asia"),
    # Oceania
    "ASX 200 (Australia)": ("^AXJO", "Oceania"),
    # Crypto benchmark
    "BTC/USD (Bitcoin)": ("BTC-USD", "Crypto"),
}

REGION_ORDER = ["Americas", "Europe", "Asia", "Oceania", "Crypto"]

# Composite encoding: hue x line style.
#
# Five regions is one class more than colour alone can carry safely. The three
# hues below are the only trio that clears the all-pairs colour-vision gate in
# both themes (worst-case CVD delta-E 9.4 dark / 9.2 light, normal-vision 20.9 /
# 24.0); adding a 4th or 5th hue drops some pair to delta-E ~1.9, i.e.
# indistinguishable to a protanope. So region 4 and 5 reuse hues and separate by
# dash pattern instead. The encoding therefore survives colourblindness and
# black-and-white printing, which a 5-hue palette would not.
REGION_STYLE: dict[str, tuple[str, tuple]] = {
    #              hue key      (dash pattern: solid)
    "Americas": ("blue", ()),
    "Europe": ("orange", ()),
    "Asia": ("aqua", ()),
    "Oceania": ("blue", (6, 2)),
    "Crypto": ("orange", (1, 1.6)),
}

THEMES = {
    "dark": {
        "surface": "#15161a",
        "ink": "#f0efec",
        "ink_soft": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "hues": {"blue": "#3987e5", "orange": "#d95926", "aqua": "#199e70"},
    },
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink_soft": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "hues": {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a"},
    },
}


@dataclass
class Series:
    """One index's cumulative log-return path."""

    name: str
    ticker: str
    region: str
    index: object  # DatetimeIndex
    cum_log: np.ndarray  # cumulative log return, in log units

    @property
    def final_log(self) -> float:
        return float(self.cum_log[-1])

    @property
    def pct(self) -> float:
        """Total simple return, in percent."""
        return (np.exp(self.final_log) - 1.0) * 100.0


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def _parse_date(value: str, flag: str) -> date:
    """Parse YYYY-MM-DD, or fail immediately with a useful message.

    Without this, a typo'd date reaches yfinance and every ticker fails
    separately with an opaque ValueError after a pointless round of requests.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"{flag}: expected a date as YYYY-MM-DD, got {value!r}")


def resolve_window(args) -> tuple[str, str]:
    """Turn --period / --start / --end into a concrete (start, end) pair."""
    end = args.end or date.today().strftime("%Y-%m-%d")
    end_dt = _parse_date(end, "--end")

    if args.start:
        start_dt = _parse_date(args.start, "--start")
        if start_dt >= end_dt:
            raise SystemExit(
                f"--start ({args.start}) must be before --end ({end}).")
        return args.start, end

    periods = {
        "1m": lambda: end_dt - timedelta(days=31),
        "3m": lambda: end_dt - timedelta(days=92),
        "6m": lambda: end_dt - timedelta(days=183),
        "1y": lambda: end_dt - timedelta(days=365),
        "ytd": lambda: date(end_dt.year, 1, 1),
    }
    start_dt = periods[args.period]()
    # "ytd" on an early-January --end collapses to a zero-length window, which
    # would otherwise cost 23 pointless requests before failing on every ticker.
    if start_dt >= end_dt:
        raise SystemExit(
            f"--period {args.period} with --end {end} gives an empty window "
            f"({start_dt} to {end}). Pick a longer period or a later --end.")
    return start_dt.strftime("%Y-%m-%d"), end


def fetch(indices, start, end, quiet=False):
    """Download each ticker; return (list[Series], list[(name, ticker, reason)])."""
    out, failed = [], []
    total = len(indices)
    for i, (name, (ticker, region)) in enumerate(indices.items(), 1):
        if not quiet:
            print(f"  [{i:>2}/{total}] {name:<32} {ticker:<12}", end="", flush=True)
        try:
            df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
        except Exception as exc:  # network / parse / symbol errors
            failed.append((name, ticker, type(exc).__name__))
            if not quiet:
                print("  error")
            continue

        close = df["Close"].dropna() if "Close" in df else None
        if close is None or len(close) < 2:
            failed.append((name, ticker, "no price data"))
            if not quiet:
                print("  no data")
            continue

        # log(P_t / P_{t-1}), first day anchored at 0, then compounded.
        log_ret = np.log(close / close.shift(1)).fillna(0.0).cumsum()
        out.append(
            Series(name=name, ticker=ticker, region=region,
                   index=log_ret.index, cum_log=log_ret.to_numpy(dtype=float))
        )
        if not quiet:
            print(f"  {len(close):>4} bars")
    return out, failed


# --------------------------------------------------------------------------
# Label placement
# --------------------------------------------------------------------------
def declutter(values, min_gap):
    """Nudge labels apart while keeping their original order.

    Two passes: push up from the bottom, then pull down anything shoved past the
    top. Returns positions whose span is clamped to the data range where
    possible, so labels stay beside the plot rather than drifting off it.
    """
    order = np.argsort(values)
    placed = np.array(values, dtype=float)

    # Upward pass.
    for i in range(1, len(order)):
        cur, prev = order[i], order[i - 1]
        if placed[cur] - placed[prev] < min_gap:
            placed[cur] = placed[prev] + min_gap

    # If the stack overshot the top, pull the whole tail back down.
    if len(order) == 0:
        return placed

    top = placed[order[-1]]
    ceiling = max(values) + min_gap * 1.5
    if top > ceiling:
        shift = top - ceiling
        for i in range(len(order) - 1, -1, -1):
            idx = order[i]
            placed[idx] -= shift
            if i > 0 and placed[idx] - placed[order[i - 1]] >= min_gap:
                break
            shift = min_gap - (placed[idx] - placed[order[i - 1]]) if i > 0 else shift
            shift = max(shift, 0)
    return placed


# --------------------------------------------------------------------------
# Plot
# --------------------------------------------------------------------------
def print_table(ranked):
    """The table view: every value, in rank order.

    The chart deliberately labels only the extremes, so this is where the rest
    of the numbers live — and it keeps the output readable without colour.
    """
    width = max(len(s.name) for s in ranked)
    print(f"\n{'#':>3}  {'Market':<{width}}  {'Region':<9}  {'Return':>9}")
    print(f"{'-' * 3}  {'-' * width}  {'-' * 9}  {'-' * 9}")
    for i, s in enumerate(ranked, 1):
        print(f"{i:>3}  {s.name:<{width}}  {s.region:<9}  {s.pct:>+8.2f}%")


def plot(series, start, end, theme="dark", out=None, show=True,
         currency_note=False, title=None, n_label=3):
    if not series:
        print("No data fetched — nothing to plot.")
        return

    t = THEMES[theme]
    ranked = sorted(series, key=lambda s: s.final_log, reverse=True)

    fig, ax = plt.subplots(figsize=(15, 9), facecolor=t["surface"])
    ax.set_facecolor(t["surface"])

    best, worst = ranked[0], ranked[-1]

    # --- lines ------------------------------------------------------------
    for s in ranked:
        hue_key, dashes = REGION_STYLE[s.region]
        colour = t["hues"][hue_key]
        extreme = s is best or s is worst
        line, = ax.plot(
            s.index, s.cum_log * 100.0,
            color=colour,
            linewidth=2.2 if extreme else 1.4,
            alpha=1.0 if extreme else 0.72,
            solid_capstyle="round",
            zorder=3 if extreme else 2,
        )
        if dashes:
            line.set_dashes(dashes)

    ax.axhline(0, color=t["axis"], linewidth=1.0, zorder=1)

    # --- end labels -------------------------------------------------------
    # Label only the leaders and laggards. With 23 markets, most finish within a
    # few percent of each other, so direct-labelling all of them produces a wall
    # of text with crossing leader lines that cannot be traced back to a line.
    # The full ranking goes to the printed table instead (see print_table).
    finals = np.array([s.final_log * 100.0 for s in ranked])
    labelled_idx = sorted(set(list(range(n_label)) +
                             list(range(len(ranked) - n_label, len(ranked)))))
    # n_label=0 is a valid request for a chart with no end labels at all, so an
    # empty selection has to be a no-op rather than an error.
    sel = [i for i in labelled_idx if 0 <= i < len(ranked)]

    span = finals.max() - finals.min()
    gap = max(span * 0.040, 0.5)
    placed = declutter(finals[sel], gap) if sel else []
    last_x = max(s.index[-1] for s in ranked)

    for i, y in zip(sel, placed):
        s = ranked[i]
        hue_key, _ = REGION_STYLE[s.region]
        colour = t["hues"][hue_key]
        extreme = s is best or s is worst
        ax.annotate(
            f"{s.name}  {s.pct:+.1f}%",
            xy=(last_x, finals[i]), xycoords="data",
            xytext=(14, y), textcoords=("offset points", "data"),
            va="center", ha="left",
            fontsize=9.0 if extreme else 8.2,
            color=t["ink"] if extreme else t["ink_soft"],
            fontweight="bold" if extreme else "normal",
            annotation_clip=False,
            arrowprops=dict(arrowstyle="-", color=colour,
                            lw=0.8, alpha=0.7, shrinkA=0, shrinkB=3),
        )

    # --- peak annotation --------------------------------------------------
    # The highest point on the chart draws the eye before anything else. If it
    # belongs to a line whose endpoint sits far below it, the reader has no way
    # to identify it, so name it where it peaks.
    peak = max(ranked, key=lambda s: s.cum_log.max())
    pk_i = int(np.argmax(peak.cum_log))
    pk_y = peak.cum_log[pk_i] * 100.0
    # Only worth annotating if the peak is well clear of where the line ends.
    if pk_y - peak.final_log * 100.0 > span * 0.12:
        hue_key, _ = REGION_STYLE[peak.region]
        ax.annotate(
            f"{peak.name.split(' (')[0]} peaked "
            f"{(np.exp(peak.cum_log[pk_i]) - 1) * 100:+.0f}%",
            xy=(peak.index[pk_i], pk_y),
            xytext=(14, 2), textcoords="offset points",
            ha="left", va="center", fontsize=8.2, color=t["muted"],
            arrowprops=dict(arrowstyle="-", color=t["hues"][hue_key],
                            lw=0.7, alpha=0.6, shrinkA=0, shrinkB=3),
        )

    # --- axes -------------------------------------------------------------
    locator = mdates.AutoDateLocator(minticks=4, maxticks=9)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))

    ax.grid(True, axis="y", color=t["grid"], linewidth=0.8, alpha=1.0)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(t["axis"])
    ax.tick_params(colors=t["muted"], labelsize=9, length=0)

    # The axis is in log units x100; the end labels quote simple returns
    # (exp(x)-1), which diverge from it as magnitude grows. Say so, so the two
    # numbers are never read as the same scale.
    ax.set_ylabel("Cumulative log return  (log units x 100)",
                  fontsize=10, color=t["ink_soft"], labelpad=10)

    # --- titles -----------------------------------------------------------
    fig.text(0.055, 0.955, title or "Cumulative Log Returns — Global Indices",
             fontsize=17, color=t["ink"], fontweight="semibold", va="bottom")
    sub = (f"{start} to {end}   ·   {len(ranked)} markets   ·   "
           f"best {best.pct:+.1f}% {best.name.split(' (')[0]}   ·   "
           f"worst {worst.pct:+.1f}% {worst.name.split(' (')[0]}")
    fig.text(0.055, 0.925, sub, fontsize=9.5, color=t["muted"], va="bottom")

    if currency_note:
        fig.text(0.055, 0.025,
                 "Each index is in its own local currency — this is local-currency "
                 "performance, not the return to a single foreign investor.",
                 fontsize=8, color=t["muted"], va="bottom", style="italic")

    # --- region key -------------------------------------------------------
    present = [r for r in REGION_ORDER if any(s.region == r for s in ranked)]
    handles = []
    for r in present:
        hue_key, dashes = REGION_STYLE[r]
        h = Line2D([], [], color=t["hues"][hue_key], linewidth=2.0,
                   label=r, solid_capstyle="round")
        if dashes:
            h.set_dashes(dashes)
        handles.append(h)
    # Placed above the plot, in a single row, so it never covers the data.
    legend = ax.legend(
        handles=handles, loc="lower left", bbox_to_anchor=(0.0, 1.005),
        frameon=False, fontsize=9, labelcolor=t["ink_soft"],
        handlelength=2.4, borderpad=0.0, columnspacing=1.8,
        ncol=len(handles),
    )
    legend.set_zorder(5)

    fig.subplots_adjust(left=0.055, right=0.775, top=0.855, bottom=0.085)

    if out:
        fig.savefig(out, dpi=120, facecolor=t["surface"])
        print(f"\nSaved chart -> {out}")
    if show:
        plt.show()
    else:
        plt.close(fig)


# --------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Compare cumulative log returns of global stock indices.")
    p.add_argument("--start", help="start date YYYY-MM-DD (overrides --period)")
    p.add_argument("--end", help="end date YYYY-MM-DD (default: today)")
    p.add_argument("--period", default="ytd",
                   choices=["1m", "3m", "6m", "1y", "ytd"],
                   help="window relative to --end (default: ytd)")
    p.add_argument("--theme", default="dark", choices=["dark", "light"])
    p.add_argument("--out", help="save the chart to this path (e.g. chart.png)")
    p.add_argument("--no-show", action="store_true",
                   help="don't open a window (useful with --out on a server)")
    p.add_argument("--currency-note", action="store_true",
                   help="stamp the local-currency caveat on the figure")
    p.add_argument("--title", help="override the chart title")
    p.add_argument("--label-count", type=int, default=3, metavar="N",
                   help="direct-label the top and bottom N markets (default: 3)")
    p.add_argument("--no-table", action="store_true",
                   help="skip the ranked table printed after the chart")
    p.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = p.parse_args(argv)

    if args.no_show:
        matplotlib.use("Agg")

    if args.label_count < 0:
        raise SystemExit("--label-count must be 0 or greater.")

    start, end = resolve_window(args)
    if not args.quiet:
        print(f"Fetching {len(INDICES)} tickers  ({start} -> {end})")

    series, failed = fetch(INDICES, start, end, quiet=args.quiet)

    if not args.quiet and series:
        print(f"\nFetched {len(series)} of {len(INDICES)}.")

    if series and not args.no_table:
        print_table(sorted(series, key=lambda s: s.final_log, reverse=True))

    plot(series, start, end, theme=args.theme, out=args.out,
         show=not args.no_show, currency_note=args.currency_note,
         title=args.title, n_label=args.label_count)

    if failed:
        print("\nFailed to fetch:")
        for name, ticker, reason in failed:
            print(f"  - {name} ({ticker}): {reason}")
    return 0 if series else 1


if __name__ == "__main__":
    raise SystemExit(main())
