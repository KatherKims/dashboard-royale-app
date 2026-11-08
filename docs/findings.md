# Findings and decision notes

**Historical version-1 notes.** Current forecast/scenario results and product status are in [CLAIMS_AND_EVIDENCE.md](CLAIMS_AND_EVIDENCE.md). The older forecast and candidate values below are retained for provenance and must not be presented as the current dashboard model.

Synthetic casino data, January 1–June 30, 2025. Planning horizon: July 1–30. These findings use the supplied data release, whose hashes appear in `data/analysis_results.json`.

## 1. Replacing the lowest-total-earnings machines is not supported

There are 56,110 machine-day rows, of which 55,092 are active. Raw totals mix machines with very different time on the floor. M-5076 was active for only 49 days; M-1118 for 55, and M-1120 for 132. Retired machines are excluded from July action targets.

M-1158 earned $15,796.25 against $51,961 expected, a gap of −$36,164.75. Its modeled payout gap is approximately −4.57 standard deviations, but downtime was only about 3.0 hours. Review configuration and meters: neither ordinary downtime nor the ranking alone establishes the cause. The variance calculation assumes independent spins and correct game math; it is not a corrected significance test across all 310 machines.

Peer comparisons use expected earnings per available hour within the same theme. They are descriptive; differences in location, denomination, occupancy and guest mix can remain. A poor peer rank does not prove replacing the hardware will help.

## 2. Demand softened after the early-year peak

Wagers per available machine-hour were $187.45 in January, $197.07 in February, $195.33 in March, $186.82 in April, $188.42 in May and $179.67 in June. June was about 8.8% below February on this exposure-adjusted measure. Month lengths alone do not explain the change.

Weekday-adjusted event associations and zone comparisons are included in the app. They cannot distinguish event effects from seasonality or other concurrent changes. Sensor entries are not unique visitors; covered hours, missing intervals and coverage shares are reported. No causal explanation for the demand trend has been established.

A weekday forecast trained on January–April achieved May–June mean absolute error of $68,699 per day, versus $218,258 for a constant average: a 68.5% reduction. Model selection uses the held-out period. A subsequent full-period refit yields a July 1–30 baseline of $40.71 million in wagers; this is a planning forecast, not an observed result.

## 3. Downtime opportunity is much smaller than wagers

There were 5,021.1 unavailable hours on active machine-days. Same-machine, same-weekday hourly wager rates imply a historical wager opportunity of $990,375, with a sensitivity range of $856,354–$1,138,231. The middle expected-earnings opportunity is $92,254 before costs over all six months.

These are machine-level counterfactuals, not proven net floor losses. Players may switch machines. Quantiles describe different operating-rate assumptions, not a confidence interval. The calculation uses raw scheduled/available seconds, including daylight-saving day lengths. The app shows the monthly timing and machine detail.

## 4. Tracked play is concentrated and incomplete

113,890 tracked players wagered $163,804,869.65 and received $148,219,409.05, giving aggregate player net of −$15,585,460.60. Tracked play covered 65.81% of all wagers; 13.61% of tracked players finished ahead on recorded six-month play.

The top 1% by six-month wagers (1,139 players) contributed 22.86% of tracked wagers. A separately ranked top 1% contributed 19.86% of positive player losses. These are different rankings. Group comparisons by region and age are descriptive and contain no individual player identifiers in app exports.

## 5. Redemption economics changed around May

Total economic comp cost was $190,669.30. The observed weighted points redeemed per face-value dollar fell from 12.51 in April to 5.84 in May and 5.71 in June. That means fewer points were redeemed per dollar of guest benefit, but it does not prove a uniform posted policy or its causal effect on demand.

Economic cost is distinct from comp face value. Loyalty redemption costs reconcile to property totals after converting UTC timestamps to Las Vegas local time and applying the 6 a.m. gaming-day boundary.

## 6. The chosen 30-day objective favors retaining the budget in this shortlist

The objective is **maximum mean incremental expected contribution**, after cash costs and planned downtime. The model compares 42 admissible portfolios from nine explicit candidates against keeping the budget, using 1,000 shared scenarios and seed 20251107. It enforces the $100,000 cap, at most three action types, catalogue lead times, costs and conservative target-overlap exclusions.

Under the documented assumptions, all spending candidates have negative mean 30-day net benefit. Keep-budget has $0 incremental cost and $0 incremental benefit, so it ranks first. This is a limited-shortlist result, not proof that every possible action or quantity is unattractive. The app compares mean, 10th-percentile and conservative objectives and exposes a sensitivity multiplier.

Illustrative candidate means: inspect M-1158 −$1,224 including planned downtime; move the weakest eligible rate performer −$1,245; lease −$2,539; technician shift −$9,278; signage −$2,323; assumed comp change −$1,028. Exact targets, distributions and costs are in the report. Effects are assumptions, not treatment estimates.

An inspection or controlled pilot may be worthwhile for learning or a longer horizon. Its information value has not been priced, so it should not be sold as a guaranteed 30-day return. The proposed 12-points-per-dollar comp candidate is an exploratory scenario within the catalogue limits, not an adopted policy.

## How to measure action results

| Action | Measurement and comparison |
| --- | --- |
| Inspection | Reconcile settings, game math and meters; document any verified discrepancy and price the corrective action separately. |
| Move / signage | Choose a feasible destination and comparison group before launch. Compare changes in expected earnings per available hour, with total floor wagers as a displacement check. |
| Maintenance | Compare unavailable hours, repeat faults and expected earnings per scheduled hour against comparable untreated machines. |
| Comp pilot | Randomize eligible participants; measure incremental contribution after economic comp costs and guest retention. Do not run a simultaneous floor-wide change. |

Before spending, specify the target, intervention, comparison group, success threshold and sample-size requirement. The data does not justify a numeric causal effect threshold on its own. Use a longer evaluation period when the 30-day sample cannot resolve the decision.

## Limits and unfinished product decisions

All six challenge questions have a reproducible descriptive or scenario analysis. Causal identification, exhaustive portfolio optimization, deployment, final presentation and the submission video are not complete. External tourism/weather data, a validated intervention-effect model, and Gemini are optional future additions, not claimed as implemented. No public repository or app has been published by this setup.
