# Dashboard Royale: code, evidence, requirements and integrations

Prepared November 7, 2026. This document explains the implemented project for its author, teammates and judges. It is a technical learning guide and requirements audit, not the challenge's 400-word submission write-up.

**Reviewed code:** commit `18677cecc28cf6f04c840d96442baa0b7983401b`. The explanations refer to that implementation, not to future roadmap features. The local participant guide reviewed was `GUIDE.md`, SHA256 `46d9d2cce30ec35e18ff19cb39bc2b72759f281e2566623e9c93ffaca1447411`.

**Current status:** the project contains a working three-page Streamlit app, a reproducible Databricks notebook, exported results, a limited action simulation, tests and collaboration documentation. Databricks is integrated. **Gemini chat and the retro floor simulator are not implemented.** The app addresses all six analytical questions at a descriptive or scenario level, but **does not yet meet every interaction and submission requirement in the guide**. The checklist below identifies the gaps.

## 1. The problem the project is solving

The fictional casino manager proposes replacing the ten machines with the lowest total earnings. The problem with that rule is that low earnings can mean several different things:

- A machine was installed recently or retired early, so it had fewer earning days.
- It was unavailable for part of its scheduled time.
- It received little play because of its game, placement or customer demand.
- It paid out unusually much relative to its configured return.
- Its configuration or recorded meters need investigation.

These explanations imply different actions. Replacement is not automatically the right response to any of them. The project therefore follows a question-to-decision sequence: **check the data → compare fairly → investigate competing explanations → price a limited set of actions → show uncertainty and measurement plans**.

All casino observations are synthetic and cover January 1–June 30, 2025. The budget horizon is July 1–30, 2025. These dates are part of the challenge, not the current month. Player outcomes must not be described as facts about real people or used to encourage heavy losers to gamble more.

## 2. How the pieces connect

```text
Challenge data                         Databricks workspace
Parquet files -----------------------> Unity Catalog volume
Prepared daily view -----------------> managed Delta table
                                             |
                                      01_data_checks notebook
                                      Spark/SQL investigation
                                      pandas/NumPy complete analysis
                                             |
                                      exported results and scenarios
                                             |
                              refresh_from_databricks.ps1
                                             |
Local Git repository <---------------- data/ + notebooks/
       |
       +--> Streamlit app.py --> browser dashboard
       |
       +--> GitHub --> teammate clones and reviews

Planned, not built:
browser question --> Streamlit server --> approved metric lookup --> Gemini explanation
floor coordinates + dated placements --> retro map --> existing scenario calculations
```

The app reads exported files. It does **not** query Databricks on every click, and visitors do not need Databricks credentials. GitHub stores the project and history; it is not, by itself, the server that runs the Streamlit app.

## 3. File-by-file guide

| File or directory | What it does | Why it matters |
| --- | --- | --- |
| [`app.py`](../app.py) | Loads derived results and renders the three pages and controls. | Gives a manager an interactive path through the analysis. |
| [`analysis/pipeline.py`](../analysis/pipeline.py) | Reads source tables, validates relationships, calculates summaries, evaluates forecasts and simulates action combinations. | Contains the reusable analytical logic. |
| [`notebooks/01_data_checks.ipynb`](../notebooks/01_data_checks.ipynb) | Original notebook, expanded with the investigation and complete analysis. Contains saved outputs. | Lets judges inspect the evidence without rebuilding the app. |
| [`notebooks/01_data_checks.py`](../notebooks/01_data_checks.py) | Databricks source-format copy of the notebook. | Easier to review in Git than a large notebook JSON diff. |
| [`data/analysis_results.json`](../data/analysis_results.json) | Source hashes, validation, monthly results, forecast comparison, assumptions, action catalogue and portfolio summaries. | Main source for the app's explanations and summary charts. |
| `data/machine_daily.parquet` | Active machine-day values, locations, earnings, exposure and downtime opportunities. | Supports machine timelines and monthly downtime. |
| `data/machines.parquet` | One diagnostic row per machine. | Supports rankings and machine selection. |
| `data/guest_groups.parquet` | Aggregates by month, region and age band. | Provides group comparisons without player IDs. |
| `data/property_daily.parquet` | Property-level daily data. | Preserves a useful daily export; the current app does not load it directly. |
| `data/scenario_net.npz` | A numerical array of nine candidate actions × 1,000 simulated net outcomes. | Allows interactive sensitivity without rerunning raw-data processing. |
| [`scripts/refresh_from_databricks.ps1`](../scripts/refresh_from_databricks.ps1) | Downloads the six result files and two notebook formats using the Databricks CLI. | Connects verified cloud analysis to local development. |
| [`tests/test_results.py`](../tests/test_results.py) | Checks reconciliations, action constraints and consistency of simulated summaries. | Helps prevent incorrect or incompatible exports. |
| [`tests/test_app.py`](../tests/test_app.py) | Uses Streamlit AppTest to exercise pages and important controls. | Finds app execution and interaction errors. |
| `.streamlit/config.toml` | Dark theme, gold accent, text colors, telemetry setting and production-mode setting. | Implements the Modern Vegas appearance. |
| `.vscode/launch.json` | Runs the `streamlit` Python module with `app.py`. | Supports launching/debugging from VS Code with the selected interpreter. |
| `requirements.txt` | Pins Streamlit, pandas, NumPy, PyArrow, Plotly and Matplotlib versions. | Makes environment setup more repeatable. |
| `.gitignore` | Excludes environments, caches, local secrets and raw-data directories. | Reduces accidental commits of machine-specific files or credentials. |
| `LICENSE-data.txt` | Retains the challenge data's MIT license. | Preserves attribution and redistribution terms. |
| [`README.md`](../README.md), [`TEAM_HANDOFF.md`](../TEAM_HANDOFF.md), [`docs/findings.md`](findings.md) | Setup, collaboration, roadmap and findings. | Makes the work understandable and transferable. |

