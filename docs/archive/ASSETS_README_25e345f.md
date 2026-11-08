# The Gilded Ace

## ACEIQ Casino Decision Dashboard

The Gilded Ace is a Streamlit dashboard built with Python and synthetic casino data.

It helps users explore machine performance, downtime, floor placement, demand trends, loyalty results, and possible July operating decisions. The dashboard is designed to show that low earnings alone are not enough to make a replacement decision.

All data in this project is synthetic.

---

## Dashboard sections

### Decision Center

A high level view of the property.

This section includes:

- Total wagers and house earnings
- Actual earnings compared with expected earnings
- Downtime opportunity
- Low earning machines
- Payout variation context
- Demand trends over time

The goal is to identify machines that may need a closer look without assuming that every low performer should be replaced.

### Investigate

Select a machine and review its performance in more detail.

This section includes:

- Actual and expected earnings
- Availability and downtime
- Cumulative performance over time
- Payout variation context
- Same theme or same zone peer comparisons
- Placement and floor context
- Bank movement history when available

### July Action Plan

Compare possible July actions using the local action catalog.

This section includes:

- A $100,000 budget limit
- Action costs
- Lead times
- Planned downtime
- Action quantity limits
- Low, base, and high planning cases
- A tray for saving actions to compare

The planner helps compare options. It does not guarantee an action will produce a specific result.

### July Demand Outlook

Review demand forecasting and demand context.

This section includes:

- Forecast holdout results
- Model comparison
- July planning baseline
- Event period comparisons
- Zone traffic context
- Machine demand prediction diagnostics

### Guest and Loyalty Insights

Review grouped loyalty and comp information.

This section includes:

- Tracked player activity
- Wagers and payouts
- Player net
- Expected player loss
- Comp costs
- Comp face value
- Comp cost trends

Guest information is grouped and does not include player identifiers.

### Methods and Evidence

Review how the dashboard works and download supporting data.

This section includes:

- Machine performance methods
- Downtime methods
- Official simulation results
- Data quality checks
- Claims appendix
- Downloadable CSV files

---

## Data

This project uses local synthetic data only.

Required files inside the `data/` folder:

```text
analysis_results.json
machines.parquet
machine_daily.parquet
guest_groups.parquet
property_daily.parquet
scenario_net.npz