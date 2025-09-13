import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import matplotlib.colors as mcolors
import matplotlib.cm as cm

def plot_indices_log_returns():
    indices = {
        'MOEX Index (Russia)': 'IMOEX.ME',
        'Nifty 50 (India)': '^NSEI',
        'S&P 500 (USA)': '^GSPC',
        'Hang Seng Index (Hong Kong)': '^HSI',
        'SSE Composite Index (China)': '000001.SS',
        'Nikkei 225 (Japan)': '^N225',
        'BTC/USD (Bitcoin)': 'BTC-USD',
        'DAX 40 (Germany)': '^GDAXI',
        'FTSE 100 (UK)': '^FTSE',
        'CAC 40 (France)': '^FCHI',
        'TSX Composite (Canada)': '^GSPTSE',
        'Bovespa (Brazil)': '^BVSP',
        'ASX 200 (Australia)': '^AXJO',
        'KOSPI (South Korea)': '^KS11',
        'Tadawul All Shares Index (Saudi Arabia': "^TASI.SR",
        'STI Index (Singapore)': "^STI",
        'FTSE Bursa KLCI (Malaysia)': "^KLSE"
    }
    end_date = datetime.today().strftime('%Y-%m-%d')
    data = {}
    failed_tickers = []

    for name, ticker in indices.items():
        try:
            df = yf.Ticker(ticker).history(start='2025-07-01', end=end_date)
            if not df.empty:
                data[name] = df
            else:
                failed_tickers.append(ticker)
        except Exception as e:
            failed_tickers.append(ticker)
            print(f"⚠️ Failed to fetch {ticker}: {str(e)}")

    cumulative_log_returns = {}
    for name, df in data.items():
        log_return = np.log(df['Close'] / df['Close'].shift(1)).fillna(0).cumsum()
        cumulative_log_returns[name] = log_return

    sorted_returns = sorted(
        cumulative_log_returns.items(),
        key=lambda x: x[1].iloc[-1],
        reverse=True
    )

    plt.style.use('dark_background')
    plt.figure(figsize=(14, 8))

    cmap = cm.get_cmap('hsv', len(sorted_returns))
    handles = []
    labels = []

    for i, (name, log_return) in enumerate(sorted_returns):
        # Calculate total percent change from cumulative log return
        pct_change = (np.exp(log_return.iloc[-1]) - 1) * 100
        line, = plt.plot(log_return * 100, label=name, color=cmap(i), linewidth=2)
        handles.append(line)
        labels.append(f"{i+1}. {name} ({pct_change:+.2f}%)")  # Add % change with sign

    plt.title('Cumulative Log Returns (2025 - Today)', fontsize=14)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cumulative Log Return (%)', fontsize=12)
    plt.legend(handles=handles, labels=labels, loc='best', fontsize=9)
    plt.grid(True, color='gray', linestyle='--', linewidth=0.5)
    plt.tight_layout()
    plt.show()

    if failed_tickers:
        print("\n⚠️ Failed to fetch these tickers:")
        for ticker in failed_tickers:
            print(f"- {ticker}")

if __name__ == "__main__":
    plot_indices_log_returns()
