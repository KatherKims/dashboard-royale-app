"""
AceIQ / The Gilded Ace Decision Intelligence Platform

Run locally:
    python -m streamlit run app.py

This app uses precomputed files in data/.
It does NOT require Databricks credentials or raw source data to run.
"""

from pathlib import Path
import json
import hashlib

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dashboard.analytics import machine_summary as build_machine_summary, machine_category
from dashboard.views import render_forecast, render_decision

# =============================================================================
# APP SETTINGS
# =============================================================================

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

MAROON = "#500000"
MAROON_LIGHT = "#7B1E1E"
GOLD = "#D9B66F"
GOLD_LIGHT = "#F6DB9C"
TEAL = "#65C6BD"
GREEN = "#68C77E"
RED = "#FF756B"
ORANGE = "#F39C59"
PURPLE = "#B985F4"
WHITE = "#F7F3EC"
MUTED = "#AEB8C3"
BG = "#0D1117"
PANEL = "#171E27"
PANEL_ALT = "#202A34"
GRID = "#34414D"

st.set_page_config(
    page_title="AceIQ | Gilded Ace Decision Intelligence",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# STYLING
# =============================================================================

st.markdown(
    f"""
    <style>
        :root {{
            --maroon: {MAROON};
            --gold: {GOLD};
            --goldlight: {GOLD_LIGHT};
            --teal: {TEAL};
            --green: {GREEN};
            --red: {RED};
            --orange: {ORANGE};
            --white: {WHITE};
            --muted: {MUTED};
            --bg: {BG};
            --panel: {PANEL};
            --panel-alt: {PANEL_ALT};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 5% 0%, rgba(80,0,0,.40), transparent 26%),
                radial-gradient(circle at 96% 3%, rgba(217,182,111,.12), transparent 24%),
                linear-gradient(180deg, #0D1117 0%, #10151C 100%);
            color: var(--white);
        }}

        .block-container {{
            max-width: 1500px;
            padding-top: 1.45rem;
            padding-bottom: 2.5rem;
        }}

        header[data-testid="stHeader"] {{
            background: rgba(13,17,23,.72);
        }}

        [data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, #260A0A 0%, #151B22 53%, #0D1117 100%);
            border-right: 1px solid rgba(217,182,111,.22);
        }}

        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 1.15rem;
        }}

        h1, h2, h3 {{
            color: var(--white) !important;
            letter-spacing: -0.035em;
        }}

        h1 {{
            font-weight: 800 !important;
        }}

        p, li {{
            color: #DBE0E4;
        }}

        .sidebar-brand {{
            background:
                linear-gradient(145deg, rgba(90,0,0,.96), rgba(42,15,18,.86));
            border: 1px solid rgba(217,182,111,.36);
            border-radius: 17px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 25px rgba(0,0,0,.20);
        }}

        .sidebar-title {{
            color: var(--goldlight);
            font-size: 1.32rem;
            font-weight: 900;
            letter-spacing: .10em;
        }}

        .sidebar-subtitle {{
            color: #E2D7C7;
            font-size: .68rem;
            letter-spacing: .12em;
            margin-top: .25rem;
        }}

        [data-testid="stMetric"] {{
            background:
                linear-gradient(145deg, rgba(31,41,52,.98), rgba(19,26,34,.98));
            border: 1px solid rgba(217,182,111,.17);
            border-radius: 14px;
            padding: .9rem 1rem;
            min-height: 114px;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--muted);
            font-size: .74rem;
            text-transform: uppercase;
            letter-spacing: .09em;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--white);
            font-size: 1.5rem;
            font-weight: 800;
        }}

        .hero {{
            position: relative;
            overflow: hidden;
            padding: 2rem 2.15rem 1.75rem 2.15rem;
            border-radius: 20px;
            margin-bottom: 1.25rem;
            background:
                linear-gradient(115deg, rgba(80,0,0,.96), rgba(52,15,17,.92) 52%, rgba(24,32,41,.96));
            border: 1px solid rgba(217,182,111,.38);
            box-shadow: 0 18px 48px rgba(0,0,0,.20);
        }}

        .hero:after {{
            content: "♠";
            position: absolute;
            right: 2rem;
            top: -2.4rem;
            font-size: 12rem;
            color: rgba(217,182,111,.12);
            pointer-events: none;
        }}

        .hero-eyebrow {{
            color: var(--goldlight);
            font-size: .74rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: .15em;
            margin-bottom: .5rem;
        }}

        .hero-title {{
            color: var(--white);
            font-size: clamp(2rem, 4vw, 3.5rem);
            font-weight: 900;
            line-height: 1.02;
            letter-spacing: -0.055em;
            max-width: 820px;
        }}

        .hero-copy {{
            color: #EEE6D9;
            font-size: 1.04rem;
            line-height: 1.55;
            max-width: 770px;
            margin-top: .7rem;
        }}

        .chip {{
            display: inline-block;
            padding: .28rem .65rem;
            border-radius: 999px;
            border: 1px solid rgba(217,182,111,.38);
            background: rgba(217,182,111,.11);
            color: var(--goldlight);
            font-size: .74rem;
            font-weight: 800;
            margin-top: .75rem;
            margin-right: .35rem;
        }}

        .section-kicker {{
            color: var(--gold);
            font-size: .70rem;
            font-weight: 850;
            letter-spacing: .13em;
            text-transform: uppercase;
            margin-bottom: .2rem;
        }}

        .decision-card {{
            background:
                linear-gradient(135deg, rgba(22,78,75,.44), rgba(23,31,40,.96));
            border: 1px solid rgba(101,198,189,.38);
            border-radius: 16px;
            padding: 1.05rem 1.2rem;
            margin: .85rem 0 1.15rem;
        }}

        .decision-label {{
            color: var(--teal);
            font-size: .72rem;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
            margin-bottom: .35rem;
        }}

        .callout {{
            border-left: 4px solid var(--gold);
            background: rgba(31,41,52,.88);
            border-radius: 10px;
            padding: .85rem 1rem;
            margin: .8rem 0 1rem;
            line-height: 1.5;
        }}

        .callout-teal {{
            border-left: 4px solid var(--teal);
            background: rgba(101,198,189,.09);
            border-radius: 10px;
            padding: .85rem 1rem;
            margin: .8rem 0 1rem;
            line-height: 1.5;
        }}

        .callout-warning {{
            border-left: 4px solid var(--red);
            background: rgba(255,117,107,.09);
            border-radius: 10px;
            padding: .85rem 1rem;
            margin: .8rem 0 1rem;
            line-height: 1.5;
        }}

        .pixel-panel {{
            background:
                linear-gradient(180deg, rgba(38,48,58,.97), rgba(21,28,36,.98));
            border: 3px solid #263442;
            border-top-color: #526576;
            border-left-color: #526576;
            border-radius: 8px;
            box-shadow:
                inset 0 0 0 2px rgba(0,0,0,.3),
                0 12px 28px rgba(0,0,0,.24);
            padding: 1rem;
            margin-bottom: 1rem;
        }}

        .pixel-title {{
            color: var(--goldlight);
            font-family: monospace;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-size: .86rem;
            margin-bottom: .7rem;
        }}

        .machine-screen {{
            background: #070A0C;
            border: 4px solid #536779;
            border-top-color: #839AAB;
            border-left-color: #839AAB;
            border-radius: 5px;
            box-shadow: inset 0 0 0 2px #020303;
            padding: .8rem;
            margin-bottom: .75rem;
            font-family: monospace;
        }}

        .machine-id {{
            color: var(--goldlight);
            font-weight: 900;
            font-size: 1.12rem;
            text-shadow: 0 0 7px rgba(246,219,156,.48);
        }}

        .machine-status {{
            color: var(--teal);
            font-size: .76rem;
            margin-top: .35rem;
        }}

        .pixel-light {{
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 5px;
            border-radius: 2px;
            background: var(--green);
            box-shadow: 0 0 9px rgba(104,199,126,.85);
            animation: glow 1.2s infinite alternate;
        }}

        @keyframes glow {{
            from {{ opacity: .5; }}
            to {{ opacity: 1; }}
        }}

        .machine-active {{
            animation: cabinetPulse .62s ease-in-out 3;
        }}

        @keyframes cabinetPulse {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-3px); filter: brightness(1.17); }}
        }}

        .score-good {{
            border-left: 6px solid var(--green);
            background: rgba(104,199,126,.10);
            border-radius: 12px;
            padding: 1rem;
        }}

        .score-neutral {{
            border-left: 6px solid var(--gold);
            background: rgba(217,182,111,.10);
            border-radius: 12px;
            padding: 1rem;
        }}

        .score-bad {{
            border-left: 6px solid var(--red);
            background: rgba(255,117,107,.10);
            border-radius: 12px;
            padding: 1rem;
        }}

        .score-title {{
            text-transform: uppercase;
            letter-spacing: .11em;
            font-size: .7rem;
            font-weight: 900;
            color: var(--muted);
        }}

        .score-number {{
            color: var(--white);
            font-size: 2.15rem;
            font-weight: 900;
            margin: .15rem 0;
        }}

        .zone-card {{
            background: rgba(26,35,45,.95);
            border: 1px solid rgba(217,182,111,.18);
            border-radius: 12px;
            padding: .75rem;
            min-height: 105px;
        }}

        .zone-name {{
            color: var(--white);
            font-weight: 850;
            font-size: .86rem;
            margin-bottom: .35rem;
        }}

        .zone-stat {{
            color: var(--goldlight);
            font-family: monospace;
            font-size: .78rem;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: .4rem;
            border-bottom: 1px solid rgba(217,182,111,.18);
        }}

        .stTabs [data-baseweb="tab"] {{
            color: var(--muted);
            border-radius: 8px 8px 0 0;
            padding: .64rem .85rem;
        }}

        .stTabs [aria-selected="true"] {{
            color: var(--goldlight) !important;
            background: rgba(217,182,111,.08);
        }}

        .stDataFrame {{
            border: 1px solid rgba(217,182,111,.15);
            border-radius: 10px;
            overflow: hidden;
        }}

        .footer-note {{
            color: #89949E;
            text-align: center;
            font-size: .78rem;
            padding: .5rem 0;
        }}

        @media (prefers-reduced-motion: reduce) {{
            *, *:before, *:after {{ animation: none !important; transition: none !important; }}
        }}
        @media (max-width: 1100px) {{
            [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ min-width: 220px; flex: 1 1 40%; }}
        }}
        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            .hero {{
                padding: 1.4rem;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_data(file_stamp):
    """Load derived dashboard data only."""
    required = [
        DATA_DIR / "analysis_results.json",
        DATA_DIR / "machines.parquet",
        DATA_DIR / "machine_daily.parquet",
        DATA_DIR / "guest_groups.parquet",
        DATA_DIR / "scenario_net.npz",
    ]

    missing = [str(path) for path in required if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Missing required files:\n\n" + "\n".join(missing)
        )

    report = json.loads(
        (DATA_DIR / "analysis_results.json").read_text(encoding="utf-8")
    )

    machines = pd.read_parquet(DATA_DIR / "machines.parquet")
    daily = pd.read_parquet(DATA_DIR / "machine_daily.parquet")
    guests = pd.read_parquet(DATA_DIR / "guest_groups.parquet")
    scenario_samples = np.load(DATA_DIR / "scenario_net.npz")["net"]

    property_path = DATA_DIR / "property_daily.parquet"

    if property_path.exists():
        property_daily = pd.read_parquet(property_path)
    else:
        property_daily = pd.DataFrame()

    daily["gaming_date"] = pd.to_datetime(daily["gaming_date"])
    variance = pd.read_parquet(DATA_DIR / "daily_variance.parquet")
    variance["gaming_date"] = pd.to_datetime(variance["gaming_date"])
    daily = daily.merge(variance, on=["machine_id", "gaming_date"], validate="one_to_one")
    metadata = json.loads((DATA_DIR / "forecast_metadata.json").read_text())
    actual_hash = hashlib.sha256((DATA_DIR / "machine_daily.parquet").read_bytes()).hexdigest()
    if actual_hash != metadata["base_daily_sha256"]:
        raise ValueError("Daily data changed. Run scripts/build_dashboard_data.py to refresh forecasts and floor exports.")

    if not property_daily.empty:
        property_daily["gaming_date"] = pd.to_datetime(
            property_daily["gaming_date"]
        )

    return (
        report,
        machines,
        daily,
        guests,
        scenario_samples,
        property_daily,
    )

# =============================================================================
# HELPERS
# =============================================================================

def money(value, decimals=0):
    """Format currency safely."""
    if value is None or pd.isna(value):
        return "—"

    value = float(value)
    output = f"${abs(value):,.{decimals}f}"

    return f"-{output}" if value < 0 else output

def pct(value, decimals=1):
    """Format percentage safely."""
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.{decimals}%}"

def safe_divide(numerator, denominator):
    """Avoid division errors."""
    if denominator is None or denominator == 0 or pd.isna(denominator):
        return np.nan

    return numerator / denominator

def chart(fig, title, key, height=None):
    """Apply shared Plotly visual styling."""
    fig.update_layout(
        title=dict(
            text=title,
            x=0.01,
            xanchor="left",
            font=dict(size=19, color=WHITE),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(color=WHITE, size=13),
        colorway=[GOLD, TEAL, PURPLE, RED],
        margin=dict(l=25, r=25, t=72, b=42),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        height=height,
    )

    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor="#5D6975",
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor="#5D6975",
    )

    st.plotly_chart(
        fig,
        width="stretch",
        key=key,
        config={
            "displaylogo": False,
            "toImageButtonOptions": {
                "format": "svg",
                "filename": key,
                "width": 1600,
                "height": 900,
            },
        },
    )

def download_table(df, filename, label="Download CSV"):
    """Create a downloadable CSV."""
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"{filename}.csv",
        mime="text/csv",
        key=f"download_{filename}",
    )

def section_header(kicker, title, copy=None):
    """Render a section header."""
    st.markdown(
        f"""
        <div class="section-kicker">{kicker}</div>
        <h2 style="margin-top:0;">{title}</h2>
        """,
        unsafe_allow_html=True,
    )

    if copy:
        st.write(copy)

def hero(title, subtitle, chips=None):
    """Render branded hero card."""
    chips = chips or []

    chip_html = "".join(
        f'<span class="chip">{chip}</span>'
        for chip in chips
    )

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-eyebrow">ACEIQ · THE GILDED ACE</div>
            <div class="hero-title">{title}</div>
            <div class="hero-copy">{subtitle}</div>
            <div>{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def callout(style, title, text):
    """Render a callout block."""
    css = {
        "default": "callout",
        "teal": "callout-teal",
        "warning": "callout-warning",
    }.get(style, "callout")

    st.markdown(
        f"""
        <div class="{css}">
            <strong>{title}</strong><br>
            {text}
        </div>
        """,
        unsafe_allow_html=True,
    )

def classification_recommendation(classification, eligible_july):
    """Give a safe next-step recommendation."""
    if not eligible_july:
        return (
            "No July floor action",
            "This machine is not on the July floor, so it should not be selected "
            "as a July action target.",
        )

    if classification == "Limited exposure":
        return ("Collect more operating history", "Fewer than 28 active days: avoid a confident replacement decision.")
    if classification == "Low expected demand":
        return ("Investigate demand and location", "Expected earnings per available hour are below same-theme peers. This is not proof of a hardware problem.")
    if classification == "Inspect configuration / meters":
        return (
            "Inspect configuration and meters first",
            "An unusually negative actual-versus-expected gap is a screening signal. "
            "Inspect game settings and meter history before considering replacement.",
        )

    if classification == "Downtime-constrained":
        return (
            "Address availability before replacement",
            "Low availability or substantial downtime opportunity means this machine "
            "may not have received a fair chance to earn.",
        )

    if classification == "Monitor payout variance":
        return (
            "Monitor against exposure-adjusted peers",
            "The machine is below expected in this period, but normal payout variation "
            "remains a plausible explanation.",
        )

    return (
        "Monitor before spending",
        "The available evidence does not establish that moving or replacing this "
        "machine would outperform keeping the budget.",
    )

# =============================================================================
# LOAD DATA
# =============================================================================

try:
    (
        report,
        machines,
        daily,
        guests,
        samples,
        property_daily,
    ) = load_data(tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(DATA_DIR.iterdir()) if p.is_file()))
    predictions = pd.read_parquet(DATA_DIR / "demand_predictions.parquet")
    predictions["gaming_date"] = pd.to_datetime(predictions["gaming_date"])
    forecast_metadata = json.loads((DATA_DIR / "forecast_metadata.json").read_text())
    locations = pd.read_parquet(DATA_DIR / "floor_locations.parquet")
    placements = pd.read_parquet(DATA_DIR / "placements.parquet")
    walkways = pd.read_parquet(DATA_DIR / "floor_walkways.parquet")

except Exception as error:
    st.error("AceIQ could not load the required derived data files.")
    st.code(str(error))
    st.info(
        "Confirm that `data/` contains the precomputed dashboard outputs, "
        "then restart Streamlit."
    )
    st.stop()

# =============================================================================
# SIDEBAR
# =============================================================================

st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-title">♠ ACEIQ</div>
        <div class="sidebar-subtitle">GILDED ACE · DECISION INTELLIGENCE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "NAVIGATE",
    [
        "Executive overview",
        "Machine investigation",
        "$100,000 decision lab",
    ],
)

st.sidebar.divider()

st.sidebar.caption("EVIDENCE PERIOD")
st.sidebar.write("January 1 – June 30, 2025")

st.sidebar.caption("DECISION HORIZON")
st.sidebar.write("July 1 – July 30, 2025")

st.sidebar.divider()

min_date = daily["gaming_date"].min().date()
max_date = daily["gaming_date"].max().date()

selected_dates = st.sidebar.date_input(
    "Dashboard evidence period",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(selected_dates, (tuple, list)):
    if len(selected_dates) != 2:
        st.info("Choose both a start date and an end date to update the evidence.")
        st.stop()
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

filtered_daily = daily[
    (daily["gaming_date"] >= start_date)
    & (daily["gaming_date"] <= end_date)
].copy()

if filtered_daily.empty:
    st.error("No machine records exist in that selected date range.")
    st.stop()

if not property_daily.empty:
    filtered_property = property_daily[
        (property_daily["gaming_date"] >= start_date)
        & (property_daily["gaming_date"] <= end_date)
    ].copy()
else:
    filtered_property = pd.DataFrame()

machine_summary = build_machine_summary(filtered_daily, machines)

st.sidebar.divider()

st.sidebar.markdown(
    """
    <div style="
        background:rgba(101,198,189,.10);
        border:1px solid rgba(101,198,189,.28);
        border-radius:11px;
        padding:.75rem;
        font-size:.80rem;
        color:#D7F0ED;
    ">
        <strong>Decision guardrail</strong><br><br>
        Observed associations are not causal proof. Scenario results depend on
        stated assumptions and should be tested with a comparison group.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar.expander("Metric definitions"):
    st.write(
        "**Actual earnings** = wagers − payouts.\n\n"
        "**Expected earnings** = wagers × (1 − configured RTP).\n\n"
        "**Downtime opportunity** = historical machine opportunity estimate, "
        "not guaranteed recoverable floor revenue."
    )

st.sidebar.caption("Synthetic Dashboard Royale data only.")

with st.sidebar.expander("Judge guide & evidence"):
    st.write("Change dates, investigate a bank, inspect the held-out forecast, then trace an action to its evidence. The floor previews hypothetical moves; it is not live casino activity.")
    for label, relative, filename in [
        ("Download judging / startup guide", "JUDGE_START_HERE.md", "AceIQ_Judge_Guide.md"),
        ("Download Claims & Evidence", "docs/CLAIMS_AND_EVIDENCE.md", "AceIQ_Claims_and_Evidence.md"),
        ("Download AI disclosure", "docs/AI_DISCLOSURE.md", "AceIQ_AI_Disclosure.md"),
    ]:
        st.download_button(label, (ROOT / relative).read_text(encoding="utf-8"), filename, mime="text/markdown", key=filename)

# =============================================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# =============================================================================

if page == "Executive overview":
    hero(
        "Read the floor. Question the ranking.",
        (
            "AceIQ helps leadership distinguish short exposure, downtime, payout "
            "variance, location context, and persistent performance gaps before "
            "spending on replacements."
        ),
        [
            "Exposure-adjusted",
            "Luck-aware",
            "Scenario-tested",
        ],
    )

    if not filtered_property.empty:
        total_wagers = filtered_property["coin_in_usd"].sum()
        total_actual = filtered_property["house_win_usd"].sum()
        total_expected = filtered_property["theo_usd"].sum()
        total_comps = filtered_property["comp_cost_usd"].sum()
    else:
        total_wagers = filtered_daily["coin_in_usd"].sum()
        total_actual = filtered_daily["house_win_usd"].sum()
        total_expected = filtered_daily["theo_usd"].sum()
        total_comps = np.nan

    actual_hold = safe_divide(total_actual, total_wagers)

    total_downtime_opportunity = machine_summary[
        "estimated_downtime_opportunity"
    ].sum()

    actual_vs_expected = total_actual - total_expected

    st.markdown(
        """
        <div class="decision-card">
            <div class="decision-label">Executive recommendation</div>
            <div style="font-size:1.04rem;line-height:1.55;color:#F2F5F5;">
                Do not automatically replace the ten lowest-earning machines.
                First separate short exposure, downtime, payout variance, and
                location context. Explore the demand forecast and floor map, then
                compare July actions in the Decision Lab. Inspection can have learning
                value even when an immediate cash benefit is unproven.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_header(
        "Floor snapshot",
        "What happened during the selected evidence period?",
        "Floor totals give context, but machine-level diagnosis requires exposure, availability, and payout-variance checks.",
    )

    metrics = st.columns(5)
    metrics[0].metric("Total wagers", money(total_wagers))
    metrics[1].metric("Actual earnings", money(total_actual))
    metrics[2].metric("Expected earnings", money(total_expected))
    metrics[3].metric("Actual hold", pct(actual_hold, 2))
    metrics[4].metric(
        "Downtime opportunity",
        money(total_downtime_opportunity),
    )

    callout(
        "default",
        "Floor-wide context",
        (
            f"Actual earnings were <strong>{money(actual_vs_expected)}</strong> relative "
            "to expected earnings during the selected period. That aggregate result does "
            "not diagnose individual machines because machines differ in availability, "
            "location, exposure, and payout variation."
        ),
    )

    demand_tab, guest_tab, comp_tab, forecast_tab = st.tabs(
        [
            "Demand & location",
            "Tracked guests",
            "Comp economics",
            "Predictions vs actual",
        ]
    )

    with demand_tab:
        section_header(
            "Demand & location",
            "Where did demand strengthen or soften?",
            "Use exposure-adjusted demand metrics before concluding that the floor became stronger or weaker.",
        )

        if not filtered_property.empty:
            monthly = (
                filtered_property.assign(
                    month=filtered_property["gaming_date"].dt.strftime("%Y-%m")
                )
                .groupby("month", as_index=False)
                .agg(
                    days=("gaming_date", "nunique"),
                    wagers=("coin_in_usd", "sum"),
                    available_hours=("available_machine_hours", "sum"),
                )
            )

            monthly["wagers_per_day"] = monthly["wagers"] / monthly["days"]

            monthly["wagers_per_available_hour"] = (
                monthly["wagers"]
                / monthly["available_hours"].replace(0, np.nan)
            )

            demand_lens = st.radio(
                "Choose demand lens",
                [
                    "Wagers per available machine-hour",
                    "Wagers per day",
                    "Total wagers",
                ],
                horizontal=True,
            )

            demand_column = {
                "Wagers per available machine-hour": "wagers_per_available_hour",
                "Wagers per day": "wagers_per_day",
                "Total wagers": "wagers",
            }[demand_lens]

            demand_fig = px.area(
                monthly,
                x="month",
                y=demand_column,
                markers=True,
                color_discrete_sequence=[GOLD],
                labels={
                    "month": "Month",
                    demand_column: f"{demand_lens} ($)",
                },
            )

            demand_fig.update_traces(
                line=dict(width=4),
                fillcolor="rgba(217,182,111,.16)",
            )

            demand_fig.update_yaxes(
                tickprefix="$",
                rangemode="tozero",
            )

            chart(
                demand_fig,
                f"{demand_lens} by month",
                "monthly_demand",
                height=400,
            )

        zone_summary = (
            filtered_daily.groupby("zone_name", as_index=False)
            .agg(
                wagers=("coin_in_usd", "sum"),
                expected=("theo_usd", "sum"),
                available_hours=("available_hours", "sum"),
                downtime_hours=("down_hours", "sum"),
            )
        )

        zone_summary["wagers_per_available_hour"] = (
            zone_summary["wagers"]
            / zone_summary["available_hours"].replace(0, np.nan)
        )

        left, right = st.columns(2)

        with left:
            zone_fig = px.bar(
                zone_summary.sort_values("wagers_per_available_hour"),
                x="wagers_per_available_hour",
                y="zone_name",
                orientation="h",
                color="wagers_per_available_hour",
                color_continuous_scale=[
                    [0, MAROON],
                    [0.5, GOLD],
                    [1, TEAL],
                ],
                labels={
                    "zone_name": "Zone",
                    "wagers_per_available_hour": "Wagers per available hour ($)",
                },
            )

            zone_fig.update_layout(coloraxis_showscale=False)
            zone_fig.update_xaxes(tickprefix="$")

            chart(
                zone_fig,
                "Observed demand efficiency by zone",
                "zone_demand",
                height=420,
            )

        with right:
            event_associations = pd.DataFrame(
                report.get("event_associations", [])
            )

            st.caption("Event comparison: full January–June reference, independent of the evidence date filter.")
            if not event_associations.empty:
                event_fig = px.bar(
                    event_associations.sort_values("difference_pct"),
                    x="difference_pct",
                    y="event",
                    orientation="h",
                    color="difference_pct",
                    color_continuous_scale=[
                        [0, RED],
                        [0.5, GOLD],
                        [1, TEAL],
                    ],
                    labels={
                        "event": "Event",
                        "difference_pct": "Difference from weekday baseline",
                    },
                )

                event_fig.update_layout(coloraxis_showscale=False)
                event_fig.update_xaxes(tickformat=".0%")

                chart(
                    event_fig,
                    "Event-day associations",
                    "event_associations",
                    height=420,
                )

        callout(
            "warning",
            "Do not treat zone differences as causal proof.",
            (
                "A low-demand zone can reflect traffic, amenities, machine mix, guest "
                "preferences, and overlapping events. Traffic sensors count entries, "
                "not unique visitors. This zone chart uses machine wagers and available hours, not sensor counts."
            ),
        )

        with st.expander("Open demand evidence and download tables"):
            st.dataframe(
                zone_summary.sort_values(
                    "wagers_per_available_hour",
                    ascending=False,
                ),
                width="stretch",
                hide_index=True,
            )

            download_table(
                zone_summary,
                "aceiq_zone_demand",
                "Download zone evidence",
            )

            if not filtered_property.empty:
                st.dataframe(
                    monthly,
                    width="stretch",
                    hide_index=True,
                )

                download_table(
                    monthly,
                    "aceiq_monthly_demand",
                    "Download monthly demand",
                )

    with guest_tab:
        section_header(
            "Tracked guest outcomes",
            "What did loyalty-card guests wager, receive, and net?",
            "Tracked guests are not the full casino population. These results exclude uncarded play.",
        )

        st.info("Player headline totals and concentration below cover January–June in full. Monthly group comparisons below use separate month controls; daily player outcomes are not available in this export.")
        player_summary = report["players"]

        guest_metrics = st.columns(4)
        guest_metrics[0].metric(
            "Tracked players",
            f"{player_summary['tracked_players']:,}",
        )
        guest_metrics[1].metric(
            "Tracked wager coverage",
            pct(player_summary["tracked_wager_coverage"]),
        )
        guest_metrics[2].metric(
            "Tracked wagers",
            money(player_summary["tracked_wagers"]),
        )
        guest_metrics[3].metric(
            "Player net",
            money(player_summary["player_net"]),
        )

        st.write(
            f"Tracked guests received **{money(player_summary['tracked_payouts'])}** "
            f"in payouts, and **{player_summary['players_ahead_share']:.1%}** "
            "finished ahead across their recorded six-month play."
        )

        concentration = pd.DataFrame(
            {
                "Group": [
                    "Top 1% of tracked players",
                    "Other tracked players",
                ],
                "Share of tracked wagers": [
                    player_summary["top1pct_wager_share"],
                    1 - player_summary["top1pct_wager_share"],
                ],
            }
        )

        concentration_fig = px.bar(
            concentration,
            x="Group",
            y="Share of tracked wagers",
            color="Group",
            text="Share of tracked wagers",
            color_discrete_map={
                "Top 1% of tracked players": GOLD,
                "Other tracked players": TEAL,
            },
        )

        concentration_fig.update_layout(showlegend=False)
        concentration_fig.update_traces(
            texttemplate="%{text:.1%}",
            textposition="outside",
        )
        concentration_fig.update_yaxes(
            tickformat=".0%",
            range=[0, 1],
        )

        chart(
            concentration_fig,
            "Tracked wager concentration",
            "tracked_wager_concentration",
            height=380,
        )

        callout(
            "warning",
            "Ethical guest-data guardrail",
            (
                "Do not use tracked-player data to push people with high losses to "
                "gamble more. Group comparisons are descriptive only. Comp recommendations "
                "should be ethical, randomized where appropriate, and focused on voluntary "
                "hospitality or non-gaming value."
            ),
        )

        available_months = sorted(
            guests["period_month"].astype(str).unique()
        )

        selected_guest_months = [
            month
            for month in available_months
            if start_date.strftime("%Y-%m")
            <= month
            <= end_date.strftime("%Y-%m")
        ]

        selected_guest_months = st.multiselect("Guest comparison months (whole months)", available_months, default=selected_guest_months, key="guest_months")
        st.caption("Group totals include complete selected months, including when the sidebar dates start or end mid-month.")
        filtered_guests = guests[
            guests["period_month"].astype(str).isin(selected_guest_months)
        ].copy()

        grouping = st.selectbox(
            "Compare tracked guest groups by",
            ["home_region", "age_band"],
            format_func=lambda item: item.replace("_", " ").title(),
        )

        grouped_guests = (
            filtered_guests.groupby(grouping, as_index=False)[
                ["wagers", "payouts", "player_net", "comp_cost"]
            ]
            .sum()
            .sort_values("wagers", ascending=False)
        )

        st.dataframe(
            grouped_guests,
            width="stretch",
            hide_index=True,
        )

        download_table(
            grouped_guests,
            "aceiq_guest_groups",
            "Download tracked-guest comparison",
        )

    with comp_tab:
        section_header(
            "Comp economics",
            "What did the loyalty program cost, and what changed?",
            "Economic comp cost and face value are not interchangeable.",
        )

        loyalty = pd.DataFrame(report.get("loyalty", []))

        if not loyalty.empty:
            loyalty = loyalty[
                loyalty["gaming_month"].astype(str).between(
                    start_date.strftime("%Y-%m"),
                    end_date.strftime("%Y-%m"),
                )
            ]

        st.caption("Redemptions and points pricing cover whole months intersecting the evidence period. The cost below uses those same whole months.")
        comp_months = loyalty["gaming_month"].astype(str).tolist() if not loyalty.empty else []
        comp_period = property_daily[property_daily.gaming_date.dt.strftime("%Y-%m").isin(comp_months)]
        total_comps = comp_period.comp_cost_usd.sum()
        comp_metrics = st.columns(3)

        comp_metrics[0].metric(
            "Economic comp cost",
            money(total_comps),
        )

        if not loyalty.empty:
            comp_metrics[1].metric(
                "Recorded redemptions",
                f"{int(loyalty['redemptions'].sum()):,}",
            )

            points_per_dollar = (
                loyalty["points_delta"].abs().sum()
                / (loyalty["face_cents"].sum() / 100)
                if loyalty["face_cents"].sum() > 0
                else np.nan
            )

            comp_metrics[2].metric(
                "Points per face-value $",
                f"{points_per_dollar:,.1f}"
                if pd.notna(points_per_dollar)
                else "—",
            )

        if not loyalty.empty:
            loyalty_fig = px.line(
                loyalty,
                x="gaming_month",
                y="points_per_face_dollar",
                markers=True,
                color_discrete_sequence=[GOLD],
                labels={
                    "gaming_month": "Month",
                    "points_per_face_dollar": "Redeemed points per $1 face value",
                },
            )

            loyalty_fig.update_traces(
                line=dict(width=4),
                marker=dict(size=10),
            )

            chart(
                loyalty_fig,
                "Observed redemption pricing over time",
                "loyalty_pricing",
                height=430,
            )

            callout(
                "default",
                "Interpret carefully",
                (
                    "Observed redemption economics changed over time, but that does not "
                    "prove one policy caused the shift. Guest mix, redemption choices, "
                    "and promotion timing can also matter."
                ),
            )

            with st.expander("Open loyalty evidence table"):
                st.dataframe(
                    loyalty,
                    width="stretch",
                    hide_index=True,
                )

                download_table(
                    loyalty,
                    "aceiq_loyalty_economics",
                    "Download loyalty evidence",
                )
        else:
            st.info("No loyalty data exists for the selected date range.")

    with forecast_tab:
        render_forecast(predictions, forecast_metadata)

# =============================================================================
# PAGE 2 — MACHINE INVESTIGATION
# =============================================================================

elif page == "Machine investigation":
    hero(
        "Low earnings are a clue, not a verdict.",
        (
            "Compare actual earnings, expected earnings, exposure, availability, "
            "downtime, and payout variation before recommending a replacement."
        ),
        [
            "Actual vs. expected",
            "Availability-adjusted",
            "Inspection before accusation",
        ],
    )

    section_header(
        "Bottom-ten comparison",
        "Does the bottom-ten list change when you use fairer metrics?",
        "Raw total earnings can make machines with short exposure, downtime, or recent installation appear weaker than they are.",
    )

    machine_bank = st.selectbox("Investigate a bank", ["All banks"] + sorted(filtered_daily.bank_id.dropna().unique()), key="investigation_bank")
    if machine_bank != "All banks":
        filtered_daily = filtered_daily[filtered_daily.bank_id == machine_bank]
        machine_summary = build_machine_summary(filtered_daily, machines)
    ranking_basis = st.radio(
        "Rank low performers by",
        [
            "Total actual earnings",
            "Actual earnings per active day",
            "Expected earnings per available hour",
        ],
        horizontal=True,
    )

    ranking_column = {
        "Total actual earnings": "actual_house_win",
        "Actual earnings per active day": "actual_per_active_day",
        "Expected earnings per available hour": "expected_per_available_hour",
    }[ranking_basis]

    bottom_ten = (
        machine_summary.sort_values([ranking_column, "machine_id"])
        .head(10)
        .copy()
    )

    if ranking_basis == "Total actual earnings":
        actual_values = bottom_ten["actual_house_win"]
        expected_values = bottom_ten["expected_house_win"]
        x_label = "Casino earnings before costs ($)"

    elif ranking_basis == "Actual earnings per active day":
        actual_values = bottom_ten["actual_per_active_day"]
        expected_values = (
            bottom_ten["expected_house_win"]
            / bottom_ten["active_days"].replace(0, np.nan)
        )
        x_label = "Casino earnings per active day ($)"

    else:
        actual_values = bottom_ten["actual_per_available_hour"]
        expected_values = bottom_ten["expected_per_available_hour"]
        x_label = "Casino earnings per available hour ($)"

    bottom_fig = go.Figure()

    bottom_fig.add_bar(
        y=bottom_ten["machine_id"],
        x=actual_values,
        orientation="h",
        name="Actual",
        marker_color=GOLD,
    )

    bottom_fig.add_bar(
        y=bottom_ten["machine_id"],
        x=expected_values,
        orientation="h",
        name="Expected",
        marker_color=TEAL,
    )

    bottom_fig.update_layout(
        barmode="group",
        height=560,
    )

    bottom_fig.update_yaxes(
        autorange="reversed",
        title="Machine",
    )

    bottom_fig.update_xaxes(
        title=x_label,
        tickprefix="$",
    )

    chart(
        bottom_fig,
        f"Bottom 10 · {ranking_basis.lower()}",
        "bottom_ten_machines",
        height=590,
    )

    callout(
        "default",
        "Why this matters",
        (
            "If the bottom-ten list changes after adjusting for active days or available "
            "hours, a raw total-earnings replacement strategy is not adequately supported."
        ),
    )

    export_columns = [
        "machine_id",
        "theme",
        "manufacturer",
        "actual_house_win",
        "expected_house_win",
        "actual_minus_expected",
        "active_days",
        "availability_rate",
        "downtime_hours",
        "estimated_downtime_opportunity",
        "eligible_july",
    ]

    export_columns = [
        col for col in export_columns
        if col in bottom_ten.columns
    ]

    download_table(
        bottom_ten[export_columns],
        "aceiq_bottom_ten",
        "Download bottom-ten diagnostic table",
    )

    st.divider()

    section_header(
        "Machine deep dive",
        "Follow the evidence before choosing an action.",
        "Use this machine-level diagnostic view to distinguish downtime, exposure, payout variation, and performance concerns.",
    )

    available_machines = sorted(machine_summary["machine_id"].astype(str))

    default_machine = (
        "M-1158"
        if "M-1158" in available_machines
        else available_machines[0]
    )

    selected_machine = st.selectbox(
        "Choose a machine",
        available_machines,
        index=available_machines.index(default_machine),
    )

    machine = machine_summary.set_index("machine_id").loc[selected_machine]
    classification = machine_category(machine)

    recommendation_title, recommendation_text = classification_recommendation(
        classification,
        bool(machine.get("eligible_july", False)),
    )

    st.markdown(
        f"""
        <div class="pixel-panel">
            <div class="pixel-title">Machine diagnostic terminal</div>
            <div class="machine-screen">
                <div class="machine-id">♠ {selected_machine}</div>
                <div class="machine-status">
                    <span class="pixel-light"></span>
                    STATUS: {classification.upper()}
                </div>
            </div>
            <div style="color:#DDE2E6;">
                <strong>{recommendation_title}</strong><br>
                {recommendation_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    machine_metrics = st.columns(5)
    machine_metrics[0].metric(
        "Active days",
        f"{int(machine['active_days']):,}",
    )
    machine_metrics[1].metric(
        "Availability",
        pct(machine["availability_rate"]),
    )
    machine_metrics[2].metric(
        "Downtime hours",
        f"{machine['downtime_hours']:.1f}",
    )
    machine_metrics[3].metric(
        "Actual − expected",
        money(machine["actual_minus_expected"]),
    )
    machine_metrics[4].metric(
        "Downtime opportunity",
        money(machine["estimated_downtime_opportunity"]),
    )

    evidence = pd.DataFrame(
        [
            {
                "Evidence": "Actual earnings",
                "Value": money(machine["actual_house_win"]),
                "Meaning": "Observed casino earnings before baseline operating costs.",
            },
            {
                "Evidence": "Expected earnings",
                "Value": money(machine["expected_house_win"]),
                "Meaning": "Wagers × configured expected hold.",
            },
            {
                "Evidence": "Availability",
                "Value": pct(machine["availability_rate"]),
                "Meaning": "Available operating hours divided by scheduled hours.",
            },
            {
                "Evidence": "Downtime opportunity",
                "Value": money(machine["estimated_downtime_opportunity"]),
                "Meaning": "Historical opportunity estimate, not guaranteed lost revenue.",
            },
            {
                "Evidence": "Standardized payout deviation",
                "Value": (
                    f"{machine.get('standardized_gap', np.nan):.2f}"
                    if pd.notna(machine.get("standardized_gap", np.nan))
                    else "—"
                ),
                "Meaning": "Selected-period screening signal based on supplied game variance; not a confirmed fault.",
            },
        ]
    )

    st.markdown("### Evidence trail")
    st.dataframe(
        evidence,
        width="stretch",
        hide_index=True,
    )

    selected_daily = (
        filtered_daily[
            filtered_daily["machine_id"].astype(str) == selected_machine
        ]
        .sort_values("gaming_date")
        .copy()
    )

    selected_daily["cumulative_actual"] = (
        selected_daily["house_win_usd"].cumsum()
    )

    selected_daily["cumulative_expected"] = (
        selected_daily["theo_usd"].cumsum()
    )

    left, right = st.columns([1.4, 1])

    with left:
        machine_fig = go.Figure()

        machine_fig.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_actual"],
            name="Cumulative actual",
            line=dict(color=GOLD, width=3),
        )

        machine_fig.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_expected"],
            name="Cumulative expected",
            line=dict(color=TEAL, width=3),
        )

        machine_fig.update_yaxes(
            title="Cumulative earnings ($)",
            tickprefix="$",
        )

        chart(
            machine_fig,
            f"{selected_machine} · actual versus expected",
            "machine_actual_expected",
            height=430,
        )

    with right:
        selected_daily["daily_availability"] = (
            selected_daily["available_hours"]
            / selected_daily["scheduled_hours"].replace(0, np.nan)
        )

        availability_fig = px.bar(
            selected_daily,
            x="gaming_date",
            y="daily_availability",
            color="daily_availability",
            color_continuous_scale=[
                [0, RED],
                [0.7, GOLD],
                [1, TEAL],
            ],
            labels={
                "gaming_date": "Date",
                "daily_availability": "Availability",
            },
        )

        availability_fig.update_layout(coloraxis_showscale=False)
        availability_fig.update_yaxes(
            tickformat=".0%",
            range=[0, 1.05],
        )

        chart(
            availability_fig,
            f"{selected_machine} · daily availability",
            "machine_availability",
            height=430,
        )

    with st.expander("Open all selected-period machine diagnostics"):
        diagnostic_table = machine_summary.copy()
        diagnostic_table["classification"] = diagnostic_table.apply(
            machine_category,
            axis=1,
        )

        st.dataframe(
            diagnostic_table.sort_values("actual_house_win"),
            width="stretch",
            hide_index=True,
        )

        download_table(
            diagnostic_table,
            "aceiq_machine_diagnostics",
            "Download full machine diagnostics",
        )

# =============================================================================
# PAGE 3 — DECISION LAB
# =============================================================================

else:
    render_decision(report, daily, machines, property_daily, predictions, locations, placements, walkways, start_date, end_date)

# =============================================================================
# FOOTER
# =============================================================================

st.divider()

st.markdown(
    """
    <div class="footer-note">
        ACEIQ · THE GILDED ACE DECISION INTELLIGENCE<br>
        Synthetic Dashboard Royale data · Actual and expected earnings are before
        baseline operating costs unless explicitly labeled as modeled net benefit.
        Scenario tools support decisions under assumptions; they do not prove causality.
    </div>
    """,
    unsafe_allow_html=True,
)
