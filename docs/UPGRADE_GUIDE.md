# AceIQ: interface, forecasting and floor-map update

This version combines the teammate's AceIQ presentation with corrected analytics and modular additions. The source attachment remains unchanged. The existing `01_data_checks` notebook and saved original scenario exports are preserved as version 1 evidence. This update was built and tested locally and shared in the team GitHub repository. It has not been deployed publicly or executed in the Databricks workspace.

## Walk through it together

Machine availability now starts with a plain-language summary and a monthly chart of unavailable time. Switch to Day for the timing of individual daily totals, inspect the largest daily interruption total, and open the readable table/CSV. The percentage is total available hours divided by total scheduled hours, including daylight-saving day lengths. Availability means ready for play, not actual player usage. This presentation change does not alter the underlying downtime estimates.

1. Start the app using the README instructions. On **Executive overview**, change the evidence dates. Machine and property totals update. Whole-period player headline statistics and event associations explicitly retain their own January–June reference period. Monthly guest and loyalty summaries explicitly use complete months.
2. Open **Predictions vs actual**. Choose the whole floor, a zone, bank or machine. Compare the frozen May–June demand predictions with observed wagers and the constant baseline. The residual chart shows when the model missed. Switch to July to view a forecast without invented actuals.
3. On **Machine investigation**, filter a bank, compare rankings and select a machine. Payout variance and the screening score now use the selected evidence period. Scores are screening clues, not confirmed faults or multiple-testing-adjusted findings.
4. Open **$100,000 decision lab → Floor map & simulator**. Historical mode resolves machine positions at 06:00 Las Vegas time on the chosen date. Colors summarize the evidence period. Position dates and evidence dates are labeled separately.
5. Switch to **Plan July actions**. Select a machine on the map or with the dropdown. Select a catalog action; a move additionally requires an empty slot. The map highlights the action scope and destination. Review cash cost, planned downtime opportunity cost, expected incremental benefit, percentiles and conditional probability of a positive return.
6. Open **Portfolio ranking**. Adjust budget, objective or benefit sensitivity. This compares the original nine candidates through the same engine used by the map. Custom map experiments do not automatically enter the shortlist.

## How the prediction model works

The target is **daily wagers per active machine**. It is not a spin simulator and does not predict realized payout profit. Two models compete:

- Constant: the machine's average daily wagers in the training period.
- Weekday: the machine's weekday history, smoothed toward its average × a floor weekday factor. The fixed smoothing weight is 10 observations. New machines fall back to their theme average.

January–March fits the candidates. April selects the model by machine-day mean absolute error (MAE). The selected specification is refit on January–April and evaluated on May–June without using test-period wagers, actual uptime, future weather or event outcomes as predictors. The supplied active-machine roster defines which days are forecast; this is not a model of future installation/retirement decisions.

The weekday model won April selection. On the final May–June holdout:

| Measure | Result |
|---|---:|
| Constant model machine-day MAE | $1,121.28 |
| Weekday model machine-day MAE | $934.98 |
| Reduction in machine-day MAE | 16.6% |
| Machine-day weighted absolute percentage error | 21.24% |
| Machines unseen in final training period | 1 |

These are machine-level errors, not the older notebook's aggregate-floor forecast errors. Do not interchange the two comparisons. The app calculates scope-specific aggregate errors and warns if the selected model loses to the baseline for that scope.

July refits the winning specification on January–June. No July actuals exist. April residuals provide illustrative daily 10th–90th percentile bands for each scope, with actual holdout coverage displayed. April also selected the model, and regimes can change: these are approximate empirical bands, not guaranteed prediction coverage. Fewer than 14 calibration days suppresses the band. Bands aggregate residuals by date to preserve observed cross-machine dependence; they are not a 30-day total-return interval.

## How predictions connect to decisions

For move, lease and signage scenarios, the July wager forecast is multiplied by each machine's historical configured hold to estimate baseline expected earnings. Intervention assumptions multiply this baseline only after catalog lead time. This assumes the historical game mix/hold remains representative; a new title's actual math is not yet known.

