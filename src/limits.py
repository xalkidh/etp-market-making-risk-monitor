import pandas as pd

from src.data import download_prices, compute_returns
from src.book import POSITIONS, market_values, exposures, betas, hypothetical_pnl
from src.var import historical_var, historical_es
from src.stress import (HISTORICAL_SCENARIOS, HYPOTHETICAL_SCENARIOS,
                        historical_scenario_pnl, factor_shocks)
from src.counterparty import counterparty_table

AMBER = 0.80   # warning threshold (utilisation)
RED = 1.00     # breach

# Simulated limits (assumptions - document these in the README)
LIMITS = {
    "1-day VaR 99%":            250_000,
    "1-day ES 99%":             400_000,
    "Worst stress loss":        3_500_000,
    "Gross exposure":           25_000_000,
    "Net exposure (abs)":       10_000_000,
    "Beta-adj. net (abs)":      8_000_000,
    "Largest position % gross": 0.30,
}

ESCALATION = {
    "GREEN": "No action. Routine monitoring.",
    "AMBER": "Warning: notify Senior Risk Officer, monitor closely, prepare mitigation.",
    "RED":   "BREACH: escalate to Senior Risk Officer and CRO; reduce risk or seek approval.",
}


def status(utilisation):
    if utilisation >= RED:
        return "RED"
    if utilisation >= AMBER:
        return "AMBER"
    return "GREEN"


def compute_metrics(prices, rets, positions=POSITIONS):
    mv = market_values(positions, prices)
    b = betas(rets)
    exp = exposures(mv)
    pnl = hypothetical_pnl(mv, rets)

    stress = {}
    for name, (s, e) in HISTORICAL_SCENARIOS.items():
        stress[name] = historical_scenario_pnl(mv, rets, s, e).sum()
    for name, params in HYPOTHETICAL_SCENARIOS.items():
        stress[name] = (mv * factor_shocks(mv, b, **params)).sum()

    metrics = {
        "1-day VaR 99%":            historical_var(pnl, 0.99),
        "1-day ES 99%":             historical_es(pnl, 0.99),
        "Worst stress loss":        -min(stress.values()),
        "Gross exposure":           exp["gross"],
        "Net exposure (abs)":       abs(exp["net"]),
        "Beta-adj. net (abs)":      abs((mv * b[mv.index]).sum()),
        "Largest position % gross": mv.abs().max() / exp["gross"],
    }
    return mv, metrics


def limit_report(prices, rets, positions=POSITIONS):
    mv, metrics = compute_metrics(prices, rets, positions)
    rows = [{"Metric": k, "Value": v, "Limit": LIMITS[k]} for k, v in metrics.items()]

    cp = counterparty_table(mv, rets)
    for name, r in cp.iterrows():
        rows.append({"Metric": f"Counterparty: {name}",
                     "Value": r["Exposure"], "Limit": r["Limit"]})

    report = pd.DataFrame(rows).set_index("Metric")
    report["Utilisation"] = report["Value"] / report["Limit"]
    report["Status"] = report["Utilisation"].apply(status)
    return report


if __name__ == "__main__":
    prices = download_prices()
    rets = compute_returns(prices, kind="simple")
    report = limit_report(prices, rets)

    show = report.copy()
    show["Utilisation"] = (show["Utilisation"] * 100).round(0).astype(int).astype(str) + "%"
    print(show.to_string(float_format=lambda x: f"{x:,.2f}"))

    print("\nSummary:", report["Status"].value_counts().to_dict())
    for metric, r in report[report["Status"] != "GREEN"].iterrows():
        print(f"\n[{r['Status']}] {metric} at {r['Utilisation']:.0%} of limit")
        print("  ->", ESCALATION[r["Status"]])