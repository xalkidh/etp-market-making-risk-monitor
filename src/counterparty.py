import numpy as np
import pandas as pd

from src.data import download_prices, compute_returns
from src.book import POSITIONS, market_values

N_SIMS = 20_000
HORIZON = 10       # days = margin period of risk
LGD = 0.60
SEED = 42

# Simulated counterparties (assumptions - document these in the README)
COUNTERPARTIES = {
    "Clearing Broker A": dict(pd_annual=0.0005, margin=1_500_000, limit=4_000_000,
                              tickers=["SPY", "QQQ", "IWM"]),
    "Clearing Broker B": dict(pd_annual=0.0010, margin=900_000, limit=1_200_000,
                              tickers=["EEM", "VGK", "HYG"]),
    "Prime Broker C":    dict(pd_annual=0.0030, margin=600_000, limit=1_500_000,
                              tickers=["TLT", "GLD"]),
}


def simulate_horizon_returns(simple_rets, horizon=HORIZON, n_sims=N_SIMS, seed=SEED):
    """Bootstrap: draw `horizon` random historical days (same day for all ETFs,
    which keeps correlations) and compound them."""
    rng = np.random.default_rng(seed)
    values = simple_rets.to_numpy()
    idx = rng.integers(0, len(values), size=(n_sims, horizon))
    cum = (1 + values[idx]).prod(axis=1) - 1      # shape (n_sims, n_assets)
    return pd.DataFrame(cum, columns=simple_rets.columns)


def counterparty_table(mv, simple_rets, counterparties=COUNTERPARTIES):
    sims = simulate_horizon_returns(simple_rets)
    rows = {}
    for name, c in counterparties.items():
        tk = c["tickers"]
        pnl_sim = (sims[tk] * mv[tk]).sum(axis=1)   # 10-day P&L of positions carried
        positive = pnl_sim.clip(lower=0)            # gains the counterparty would owe us
        ee = positive.mean()
        pfe = np.percentile(positive, 95)
        ead = c["margin"] + ee
        rows[name] = {
            "Margin held": c["margin"],
            "EE": ee,
            "PFE95": pfe,
            "Exposure": c["margin"] + pfe,
            "Limit": c["limit"],
            "Expected loss 1y": c["pd_annual"] * LGD * ead,
        }
    t = pd.DataFrame(rows).T
    t["Utilisation"] = t["Exposure"] / t["Limit"]
    t["Share"] = t["Exposure"] / t["Exposure"].sum()
    return t


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")
    mv = market_values(POSITIONS, prices)

    t = counterparty_table(mv, rets)
    for name, r in t.iterrows():
        print(f"\n{name}")
        print(f"  Margin held:        {r['Margin held']:>12,.0f} $")
        print(f"  Expected exposure:  {r['EE']:>12,.0f} $")
        print(f"  PFE 95% ({HORIZON}d):     {r['PFE95']:>12,.0f} $")
        print(f"  Exposure vs limit:  {r['Exposure']:>12,.0f} / {r['Limit']:,.0f} $ ({r['Utilisation']:.0%})")
        print(f"  Expected loss (1y): {r['Expected loss 1y']:>12,.0f} $")
        print(f"  Share of total:     {r['Share']:.0%}")

    hhi = (t["Share"] ** 2).sum()
    print(f"\nConcentration HHI: {hhi:.2f} (perfectly spread = {1/len(t):.2f})")