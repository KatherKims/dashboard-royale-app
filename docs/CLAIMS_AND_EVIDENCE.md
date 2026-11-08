# AceIQ — Claims & Evidence appendix

Updated November 7, 2026 against application commit `3271aaad8b6790e01d3e2f3985e71cb2dcc594f8` (`final`). This update changes evidence documentation and the in-app appendix, not the analytical calculations or retro layout.

All casino and player records are synthetic. Historical period: **January 1–June 30, 2025**. Decision horizon: **July 1–30, 2025**. Dollar findings below use the full historical period unless specified. July outcomes are unavailable. “Theo” means expected house win based on game math, before operating costs; it is not net profit.

## Conclusion supported by the evidence

**Do not automatically replace the ten lowest earners.** Their totals mix exposure, availability, demand and payout variation. M-1158 merits inspection, not a definitive defect diagnosis. For maximizing expected 30-day incremental contribution, the original limited simulation favors **preserving the $100,000** under its disclosed assumptions. This does not establish that every possible investment is unattractive or that inspection has no information value.

## Fit to the original guide

| Original question | Evidence | Boundary of the answer |
|---|---|---|
| Which machines underperform after exposure, availability and luck? | C1–C3; Investigate | Separates plausible explanations and inspection leads; does not prove a hardware defect. |
| What changed in demand, and why? | C4, C9–C11 | Quantifies change and context; causal explanations remain hypotheses. |
| How much play was lost to downtime, and when? | C5; monthly/daily availability in Investigate | Estimates machine-level missed-play opportunity and timing, not net recoverable floor revenue. |
| What did tracked players wager, receive and net, and how concentrated was it? | C6–C7; Guest & Loyalty Insights and appendix | Individual concentration is fixed six-month report evidence, now included in the appendix; group shares are a different measure. |
| What did comps cost, and did anything change? | C8 | Shows economic cost and redemption-ratio change; does not prove policy causality or program ROI. |
| What should the $100,000 fund, and how would we know it worked? | C12–C14; July Action Plan | Conditional preserve-budget recommendation and proposed evaluation plans; sandbox limitations remain. |

This mapping documents analytical coverage, not certification that every interaction or submission requirement is complete.

## Claims, sources and alternatives

The same claim records are available in **Methods & Evidence → Claims Appendix → Download claims appendix CSV** and `docs/CLAIMS_AND_EVIDENCE.csv`. Repository paths below are relative to the project root.

### C1. Historical money totals reconcile.

**Evidence:** data/analysis_results.json: validation; data/machine_daily.parquet; analysis/pipeline.py; notebooks/01_data_checks.ipynb.

**Finding / method:** January–June active machine-days: $248,905,219.25 wagers − $225,267,064.15 payouts = $23,638,155.10 actual house win. Expected house win (theo) is $23,545,364.48. Weighted hold = total house win / total wagers = 9.50%.

**Alternative / limitation:** Wagers include recycled winnings. Actual and expected house win are before operating costs, not net business profit. Reconciliation establishes arithmetic consistency, not accuracy of every source measurement.

**Decision / where to inspect:** Use consistent units and weighted ratios when comparing actual and expected results. Visible in Decision Center; fixed six-month totals here.

### C2. Low total earnings do not establish true underperformance.

**Evidence:** data/machines.parquet; data/machine_daily.parquet; data/daily_variance.parquet; app.py: build_machine_summary, machine_category.

**Finding / method:** 55,092 active rows out of 56,110 machine-days. M-5076 has 49 active days, M-1118 has 55 and M-1120 has 132. Compare availability, expected earnings per available hour, exposure and actual-minus-expected payout variation.

**Alternative / limitation:** Short exposure, lifecycle changes, downtime, low demand and payout luck can all lower totals. Peer comparisons do not fully control location or guest mix. Retired machines are not July replacement targets.

**Decision / where to inspect:** Investigate before replacing the bottom ten. Investigate recomputes selected-period evidence; full-period inspection screening is suppressed for restricted date ranges.

### C3. M-1158 is an inspection lead, not a proven faulty machine.

**Evidence:** data/machines.parquet; data/daily_variance.parquet; data/machine_daily.parquet; app.py: build_machine_summary.

