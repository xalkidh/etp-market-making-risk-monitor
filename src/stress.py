import pandas as pd

from src.data import download_prices, compute_returns
from src.book import POSITIONS, market_values, betas, hypothetical_pnl
from src.var import historical_var, historical_es

# --- Assumptions (document these in the README) ---
TLT_DURATION = 16.5      # years
HYG_SPREAD_DURATION = 3.5
HALF_SPREAD_BPS = {      # normal half-spread, basis points
    "SPY": 0.5, "QQQ": 0.5, "IWM": 1.0, "EEM": 2.0,
    "TLT": 1.0, "GLD": 1.0, "HYG": 3.0, "VGK": 2.0,
}

HISTORICAL_SCENARIOS = {
    "ETF flash crash (Aug 2015)": ("2015-08-17", "2015-08-25"),
    "Q4 2018 sell-off":           ("2018-10-03", "2018-12-24"),
    "Covid crash (2020)":         ("2020-02-19", "2020-03-23"),
    "Rate shock (H1 2022)":       ("2022-01-03", "2022-06-16"),
    "Tariff shock (Apr 2025)":    ("2025-04-02", "2025-04-08"),
}

# equity: market move | rates_bp: change in yields | credit_bp: spread change
HYPOTHETICAL_SCENARIOS = {
    "Equity -10%, flight to quality": dict(equity=-0.10, rates_bp=-50, credit_bp=150, gold=0.03),
    "Rates +100bp":                   dict(equity=-0.04, rates_bp=100, credit_bp=50,  gold=-0.03),
    "Credit event (spreads +300bp)":  dict(equity=-0.06, rates_bp=-30, credit_bp=300, gold=0.02),
    "Gold crash -10%":                dict(equity=-0.02, rates_bp=30,  credit_bp=0,   gold=-0.10),
}


def historical_scenario_pnl(mv, simple_rets, start, end):
    """P&L of today's book if the cumulative moves of [start, end] repeated."""
    window = simple_rets.loc[start:end, mv.index]
    cum = (1 + window).prod() - 1
    return mv * cum


def factor_shocks(mv, b, equity, rates_bp, credit_bp, gold):
    """Translate factor shocks into a % move per ETF."""
    shocks = b[mv.index] * equity                          # beta-driven
    shocks["TLT"] = -TLT_DURATION * rates_bp / 10_000      # duration-driven
    shocks["GLD"] = gold
    shocks["HYG"] = b["HYG"] * equity - HYG_SPREAD_DURATION * credit_bp / 10_000
    return shocks


def liquidation_cost(mv, multiplier=10):
    """Cost of closing the whole book if half-spreads widen by `multiplier`."""
    hs = pd.Series(HALF_SPREAD_BPS)[mv.index] / 10_000
    return (mv.abs() * hs * multiplier).sum()


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")
    mv = market_values(POSITIONS, prices)
    b = betas(rets)

    pnl = hypothetical_pnl(mv, rets)
    var99 = historical_var(pnl, 0.99)
    es99 = historical_es(pnl, 0.99)

    results = {}
    for name, (s, e) in HISTORICAL_SCENARIOS.items():
        results[name] = historical_scenario_pnl(mv, rets, s, e).sum()
    for name, params in HYPOTHETICAL_SCENARIOS.items():
        shocks = factor_shocks(mv, b, **params)
        results[name] = (mv * shocks).sum()

    table = pd.DataFrame({"Stress P&L ($)": pd.Series(results)})
    table["x 1-day VaR99"] = table["Stress P&L ($)"] / -var99
    print(table.sort_values("Stress P&L ($)").round(2))
    print(f"\n1-day Hist VaR99: {var99:,.0f} | ES99: {es99:,.0f}")

    print("\nLiquidation cost if spreads x10:",
          f"{liquidation_cost(mv, 10):,.0f} $",
          f"(x1 normal: {liquidation_cost(mv, 1):,.0f} $)")

    print("\nP&L per ETF in Covid scenario ($):")
    print(historical_scenario_pnl(mv, rets, *HISTORICAL_SCENARIOS["Covid crash (2020)"]).round(0))