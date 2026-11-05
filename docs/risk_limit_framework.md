# Risk Limit Framework

**Project:** ETP Market-Making Risk Monitor
**Version:** 1.0 (November 2026)
**Status:** Illustrative. All limits, roles and thresholds are simulated assumptions for demonstration purposes. In a real firm they are approved by the board or the risk committee.

---

## 1. Purpose and scope

This document defines how market risk and counterparty credit risk are limited and monitored for a simulated electronic market-making book in Exchange Traded Products (ETPs).

It answers four questions:

1. How much risk is the desk allowed to take (limits)?
2. How do we know when the desk is approaching or exceeding that risk (monitoring zones)?
3. Who must be told, and what must happen next (escalation)?
4. How do we know the risk models behind the limits can be trusted (model validation)?

**Scope:** an 8-ETF book (SPY, QQQ, IWM, EEM, TLT, GLD, HYG, VGK) and three simulated counterparties (two clearing brokers, one prime broker).

---

## 2. Roles and responsibilities

The framework follows the usual "lines of defence" idea: those who take risk are separate from those who control it.

| Role | Responsibility |
|---|---|
| **Trading desk** (1st line) | Takes positions within limits. Runs a what-if check before adding large positions. Reports any expected breach in advance. |
| **Risk Associate** (2nd line) | Runs the daily monitoring, prepares the risk report and dashboard, flags AMBER and RED items, maintains this document and the model validation results. |
| **Senior Risk Officer** | Receives all AMBER and RED alerts. Decides on mitigation or on a temporary exception. |
| **CRO** | Receives all RED alerts (breaches). Approves exceptions, limit changes and model changes. |

---

## 3. Limit structure

Limits are set on several measures because each one captures a different kind of risk. A book can look safe on one measure and dangerous on another.

### 3.1 Market risk and exposure limits

| Metric | Definition | Limit | What it protects against |
|---|---|---|---|
| **1-day VaR 99%** | Loss that is exceeded on about 1 day in 100, from historical simulation | 250,000 $ | A typical bad day |
| **1-day ES 99%** | Average loss on the worst 1% of days | 400,000 $ | The size of losses beyond VaR (tail risk) |
| **Worst stress loss** | Largest loss across all historical and hypothetical stress scenarios | 3,500,000 $ | Severe, rare events that the past 10 years may under-represent |
| **Gross exposure** | Sum of absolute market values of all positions | 25,000,000 $ | Overall size of the book, including hidden risk in offsetting positions |
| **Net exposure (absolute)** | Absolute value of the sum of signed market values | 10,000,000 $ | Overall market direction |
| **Beta-adjusted net (absolute)** | Net exposure with each position scaled by its beta to SPY | 8,000,000 $ | Directional risk expressed in "SPY-equivalent" dollars |
| **Largest position as % of gross** | Largest single position divided by gross exposure | 30% | Concentration in one product |

### 3.2 Counterparty limits

For each counterparty, exposure is defined as **margin held + 95% Potential Future Exposure (PFE)** over a 10-day margin period of risk.

| Counterparty | Exposure limit |
|---|---|
| Clearing Broker A | 4,000,000 $ |
| Clearing Broker B | 1,200,000 $ |
| Prime Broker C | 1,500,000 $ |

Concentration across counterparties is also tracked with the Herfindahl-Hirschman Index (HHI), the sum of squared exposure shares. For three counterparties the minimum is 0.33 (perfectly spread) and the maximum is 1.00.

### 3.3 How the limit levels were chosen

The levels are illustrative. They were set so that the baseline book uses roughly 70-75% of each limit, which leaves room for normal inventory changes and keeps the AMBER zone meaningful. A real firm would calibrate limits to its capital, its risk appetite and its regulatory requirements.

---

## 4. Monitoring zones and escalation

For every metric, **utilisation = current value / limit**.

| Zone | Utilisation | Meaning | Required action |
|---|---|---|---|
| **GREEN** | below 80% | Normal operation | Routine monitoring |
| **AMBER** | 80% to below 100% | Early warning, limit not yet broken | Notify the Senior Risk Officer. Monitor closely during the day. Prepare mitigation (reduce or hedge the position). |
| **RED** | 100% or above | **Limit breach** | Escalate immediately to the Senior Risk Officer **and** the CRO. The desk must reduce risk or obtain a documented, time-limited exception. |

**Why an AMBER zone exists:** markets move fast, and reducing a large position takes time and costs money (wider spreads, market impact). A warning before the limit is reached gives the desk a chance to act in an orderly way. Waiting until the breach would mean selling under pressure.

**Breach record:** every RED event is logged with the following fields.

| Field | Content |
|---|---|
| Date and time | When the breach was detected |
| Metric | Which limit was broken |
| Value and limit | Size of the breach |
| Cause | Market move, new trade, model change |
| Action taken | Position reduced, hedge added, exception approved |
| Approved by | Name of the approver |
| Resolution time | When the book returned inside the limit |