**Finding / method:** January–June actual house win $15,796.25 versus theo $51,961.00: gap −$36,164.75, modeled standardized gap −4.57, downtime 3.01 hours. The selected June-only standardized gap is about −0.98.

**Alternative / limitation:** The standardized score assumes correct game math and modeled payout variance; it is not a defect probability. Random variation or recording/configuration error remain possible. Screening many machines is not corrected for multiple comparisons.

**Decision / where to inspect:** Inspect paytable/configuration and meter history before spending on replacement. Do not apply the six-month anomaly score to a one-month selection. Inspect the machine evidence in Investigate.

### C4. Demand per available machine-hour softened after February.

**Evidence:** data/analysis_results.json: monthly, zone_monthly, event_associations; data/property_daily.parquet; analysis/pipeline.py.

**Finding / method:** Monthly total wagers / total available machine-hours declined from $197.07 in February to $179.67 in June, about 8.8%. Zone and event comparisons provide descriptive context.

**Alternative / limitation:** Seasonality, events, machine mix, location and guest mix overlap. Associations and descriptive before/after movement comparisons do not establish a causal explanation. External context is not a causal control.

**Decision / where to inspect:** Investigate demand patterns before attributing low earnings to hardware. Decision Center and Investigate show selected-period context; the February–June comparison here is fixed.

### C5. Downtime creates estimated missed-play opportunity, not measured net floor loss.

**Evidence:** data/analysis_results.json: downtime; data/machine_daily.parquet; analysis/pipeline.py.

**Finding / method:** January–June downtime is 5,021.08 hours. Same-machine/weekday operating-rate quantiles, with fallbacks, imply midpoint missed wagers $990,374.55, sensitivity $856,353.76–$1,138,230.52, and midpoint missed theo $92,253.68.

**Alternative / limitation:** Visitors may switch machines, and downtime may fall in quiet hours. Quantile-based low/mid/high estimates are sensitivity cases, not statistical confidence intervals or guaranteed recoverable revenue.

**Decision / where to inspect:** Use monthly/daily availability evidence in Investigate to prioritize investigation. Evaluate maintenance using recovered availability and total-floor contribution, including displacement.

### C6. Tracked-player totals cover only part of casino play.

**Evidence:** data/analysis_results.json: players; data/guest_groups.parquet; analysis/pipeline.py: player aggregation.

**Finding / method:** Six-month totals: 113,890 distinct tracked players, $163,804,869.65 wagers, $148,219,409.05 payouts and −$15,585,460.60 player net. Tracked wagers cover 65.81% of machine wagers; 13.61% of tracked players finished ahead.

**Alternative / limitation:** Card users do not represent all visitors. Guest-page counts are player-months and cannot be summed into distinct six-month players. Partial date selections use complete included months, as disclosed in the UI.

**Decision / where to inspect:** Use Guest & Loyalty Insights for monthly group comparisons. Distinct-player, coverage and ahead-share figures above are fixed report findings, not dynamically filtered guest-page cards.

### C7. Tracked wagers and positive player losses are concentrated.

**Evidence:** data/analysis_results.json: players.top1pct_count, top1pct_wager_share, top1pct_positive_loss_share; analysis/pipeline.py.

**Finding / method:** Rank six-month totals by player: the top 1% (1,139 players) by wagers account for 22.86% of tracked wagers. A separate ranking by positive player loss accounts for 19.86% of positive losses.

**Alternative / limitation:** These rankings need not contain the same people. Positive-loss share is not share of net casino win. Region/age group shares on the guest page do not answer individual concentration.

**Decision / where to inspect:** These fixed report findings are available in this appendix and its CSV; the current guest page has no individual concentration cards. Do not use loss concentration to target heavy losers.

### C8. Comp redemption economics changed around May.

**Evidence:** data/analysis_results.json: loyalty; data/property_daily.parquet; analysis/pipeline.py: loyalty-ledger reconciliation.

**Finding / method:** January–June economic comp cost is $190,669.30. Weighted redeemed points per face-value dollar fell from 12.51 in April to 5.84 in May and 5.71 in June. Ledger aggregation uses the Las Vegas 6 a.m. gaming-day boundary.

