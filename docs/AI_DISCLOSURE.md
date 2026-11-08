# AI disclosure · local rebuild

Updated November 8, 2026. An OpenAI coding assistant helped implement the compact Streamlit pages, local SVG/JavaScript floor, API validation, plan playback, suggestions, tests and documentation. The user supplied the detailed rebuild specification and approved local-only implementation. Baseline source: `08dab59`; the rebuild was subsequently integrated on top of `25e345f` with the user's authorization. Earlier teammate versions remain in Git history.

Existing analysis, source exports, analytics/forecast modules and the shared decision engine were reused without changing their financial definitions or forcing attractive results. New add/remove what-if assumptions were explicitly specified by the user and are disclosed in previews and Claims & Evidence. Artwork is code-generated SVG; no image generation service was used. No new ML library or LLM is used to choose actions. Suggestions are deterministic constrained evaluations of the existing forecasts and scenario model.

The assistant ran numerical, API, geometry and Streamlit checks and interacted with a local browser. See LOCAL_REBUILD for precisely what was verified. Tests do not establish causal validity, physical feasibility or full accessibility. User/team review remains necessary before using recommendations as evidence in a demo.

Gemini chat is not implemented. The running app does not call Databricks; notebooks preserve the original Databricks work and local exports support this interface. No secrets are required. Original cloud datasets were not modified. The user subsequently authorized committing and pushing the source rebuild to GitHub. Public floor hosting is not configured by this update. Decorative guests are independent of the financial model. Hypothetical July outcomes are not observed data.

The previous disclosure is preserved in `docs/archive/AI_DISCLOSURE_08dab59.md` as historical context.

The final presentation pass also used the supplied Datathon Project Ideation PDF as a reference for chart definitions and concise summaries. The assistant restored evidence views, added an optional random Evidence Claw, reconciled formulas against local exports, and drafted a Devpost description. The claw is a browsing aid, not an analytical recommendation. No generative model is used by the running app.


## Public Streamlit Floor Lab update

AI-assisted implementation added `dashboard/cloud_floor.py` and routed dashboard floor links to the same Streamlit app. It exposes the existing FloorSimulation engine through form controls, a supplied-coordinate map, July day selection, preview/confirmation, undo, suggestions and downloads. Drag-and-drop and decorative walking guests remain local SVG features. Financial models and datasets are unchanged. Databricks verification is pinned to application revision 2a124ca and does not claim to validate this later UI addition.


## Public SVG simulator supersedes the form-only edition

The original SVG floor is now embedded publicly through an AI-assisted Streamlit component adapter. Drag/drop, playback, decorative guests, previews, confirmations and undo use the same UI and Python model as the local edition. The public bridge preserves exact daily results; source data and model files are unchanged. July is simulated, and artwork/guests are decorative. Databricks evidence remains pinned to its documented model revision; it does not verify this new hosting adapter.
