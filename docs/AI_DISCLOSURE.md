# AceIQ — AI-use disclosure

Updated November 7, 2026. Applies to the current dashboard, forecast, floor map and scenario engine.

OpenAI Codex assisted with project planning; Python/Streamlit code generation and revision; data checks and analytical calculations; Databricks notebook/job operations; forecasting and simulation implementation; interface styling and floor-map development; tests and debugging; documentation; GitHub setup; and packaging/deployment preparation. The team directed the project goals, selected the Modern Vegas dashboard and retro floor-map direction, and chose maximum expected 30-day incremental contribution as the default decision objective. A teammate supplied an interface implementation that was incorporated and revised.

Numerical results come from the supplied synthetic data and documented calculations. AI-generated explanations are not independent evidence. The action-effect distributions are explicitly stated assumptions, not measured causal effects. Code tests and local interaction checks were performed, but these do not prove every inference correct or constitute independent human validation.

Databricks was used for the original data investigation, reproducible notebook/job workflow and exported results. The current Streamlit app reads local derived files; it does not make a live Databricks query. The newer forecast/map modules and extension notebook were implemented and checked locally; they have not been executed in the Databricks workspace. No Databricks generative-AI feature is claimed as the source of the model or findings.

The Gemini API has **not** been integrated, and the dashboard contains no Gemini chat feature. The prediction model is a Python weekday demand model, not a large language model. The Monte Carlo action scenarios use NumPy seeded random draws, not Gemini-generated probabilities. The retro floor map is implemented using supplied coordinates and Plotly; movement arrows depict hypothetical actions, not real-time casino activity.

The team remains responsible for reviewing the calculations, assumptions, sources and final submission. Before submitting, each teammate should add any other AI tools they actually used and their purposes. This statement does not claim every line was manually authored by the team or independently reviewed.
