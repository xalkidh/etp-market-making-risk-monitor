from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

TICKERS = ["SPY", "QQQ", "IWM", "EEM", "TLT", "GLD", "HYG", "VGK"]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def download_prices(tickers=TICKERS, start="2015-01-01", end=None, force=False):
    """Adjusted close prices. Cached in data/prices.csv."""
    path = DATA_DIR / "prices.csv"
    if path.exists() and not force:
        return pd.read_csv(path, index_col=0, parse_dates=True)

    DATA_DIR.mkdir(exist_ok=True)
    raw = yf.download(tickers, start=start, end=end,
                      auto_adjust=True, progress=False)
    prices = raw["Close"].dropna(how="all")[tickers]
    prices = prices[prices.index < pd.Timestamp.today().normalize()]
    prices.to_csv(path)
    return prices


def compute_returns(prices, kind="log"):
    """Daily returns. kind: 'log' or 'simple'."""
    if kind == "log":
        returns = np.log(prices / prices.shift(1))
    elif kind == "simple":
        returns = prices.pct_change()
    else:
        raise ValueError("kind must be 'log' or 'simple'")
    return returns.dropna()


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices)
    print(prices.tail())
    print("\nShape:", rets.shape)
    print("Missing values:", int(rets.isna().sum().sum()))
    print("\nAnnualised volatility (%):")
    print((rets.std() * np.sqrt(252) * 100).round(1))
    print("\nWorst day per ETF:")
    print(rets.idxmin())