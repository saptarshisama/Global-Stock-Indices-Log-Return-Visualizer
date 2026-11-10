# Global Stock Indices — Log Return Visualizer

Compares the **cumulative log returns** of 23 major world equity indices, plus Bitcoin as a cross-asset benchmark, over any date window — ranked best to worst, in local currency or converted to USD.

![Cumulative log returns of global indices, 2026 year to date](assets/chart-dark.png)

---

## Why log returns

Log returns are **additive over time**, so a cumulative sum is a true compounded path rather than a sum of percentages that quietly overstates the result. They also make gains and losses symmetric: −50% and +100% are equal and opposite moves.

The chart plots the cumulative log return. The percentages in the labels and the table are converted back to simple returns with `exp(x) − 1`, because that is the number people actually recognise. The two diverge as magnitude grows — a log value of 0.35 is a +41.9% simple return — which is why the y-axis is labelled in log units and the callouts in percent.

### Two currency bases — and they disagree

By default every index is quoted in **its own local currency**, which measures local-market performance rather than the return earned by a single foreign investor.

Pass **`--usd`** to convert every index to USD at daily spot rates before computing returns. That answers the other question: *what did a USD-based investor actually earn?* The two rankings are genuinely different, because currency moves are part of the return:

| Market | Local | USD | Difference |
|---|---:|---:|---|
| TAIEX (Taiwan) | +41.9% | **+30.8%** | TWD fell — 11 points of the gain was currency |
| KOSPI (South Korea) | +16.5% | **+19.8%** | KRW rose, adding to the gain |
| SSE Composite (China) | −9.0% | **−4.8%** | CNY rose, cushioning the loss |
| Nifty 50 (India) | −4.2% | **−9.1%** | INR fell, deepening the loss |
| Jakarta (Indonesia) | −42.0% | **−45.4%** | IDR fell on top of an already bad year |
| S&P 500 (USA) | +10.1% | +10.1% | unchanged — already USD |

Conversion is applied to the **price level before returns are computed**, which is exact. Summing index returns and FX returns afterwards is only an approximation and drifts over long windows.

Both modes name their basis in the chart title, because the two are otherwise visually identical and mistaking one for the other misreads every number on the chart. `--currency-note` adds the matching caveat as a footnote.

![The same window converted to USD, showing a reordered ranking](assets/chart-usd-dark.png)

---

## The chart

<img src="assets/chart-light.png" alt="The same chart rendered in the light theme" width="100%">

Design decisions that are doing real work:

- **Colour encodes region, not rank.** Lines are grouped Americas / Europe / Asia / Oceania / Crypto, so regional clustering is visible at a glance — that is the actual story in the data, and colouring by rank would have wasted the channel on information the y-position already carries.
- **Composite encoding — hue × line style.** Five regions is one class more than colour alone can carry safely. The three hues used are the only trio that clears the all-pairs colour-vision gate in both themes (worst-case CVD ΔE 9.4 dark / 9.2 light); adding a fourth or fifth hue drops some pair to ΔE ≈ 1.9, which is indistinguishable to a protanope. So the last two regions reuse hues and separate by dash pattern. **The encoding therefore survives colourblindness and black-and-white printing.**
- **Only the extremes are labelled on the combined chart.** With 23 markets, most finish within a few percent of each other; direct-labelling all of them produces a wall of text with crossing leader lines that cannot be traced back to a line. The leaders and laggards get callouts (`--label-count N`), the full ranking goes to the printed table, and `--by-region` / `--region` label every index once there are few enough to do so legibly.
- **Panel labels are placed, not guessed.** In `--by-region`, each panel's index list goes in whichever corner contains the fewest plotted points, measured per panel. A fixed corner collided with Asia's curves, which fill both vertical halves.
- **The peak is named.** The highest point on the chart draws the eye first. If it belongs to a line that ends far below it, the reader has no way to identify it — so it is annotated where it peaks.
- **Both themes are selected, not flipped.** The light and dark hues are separate steps validated against their own surface, not an automatic inversion.