Time-frames for notification (for example "same day" for AMBER, "immediately" for RED) are set by the firm. This document leaves them as policy choices rather than fixed numbers.

---

## 5. Pre-trade what-if check

Before a large trade is approved, the desk or the risk team enters the proposed positions in the dashboard (sidebar) and checks which limits would change zone.

**Worked example.** Adding about 4.5 million $ long in SPY (from 6,000 to 12,000 shares) moves the book from 8 GREEN and 2 AMBER to **6 RED, 2 AMBER and 2 GREEN**:

- RED: VaR (130%), ES (120%), worst stress loss (115%), net exposure (117%), beta-adjusted net (128%), largest position (139%).
- AMBER: gross exposure (87%) and Clearing Broker B (84%, unchanged because SPY is not carried there).

The first limit to break as the SPY position grows is the **concentration limit**, at roughly 7,200 shares (about 1,200 extra shares). The outcome of such a request is therefore either a refusal or a smaller size combined with a hedge, for example a short in another high-beta product to keep the beta-adjusted net inside its limit.

---

## 6. Model risk and validation

Limits are only as reliable as the models that measure them.

### 6.1 VaR backtesting

VaR is backtested out of sample: the VaR for day *t* uses only the 500 trading days before *t*, and is compared with the actual hypothetical P&L of day *t*.

Tests used:

- **Kupiec proportion-of-failures test:** is the share of exceptions statistically compatible with 1%? Reject the model if the p-value is below 0.05.
- **Basel traffic light** (250 days, 99% VaR): 0-4 exceptions GREEN, 5-9 YELLOW, 10 or more RED.
- **Clustering check:** exceptions per year, to see whether they concentrate in crisis periods.

### 6.2 Results (data to 3 November 2026)

| Method | Exceptions | Expected | Kupiec p-value | Last 250 days |
|---|---|---|---|---|
| Historical simulation | 38 | 24.8 | 0.013 (rejected) | 3 (GREEN) |
| Parametric (normal) | 53 | 24.8 | 0.000 (rejected) | 6 (YELLOW) |

Findings:

- Both models are rejected over the full sample. The normal assumption performs worse, which is consistent with fat tails in market returns.
- Exceptions cluster in 2020 (13 for historical simulation), because a 500-day window reacts slowly when volatility jumps.

### 6.3 Consequences for the framework

- **Historical simulation is the reference VaR**, and VaR is never used on its own. It is complemented by **Expected Shortfall** and by **stress tests**, which do not rely on a distribution.
- **Review triggers.** The VaR model is reviewed if the Kupiec test rejects it on a rolling basis, if the Basel traffic light turns YELLOW or RED, or after a major volatility regime change.
- **Possible improvements** documented for a later version: EWMA volatility weighting and filtered historical simulation, which give more weight to recent observations.

### 6.4 Stress testing

Stress tests answer a different question from VaR: "What would we lose if scenario X happened?" They carry no probability.

- **Historical scenarios:** ETF flash crash (Aug 2015), Q4 2018 sell-off, Covid crash (2020), rate shock (H1 2022), tariff shock (Apr 2025). The cumulative returns of each period are applied to today's positions.
- **Hypothetical scenarios:** equity -10% with flight to quality, rates +100bp, credit event with spreads +300bp, gold -10%. Factor shocks are translated to each ETF through beta, duration and spread duration.
- **Liquidity stress:** cost of closing the whole book if half-spreads widen tenfold. This figure is a lower bound because it ignores market impact.

---

## 7. Review cycle

- **Daily:** run the dashboard and the limit report, escalate AMBER and RED items.
- **Quarterly:** review limit levels against the book, capital and market conditions. Re-run the backtests.
- **Event-driven:** after any RED breach, any model-review trigger, or a change in the trading strategy or product set.

All changes to limits or models require CRO approval and a new version of this document.

---

## 8. Assumptions and limitations

This is a demonstration project. Reviewers should know the following.

- **Real:** daily adjusted prices from Yahoo Finance via `yfinance` (not an institutional data source).
- **Simulated:** positions, counterparties, margins, default probabilities (PD), loss given default (LGD = 60%), limits, roles and escalation chain.
- **Hypothetical P&L:** today's positions applied to historical returns, so intraday trading and changes in positions are not modelled.
- **Stress shocks** (durations, spread sensitivities, factor moves) are assumptions, not estimates fitted to data.
- **Counterparty model:** a bootstrap of 10-day returns, with no netting agreements and no collateral dynamics.
- **Liquidity:** fixed half-spreads, no market impact, no intraday liquidity.
- **No regulatory mapping.** The framework is not a substitute for the requirements of any specific regulator.