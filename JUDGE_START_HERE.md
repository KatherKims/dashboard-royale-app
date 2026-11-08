# Open AceIQ

This is an interactive Streamlit dashboard for Dashboard Royale. The included data is synthetic and precomputed; judges do not need Databricks credentials or the raw challenge dataset. Internet access is required for the first dependency installation, not for the local analysis afterward. No Gemini key is required.

## On Katherine's configured computer

1. Open this folder in VS Code (the folder containing `app.py`).
2. Press **F5**, or choose **Run → Start Debugging → Run casino dashboard**.
3. Use the browser at **http://127.0.0.1:8501**. Keep VS Code open. Stop with **Shift+F5**.

Alternatively, double-click `START_DASHBOARD.cmd`. Keep its window open; Ctrl+C stops that launch. Use one launch method at a time. Clicking the Python file's ordinary Run button is not the same as running Streamlit.

## On another computer

Unzip the entire package first. Install Python **3.12** from python.org. On Windows, double-click `START_DASHBOARD.cmd`; it creates `.venv` and installs pinned requirements on first use, then opens the dashboard. If setup fails, the window stays open with the error.

Manual Windows commands, from this folder:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --global.developmentMode false
```

macOS/Linux, with Python 3.12 installed:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --global.developmentMode false
```

Windows startup has been checked on the development computer. macOS/Linux instructions are provided but have not been tested on those operating systems. A local address works only on the computer running the app. For file-based judging, attach the complete ZIP, not just `app.py` or a private GitHub link.

## Two-minute judging route

1. **Executive overview:** inspect actual/expected earnings; change the evidence dates. Explore demand, tracked guests and comp tabs. Guest headline totals stay January–June; complete-month and validation periods are labeled.
2. **Predictions vs actual:** compare the frozen May–June holdout against the constant baseline; open the method explanation and inspect errors/coverage. Switch scope to a bank or machine.
3. **Machine investigation:** select a bank and M-1158 (use All banks if needed). Compare exposure, expected earnings, availability and payout screening. A flag is not proof of a defect.
4. **$100,000 decision lab → Floor map & simulator:** select **Plan July actions**, a machine, **Move to an empty slot**, and a destination. The arrow previews the proposed move. Change assumptions to see cost/benefit uncertainty update. Historical mode changes positions by snapshot date; colors summarize the selected evidence period.
5. **Portfolio ranking:** compare keeping the budget to the disclosed spending shortlist. Change benefit sensitivity and inspect the recommendation. Map experiments do not automatically become combined portfolios.
6. Download the **Claims & Evidence** and **AI disclosure** from the sidebar, or read `docs/CLAIMS_AND_EVIDENCE.md` and `docs/AI_DISCLOSURE.md`.

## What “interactive” means here

Controls update charts, selections, map highlights and scenario calculations. Historical machines do not move on their own. A move arrow is a hypothetical preview, not an automatic animation or saved change to the supplied placements. The app is not connected to live casino data.

## If it does not start or respond

- Port 8501 already in use: use the running dashboard, or stop the earlier VS Code/terminal launch before restarting.
- Blank/stale browser: confirm the server is still running, then refresh the browser. Wait for a calculation to finish.
- Missing packages: run the pip-install command above using `.venv` Python.
- Missing data: unzip the entire package and keep `data/`, `dashboard/` and `app.py` together.
- Do not share `.env`, `.streamlit/secrets.toml`, tokens, or your local `.venv`.

For reproduction and test commands, see README. The original Databricks notebook is preserved separately from the current local forecast/map notebook.
