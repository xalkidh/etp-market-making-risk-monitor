import numpy as np
import pandas as pd
from scipy.stats import norm

from src.data import download_prices, compute_returns
from src.book import POSITIONS, market_values, hypothetical_pnl


def historical_var(pnl, alpha=0.99):
    """Loss (positive number) exceeded on (1-alpha) of days."""
    return -np.percentile(pnl, (1 - alpha) * 100)


def historical_es(pnl, alpha=0.99):
    """Average loss on the days that are worse than the VaR."""
    tail = pnl[pnl <= -historical_var(pnl, alpha)]
    return -tail.mean()


def parametric_var(pnl, alpha=0.99):
    z = norm.ppf(1 - alpha)  # negative, e.g. -2.33 for 99%
    return -(pnl.mean() + z * pnl.std())


def parametric_es(pnl, alpha=0.99):
    z = norm.ppf(1 - alpha)
    return -pnl.mean() + pnl.std() * norm.pdf(z) / (1 - alpha)


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")
    mv = market_values(POSITIONS, prices)
    pnl = hypothetical_pnl(mv, rets)

    rows = {}
    for a in (0.95, 0.99):
        rows[f"{int(a*100)}%"] = {
            "Hist VaR": historical_var(pnl, a),
            "Param VaR": parametric_var(pnl, a),
            "Hist ES": historical_es(pnl, a),
            "Param ES": parametric_es(pnl, a),
        }
    table = pd.DataFrame(rows).T
    print("1-day risk measures ($):")
    print(table.round(0))

    var99 = historical_var(pnl, 0.99)
    print("\n10-day 99% hist VaR ($):", round(var99 * np.sqrt(10)))
    print("Days observed:", len(pnl))
    print("Days loss > 99% hist VaR:", int((pnl < -var99).sum()),
          "(expected ~", round(len(pnl) * 0.01), ")")