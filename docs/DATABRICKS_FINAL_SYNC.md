# Databricks final-product sync

The final dashboard and floor engine at commit `2a124ca0b901ab9e4c18d87f471679c0673600a1` were archived, verified and executed in Databricks on 2026-11-08T16:41:59.186612+00:00.

## Open the work

- [Original notebook with final section appended](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#notebook/4100737999894437)
- [Standalone final-product evidence](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#notebook/3148291400352103)
- [Successful cloud run](https://dbc-3501c3c5-1cc4.cloud.databricks.com/?o=7474651870217400#job/796646835901211/run/1115290540544965)

These links require access to the Databricks workspace. They are not public judge links. GitHub copies of both notebooks contain saved results, tables and charts. In Databricks, refresh the notebook tab and scroll to **FINAL PRODUCT — revision 2a124ca**, or use notebook 05 directly. To recompute only the final evidence, choose **Run all** in notebook 05 on serverless compute with access to the volume and prepared table.

## What is synchronized

The original notebook's earlier code and saved outputs remain intact, with an updated introduction and a clearly separated final section. A backup is available at `/Users/katherine.t.kim@tamu.edu/Dashboard_Royale/01_data_checks_backup_before_final_2a124ca`.

Notebook 05 loads the exact archived project modules, data, assets and documentation. It covers bottom-ten investigation, payout residuals, machine/monthly availability, demand/event/traffic context, guest concentration, comp economics, forecast reproduction, portfolio comparisons, broader suggestions, atomic swap/undo, and July playback. Fifteen static evidence charts use the final definitions and concise interpretation notes. The interactive browser layout and controls are documented with screenshots; they are not hosted inside Databricks.

The archive contains 76 SHA-256-checked source files. Location: `/Volumes/workspace/default/dashboard_royale_source/final_product/2a124ca/aceiq_final_product.zip`. It has no credentials, virtual environment or Git history. This snapshot remains pinned to the final application commit; later notebook/documentation commits do not change the application model or the archived source.

## Verified results

- Cloud prepared-table totals match final exports within $0.01 across 55,092 active machine-days: wagers $248,905,219.25; payouts $225,267,064.15; actual house win $23,638,155.10; expected house win $23,545,364.48.
- All 16 regression tests passed, plus the leakage/placement/shared-action validation script.
- Rebuilt forecast predictions match the saved predictions. Machine-day holdout MAE: $934.98 versus $1,121.28 constant baseline (16.6% reduction).
- Shared floor engine: 1,000 seeded draws; 308 initial machines, six vacant slots. The example two-machine swap costs $3,600 and preserves the roster; undo restores the original layout.
- The limited original shortlist still favors keeping budget. Broader individual floor suggestions have a different search scope and are conditional planning estimates.

See [machine-readable verification](databricks_verification.json). Cloud chart PNGs and `verification.json` are in the versioned volume's `verification/` folder. Notebook outputs were exported from the successful run, not manually invented.

## Version boundaries

Historical property forecast (68.5% improvement) and version-1 Monte Carlo outputs remain historical evidence. The current machine-day forecast (16.6%) and shared floor engine are different models. Do not mix their metrics or distributions. July actuals are absent; scenarios are not causal forecasts of guaranteed intervention success.

The existing scheduled/one-off complete-analysis job points at the original combined notebook. Running that whole notebook also reruns its historical export cells. Use notebook 05 for final evidence without rerunning historical exports. `scripts/refresh_from_databricks.ps1` remains the legacy six-file export helper; it does not regenerate final forecasts or floor assets.

The application still runs locally via `python run_local.py`, with Streamlit on port 8501 and the separate floor lab on port 8502. This update does not publish either service. There is no live Databricks dependency in the app and Gemini chat is not implemented. Existing source tables and exports were not modified by this sync.