The app uses pandas for tables, NumPy for numerical simulation, Plotly for interactive charts, and Streamlit for the interface. PyArrow reads/writes Parquet. Matplotlib produces the notebook's presentation-style figures.

## 4. Source data and safeguards

The reusable pipeline reads ten source tables: `prepared_daily_view`, `property_day`, `player_period`, `machine_day`, `machines`, `game_math`, `action_catalog`, `loyalty_ledger`, `zone_traffic_hourly` and `events`. The earlier notebook investigation also reads `operations` for the selected machine's maintenance/event history.

| Source | Unit of observation and purpose |
| --- | --- |
| `prepared_daily_view` | Machine-day: convenient prepared measures and dated location fields. |
| `machine_day` | Raw daily meters: recorded earnings, scheduled/available seconds and squared-bet totals. |
| `machines` | Machine identity, game/theme/manufacturer and installation/retirement dates. |
| `game_math` | Configuration-level payout variance used to assess payout deviations. |
| `property_day` | One row per gaming date: floor totals and comp economics. |
| `player_period` | Player-period summaries: tracked wagers, payouts, player net and grouping fields. |
| `loyalty_ledger` | Individual loyalty events: points, redemption value and economic cost. |
| `zone_traffic_hourly` | Zone-hour sensor observations and coverage. |
| `events` | Event names and date ranges. |
| `action_catalog` | Action prices, quantity limits, lead times and operational constraints; not measured benefits. |

Inside `run(root, output, execution)`, the nested `read(name)` locates one source file, records its SHA256 fingerprint, and reads it into pandas. A fingerprint identifies the exact input file used; it does not prove that the source data is correct. Numeric conversion handles money and game-math columns while avoiding pipe-separated lists such as permitted bet amounts. `records(df)` converts tables to JSON-compatible records, including dates.

The verified prepared data has **56,110 rows and 44 columns**. There are **55,092 active machine-days**, **1,018 inactive rows**, **310 machine identities** and **181 dates**. Inactive rows are excluded from earning-rate calculations. A machine identity is not the same thing as a simultaneously occupied floor slot.

Checks include duplicate machine-day keys, duplicate property dates, valid raw available seconds, money formulas and aggregate reconciliation. The notebook also checks unique machine/configuration identifiers, missing configurations, missing monetary inputs, and agreement between prepared and raw earnings. Joins specify one-to-one or many-to-one expectations to guard against multiplying rows.

These safeguards are useful, not a universal guarantee. The pandas joins are inner joins, and a complete future validation suite should explicitly assert coverage of every expected key. `np.allclose` uses its default relative tolerance as well as the supplied absolute tolerance; the check is not strictly an absolute sub-cent test. Several checks use Python `assert`, which should not be disabled with optimized Python execution.

## 5. Money definitions and verified totals

```text
Actual house win = wagers − payouts
Expected house win (theo) = wagers × (1 − configured RTP)
Overall hold = sum(actual house win) / sum(wagers)
Payout gap = actual house win − expected house win
Player net = payouts received − wagers placed
```

RTP is the configured long-run return to player. A 92% RTP means the theoretical casino margin is 8%. If guests wager $1,000, expected house win is $80. Actual house win can differ substantially in a short sample. Wagers include money bet repeatedly and are not equivalent to cash deposited or casino revenue.

| January–June measure | Verified result |
| --- | ---: |
| Total wagers | $248,905,219.25 |
| Total payouts | $225,267,064.15 |
| Actual casino earnings before costs | $23,638,155.10 |
| Expected casino earnings before costs | $23,545,364.48 |
| Actual minus expected | +$92,790.62 |
| Overall hold | 9.50% |

The hold is a ratio of totals, not an unweighted average of daily percentages. Raw cent amounts are divided by 100 where needed. Squared cent amounts require a factor of 10,000 when converted to squared dollars. Negative house win is permitted because players can win more than they wager during an interval.

Neither actual house win nor theo is total business profit. The code does not build a complete property profit-and-loss statement from food/beverage margin, payroll, taxes and all other operating costs. Its action model calculates incremental modeled benefit after the costs it explicitly includes.

## 6. Question 1: which machines are truly underperforming?

The original notebook first reproduces the manager's bottom ten by total actual earnings. It then calculates active days, available/scheduled hours, availability, actual earnings per active day, expected earnings per available hour, payout gap and modeled payout variability. The app allows the user to change the ranking basis and inspect any machine.

Exposure matters: M-5076 appears near the bottom with only 49 active days. M-1118 had 55 days and M-1120 had 132; those latter two were retired before the period ended. An earlier retirement should not become another July replacement recommendation.

The pipeline's July candidates must be installed by July 1 and not retired on or before that date. It also requires at least 28 active historical days when constructing the spending shortlist. That 28-day threshold is an implementation choice, not a requirement from the guide.

### Separating the payout gap from downtime

