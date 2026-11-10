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
# Each entry is display name -> (Yahoo Finance ticker, region, quote currency).
# Region drives the colour/line-style encoding, so it is data, not decoration.
# Currency drives --usd conversion; every value below was confirmed against the
# `currency` field Yahoo reports for that ticker, not assumed from the country.
#
# Deliberately excluded, do not re-add without changing the data source:
#   MOEX Index (Russia) 'IMOEX.ME'  — Yahoo stopped serving this after the 2022
#       sanctions ("possibly delisted; no price data found").
#   Tadawul All Shares (Saudi) '^TASI.SR' — same symptom, returns zero rows for
#       every window tested. Needs the Tadawul site or another vendor.
# Both would otherwise fail silently into the "failed" list on every run.
# The fourth field is a tier: 1 = the twenty headline indices a global market
# report would always carry, 2 = the next ten, 3 = everything else. Tiers are
# curated by market significance, deliberately NOT by performance in the window:
# "Top 20" must mean the same set every run, or two runs cannot be compared.
# Every ticker here was confirmed to return data; see EXCLUDED below for the
# ones that did not.
INDICES: dict[str, tuple[str, str, str, int]] = {
    # --- Americas ---------------------------------------------------------
    "S&P 500 (USA)": ("^GSPC", "Americas", "USD", 1),
    "Nasdaq Composite (USA)": ("^IXIC", "Americas", "USD", 1),
    "Dow Jones (USA)": ("^DJI", "Americas", "USD", 1),
    "Russell 2000 (USA)": ("^RUT", "Americas", "USD", 2),
    "S&P MidCap 400 (USA)": ("^SP400", "Americas", "USD", 3),
    "NYSE Composite (USA)": ("^NYA", "Americas", "USD", 3),
    "TSX Composite (Canada)": ("^GSPTSE", "Americas", "CAD", 1),
    "Bovespa (Brazil)": ("^BVSP", "Americas", "BRL", 1),
    "IPC (Mexico)": ("^MXX", "Americas", "MXN", 2),
    # --- Europe -----------------------------------------------------------
    "DAX 40 (Germany)": ("^GDAXI", "Europe", "EUR", 1),
    "FTSE 100 (UK)": ("^FTSE", "Europe", "GBP", 1),
    "CAC 40 (France)": ("^FCHI", "Europe", "EUR", 1),
    "Euro Stoxx 50 (Eurozone)": ("^STOXX50E", "Europe", "EUR", 1),
    "STOXX Europe 600": ("^STOXX", "Europe", "EUR", 1),
    "SMI (Switzerland)": ("^SSMI", "Europe", "CHF", 1),
    "IBEX 35 (Spain)": ("^IBEX", "Europe", "EUR", 2),
    "FTSE MIB (Italy)": ("FTSEMIB.MI", "Europe", "EUR", 2),
    "AEX (Netherlands)": ("^AEX", "Europe", "EUR", 2),
    "BEL 20 (Belgium)": ("^BFX", "Europe", "EUR", 3),
    "OMX Stockholm 30 (Sweden)": ("^OMX", "Europe", "SEK", 3),
    "OMX Copenhagen 25 (Denmark)": ("^OMXC25", "Europe", "DKK", 3),
    "OMX Helsinki 25 (Finland)": ("^OMXH25", "Europe", "EUR", 3),
    "ATX (Austria)": ("^ATX", "Europe", "EUR", 3),
    "PSI (Portugal)": ("^BVLG", "Europe", "EUR", 3),
    "Athex Composite (Greece)": ("GD.AT", "Europe", "EUR", 3),
    "BIST 100 (Turkey)": ("XU100.IS", "Europe", "TRY", 3),
    # --- Asia -------------------------------------------------------------
    "Nikkei 225 (Japan)": ("^N225", "Asia", "JPY", 1),
    "SSE Composite (China)": ("000001.SS", "Asia", "CNY", 1),
    "Shenzhen Component (China)": ("399001.SZ", "Asia", "CNY", 2),
    "Hang Seng (Hong Kong)": ("^HSI", "Asia", "HKD", 1),
    "Hang Seng China Ent (HK)": ("^HSCE", "Asia", "HKD", 2),
    "Nifty 50 (India)": ("^NSEI", "Asia", "INR", 1),
    "BSE Sensex (India)": ("^BSESN", "Asia", "INR", 1),
    "Nifty 100 (India)": ("^CNX100", "Asia", "INR", 3),
    "Nifty Bank (India)": ("^NSEBANK", "Asia", "INR", 3),
    "KOSPI (South Korea)": ("^KS11", "Asia", "KRW", 1),
    "KOSDAQ (South Korea)": ("^KQ11", "Asia", "KRW", 3),
    "TAIEX (Taiwan)": ("^TWII", "Asia", "TWD", 1),
    "STI (Singapore)": ("^STI", "Asia", "SGD", 2),
    "Jakarta Composite (Indonesia)": ("^JKSE", "Asia", "IDR", 2),
    "FTSE Bursa KLCI (Malaysia)": ("^KLSE", "Asia", "MYR", 3),
    "TA-125 (Israel)": ("^TA125.TA", "Asia", "ILS", 3),
    # --- Oceania ----------------------------------------------------------
    "ASX 200 (Australia)": ("^AXJO", "Oceania", "AUD", 1),
    "NZX 50 (New Zealand)": ("^NZ50", "Oceania", "NZD", 3),
    # --- Africa -----------------------------------------------------------
    "JSE Top 40 (South Africa)": ("^JN0U.JO", "Africa", "USD", 2),
    # --- Crypto benchmarks — already quoted in USD ------------------------
    "BTC/USD (Bitcoin)": ("BTC-USD", "Crypto", "USD", 1),
    "ETH/USD (Ethereum)": ("ETH-USD", "Crypto", "USD", 3),
}

