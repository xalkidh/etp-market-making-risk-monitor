import sys
from pathlib import Path

# Let Streamlit find the `src` package (run from the repo root)
sys.path.append(str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.data import download_prices, compute_returns
from src.book import POSITIONS, market_values, exposures, betas, hypothetical_pnl
from src.var import historical_var, historical_es
from src.stress import (HISTORICAL_SCENARIOS, HYPOTHETICAL_SCENARIOS,
                        historical_scenario_pnl, factor_shocks)
from src.counterparty import counterparty_table
from src.limits import limit_report, ESCALATION

st.set_page_config(page_title="ETP Risk Monitor", layout="wide")
COLORS = {"GREEN": "background-color: #c8e6c9", "AMBER": "background-color: #ffe0b2",
          "RED": "background-color: #ffcdd2"}


@st.cache_data
def load_data():
    prices = download_prices()
    return prices, compute_returns(prices, kind="simple")


prices, rets = load_data()

# ---- Sidebar: what-if positions ----
st.sidebar.header("Positions (shares, + long / - short)")
positions = {t: st.sidebar.number_input(t, value=int(q), step=1000)
             for t, q in POSITIONS.items()}

# ---- Calculations ----
mv = market_values(positions, prices)
exp = exposures(mv)
pnl = hypothetical_pnl(mv, rets)
var99, es99 = historical_var(pnl, 0.99), historical_es(pnl, 0.99)
report = limit_report(prices, rets, positions)

# ---- Header ----
st.title("ETP Market-Making Risk Monitor")
st.caption(f"Prices: Yahoo Finance, last close {prices.index[-1].date()}. "
           "Positions, limits and counterparties are simulated.")

counts = report["Status"].value_counts()
c1, c2, c3 = st.columns(3)
c1.metric("RED (breaches)", int(counts.get("RED", 0)))
c2.metric("AMBER (warnings)", int(counts.get("AMBER", 0)))
c3.metric("GREEN", int(counts.get("GREEN", 0)))

# ---- Limits table ----
st.subheader("Limit monitoring")
def fmt(metric, x):
    return f"{x:.0%}" if "% gross" in metric else f"{x:,.0f}"

show = report.copy()
show["Utilisation"] = (show["Utilisation"] * 100).round(0)
show["Value"] = [fmt(m, v) for m, v in zip(report.index, report["Value"])]
show["Limit"] = [fmt(m, v) for m, v in zip(report.index, report["Limit"])]
styled = (show.style.apply(lambda col: [COLORS[v] for v in col], subset=["Status"])
          .format({"Utilisation": "{:.0f}%"}))
st.dataframe(styled, use_container_width=True)

for metric, r in report[report["Status"] != "GREEN"].iterrows():
    msg = f"**{metric}** at {r['Utilisation']:.0%} of limit. {ESCALATION[r['Status']]}"
    (st.error if r["Status"] == "RED" else st.warning)(msg)

# ---- Exposure and P&L distribution ----
left, right = st.columns(2)
with left:
    st.subheader("Market value per ETF ($)")
    st.bar_chart(mv)
    st.write(f"Long {exp['long']:,.0f} | Short {exp['short']:,.0f} | "
             f"Net {exp['net']:,.0f} | Gross {exp['gross']:,.0f}")
with right:
    st.subheader("Hypothetical daily P&L")
    fig, ax = plt.subplots()
    ax.hist(pnl, bins=80, color="#90a4ae")
    ax.axvline(-var99, color="orange", label=f"VaR 99%: {var99:,.0f}")
    ax.axvline(-es99, color="red", label=f"ES 99%: {es99:,.0f}")
    ax.set_xlabel("P&L ($)")
    ax.legend()
    st.pyplot(fig)

# ---- Stress tests ----
st.subheader("Stress test P&L ($)")
b = betas(rets)
stress = {n: historical_scenario_pnl(mv, rets, s, e).sum()
          for n, (s, e) in HISTORICAL_SCENARIOS.items()}
stress.update({n: (mv * factor_shocks(mv, b, **p)).sum()
               for n, p in HYPOTHETICAL_SCENARIOS.items()})
st.bar_chart(pd.Series(stress).sort_values())

# ---- Counterparties ----
st.subheader("Counterparty exposure")
st.dataframe(counterparty_table(mv, rets).style.format("{:,.2f}"),
             use_container_width=True)