For M-1158:

| Measure | Result |
| --- | ---: |
| Actual house win | $15,796.25 |
| Expected house win on observed wagers | $51,961.00 |
| Payout gap | −$36,164.75 |
| Downtime | Approximately 3.01 hours |
| Standardized payout gap | Approximately −4.57 |

The theo is computed on wagers that actually occurred. A payout gap therefore concerns the outcome of observed play; downtime concerns opportunities for play that did not occur on that machine. They are different quantities. Little downtime is weak support for explaining a large negative payout gap through maintenance alone.

The game-math calculation is:

```text
Payout variance in dollars²
    = sum(squared bet amounts in cents² × payout-multiplier variance) / 10,000
Payout standard deviation = square root(payout variance)
Standardized gap = (actual − expected) / standard deviation
```

The app displays a warning when the absolute standardized gap exceeds three. That is a screening rule, not proof of a defect, misconduct or a particular probability. It assumes independent spins and correct configuration data. Looking across many machines, especially machines selected for low earnings, makes extreme results more likely. The code does not perform a multiple-testing correction or establish a causal diagnosis.

The pipeline also compares a machine's expected earnings per available hour with the median for its theme. A ratio of 0.5 means half that theme median. This is a descriptive peer comparison, not a model controlling simultaneously for denomination, placement, guest mix and all operating conditions. Location is investigated through daily zone/bank aggregates; a fully adjusted model of machine quality has not been built.

**Decision value:** the analysis supports different investigation routes—lifecycle review, configuration inspection, maintenance assessment or demand/location review—instead of automatically replacing all ten machines.

## 7. Question 2: what changed in demand, and why?

Monthly comparisons include total wagers, wagers per day, and wagers per available machine-hour. These answer different questions. A shorter month can have lower total play even if an average day is busy; fewer operating machines can also reduce total play without a decline in demand per operating machine.

Expected earnings and availability are aggregated by month, zone and bank. The app currently rolls these bank-level rows into zone-level comparisons. It does not expose a bank selector.

The verified wagers per available machine-hour were approximately **$187.45 in January, $197.07 in February, $195.33 in March, $186.82 in April, $188.42 in May and $179.67 in June**. June was about 8.8% below February on this measure. This describes a decline after the early-year peak; it does not prove why it happened.

For event comparisons, the code learns average wagers on each weekday using non-event days, sums the matching weekday baselines across an event's dates, and compares observed event wagers with that sum. This partly addresses weekday composition. It does not fully address seasonal changes, overlapping events, tourism or other confounders. The external tourism/weather reference datasets are not used in this implementation.

Traffic timestamps are shifted back six hours to assign gaming dates. The code excludes missing counts and intervals without positive coverage, then reports entries per covered hour and the share of valid intervals. Entries are not unique people. One limitation is that the current validity rule does **not explicitly inspect `counter_status`**, although the guide recommends doing so. That should be reviewed before relying strongly on the sensor comparisons. Sensor rows are grouped by their derived month without an explicit January–June filter; boundary rows should also be checked if the input release changes.

**Decision value:** compare locations and timing on fairer denominators, while describing possible explanations as hypotheses rather than established causes.

## 8. Question 3: how much play was lost to downtime, and when?

Measured downtime comes from `(scheduled_seconds − available_seconds) / 3600` on active machine-days. The calculation does not assume every gaming day has 24 hours, which matters at daylight-saving transitions.

There are two deliberately different estimates in the notebook/project:

| Estimate | Calculation | Interpretation |
| --- | --- | --- |
| Earlier notebook repair scenario | Machine's downtime × its whole-period theo per available hour × assumed recovery × assumed retained floor play. | Simple historical illustration; no action costs deducted. |
| Complete pipeline/app | Same-machine, same-weekday operating wager rates × downtime, then multiplied by the configured margin. | More detailed historical opportunity estimate, with low/middle/high operating-rate assumptions. |

For the second estimate, the pipeline uses days with at least 20 available hours. It estimates the 25th, 50th and 75th percentiles of wagers per available hour for each machine and weekday. Missing groups fall back to machine-level rates; if still missing, all three fall back to the overall operating-rate median. Each daily rate is multiplied by downtime. The middle wager estimate is converted to theo using that day's configured margin.

The exported results are **5,021.08 downtime hours**, **$990,374.55 middle-case historical wager opportunity**, a wager sensitivity range of **$856,353.76–$1,138,230.52**, and **$92,253.68 middle-case expected-earnings opportunity** across the six months. Monthly downtime is charted, and the machine page gives individual opportunity estimates.

This is not an observed dollar loss or a confidence interval. Unavailable hours might have had different demand from available hours, and players may have switched to another machine. The simulation's retained-play assumption reduces the amount credited as additional floor business. A six-month opportunity total must also be scaled to the July action horizon; it cannot be claimed as a 30-day repair benefit.

## 9. Question 4: what happened to tracked players?

`player_period` is first summed by player across the six months. This prevents a frequent player from being treated as a new person each month when calculating overall concentration.

| Tracked-play result | Value |
| --- | ---: |
| Distinct tracked players | 113,890 |
| Tracked wagers | $163,804,869.65 |
| Tracked payouts | $148,219,409.05 |
| Aggregate player net | −$15,585,460.60 |
| Share of all floor wagers represented | 65.81% |
| Players ahead on recorded six-month play | 13.61% |
| Top 1% of players' share of tracked wagers | 22.86% |
| Separately ranked top 1%'s share of positive player losses | 19.86% |

