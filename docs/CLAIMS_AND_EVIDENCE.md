# Claims & Evidence · local rebuild

Updated November 8, 2026 for the rebuild based on `08dab59`, integrated on top of `25e345f`. This supersedes the baseline appendix for the current interface. Synthetic history: January–June 2025; modeled planning: July 1–30. Sources, original exports, shared financial definitions and forecasts are unchanged.

## Original guide coverage

Underperformance: C1–C3. Demand change and context: C4/C8. Downtime and timing: C5. Tracked outcomes and concentration: C6. Comp costs/change: C7. The $100,000 decision and evaluation: C10–C14. Floor context: C9. This is evidence coverage, not a claim of causal identification or a public deployment.

## C1 · Historical money reconciles

**Evidence:** machine_daily.parquet; analysis_results.json; pipeline.py

**Finding / method:** $248,905,219.25 wagers − $225,267,064.15 payouts = $23,638,155.10 actual house win. Theo $23,545,364.48; weighted hold 9.50%.

**Alternative / limitation:** January–June active records. Wagers include recycled winnings; earnings are before operating costs.

**Inspect:** Overview; tests/test_results.py

## C2 · Raw bottom ten mix exposure, availability and luck

**Evidence:** machine_daily.parquet; machines.parquet; daily_variance.parquet

**Finding / method:** M-5076 has 49 active days, M-1118 55, M-1120 132. Selected-period rates and payout scores are recomputed.

**Alternative / limitation:** 55,092 active records of 56,110 original machine-days. Rates/peers do not establish causality.

**Inspect:** Machines; analytics.machine_summary

## C3 · M-1158 merits inspection, not a defect verdict

**Evidence:** machines.parquet; daily_variance.parquet

**Finding / method:** Full-period actual $15,796.25 vs theo $51,961.00; gap −$36,164.75, modeled standardized gap −4.57, downtime 3.01 hours.

**Alternative / limitation:** Variance assumptions and multiple-machine screening matter. June-only score is about −0.98. Verify meters/configuration before irreversible action.

**Inspect:** Machines → M-1158

## C4 · Exposure-adjusted demand softened after February

**Evidence:** analysis_results.json: monthly, event_associations, traffic

**Finding / method:** $197.07 wagers/available machine-hour in February vs $179.67 in June: about 8.8% lower.

**Alternative / limitation:** Events, placement, seasonality and machine mix overlap. Why remains a set of hypotheses, not a proven causal finding.

**Inspect:** Overview trends and demand-context expander

## C5 · Downtime is an opportunity estimate

**Evidence:** analysis_results.json: downtime; machine_daily.parquet

**Finding / method:** 5,021.08 unavailable hours; midpoint missed wagers $990,374.55; sensitivity $856,353.76–$1,138,230.52; missed theo $92,253.68.

**Alternative / limitation:** Guests may switch machines. Quantile sensitivity is not a confidence interval or guaranteed recoverable floor revenue.

**Inspect:** Machines → monthly availability and daily outages

## C6 · Tracked play is partial and concentrated

**Evidence:** analysis_results.json: players; guest_groups.parquet

**Finding / method:** 113,890 distinct tracked players: $163,804,869.65 wagers, $148,219,409.05 payouts, −$15,585,460.60 net. Coverage 65.81%; top 1% wager share 22.86%, separately ranked positive-loss share 19.86%.

**Alternative / limitation:** Distinct/concentration values are fixed full-cohort January–June results. Filtered group counts are player-months. Guest monthly totals use whole included months and region.

**Inspect:** Guests; fixed-cohort concentration panel

## C7 · Comp economics changed around May

**Evidence:** analysis_results.json: loyalty; pipeline.py

**Finding / method:** $190,669.30 property economic comp cost; points/face-value dollar 12.51 April, 5.84 May, 5.71 June.

**Alternative / limitation:** Redemption mix can change without a universal policy change. Economic cost differs from face value; do not double-subtract comps. Property comp panel is all regions.

**Inspect:** Guests → property comp economics

## C8 · Forecast protocol and metrics now use one machine-level version

**Evidence:** forecast_metadata.json; demand_predictions.parquet; dashboard/forecast.py

**Finding / method:** January–March fit, April selection, January–April refit, frozen May–June test: machine-day MAE $934.98 vs $1,121.28, WAPE 21.24%.

**Alternative / limitation:** One unseen test machine uses fallback; supplied roster is not predicted. Illustrative April bands are imperfect. Original property-model 68.52% improvement is historical, not this score. No July actuals plotted.

**Inspect:** Scenarios → holdout; Methods dialog

## C9 · Floor placements are time-valid; art and guests are decorative

**Evidence:** floor_locations.parquet; placements.parquet; analytics.floor_snapshot

**Finding / method:** July 1 at 06:00 Las Vegas: 308 occupied supplied slots and six vacant. Real coordinates place original machines. Swaps preserve both identities and roster.

