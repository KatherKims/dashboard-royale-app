## Inspiration

The Gilded Ace manager wants to replace the ten slot machines with the lowest earnings. What sounded like a ranking problem became an investigation: low earnings can reflect limited exposure, downtime, demand or unusual payouts.

That became the question behind AceIQ: **is a machine truly underperforming, or is it being judged unfairly?** We wanted to make the evidence understandable before recommending an expensive decision.

## What it does

AceIQ combines a retro Streamlit dashboard with an interactive casino floor. Users compare actual and expected earnings, active days, availability, payout variation and same-theme peers. Date filters update machine evidence, while concise chart summaries explain findings and limitations.

The dashboard covers demand, event associations, traffic coverage, tracked-player outcomes, comp economics and forecast validation. Its July planner compares actions within a $100,000 cash budget using 1,000 seeded Monte Carlo draws.

The floor supports moving, swapping, adding and removing machines, plus inspection, replacement and maintenance scenarios. Users preview costs, uncertainty and incremental net before confirming, play through July, review suggestions and undo changes. The public floor uses Streamlit controls; the local SVG edition adds drag-and-drop and decorative guests. Both share the same financial model.

## How we built it

We used Python, Streamlit, Pandas, NumPy, Plotly and PyArrow, with local synthetic Parquet, JSON and NPZ exports. Databricks notebooks preserve and verify the final analysis; the app runs without a live connection. JavaScript, SVG and CSS power the floor.

We reconciled totals, adjusted comparisons for exposure, incorporated supplied payout variance and documented claims. Forecast selection uses January–March training and April validation, followed by a January–April refit and frozen May–June test against a constant baseline. July remains unobserved.

## Challenges we ran into

We started with little experience in large datasets, theoretical win or operational planning. We learned to distinguish tracked play from total activity, avoid double-counting comp costs, and separate location associations from causal evidence.

Another challenge was keeping scenario assumptions visible instead of presenting simulated returns as guarantees.

## What we learned

A useful dashboard connects questions, evidence and decisions. Validation, understandable comparisons and honest uncertainty matter as much as visual design.

## Built With

Python, Streamlit, Pandas, NumPy, Plotly, PyArrow, Databricks, JavaScript, SVG, CSS, Parquet, JSON, NumPy NPZ, time-series forecasting and Monte Carlo simulation.