The top 1% is rounded up to 1,139 players. Wager concentration and positive-loss concentration use different rankings. Positive losses are `max(−player_net, 0)`, so winners do not cancel losers in that denominator.

The app can compare aggregate results by home region or age band. Group exports retain month and count player-period rows, not necessarily distinct people over a multi-month selection. The current UI shows the grouped table; it does not filter the whole dashboard to one chosen guest group.

Tracked play is only carded play, so it should not equal floor-wide meters. The pipeline reports coverage rather than declaring the difference an error. It does not independently reconcile every player total against raw `carded_*` meter fields. Grouped app exports omit player IDs. The findings describe outcomes and concentration; they are not a marketing plan to increase losses among vulnerable guests.

## 10. Question 5: what did comps cost, and what changed?

The pipeline converts loyalty-event UTC timestamps to `America/Los_Angeles`, removes the timezone after conversion, and subtracts six hours before deriving the gaming month. This applies the guide's local gaming-day convention while handling the timezone's daylight-saving rules.

It selects redemption events in January–June, totals redeemed points, face value and economic cost, and reconciles redemption economic cost to the property totals. Economic comp cost is **$190,669.30** over six months.

```text
Observed points per face-value dollar
    = −sum(redeemed points_delta) / (sum(face_value_cents) / 100)
```

The weighted ratio falls from **12.51 in April to 5.84 in May and 5.71 in June**. Fewer redeemed points per dollar of benefit is evidence of changed redemption economics or mix. It is not sufficient proof that one uniform posted policy changed, or that the change caused guest demand to rise or fall.

The app compares face value with economic cost, and the pipeline calculates comp cost relative to theo. It does not subtract both comp cost and linked food/beverage cost of goods sold. Nor does it build a complete food/beverage margin analysis from transactions. That distinction prevents the results from being presented as a full property profit calculation.

## 11. The forecasting model and its validation

The project uses a simple time-series baseline approach rather than a complex machine-learning model:

1. Train on January–April.
2. Forecast each held-out May–June day using its weekday's training average.
3. Compare against a second forecast that uses the same constant training-period average every day.
4. Measure mean absolute error: the average absolute difference between predicted and observed daily wagers.

| Held-out performance | Daily wager MAE |
| --- | ---: |
| Constant-average forecast | $218,258.10 |
| Weekday-average forecast | $68,698.55 |
| Reduction in MAE | 68.52% |

Both predictions are fitted without May–June outcomes. The code then selects the lower-error method and refits it on January–June for a July 1–30 planning baseline of **$40,711,161.62 wagers**. There are no July outcomes with which to validate that forecast. Since May–June is used to choose the winner, it should not be described as an additional untouched test set for a model selected elsewhere.

The action simulation bootstraps ratios of observed training wagers to fitted training wagers and averages 30 sampled ratios into a shared demand multiplier. Those ratios are fitted training residuals, not out-of-sample forecast errors. Days are sampled independently, so serial dependence, monthly shifts and event clusters are not modeled.

**Important implementation detail:** the full-period-refit July forecast is displayed, but `july_pred` is not directly used as the level baseline for action benefits. Those benefits mostly use historical machine rates or six-month averages. The selected forecast method affects the demand residual multiplier. Therefore, the connection from forecasting to the final spending recommendation is present but limited; it should be strengthened and demonstrated before claiming full credit for a model that changes a decision.

The app currently hardcodes the success sentence to say the weekday model improved the result. That matches this data release. If refreshed data makes the constant model win, the sentence must be updated to use the recorded winner dynamically.

## 12. Question 6: what should the $100,000 fund?

The user-selected objective is **maximize expected 30-day incremental benefit**, after the modeled action costs and planned downtime. The guide permits keeping the money, so that option is included as a zero-cost, zero-incremental-benefit baseline.

### Catalogue costs and shortlist

```text
Benefit days = max(0, 30 − catalogue lead_days)
Cash cost = quantity × (unit_cost_cents + recurring_cost_cents_per_day × benefit_days) / 100
Modeled net benefit = modeled operating benefit − cash cost − planned downtime opportunity cost
```

For one lease, $2,500 plus 16 days × $55 equals **$3,380**. Fixed packages are charged in full. Planned lost theo is deducted from modeled contribution, not treated as another cash purchase against the $100,000 cap.

| Shortlisted candidate | Target | Cash cost | Lead / benefit days |
| --- | --- | ---: | --- |
| Inspection | M-1158 | $1,200 | 1 / 29 |
| Inspection | M-1181 | $1,200 | 1 / 29 |
| Move one machine | M-5076 | $1,800 | 2 / 28 |
| Lease replacement | M-5076 | $3,380 | 14 / 16 |
| Additional technician shift | Roster still to select | $11,520 | 7 / 23 |
| Preventive maintenance | Ridgeline machines in the eligible set | $9,000 | 7 / 23 |
| Wayfinding/signage | Back Forty | $7,500 | 10 / 20 |
| Comp-rate change | Exploratory 12 points per face-value dollar | $1,500 | 3 / 27 |
| Controlled comp pilot | No extra comp budget assumed | $4,000 | 5 / 25 |