# Tried and rejected: Yahoo returns no rows for these over any window tested.
# Kept as a record so they are not re-added on a hunch.
#   IMOEX.ME (MOEX, Russia)        — delisted from Yahoo after 2022 sanctions
#   ^TASI.SR / ^TASI (Tadawul)     — zero rows
#   000300.SS (CSI 300, China)     — zero rows; ^SSE/Shenzhen cover China
#   ^TOPX / ^TOPIX (Japan)         — zero rows. The 1306.T ETF proxy returns
#       data but carries an unadjusted 10:1 reverse split (36.4 -> 381.9
#       overnight, reported as +948%), so it is rejected by the split guard.
#   ^SET.BK (Thailand), PSEI.PS (Philippines), ^VNINDEX (Vietnam)
#   ^WIG20 / WIG20.WA (Poland), ^BUX (Hungary), PX.PR (Czechia)
#   ^OSEAX (Norway), ^IPSA (Chile), ^COLCAP (Colombia)
#   ^CASE30 (Egypt), ^DFMGI (UAE), ^QSI (Qatar)
#   ^MERV (Argentina)              — only 64 rows and no currency reported

REGION_ORDER = ["Americas", "Europe", "Asia", "Oceania", "Africa", "Crypto"]

# Selection presets. Tier 1 is twenty indices, tier 1+2 is thirty, and "all" is
# everything that resolves — which is what the menu offers.
SELECTIONS = {
    "top20": ("Top 20 across regions", lambda t: t <= 1),
    "top30": ("Top 30 across regions", lambda t: t <= 2),
    "all": ("All major indices", lambda t: True),
}

# Yahoo FX convention: "XXXUSD=X" quotes 1 XXX in USD, so converting a
# local-currency level to USD is a multiplication. USD needs no pair.
FX_SUFFIX = "USD=X"

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
    "Africa": ("aqua", (6, 2)),
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
        # Light -> dark steps of each region hue, for telling individual
        # indices apart inside a region panel. Each trio validates as an
        # ordinal ramp against this surface (monotone lightness, visible step
        # gaps, dark end still clearing the surface).
        "ramps": {
            "blue": ["#9ec5f4", "#3987e5", "#184f95"],
            "orange": ["#f5b394", "#d95926", "#8a3514"],
            "aqua": ["#7fdcb8", "#199e70", "#0a5436"],
        },
    },
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink_soft": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "hues": {"blue": "#2a78d6", "orange": "#eb6834", "aqua": "#1baf7a"},
        "ramps": {
            "blue": ["#6da7ec", "#2a78d6", "#184f95"],
            "orange": ["#e07a4a", "#c44a1c", "#8a3514"],
            "aqua": ["#36c08a", "#149066", "#0a5a3d"],
        },
    },
}

# Within a region panel, each index gets its own (lightness step, dash) pair.
# Two channels rather than one: 3 steps x 3 dashes = 9 styles, which covers the
# largest region, and a reader who cannot separate the lightness steps can still
# separate solid from dashed from dotted.
PANEL_DASHES = [(), (5, 2), (1, 1.6)]


