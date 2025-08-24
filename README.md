📈 Global Stock Indices Log Return Visualizer

A Python tool to analyze and compare cumulative log returns of major global stock indices and Bitcoin since January 1, 2025.
It answers a simple but powerful question:
👉 Which markets and assets are leading the world in 2025?

<img width="1920" height="967" alt="Performance Chart" src="https://github.com/user-attachments/assets/cfc9091b-56cc-4167-b1c0-0161661aafaf" />
🔍 Features

📥 Fetches daily market data from Yahoo Finance using yfinance

📊 Computes cumulative log returns from daily closing prices

🏆 Ranks indices by performance (year-to-date)

🎨 Generates clean, dark-themed charts with:

Dynamic color mapping for clarity

% return labels in the legend

Auto-sorted ranking by performance

⚠️ Handles missing data gracefully, listing failed tickers in the console

🌐 Markets Covered

🇺🇸 S&P 500 (USA)

🇮🇳 Nifty 50 (India)

🇷🇺 MOEX Index (Russia)

🇨🇳 SSE Composite Index (China)

🇯🇵 Nikkei 225 (Japan)

🇩🇪 DAX 40 (Germany)

🇬🇧 FTSE 100 (UK)

🇫🇷 CAC 40 (France)

🇨🇦 TSX Composite (Canada)

🇧🇷 Bovespa (Brazil)

🇦🇺 ASX 200 (Australia)

🇰🇷 KOSPI (South Korea)

🇭🇰 Hang Seng Index (Hong Kong)

₿ BTC/USD (Bitcoin)

📊 Sample Output

The script produces a ranked line chart where:

X-axis → Date (from Jan 1, 2025 → Today)

Y-axis → Cumulative log return (%)

Legend → Ranked indices with % return values

🛠 Installation & Requirements

Dependencies:

Python 3.7+

yfinance

matplotlib

numpy

Install with pip:

pip install yfinance matplotlib numpy

▶️ Usage

Run the script from your terminal:

python indices_log_return_plot.py


A chart window will open showing the comparative performance of all tracked indices.

🚀 Why This Project?

Markets move fast. Instead of scanning dozens of charts individually, this tool gives you a single snapshot of how global indices and Bitcoin are performing relative to one another. Perfect for:

Investors tracking global diversification

Analysts comparing regional performance trends

Anyone curious about 2025 market leaders and laggards

✨ Pull requests, issues, and suggestions are welcome!