The weak-machine target is the eligible machine with the lowest theo per available hour. The preventive target is the manufacturer with the largest aggregate middle-case downtime opportunity among eligible machines. Signage targets the zone with the lowest historical theo per available hour. These rules identify candidates, not proven causal remedies. M-5076's short history is especially relevant when judging the confidence in that move/replacement choice.

### Effect assumptions

`np.random.default_rng(20251107)` fixes the random seed and creates 1,000 scenarios. Triangular distributions specify a lower bound, most likely value and upper bound. These choices are assumptions; they were not estimated from controlled interventions.

| Quantity | Assumed triangular values: low, mode, high |
| --- | --- |
| Retained additional floor play | 25%, 50%, 100% |
| Move's play uplift | −10%, 20%, 60% |
| Lease replacement's uplift | −10%, 50%, 150% |
| Technician's recovered downtime opportunity | 10%, 30%, 60% |
| Preventive maintenance recovery | 20%, 50%, 80% |
| Signage play uplift | 0%, 2.5%, 8% |
| Comp economic-cost savings | 0%, 10%, 25% |
| Comp policy's loss of expected gaming earnings | 0%, 0.05%, 0.2% |

Move, lease, maintenance and signage calculations combine an appropriate historical opportunity with the effect, retained-play and demand multipliers. Comp policy compares assumed comp savings with assumed lost gaming earnings and its implementation cost. It does not causally derive those percentages from the proposed 12-point rate. Inspections and the pilot receive no unsupported immediate monetary return; their information value is unpriced.

Planned downtime deductions include two hours for inspections, three for a move, six for a lease replacement and 90 minutes per machine in preventive maintenance. The generic cost function reads catalogue costs/lead times, but several effect durations and downtime values are hardcoded to this catalogue's current values. A future catalogue change requires review, not just reloading the file. `busiest_down` is calculated but unused in the current spending formulas.

### Portfolio search and uncertainty

The code enumerates every subset of the nine explicit candidates, then rejects combinations over budget, combinations with more than three action types, overlapping machine targets, and comp-pilot/floor-wide-comp-change conflicts. It also isolates comp changes from other play interventions except inspection to avoid double-counting demand effects. These conservative rules leave **42 portfolios**.

This is not an exhaustive search of every catalogue action, machine, destination or permitted quantity. There is one unit per listed candidate; purchased replacements, bank moves, promotions and surveys are not evaluated. Destinations, technician roster and other operational feasibility details remain unresolved. The target sets used for overlap checks are conservative, including historical occupants of the signage zone.

Each portfolio sums candidate outcomes within the same scenario. Shared demand and retention samples make alternatives face comparable conditions. The outputs include mean, median, 10th/90th percentiles, chance of a positive modeled benefit, and a separately specified conservative case. They are distributions of assumption-driven expected contribution, **not realized casino payout profit** or confidence levels for proven interventions. The conservative case is a selected stress scenario, not a mathematical lower bound over all possible outcomes.

The decision page can change the budget ceiling, ranking objective and net operating-benefit multiplier. It reconstructs operating benefit from stored net outcomes, scales it, then subtracts fixed cash/downtime costs again. Scaling includes negative operating effects too. It does not let a user independently edit every triangular parameter or create a new destination/action quantity. The detailed candidate table's `expected_net` remains the original baseline value; the displayed portfolio results respond to the sensitivity control.

At the default assumptions, **keeping the budget ranks first** under the selected 30-day mean-benefit objective. This says the evaluated spending cases do not beat zero within that model. It does not prove no worthwhile action exists. A longer horizon, different evidence-supported effects, or a value for learning could change the result.

The measurement plan proposes configuration/meter verification for inspection; comparable controls plus floor-wide displacement checks for moves/signage; downtime and repeat-fault measures for maintenance; and randomized eligible groups with contribution and retention measures for comps. These are proposed study designs. Numeric success thresholds, statistical power calculations and implemented experiments are not present.

## 13. How the dashboard code works

`load_data()` uses Streamlit caching to load the report, machines, active daily rows, guest groups and scenario array. Every interaction reruns the script, while the cache avoids repeated file loading. Because the cached function takes no file-version argument, a data refresh should be followed by clearing the app cache or restarting the server to avoid stale results.

`money()` formats whole-dollar display values, so exported precise values can differ from displayed rounded labels. `chart()` applies the shared background, fonts, margins and chart toolbar settings. Plotly's download control exports an SVG at presentation dimensions. `download_table()` creates CSV downloads with distinct widget keys.

| Page | Available interactions | What the reader learns |
| --- | --- | --- |
| Casino overview | Demand denominator; guest grouping dimension; tabs for guests, comps and forecast validation; tables and downloads. | What changed across the floor, who is represented, and how reliable the simple forecast was. |
| Machine investigation | Three bottom-ten ranking bases; machine selector; actual/theo timeline; detailed tables. | Whether low totals reflect exposure, payout variation or operating opportunity. |
| $100,000 decision lab | Budget cap; three ranking objectives; effect sensitivity; feasible-plan selection and downloads. | How assumptions and costs affect the preferred plan. |

The theme is Modern Vegas: charcoal, off-white and gold, with teal used for expected-earnings comparisons. Some other charts use these colors simply as accents, so the sidebar's global color statement should eventually be narrowed to earnings charts. A CSS breakpoint wraps metric columns on narrower screens. Color is accompanied by labels, but a full accessibility audit has not been performed.

There is no date-range input, dedicated bank drilldown, Gemini chat control or floor map in the current app.

