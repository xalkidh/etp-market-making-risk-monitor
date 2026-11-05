import pandas as pd

from data import download_prices, compute_returns

# Signed positions in shares (+ long, - short). Simulated market-maker inventory.
POSITIONS = {
    "SPY": 6_000, "QQQ": -4_000, "IWM": 9_000, "EEM": 30_000,
    "TLT": -15_000, "GLD": 5_000, "HYG": 20_000, "VGK": -12_000,
}


def market_values(positions, prices):
    """Signed market value per ETF using the latest close."""
    last = prices.iloc[-1]
    return pd.Series(positions) * last[list(positions)]


def exposures(mv):
    return pd.Series({
        "long": mv[mv > 0].sum(),
        "short": mv[mv < 0].sum(),
        "net": mv.sum(),
        "gross": mv.abs().sum(),
    })


def betas(simple_returns, benchmark="SPY"):
    """Beta of each ETF vs the benchmark: cov(r_i, r_b) / var(r_b)."""
    cov = simple_returns.cov()[benchmark]
    return cov / simple_returns[benchmark].var()


def hypothetical_pnl(mv, simple_returns):
    """Daily P&L today's book would have made on each historical day."""
    return (simple_returns[mv.index] * mv).sum(axis=1)


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")

    mv = market_values(POSITIONS, prices)
    b = betas(rets)

    print("Market value per ETF ($):")
    print(mv.round(0))
    print("\nExposures ($):")
    print(exposures(mv).round(0))
    print("\nBeta vs SPY:")
    print(b.round(2))
    print("\nBeta-adjusted net exposure ($):", round((mv * b[mv.index]).sum()))

    pnl = hypothetical_pnl(mv, rets)
    print("\nHypothetical daily P&L ($): mean / std / worst / best")
    print(round(pnl.mean()), round(pnl.std()), round(pnl.min()), round(pnl.max()))
    print("Worst day:", pnl.idxmin().date())