---

## Comparing individual markets

The combined chart shows how regions move together. To compare *countries* — who leads inside each region, who is actually outperforming — there are three views.

### `--by-region`: small multiples

One panel per region, every index named and ranked with its return. Panels share both axes, so their heights compare directly: Americas and Europe are visibly tight bands while Asia sprawls from +42% to −42%.

![One panel per region, each index labelled](assets/chart-by-region.png)

```bash
python index_comparison.py --by-region
```

### `--region`: drill into one

Charts a single region full-size, and because there are few enough lines, **every index gets its own end label** instead of just the top and bottom three.

```bash
python index_comparison.py --region Asia
```

Repeatable and case-insensitive, so `--region asia --region europe` compares two regions head to head.

### The key table

Printed after every run. This is where "who is outperforming" actually gets answered, because raw return alone is misleading:

```
AMERICAS  (6 markets)
  #  Market                  Region      In-rgn     Return       Vol      MaxDD   Ret/Vol   Bars
---  ----------------------  ---------  -------  ---------  --------  ---------  --------  -----
  1  TSX Composite (Canada)  Americas      1/6*    +14.31%      14.3%     -9.33%     +1.00    215
  2  IPC (Mexico)            Americas       2/6    +12.03%      17.0%    -11.49%     +0.71    215
  3  S&P 500 (USA)           Americas       3/6    +10.08%      14.0%     -9.10%     +0.72    215
```

| Column | Meaning |
|---|---|
| **In-rgn** | Rank within its own region. `*` marks that region's leader. |
| **Return** | Total simple return over the window. |
| **Vol** | Annualised volatility — standard deviation of daily log returns × √252. |
| **MaxDD** | Worst peak-to-trough fall inside the window. |
| **Ret/Vol** | Return per unit of volatility. A crude risk-adjusted ranking, **not** a Sharpe ratio — there is no risk-free rate here. |
| **Bars** | Trading days actually fetched. Varies by holiday calendar. |

Two things this surfaces that the ranking hides:

- **KOSPI's +16.5% came with 60.6% volatility and a −44.9% drawdown** (Ret/Vol 0.27). TSX earned a similar +14.3% at 14.3% vol (Ret/Vol 1.00). Same ballpark return, very different ride.
- **Within Europe, IBEX edges SMI on return** (+12.86% vs +12.82%) but SMI did it at 12.8% vol against IBEX's 17.6%.

`--by-region` groups the table by region with per-region rankings. A region summary always prints last:

```
REGION      Markets     Median       Best  Leader
----------  -------  ---------  ---------  ----------------------------
Americas          6     +9.38%    +14.31%  TSX Composite (Canada)
Europe            6     +7.70%    +12.86%  IBEX 35 (Spain)
Oceania           1     +3.46%     +3.46%  ASX 200 (Australia)
Asia              9     -3.18%    +41.95%  TAIEX (Taiwan)
Crypto            1    -15.22%    -15.22%  BTC/USD (Bitcoin)
```

Sorted by median, which answers the regional question properly: **the Americas lead on median (+9.38%) even though Asia holds the single best market.** Asia's median is negative — one star and a long tail of losers.

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
| `--usd` | Convert every index to USD at daily spot rates before computing returns. |
| `--currency-note` | Stamp the currency-basis caveat on the figure. |
| `--title TEXT` | Override the chart title. |
| `--by-region` | Small multiples: one panel per region, every index labelled. Also groups the table. |
| `--region NAME` | Chart only this region. Repeatable, case-insensitive. |
| `--label-count N` | Direct-label the top and bottom N markets. Default 3; `0` draws no end labels. Lifted automatically when `--region` narrows the set. |
| `--no-table` | Skip the ranked table. |
| `--quiet` | Suppress per-ticker progress output. |

