# Global Market Analysis — Log Return Visualizer

Compares the **cumulative log returns** of **47 indices across 6 regions** — ranked best to worst, grouped by region, in local currency or converted to USD so markets are comparable on one basis.

## Just run it

```bash
pip install -r requirements.txt
python index_comparison.py
```

No arguments. It opens a menu:

```
----------------------------------------------------------------
  GLOBAL MARKET ANALYSIS - cumulative log returns
  47 indices across 6 regions
----------------------------------------------------------------

How do you want to start?
  1. Quick default  (default)
     Year to date / Top 20 / local currency / per-region panels
  2. Customise everything
     Answer a few questions
  3. Quit

  Choose 1-3 [1]:
```

**Press Enter and you get a chart.** That's the whole interface for the common case — you don't have to remember anything.

Choose `2` and it walks you through which indices, which region, what period, which currency basis, which layout, theme, and whether to save a PNG. Every question has a default in brackets that Enter accepts, so you can tab through the ones you don't care about.

### Choosing which markets

| Choice | Count | What it is |
|---|---|---|
| **Top 20 across regions** | 20 | The headline indices a global market report always carries — S&P 500, Nikkei, DAX, FTSE, Hang Seng, Nifty, TAIEX, Bovespa, ASX, BTC… |
| **Top 30 across regions** | 30 | Adds Russell 2000, IBEX 35, FTSE MIB, AEX, IPC Mexico, Shenzhen, Hang Seng China Ent, STI, Jakarta, JSE Top 40 |
| **All major indices** | 47 | Everything, including the Nordics, Austria, Greece, Portugal, Turkey, Israel, New Zealand, KOSDAQ and Ethereum |

Tiers are **curated by market significance, not by performance in the window** — deliberately. If "Top 20" meant "the 20 best performers this period" the set would change every run and two runs couldn't be compared.

The quick default gives you Top 20, year to date, in local currency, as per-region panels with every index individually coloured and the ranked table printed below.

![One panel per region, every index individually coloured and labelled](assets/chart-by-region.png)

Every index gets its own shade and dash inside its region's colour, so you can match any curve to a name in the legend beside it. Each panel is scaled to its own region and prints its range in the title — one shared scale stretched to Asia's ±80% flattened the other regions into unreadable bands.

And the table, printed every run, every selected market best to worst:

```
  #  Market                    Region      In-rgn     Return       Vol      MaxDD   Ret/Vol   Bars
---  ------------------------  ---------  -------  ---------  --------  ---------  --------  -----
  1  TAIEX (Taiwan)            Asia          1/7*    +41.95%      30.3%    -20.31%     +1.38    204
  2  KOSPI (South Korea)       Asia           2/7    +16.46%      60.6%    -44.94%     +0.27    208
  3  TSX Composite (Canada)    Americas      1/5*    +14.31%      14.3%     -9.33%     +1.00    215
  4  Nikkei 225 (Japan)        Asia           3/7    +13.39%      31.0%    -20.63%     +0.43    206
  5  SMI (Switzerland)         Europe        1/6*    +12.82%      12.8%    -12.08%     +1.00    216
  ...
```

### The three flags worth remembering

Everything else has a sensible default. These are the ones that change the answer:

```bash
python index_comparison.py --usd          # compare on one currency basis
python index_comparison.py --period 1y    # 1m, 3m, 6m, 1y, ytd
python index_comparison.py --region Asia  # just one region, full size
```

`python index_comparison.py --help` lists the rest.

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

## Design decisions

The light theme (`--theme light`), same default view:

<img src="assets/chart-light.png" alt="The per-region view rendered in the light theme" width="100%">

Decisions that are doing real work:

- **Colour encodes region, not rank.** Lines are grouped Americas / Europe / Asia / Oceania / Crypto, so regional clustering is visible at a glance — that is the actual story in the data, and colouring by rank would have wasted the channel on information the y-position already carries.
- **Composite encoding — hue × line style.** Five regions is one class more than colour alone can carry safely. The three hues used are the only trio that clears the all-pairs colour-vision gate in both themes (worst-case CVD ΔE 9.4 dark / 9.2 light); adding a fourth or fifth hue drops some pair to ΔE ≈ 1.9, which is indistinguishable to a protanope. So the last two regions reuse hues and separate by dash pattern. **The encoding therefore survives colourblindness and black-and-white printing.**
- **Only the extremes are labelled on the combined chart.** With twenty or more markets on one axis, most finish within a few percent of each other; direct-labelling all of them produces a wall of text with crossing leader lines that cannot be traced back to a line. There the leaders and laggards get callouts (`--label-count N`) and the table carries the rest. The default per-region view labels every index, because a panel holds at most nine lines.
- **Within a panel, each index has its own shade *and* dash.** Two channels, not one: three lightness steps × three dash patterns gives nine distinct styles, enough for the largest region. A reader who can't separate the shades can still separate solid from dashed from dotted, so the encoding survives colourblindness and black-and-white printing. Every lightness ramp is validated as an ordinal scale against its own surface, not eyeballed.
- **Panels are scaled per region, with the range in the title.** A shared y-scale is the textbook choice for small multiples, and it was wrong here: stretched to Asia's +42%/−42% spread, the Americas and Europe collapsed into thin bands near zero and the within-region detail — the thing these panels exist to show — disappeared. Each panel now uses its full height and states its range, so comparison happens by reading rather than by eyeballing equal heights.
- **Legends sit beside their panel, not inside it.** Placing the key in whichever corner had the fewest points worked until a region had nine entries; Asia's panel then had no gap big enough. A reserved column cannot collide at all.
- **The peak is named.** The highest point on the chart draws the eye first. If it belongs to a line that ends far below it, the reader has no way to identify it — so it is annotated where it peaks.
- **Both themes are selected, not flipped.** The light and dark hues are separate steps validated against their own surface, not an automatic inversion.