**Alternative / limitation:** A change in redemption mix can alter the ratio without a uniform posted policy change. Face value differs from economic cost. Avoid subtracting comp costs twice when already included in a cost measure.

**Decision / where to inspect:** Investigate policy and redemption mix before claiming cause or loyalty-program ROI. Guest & Loyalty Insights shows monthly comparisons; evaluate changes using a controlled pilot.

### C9. The original property-level forecast beats a constant comparator in May–June.

**Evidence:** data/analysis_results.json: forecast; analysis/pipeline.py: property forecast; app.py: July Demand Outlook headline metrics.

**Finding / method:** Fit January–April; compare predictions with May–June floor-wide daily wagers. Weekday MAE is $68,698.55 versus $218,258.10 constant MAE (68.52% lower). January–June refit gives a July 1–30 wager scenario of $40,711,161.62.

**Alternative / limitation:** May–June errors also select the winning method, so this is not an untouched final test of an independently selected winner. July has no actual outcomes. The adjacent April-selection explanation describes a different model (C10).

**Decision / where to inspect:** Label these as the original property-level results. Do not pair their 68.52% improvement with the newer model’s selection protocol or interpret the July scenario as validated realized demand.

### C10. The newer machine-level model has a separate validation protocol.

**Evidence:** data/forecast_metadata.json; data/demand_predictions.parquet; dashboard/forecast.py; scripts/build_dashboard_data.py.

**Finding / method:** Fit January–March, select on April, refit January–April, freeze May–June predictions. Machine-day MAE $934.98 versus $1,121.28 baseline (16.6% lower), WAPE 21.24%. Retained floor aggregation gives MAE $99,117.16 versus $231,842.16 and illustrative band coverage 62.3%.

**Alternative / limitation:** These are not C9’s model or error scale. April selects the model and calibrates 10th–90th percentile bands; 62.3% coverage is below nominal 80%. Active roster is supplied; one unseen test machine uses a fallback. No July actuals exist.

**Decision / where to inspect:** Use the saved machine diagnostics separately from the original headline forecast. The current July diagnostic chart incorrectly turns missing actuals into zeros; disregard that Observed series until corrected.

### C11. The current floor view is a bank-level schematic.

**Evidence:** data/floor_locations.parquet; data/floor_walkways.parquet; data/placements.parquet; app.py: build_location_lookup and selected-period bank summaries.

**Finding / method:** Supplied bank coordinates locate bank aggregates. Selected-period machine evidence uses dominant bank/zone metadata; placement history supports descriptive movement comparisons.

**Alternative / limitation:** This is not the earlier dated, slot-level occupancy simulator. It does not demonstrate executed moves, movement uplift, or validated power/accessibility/capacity feasibility. Historical bank membership is not necessarily July placement.

**Decision / where to inspect:** Use the map to locate patterns and choose an investigation target. Do not claim 308 occupied slots, six empty slots, animated machine moves or causal location effects from the current visible map.

### C12. Preserve Budget ranks first in the stored, limited Monte Carlo comparison.

**Evidence:** data/analysis_results.json: simulation; data/scenario_net.npz; analysis/pipeline.py: candidate effects and portfolio enumeration.

**Finding / method:** 1,000 scenarios, seed 20251107, nine spending candidates and 42 feasible portfolios. At most three action types and $100,000 catalogue cash budget. Keep-budget incremental net is $0; all spending candidates have negative modeled means. Next-best single candidate is comp-policy change at −$1,028.37 mean.

**Alternative / limitation:** Effects and retained-play fractions are assumptions, not measured intervention outcomes. The shortlist is not exhaustive; inspection information value is unpriced. These saved results do not rerun when dates or sandbox controls change.

**Decision / where to inspect:** For the stated 30-day objective, preserve funds under the stored assumptions; consider a separately justified learning action. July Action Plan displays this original comparison, not a live DecisionEngine optimization.

### C13. The interactive action sandbox is a separate what-if calculation.

**Evidence:** app.py: estimate_action_sandbox, plan_budget_used, add_to_plan; data/analysis_results.json: action_catalog.