## 14. What Databricks contributes today

The original prepared table is `workspace.default.prepared_daily_view`. The notebook uses `spark.table`, `spark.read.parquet`, temporary SQL views and grouped SQL calculations. It saves the machine diagnostic output as `workspace.default.dashboard_royale_machine_diagnostics`. The diagnostics are aggregated to machine level before converting to pandas for plotting.

Source files and exports are stored in the Unity Catalog volume at `/Volumes/workspace/default/dashboard_royale_source`. A volume is a governed location for files, distinct from a table queried by name. The earlier charts/results are in `analysis_exports`; the app's files are in `app_exports`. Databricks documents this file/table distinction in its [volume documentation](https://docs.databricks.com/aws/en/volumes/) and [table-type documentation](https://docs.databricks.com/aws/en/tables/types).

The expanded notebook preserves the original checks, incorporates the Spark investigation, and includes a copy of the complete `run()` pipeline. Notebook widgets control the selected bottom-ten machine and the earlier historical recovery illustration. They do not automatically change all complete-pipeline assumptions or the exported app's date range. The saved earlier charts retain their original context.

The complete pipeline uses pandas and NumPy on the Databricks driver. It is not a fully distributed Spark implementation. That is sufficient for the current data footprint, but larger releases would require profiling and potentially distributed aggregation before local collection. Hashing source files also reads their bytes into driver memory.

