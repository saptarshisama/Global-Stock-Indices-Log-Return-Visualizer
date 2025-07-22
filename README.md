# 📈 Global Stock Indices Log Return Visualizer

This Python script fetches **daily historical data** for major **global stock indices and Bitcoin** since **January 1st, 2025**, computes their **cumulative log returns**, and visualizes them using a **ranked, color-coded line plot**.

It helps you quickly compare the performance of various world markets in 2025—answering the question: _Which country or asset performed the best this year?_

---

## 🔍 What It Does

- Downloads historical price data using **Yahoo Finance** for major global indices:
  - Examples: **S&P 500 (USA)**, **Nifty 50 (India)**, **MOEX (Russia)**, **BTC/USD**, etc.
- Calculates **cumulative log returns** from closing prices.
- Ranks indices based on year-to-date performance.
- Plots a clean, dark-themed **matplotlib** chart with:
  - Dynamic color mapping
  - Percentage returns
  - Performance-based labeling
- Displays any failed data fetches in the console for transparency.

---

## 📊 Sample Output

A line chart showing cumulative performance (in %) from **Jan 1, 2025** to **today**.

Legend format:


---

## 🌐 Indices Included

- 🇺🇸 S&P 500 (USA)
- 🇮🇳 Nifty 50 (India)
- 🇷🇺 MOEX Index (Russia)
- 🇨🇳 SSE Composite Index (China)
- 🇯🇵 Nikkei 225 (Japan)
- 🇩🇪 DAX 40 (Germany)
- 🇬🇧 FTSE 100 (UK)
- 🇫🇷 CAC 40 (France)
- 🇨🇦 TSX Composite (Canada)
- 🇧🇷 Bovespa (Brazil)
- 🇦🇺 ASX 200 (Australia)
- 🇰🇷 KOSPI (South Korea)
- 🇭🇰 Hang Seng Index (Hong Kong)
- ₿ BTC/USD (Bitcoin)

---

## 🛠 Requirements

- Python 3.7+
- `yfinance`
- `matplotlib`
- `numpy`

Install dependencies:

```bash
pip install yfinance matplotlib numpy

▶️ How to Run
Simply run the script from your terminal:

bash
Copy
Edit
python indices_log_return_plot.py
