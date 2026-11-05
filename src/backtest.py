import numpy as np
import pandas as pd
from scipy.stats import chi2, norm

from data import download_prices, compute_returns
from book import POSITIONS, market_values, hypothetical_pnl

WINDOW = 500  # ~2 trading years


def rolling_hist_var(pnl, alpha=0.99, window=WINDOW):
    """VaR for day t from the `window` days BEFORE t (shift avoids look-ahead)."""
    return -pnl.rolling(window).quantile(1 - alpha).shift(1)


def rolling_param_var(pnl, alpha=0.99, window=WINDOW):
    z = norm.ppf(1 - alpha)
    mu = pnl.rolling(window).mean()
    sd = pnl.rolling(window).std()
    return -(mu + z * sd).shift(1)


def get_exceptions(pnl, var):
    valid = var.notna()
    return pnl[valid] < -var[valid]


def kupiec_pof(x, n, p=0.01):
    """Kupiec proportion-of-failures test. Returns (LR statistic, p-value)."""
    pi = x / n

    def loglik(q):
        return (n - x) * np.log(1 - q) + (x * np.log(q) if x > 0 else 0.0)

    lr = -2 * (loglik(p) - loglik(pi))
    return lr, 1 - chi2.cdf(lr, df=1)


def traffic_light(n_exceptions_250d):
    if n_exceptions_250d <= 4:
        return "GREEN"
    if n_exceptions_250d <= 9:
        return "YELLOW"
    return "RED"


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")
    mv = market_values(POSITIONS, prices)
    pnl = hypothetical_pnl(mv, rets)

    methods = {
        "Historical": rolling_hist_var(pnl),
        "Parametric": rolling_param_var(pnl),
    }

    for name, var in methods.items():
        exc = get_exceptions(pnl, var)
        n, x = len(exc), int(exc.sum())
        lr, pval = kupiec_pof(x, n)
        last250 = int(exc.iloc[-250:].sum())
        print(f"=== {name} VaR 99% (rolling {WINDOW}d) ===")
        print(f"Days tested: {n} | Exceptions: {x} | Expected: {n*0.01:.1f}")
        print(f"Kupiec LR = {lr:.2f}, p-value = {pval:.3f} ->",
              "REJECT" if pval < 0.05 else "do not reject")
        print(f"Last 250 days: {last250} exceptions -> {traffic_light(last250)}")
        print("Exceptions per year:")
        print(exc[exc].groupby(exc[exc].index.year).size().to_string())
        print()