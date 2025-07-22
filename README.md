📈 Global Stock Indices Log Return Visualizer
This Python script fetches daily historical data for major global stock indices and Bitcoin since January 1st, 2025, computes their cumulative log returns, and visualizes them using a ranked, color-coded line plot.

It helps you quickly compare the performance of various world markets in 2025—answering the question: Which country or asset performed the best this year?

🔍 What It Does
Downloads historical price data using Yahoo Finance for major global indices:

Examples: S&P 500 (USA), Nifty 50 (India), MOEX (Russia), BTC/USD, etc.

Calculates cumulative log returns from closing prices.

Ranks indices based on year-to-date performance.

Plots a clean, dark-themed matplotlib chart with:

Dynamic color mapping

Percentage returns

Performance labels

Displays any failed data fetches for transparency.

📊 Sample Output
A line chart showing cumulative performance (in %) from Jan 1, 2025 to today.

Legend includes:

Ranking

Index name

Year-to-date return (with sign and %)

Example legend item:

markdown
Copy
Edit
1. BTC/USD (Bitcoin) (+45.67%)
🛠 Requirements
Python 3.7+

yfinance

matplotlib

numpy

Install dependencies:

bash
Copy
Edit
pip install yfinance matplotlib numpy
▶️ How to Run
bash
Copy
Edit
python indices_log_return_plot.py
🌐 Indices Included
🗽 S&P 500 (USA)

🇮🇳 Nifty 50 (India)

🇷🇺 MOEX (Russia)

🇨🇳 SSE Composite (China)

🇯🇵 Nikkei 225 (Japan)

🇩🇪 DAX 40 (Germany)

🇬🇧 FTSE 100 (UK)

🇫🇷 CAC 40 (France)

🇨🇦 TSX Composite (Canada)

🇧🇷 Bovespa (Brazil)

🇦🇺 ASX 200 (Australia)

🇰🇷 KOSPI (South Korea)

🇭🇰 Hang Seng (Hong Kong)

₿ BTC/USD (Bitcoin)

⚠️ Notes
If any index fails to load (e.g., due to Yahoo Finance data issues), it's listed in the console output.

The script uses cumulative log returns to give a time-consistent and compounding-aware measure of performance.

📁 File Structure
text
Copy
Edit
indices_log_return_plot.py   # Main script
README.md                    # (This file)