**Finding / method:** Selected historical rates, catalogue prices/lead times and user assumptions produce low/base/high contribution estimates. Planned downtime is deducted from economic benefit. Custom tray actions do not join the stored 42-portfolio ranking.

**Alternative / limitation:** The ranges are sensitivities, not Monte Carlo confidence intervals. The tray currently counts downtime opportunity against cash budget. Its comp-policy estimate omits the original simulation’s demand-loss penalty. Successive action selections also reset in an automated interaction check.

**Decision / where to inspect:** Verify the selected action and compute cash budget separately before acting. M-1158 inspection costs $1,200 cash plus $23.95 opportunity cost; correct cash remaining is $98,800, although the tray reports about $98,776.

### C14. Evaluation plans are proposed; no intervention effect has been measured.

**Evidence:** app.py: action measurement plans; analysis/pipeline.py; notebooks/01_data_checks.ipynb; this appendix’s evaluation table.

**Finding / method:** Predefine target, untreated comparison, timing, cash cost and a contribution/availability outcome. Monitor whole-floor play for displacement and inspect meter/configuration evidence for anomalies.

**Alternative / limitation:** No randomized action trial, verified repair effect or July intervention outcome exists in these exports. Thirty days may be underpowered. A favorable simulated result is not proof that an intervention works.

**Decision / where to inspect:** Use the dashboard to choose and design a test, then evaluate genuinely new evidence. Databricks supports the notebook/analysis provenance; the dashboard reads local exports and has no live Databricks or Gemini API connection.

## Keep the two forecast versions separate

| Item | Original property-level model | Newer machine-level model |
|---|---|---|
| Saved evidence | `analysis_results.json: forecast` | `forecast_metadata.json`; `demand_predictions.parquet` |
| Target | Floor-wide daily wagers | Machine-day wagers; can be aggregated |
| Selection | Choose weekday versus constant using May–June errors after January–April fit | Fit January–March; select on April |
| Evaluation | May–June out-of-sample predictions, also used for selection | January–April refit; frozen May–June test |
| Main result | $68,698.55 MAE vs $218,258.10 | $934.98 machine-day MAE vs $1,121.28 |
| Current app use | Main July Demand Outlook headline and original stored scenario context | Additional diagnostics and method text on the same page |
| July | Refit January–June; scenario only | Refit January–June; forecast only |

The current method panel and primary scorecards are not consistently version-labeled. C9 and C10 provide the correct attribution; this appendix does not repair that UI mismatch. The newer daily bands are illustrative and do not form a 30-day profit interval. The original simulation largely uses historical operating rates: it does not convert every newer forecast prediction into an optimized action.

## What the original Monte Carlo comparison assumes

`analysis/pipeline.py` generates 1,000 scenarios using seed `20251107`. It samples January–April fitted-demand residual ratios into 30-day averages and shares demand/retention draws across candidate comparisons. Effects are stipulated, not estimated treatment effects:

| Assumption | Distribution / treatment |
|---|---|
| Retained incremental floor play | Triangular 25%, 50%, 100% (minimum, mode, maximum) |
| Machine move uplift | Triangular −10%, 20%, 60% |
| Leased-title uplift | Triangular −10%, 50%, 150% |
| Technician recovery of downtime opportunity | Triangular 10%, 30%, 60%; assumes one shift can address the modeled scope |
| Preventive-maintenance recovery | Triangular 20%, 50%, 80% |
| Signage uplift | Triangular 0%, 2.5%, 8% |
| Comp-policy savings / demand-loss penalty | Savings triangular 0%, 10%, 25%; theo-loss fraction triangular 0%, 0.05%, 0.2% |
| Inspection and comp-pilot monetary benefit | No recovery credited without an effect estimate; information value is not monetized |

Catalogue lead times reduce benefit days; catalogue cash and planned downtime opportunity reduce incremental net. Feasible portfolios use at most three action types, enforce the cash ceiling, and exclude coded overlaps/incompatibilities. The nine-candidate shortlist uses one catalogue unit per candidate and does not explore all quantities, destinations or purchases. Scenario probabilities are conditional on these assumptions, not empirical success rates. Candidate samples in `scenario_net.npz` are distinct from the 42 portfolio combinations; candidate order is defined by the original pipeline and report.