**Alternative / limitation:** Decorative rooms, guests and relocation curves do not model customer movement or validate physical feasibility. Original configurations remain associated with machine identity; additions use a labeled proxy.

**Inspect:** Floor lab; tests/test_upgrade.py; tests/test_floor_simulation.py

## C10 · Shared catalogue actions reconcile across tools

**Evidence:** dashboard/decisions.py; dashboard/floor_simulation.py

**Finding / method:** Existing 1,000 deterministic draws and July forecast baselines are reused. Every tested catalogue action and swap matches shared-engine day-30 net samples; cash stays separate from downtime.

**Alternative / limitation:** Effect distributions are assumptions, not learned causal effects. Daily benefit allocation follows forecast shares (maintenance spread over active days), not an intraday response model.

**Inspect:** Scenarios; floor preview, confirmation, playback and export

## C11 · Search scope changes the recommendation

**Evidence:** dashboard/decisions.py: shortlist; floor_simulation.suggestions

**Finding / method:** The original nine-target shortlist favors keep-budget. The wider individually feasible floor search can return positive modeled move/lease/maintenance options against the current plan.

**Alternative / limitation:** Not globally optimized combinations or layout. Moves use the first legal vacancy, not a location-specific uplift estimate. Add/remove and swaps are outside suggestions.

**Inspect:** Scenarios → shortlist; Manage → Suggested changes

## C12 · Add/remove are explicit what-if extensions

**Evidence:** dashboard/floor_simulation.py: action_daily

**Finding / method:** Entered cash paid upfront. Addition = eligible proxy forecast × triangular(0.5,1,1.5) × entered incremental share × existing demand draw. Removal loses forecast × (1−retained share) × demand after activation.

**Alternative / limitation:** No invented resale, operating or lease savings. NEW- identities are hypothetical and do not rewrite sources. Extension results do not appear in official nine-candidate history.

**Inspect:** Floor composer, preview assumptions, daily export

## C13 · All floor plans pass centralized constraints

**Evidence:** floor_simulation.validate; floor_server.py

**Finding / method:** $100,000 cash, maximum three types including extensions, catalogue quantities, nonoverlapping target sets, legal destinations, unique reservations, removal/arrival timing. Swap uses two move units.

**Alternative / limitation:** This validates modeled constraints, not engineering, access, licensing or operational feasibility. Browser plans are transient. Refresh resets; exports are manual local downloads.

**Inspect:** tests/test_floor_simulation.py; tests/test_floor_api.py

## C14 · No real intervention effect or API integration is claimed

**Evidence:** notebooks/01_data_checks.ipynb; data_bundle.py; run_local.py

**Finding / method:** Historical Databricks notebooks and exports are retained. Runtime reads local files. Gemini chat and live Databricks queries are not implemented.

**Alternative / limitation:** Proposed tests need untreated controls, predefined dates and contribution/availability outcomes. Monitor floor-wide displacement; 30 days may be underpowered.

**Inspect:** Methods dialog; README; AI_DISCLOSURE.md

## How to evaluate an action

Inspect settings and meter reconciliation for anomalies; random payout recovery alone is not proof of repair. For moves, replacements and signage, compare treated units with matched untreated units over the same dates and check whole-floor play for displacement. For maintenance, measure availability, repeat faults and contribution per scheduled hour. For comp changes, use a controlled pilot and measure incremental contribution after economic comp cost, without targeting heavy-loss players. Predefine sample size, minimum useful effect and stopping rules. These experiments have not been run.

## Version boundary

`analysis_results.json` and `scenario_net.npz` preserve the original version-1 pipeline. The rebuilt UI uses the retained shared DecisionEngine for current calculations, not those older stored candidate arrays. Both are seeded 1,000-scenario systems with different demand/effect construction; do not mix their values. Source hashes are recorded, but the new loader does not claim a runtime cryptographic integrity gate. See LOCAL_REBUILD for performed checks and residual limitations. No July actuals or real intervention effects exist.

## Reference comparison update

See [REFERENCE_COMPARISON.md](REFERENCE_COMPARISON.md) for the PDF-to-current-chart mapping and independent reconciliation checks. New evidence views use the existing exports and definitions. The optional claw chooses a raw-bottom-ten machine for investigation and makes no analytical recommendation.


## Public Streamlit Floor Lab update

AI-assisted implementation added `dashboard/cloud_floor.py` and routed dashboard floor links to the same Streamlit app. It exposes the existing FloorSimulation engine through form controls, a supplied-coordinate map, July day selection, preview/confirmation, undo, suggestions and downloads. Drag-and-drop and decorative walking guests remain local SVG features. Financial models and datasets are unchanged. Databricks verification is pinned to application revision 2a124ca and does not claim to validate this later UI addition.