The full notebook previously passed an end-to-end serverless job run. Saved tables and chart outputs are embedded so judges can inspect results without rerunning. The [verified run](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#job/1101185085183547/run/614558976320488) requires workspace access; it is not a public judging link.

The NPZ scenario archive is built in an in-memory `BytesIO` buffer before writing its bytes to the volume. This fixes the random-seek write failure encountered when writing a ZIP-based NumPy archive directly to that storage path.

`refresh_from_databricks.ps1` uses the authenticated CLI profile to copy result files and export the notebook as `.ipynb` and source `.py`. It stops on nonzero CLI exit codes. It is a one-way, sequential download—not an atomic snapshot transaction, scheduled pipeline, two-way code sync, or live app connection. Refresh only from a completed run, review changes, run checks and restart the app. Editing `pipeline.py` locally does not automatically update the notebook's copied implementation; keep those implementations aligned deliberately.

For the sponsor prize, the defensible claim is that Databricks provides the reproducible workspace, governed data organization, Spark/SQL investigation, diagnostic table and repeatable job execution. Do not claim that the app requires Databricks at runtime, that all processing is distributed, or that using the platform guarantees a prize. The supplied prize image emphasizes creativity, implementation and meaningful improvement; demonstrating the actual workflow is stronger than displaying a logo.

## 15. How Gemini would fit—and what is missing

**There are no Gemini API calls, Google GenAI dependency, API-key configuration, chatbot UI or Gemini answer-validation tests in the reviewed code.** Gemini appears only in the team roadmap. The existing calculations and screenshots must not be presented as Gemini-generated analysis.

A proposed architecture is to let the Streamlit server offer a few approved, read-only analytical functions. Gemini requests a function with structured arguments; the application validates and executes it, then supplies the result for explanation. This is the function-calling pattern described in Google's [official documentation](https://ai.google.dev/gemini-api/docs/function-calling). The following is a design proposal, not an existing implementation.

| Proposed function | Return only the necessary evidence |
| --- | --- |
| `get_machine_summary(machine_id)` | Earnings, exposure, payout gap, downtime, period and limitations for one valid machine. |
| `get_monthly_demand()` | Monthly demand measures and denominator definitions. |
| `get_plan_summary(plan_id, sensitivity)` | Cost, modeled outcomes, assumptions and exact sensitivity setting. |
| `get_validation_summary()` | Training/test dates, model errors and validation limitations. |

For “Why is M-1158 flagged?”, the tool would return the actual/expected gap, roughly three downtime hours and the modeled standardized gap. Gemini could explain that downtime alone is a weak explanation and that configuration/meter review is warranted. It should not conclude that the machine is defective or that someone cheated.

Keep numerical calculation in the tested Python layer. Restrict tool names and parameter ranges; do not execute arbitrary generated Python or SQL. Include source fields, period, scenario settings and limitations with answers. A prompt alone does not guarantee correct numbers: test quoted values against tool outputs and keep the underlying evidence visible.

The key would live in server-side environment variables or Streamlit secrets, never in Git or browser JavaScript, consistent with Google's [key-handling guidance](https://ai.google.dev/gemini-api/docs/api-key). The base dashboard should continue to work if chat is disabled or the API fails. Add timeouts, bounded context, request limits and an explicit usage budget. Send only the summaries needed for the question. The model choice and sponsor-specific Gemini criteria still need verification; no Gemini prize requirements have been provided here.

Implementation would require a model/API choice, SDK dependency, secret configuration, validated lookup functions, chat/session UI, a controlled function-call loop, error handling and numerical/source-grounding tests. None of these are implied by the Databricks CLI connection.

## 16. The retro floor simulator's place in the project

The optional idea is a top-down casino management-game view using the supplied `floor_locations`, `floor_walkways` and dated `placements`. These tables are not consumed by the current app/pipeline. A correct map must use the placement valid on the selected date rather than assuming a machine stayed in one place for six months.

Machine sprites could be colored by expected earnings per available hour or downtime. Ghost sprites/arrows could preview moves; badges could identify maintenance and replacements. A side panel would reuse the decision-lab costs and scenario outcomes, including uncertainty and retained-play assumptions. Occupied destinations, lifecycle eligibility and action conflicts would need validation.

The animation would explain a scenario, not establish the causal return of moving hardware. Calling the color “expected contribution” would require a clearly defined after-cost calculation; the current theo is before operating costs. The simulator remains a stretch feature after the guide's essential interactions and submission artifacts.

## 17. Requirement-by-requirement audit against GUIDE.md

“Implemented” below means the relevant code exists. It does not promise maximum judging credit or establish causality.

### Six analytical questions

| Guide question | Evidence in the implementation | Status / remaining limit |
| --- | --- | --- |
| True machine underperformance after exposure, availability and luck | Rates, lifecycle filters, payout standardization, theme peers and downtime comparison. | Substantial diagnostic coverage; no full location-adjusted causal classification. |
| Demand change and explanations | Monthly normalized rates, zone/bank aggregates, weekday-adjusted event associations and traffic coverage. | Descriptive coverage; causes remain unresolved. |
| Lost play from downtime and timing | Raw-second downtime, operating-rate sensitivity, monthly and machine displays. | Counterfactual estimate; not proven net floor loss. |
| Player wagers, payouts, net and concentration | Six-month player aggregation, coverage, two top-1% calculations, group summaries. | Implemented for tracked play; raw carded-meter reconciliation remains an extension. |
| Comp cost and change | Economic cost, face value, redemption ratio, local gaming-month reconciliation. | Implemented descriptively; no causal policy-effect estimate or full POS margin model. |
| $100,000 actions and evaluation | Catalogue-priced shortlist, constrained combinations, uncertainty and measurement plans. | Limited scenario search; operational targets/effects need validation before action. |

### The four interactions judges are instructed to try

| Judge action | Current status |
| --- | --- |
| Change the analysis period | **Missing.** Month charts are not date filters. All core results use January–June. Add a common period selector and recompute affected rates, denominators and concentration correctly. Keep forecast train/test dates separate. |
| Drill into one bank or guest group | **Partial.** There is a machine drilldown and a choice of guest grouping dimension, with a table of groups. There is no dedicated bank selector or selected-group investigation view. |
| Find model validation | **Implemented.** Overview → Forecast check displays time split, errors and actual/predicted series. |
| Trace one recommendation to evidence | **Partial/substantial.** Plan costs, targets, assumptions, distributions and machine evidence are available. A direct click from each action to its exact supporting measurements would make the trace clearer. |

### Judging rubric

| Criterion | Weight | Current support and gap |
| --- | ---: | --- |
| Analytical validity | 30% | Money checks, exposure adjustment, payout variability and competing explanations; assumptions and incomplete causal adjustment must remain visible. |
| Dashboard and communication | 25% | Three-page narrative, labeled charts, downloads and explanations; date/group drilldowns and accessibility review remain. |
| Modeling and validation | 20% | Honest time-based comparison with a simple baseline; the forecast's effect on a spending decision needs a clearer demonstration. |
| Recommendations and tradeoffs | 15% | Priced shortlist, uncertainty, retained budget and measurement plans; effects, destinations and sample-size criteria are not validated. |
| Originality | 10% | Reproducible investigate-before-replace framing and contrasting payout/downtime evidence; Gemini and retro map cannot count as implemented originality yet. |

### Submission deliverables

| Required deliverable | Status |
| --- | --- |
| Public interactive dashboard link or usable file | Local working app and shareable source ZIP exist. The GitHub repository is private and no public hosted app has been verified. A file submission needs clear installation/opening instructions. |
| Video, at most two minutes | Not created in this project. |
| Main write-up, at most 400 words | Not created. This long explanation is not a compliant substitute. |
| ML/time-series method tied to a decision | Forecast implemented and evaluated; strengthen and state the decision connection. |
| All code/transformation steps | Present in the repository/notebook; provide judges with access rather than relying on a private link. |
| At most three priced action types, or retain budget | The model enforces the limit and includes retention; select and justify the final recommendation. |
| AI-use disclosure appendix | A draft is provided below; the team must review it and append any additional tools used. |
| Claims & Evidence appendix | A structured starting appendix is provided below; validate it against the final code, charts and recommendation before submission. |

The core analytical work is therefore well advanced, but it would be inaccurate to say the submission fully meets the guide today.

## 18. Claims & Evidence appendix: starting version

All results refer to the current synthetic data release. The transformations are in `analysis/pipeline.py` unless the notebook is explicitly named.

| Claim | Source → transformation | Result | Alternative explanation | Limitation |
| --- | --- | --- | --- | --- |
| Low total earnings can reflect short exposure. | `prepared_daily_view` active rows + `machines` lifecycle → count active days and compare total/rate rankings. | M-5076: 49 days; M-1118: 55; M-1120: 132. | Low demand may also matter. | Exposure adjustment alone does not identify machine quality. |
| M-1158's payout gap is not well explained by downtime alone. | Raw meters + `game_math` → actual/theo, raw seconds, variance; notebook operations/timeline. | −$36,164.75 payout gap, about 3.01 downtime hours, standardized gap about −4.57. | Random variation, configuration or recording issue. | Screening signal, not defect or wrongdoing proof; multiple comparisons. |
| Exposure-adjusted floor demand softened after February. | `property_day` → sum wagers / sum available machine-hours by month. | $197.07 in February versus $179.67 in June. | Seasonal composition, events or game/location changes. | Observational; no causal attribution. |
| Downtime represents a limited historical machine-level opportunity. | Active raw seconds + prepared daily rates → same-machine/weekday quantiles × unavailable hours. | 5,021.08 hours; $990,374.55 middle wager opportunity; $92,253.68 middle theo opportunity. | Guests shifted to other machines; downtime happened at quiet times. | Not observed lost floor revenue or a confidence interval. |
| Tracked play covers only part of the floor. | `player_period` player totals / `property_day` wagers. | 65.81% wager coverage. | Different card-use behavior across guests. | Cannot generalize tracked player outcomes to all guests. |
| Tracked wagers are concentrated. | Sum each player's six months, rank, take ceil(1% of players). | 1,139 players contribute 22.86% of tracked wagers. | Carded selection and unequal visit frequency. | Not a recommendation to target heavy losers. |
| Redemption economics or mix changed around May. | Loyalty redemptions → local gaming month → points / face dollars; reconcile cost. | 12.51 points/$ in April, 5.84 in May; $190,669.30 six-month economic cost. | Different redemption mix, rather than one uniform rule change. | No established causal effect on demand or profitability. |
| Weekday forecasting beats a constant average on the held-out period. | January–April means → May–June predictions → MAE. | $68,698.55 versus $218,258.10; 68.52% improvement. | A different period or regime could favor another model. | One holdout, used for selection; no July outcomes. |
| Retaining the budget wins the current shortlist's 30-day mean-benefit comparison. | `action_catalog` + historical rates + disclosed distributions → 1,000 shared scenarios → 42 admissible plans. | $0 incremental cost/benefit ranks above the spending plans at baseline assumptions. | Better targets/effects, longer horizon or information value could favor spending. | Assumed effects; limited candidates/quantities; not global optimization. |

## 19. AI-use disclosure draft

> OpenAI Codex assisted with code generation and revision, data checks, analytical calculations, visualization, documentation, test execution, Databricks notebook/job operations and GitHub project setup. The team directed the project scope, style and selected decision objective. Numerical findings come from the supplied synthetic data and documented transformations; action-effect distributions are assumptions rather than validated intervention effects. The team must review the outputs, assumptions and final submission. Gemini API has not been integrated or used by the current dashboard. The proposed Gemini chat and retro floor simulator are roadmap items only.

Edit this to include any additional AI tools actually used by teammates and remove nothing necessary for an accurate disclosure. Do not claim that every line or inference has already received independent human validation.

## 20. What has been tested, and how to reproduce it

Previously completed verification includes an end-to-end Databricks notebook run, local Streamlit interaction checks and three result-consistency tests. This documentation review inspected the implementation and exported evidence; it did not rerun the full raw-data pipeline or remotely revalidate the workspace.

`test_results.py` checks agreement between daily, machine and monthly totals; duplicate keys; downtime totals; ordered opportunity quantiles; catalogue cost calculations; selected machine eligibility; budget and action-type limits; target overlap; comp conflicts; finite scenario arrays; and agreement of mean/10th-percentile summaries with the exported scenarios. These are consistency checks, not independent proof of every formula or causal assumption.

`test_app.py` checks page rendering, alternative ranking modes, a machine selection, the two alternate decision objectives, zero budget, a doubled benefit multiplier and several plan selections. It primarily asserts absence of app exceptions. It does not comprehensively test accessibility, chart meaning, fresh installation, downloads, every guest/demand control, public hosting or Gemini behavior.

From the project folder, with Python 3.12 installed:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

To check included exports and app behavior:

```powershell
.venv\Scripts\python tests/test_results.py
.venv\Scripts\python tests/test_app.py
```

To rebuild from the separately downloaded challenge data:

```powershell
.venv\Scripts\python analysis/pipeline.py --data "C:\path\to\dashboard-royale\data" --output data
```

Alternatively run the Databricks notebook and use the refresh script with an authorized CLI profile. The notebook cannot run unchanged in ordinary local Python because it uses `spark`, `dbutils` and Databricks display functions. The reusable `pipeline.py` is the local route. Version-pinned Windows development packages do not establish that a Linux public deployment has been tested.

GitHub Desktop's collaboration cycle is fetch/pull → create a task branch → edit → review diff → commit → push → pull request. Avoid editing the copied pipeline independently in two places without synchronizing it. A ZIP supports viewing/running; cloning preserves history and the remote connection for collaboration.

## 21. Recommended completion order

1. Implement a shared analysis-period selector, recomputing metrics with correct denominators and preserving separate forecasting validation dates.
2. Add a bank or selected-guest-group drilldown and direct evidence links from plan targets.
3. Review sensor status, input coverage and the forecasting-to-action baseline connection; make refreshed-data descriptions dynamic.
4. Confirm the final recommendation, scenario assumptions, operational targets and measurable success criteria with the team.
5. Test the final public link or file package from a fresh environment; prepare the two-minute video and separate 400-word write-up.
6. Review the Claims & Evidence appendix and AI-use disclosure against that final version.
7. If time remains, add the retro floor view and/or grounded Gemini chat. Decide their priority together; neither replaces the requirements above.

The defensible project story is: **we challenge a misleading earnings ranking, separate observed performance from assumptions, and make the spending decision traceable to evidence and uncertainty.**