The latest app's custom sandbox uses selected historical rates and user-controlled sensitivity assumptions. It does not rerun these Monte Carlo draws or the stored portfolio ranking. In particular, its comp-policy calculation omits the original simulation's demand-loss penalty. Do not describe the current app as using the retained `dashboard/decisions.py` shared engine for its displayed official recommendation.

## How we would know an action worked

| Action | Predefined comparison and evidence | Success criterion |
|---|---|---|
| Preserve budget / monitor | Track availability, expected earnings per scheduled hour and payout diagnostics; evaluate forecast errors on genuinely new outcomes. | Reconsider when new evidence changes the cost-benefit case. No cash uplift is claimed from doing nothing. |
| Inspect | Verify configured game math, meter reconciliation, repair records and any corrections. | A verified discrepancy is resolved; random payout recovery alone is not proof. Price corrective work separately. |
| Move / replace / signage | Compare treated machines or banks with matched untreated controls over the same dates; record downtime and whole-floor play. | Incremental contribution after cash cost and downtime exceeds zero with uncertainty reported, including displacement. |
| Maintenance / staffing | Compare unavailable hours, repeat faults and contribution per scheduled hour with an untreated group. | Recovered availability and positive incremental contribution after costs, beyond background demand change. |
| Comp pilot | Randomize eligible participants where feasible; measure economic comp costs and incremental contribution. | Positive contribution after costs with uncertainty; avoid targeting high-loss players. |

These are proposed plans, not completed experiments. Set comparison groups, material effect thresholds, sample size and stopping rules before implementation. Thirty days may be insufficient; an inconclusive result does not demonstrate success or failure.

## Scope, provenance and verification

- Date controls affect machine/property evidence. The concentration and distinct-player findings here remain January–June; guest group exports cover whole months and contain player-month counts. Forecast evaluation windows and the original portfolio ranking stay fixed.
- `analysis/pipeline.py` reproduces original exports from the raw challenge inputs. `scripts/build_dashboard_data.py` produces the retained machine forecast, placement and variance extensions. Source hashes are recorded in the report/metadata; the current `app.py` does **not** enforce the earlier runtime hash-mismatch guard.
- `notebooks/01_data_checks.ipynb` preserves original Databricks analysis. The later `notebooks/02_Floor_and_Forecast.ipynb` and shared modules retain extension work, but their presence does not prove every feature is used by the latest UI or was executed in Databricks. The reviewed app reads local exports; it does not query Databricks live.
- Gemini chat is **not implemented**. Do not claim Gemini integration or describe the numerical models as generative AI. See `AI_DISCLOSURE.md` for the separate tool-use disclosure.
- Review of application commit `3271aaa`: all six pages rendered at the default period; a complete June range and bank B-01 drilldown rendered; three original numerical export-consistency tests passed. These checks do not establish causal validity, full accessibility or error-free interaction. The repository's older `tests/test_app.py` targets a previous UI and is not evidence of current end-to-end coverage.
- This update leaves styling, analytical calculations and deployment unchanged. Public judge access is a separate pending task; no public URL is verified by this appendix.

## Known limitations in the reviewed application

These remain open; documenting them is not a code fix.

| Issue | Effect on interpretation or use |
|---|---|
| Incomplete date-range selection can crash | A one-date tuple is converted to a timestamp; completed date ranges worked in review. |
| July diagnostic actuals become zero | All July actuals are missing, but ordinary grouped sum creates zeros and an Observed line. Do not interpret it as measured July play. |
| Forecast versions are mixed in the explanation | Attribute headline metrics to C9 and machine diagnostics/protocol to C10. |
| Action tray mixes cash and opportunity cost | Check catalogue cash separately against $100,000. Keep planned downtime as an economic cost in net benefit. |
| Action selection can reset | Sequential AppTest changes sometimes retained the previous choice. Verify the displayed action before adding it; the exact browser sequence was not independently reproduced. |
| Individual concentration is not a guest-page card | C6–C7 and the downloadable appendix contain the fixed-period findings; monthly group charts do not replace them. |

The retro identity and current page structure are retained. These limitations concern analytical labeling and interaction correctness, not a request for another visual redesign.