---

## The other views

The default is per-region panels. Two alternatives:

### `--region`: drill into one

Charts a single region full-size, and because there are few enough lines, **every index gets its own end label**.

```bash
python index_comparison.py --region Asia
```

Repeatable and case-insensitive, so `--region asia --region europe` compares two regions head to head.

### `--combined`: all on one axis

The original view. Best for seeing how whole regions move together rather than who leads within one — colour groups by region, and only the global leaders and laggards are labelled.

![All markets on one axis, coloured by region](assets/chart-dark.png)

```bash
python index_comparison.py --combined
```

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

In the default view a one-line pecking order per region also prints, for reading a single region without scanning the full list:

```
Americas  TSX Composite +14.3%  >  IPC +12.0%  >  S&P 500 +10.1%  >  Nasdaq Composite +8.7%  >  ...
Europe    IBEX 35 +12.9%  >  SMI +12.8%  >  FTSE 100 +8.4%  >  DAX 40 +7.0%  >  ...
```

And a region summary always prints last:

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

## All the options

You don't need these to use it — `python index_comparison.py` is the intended entry point. This is the reference.

| Flag | Description |
|---|---|
| `--selection {top20,top30,all}` | Which indices to include. Default `top20`. |
| `--interactive` | Force the menu (it opens automatically when run with no arguments). |
| `--no-interactive` | Never prompt — use flags and defaults only. For scripts and CI. |
| `--period {1m,3m,6m,1y,ytd}` | Window relative to `--end`. Default `ytd`. |
| `--start YYYY-MM-DD` | Exact start date. Overrides `--period`. |
| `--end YYYY-MM-DD` | End date. Defaults to today. |
| `--usd` | Convert every index to USD at daily spot rates before computing returns. |
| `--region NAME` | Chart only this region. Repeatable, case-insensitive. |
| `--combined` | All markets on one axis instead of per-region panels. |
| `--theme {dark,light}` | Default `dark`. |
| `--out PATH` | Save the chart to this path. |
| `--no-show` | Don't open a window (switches to the Agg backend). Use on a server or in CI. |
| `--currency-note` | Stamp the currency-basis caveat on the figure. |
| `--title TEXT` | Override the chart title. |
| `--label-count N` | With `--combined`, direct-label the top and bottom N markets. Default 3; `0` draws none. |
| `--no-table` | Skip the printed table. |
| `--quiet` | Suppress per-ticker progress output. |

The screenshots above are reproducible:

```bash
python index_comparison.py --no-interactive --period ytd --end 2026-11-10 --out assets/chart-by-region.png --no-show --currency-note
```

```bash
python index_comparison.py --no-interactive --period ytd --end 2026-11-10 --combined --out assets/chart-dark.png --no-show --currency-note
```

```bash
python index_comparison.py --no-interactive --period ytd --end 2026-11-10 --combined --usd --out assets/chart-usd-dark.png --no-show --currency-note
```

---

## Markets covered

Tickers with the currency each is quoted in. Every currency was confirmed against the `currency` field Yahoo reports for that ticker, not assumed from the country.

