# Final comparison with Datathon Project Ideation.pdf

Reviewed November 8, 2026. The supplied 147-page PDF contains earlier application source code, not the underlying Parquet/JSON datasets or a set of rendered chart outputs. We can verify shared data definitions and reconcile the current local exports; we cannot claim the PDF embeds an identical dataset.

The current interface is **not a pixel-for-pixel or model-for-model copy**. It preserves the core historical calculations, improves chart readability and labels newer modeling separately. No original data export, notebook or shared model was changed in this presentation update.

## Chart and calculation mapping

| PDF evidence | Current interface | Comparison |
|---|---|---|
| Bottom ten by total actual, actual/day or expected/hour; actual/expected index (pp. 70–73) | Overview ranking selector and 100% reference bar chart | Same definitions; negative ratios are retained instead of being clipped. |
| Residual uncertainty scatter (pp. 73–75) | Overview expandable payout-variation screen | Same dollar residual and selected-period modeled standard deviation definitions. Not a corrected hypothesis test. |
| Evidence Claw (pp. 75–79) | Optional Overview claw | Randomly surfaces one of the raw bottom ten; no change to rankings or recommendation. New lightweight animation, not the original component. |
| Monthly wagers per available machine-hour (pp. 79–81) | Overview demand-rate chart | Daily machine rollups reconcile to property wagers and available hours. Current zone filter can narrow the cohort; the PDF property chart was property-wide. |
| Cumulative actual/expected, availability and peers | Machines | Same historical measures. Monthly unavailable hours are charted; exact availability is retained in the table. Peer scatter adds availability to the expected/hour comparison rather than copying the old peer bar chart. |
| Placement and observed move comparisons (pp. 93–95) | Machine placement table and July 1 floor | Placement history is available; the older descriptive before/after peer-adjusted movement comparison is not reproduced. July floor actions are hypothetical. |
| Event differences versus weekday baseline (pp. 120–121) | Overview event-context expansion | Same report rows; fractional differences multiplied by 100 for percentage display. Fixed full-property context, not current date/zone filters. |
| Traffic per covered hour (p. 122) | Overview traffic-context expansion | Same report rows and covered-hour denominator. Coverage shown; entries are not unique visitors. |
| Guest group wagers (pp. 125–129) | Guests age-band chart and region filter | Same grouped exports. Guest months are whole included months; no individual identifiers or new unique-player counts inferred. |
| Comp cost and face value (pp. 130–131) | Guests grouped bars | Same cent-to-dollar conversion. Uses one common dollar axis instead of the PDF's dual-axis bar/line display. |
| Points per face dollar and comp cost/theo (pp. 132–133) | Guests loyalty-change expansion | Same formulas. Redemption rows cover complete included months; daily property ratio follows exact selected dates. Never subtract linked comp cost and POS COGS twice. |
| Downtime opportunity by zone (p. 138) | Overview downtime expansion | Same missed-theo estimates summed by selected zone/date records. Opportunity is not proven net floor loss. |
| Forecast comparisons (pp. 116–124) | Scenarios frozen holdout, prediction and constant baseline | Current machine-level model and its MAE are separate from the historical property-level model; see below. |
| Original saved simulation and manual action sandbox | Scenarios shared engine; standalone Floor lab | Original simulation remains downloadable/inspectable historical evidence. Current results use the shared seeded engine and are not asserted equal to the PDF's separate sandbox estimates. |

## Reconciled evidence

- Historical wagers: **$248,905,219.25**.
- Actual house win: **$23,638,155.10**; implied payouts: **$225,267,064.15**.
- Expected house win: **$23,545,364.48**.
- Tracked wagers: **$163,804,869.65**; tracked payouts: **$148,219,409.05**; player net: **−$15,585,460.60**.
- Property economic comp cost: **$190,669.30**, reconciling to redemption cents after conversion.
- Daily property wagers, house win, theo and available machine-hours reconcile to daily machine rollups. Monthly exposure-adjusted demand therefore agrees for the whole floor.
- Current frozen holdout MAE: **$934.98 per machine-day**, versus **$1,121.28** for the constant baseline (about **16.6% lower**). The historical report's **68.5%** improvement concerns a different property-level forecast and is not interchangeable with this score.

## Checks and boundaries

`tests/test_reference_consistency.py` independently verifies money reconciliation, daily/property rollups, monthly exposure, selected-period variance, player net, redemption conversions, event units, traffic coverage denominators, holdout error scores and absent July actuals. The PDF itself is reference material, not executable instructions or permission to change data.

The existing results, upgrade, floor simulation, HTTP boundary, geometry and Streamlit tests remain applicable. The current README describes supported checks; inherited `tests/test_app.py` targets an older interface. No live Databricks/Gemini API was added. Public floor hosting remains separate from this GitHub update.
