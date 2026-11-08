# Team handoff — The Gilded Ace

This is the Dashboard Royale casino analytics project. All casino data is synthetic. The app uses January–June 2025 evidence to investigate low-earning machines and compare July 1–30 decisions with a $100,000 budget.

**Current version:** Start with [README.md](README.md) and [rebuild verification](docs/LOCAL_REBUILD.md). The compact dashboard and standalone interactive floor are implemented. Older upgrade guides and the roadmap below describe earlier versions. Gemini remains unimplemented.

## Start here

1. Clone the repository using **GitHub Desktop → File → Clone repository**. You need an invitation if the repository is private. A ZIP is fine for viewing, but **cloning is the right choice for collaborating** because it includes Git history and the GitHub connection.
2. Choose **Repository → Open in Visual Studio Code**. Open the whole project folder, not just `app.py`.
3. Follow the Python 3.12 setup commands in `README.md`. Run `python run_local.py` using your virtual environment to start both the dashboard and floor lab.
4. Read `docs/findings.md` before changing calculations. Read the original combined notebook in `notebooks/01_data_checks.ipynb` for the evidence and saved results.

The app runs from the included derived data; teammates do not need Databricks access to run it. To rerun the raw-data pipeline, download the original challenge dataset. The included refresh script requires Katherine's existing Databricks access or your own workspace permissions; it is not needed for normal app development.

## What works now

| Area | Status |
| --- | --- |
| Casino overview | Demand, earnings, tracked guest summaries, comp costs, and time-split forecast validation |
| Machine investigation | Actual versus expected earnings, exposure-adjusted rankings, payout gaps and downtime |
| Decision lab | 1,000 shared scenarios; 42 admissible portfolios from a limited shortlist; budget, objective and benefit-sensitivity controls |
| Databricks | Original `01_data_checks` notebook contains checks, investigation and completed analysis; end-to-end run passed |
| Local checks | UI interactions, exported totals, action feasibility and scenario rankings passed |
| Retro floor simulator | Coordinate-based map and interactive actions implemented locally |
| Gemini chat | Roadmap only, not implemented |
| Public app deployment | Not yet deployed |

The selected objective is **maximize expected 30-day incremental contribution after action costs and planned downtime**. Keeping the budget wins under the current shortlist and assumptions. This is not proof that all possible interventions are unprofitable. An inspection can buy information whose value is not priced in the current model.

## Working together without overwriting each other

1. In GitHub Desktop, **Fetch origin**, then **Pull origin** if offered.
2. Create a branch for your task: **Branch → New branch**, for example `feature/floor-map` or `feature/gemini-chat`.
3. Agree who is editing each area. Avoid simultaneous edits to the large notebook or regenerating data from different versions without discussion.
4. Edit in VS Code. Review the diff in GitHub Desktop, write a short description, and **Commit**. A commit saves locally.
5. **Publish branch** or **Push origin** uploads the branch. Open a pull request for another teammate to review before merging.
6. After a merge, switch back to `main` and pull before starting the next branch.

Never commit API keys, passwords, `.env`, `.streamlit/secrets.toml` or Databricks credentials. These locations are ignored already. A ZIP export has no `.git` folder and is not a collaborative Git checkout.

## Proposed work split — choose owners together

- Dashboard owner: charts, language, accessibility and presentation exports in `app.py`.
- Analysis reviewer: formulas, assumptions, source joins and validation in `analysis/pipeline.py` and `tests/`.
- Optional Gemini owner: grounded read-only explanations, error handling, source labels and usage limits.
- Optional floor-map owner: dated placements, coordinates, machine selection and scenario overlays.

No roles have been assigned to a person yet. Keep the three-page dashboard and submission requirements ahead of stretch features.

## Gemini: “Ask the floor” — optional next phase

Goal: let a user ask “Why is M-1158 flagged?” or “Why does keeping the budget rank first?” and get a concise explanation of the verified metrics.

Recommended design:

- Streamlit sends the question and the relevant calculated summaries to Gemini from the server.
- Use a small allowlist of read-only functions such as `get_machine_summary(machine_id)`, `get_monthly_demand()` and `get_plan_assumptions(plan_id)`. Let Python calculate; let Gemini explain.
- Include the selected machine, period, metric definition and source table in every answer. Distinguish observed facts, modeling assumptions and unknown causes.
- Return “the data does not establish that” when asked for unsupported causal claims. Never let the chatbot execute arbitrary SQL/code or change the budget plan automatically.
- Keep the key in server-side secrets. Send only necessary synthetic summaries, not credentials or full workspace files. Add request limits and a helpful fallback when the API is unavailable.
- Test against known questions with known numerical answers; compare each quoted amount to the exported report. Fluent explanations alone are not evidence of correctness.

Decisions still open: which Gemini model fits the sponsor rules, the allowed usage budget, whether answers stream, and the exact set of supported questions. No API key or model has been selected or configured.

Official references: [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling), [key handling](https://ai.google.dev/gemini-api/docs/api-key).

## Retro 2D floor simulator — stretch phase

Vision: a top-down, pixel-art casino management game that stays faithful to the data. Click a machine, inspect its evidence, and preview proposed actions. Pixel furniture, small machine sprites and a restrained neon palette can give the game feel while keeping labels and numbers easy to read.

Minimum useful version:

1. Use supplied `floor_locations` coordinates and `floor_walkways`; map machines using `placements` valid on the chosen date. Do not assume each machine stayed in one location. Show vacant slots and retired machines accurately.
2. Toggle colors between **expected earnings per available hour** and **downtime**. If showing contribution after costs, define and calculate those costs explicitly; current theoretical earnings are before operating costs.
3. Clicking a machine opens its actual/expected earnings, exposure, downtime and proposed action.
4. Add ghost sprites/arrows for moves, a replacement marker, and a maintenance badge. Keep the observed layout and proposed layout visually distinct.
5. Beside the map, show spending, remaining budget, modeled incremental contribution, 10th–90th percentile outcomes and the exact assumptions. Reuse the decision-lab calculations rather than inventing a second simulation.
6. Reject occupied/infeasible destinations, conflicting actions, retired targets and over-budget plans. Include lead times, planned downtime and possible displacement of play to other machines.

Start with a clickable map in Streamlit. Add drag-and-drop and animations only if time permits. The map does not establish the causal effect of a move; those effects remain assumptions until tested.

Design choices for the team: pixel-art density, top-down versus isometric view, interaction style, and which page contains the map. The approved dashboard style remains Modern Vegas; the retro treatment is currently scoped to this optional simulator.

## Before submission

- Review all six challenge questions, chart labels, source evidence and action measurement plans.
- Decide the final recommendation together and preserve the assumptions behind it.
- Test the app from a fresh clone; confirm secrets are not needed for the basic dashboard.
- Deploy the app and prepare the required walkthrough/submission separately. A GitHub repository is not itself a running Streamlit website.

Source data: [TAMU Datathon Dashboard Royale](https://github.com/tamu-datathon-org/dashboard-royale). Retain `LICENSE-data.txt` when sharing derived data.