Maintenance uses estimated historical downtime opportunity per calendar day across the correct scope, multiplied by remaining benefit days and an assumed recovery fraction. A $9,000 preventive sweep covers an eligible manufacturer group, not one machine. Planned downtime is charged for every affected machine.

Both map and portfolio calculations call `DecisionEngine.evaluate`. All actions share repeatable demand and retained-play draws. Moving a slider changes the assumptions without changing the underlying seeded random quantiles. A 1,000-scenario demand multiplier spans 0.85–1.15; intervention and retained-play effects are triangular assumptions, **not fitted causal effects**. The new engine's results can differ from the original notebook because it now uses the machine-demand forecast and a documented common demand assumption. Version 1 results remain untouched for provenance.

Net benefit = additional expected earnings − action cash cost − planned downtime opportunity cost. Inspection and pilot financial recovery remain zero unless supported by a verified corrective-effect estimate. Keeping the budget is a neutral $0 incremental reference. All probabilities are conditional on assumptions; they are not measured success rates.

## Floor-map boundaries

- Supplied `floor_locations` coordinates and effective-dated `placements` determine positions. Retirement and installation dates also constrain occupancy. Placement end times are exclusive.
- July 1 resolves to **308 occupied slots and 6 empty slots**. The broader six-month dataset includes 310 machines because machines enter or leave the floor.
- The map draws schematic zone connections from `floor_walkways`. A known closure is marked at the snapshot instant; straight lines are not measured physical routes.
- Empty slots are allowed move targets; occupied slots are not. Swaps and moves of whole banks are not implemented.
- July interventions require eligibility and at least 28 observed active days. Physical compatibility, power, accessibility, staffing and other operating feasibility still need human review.
- Zone wager-rate differences are context, not an automatic causal uplift. A destination does not silently increase the modeled move benefit. The user must supply an explicit uplift assumption.
- Historical colors describe the evidence-period totals for each machine, not earnings caused by its displayed slot.

## Code ownership and extension points

| File | What to change here |
|---|---|
| `app.py` | Teammate's branding, overview, guest/comp presentation and machine investigation |
| `dashboard/analytics.py` | Date-aware summaries, screening and placement resolution |
| `dashboard/forecast.py` | Fit/predict logic, holdout protocol and error bands |
| `dashboard/decisions.py` | Shared action math, catalog costs, eligibility and portfolio constraints |
| `dashboard/views.py` | Forecast controls, floor rendering, map interaction and decision presentation |
| `scripts/build_dashboard_data.py` | Rebuild small forecast, variance and floor exports |
| `notebooks/02_Floor_and_Forecast.ipynb` | Reproduce the new model and decision calculations from the repo |
| `tests/test_upgrade.py` | Numeric and leakage regressions |
| `tests/test_app.py` | Streamlit user journeys |

Good next additions for either teammate: compare two saved map scenarios; add a proposal tray with validated combined budget/overlap rules; add richer pixel cabinet art; add a human-readable model explanation; or implement Gemini chat against explicitly allowed aggregate-data functions. Gemini is **not integrated yet**.

Keep new action formulas in the shared engine rather than duplicating them in the UI. Keep actual outcomes, game-math expectations, demand predictions and intervention assumptions distinctly labeled.

## Rebuild and validate

After running `analysis/pipeline.py` on the challenge data:

```powershell
python scripts/build_dashboard_data.py --source "C:\path\to\dashboard-royale\data" --output data
python tests/test_results.py
python tests/test_upgrade.py
python tests/test_app.py
python -m streamlit run app.py
```

The app checks that the daily-data hash matches the forecast export and rejects stale combinations. The original cloud notebook has not been updated in this turn. After refreshing original Databricks exports, rebuild the extension exports before launching the new app. To execute the new notebook in Databricks, first open the updated repository in a Databricks Git folder, then run its cells against the included data. The included raw floor metadata is synthetic; no raw player identities or credentials are exported.

The map uses Streamlit's documented Plotly selection callback: [official API reference](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart).