def panel_style(rank: int, ramp: list[str]) -> tuple[str, tuple]:
    """Colour + dash for the rank-th index inside a region panel."""
    return ramp[rank % len(ramp)], PANEL_DASHES[(rank // len(ramp)) % 3]


@dataclass
class Series:
    """One index's cumulative log-return path."""

    name: str
    ticker: str
    region: str
    index: object  # DatetimeIndex
    cum_log: np.ndarray  # cumulative log return, in log units
    currency: str = "USD"  # the currency this path is measured in

    @property
    def final_log(self) -> float:
        return float(self.cum_log[-1])

    @property
    def pct(self) -> float:
        """Total simple return, in percent."""
        return (np.exp(self.final_log) - 1.0) * 100.0

    @property
    def daily_log(self) -> np.ndarray:
        """Day-over-day log returns (day 1 anchored at 0)."""
        return np.diff(self.cum_log, prepend=0.0)

    @property
    def vol(self) -> float:
        """Annualised volatility, in percent.

        Standard deviation of daily log returns scaled by sqrt(252). This is a
        comparability aid, not a risk model: it assumes roughly 252 trading days
        and says nothing about fat tails.
        """
        d = self.daily_log
        if len(d) < 3:
            return float("nan")
        return float(d.std(ddof=1) * np.sqrt(252) * 100.0)

    @property
    def max_drawdown(self) -> float:
        """Worst peak-to-trough fall over the window, in percent (negative)."""
        level = np.exp(self.cum_log)
        peak = np.maximum.accumulate(level)
        return float((level / peak - 1.0).min() * 100.0)

    @property
    def return_per_vol(self) -> float:
        """Total return divided by annualised volatility.

        A crude risk-adjusted ranking: how much return each unit of wobble
        bought. Not a Sharpe ratio — there is no risk-free rate here.
        """
        v = self.vol
        if not np.isfinite(v) or v == 0:
            return float("nan")
        return self.pct / v

    @property
    def bars(self) -> int:
        return len(self.cum_log)


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


# A single-day move this large is not a market move. Broad indices do not gain
# or lose two thirds of their value overnight; in practice it means a split or
# redenomination that auto_adjust did not back out, and the fake jump then
# poisons volatility, drawdown and the whole cumulative path.
# (Found with 1306.T, which jumped 36.4 -> 381.9 on an unadjusted 10:1 reverse
# split — reported as +948% in a day.)
MAX_DAILY_LOG_MOVE = 0.60  # ~ -45% to +82% in one session


def _close_series(ticker, start, end):
    """Fetch one ticker's adjusted close. Returns (series, None) or (None, reason)."""
    try:
        df = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True)
    except Exception as exc:  # network / parse / symbol errors
        return None, type(exc).__name__
    close = df["Close"].dropna() if "Close" in df else None
    if close is None or len(close) < 2:
        return None, "no price data"

    moves = np.abs(np.diff(np.log(close.to_numpy(dtype=float))))
    if moves.size and moves.max() > MAX_DAILY_LOG_MOVE:
        pct = (np.exp(moves.max()) - 1) * 100
        return None, f"unadjusted split? {pct:+.0f}% in one day"
    return close, None


def fetch_fx(currencies, start, end, quiet=False):
    """Fetch USD conversion rates. Returns ({currency: series}, [(cur, reason)]).

    Yahoo quotes these as "1 unit of XXX = N USD", so a local price level is
    converted by multiplying. USD maps to None and is never fetched.
    """
    rates, failed = {}, []
    needed = sorted(c for c in set(currencies) if c != "USD")
    for i, cur in enumerate(needed, 1):
        pair = f"{cur}{FX_SUFFIX}"
        if not quiet:
            print(f"  [{i:>2}/{len(needed)}] FX {cur}->USD  {pair:<12}",
                  end="", flush=True)
        close, reason = _close_series(pair, start, end)
        if close is None:
            failed.append((cur, reason))
            if not quiet:
                print(f"  {reason}")
            continue
        rates[cur] = close
        if not quiet:
            print(f"  {len(close):>4} bars")
    return rates, failed


def fetch(indices, start, end, quiet=False, to_usd=False, fx=None):
    """Download each ticker; return (list[Series], list[(name, ticker, reason)]).

    With to_usd, each index level is converted to USD *before* returns are
    computed. Converting the level is exact; summing index and FX returns
    afterwards would only approximate it, and would drift over long windows.
    """
    out, failed = [], []
    total = len(indices)
    fx = fx or {}
    for i, (name, (ticker, region, currency, _tier)) in enumerate(
            indices.items(), 1):
        if not quiet:
            print(f"  [{i:>2}/{total}] {name:<32} {ticker:<12}", end="", flush=True)

        close, reason = _close_series(ticker, start, end)
        if close is None:
            failed.append((name, ticker, reason))
            if not quiet:
                print(f"  {reason}")
            continue

        measured_in = currency
        if to_usd and currency != "USD":
            rate = fx.get(currency)
            if rate is None:
                failed.append((name, ticker, f"no {currency}->USD rate"))
                if not quiet:
                    print(f"  no {currency} rate")
                continue
            # Align on the index's own trading days; FX and equity calendars
            # differ (FX trades on local market holidays and vice versa), so
            # reindex onto the price dates and carry the last known rate
            # forward. Any leading gap is dropped rather than back-filled, so a
            # rate is never invented before the first quote.
            aligned = rate.reindex(close.index.union(rate.index)).ffill()
            aligned = aligned.reindex(close.index)
            usd_close = (close * aligned).dropna()
            if len(usd_close) < 2:
                failed.append((name, ticker, f"no overlap with {currency} rate"))
                if not quiet:
                    print("  no FX overlap")
                continue
            close = usd_close
            measured_in = "USD"

        # log(P_t / P_{t-1}), first day anchored at 0, then compounded.
        log_ret = np.log(close / close.shift(1)).fillna(0.0).cumsum()
        out.append(
            Series(name=name, ticker=ticker, region=region,
                   index=log_ret.index, cum_log=log_ret.to_numpy(dtype=float),
                   currency=measured_in)
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
def _fmt(v, suffix="%", width=8, dp=2, signed=True):
    """Format a float that may be NaN, right-aligned."""
    if not np.isfinite(v):
        return f"{'n/a':>{width}}"
    sign = "+" if signed else ""
    return f"{v:>{sign}{width}.{dp}f}{suffix}"


def print_table(ranked, region_order=False):
    """The table view: every value, with the stats the chart can't show.

    The chart labels only the extremes, so this is where the rest of the numbers
    live — and it is the readable-without-colour view.

    Columns beyond return exist to answer "who is actually outperforming":
    a market can top the return ranking while taking far more risk to get there,
    which vol and drawdown expose and raw return hides.
    """
    if not ranked:
        return

    width = max(len(s.name) for s in ranked)
    basis = "USD" if all(s.currency == "USD" for s in ranked) else "local ccy"

    # Rank within each region, so "best in Europe" is readable directly.
    region_rank = {}
    for r in REGION_ORDER:
        members = [s for s in ranked if s.region == r]
        for i, s in enumerate(sorted(members, key=lambda x: x.final_log,
                                     reverse=True), 1):
            region_rank[s.name] = (i, len(members))

    head = (f"{'#':>3}  {'Market':<{width}}  {'Region':<9}  {'In-rgn':>7}  "
            f"{'Return':>9}  {'Vol':>8}  {'MaxDD':>9}  {'Ret/Vol':>8}  {'Bars':>5}")
    rule = (f"{'-' * 3}  {'-' * width}  {'-' * 9}  {'-' * 7}  "
            f"{'-' * 9}  {'-' * 8}  {'-' * 9}  {'-' * 8}  {'-' * 5}")

    def row(i, s):
        rr, rn = region_rank.get(s.name, (0, 0))
        tag = f"{rr}/{rn}" + ("*" if rr == 1 and rn > 1 else "")
        return (f"{i:>3}  {s.name:<{width}}  {s.region:<9}  {tag:>7}  "
                f"{_fmt(s.pct)}  {_fmt(s.vol, dp=1, signed=False)}  "
                f"{_fmt(s.max_drawdown)}  "
                f"{_fmt(s.return_per_vol, suffix='', dp=2)}  {s.bars:>5}")

    print(f"\nReturns measured in {basis}."
          f"  Vol = annualised stdev of daily log returns."
          f"  MaxDD = worst peak-to-trough fall.")
    print(f"Ret/Vol = return per unit of volatility (not a Sharpe ratio)."
          f"  * = best in its region.")

    # One table, every market, best to worst. The Region and In-rgn columns
    # carry the grouping, so splitting this into five tables would only make
    # the overall ranking harder to read.
    print()
    print(head)
    print(rule)
    for i, s in enumerate(ranked, 1):
        print(row(i, s))

    if region_order:
        # Compact per-region ordering, for reading a single region's ranking
        # without scanning the full list.
        print()
        for r in REGION_ORDER:
            members = sorted([s for s in ranked if s.region == r],
                             key=lambda x: x.final_log, reverse=True)
            if not members:
                continue
            order = "  >  ".join(f"{s.name.split(' (')[0]} {s.pct:+.1f}%"
                                 for s in members)
            print(f"{r:<9} {order}")

    # Region summary: the one-line answer to "which region is winning".
    print(f"\n{'REGION':<10}  {'Markets':>7}  {'Median':>9}  {'Best':>9}  "
          f"{'Leader':<28}")
    print(f"{'-' * 10}  {'-' * 7}  {'-' * 9}  {'-' * 9}  {'-' * 28}")
    rows = []
    for r in REGION_ORDER:
        members = [s for s in ranked if s.region == r]
        if not members:
            continue
        best = max(members, key=lambda x: x.final_log)
        rows.append((float(np.median([s.pct for s in members])), r,
                     len(members), best))
    for med, r, n, best in sorted(rows, reverse=True):
        print(f"{r:<10}  {n:>7}  {med:>+8.2f}%  {best.pct:>+8.2f}%  "
              f"{best.name:<28}")


def plot_by_region(series, start, end, theme="dark", out=None, show=True,
                   currency_note=False, title=None, usd=False):
    """Small multiples: one panel per region, every index individually styled.

    This is the default view. It answers "who leads inside each region", which
    23 lines on one axis cannot show; --combined gives the single-axis chart
    for "how do the regions compare".

    Each index gets its own shade and dash within its region's hue, so a curve
    can be matched to a name. Panels are scaled per region and print their own
    range, since one shared scale stretched to Asia's spread flattened the
    other regions into unreadable bands.
    """
    if not series:
        print("No data fetched — nothing to plot.")
        return

    t = THEMES[theme]
    present = [r for r in REGION_ORDER if any(s.region == r for s in series)]
    n = len(present)
    # Two columns: each panel needs a legend column beside it, which three
    # panels per row cannot fit without squeezing the plots to nothing.
    ncol = 1 if n == 1 else 2
    nrow = -(-n // ncol)  # ceil

    # Extra height for the figure header so it never lands on a panel title.
    header_in = 1.15
    # Shared x (one timeline) but independent y: a shared y-scale stretched to
    # Asia's +/-80% squashed Americas and Europe into a thin band near zero,
    # hiding the within-region detail these panels exist to show. Each panel's
    # own range is printed in its title so cross-region comparison is still
    # possible by reading, not by eyeballing equal heights.
    fig, axes = plt.subplots(nrow, ncol,
                             figsize=(16, header_in + 3.1 * nrow),
                             facecolor=t["surface"], sharex=True, sharey=False,
                             squeeze=False)
    flat = [a for row in axes for a in row]

    for ax, region in zip(flat, present):
        ax.set_facecolor(t["surface"])
        members = sorted([s for s in series if s.region == region],
                         key=lambda x: x.final_log, reverse=True)

        # Scale to this region, always including zero so the baseline means
        # the same thing in every panel.
        pv = np.concatenate([s.cum_log for s in members]) * 100.0
        lo, hi = min(pv.min(), 0.0), max(pv.max(), 0.0)
        pad = (hi - lo) * 0.12 or 1.0
        ylim = (lo - pad, hi + pad)
        hue_key, _ = REGION_STYLE[region]
        ramp = t["ramps"][hue_key]

        # Each index gets its own shade + dash within the region's hue, so a
        # curve can actually be matched to its name. The region still reads as
        # one colour family across panels.
        styles = []
        for i, s in enumerate(members):
            colour, dashes = panel_style(i, ramp)
            styles.append((colour, dashes))
            lead = i == 0
            line, = ax.plot(
                s.index, s.cum_log * 100.0, color=colour,
                linewidth=2.4 if lead else 1.5,
                alpha=1.0 if lead else 0.95,
                solid_capstyle="round", zorder=3 if lead else 2,
            )
            if dashes:
                line.set_dashes(dashes)

        ax.axhline(0, color=t["axis"], linewidth=0.9, zorder=1)
        ax.set_ylim(*ylim)

        # A real legend, not a text block: each row carries that index's own
        # colour and dash, so a curve can be matched to its name. A plain list
        # named the members but left every line looking identical.
        #
        # It sits in a reserved column to the right of the plot rather than
        # inside it. Hunting for an empty corner worked until the box grew to
        # nine rows, at which point Asia's panel had no gap big enough.
        handles = []
        for (colour, dashes), s in zip(styles, members):
            h = Line2D([], [], color=colour, linewidth=2.2,
                       solid_capstyle="round",
                       label=f"{s.name.split(' (')[0]}  {s.pct:+.1f}%")
            if dashes:
                h.set_dashes(dashes)
            handles.append(h)

        leg = ax.legend(
            handles=handles, loc="upper left", bbox_to_anchor=(1.015, 1.0),
            fontsize=7.8, labelcolor=t["ink_soft"], frameon=False,
            handlelength=2.3, handletextpad=0.6, labelspacing=0.5,
            borderpad=0.0, borderaxespad=0.0,
        )
        leg.set_zorder(5)

        # Each panel has its own y-scale, so the spread belongs in the title:
        # it is what makes two panels comparable without equal heights.
        med = float(np.median([s.pct for s in members]))
        spread = (f"   ·   best {members[0].pct:+.1f}% "
                  f"to worst {members[-1].pct:+.1f}%") if len(members) > 1 else ""
        ax.set_title(f"{region}   ·   {len(members)} market"
                     f"{'s' if len(members) != 1 else ''}   ·   "
                     f"median {med:+.1f}%{spread}",
                     fontsize=10.5, color=t["ink"], loc="left", pad=8)

        ax.grid(True, axis="y", color=t["grid"], linewidth=0.7)
        ax.set_axisbelow(True)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(t["axis"])
        ax.tick_params(colors=t["muted"], labelsize=8.5, length=0)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.0f}%"))
        loc = mdates.AutoDateLocator(minticks=3, maxticks=6)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(loc))

    # Blank out any unused cell rather than leaving empty axes.
    for ax in flat[n:]:
        ax.set_visible(False)

    # Header sits in its own reserved band, measured in inches so it holds at
    # any panel count.
    fig_h = header_in + 3.1 * nrow
    basis = "in USD" if usd else "in Local Currency"
    fig.text(0.055, 1 - 0.42 / fig_h,
             title or f"Cumulative Log Returns by Region, {basis}",
             fontsize=16, color=t["ink"], fontweight="semibold",
             va="center", ha="left")
    fig.text(0.055, 1 - 0.72 / fig_h,
             f"{start} to {end}   ·   each panel scaled to its own region "
             f"(range in the panel title)   ·   ranked best to worst",
             fontsize=9, color=t["muted"], va="center", ha="left")

    if currency_note:
        note = ("Converted to USD at daily spot rates, so returns include "
                "currency moves." if usd else
                "Each index is in its own local currency.")
        fig.text(0.055, 0.14 / fig_h, note, fontsize=8, color=t["muted"],
                 va="center", style="italic")

    # wspace leaves the gap each panel's legend column occupies.
    fig.subplots_adjust(left=0.05, right=0.84,
                        top=1 - header_in / fig_h,
                        bottom=0.42 / fig_h,
                        hspace=0.32, wspace=0.42)

    if out:
        fig.savefig(out, dpi=120, facecolor=t["surface"])
        print(f"\nSaved chart -> {out}")
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot(series, start, end, theme="dark", out=None, show=True,
         currency_note=False, title=None, n_label=3, usd=False):
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
    # The currency basis goes in the title, not a footnote: the two modes are
    # otherwise visually identical, and mistaking one for the other misreads
    # every number on the chart.
    basis = "in USD" if usd else "in Local Currency"
    # Name the actual scope: saying "Global Indices" on a chart filtered to one
    # region would misdescribe it.
    regions = [r for r in REGION_ORDER if any(s.region == r for s in ranked)]
    scope = " + ".join(regions) if len(regions) <= 2 else "Global Indices"
    fig.text(0.055, 0.955,
             title or f"Cumulative Log Returns — {scope}, {basis}",
             fontsize=17, color=t["ink"], fontweight="semibold", va="bottom")
    sub = (f"{start} to {end}   ·   {len(ranked)} markets   ·   "
           f"best {best.pct:+.1f}% {best.name.split(' (')[0]}   ·   "
           f"worst {worst.pct:+.1f}% {worst.name.split(' (')[0]}")
    fig.text(0.055, 0.925, sub, fontsize=9.5, color=t["muted"], va="bottom")

    if currency_note:
        note = ("Converted to USD at daily spot rates, so returns include "
                "currency moves — this is what a USD-based investor earned."
                if usd else
                "Each index is in its own local currency — this is local-currency "
                "performance, not the return to a single foreign investor.")
        fig.text(0.055, 0.025, note,
                 fontsize=8, color=t["muted"], va="bottom", style="italic")

    # --- region key -------------------------------------------------------
    # Only when colour is actually distinguishing something: with one region
    # every line shares a hue, so a one-entry key is noise (the title says it).
    present = [r for r in REGION_ORDER if any(s.region == r for s in ranked)]
    if len(present) > 1:
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
# Interactive mode
# --------------------------------------------------------------------------
# Running with no arguments opens a menu rather than assuming a view. Option 1
# is the quick default, so the common case is still one keypress; every other
# prompt has a default in brackets that Enter accepts.
# Plain ASCII: the Windows console defaults to cp1252, where box-drawing
# characters raise UnicodeEncodeError and crash the menu before it draws.
RULE = "-" * 64


def _ask(prompt, options, default_key):
    """Numbered menu. Returns the chosen key. Enter accepts the default."""
    print(f"\n{prompt}")
    keys = list(options)
    for i, k in enumerate(keys, 1):
        label, hint = options[k]
        mark = "  (default)" if k == default_key else ""
        print(f"  {i}. {label}{mark}")
        if hint:
            print(f"     {hint}")
    while True:
        try:
            raw = input(
                f"\n  Choose 1-{len(keys)} [{keys.index(default_key) + 1}]: ").strip()
        except EOFError:
            # stdin ran out (piped input, closed terminal): take the default
            # rather than dying with a traceback.
            print()
            return default_key
        if not raw:
            return default_key
        if raw.isdigit() and 1 <= int(raw) <= len(keys):
            return keys[int(raw) - 1]
        print("  Not a valid choice.")


def _input(prompt, fallback=""):
    """input() that treats end-of-stdin as 'accept the default'."""
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        return fallback


def _ask_yes_no(prompt, default=False):
    d = "Y/n" if default else "y/N"
    while True:
        raw = _input(f"  {prompt} [{d}]: ").lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("  Answer y or n.")


def _ask_date(prompt, default):
    """Ask for a YYYY-MM-DD date, re-prompting until valid."""
    while True:
        raw = _input(f"  {prompt} [{default}]: ")
        if not raw:
            return default
        try:
            datetime.strptime(raw, "%Y-%m-%d")
            return raw
        except ValueError:
            print("  Use the form YYYY-MM-DD, e.g. 2026-01-15.")


def run_interactive(args):
    """Fill `args` by asking. Returns args, or None if the user quits."""
    tier_counts = {k: sum(1 for v in INDICES.values() if pred(v[3]))
                   for k, (_lbl, pred) in SELECTIONS.items()}

    print(f"\n{RULE}")
    print("  GLOBAL MARKET ANALYSIS - cumulative log returns")
    print(f"  {len(INDICES)} indices across {len(REGION_ORDER)} regions")
    print(RULE)

    start_choice = _ask(
        "How do you want to start?",
        {
            "quick": ("Quick default",
                      "Year to date / Top 20 / local currency / per-region panels"),
            "custom": ("Customise everything", "Answer a few questions"),
            "quit": ("Quit", ""),
        },
        "quick")

    if start_choice == "quit":
        return None

    if start_choice == "quick":
        args.period, args.selection, args.usd = "ytd", "top20", False
        print("\n  Running the quick default...")
        return args

    # --- which markets ----------------------------------------------------
    args.selection = _ask(
        "Which indices?",
        {k: (f"{lbl} ({tier_counts[k]} indices)",
             "slower to fetch" if tier_counts[k] > 30 else "")
         for k, (lbl, _p) in SELECTIONS.items()},
        "top20")

    region_choice = _ask(
        "Limit to a region?",
        {"all": ("All regions", "")} |
        {r.lower(): (r, "") for r in REGION_ORDER},
        "all")
    args.region = None if region_choice == "all" else [region_choice]

    # --- time window ------------------------------------------------------
    window = _ask(
        "Over what period?",
        {"ytd": ("Year to date", ""), "1m": ("Last month", ""),
         "3m": ("Last 3 months", ""), "6m": ("Last 6 months", ""),
         "1y": ("Last year", ""), "custom": ("Exact dates", "")},
        "ytd")
    if window == "custom":
        today = date.today().strftime("%Y-%m-%d")
        args.end = _ask_date("End date", today)
        default_start = f"{datetime.strptime(args.end, '%Y-%m-%d').year}-01-01"
        args.start = _ask_date("Start date", default_start)
    else:
        args.period = window

    # --- currency basis ---------------------------------------------------
    basis = _ask(
        "Which currency basis?",
        {"local": ("Local currency",
                   "How each market did at home"),
         "usd": ("Convert to USD",
                 "What a USD-based investor earned, including currency moves")},
        "local")
    args.usd = basis == "usd"

    # --- presentation -----------------------------------------------------
    view = _ask(
        "Which chart layout?",
        {"panels": ("One panel per region", "Every index individually coloured"),
         "combined": ("All on one axis", "Best for comparing whole regions")},
        "panels")
    args.combined = view == "combined"

    args.theme = _ask("Colour theme?",
                      {"dark": ("Dark", ""), "light": ("Light", "")}, "dark")

    print()
    if _ask_yes_no("Save the chart to a file as well?", False):
        suggested = f"chart-{args.selection}{'-usd' if args.usd else ''}.png"
        out = _input(f"  Filename [{suggested}]: ")
        args.out = out or suggested

    args.currency_note = True
    return args


def select_universe(selection, regions):
    """Apply the tier preset and optional region filter."""
    _label, pred = SELECTIONS[selection]
    chosen = {k: v for k, v in INDICES.items() if pred(v[3])}
    if regions:
        chosen = {k: v for k, v in chosen.items() if v[1] in regions}
    return chosen


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
    p.add_argument("--usd", action="store_true",
                   help="convert every index to USD before computing returns, "
                        "so all markets are compared on one currency basis")
    p.add_argument("--currency-note", action="store_true",
                   help="stamp the currency-basis caveat on the figure")
    p.add_argument("--title", help="override the chart title")
    p.add_argument("--combined", action="store_true",
                   help="all markets on one axis instead of per-region panels")
    p.add_argument("--region", action="append", metavar="NAME",
                   help=f"chart only this region (repeatable). "
                        f"One of: {', '.join(REGION_ORDER)}")
    p.add_argument("--label-count", type=int, default=3, metavar="N",
                   help="with --combined, direct-label the top and bottom N "
                        "markets (default: 3)")
    p.add_argument("--selection", default="top20", choices=list(SELECTIONS),
                   help="which indices to include (default: top20)")
    p.add_argument("--no-table", action="store_true",
                   help="skip the ranked table printed after the chart")
    p.add_argument("--quiet", action="store_true", help="suppress progress output")
    p.add_argument("--interactive", action="store_true",
                   help="force the question-and-answer menu")
    p.add_argument("--no-interactive", action="store_true",
                   help="never prompt; use flags and defaults only")
    args = p.parse_args(argv)

    # No arguments at all -> the menu, since that is the discoverable entry
    # point. Any flag means the caller knows what they want, so stay quiet and
    # non-interactive (scripts and CI rely on this).
    interactive = args.interactive or (not argv and len(sys.argv) == 1)
    if args.no_interactive:
        interactive = False
    if interactive and not sys.stdin.isatty():
        # Piped or redirected stdin cannot answer prompts; fall back silently.
        interactive = False

    if interactive:
        if run_interactive(args) is None:
            return 0

    if args.no_show:
        matplotlib.use("Agg")

    if args.label_count < 0:
        raise SystemExit("--label-count must be 0 or greater.")

    # Resolve --region case-insensitively, then apply the tier preset and the
    # region filter *before* fetching, so a narrowed run costs fewer requests.
    wanted = []
    if args.region:
        lookup = {r.lower(): r for r in REGION_ORDER}
        for raw in args.region:
            key = lookup.get(raw.strip().lower())
            if key is None:
                raise SystemExit(
                    f"--region {raw!r} is not a region. "
                    f"Choose from: {', '.join(REGION_ORDER)}")
            if key not in wanted:
                wanted.append(key)

    universe = select_universe(args.selection, wanted)
    if not universe:
        where = f" in {', '.join(wanted)}" if wanted else ""
        raise SystemExit(
            f"No markets{where} for selection {args.selection!r}. "
            f"Try --selection all.")

    start, end = resolve_window(args)

    fx, fx_failed = {}, []
    if args.usd:
        currencies = [c for _, _, c, _t in universe.values()]
        if not args.quiet:
            n = len({c for c in currencies if c != "USD"})
            print(f"Fetching {n} FX rates  ({start} -> {end})")
        fx, fx_failed = fetch_fx(currencies, start, end, quiet=args.quiet)

    if not args.quiet:
        print(f"Fetching {len(universe)} tickers  ({start} -> {end})")

    series, failed = fetch(universe, start, end, quiet=args.quiet,
                           to_usd=args.usd, fx=fx)

    if not args.quiet and series:
        print(f"\nFetched {len(series)} of {len(universe)}.")

    # Per-region panels are the default view: they answer "who leads where"
    # without the reader needing to know any flags. --combined restores the
    # all-on-one-axis chart.
    panels = not args.combined

    if series and not args.no_table:
        print_table(sorted(series, key=lambda s: s.final_log, reverse=True),
                    region_order=panels)

    if panels:
        plot_by_region(series, start, end, theme=args.theme, out=args.out,
                       show=not args.no_show,
                       currency_note=args.currency_note,
                       title=args.title, usd=args.usd)
    else:
        # A narrowed run has few enough lines to label them all, so lift the
        # cap rather than labelling only three of six.
        n_label = args.label_count
        if args.region and series:
            n_label = max(n_label, len(series))
        plot(series, start, end, theme=args.theme, out=args.out,
             show=not args.no_show, currency_note=args.currency_note,
             title=args.title, n_label=n_label, usd=args.usd)

    if fx_failed:
        print("\nFX rates unavailable:")
        for cur, reason in fx_failed:
            print(f"  - {cur}->USD: {reason}")

    if failed:
        print("\nFailed to fetch:")
        for name, ticker, reason in failed:
            print(f"  - {name} ({ticker}): {reason}")
    return 0 if series else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        # Ctrl-C at a prompt or mid-download is a normal way to leave; a
        # traceback here just looks like a crash.
        print("\nCancelled.")
        raise SystemExit(130)
