# The Gilded Ace — Dashboard Royale

A learning project built with Databricks and Python. The app has three pages: Casino overview, Machine investigation, and the $100,000 decision lab. All casino data is synthetic, January–June 2025. July 1–30 is the decision horizon, not the current calendar month.

## What each tool does

- **Databricks** runs the documented analysis and preserves the notebook for judges.
- **Streamlit** turns Python code into a web app with charts and controls.
- **VS Code** is where you edit that Python code on your computer.
- **Git** keeps a history of changes; **GitHub Desktop** provides buttons to review and save that history. GitHub stores a shared copy online.

The public app reads small exported results. Visitors do not need a Databricks account, and the app needs no Databricks password or token. Refreshing the data is an explicit export step; the app is not a live database connection.

## Open and run in VS Code

1. In VS Code choose **File → Open Folder** and select this folder.
2. Install the Microsoft Python extension if prompted. Use Python 3.12.
3. Open **Terminal → New Terminal** and run:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py
```

4. Open the localhost address printed in the terminal. Edit `app.py`, save, and refresh the app. Stop it with Ctrl+C.

If `py -3.12` is unavailable, install Python 3.12 first. This project was tested using Python 3.12. Choose the `.venv` interpreter in VS Code; the included Run configuration then works with F5.

## Add this work to GitHub Desktop

1. Choose **File → Add local repository** and select this folder. If it says this is not a Git repository, choose **Create a repository here**.
2. The first local checkpoint has already been saved. Click **History** to see it. After your next edit, review **Changes**, enter a short summary, then **Commit to main**. A commit is a saved checkpoint.
3. When ready to upload, choose **Publish repository**. Review visibility before publishing. Raw data, passwords and tokens do not belong in Git.
4. After later edits: review Changes → write a summary → Commit → Push origin. Committing saves locally; pushing updates GitHub.

Official instructions: [add a local repository](https://docs.github.com/en/desktop/adding-and-cloning-repositories/adding-a-repository-from-your-local-computer-to-github-desktop).

## Where to find things

| File/folder | Purpose |
| --- | --- |
| `app.py` | Three-page Streamlit application |
| `analysis/pipeline.py` | Reproducible analysis and scenario calculations |
| `notebooks/01_data_checks.ipynb` | Original Databricks notebook with the combined investigation |
| `data/` | Derived synthetic results used by the app |
| `docs/findings.md` | Findings, caveats and measurement plans |
| `scripts/refresh_from_databricks.ps1` | Download fresh exports and the original notebook using your CLI login |

## Reproduce locally

Download the [challenge dataset](https://github.com/tamu-datathon-org/dashboard-royale), then:

```powershell
.venv\Scripts\python analysis/pipeline.py --data "C:\path\to\dashboard-royale\data" --output data
```

The report records source file SHA256 hashes, validation, train/test dates, simulation seed and assumptions. Player exports contain only grouped summaries, not player identifiers.

## Checks completed

The original Databricks notebook ran successfully end to end. Its result snapshots are embedded for reading without rerunning. Local interaction checks passed for all three pages, machine rankings, machine selection, the three decision objectives, zero budget and the benefit sensitivity control. Cross-checks reconcile exported totals, catalogue costs, eligible targets and scenario rankings.

To repeat the local checks:

```powershell
.venv\Scripts\python tests/test_results.py
.venv\Scripts\python tests/test_app.py
```

## Refresh from Databricks

After running the complete-analysis section in the original Databricks notebook:

```powershell
powershell -File scripts/refresh_from_databricks.ps1
```

The script downloads results and notebook snapshots into this project. Review the resulting changes in GitHub Desktop. This is a one-way export, not automatic two-way synchronization.

## Publish later

Streamlit Community Cloud can run `app.py` from a GitHub repository. Choose this repository, branch `main`, main file `app.py`, and Python 3.12. No Databricks credentials are needed. [Official deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy).

## How to interpret the decision lab

The default objective is **maximize expected 30-day incremental contribution**, after action costs and planned downtime. The simulation compares a limited, disclosed shortlist and the keep-budget option. It does not prove causal effects or find the globally best action across every possible location, quantity and catalogue item. Distributions describe assumptions, not statistically established treatment effects. Inspections and pilots receive no unmeasured monetary information value.

Source data attribution and license are in `LICENSE-data.txt`. The challenge guide remains the authority for submission requirements.
