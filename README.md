# 📈 Global Stock Indices Log Return Visualizer

A Python tool to **analyze and compare cumulative log returns** of major **global stock indices and Bitcoin** since **January 1, 2025**.  
It answers a simple but powerful question:  
**Which markets and assets are leading the world in 2025?**

![Sample Chart](https://github.com/user-attachments/assets/cfc9091b-56cc-4167-b1c0-0161661aafaf)

---

## Features

- **Fetches daily market data** from Yahoo Finance using `yfinance`  
- **Computes cumulative log returns** from daily closing prices  
- **Ranks indices by performance** (year-to-date)  
- **Generates clean, dark-themed charts** with:  
  - Dynamic color mapping  
  - Percentage returns in the legend  
  - Auto-sorted ranking by performance  
- **Handles missing data gracefully**, listing failed tickers in the console  

---

## Markets Covered

- 🇷🇺 **MOEX Index (Russia)** — `IMOEX.ME`  
- 🇮🇳 **Nifty 50 (India)** — `^NSEI`  
- 🇺🇸 **S&P 500 (USA)** — `^GSPC`  
- 🇭🇰 **Hang Seng Index (Hong Kong)** — `^HSI`  
- 🇨🇳 **SSE Composite Index (China)** — `000001.SS`  
- 🇯🇵 **Nikkei 225 (Japan)** — `^N225`  
- ₿ **BTC/USD (Bitcoin)** — `BTC-USD`  
- 🇩🇪 **DAX 40 (Germany)** — `^GDAXI`  
- 🇬🇧 **FTSE 100 (UK)** — `^FTSE`  
- 🇫🇷 **CAC 40 (France)** — `^FCHI`  
- 🇨🇦 **TSX Composite (Canada)** — `^GSPTSE`  
- 🇧🇷 **Bovespa (Brazil)** — `^BVSP`  
- 🇦🇺 **ASX 200 (Australia)** — `^AXJO`  
- 🇰🇷 **KOSPI (South Korea)** — `^KS11`  
- 🇸🇦 **Tadawul All Shares Index (Saudi Arabia)** — `^TASI.SR`  
- 🇸🇬 **STI Index (Singapore)** — `^STI`  
- 🇲🇾 **FTSE Bursa KLCI (Malaysia)** — `^KLSE`  


---

## Sample Output

The script produces a **ranked line chart** where:  

- **X-axis:** Date (from Jan 1, 2025 → Today)  
- **Y-axis:** Cumulative log return (%)  
- **Legend:** Ranked indices with % return values  

---

## Installation & Requirements

**Dependencies:**
- Python 3.7+  
- [yfinance](https://pypi.org/project/yfinance/)  
- [matplotlib](https://matplotlib.org/)  
- [numpy](https://numpy.org/)  

Install with pip:  

```bash
pip install yfinance matplotlib numpy