The screenshots above are reproducible:

```bash
python index_comparison.py --period ytd --end 2026-11-10 --theme dark --out assets/chart-dark.png --no-show --currency-note
```

```bash
python index_comparison.py --period ytd --end 2026-11-10 --usd --theme dark --out assets/chart-usd-dark.png --no-show --currency-note
```

```bash
python index_comparison.py --period ytd --end 2026-11-10 --by-region --out assets/chart-by-region.png --no-show --currency-note
```

---

## Markets covered

Tickers with the currency each is quoted in. Every currency was confirmed against the `currency` field Yahoo reports for that ticker, not assumed from the country.

| Region | Markets |
|---|---|
| **Americas** | S&P 500 `^GSPC` *USD* · Nasdaq Composite `^IXIC` *USD* · Dow Jones `^DJI` *USD* · TSX Composite `^GSPTSE` *CAD* · Bovespa `^BVSP` *BRL* · IPC Mexico `^MXX` *MXN* |
| **Europe** | DAX 40 `^GDAXI` *EUR* · FTSE 100 `^FTSE` *GBP* · CAC 40 `^FCHI` *EUR* · Euro Stoxx 50 `^STOXX50E` *EUR* · SMI `^SSMI` *CHF* · IBEX 35 `^IBEX` *EUR* |
| **Asia** | Nifty 50 `^NSEI` *INR* · Hang Seng `^HSI` *HKD* · SSE Composite `000001.SS` *CNY* · Nikkei 225 `^N225` *JPY* · KOSPI `^KS11` *KRW* · TAIEX `^TWII` *TWD* · Jakarta Composite `^JKSE` *IDR* · STI `^STI` *SGD* · FTSE Bursa KLCI `^KLSE` *MYR* |
| **Oceania** | ASX 200 `^AXJO` *AUD* |
| **Crypto** | BTC/USD `BTC-USD` *USD* |

### Deliberately excluded

Two tickers are commented out in the source rather than deleted, with the reason recorded:

- **MOEX Index (Russia)** `IMOEX.ME` — Yahoo Finance stopped serving this after the 2022 sanctions.
- **Tadawul All Shares (Saudi Arabia)** `^TASI.SR` — same symptom; returns zero rows for every window tested.

Both return *"possibly delisted; no price data found"* and would otherwise fail silently into the failure list on every run. Re-enabling either needs a different data source (the MOEX ISS API, or the Tadawul site), not `yfinance`.

---

## How it works

1. **Fetch** — each ticker's daily history via `yfinance`, with `auto_adjust=True` so splits and dividends don't appear as fake jumps.
2. **Convert** *(only with `--usd`)* — multiply the price level by that currency's `XXXUSD=X` daily rate. FX and equity calendars differ, so rates are reindexed onto the index's own trading days and carried forward; a leading gap is dropped rather than back-filled, so a rate is never invented before the first quote.
3. **Compute** — `log(Pₜ / Pₜ₋₁)`, anchored at 0 on the first day, then cumulatively summed.
4. **Rank** — sorted by final cumulative return.
5. **Render** — region-encoded lines, selective callouts, and a ranked table.

Failures are collected and reported at the end with a reason (`no price data` vs. an exception type) rather than being swallowed, so a dead ticker is visible instead of silently missing.

---

## Notes

- Data is sourced from Yahoo Finance and is **not** survivorship-bias free or guaranteed accurate. Don't trade on it.
- Markets have different holiday calendars, so the number of bars per index varies slightly over the same window. Each series is plotted against its own trading dates.
- `--usd` uses spot rates only. It does not model hedging costs, and it ignores the interest-rate differential a hedged investor would actually earn or pay.
- If an FX rate can't be fetched, that index is dropped with the reason rather than silently falling back to local currency, so a USD chart never mixes bases.
- `--no-show` switches matplotlib to the `Agg` backend, so it works headless.