| Region | Markets |
|---|---|
| **Americas** (9) | S&P 500 `^GSPC` *USD* · Nasdaq Composite `^IXIC` *USD* · Dow Jones `^DJI` *USD* · Russell 2000 `^RUT` *USD* · S&P MidCap 400 `^SP400` *USD* · NYSE Composite `^NYA` *USD* · TSX Composite `^GSPTSE` *CAD* · Bovespa `^BVSP` *BRL* · IPC `^MXX` *MXN* |
| **Europe** (17) | DAX 40 `^GDAXI` *EUR* · FTSE 100 `^FTSE` *GBP* · CAC 40 `^FCHI` *EUR* · Euro Stoxx 50 `^STOXX50E` *EUR* · STOXX Europe 600 `^STOXX` *EUR* · SMI `^SSMI` *CHF* · IBEX 35 `^IBEX` *EUR* · FTSE MIB `FTSEMIB.MI` *EUR* · AEX `^AEX` *EUR* · BEL 20 `^BFX` *EUR* · OMX Stockholm 30 `^OMX` *SEK* · OMX Copenhagen 25 `^OMXC25` *DKK* · OMX Helsinki 25 `^OMXH25` *EUR* · ATX `^ATX` *EUR* · PSI `^BVLG` *EUR* · Athex Composite `GD.AT` *EUR* · BIST 100 `XU100.IS` *TRY* |
| **Asia** (16) | Nikkei 225 `^N225` *JPY* · SSE Composite `000001.SS` *CNY* · Shenzhen Component `399001.SZ` *CNY* · Hang Seng `^HSI` *HKD* · Hang Seng China Ent `^HSCE` *HKD* · Nifty 50 `^NSEI` *INR* · BSE Sensex `^BSESN` *INR* · Nifty 100 `^CNX100` *INR* · Nifty Bank `^NSEBANK` *INR* · KOSPI `^KS11` *KRW* · KOSDAQ `^KQ11` *KRW* · TAIEX `^TWII` *TWD* · STI `^STI` *SGD* · Jakarta Composite `^JKSE` *IDR* · FTSE Bursa KLCI `^KLSE` *MYR* · TA-125 `^TA125.TA` *ILS* |
| **Oceania** (2) | ASX 200 `^AXJO` *AUD* · NZX 50 `^NZ50` *NZD* |
| **Africa** (1) | JSE Top 40 `^JN0U.JO` *USD* |
| **Crypto** (2) | BTC/USD `BTC-USD` *USD* · ETH/USD `ETH-USD` *USD* |

Tier 1 (Top 20) and tier 2 (Top 30) membership is set in the source, next to each ticker.

### Tried and excluded

Every ticker above was confirmed to return data. These were tested and rejected, recorded in the source so they aren't re-added on a hunch:

**No data from Yahoo over any window tested** — MOEX `IMOEX.ME` (delisted after the 2022 sanctions), Tadawul `^TASI.SR`, CSI 300 `000300.SS`, TOPIX `^TOPX`, SET Thailand `^SET.BK`, PSEi Philippines `PSEI.PS`, VN-Index `^VNINDEX`, WIG20 Poland, BUX Hungary, PX Czechia, Oslo All-Share, IPSA Chile, COLCAP Colombia, EGX 30 Egypt, DFM `^DFMGI`, QE Qatar. Merval Argentina `^MERV` returns only 64 rows and no currency.

**Rejected by the split guard** — the TOPIX proxy ETF `1306.T` returns data, but it carries an unadjusted 10:1 reverse split (¥36.4 → ¥381.9 overnight, which reads as **+948% in a day**). Left in, it reported 367% annualised volatility and a −91% drawdown. See *Data quality* below.

Re-enabling any of these needs a different data source, not `yfinance`.

---

## How it works

1. **Select** — apply the tier preset and any region filter *before* fetching, so a narrowed run costs fewer requests.
2. **Fetch** — each ticker's daily history via `yfinance`, with `auto_adjust=True` so splits and dividends don't appear as fake jumps.
3. **Screen** — reject any series containing an implausible single-day move (see below).
4. **Convert** *(only with `--usd`)* — multiply the price level by that currency's `XXXUSD=X` daily rate. FX and equity calendars differ, so rates are reindexed onto the index's own trading days and carried forward; a leading gap is dropped rather than back-filled, so a rate is never invented before the first quote.
5. **Compute** — `log(Pₜ / Pₜ₋₁)`, anchored at 0 on the first day, then cumulatively summed.
6. **Rank** — sorted by final cumulative return.
7. **Render** — region-encoded lines and the ranked table.

Failures are collected and reported at the end with a reason rather than being swallowed, so a dead ticker is visible instead of silently missing.

### Data quality

`auto_adjust=True` is supposed to back out splits, but it doesn't always. The TOPIX proxy ETF `1306.T` carried an unadjusted 10:1 reverse split — ¥36.4 to ¥381.9 overnight — and reported **+948% in a single day**, which poisoned its volatility (367%), drawdown (−91%) and whole cumulative path.

So any series containing a single-day log move above 0.60 (roughly −45% to +82%) is rejected with the reason `unadjusted split? +N% in one day`. Broad indices don't move that far in a session; in practice such a jump means a corporate action the adjustment missed. The threshold is deliberately loose enough to pass genuinely violent markets — Bitcoin at 37% annualised volatility, Ethereum at 50%, KOSDAQ at 55% and Turkey's BIST all survive it.

---

## Notes

- Data is sourced from Yahoo Finance and is **not** survivorship-bias free or guaranteed accurate. Don't trade on it.
- Markets have different holiday calendars, so the number of bars per index varies slightly over the same window. Each series is plotted against its own trading dates.
- `--usd` uses spot rates only. It does not model hedging costs, and it ignores the interest-rate differential a hedged investor would actually earn or pay.
- If an FX rate can't be fetched, that index is dropped with the reason rather than silently falling back to local currency, so a USD chart never mixes bases.
- `--no-show` switches matplotlib to the `Agg` backend, so it works headless.
