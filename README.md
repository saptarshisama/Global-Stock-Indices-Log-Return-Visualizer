# Global Stock Indices — Log Return Visualizer

Compares the **cumulative log returns** of 23 major world equity indices, plus Bitcoin as a cross-asset benchmark, over any date window — ranked best to worst.

![Cumulative log returns of global indices, 2026 year to date](assets/chart-dark.png)

---

## Why log returns

Log returns are **additive over time**, so a cumulative sum is a true compounded path rather than a sum of percentages that quietly overstates the result. They also make gains and losses symmetric: −50% and +100% are equal and opposite moves.

The chart plots the cumulative log return. The percentages in the labels and the table are converted back to simple returns with `exp(x) − 1`, because that is the number people actually recognise. The two diverge as magnitude grows — a log value of 0.35 is a +41.9% simple return — which is why the y-axis is labelled in log units and the callouts in percent.

### One caveat worth stating plainly

Every index is quoted in **its own local currency**. This chart measures local-currency performance, not the return earned by a single foreign investor. A market can lead this ranking while a falling currency erases the gain in USD terms. Pass `--currency-note` to stamp that disclaimer onto the figure.

---

## The chart

<img src="assets/chart-light.png" alt="The same chart rendered in the light theme" width="100%">

Design decisions that are doing real work:

- **Colour encodes region, not rank.** Lines are grouped Americas / Europe / Asia / Oceania / Crypto, so regional clustering is visible at a glance — that is the actual story in the data, and colouring by rank would have wasted the channel on information the y-position already carries.
- **Composite encoding — hue × line style.** Five regions is one class more than colour alone can carry safely. The three hues used are the only trio that clears the all-pairs colour-vision gate in both themes (worst-case CVD ΔE 9.4 dark / 9.2 light); adding a fourth or fifth hue drops some pair to ΔE ≈ 1.9, which is indistinguishable to a protanope. So the last two regions reuse hues and separate by dash pattern. **The encoding therefore survives colourblindness and black-and-white printing.**
- **Only the extremes are labelled.** With 23 markets, most finish within a few percent of each other; direct-labelling all of them produces a wall of text with crossing leader lines that cannot be traced back to a line. The leaders and laggards get callouts (`--label-count N`), and the full ranking goes to the printed table.
- **The peak is named.** The highest point on the chart draws the eye first. If it belongs to a line that ends far below it, the reader has no way to identify it — so it is annotated where it peaks.
- **Both themes are selected, not flipped.** The light and dark hues are separate steps validated against their own surface, not an automatic inversion.

Every value is reachable without reading colour, via the ranked table:

```
  #  Market                         Region        Return
---  -----------------------------  ---------  ---------
  1  TAIEX (Taiwan)                 Asia         +41.95%
  2  KOSPI (South Korea)            Asia         +16.46%
  3  TSX Composite (Canada)         Americas     +14.31%
...
 22  BTC/USD (Bitcoin)              Crypto       -15.22%
 23  Jakarta Composite (Indonesia)  Asia         -42.00%
```

---

## Install

```bash
pip install -r requirements.txt
```

Requires Python 3.9+ (builtin generic annotations). Verified on 3.10.

## Usage

```bash
python index_comparison.py
```

Year to date by default, dark theme, opens a window and prints the ranked table.

```bash
python index_comparison.py --period 1y --theme light
```

```bash
python index_comparison.py --start 2026-01-01 --end 2026-11-10 --out chart.png --no-show
```

Saves a PNG without opening a window — use this on a server or in CI.

### Options

| Flag | Description |
|---|---|
| `--start YYYY-MM-DD` | Start date. Overrides `--period`. |
| `--end YYYY-MM-DD` | End date. Defaults to today. |
| `--period {1m,3m,6m,1y,ytd}` | Window relative to `--end`. Default `ytd`. |
| `--theme {dark,light}` | Default `dark`. |
| `--out PATH` | Save the chart to this path. |
| `--no-show` | Don't open a window (switches to the Agg backend). |
| `--currency-note` | Stamp the local-currency caveat on the figure. |
| `--title TEXT` | Override the chart title. |
| `--label-count N` | Direct-label the top and bottom N markets. Default 3; `0` draws no end labels. |
| `--no-table` | Skip the ranked table. |
| `--quiet` | Suppress per-ticker progress output. |

The screenshots above are reproducible:

```bash
python index_comparison.py --period ytd --end 2026-11-10 --theme dark --out assets/chart-dark.png --no-show --currency-note
```

---

## Markets covered

| Region | Markets |
|---|---|
| **Americas** | S&P 500 `^GSPC` · Nasdaq Composite `^IXIC` · Dow Jones `^DJI` · TSX Composite `^GSPTSE` · Bovespa `^BVSP` · IPC Mexico `^MXX` |
| **Europe** | DAX 40 `^GDAXI` · FTSE 100 `^FTSE` · CAC 40 `^FCHI` · Euro Stoxx 50 `^STOXX50E` · SMI `^SSMI` · IBEX 35 `^IBEX` |
| **Asia** | Nifty 50 `^NSEI` · Hang Seng `^HSI` · SSE Composite `000001.SS` · Nikkei 225 `^N225` · KOSPI `^KS11` · TAIEX `^TWII` · Jakarta Composite `^JKSE` · STI `^STI` · FTSE Bursa KLCI `^KLSE` |
| **Oceania** | ASX 200 `^AXJO` |
| **Crypto** | BTC/USD `BTC-USD` |

### Deliberately excluded

Two tickers are commented out in the source rather than deleted, with the reason recorded:

- **MOEX Index (Russia)** `IMOEX.ME` — Yahoo Finance stopped serving this after the 2022 sanctions.
- **Tadawul All Shares (Saudi Arabia)** `^TASI.SR` — same symptom; returns zero rows for every window tested.

Both return *"possibly delisted; no price data found"* and would otherwise fail silently into the failure list on every run. Re-enabling either needs a different data source (the MOEX ISS API, or the Tadawul site), not `yfinance`.

---

## How it works

1. **Fetch** — each ticker's daily history via `yfinance`, with `auto_adjust=True` so splits and dividends don't appear as fake jumps.
2. **Compute** — `log(Pₜ / Pₜ₋₁)`, anchored at 0 on the first day, then cumulatively summed.
3. **Rank** — sorted by final cumulative return.
4. **Render** — region-encoded lines, selective callouts, and a ranked table.

Failures are collected and reported at the end with a reason (`no price data` vs. an exception type) rather than being swallowed, so a dead ticker is visible instead of silently missing.

---

## Notes

- Data is sourced from Yahoo Finance and is **not** survivorship-bias free or guaranteed accurate. Don't trade on it.
- Markets have different holiday calendars, so the number of bars per index varies slightly over the same window. Each series is plotted against its own trading dates.
- `--no-show` switches matplotlib to the `Agg` backend, so it works headless.
