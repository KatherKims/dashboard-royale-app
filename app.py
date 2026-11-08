"""
AceIQ: Gilded Ace Decision Intelligence
========================================
Run locally:
    python3 -m streamlit run app.py

Required files inside data/:
    analysis_results.json
    machines.parquet
    machine_daily.parquet
    guest_groups.parquet
    property_daily.parquet
    scenario_net.npz

Optional local files:
    floor_locations.parquet
    placements.parquet
    floor_walkways.parquet
    daily_variance.parquet
    demand_predictions.parquet
    forecast_metadata.json

This application uses local synthetic data only.
No external API or generative model is used at runtime.
"""

from pathlib import Path
import html
import json
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.retro_style import masthead, stylesheet


# =============================================================================
# CONFIGURATION
# =============================================================================

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"

BG = "#0A1118"
PANEL = "#17222C"
PANEL_DARK = "#101A22"
WHITE = "#F8F3EA"
MUTED = "#A7B7C2"
GOLD = "#E8BD63"
GOLD_LIGHT = "#F8DA92"
TEAL = "#69D6CB"
GREEN = "#62CA85"
RED = "#F1786C"
ORANGE = "#F3A85B"
PURPLE = "#B88BFF"
BLUE = "#77BDF5"
GRAY = "#7B8993"
GRID = "#31404D"

MAX_BUDGET = 100_000
MAX_ACTION_TYPES = 3
JULY_HORIZON_DAYS = 30

st.set_page_config(
    page_title="AceIQ | Gilded Ace Decision Intelligence",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# VISUAL STYLE
# =============================================================================

# This retains your existing dashboard's design language. The external
# dashboard.retro_style stylesheet and masthead are still used unchanged.
st.markdown(
    f"""
    <style>
        :root {{
            --bg: {BG};
            --panel: {PANEL};
            --panel-dark: {PANEL_DARK};
            --white: {WHITE};
            --muted: {MUTED};
            --gold: {GOLD};
            --gold-light: {GOLD_LIGHT};
            --teal: {TEAL};
            --green: {GREEN};
            --red: {RED};
            --orange: {ORANGE};
            --purple: {PURPLE};
            --blue: {BLUE};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 6% 0%, rgba(110,0,0,.25), transparent 25%),
                radial-gradient(circle at 96% 0%, rgba(232,189,99,.08), transparent 24%),
                linear-gradient(180deg, #0A1118 0%, #091017 100%);
            color: var(--white);
        }}

        .block-container {{
            max-width: 1420px;
            padding-top: .8rem;
            padding-bottom: 2rem;
        }}

        header[data-testid="stHeader"] {{
            background: rgba(10,17,24,.88);
        }}

        h1, h2, h3, h4 {{
            color: var(--white) !important;
        }}

        h2 {{
            margin: .15rem 0 .35rem !important;
            letter-spacing: -.035em;
        }}

        h3 {{
            margin: .2rem 0 .35rem !important;
        }}

        .topbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            padding: .85rem 1.1rem;
            margin-bottom: .8rem;
            border: 1px solid rgba(232,189,99,.35);
            border-radius: 15px;
            background:
                linear-gradient(105deg, rgba(75,0,0,.95), rgba(24,34,44,.98));
            box-shadow: 0 12px 28px rgba(0,0,0,.22);
        }}

        .brand {{
            color: var(--gold);
            font-size: 1.1rem;
            font-weight: 950;
            letter-spacing: .14em;
        }}

        .brand-sub {{
            color: #E8DED0;
            font-size: .66rem;
            letter-spacing: .10em;
            text-transform: uppercase;
            margin-top: .12rem;
        }}

        .top-note {{
            color: #D5E0E4;
            text-align: right;
            font-size: .73rem;
            line-height: 1.4;
        }}

        .eyebrow {{
            color: var(--gold);
            font-size: .67rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .12em;
        }}

        .subtle {{
            color: #C8D2D8;
            font-size: .84rem;
            line-height: 1.45;
        }}

        .hero {{
            position: relative;
            overflow: hidden;
            margin: .65rem 0 .8rem;
            padding: 1.05rem 1.15rem;
            border: 1px solid rgba(105,214,203,.36);
            border-radius: 14px;
            background:
                linear-gradient(135deg, rgba(16,79,73,.44), rgba(18,27,36,.96));
        }}

        .hero::after {{
            content: "♠";
            position: absolute;
            top: -2.2rem;
            right: 1.2rem;
            color: rgba(232,189,99,.10);
            font-size: 8rem;
            pointer-events: none;
        }}

        .panel {{
            padding: .85rem .95rem;
            border: 1px solid rgba(232,189,99,.18);
            border-radius: 12px;
            background:
                linear-gradient(145deg, rgba(28,40,52,.98), rgba(16,25,33,.98));
        }}

        .finding {{
            min-height: 150px;
            padding: .9rem;
            border: 1px solid rgba(232,189,99,.16);
            border-radius: 12px;
            background: rgba(24,36,47,.88);
            line-height: 1.45;
        }}

        .finding-number {{
            color: var(--gold);
            font-size: .68rem;
            font-weight: 950;
            letter-spacing: .11em;
            text-transform: uppercase;
        }}

        .notice,
        .warning,
        .success,
        .purple,
        .insight {{
            margin: .65rem 0;
            padding: .72rem .85rem;
            border-radius: 9px;
            font-size: .82rem;
            line-height: 1.48;
        }}

        .notice {{
            border-left: 4px solid var(--blue);
            color: #E6F2FF;
            background: rgba(119,189,245,.10);
        }}

        .warning {{
            border-left: 4px solid var(--orange);
            color: #F2E8DC;
            background: rgba(243,168,91,.10);
        }}

        .success {{
            border-left: 4px solid var(--teal);
            color: #E4F8F4;
            background: rgba(105,214,203,.10);
        }}

        .purple {{
            border-left: 4px solid var(--purple);
            color: #F1EBFF;
            background: rgba(184,139,255,.10);
        }}

        .insight {{
            border-left: 4px solid var(--teal);
            color: #EAF8F5;
            background:
                linear-gradient(135deg, rgba(22,69,70,.48), rgba(19,29,38,.90));
        }}

        .insight.warning {{
            border-left-color: var(--orange);
            background:
                linear-gradient(135deg, rgba(89,54,26,.44), rgba(25,29,34,.92));
        }}

        .insight.purple {{
            border-left-color: var(--purple);
            background:
                linear-gradient(135deg, rgba(61,39,98,.42), rgba(24,27,37,.92));
        }}

        .insight.blue {{
            border-left-color: var(--blue);
            background:
                linear-gradient(135deg, rgba(33,67,94,.42), rgba(24,27,37,.92));
        }}

        .insight-label {{
            margin-bottom: .2rem;
            color: var(--gold);
            font-size: .64rem;
            font-weight: 950;
            letter-spacing: .11em;
            text-transform: uppercase;
        }}

        .status-pill {{
            display: inline-block;
            padding: .25rem .55rem;
            border-radius: 999px;
            font-size: .67rem;
            font-weight: 900;
        }}

        [data-testid="stMetric"] {{
            min-height: 82px;
            background:
                linear-gradient(145deg, rgba(27,39,50,.98), rgba(15,24,32,.98));
            border: 1px solid rgba(232,189,99,.15);
            border-radius: 11px;
            padding: .62rem .72rem;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--muted);
            font-size: .64rem;
            text-transform: uppercase;
            letter-spacing: .06em;
        }}

        [data-testid="stMetricValue"] {{
            color: var(--white);
            font-weight: 850;
            font-size: 1.18rem;
        }}

        .footer {{
            color: #80919D;
            text-align: center;
            font-size: .7rem;
            padding: 1rem 0 .2rem;
        }}

        .quality-row {{
            margin: .45rem 0;
            padding: .55rem .7rem;
            border: 1px solid rgba(232,189,99,.13);
            border-radius: 8px;
            background: rgba(22,33,43,.72);
            color: #DCE7EA;
            font-size: .80rem;
        }}

        .quality-pass {{
            color: #82DA9B;
            font-weight: 900;
        }}

        .quality-warn {{
            color: #F4BA6A;
            font-weight: 900;
        }}

        .quality-fail {{
            color: #F48175;
            font-weight: 900;
        }}

        /* Evidence Claw */
        .claw-cabinet {{
            width: 100%;
            box-sizing: border-box;
            overflow: hidden;
            padding: 14px;
            border: 6px solid #642E13;
            border-top-color: #B66A23;
            border-left-color: #B66A23;
            border-radius: 19px 19px 11px 11px;
            background:
                radial-gradient(circle at 50% 12%, rgba(255,229,142,.13), transparent 25%),
                linear-gradient(145deg, #68151D 0%, #350A13 48%, #151C27 100%);
            box-shadow:
                inset 0 0 0 2px rgba(255,218,118,.16),
                inset 0 -13px 25px rgba(0,0,0,.28),
                0 9px 20px rgba(0,0,0,.25);
        }}

        .claw-neon {{
            color: #FFE29A;
            text-align: center;
            font-size: .68rem;
            font-weight: 950;
            letter-spacing: .12em;
            text-shadow: 0 0 8px rgba(255,205,92,.7);
        }}

        .claw-glass {{
            position: relative;
            height: 230px;
            margin-top: 9px;
            overflow: hidden;
            border: 4px solid #7898AA;
            border-top-color: #C7E9F1;
            border-left-color: #C7E9F1;
            border-radius: 8px;
            background:
                linear-gradient(115deg, rgba(255,255,255,.12), transparent 30%),
                linear-gradient(180deg, #253D4E, #0B1720);
        }}

        .claw-rail {{
            position: absolute;
            top: 14px;
            left: 10%;
            width: 80%;
            height: 4px;
            background: #D9EFF1;
            box-shadow: 0 0 7px rgba(206,242,247,.65);
        }}

        .claw-carriage {{
            position: absolute;
            top: 19px;
            left: 50%;
            width: 70px;
            height: 190px;
            transform: translateX(-50%);
            z-index: 5;
        }}

        .claw-cable {{
            position: absolute;
            top: 0;
            left: 33px;
            width: 3px;
            height: 58px;
            background: linear-gradient(#ECFAFA, #7A9AA5);
        }}

        .claw-arm {{
            position: absolute;
            top: 53px;
            left: 17px;
            width: 36px;
            height: 31px;
        }}

        .claw-arm::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 14px;
            width: 7px;
            height: 10px;
            border-radius: 4px;
            background: #E8F8F8;
        }}

        .prong {{
            position: absolute;
            top: 8px;
            width: 12px;
            height: 17px;
            border: 3px solid #E8F8F8;
            border-top: none;
            border-radius: 0 0 10px 10px;
        }}

        .prong.left {{
            left: 0;
            transform: rotate(22deg);
        }}

        .prong.right {{
            right: 0;
            transform: rotate(-22deg);
        }}

        .claw-prize {{
            position: absolute;
            top: 87px;
            left: 50%;
            transform: translateX(-50%);
            width: 68px;
            height: 29px;
            border: 2px solid #FFE9A6;
            border-radius: 16px;
            background: linear-gradient(145deg, #D6A53C, #774711);
            color: #FFF7D8;
            font-family: monospace;
            font-size: 8px;
            font-weight: 950;
            line-height: 25px;
            text-align: center;
            box-shadow: 0 0 12px rgba(255,216,108,.7);
        }}

        .capsule {{
            position: absolute;
            bottom: 15px;
            width: 52px;
            height: 29px;
            border: 2px solid rgba(255,245,210,.52);
            border-radius: 16px;
            color: #FFF3CC;
            font-family: monospace;
            font-size: 7px;
            font-weight: 900;
            line-height: 25px;
            text-align: center;
            overflow: hidden;
        }}

        .capsule.one {{
            left: 4%;
            transform: rotate(-5deg);
            background: #9B2834;
        }}

        .capsule.two {{
            left: 27%;
            bottom: 35px;
            transform: rotate(4deg);
            background: #60479B;
        }}

        .capsule.three {{
            left: 51%;
            transform: rotate(-3deg);
            background: #9A6C1E;
        }}

        .capsule.four {{
            left: 75%;
            bottom: 35px;
            transform: rotate(5deg);
            background: #277E73;
        }}

        .claw-caption {{
            margin-top: 7px;
            color: #D6E2E5;
            text-align: center;
            font-size: .69rem;
            line-height: 1.35;
        }}

        .claw-run-a .claw-carriage {{
            animation: clawA 1.35s ease-in-out;
        }}

        .claw-run-b .claw-carriage {{
            animation: clawB 1.35s ease-in-out;
        }}

        .claw-run-a .claw-prize,
        .claw-run-b .claw-prize {{
            animation: revealPrize 1.35s ease-in-out;
        }}

        @keyframes clawA {{
            0% {{ transform: translateX(-50%) translateY(0); }}
            45% {{ transform: translateX(-50%) translateY(65px); }}
            65% {{ transform: translateX(-50%) translateY(65px) scale(.96); }}
            100% {{ transform: translateX(-50%) translateY(0); }}
        }}

        @keyframes clawB {{
            0% {{ transform: translateX(-50%) translateY(0); }}
            45% {{ transform: translateX(-50%) translateY(65px); }}
            65% {{ transform: translateX(-50%) translateY(65px) scale(.96); }}
            100% {{ transform: translateX(-50%) translateY(0); }}
        }}

        @keyframes revealPrize {{
            0%, 42% {{
                opacity: 0;
                transform: translate(-50%, 12px) scale(.55);
            }}
            58% {{
                opacity: 1;
                transform: translate(-50%, 0) scale(1.08);
            }}
            100% {{
                opacity: 1;
                transform: translate(-50%, 0) scale(1);
            }}
        }}

        @media(max-width: 850px) {{
            .topbar {{
                align-items: flex-start;
                flex-direction: column;
            }}

            .top-note {{
                text-align: left;
            }}
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(stylesheet(), unsafe_allow_html=True)


# =============================================================================
# DISPLAY HELPERS
# =============================================================================

def money(value: Any, decimals: int = 0) -> str:
    """Format a dollar value safely."""
    if value is None or pd.isna(value):
        return "—"

    numeric_value = float(value)
    rendered = f"${abs(numeric_value):,.{decimals}f}"
    return f"-{rendered}" if numeric_value < 0 else rendered


def pct(value: Any, decimals: int = 1) -> str:
    """Format decimal fractions as percentages safely."""
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.{decimals}%}"


def safe_float(value: Any, default: float = 0.0) -> float:
    """Return a safe finite float."""
    try:
        numeric_value = float(value)
        return numeric_value if np.isfinite(numeric_value) else default
    except (TypeError, ValueError):
        return default


def section_header(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="eyebrow">{html.escape(str(kicker))}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {title}")

    if subtitle:
        st.markdown(
            f'<div class="subtle">{html.escape(str(subtitle))}</div>',
            unsafe_allow_html=True,
        )


def insight_bubble(
    label: str,
    message: str,
    tone: str = "normal",
) -> None:
    tone_class = ""

    if tone in {"warning", "purple", "blue"}:
        tone_class = f" {tone}"

    st.markdown(
        f"""
        <div class="insight{tone_class}">
            <div class="insight-label">{html.escape(str(label))}</div>
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def download_csv(
    dataframe: pd.DataFrame,
    filename: str,
    label: str,
) -> None:
    st.download_button(
        label=label,
        data=dataframe.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_chart(
    figure: go.Figure,
    title: str,
    key: str,
    height: int = 380,
    legend: bool = True,
) -> None:
    figure.update_layout(
        title=dict(
            text=title,
            x=0,
            xanchor="left",
            font=dict(color=WHITE, size=16),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(
            family="Consolas, Liberation Mono, monospace",
            color=WHITE,
            size=12,
        ),
        margin=dict(l=42, r=22, t=58, b=46),
        height=height,
        bargap=.28,
        bargroupgap=.08,
        showlegend=legend,
        legend=dict(
            orientation="h",
            y=1.03,
            x=0,
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor=PANEL,
            bordercolor=GRID,
            font_color=WHITE,
            font_size=12,
        ),
    )

    figure.update_xaxes(
        gridcolor=GRID,
        zerolinecolor="#485661",
        tickfont=dict(size=10),
        automargin=True,
    )

    figure.update_yaxes(
        gridcolor=GRID,
        zerolinecolor="#485661",
        tickfont=dict(size=10),
        automargin=True,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        key=key,
        config={
            "displayModeBar": False,
            "displaylogo": False,
            "responsive": True,
        },
    )


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(show_spinner="Loading local AceIQ data...")
def load_data() -> dict[str, Any]:
    """
    Load required data and any available optional local evidence.

    Optional data is never fabricated. The dashboard only activates a related
    analysis when its source file is present.
    """

    required_paths = {
        "report": DATA_DIR / "analysis_results.json",
        "machines": DATA_DIR / "machines.parquet",
        "daily": DATA_DIR / "machine_daily.parquet",
        "guests": DATA_DIR / "guest_groups.parquet",
        "property_daily": DATA_DIR / "property_daily.parquet",
        "scenario_net": DATA_DIR / "scenario_net.npz",
    }

    missing_paths = [
        str(path)
        for path in required_paths.values()
        if not path.exists()
    ]

    if missing_paths:
        raise FileNotFoundError(
            "Missing required local data files:\n\n"
            + "\n".join(missing_paths)
            + f"\n\nExpected location:\n{DATA_DIR}"
        )

    loaded: dict[str, Any] = {}

    loaded["report"] = json.loads(
        required_paths["report"].read_text(encoding="utf-8")
    )
    loaded["machines"] = pd.read_parquet(required_paths["machines"])
    loaded["daily"] = pd.read_parquet(required_paths["daily"])
    loaded["guests"] = pd.read_parquet(required_paths["guests"])
    loaded["property_daily"] = pd.read_parquet(
        required_paths["property_daily"]
    )
    loaded["scenario_samples"] = np.load(
        required_paths["scenario_net"]
    )["net"]

    optional_parquet_paths = {
        "daily_variance": DATA_DIR / "daily_variance.parquet",
        "demand_predictions": DATA_DIR / "demand_predictions.parquet",
        "floor_locations": DATA_DIR / "floor_locations.parquet",
        "floor_walkways": DATA_DIR / "floor_walkways.parquet",
        "placements": DATA_DIR / "placements.parquet",
    }

    for key, path in optional_parquet_paths.items():
        loaded[key] = (
            pd.read_parquet(path)
            if path.exists()
            else pd.DataFrame()
        )

    forecast_metadata_path = DATA_DIR / "forecast_metadata.json"
    loaded["forecast_metadata"] = (
        json.loads(
            forecast_metadata_path.read_text(encoding="utf-8")
        )
        if forecast_metadata_path.exists()
        else {}
    )

    daily = loaded["daily"].copy()
    property_daily = loaded["property_daily"].copy()
    machines = loaded["machines"].copy()
    guests = loaded["guests"].copy()

    daily["gaming_date"] = pd.to_datetime(
        daily["gaming_date"],
        errors="coerce",
    )
    property_daily["gaming_date"] = pd.to_datetime(
        property_daily["gaming_date"],
        errors="coerce",
    )

    machines["machine_id"] = machines["machine_id"].astype(str)
    daily["machine_id"] = daily["machine_id"].astype(str)

    if "period_month" in guests.columns:
        guests["period_month"] = guests["period_month"].astype(str)

    daily_variance = loaded["daily_variance"].copy()

    if not daily_variance.empty:
        daily_variance["machine_id"] = (
            daily_variance["machine_id"].astype(str)
        )
        daily_variance["gaming_date"] = pd.to_datetime(
            daily_variance["gaming_date"],
            errors="coerce",
        )

    placements = loaded["placements"].copy()

    if not placements.empty:
        placements["machine_id"] = placements["machine_id"].astype(str)
        placements["effective_from_utc"] = pd.to_datetime(
            placements["effective_from_utc"],
            errors="coerce",
            utc=True,
        )
        placements["effective_to_utc"] = pd.to_datetime(
            placements["effective_to_utc"],
            errors="coerce",
            utc=True,
        )

    loaded["daily"] = daily
    loaded["property_daily"] = property_daily
    loaded["machines"] = machines
    loaded["guests"] = guests
    loaded["daily_variance"] = daily_variance
    loaded["placements"] = placements

    return loaded


# =============================================================================
# ANALYTICS
# =============================================================================

def active_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Keep all machine-days where the machine was scheduled/on the floor.

    Do not exclude zero-availability days: a fully down machine-day is
    operational evidence and must remain in availability and downtime metrics.
    """

    result = dataframe.copy()

    if "scheduled_hours" in result.columns:
        result = result[
            result["scheduled_hours"].fillna(0) > 0
        ].copy()

    return result

def build_machine_summary(
    filtered_daily: pd.DataFrame,
    machines: pd.DataFrame,
    daily_variance: pd.DataFrame,
    use_full_period_screen: bool,
) -> pd.DataFrame:
    """
    Build selected-period machine evidence.

    Full-period standardized gap fields are shown only for the complete
    Jan-Jun screen because those values are precomputed for the full dataset.
    Selected-period uncertainty is calculated from daily_variance instead.
    """

    daily_active = active_rows(filtered_daily)

    summary = (
        daily_active.groupby("machine_id", as_index=False)
        .agg(
            actual_house_win=("house_win_usd", "sum"),
            expected_house_win=("theo_usd", "sum"),
            total_wagers=("coin_in_usd", "sum"),
            available_hours=("available_hours", "sum"),
            scheduled_hours=("scheduled_hours", "sum"),
            downtime_hours=("down_hours", "sum"),
            estimated_downtime_opportunity=("missed_theo_mid", "sum"),
            estimated_missed_wagers=("missed_wagers_mid", "sum"),
            active_days=("gaming_date", "nunique"),
        )
    )

    summary["availability_rate"] = (
        summary["available_hours"]
        / summary["scheduled_hours"].replace(0, np.nan)
    )
    summary["actual_per_active_day"] = (
        summary["actual_house_win"]
        / summary["active_days"].replace(0, np.nan)
    )
    summary["expected_per_active_day"] = (
        summary["expected_house_win"]
        / summary["active_days"].replace(0, np.nan)
    )
    summary["actual_per_available_hour"] = (
        summary["actual_house_win"]
        / summary["available_hours"].replace(0, np.nan)
    )
    summary["expected_per_available_hour"] = (
        summary["expected_house_win"]
        / summary["available_hours"].replace(0, np.nan)
    )
    summary["actual_minus_expected"] = (
        summary["actual_house_win"]
        - summary["expected_house_win"]
    )
    summary["actual_to_expected"] = (
        summary["actual_house_win"]
        / summary["expected_house_win"].replace(0, np.nan)
    )

    if not daily_variance.empty:
        variance_filtered = daily_variance[
            daily_variance["gaming_date"].isin(
                daily_active["gaming_date"].unique()
            )
        ].copy()

        variance_summary = (
            variance_filtered.groupby("machine_id", as_index=False)
            .agg(variance_usd2=("variance_usd2", "sum"))
        )

        summary = summary.merge(
            variance_summary,
            on="machine_id",
            how="left",
        )
    else:
        summary["variance_usd2"] = np.nan

    summary["payout_sd_selected"] = np.sqrt(
        summary["variance_usd2"].clip(lower=0)
    )
    summary["standardized_gap_selected"] = (
        summary["actual_minus_expected"]
        / summary["payout_sd_selected"].replace(0, np.nan)
    )

    metadata_columns = [
        "machine_id",
        "manufacturer",
        "theme",
        "install_date",
        "retire_date",
        "lease_class",
        "eligible_july",
        "availability",
        "theo_per_hour",
        "actual_per_day",
        "payout_gap",
        "payout_sd",
        "standardized_gap",
        "theme_peer_theo_per_hour",
        "peer_ratio",
    ]

    metadata_columns = [
        column
        for column in metadata_columns
        if column in machines.columns
    ]

    summary = summary.merge(
        machines[metadata_columns],
        on="machine_id",
        how="left",
        suffixes=("", "_metadata"),
    )

    if "eligible_july" not in summary.columns:
        summary["eligible_july"] = False

    summary["eligible_july"] = (
        summary["eligible_july"]
        .fillna(False)
        .astype(bool)
    )

    if "standardized_gap" not in summary.columns:
        summary["standardized_gap"] = np.nan

    if not use_full_period_screen:
        summary["standardized_gap"] = np.nan

    return summary


def add_location_context(
    machine_summary: pd.DataFrame,
    filtered_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Attach the dominant selected-period placement for compact summaries.

    Detailed placement changes are handled separately in the investigation view.
    This summary field is descriptive only and never treated as proof of a
    location effect.
    """

    daily_active = active_rows(filtered_daily)

    locations = (
        daily_active.groupby(
            ["machine_id", "zone_name", "bank_id"],
            as_index=False,
        )
        .agg(
            available_hours=("available_hours", "sum"),
            days=("gaming_date", "nunique"),
        )
        .sort_values(
            ["machine_id", "available_hours"],
            ascending=[True, False],
        )
        .drop_duplicates("machine_id")
    )

    return machine_summary.merge(
        locations[
            [
                "machine_id",
                "zone_name",
                "bank_id",
                "days",
            ]
        ].rename(columns={"days": "dominant_location_days"}),
        on="machine_id",
        how="left",
    )


def build_zone_summary(filtered_daily: pd.DataFrame) -> pd.DataFrame:
    daily_active = active_rows(filtered_daily)

    zones = (
        daily_active.groupby("zone_name", as_index=False)
        .agg(
            wagers=("coin_in_usd", "sum"),
            actual=("house_win_usd", "sum"),
            expected=("theo_usd", "sum"),
            available_hours=("available_hours", "sum"),
            scheduled_hours=("scheduled_hours", "sum"),
            downtime_hours=("down_hours", "sum"),
            downtime_opportunity=("missed_theo_mid", "sum"),
            missed_wagers=("missed_wagers_mid", "sum"),
            machine_count=("machine_id", "nunique"),
        )
    )

    zones["wagers_per_available_hour"] = (
        zones["wagers"]
        / zones["available_hours"].replace(0, np.nan)
    )
    zones["availability_rate"] = (
        zones["available_hours"]
        / zones["scheduled_hours"].replace(0, np.nan)
    )
    zones["actual_minus_expected"] = (
        zones["actual"]
        - zones["expected"]
    )

    return zones


def build_bank_summary(filtered_daily: pd.DataFrame) -> pd.DataFrame:
    daily_active = active_rows(filtered_daily)

    banks = (
        daily_active.groupby(
            ["zone_name", "bank_id"],
            as_index=False,
        )
        .agg(
            wagers=("coin_in_usd", "sum"),
            actual=("house_win_usd", "sum"),
            expected=("theo_usd", "sum"),
            available_hours=("available_hours", "sum"),
            scheduled_hours=("scheduled_hours", "sum"),
            downtime_hours=("down_hours", "sum"),
            downtime_opportunity=("missed_theo_mid", "sum"),
            missed_wagers=("missed_wagers_mid", "sum"),
            machine_count=("machine_id", "nunique"),
        )
    )

    banks["wagers_per_available_hour"] = (
        banks["wagers"]
        / banks["available_hours"].replace(0, np.nan)
    )
    banks["availability_rate"] = (
        banks["available_hours"]
        / banks["scheduled_hours"].replace(0, np.nan)
    )
    banks["actual_minus_expected"] = (
        banks["actual"]
        - banks["expected"]
    )

    return banks
def build_location_lookup(
    floor_locations: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build a bank-level floor coordinate lookup.

    machine_daily reports bank_id, so prefer bank-node coordinates from
    floor_locations. This is descriptive floor context only.
    """

    output_columns = [
        "bank_id",
        "zone_id",
        "x_m",
        "y_m",
        "capacity",
    ]

    if floor_locations.empty:
        return pd.DataFrame(columns=output_columns)

    locations = floor_locations.copy()

    required_columns = [
        "bank_id",
        "zone_id",
        "x_m",
        "y_m",
        "capacity",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in locations.columns
    ]

    if missing_columns:
        return pd.DataFrame(columns=output_columns)

    valid_locations = locations[
        locations["bank_id"].notna()
        & locations["x_m"].notna()
        & locations["y_m"].notna()
    ].copy()

    if valid_locations.empty:
        return pd.DataFrame(columns=output_columns)

    if "node_type" in valid_locations.columns:
        bank_nodes = valid_locations[
            valid_locations["node_type"]
            .astype(str)
            .str.lower()
            .eq("bank")
        ].copy()

        if bank_nodes.empty:
            bank_nodes = valid_locations.copy()
    else:
        bank_nodes = valid_locations.copy()

    bank_nodes = (
        bank_nodes.sort_values("bank_id")
        .drop_duplicates("bank_id")
    )

    return bank_nodes.loc[
        :,
        [
            "bank_id",
            "zone_id",
            "x_m",
            "y_m",
            "capacity",
        ],
    ].copy()

def movement_history(
    machine_id: str,
    filtered_daily: pd.DataFrame,
) -> pd.DataFrame:
    """
    Use observed machine_daily zone/bank history for date-aligned movement
    evidence. This is safer than assigning UTC placement timestamps directly to
    gaming days without a dedicated gaming-day conversion table.
    """

    machine_days = filtered_daily[
        filtered_daily["machine_id"].astype(str) == str(machine_id)
    ].copy()

    if machine_days.empty:
        return pd.DataFrame()

    location_daily = (
        machine_days.groupby(
            [
                "gaming_date",
                "zone_name",
                "bank_id",
            ],
            as_index=False,
        )
        .agg(
            wagers=("coin_in_usd", "sum"),
            actual=("house_win_usd", "sum"),
            expected=("theo_usd", "sum"),
            available_hours=("available_hours", "sum"),
        )
        .sort_values("gaming_date")
    )

    location_daily["location_key"] = (
        location_daily["zone_name"].astype(str)
        + " | "
        + location_daily["bank_id"].astype(str)
    )

    location_daily["movement_segment"] = (
        location_daily["location_key"]
        .ne(location_daily["location_key"].shift())
        .cumsum()
    )

    segments = (
        location_daily.groupby(
            [
                "movement_segment",
                "zone_name",
                "bank_id",
            ],
            as_index=False,
        )
        .agg(
            start_date=("gaming_date", "min"),
            end_date=("gaming_date", "max"),
            days=("gaming_date", "nunique"),
            wagers=("wagers", "sum"),
            actual=("actual", "sum"),
            expected=("expected", "sum"),
            available_hours=("available_hours", "sum"),
        )
    )

    segments["wagers_per_available_hour"] = (
        segments["wagers"]
        / segments["available_hours"].replace(0, np.nan)
    )
    segments["expected_per_available_hour"] = (
        segments["expected"]
        / segments["available_hours"].replace(0, np.nan)
    )
    segments["actual_per_available_hour"] = (
        segments["actual"]
        / segments["available_hours"].replace(0, np.nan)
    )
    segments["actual_minus_expected"] = (
        segments["actual"]
        - segments["expected"]
    )

    return segments.sort_values("start_date")


def descriptive_move_comparison(
    machine_id: str,
    filtered_daily: pd.DataFrame,
    machine_summary: pd.DataFrame,
) -> dict[str, Any]:
    """
    Produce a descriptive before/after location comparison.

    This does NOT claim causality. The peer benchmark compares machines that did
    not move in the selected period, using the same two date ranges where
    possible. It is presented as a diagnostic, not a causal estimate.
    """

    segments = movement_history(machine_id, filtered_daily)

    if len(segments) < 2:
        return {
            "available": False,
            "reason": (
                "No selected-period bank change was observed for this machine."
            ),
        }

    before = segments.iloc[0]
    after = segments.iloc[-1]

    if (
        pd.isna(before["start_date"])
        or pd.isna(before["end_date"])
        or pd.isna(after["start_date"])
        or pd.isna(after["end_date"])
    ):
        return {
            "available": False,
            "reason": "Placement dates could not be resolved.",
        }

    daily_active = active_rows(filtered_daily).copy()
    location_counts = (
        daily_active.groupby("machine_id")["bank_id"]
        .nunique()
        .rename("bank_count")
    )

    stable_machine_ids = location_counts[
        location_counts == 1
    ].index.astype(str)

    target_row = machine_summary[
        machine_summary["machine_id"].astype(str) == str(machine_id)
    ]

    target_theme = (
        str(target_row.iloc[0]["theme"])
        if not target_row.empty and "theme" in target_row.columns
        else None
    )

    peer_pool = daily_active[
        daily_active["machine_id"].astype(str).isin(stable_machine_ids)
        & (
            daily_active["machine_id"].astype(str)
            != str(machine_id)
        )
    ].copy()

    if target_theme and "theme" in machine_summary.columns:
        theme_ids = machine_summary[
            machine_summary["theme"].astype(str) == target_theme
        ]["machine_id"].astype(str)

        themed_pool = peer_pool[
            peer_pool["machine_id"].astype(str).isin(theme_ids)
        ].copy()

        if themed_pool["machine_id"].nunique() >= 3:
            peer_pool = themed_pool

    def rate_between(
        frame: pd.DataFrame,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> float:
        slice_frame = frame[
            (frame["gaming_date"] >= start)
            & (frame["gaming_date"] <= end)
        ]

        available = slice_frame["available_hours"].sum()
        expected = slice_frame["theo_usd"].sum()

        return (
            expected / available
            if available > 0
            else np.nan
        )

    machine_before_rate = safe_float(
        before["expected_per_available_hour"],
        np.nan,
    )
    machine_after_rate = safe_float(
        after["expected_per_available_hour"],
        np.nan,
    )

    peer_before_rate = rate_between(
        peer_pool,
        before["start_date"],
        before["end_date"],
    )
    peer_after_rate = rate_between(
        peer_pool,
        after["start_date"],
        after["end_date"],
    )

    machine_change = machine_after_rate - machine_before_rate
    peer_change = peer_after_rate - peer_before_rate
    descriptive_difference = machine_change - peer_change

    return {
        "available": True,
        "before": before.to_dict(),
        "after": after.to_dict(),
        "peer_count": int(peer_pool["machine_id"].nunique()),
        "machine_before_rate": machine_before_rate,
        "machine_after_rate": machine_after_rate,
        "peer_before_rate": peer_before_rate,
        "peer_after_rate": peer_after_rate,
        "machine_change": machine_change,
        "peer_change": peer_change,
        "descriptive_difference": descriptive_difference,
    }


def machine_category(row: pd.Series) -> str:
    """
    Classify machine evidence conservatively.

    - Inspection requires the precomputed full-period standardized screen.
    - Maintenance requires material availability evidence.
    - A negative residual without either signal remains monitoring evidence.
    """

    if not bool(row.get("eligible_july", False)):
        return "Not a July action target"

    standardized_gap = row.get("standardized_gap", np.nan)
    availability = row.get("availability_rate", np.nan)
    actual_gap = row.get("actual_minus_expected", np.nan)
    downtime_opportunity = safe_float(
        row.get("estimated_downtime_opportunity", 0)
    )
    expected = safe_float(row.get("expected_house_win", 0))

    if pd.notna(standardized_gap) and standardized_gap <= -3:
        return "Inspection candidate"

    if pd.notna(availability) and availability < .90:
        return "Maintenance candidate"

    if expected > 0 and downtime_opportunity > expected * .10:
        return "Maintenance candidate"

    if pd.notna(actual_gap) and actual_gap < 0:
        return "Monitor payout variance"

    return "Monitor"


def recommendation_for_machine(
    row: pd.Series,
) -> tuple[str, str, str]:
    category = machine_category(row)

    if category == "Not a July action target":
        return (
            "No July action",
            "This machine is not eligible for a July machine-level action.",
            GRAY,
        )

    if category == "Inspection candidate":
        return (
            "Inspect configuration and meters first",
            (
                "The full-period payout-gap screen is unusually negative while "
                "availability is high. Verify configuration, game math, and "
                "meter history before relocation or replacement."
            ),
            PURPLE,
        )

    if category == "Maintenance candidate":
        return (
            "Address availability before replacement",
            (
                "Low availability or material historical downtime opportunity "
                "means the machine may not have received a fair chance to earn."
            ),
            ORANGE,
        )

    if category == "Monitor payout variance":
        return (
            "Monitor against exposure-adjusted peers",
            (
                "The machine is below expected, but selected evidence does not "
                "establish a machine defect or a proven location effect."
            ),
            GOLD,
        )

    return (
        "Monitor before spending",
        (
            "The current evidence does not establish that an irreversible "
            "intervention would outperform preserving the budget."
        ),
        GREEN,
    )


def official_simulation_result(
    report: dict[str, Any],
) -> dict[str, Any]:
    simulation = report.get("simulation", {})
    recommended = simulation.get("recommended", {})

    cost = recommended.get("cost", np.nan)
    keep_budget = pd.notna(cost) and safe_float(cost, -1) == 0

    return {
        "simulation": simulation,
        "recommended": recommended,
        "cost": cost,
        "mean_net": recommended.get("mean_net", np.nan),
        "keep_budget": keep_budget,
    }


# =============================================================================
# DATA QUALITY
# =============================================================================

def build_data_quality_checks(
    daily: pd.DataFrame,
    property_daily: pd.DataFrame,
    machines: pd.DataFrame,
    daily_variance: pd.DataFrame,
    placements: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produce visible checks rather than silently trusting source tables.

    Flags are diagnostic. Outlier values are not automatically removed because
    extreme outcomes can be legitimate slot-machine variance.
    """

    checks: list[dict[str, Any]] = []

    duplicate_machine_days = int(
        daily.duplicated(
            subset=["machine_id", "gaming_date"],
            keep=False,
        ).sum()
    )

    checks.append(
        {
            "check": "Duplicate machine-day records",
            "status": (
                "PASS"
                if duplicate_machine_days == 0
                else "REVIEW"
            ),
            "detail": (
                "No duplicate machine_id + gaming_date records found."
                if duplicate_machine_days == 0
                else (
                    f"{duplicate_machine_days:,} duplicate rows found; "
                    "machine-day sums may be overstated."
                )
            ),
        }
    )

    invalid_availability = int(
        (
            (daily["available_hours"] < 0)
            | (daily["scheduled_hours"] < 0)
            | (
                daily["available_hours"]
                > daily["scheduled_hours"] + .001
            )
            | (daily["down_hours"] < 0)
        ).sum()
    )

    checks.append(
        {
            "check": "Availability and downtime bounds",
            "status": (
                "PASS"
                if invalid_availability == 0
                else "REVIEW"
            ),
            "detail": (
                "Available, scheduled, and downtime hours are within expected bounds."
                if invalid_availability == 0
                else (
                    f"{invalid_availability:,} records have hours outside expected bounds."
                )
            ),
        }
    )

    invalid_wagers = int(
        (daily["coin_in_usd"] < 0).sum()
    )

    checks.append(
        {
            "check": "Negative coin-in values",
            "status": (
                "PASS"
                if invalid_wagers == 0
                else "REVIEW"
            ),
            "detail": (
                "No negative machine-day coin-in values found."
                if invalid_wagers == 0
                else (
                    f"{invalid_wagers:,} machine-day rows have negative coin-in."
                )
            ),
        }
    )

    property_reconciliation = np.abs(
        property_daily["house_win_usd"]
        - (
            property_daily["coin_in_usd"]
            - property_daily["payout_usd"]
        )
    )

    unreconciled_property_days = int(
        (property_reconciliation > .02).sum()
    )

    checks.append(
        {
            "check": "Property house-win reconciliation",
            "status": (
                "PASS"
                if unreconciled_property_days == 0
                else "REVIEW"
            ),
            "detail": (
                "Property house win equals coin-in minus payouts within rounding."
                if unreconciled_property_days == 0
                else (
                    f"{unreconciled_property_days:,} property days do not reconcile."
                )
            ),
        }
    )
    machine_totals = (
        daily.groupby(
            "gaming_date",
            as_index=False,
        )
        .agg(
            machine_coin_in=(
                "coin_in_usd",
                "sum",
            ),
            machine_house_win=(
                "house_win_usd",
                "sum",
            ),
            machine_theo=(
                "theo_usd",
                "sum",
            ),
        )
    )

    property_totals = property_daily[
        [
            "gaming_date",
            "coin_in_usd",
            "house_win_usd",
            "theo_usd",
        ]
    ].rename(
        columns={
            "coin_in_usd": "property_coin_in",
            "house_win_usd": "property_house_win",
            "theo_usd": "property_theo",
        }
    )

    reconciliation = property_totals.merge(
        machine_totals,
        on="gaming_date",
        how="left",
    )

    reconciliation["coin_in_difference"] = (
        reconciliation["property_coin_in"]
        - reconciliation["machine_coin_in"]
    )

    reconciliation["house_win_difference"] = (
        reconciliation["property_house_win"]
        - reconciliation["machine_house_win"]
    )

    reconciliation["theo_difference"] = (
        reconciliation["property_theo"]
        - reconciliation["machine_theo"]
    )

    unreconciled_machine_property_days = int(
        (
            reconciliation[
                [
                    "coin_in_difference",
                    "house_win_difference",
                    "theo_difference",
                ]
            ]
            .abs()
            .max(axis=1)
            > 0.05
        ).sum()
    )

    checks.append(
        {
            "check": "Machine-to-property daily reconciliation",
            "status": (
                "PASS"
                if unreconciled_machine_property_days == 0
                else "REVIEW"
            ),
            "detail": (
                "Machine-day totals reconcile to property-day coin-in, house "
                "win, and theo within rounding."
                if unreconciled_machine_property_days == 0
                else (
                    f"{unreconciled_machine_property_days:,} property days do "
                    "not reconcile between machine and property totals."
                )
            ),
        }
    )

    missing_machine_metadata = int(
        (~daily["machine_id"].isin(machines["machine_id"])).sum()
    )

    checks.append(
        {
            "check": "Machine metadata coverage",
            "status": (
                "PASS"
                if missing_machine_metadata == 0
                else "REVIEW"
            ),
            "detail": (
                "Every machine-day record maps to machines.parquet."
                if missing_machine_metadata == 0
                else (
                    f"{missing_machine_metadata:,} machine-day rows have no metadata match."
                )
            ),
        }
    )

    if not daily_variance.empty:
        daily_variance_join = daily.merge(
            daily_variance[
                [
                    "machine_id",
                    "gaming_date",
                    "variance_usd2",
                ]
            ],
            on=["machine_id", "gaming_date"],
            how="left",
        )

        missing_variance = int(
            daily_variance_join["variance_usd2"].isna().sum()
        )

        checks.append(
            {
                "check": "Variance evidence coverage",
                "status": (
                    "PASS"
                    if missing_variance == 0
                    else "REVIEW"
                ),
                "detail": (
                    "Every machine-day row has a daily variance estimate."
                    if missing_variance == 0
                    else (
                        f"{missing_variance:,} machine-day rows are missing variance estimates."
                    )
                ),
            }
        )

    if not placements.empty:
        placement_dupes = int(
            placements.duplicated(
                subset=[
                    "machine_id",
                    "location_id",
                    "effective_from_utc",
                ],
                keep=False,
            ).sum()
        )

        checks.append(
            {
                "check": "Duplicate placement starts",
                "status": (
                    "PASS"
                    if placement_dupes == 0
                    else "REVIEW"
                ),
                "detail": (
                    "No duplicate machine/location placement starts found."
                    if placement_dupes == 0
                    else (
                        f"{placement_dupes:,} duplicate placement-start rows found."
                    )
                ),
            }
        )

    low_exposure_count = int(
        (
            daily.groupby("machine_id")["available_hours"]
            .sum()
            .lt(168)
            .sum()
        )
    )

    checks.append(
        {
            "check": "Low-exposure machine flag",
            "status": "INFO",
            "detail": (
                f"{low_exposure_count:,} machines have fewer than 168 available "
                "hours in the source period. Low-exposure machines require "
                "extra caution in rankings."
            ),
        }
    )

    return pd.DataFrame(checks)


# =============================================================================
# ACTION CATALOG / JULY ACTION TRAY
# =============================================================================

def catalog_dataframe(
    report: dict[str, Any],
) -> pd.DataFrame:
    catalog = pd.DataFrame(report.get("action_catalog", []))

    if catalog.empty:
        return catalog

    numeric_columns = [
        "unit_cost_cents",
        "recurring_cost_cents_per_day",
        "lead_days",
        "downtime_minutes",
        "quantity_limit",
    ]

    for column in numeric_columns:
        if column in catalog.columns:
            catalog[column] = pd.to_numeric(
                catalog[column],
                errors="coerce",
            )

    return catalog


def action_cost_from_catalog(
    action_row: pd.Series,
    quantity: int = 1,
) -> float:
    """
    Apply the official action-catalog pricing rule.

    quantity × (
      unit cost
      + recurring per-day cost × max(0, 30 − lead days)
    )
    """

    unit_cost = safe_float(
        action_row.get("unit_cost_cents", 0)
    ) / 100

    recurring_per_day = safe_float(
        action_row.get("recurring_cost_cents_per_day", 0)
    ) / 100

    lead_days = safe_float(action_row.get("lead_days", 0))

    usable_days = max(
        0,
        JULY_HORIZON_DAYS - lead_days,
    )

    return quantity * (
        unit_cost
        + recurring_per_day * usable_days
    )


def downtime_cost_for_targets(
    action_row: pd.Series,
    target_machine_ids: list[str],
    machine_summary: pd.DataFrame,
) -> float:
    """
    Value planned catalog downtime at selected-period expected earnings/hour.

    This is an opportunity-cost estimate, not a guaranteed realized loss.
    """

    downtime_hours = safe_float(
        action_row.get("downtime_minutes", 0)
    ) / 60

    if downtime_hours <= 0 or not target_machine_ids:
        return 0.0

    targets = machine_summary[
        machine_summary["machine_id"]
        .astype(str)
        .isin([str(machine_id) for machine_id in target_machine_ids])
    ].copy()

    if targets.empty:
        return 0.0

    expected_per_hour = targets[
        "expected_per_available_hour"
    ].replace([np.inf, -np.inf], np.nan).fillna(0)

    return float(expected_per_hour.sum() * downtime_hours)


def action_measurement_plan(
    action_type_id: str,
) -> tuple[str, str]:
    """
    Return explicit uncertainty and measurement language by action type.
    """

    plans = {
        "A-MOVE-MACHINE": (
            (
                "Observed zone differences are descriptive. A destination "
                "advantage may reflect traffic, mix, visibility, or guest "
                "composition rather than a causal location effect."
            ),
            (
                "Pre-register a matched unchanged machine or bank. Compare "
                "expected earnings per available hour before and after the "
                "move, while monitoring nearby-machine displacement."
            ),
        ),
        "A-MOVE-BANK": (
            (
                "Whole-bank movement changes several conditions at once, so "
                "observed improvement cannot isolate location alone."
            ),
            (
                "Use an untreated comparable bank as a control and compare "
                "wagers, expected earnings per available hour, downtime, and "
                "nearby displacement."
            ),
        ),
        "A-REPLACE-LEASE": (
            (
                "New-title uplift is a scenario assumption, not observed "
                "causal replacement evidence."
            ),
            (
                "Compare the leased title with matched unchanged machines, "
                "track expected earnings per available hour, and measure "
                "displacement from adjacent machines."
            ),
        ),
        "A-REPLACE-BUY": (
            (
                "A purchase has irreversible capital cost and uncertain "
                "incremental demand. The catalog price is known; benefit is not."
            ),
            (
                "Use a staged evaluation where possible: compare performance "
                "with matched unchanged titles and track payback beyond July."
            ),
        ),
        "A-TECH-SHIFT": (
            (
                "Historical downtime opportunity is not guaranteed net new "
                "floor revenue because some guests may have played elsewhere."
            ),
            (
                "Track response time, unavailable hours, repeat faults, repair "
                "turnaround, and expected earnings per scheduled hour against "
                "an untreated shift or comparable machine set."
            ),
        ),
        "A-PREVENTIVE": (
            (
                "Manufacturer-level maintenance may prevent some faults, but "
                "the recovery fraction is uncertain and planned downtime occurs."
            ),
            (
                "Compare repeat faults, downtime, repair turnaround, and "
                "expected earnings per scheduled hour with untreated "
                "manufacturers or comparable machines."
            ),
        ),
        "A-INSPECT": (
            (
                "Inspection has information value, but the 30-day cash model "
                "does not credit an unverified corrective benefit."
            ),
            (
                "Reconcile configured RTP, game math, meter history, firmware, "
                "and repair records. Document findings before selecting any "
                "corrective action."
            ),
        ),
        "A-WAYFINDING": (
            (
                "Traffic and zone-demand differences are observational; signs "
                "may shift existing play rather than create new demand."
            ),
            (
                "Compare zone entries, bank-level wagers per available hour, "
                "and nearby-zone displacement against a comparable unchanged zone."
            ),
        ),
        "A-COMP-PILOT": (
            (
                "The pilot is a learning action. It should not target guests "
                "based on gambling losses or encourage harmful gambling."
            ),
            (
                "Use a randomized or clearly defined control group. Measure "
                "hospitality/redemption outcomes, comp cost, and player "
                "experience without using loss behavior as a targeting signal."
            ),
        ),
        "A-COMP-CHANGE": (
            (
                "A floor-wide rate change has no concurrent property-level "
                "control group, so effects are difficult to identify."
            ),
            (
                "Track comp cost, redemption volume, points per face-value "
                "dollar, guest satisfaction, and player-service outcomes. "
                "Do not infer causality from a single before/after comparison."
            ),
        ),
        "A-PROMO": (
            (
                "Promotion response is uncertain and may pull demand forward "
                "or displace normal play."
            ),
            (
                "Compare with matched weekdays or a pre-registered baseline; "
                "measure incremental contribution after promotion cost and "
                "avoid incentives tied to harmful gambling behavior."
            ),
        ),
        "A-SURVEY": (
            (
                "A larger survey improves information, not necessarily July "
                "cash contribution."
            ),
            (
                "Track response rate, sample composition, confidence intervals, "
                "and whether findings change a later operational decision."
            ),
        ),
    }

    return plans.get(
        action_type_id,
        (
            "Effect is uncertain and should not be interpreted as causal proof.",
            "Define a comparison group, success metric, and measurement period before implementation.",
        ),
    )


def action_assumption_text(
    action_type_id: str,
    retained_play: float,
    maintenance_recovery: float,
    lease_uplift: float,
    move_uplift: float,
    comp_savings: float,
) -> str:
    """
    Make sandbox assumptions explicit rather than mixing them with observed data.
    """

    assumptions = {
        "A-MOVE-MACHINE": (
            f"Planning sensitivity: destination expected-demand uplift "
            f"{move_uplift:.0%}; retained incremental play "
            f"{retained_play:.0%}."
        ),
        "A-MOVE-BANK": (
            f"Planning sensitivity: bank-level destination uplift "
            f"{move_uplift:.0%}; retained incremental play "
            f"{retained_play:.0%}."
        ),
        "A-REPLACE-LEASE": (
            f"Planning sensitivity: new-title uplift {lease_uplift:.0%}; "
            f"retained incremental play {retained_play:.0%}."
        ),
        "A-REPLACE-BUY": (
            f"Planning sensitivity: new-title uplift {lease_uplift:.0%}; "
            f"retained incremental play {retained_play:.0%}."
        ),
        "A-TECH-SHIFT": (
            f"Planning sensitivity: recover {maintenance_recovery:.0%} of "
            "historical midpoint downtime opportunity after lead time."
        ),
        "A-PREVENTIVE": (
            f"Planning sensitivity: recover {maintenance_recovery:.0%} of "
            "manufacturer midpoint downtime opportunity after planned downtime."
        ),
        "A-WAYFINDING": (
            f"Planning sensitivity: zone uplift {move_uplift:.0%}; retained "
            f"incremental play {retained_play:.0%}."
        ),
        "A-COMP-CHANGE": (
            f"Planning sensitivity: save {comp_savings:.0%} of selected-period "
            "comp cost. This is not an observed causal estimate."
        ),
        "A-COMP-PILOT": (
            "Information-only scenario: no immediate cash benefit is credited."
        ),
        "A-INSPECT": (
            "Information-only scenario: no unverified corrective cash benefit is credited."
        ),
        "A-PROMO": (
            "No unverified promotional revenue is credited in this conservative sandbox."
        ),
        "A-SURVEY": (
            "Information-only scenario: no immediate cash benefit is credited."
        ),
        "A-HOLD": (
            "No intervention effect is credited. Unspent budget remains available."
        ),
    }

    return assumptions.get(
        action_type_id,
        "No action-specific scenario assumption is available.",
    )


def estimate_action_sandbox(
    action_row: pd.Series,
    target: str,
    target_machine_ids: list[str],
    machine_summary: pd.DataFrame,
    zone_summary: pd.DataFrame,
    filtered_daily: pd.DataFrame,
    filtered_property: pd.DataFrame,
    retained_play: float,
    maintenance_recovery: float,
    lease_uplift: float,
    move_uplift: float,
    comp_savings: float,
) -> dict[str, Any]:
    """
    Estimate a transparent action sandbox.

    Catalog cost, lead time, recurring cost, and downtime are observed inputs.
    Benefit estimates are visibly labeled planning sensitivities—not evidence of
    causal effect.
    """

    action_type_id = str(action_row.get("action_type_id", ""))
    action_cost = action_cost_from_catalog(action_row)
    downtime_cost = downtime_cost_for_targets(
        action_row,
        target_machine_ids,
        machine_summary,
    )

    lead_days = safe_float(action_row.get("lead_days", 0))
    benefit_days = max(0, JULY_HORIZON_DAYS - lead_days)

    baseline_benefit = 0.0
    low_benefit = 0.0
    high_benefit = 0.0

    selected_targets = machine_summary[
        machine_summary["machine_id"]
        .astype(str)
        .isin([str(value) for value in target_machine_ids])
    ].copy()

    target_expected_hour = safe_float(
        selected_targets[
            "expected_per_available_hour"
        ].sum()
        if not selected_targets.empty
        else 0
    )

    if action_type_id in {
        "A-MOVE-MACHINE",
        "A-MOVE-BANK",
        "A-WAYFINDING",
    }:
        baseline = target_expected_hour * 24 * benefit_days
        low_uplift = max(-.10, move_uplift - .20)
        high_uplift = min(1.50, move_uplift + .30)

        low_benefit = (
            baseline
            * low_uplift
            * max(.10, retained_play - .25)
        )
        baseline_benefit = (
            baseline
            * move_uplift
            * retained_play
        )
        high_benefit = (
            baseline
            * high_uplift
            * min(1.0, retained_play + .25)
        )

    elif action_type_id in {
        "A-REPLACE-LEASE",
        "A-REPLACE-BUY",
    }:
        baseline = target_expected_hour * 24 * benefit_days
        low_uplift = -.10
        high_uplift = min(2.0, lease_uplift + .65)

        low_benefit = (
            baseline
            * low_uplift
            * max(.10, retained_play - .25)
        )
        baseline_benefit = (
            baseline
            * lease_uplift
            * retained_play
        )
        high_benefit = (
            baseline
            * high_uplift
            * min(1.0, retained_play + .25)
        )

    elif action_type_id in {
        "A-TECH-SHIFT",
        "A-PREVENTIVE",
    }:
        source_daily = filtered_daily.copy()

        if action_type_id == "A-PREVENTIVE":
            target_manufacturer = str(target)

            target_ids = machine_summary[
        (
            machine_summary["manufacturer"].astype(str)
            == target_manufacturer
        )
        & (
            machine_summary["eligible_july"]
        )
    ]["machine_id"].astype(str)

            source_daily = source_daily[
                source_daily["machine_id"].astype(str).isin(target_ids)
            ]

        historical_opportunity = safe_float(
            source_daily["missed_theo_mid"].sum()
        )

        source_days = max(
            source_daily["gaming_date"].nunique(),
            1,
        )

        july_opportunity = (
            historical_opportunity
            / source_days
            * benefit_days
        )

        low_recovery = max(.05, maintenance_recovery - .20)
        high_recovery = min(.95, maintenance_recovery + .25)

        low_benefit = (
            july_opportunity
            * low_recovery
            * retained_play
        )
        baseline_benefit = (
            july_opportunity
            * maintenance_recovery
            * retained_play
        )
        high_benefit = (
            july_opportunity
            * high_recovery
            * retained_play
        )

    elif action_type_id == "A-COMP-CHANGE":
        historical_comp_cost = safe_float(
            filtered_property["comp_cost_usd"].sum()
        )

        period_days = max(
            filtered_property["gaming_date"].nunique(),
            1,
        )

        july_comp_cost = (
            historical_comp_cost
            / period_days
            * benefit_days
        )

        low_benefit = 0.0
        baseline_benefit = july_comp_cost * comp_savings
        high_benefit = july_comp_cost * min(.25, comp_savings + .15)

    net_low = low_benefit - action_cost - downtime_cost
    net_base = baseline_benefit - action_cost - downtime_cost
    net_high = high_benefit - action_cost - downtime_cost

    spread = net_high - net_low

    if spread > 10_000:
        uncertainty = "High"
    elif spread > 3_000:
        uncertainty = "Medium"
    else:
        uncertainty = "Lower"

    if action_type_id in {
        "A-INSPECT",
        "A-COMP-PILOT",
        "A-SURVEY",
    }:
        signal = "Learning action"
    elif net_base > 0 and net_low >= 0:
        signal = "Favorable under sandbox assumptions"
    elif net_base > 0:
        signal = "Potential upside with meaningful uncertainty"
    else:
        signal = "Weak under sandbox assumptions"

    limitation, measurement = action_measurement_plan(action_type_id)

    return {
        "action_type_id": action_type_id,
        "action_name": str(action_row.get("name", "")),
        "target": target,
        "target_machine_ids": target_machine_ids,
        "action_cost": action_cost,
        "downtime_cost": downtime_cost,
        "total_cost": action_cost + downtime_cost,
        "benefit_days": benefit_days,
        "low": net_low,
        "base": net_base,
        "high": net_high,
        "uncertainty": uncertainty,
        "signal": signal,
        "assumptions": action_assumption_text(
            action_type_id,
            retained_play,
            maintenance_recovery,
            lease_uplift,
            move_uplift,
            comp_savings,
        ),
        "limitation": limitation,
        "measurement": measurement,
    }


# =============================================================================
# SESSION STATE
# =============================================================================

def initialize_state() -> None:
    defaults = {
        "selected_machine_id": None,
        "selected_action_type_id": "A-HOLD",
        "selected_target": None,
        "retained_play": .50,
        "maintenance_recovery": .50,
        "lease_uplift": .50,
        "move_uplift": .20,
        "comp_savings": .10,
        "july_plan": [],
        "plan_message": "",
        "plan_message_type": "info",
        "claw_machine_id": None,
        "claw_count": 0,
        "claw_animation_mode": "claw-run-a",
        "period_signature": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_period_state() -> None:
    st.session_state.july_plan = []
    st.session_state.selected_action_type_id = "A-HOLD"
    st.session_state.selected_target = None
    st.session_state.claw_machine_id = None
    st.session_state.plan_message = (
        "Evidence period changed. The July Action Tray was reset."
    )
    st.session_state.plan_message_type = "info"


def plan_budget_used() -> float:
    return float(
        sum(
            safe_float(item.get("total_cost", 0))
            for item in st.session_state.july_plan
        )
    )


def plan_action_types() -> set[str]:
    return {
        str(item.get("action_type_id", ""))
        for item in st.session_state.july_plan
        if item.get("action_type_id")
    }


def plan_count_for_action(
    action_type_id: str,
) -> int:
    return sum(
        1
        for item in st.session_state.july_plan
        if item.get("action_type_id") == action_type_id
    )


def existing_target_machine_ids() -> set[str]:
    machine_ids: set[str] = set()

    for item in st.session_state.july_plan:
        for machine_id in item.get("target_machine_ids", []):
            machine_ids.add(str(machine_id))

    return machine_ids


def conflicting_machine_action_exists(
    target_machine_ids: list[str],
    action_row: pd.Series,
    catalog: pd.DataFrame,
) -> bool:
    """
    Enforce same-machine conflicts only where the catalog declares them.

    Move / lease / purchase / bank move all belong to the same_machine
    incompatibility group. Inspections remain allowed because they are a
    reversible information action.
    """

    incompatibility_group = action_row.get(
        "incompatibility_group",
        None,
    )

    if incompatibility_group != "same_machine":
        return False

    target_set = {str(machine_id) for machine_id in target_machine_ids}

    for item in st.session_state.july_plan:
        existing_action_id = item.get("action_type_id", "")

        existing_catalog_rows = catalog[
            catalog["action_type_id"] == existing_action_id
        ]

        if existing_catalog_rows.empty:
            continue

        existing_group = existing_catalog_rows.iloc[0].get(
            "incompatibility_group",
            None,
        )

        existing_targets = {
            str(machine_id)
            for machine_id in item.get("target_machine_ids", [])
        }

        if (
            existing_group == "same_machine"
            and target_set.intersection(existing_targets)
        ):
            return True

    return False


def add_to_plan(
    action_row: pd.Series,
    target: str,
    sandbox: dict[str, Any],
    catalog: pd.DataFrame,
) -> None:
    action_type_id = str(action_row.get("action_type_id", ""))

    if action_type_id == "A-HOLD":
        st.session_state.plan_message = (
            "Preserve Budget is already the $0 baseline and does not need to be added."
        )
        st.session_state.plan_message_type = "info"
        return

    if (
        action_type_id not in plan_action_types()
        and len(plan_action_types()) >= MAX_ACTION_TYPES
    ):
        st.session_state.plan_message = (
            "The July plan allows no more than three action types."
        )
        st.session_state.plan_message_type = "error"
        return

    quantity_limit = int(
        safe_float(action_row.get("quantity_limit", 0))
    )

    if (
        quantity_limit > 0
        and plan_count_for_action(action_type_id) >= quantity_limit
    ):
        st.session_state.plan_message = (
            f"{action_row.get('name', action_type_id)} has reached its catalog "
            f"quantity limit of {quantity_limit}."
        )
        st.session_state.plan_message_type = "error"
        return

    incompatibility_group = action_row.get(
        "incompatibility_group",
        None,
    )

    if incompatibility_group == "comp_policy":
        conflicting_comp = any(
            str(item.get("incompatibility_group", ""))
            == "comp_policy"
            for item in st.session_state.july_plan
        )

        if conflicting_comp:
            st.session_state.plan_message = (
                "The catalog does not allow the comp pilot and the floor-wide "
                "comp-rate change in the same July plan."
            )
            st.session_state.plan_message_type = "error"
            return

    if conflicting_machine_action_exists(
        sandbox["target_machine_ids"],
        action_row,
        catalog,
    ):
        st.session_state.plan_message = (
            "This target already has a conflicting move or replacement action."
        )
        st.session_state.plan_message_type = "error"
        return

    if plan_budget_used() + sandbox["total_cost"] > MAX_BUDGET:
        st.session_state.plan_message = (
            "Adding this action would exceed the $100,000 July budget."
        )
        st.session_state.plan_message_type = "error"
        return

    duplicate_target_action = any(
        (
            item.get("action_type_id") == action_type_id
            and str(item.get("target")) == str(target)
        )
        for item in st.session_state.july_plan
    )

    if duplicate_target_action:
        st.session_state.plan_message = (
            "That action and target combination is already in the July tray."
        )
        st.session_state.plan_message_type = "error"
        return

    st.session_state.july_plan.append(
        {
            "action_type_id": action_type_id,
            "action": str(action_row.get("name", action_type_id)),
            "target": str(target),
            "target_machine_ids": sandbox["target_machine_ids"],
            "incompatibility_group": incompatibility_group,
            "action_cost": sandbox["action_cost"],
            "downtime_cost": sandbox["downtime_cost"],
            "total_cost": sandbox["total_cost"],
            "base_net": sandbox["base"],
            "low_net": sandbox["low"],
            "high_net": sandbox["high"],
            "uncertainty": sandbox["uncertainty"],
            "measurement": sandbox["measurement"],
        }
    )

    st.session_state.plan_message = (
        f"{action_row.get('name', action_type_id)} was added to the July Action Tray."
    )
    st.session_state.plan_message_type = "success"

    # =============================================================================
# LOAD DATA
# =============================================================================

try:
    DATA = load_data()
except Exception as error:
    st.error(
        "AceIQ could not load its required local data files."
    )
    st.code(str(error))
    st.stop()

report = DATA["report"]
machines = DATA["machines"]
daily = DATA["daily"]
guests = DATA["guests"]
property_daily = DATA["property_daily"]
scenario_samples = DATA["scenario_samples"]

daily_variance = DATA["daily_variance"]
demand_predictions = DATA["demand_predictions"]
floor_locations = DATA["floor_locations"]
floor_walkways = DATA["floor_walkways"]
placements = DATA["placements"]
forecast_metadata = DATA["forecast_metadata"]

initialize_state()

if daily.empty or daily["gaming_date"].dropna().empty:
    st.error("machine_daily.parquet does not contain valid gaming dates.")
    st.stop()

min_date = daily["gaming_date"].min().date()
max_date = daily["gaming_date"].max().date()


# =============================================================================
# HEADER AND NAVIGATION
# =============================================================================

st.markdown(masthead(), unsafe_allow_html=True)

page = st.radio(
    "Navigation",
    [
        "Decision Center",
        "Investigate",
        "July Action Plan",
        "July Demand Outlook",
        "Guest & Loyalty Insights",
        "Methods & Evidence",
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="main_navigation",
)

date_col, note_col = st.columns([1, 2.8])

with date_col:
    selected_dates = st.date_input(
        "Evidence period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

if (
    isinstance(selected_dates, tuple)
    and len(selected_dates) == 2
):
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

period_signature = (
    f"{start_date.date()}_{end_date.date()}"
)

if st.session_state.period_signature is None:
    st.session_state.period_signature = period_signature

elif st.session_state.period_signature != period_signature:
    st.session_state.period_signature = period_signature
    reset_period_state()

with note_col:
    st.markdown(
        f"""
        <div class="arcade-period">
            <strong>Active period:</strong>
            {start_date.strftime("%b %d, %Y")} –
            {end_date.strftime("%b %d, %Y")}<br>
            Machine, downtime, demand, and comp calculations use this local
            synthetic-data evidence period. Forecast holdout validation remains
            fixed to its precomputed May–June test window.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# FILTERED EVIDENCE
# =============================================================================

filtered_daily = daily[
    (
        daily["gaming_date"] >= start_date
    )
    & (
        daily["gaming_date"] <= end_date
    )
].copy()

filtered_property = property_daily[
    (
        property_daily["gaming_date"] >= start_date
    )
    & (
        property_daily["gaming_date"] <= end_date
    )
].copy()

if filtered_daily.empty:
    st.error(
        "No machine data exists for the selected evidence period."
    )
    st.stop()

if filtered_property.empty:
    st.error(
        "No property-level data exists for the selected evidence period."
    )
    st.stop()

full_period_selected = (
    start_date.date() == min_date
    and end_date.date() == max_date
)

machine_summary = build_machine_summary(
    filtered_daily=filtered_daily,
    machines=machines,
    daily_variance=daily_variance,
    use_full_period_screen=full_period_selected,
)

machine_summary = add_location_context(
    machine_summary=machine_summary,
    filtered_daily=filtered_daily,
)

machine_summary["classification"] = machine_summary.apply(
    machine_category,
    axis=1,
)

zone_summary = build_zone_summary(filtered_daily)
bank_summary = build_bank_summary(filtered_daily)
location_lookup = build_location_lookup(floor_locations)
quality_checks = build_data_quality_checks(
    daily=daily,
    property_daily=property_daily,
    machines=machines,
    daily_variance=daily_variance,
    placements=placements,
)

catalog = catalog_dataframe(report)
official = official_simulation_result(report)

machine_ids = sorted(
    machine_summary["machine_id"]
    .astype(str)
    .tolist()
)

if not machine_ids:
    st.error(
        "No machines are available in the selected evidence period."
    )
    st.stop()

if (
    st.session_state.selected_machine_id is None
    or st.session_state.selected_machine_id
    not in machine_ids
):
    st.session_state.selected_machine_id = (
        "M-1158"
        if "M-1158" in machine_ids
        else machine_ids[0]
    )


# =============================================================================
# DECISION CENTER
# =============================================================================

if page == "Decision Center":
    section_header(
        "Decision Center",
        "From low revenue to the right decision.",
        (
            "The raw bottom ten begins the investigation. Exposure, payout "
            "variance, downtime, and placement context determine the next step."
        ),
    )

    if official["keep_budget"]:
        executive_heading = (
            "Do not automatically replace the ten lowest-earning machines."
        )
        executive_text = (
            "The official precomputed 30-day portfolio model ranks preserving "
            "the budget first. Evidence can still support reversible inspection "
            "or operational learning actions."
        )
    else:
        executive_heading = (
            "Use the official portfolio result as the July decision baseline."
        )
        executive_text = (
            "Review the precomputed portfolio recommendation, uncertainty, "
            "assumptions, and limitations before committing budget."
        )

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow" style="color:{TEAL};">
                Executive recommendation
            </div>
            <h2>{html.escape(executive_heading)}</h2>
            <div class="subtle">{html.escape(executive_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_wagers = filtered_property["coin_in_usd"].sum()
    total_actual = filtered_property["house_win_usd"].sum()
    total_expected = filtered_property["theo_usd"].sum()
    total_downtime_opportunity = filtered_daily[
        "missed_theo_mid"
    ].sum()

    metrics = st.columns(4)
    metrics[0].metric(
        "Selected-period wagers",
        money(total_wagers),
    )
    metrics[1].metric(
        "Actual earnings",
        money(total_actual),
    )
    metrics[2].metric(
        "Actual − expected",
        money(total_actual - total_expected),
    )
    metrics[3].metric(
        "Downtime opportunity",
        money(total_downtime_opportunity),
    )

    st.caption(
        "Source: property_daily.parquet and machine_daily.parquet. "
        "Downtime opportunity is historical midpoint theoretical opportunity, "
        "not guaranteed recoverable floor revenue."
    )

    st.markdown("### Why the raw bottom-ten list can fail")

    card_one, card_two, card_three = st.columns(3)

    with card_one:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">1 · Exposure</div>
                <h3>Not every machine had the same opportunity.</h3>
                Installation timing, retirement, and downtime affect raw totals.
                Compare active days, scheduled hours, and available-hour rates.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card_two:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">2 · Luck</div>
                <h3>Actual results can differ from expected results.</h3>
                Slots have payout variation. Compare actual house win with theo
                and its variance before concluding that a machine is weak.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card_three:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">3 · Context</div>
                <h3>Location is a clue, not causal proof.</h3>
                Zone traffic, bank mix, visibility, and guest behavior can all
                create observed differences in machine demand.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    ranking_method = st.radio(
        "Compare bottom-ten machines using",
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
        "Expected earnings per available hour": (
            "expected_per_available_hour"
        ),
    }[ranking_method]

    bottom_ten = (
        machine_summary.sort_values(
            [ranking_column, "machine_id"],
            ascending=[True, True],
        )
        .head(10)
        .copy()
    )

    bottom_ten["actual_index"] = (
        bottom_ten["actual_to_expected"] * 100
    )

    bottom_ten = bottom_ten.sort_values(
        ["actual_index", "machine_id"],
        ascending=[True, True],
    )

    index_colors = []

    for row in bottom_ten.itertuples():
        if str(row.machine_id) == "M-1158":
            index_colors.append(PURPLE)
        elif pd.isna(row.actual_index):
            index_colors.append(GRAY)
        elif row.actual_index < 75:
            index_colors.append(ORANGE)
        elif row.actual_index < 100:
            index_colors.append(GOLD)
        else:
            index_colors.append(GREEN)

    bottom_figure = go.Figure()

    bottom_figure.add_bar(
        y=bottom_ten["machine_id"],
        x=bottom_ten["actual_index"],
        orientation="h",
        marker_color=index_colors,
        customdata=np.column_stack(
            [
                bottom_ten["actual_house_win"],
                bottom_ten["expected_house_win"],
                bottom_ten["actual_minus_expected"],
                bottom_ten["active_days"],
                bottom_ten["availability_rate"],
                bottom_ten["standardized_gap_selected"],
            ]
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Actual as % of expected: %{x:.1f}%<br>"
            "Actual: $%{customdata[0]:,.0f}<br>"
            "Expected: $%{customdata[1]:,.0f}<br>"
            "Actual − expected: $%{customdata[2]:,.0f}<br>"
            "Active days: %{customdata[3]:.0f}<br>"
            "Availability: %{customdata[4]:.1%}<br>"
            "Selected-period standardized residual: %{customdata[5]:.2f}"
            "<extra></extra>"
        ),
        name="Actual / expected",
    )

    bottom_figure.add_vline(
        x=100,
        line_width=2,
        line_dash="dash",
        line_color=TEAL,
        annotation_text="EXPECTED = 100%",
        annotation_position="top",
        annotation_font_color=TEAL,
    )

    bottom_figure.update_xaxes(
        title=(
            "Actual house earnings as a percentage of theoretical earnings"
        ),
        ticksuffix="%",
        rangemode="tozero",
    )

    bottom_figure.update_yaxes(
        title=None,
    )

    render_chart(
        bottom_figure,
        "Did each selected candidate realize expected earnings?",
        "bottom-ten-index-chart",
        height=440,
        legend=False,
    )

    valid_bottom = bottom_ten.dropna(
        subset=["actual_index"]
    )

    if not valid_bottom.empty:
        weakest = valid_bottom.iloc[0]

        standardized_text = (
            f" Its selected-period standardized residual is "
            f"<strong>{safe_float(weakest['standardized_gap_selected']):.2f}</strong>."
            if pd.notna(weakest["standardized_gap_selected"])
            else ""
        )

        insight_bubble(
            "How to read this",
            (
                f"<strong>{html.escape(str(weakest['machine_id']))}</strong> "
                f"realized <strong>{pct(weakest['actual_to_expected'])}</strong> "
                f"of its theoretical earnings in the selected period, with an "
                f"actual-minus-expected result of "
                f"<strong>{money(weakest['actual_minus_expected'])}</strong>."
                f"{standardized_text} "
                "The evidence supports investigation; it does not prove a "
                "defect, misconduct, or causal location problem."
            ),
            tone=(
                "purple"
                if str(weakest["machine_id"]) == "M-1158"
                else "warning"
            ),
        )

    st.markdown("### Residual uncertainty screen")

    residual_plot = machine_summary.dropna(
        subset=[
            "expected_house_win",
            "actual_minus_expected",
            "payout_sd_selected",
        ]
    ).copy()

    if not residual_plot.empty:
        residual_plot["residual_per_sd"] = (
            residual_plot["standardized_gap_selected"]
        )

        residual_figure = go.Figure()

        residual_figure.add_scatter(
            x=residual_plot["expected_house_win"],
            y=residual_plot["actual_minus_expected"],
            mode="markers",
            marker=dict(
                size=9,
                color=residual_plot["residual_per_sd"],
                colorscale=[
                    [0.0, PURPLE],
                    [0.35, RED],
                    [0.5, GOLD],
                    [0.7, TEAL],
                    [1.0, GREEN],
                ],
                cmin=-4,
                cmax=4,
                showscale=True,
                colorbar=dict(
                    title=dict(
                        text="Residual<br>standard deviations",
                        font=dict(color=WHITE),
                    ),
                    tickfont=dict(color=WHITE),
                ),
                line=dict(color=BG, width=1),
            ),
            text=residual_plot["machine_id"],
            customdata=np.column_stack(
                [
                    residual_plot["actual_house_win"],
                    residual_plot["expected_house_win"],
                    residual_plot["actual_minus_expected"],
                    residual_plot["payout_sd_selected"],
                    residual_plot["availability_rate"],
                ]
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Expected earnings: $%{x:,.0f}<br>"
                "Actual − expected: $%{y:,.0f}<br>"
                "Actual: $%{customdata[0]:,.0f}<br>"
                "Expected: $%{customdata[1]:,.0f}<br>"
                "Selected-period payout SD: $%{customdata[3]:,.0f}<br>"
                "Availability: %{customdata[4]:.1%}"
                "<extra></extra>"
            ),
            name="Machine",
        )

        residual_figure.add_hline(
            y=0,
            line_dash="dash",
            line_color=TEAL,
        )

        render_chart(
            residual_figure,
            "Actual-versus-expected residuals need exposure and variance context",
            "residual-uncertainty-chart",
            height=420,
            legend=False,
        )

        insight_bubble(
            "Variance guardrail",
            (
                "A large negative dollar residual is more concerning when it is "
                "large relative to the machine's modeled payout variability. "
                "The chart is a screening tool, not a diagnosis of malfunction."
            ),
            tone="blue",
        )

    st.markdown("### Evidence Claw")

    insight_bubble(
        "How to use it",
        (
            "Draw a machine from the raw total-earnings bottom ten. The claw "
            "reveals local-data evidence only. It does not alter rankings, "
            "recommendations, or the official model."
        ),
        tone="blue",
    )

    raw_bottom = (
        machine_summary.sort_values(
            ["actual_house_win", "machine_id"],
            ascending=[True, True],
        )
        .head(10)["machine_id"]
        .astype(str)
        .tolist()
    )

    capsules = raw_bottom[:4]

    while len(capsules) < 4:
        capsules.append("ACEIQ")

    selected_prize = st.session_state.claw_machine_id

    animation_class = (
        st.session_state.claw_animation_mode
        if selected_prize
        else ""
    )

    prize_html = ""

    if selected_prize:
        prize_html = (
            '<div class="claw-prize">'
            + html.escape(str(selected_prize))
            + "</div>"
        )

    claw_html = (
        '<div class="claw-cabinet '
        + animation_class
        + '">'
        '<div class="claw-neon">✦ EVIDENCE CLAW ✦</div>'
        '<div class="claw-glass">'
        '<div class="claw-rail"></div>'
        '<div class="claw-carriage">'
        '<div class="claw-cable"></div>'
        '<div class="claw-arm">'
        '<div class="prong left"></div>'
        '<div class="prong right"></div>'
        "</div>"
        + prize_html
        + "</div>"
        '<div class="capsule one">'
        + html.escape(capsules[0])
        + "</div>"
        '<div class="capsule two">'
        + html.escape(capsules[1])
        + "</div>"
        '<div class="capsule three">'
        + html.escape(capsules[2])
        + "</div>"
        '<div class="capsule four">'
        + html.escape(capsules[3])
        + "</div>"
        "</div>"
        '<div class="claw-caption">'
        "A low total is the start of an investigation, not the end of one."
        "</div>"
        "</div>"
    )

    st.markdown(
        claw_html,
        unsafe_allow_html=True,
    )

    if st.button(
        "🕹 Grab a machine",
        type="primary",
        use_container_width=True,
    ):
        choices = [
            machine_id
            for machine_id in raw_bottom
            if machine_id != selected_prize
        ]

        if not choices:
            choices = raw_bottom

        rng = np.random.default_rng(
            2025 + st.session_state.claw_count
        )

        selected = str(rng.choice(choices))

        st.session_state.claw_machine_id = selected
        st.session_state.selected_machine_id = selected
        st.session_state.claw_count += 1
        st.session_state.claw_animation_mode = (
            "claw-run-b"
            if st.session_state.claw_animation_mode
            == "claw-run-a"
            else "claw-run-a"
        )

        st.rerun()

    if selected_prize and selected_prize in machine_ids:
        picked = (
            machine_summary.set_index("machine_id")
            .loc[selected_prize]
            .copy()
        )

        result_title, result_reason, accent = (
            recommendation_for_machine(picked)
        )

        selected_left, selected_right = st.columns([1.2, .8])

        with selected_left:
            st.markdown(
                f"""
                <div class="panel"
                     style="margin-top:.7rem;border-left:4px solid {accent};">
                    <div class="eyebrow">Claw result</div>
                    <h3>♠ {html.escape(str(selected_prize))}</h3>
                    <span class="status-pill"
                          style="color:{accent};
                                 background:{accent}22;
                                 border:1px solid {accent}66;">
                        {html.escape(machine_category(picked))}
                    </span>
                    <div class="subtle" style="margin-top:.6rem;">
                        <strong>{html.escape(result_title)}</strong><br>
                        {html.escape(result_reason)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with selected_right:
            result_metrics = st.columns(2)
            result_metrics[0].metric(
                "Actual",
                money(picked["actual_house_win"]),
            )
            result_metrics[1].metric(
                "Expected",
                money(picked["expected_house_win"]),
            )
            result_metrics[0].metric(
                "Availability",
                pct(picked["availability_rate"]),
            )
            result_metrics[1].metric(
                "Residual",
                money(picked["actual_minus_expected"]),
            )

    monthly_demand = (
        filtered_property.assign(
            month=filtered_property["gaming_date"]
            .dt.strftime("%Y-%m")
        )
        .groupby("month", as_index=False)
        .agg(
            wagers=("coin_in_usd", "sum"),
            available_hours=(
                "available_machine_hours",
                "sum",
            ),
        )
    )

    if not monthly_demand.empty:
        monthly_demand["wagers_per_available_hour"] = (
            monthly_demand["wagers"]
            / monthly_demand["available_hours"].replace(
                0,
                np.nan,
            )
        )

        demand_figure = go.Figure()

        demand_figure.add_scatter(
            x=monthly_demand["month"],
            y=monthly_demand[
                "wagers_per_available_hour"
            ],
            mode="lines+markers",
            line=dict(color=GOLD, width=3),
            marker=dict(
                color=GOLD_LIGHT,
                size=9,
                line=dict(color=BG, width=1),
            ),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Wagers per available machine-hour: $%{y:,.2f}"
                "<extra></extra>"
            ),
            name="Observed demand",
        )

        demand_figure.update_yaxes(
            title="Wagers per available machine-hour",
            tickprefix="$",
        )

        render_chart(
            demand_figure,
            "Demand over time",
            "decision-center-demand-chart",
            height=330,
            legend=False,
        )

        peak_row = monthly_demand.loc[
            monthly_demand[
                "wagers_per_available_hour"
            ].idxmax()
        ]

        latest_row = monthly_demand.iloc[-1]

        change_from_peak = (
            latest_row["wagers_per_available_hour"]
            / peak_row["wagers_per_available_hour"]
            - 1
        )

        insight_bubble(
            "Demand takeaway",
            (
                f"Demand peaked in <strong>{peak_row['month']}</strong> at "
                f"<strong>{money(peak_row['wagers_per_available_hour'], 2)}</strong> "
                "per available machine-hour. The latest visible month was "
                f"<strong>{latest_row['month']}</strong> at "
                f"<strong>{money(latest_row['wagers_per_available_hour'], 2)}</strong>, "
                f"a change of <strong>{pct(change_from_peak)}</strong> from the peak."
            ),
        )


# =============================================================================
# INVESTIGATE
# =============================================================================

elif page == "Investigate":
    section_header(
        "Machine Investigation",
        "Luck, location, downtime, or a persistent gap?",
        (
            "Follow one machine from descriptive evidence to a reversible "
            "operational next step."
        ),
    )

    filters = st.columns(3)
    pool = machine_summary.copy()

    with filters[0]:
        zone_options = sorted(
            pool["zone_name"]
            .dropna()
            .astype(str)
            .unique()
        )

        zone_filter = st.selectbox(
            "Zone",
            ["All zones"] + zone_options,
        )

    if zone_filter != "All zones":
        pool = pool[
            pool["zone_name"].astype(str)
            == zone_filter
        ]

    with filters[1]:
        bank_options = sorted(
            pool["bank_id"]
            .dropna()
            .astype(str)
            .unique()
        )

        bank_filter = st.selectbox(
            "Bank",
            ["All banks"] + bank_options,
        )

    if bank_filter != "All banks":
        pool = pool[
            pool["bank_id"].astype(str)
            == bank_filter
        ]

    with filters[2]:
        manufacturer_options = sorted(
            pool["manufacturer"]
            .dropna()
            .astype(str)
            .unique()
        )

        manufacturer_filter = st.selectbox(
            "Manufacturer",
            ["All manufacturers"] + manufacturer_options,
        )

    if manufacturer_filter != "All manufacturers":
        pool = pool[
            pool["manufacturer"].astype(str)
            == manufacturer_filter
        ]

    investigate_options = sorted(
        pool["machine_id"]
        .astype(str)
        .tolist()
    )

    if not investigate_options:
        st.warning(
            "No machines match the selected filters."
        )
        st.stop()

    selected_machine_index = (
        investigate_options.index(
            st.session_state.selected_machine_id
        )
        if st.session_state.selected_machine_id
        in investigate_options
        else 0
    )

    selected_machine_id = st.selectbox(
        "Select machine",
        investigate_options,
        index=selected_machine_index,
    )

    st.session_state.selected_machine_id = (
        selected_machine_id
    )

    machine = (
        machine_summary.set_index("machine_id")
        .loc[selected_machine_id]
        .copy()
    )

    machine["machine_id"] = selected_machine_id

    conclusion, conclusion_reason, accent = (
        recommendation_for_machine(machine)
    )

    st.markdown(
        f"""
        <div class="panel"
             style="border-left:4px solid {accent};">
            <div class="eyebrow">Machine conclusion</div>
            <h2>♠ {html.escape(selected_machine_id)}</h2>
            <span class="status-pill"
                  style="color:{accent};
                         background:{accent}22;
                         border:1px solid {accent}66;">
                {html.escape(machine_category(machine))}
            </span>
            <div class="subtle" style="margin-top:.6rem;">
                <strong>{html.escape(conclusion)}</strong><br>
                {html.escape(conclusion_reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    investigation_metrics = st.columns(6)

    investigation_metrics[0].metric(
        "Actual",
        money(machine["actual_house_win"]),
    )
    investigation_metrics[1].metric(
        "Expected",
        money(machine["expected_house_win"]),
    )
    investigation_metrics[2].metric(
        "Actual − expected",
        money(machine["actual_minus_expected"]),
    )
    investigation_metrics[3].metric(
        "Availability",
        pct(machine["availability_rate"]),
    )
    investigation_metrics[4].metric(
        "Active days",
        f"{int(machine['active_days']):,}",
    )
    investigation_metrics[5].metric(
        "Residual SDs",
        (
            f"{safe_float(machine['standardized_gap_selected']):.2f}"
            if pd.notna(
                machine["standardized_gap_selected"]
            )
            else "—"
        ),
    )

    if not full_period_selected:
        st.markdown(
            """
            <div class="notice">
                <strong>Selected-period screen:</strong> the standardized residual
                shown above is recalculated from selected-period daily variance.
                The precomputed full-period inspection screen is intentionally
                hidden unless Jan. 1–Jun. 30 is selected.
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif pd.notna(machine.get("standardized_gap", np.nan)):
        st.markdown(
            f"""
            <div class="notice">
                <strong>Full-period screen:</strong> precomputed standardized payout
                gap = <strong>{safe_float(machine["standardized_gap"]):.2f}</strong>.
                Values at or below −3 are inspection leads, not proof of a defect.
            </div>
            """,
            unsafe_allow_html=True,
        )

    selected_daily = filtered_daily[
        filtered_daily["machine_id"].astype(str)
        == selected_machine_id
    ].sort_values("gaming_date").copy()

    selected_daily["cumulative_actual"] = (
        selected_daily["house_win_usd"].cumsum()
    )
    selected_daily["cumulative_expected"] = (
        selected_daily["theo_usd"].cumsum()
    )
    selected_daily["cumulative_residual"] = (
        selected_daily["house_win_usd"]
        - selected_daily["theo_usd"]
    ).cumsum()

    chart_left, chart_right = st.columns([1.15, .85])

    with chart_left:
        cumulative_figure = go.Figure()

        cumulative_figure.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_actual"],
            name="Actual",
            mode="lines",
            line=dict(color=GOLD, width=3),
        )

        cumulative_figure.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_expected"],
            name="Expected",
            mode="lines",
            line=dict(color=TEAL, width=3),
        )

        cumulative_figure.update_yaxes(
            title="Cumulative house earnings",
            tickprefix="$",
        )

        render_chart(
            cumulative_figure,
            "Did the actual-versus-expected gap persist?",
            "machine-cumulative-chart",
            height=385,
        )

    with chart_right:
        downtime_days = selected_daily[
            selected_daily["down_hours"] > 0
        ].copy()

        if downtime_days.empty:
            st.markdown(
                """
                <div class="panel"
                     style="min-height:310px;
                            display:flex;
                            flex-direction:column;
                            justify-content:center;">
                    <div class="eyebrow">Downtime evidence</div>
                    <h3>No selected-period downtime incidents</h3>
                    <div class="subtle">
                        No machine-day has positive downtime hours in the selected
                        evidence period.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            downtime_figure = go.Figure()

            downtime_figure.add_bar(
                x=downtime_days["gaming_date"],
                y=downtime_days["down_hours"],
                marker_color=ORANGE,
                name="Downtime",
                hovertemplate=(
                    "<b>%{x|%b %d, %Y}</b><br>"
                    "Downtime: %{y:.2f} hours"
                    "<extra></extra>"
                ),
            )

            downtime_figure.update_yaxes(
                title="Downtime hours",
                rangemode="tozero",
            )

            render_chart(
                downtime_figure,
                "Downtime incidents only",
                "machine-downtime-chart",
                height=385,
                legend=False,
            )

    selected_variance = daily_variance[
        daily_variance["machine_id"].astype(str)
        == selected_machine_id
    ].copy()

    if not selected_variance.empty:
        selected_variance = selected_variance[
            (
                selected_variance["gaming_date"]
                >= start_date
            )
            & (
                selected_variance["gaming_date"]
                <= end_date
            )
        ].sort_values("gaming_date")

        if not selected_variance.empty:
            selected_variance["cumulative_sd"] = np.sqrt(
                selected_variance["variance_usd2"]
                .clip(lower=0)
                .cumsum()
            )

            uncertainty_figure = go.Figure()

            uncertainty_figure.add_scatter(
                x=selected_daily["gaming_date"],
                y=selected_daily["cumulative_residual"],
                mode="lines",
                name="Cumulative actual − expected",
                line=dict(color=PURPLE, width=3),
            )

            uncertainty_figure.add_scatter(
                x=selected_variance["gaming_date"],
                y=1.96 * selected_variance["cumulative_sd"],
                mode="lines",
                name="+ 1.96 payout SD",
                line=dict(
                    color=TEAL,
                    width=2,
                    dash="dot",
                ),
            )

            uncertainty_figure.add_scatter(
                x=selected_variance["gaming_date"],
                y=-1.96 * selected_variance["cumulative_sd"],
                mode="lines",
                name="− 1.96 payout SD",
                line=dict(
                    color=TEAL,
                    width=2,
                    dash="dot",
                ),
                fill="tonexty",
                fillcolor="rgba(105,214,203,.10)",
            )

            uncertainty_figure.update_yaxes(
                title="Cumulative residual / modeled variability",
                tickprefix="$",
            )

            render_chart(
                uncertainty_figure,
                "Residual against cumulative payout-variance context",
                "machine-variance-context-chart",
                height=365,
            )

            st.caption(
                "The teal band is 1.96 × cumulative modeled payout standard "
                "deviation under the supplied variance inputs. It is a "
                "screening context, not a guaranteed confidence interval."
            )

    availability_value = safe_float(
        machine["availability_rate"],
        np.nan,
    )
    gap_value = safe_float(
        machine["actual_minus_expected"],
        np.nan,
    )
    standardized_value = safe_float(
        machine["standardized_gap_selected"],
        np.nan,
    )

    if (
        full_period_selected
        and safe_float(machine.get("standardized_gap", np.nan), 0)
        <= -3
    ):
        investigation_message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> has a "
            f"full-period standardized payout gap of "
            f"<strong>{safe_float(machine['standardized_gap']):.2f}</strong> "
            f"and <strong>{pct(availability_value)}</strong> availability. "
            "Downtime alone is insufficient to explain the result. Inspection "
            "of configuration, game math, and meters is the reversible next step."
        )
        investigation_tone = "purple"

    elif availability_value < .90:
        investigation_message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> had "
            f"<strong>{pct(availability_value)}</strong> availability with "
            f"<strong>{machine['downtime_hours']:.1f}</strong> downtime hours. "
            "The machine did not have a fully comparable opportunity to earn, "
            "so maintenance evidence should be addressed before replacement."
        )
        investigation_tone = "warning"

    else:
        standardized_clause = (
            f" Its selected-period residual is "
            f"<strong>{standardized_value:.2f}</strong> modeled payout standard "
            "deviations from expected."
            if np.isfinite(standardized_value)
            else ""
        )

        investigation_message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> finished "
            f"<strong>{money(gap_value)}</strong> versus expected with "
            f"<strong>{pct(availability_value)}</strong> availability."
            f"{standardized_clause} "
            "The evidence supports peer comparison and monitoring before an "
            "irreversible action."
        )
        investigation_tone = "normal"

    insight_bubble(
        "Investigation takeaway",
        investigation_message,
        tone=investigation_tone,
    )

    # -------------------------------------------------------------------------
    # Peer context
    # -------------------------------------------------------------------------

    peers = machine_summary[
        machine_summary["theme"].astype(str)
        == str(machine.get("theme", ""))
    ].copy()

    peer_label = "Same-theme machines"

    if len(peers) < 3:
        peers = machine_summary[
            machine_summary["zone_name"].astype(str)
            == str(machine.get("zone_name", ""))
        ].copy()
        peer_label = "Same-zone machines"

    if not peers.empty:
        selected_peers = (
            peers.sort_values(
                "expected_per_available_hour",
                ascending=True,
            )
            .tail(min(14, len(peers)))
            .copy()
        )

        peer_colors = [
            PURPLE
            if str(machine_id) == selected_machine_id
            else GOLD
            for machine_id in selected_peers["machine_id"]
        ]

        peer_figure = go.Figure()

        peer_figure.add_bar(
            x=selected_peers[
                "expected_per_available_hour"
            ],
            y=selected_peers["machine_id"],
            orientation="h",
            marker_color=peer_colors,
            customdata=np.column_stack(
                [
                    selected_peers["actual_per_available_hour"],
                    selected_peers["availability_rate"],
                    selected_peers[
                        "standardized_gap_selected"
                    ],
                ]
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Expected/hour: $%{x:,.2f}<br>"
                "Actual/hour: $%{customdata[0]:,.2f}<br>"
                "Availability: %{customdata[1]:.1%}<br>"
                "Selected residual SDs: %{customdata[2]:.2f}"
                "<extra></extra>"
            ),
            name="Expected/hour",
        )

        peer_figure.update_xaxes(
            title="Expected earnings per available hour",
            tickprefix="$",
        )

        render_chart(
            peer_figure,
            f"{peer_label}: exposure-adjusted earning rate",
            "machine-peer-context-chart",
            height=365,
            legend=False,
        )

        insight_bubble(
            "Peer-context guardrail",
            (
                f"This comparison uses <strong>{html.escape(peer_label.lower())}</strong>. "
                "It is descriptive. It does not fully adjust for denomination, "
                "guest mix, specific sightlines, occupancy, or all floor conditions."
            ),
            tone="blue",
        )

    # -------------------------------------------------------------------------
    # Placement / movement evidence
    # -------------------------------------------------------------------------

    st.markdown("### Placement and floor context")

    movement_segments = movement_history(
        selected_machine_id,
        filtered_daily,
    )

    placement_left, placement_right = st.columns([1.05, .95])

    with placement_left:
        if movement_segments.empty:
            st.info(
                "No observed selected-period placement data is available "
                "for this machine."
            )

        else:
            movement_display = movement_segments.copy()

            movement_display["start_date"] = (
                movement_display["start_date"].dt.strftime(
                    "%b %d, %Y"
                )
            )
            movement_display["end_date"] = (
                movement_display["end_date"].dt.strftime(
                    "%b %d, %Y"
                )
            )

            st.dataframe(
                movement_display[
                    [
                        "zone_name",
                        "bank_id",
                        "start_date",
                        "end_date",
                        "days",
                        "available_hours",
                        "wagers_per_available_hour",
                        "expected_per_available_hour",
                        "actual_minus_expected",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            if len(movement_segments) > 1:
                move_comparison = descriptive_move_comparison(
                    selected_machine_id,
                    filtered_daily,
                    machine_summary,
                )

                if move_comparison["available"]:
                    insight_bubble(
                        "Observed movement comparison",
                        (
                            f"The machine's expected earnings per available hour "
                            f"changed from "
                            f"<strong>{money(move_comparison['machine_before_rate'], 2)}</strong> "
                            f"to "
                            f"<strong>{money(move_comparison['machine_after_rate'], 2)}</strong>. "
                            f"A stable-peer benchmark changed by "
                            f"<strong>{money(move_comparison['peer_change'], 2)}</strong> "
                            f"over the corresponding periods. The descriptive "
                            f"difference is "
                            f"<strong>{money(move_comparison['descriptive_difference'], 2)}</strong> "
                            f"per available hour using "
                            f"<strong>{move_comparison['peer_count']:,}</strong> stable peers. "
                            "This is not causal proof because placement changes "
                            "may coincide with other operational differences."
                        ),
                        tone="blue",
                    )
            else:
                insight_bubble(
                    "Placement finding",
                    (
                        "No bank movement was observed in the selected period. "
                        "Location effects therefore cannot be tested through a "
                        "before-versus-after move for this machine."
                    ),
                    tone="blue",
                )

    with placement_right:
        if location_lookup.empty:
            st.info(
                "floor_locations.parquet is unavailable, so no floor-coordinate "
                "map can be displayed."
            )

        else:
            floor_data = (
                bank_summary.merge(
                    location_lookup,
                    on="bank_id",
                    how="left",
                )
                .dropna(subset=["x_m", "y_m"])
                .copy()
            )

            if floor_data.empty:
                st.info(
                    "No bank summary rows could be matched to floor coordinates."
                )

            else:
                floor_data["selected_bank"] = (
                    floor_data["bank_id"].astype(str)
                    == str(machine.get("bank_id", ""))
                )

                floor_figure = go.Figure()

                floor_figure.add_scatter(
                    x=floor_data["x_m"],
                    y=floor_data["y_m"],
                    mode="markers+text",
                    text=floor_data["bank_id"],
                    textposition="top center",
                    marker=dict(
                        size=np.clip(
                            floor_data["machine_count"] * 3,
                            10,
                            25,
                        ),
                        color=floor_data[
                            "wagers_per_available_hour"
                        ],
                        colorscale="YlOrBr",
                        showscale=True,
                        colorbar=dict(
                            title=dict(
                                text="Wagers /<br>available hour",
                                font=dict(color=WHITE),
                            ),
                            tickfont=dict(color=WHITE),
                        ),
                        line=dict(color=BG, width=1),
                    ),
                    customdata=np.column_stack(
                        [
                            floor_data["zone_name"],
                            floor_data["wagers_per_available_hour"],
                            floor_data["availability_rate"],
                            floor_data["downtime_opportunity"],
                        ]
                    ),
                    hovertemplate=(
                        "<b>%{text}</b><br>"
                        "Zone: %{customdata[0]}<br>"
                        "Wagers / available hour: $%{customdata[1]:,.2f}<br>"
                        "Availability: %{customdata[2]:.1%}<br>"
                        "Downtime theo opportunity: $%{customdata[3]:,.0f}"
                        "<extra></extra>"
                    ),
                    name="Banks",
                )

                selected_bank_rows = floor_data[
                    floor_data["selected_bank"]
                ]

                if not selected_bank_rows.empty:
                    floor_figure.add_scatter(
                        x=selected_bank_rows["x_m"],
                        y=selected_bank_rows["y_m"],
                        mode="markers",
                        marker=dict(
                            size=30,
                            color="rgba(0,0,0,0)",
                            line=dict(
                                color=PURPLE,
                                width=4,
                            ),
                        ),
                        hoverinfo="skip",
                        name="Selected bank",
                    )

                floor_figure.update_xaxes(
                    title="Floor X coordinate (meters)",
                )
                floor_figure.update_yaxes(
                    title="Floor Y coordinate (meters)",
                    scaleanchor="x",
                    scaleratio=1,
                )

                render_chart(
                    floor_figure,
                    "Selected-period bank context",
                    "machine-floor-map",
                    height=440,
                )

    if not floor_walkways.empty:
        walkway_count = len(floor_walkways)

        walkway_closures = floor_walkways[
            floor_walkways["closed_from_utc"].notna()
        ].copy()

        closure_text = (
            f"{len(walkway_closures):,} walkway closure records exist."
            if not walkway_closures.empty
            else "No walkway closure records are present."
        )

        st.caption(
            f"Walkway context: {walkway_count:,} floor connections are supplied. "
            f"{closure_text} Walkway adjacency provides floor context only; it "
            "does not establish that traffic caused machine performance."
        )

    st.markdown(
        """
        <div class="warning">
            A payout gap is an inspection lead. It is not proof of malfunction,
            fraud, tampering, cheating, or wrongdoing. Location comparisons are
            descriptive unless a controlled test is designed in advance.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Open detailed selected-period machine evidence"):
        evidence_columns = [
            "machine_id",
            "manufacturer",
            "theme",
            "zone_name",
            "bank_id",
            "active_days",
            "availability_rate",
            "actual_house_win",
            "expected_house_win",
            "actual_minus_expected",
            "actual_to_expected",
            "expected_per_available_hour",
            "actual_per_available_hour",
            "payout_sd_selected",
            "standardized_gap_selected",
            "standardized_gap",
            "downtime_hours",
            "estimated_downtime_opportunity",
            "classification",
        ]

        evidence_columns = [
            column
            for column in evidence_columns
            if column in machine_summary.columns
        ]

        st.dataframe(
            machine_summary[
                evidence_columns
            ].sort_values(
                "actual_house_win"
            ),
            use_container_width=True,
            hide_index=True,
        )

        download_csv(
            machine_summary,
            "aceiq_machine_diagnostics.csv",
            "Download machine diagnostics CSV",
        )


        # =============================================================================
# JULY ACTION PLAN
# =============================================================================

elif page == "July Action Plan":
    section_header(
        "July Action Plan",
        "Price the decision before spending.",
        (
            "Catalog costs and limits are local challenge data. Benefit ranges "
            "are visible planning sensitivities, not causal claims."
        ),
    )

    if catalog.empty:
        st.error(
            "The action catalog is missing from analysis_results.json."
        )
        st.stop()

    if official["keep_budget"]:
        st.markdown(
            """
            <div class="hero">
                <div class="eyebrow" style="color:#69D6CB;">
                    Official precomputed result
                </div>
                <h2>
                    Preserve Budget ranks first in the official 30-day portfolio model.
                </h2>
                <div class="subtle">
                    The tray below is an interactive planning sandbox. It does not
                    replace the official precomputed simulation or convert scenario
                    assumptions into causal findings.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    action_names = (
        catalog.set_index("action_type_id")["name"]
        .to_dict()
    )

    action_ids = catalog["action_type_id"].astype(str).tolist()

    if (
        st.session_state.selected_action_type_id
        not in action_ids
    ):
        st.session_state.selected_action_type_id = (
            "A-HOLD"
            if "A-HOLD" in action_ids
            else action_ids[0]
        )

    control_left, control_center, control_right = st.columns(
        [1.05, 1.05, 1.1]
    )

    with control_left:
        selected_action_id = st.selectbox(
            "Catalog action",
            action_ids,
            index=action_ids.index(
                st.session_state.selected_action_type_id
            ),
            format_func=lambda action_id: (
                action_names.get(action_id, action_id)
            ),
        )

        st.session_state.selected_action_type_id = (
            selected_action_id
        )

        action_row = (
            catalog[
                catalog["action_type_id"]
                == selected_action_id
            ]
            .iloc[0]
            .copy()
        )

        action_unit = str(action_row.get("unit", "none"))
        action_cost = action_cost_from_catalog(action_row)

        st.markdown(
            f"""
            <div class="panel" style="margin-top:.65rem;">
                <div class="eyebrow">Catalog terms</div>
                <h3>{html.escape(str(action_row.get("name", "")))}</h3>
                <div class="subtle">
                    <strong>Catalog cost:</strong> {money(action_cost)}<br>
                    <strong>Lead time:</strong> {int(safe_float(action_row.get("lead_days", 0)))} days<br>
                    <strong>Planned downtime:</strong> {safe_float(action_row.get("downtime_minutes", 0)):.0f} minutes per target<br>
                    <strong>Quantity limit:</strong> {int(safe_float(action_row.get("quantity_limit", 0)))}<br>
                    {html.escape(str(action_row.get("notes", "")))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    target_machine_ids: list[str] = []
    selected_target = "No target required"

    with control_center:
        if action_unit == "machine":
            eligible_machines = machine_summary[
                machine_summary["eligible_july"]
            ].copy()

            if selected_action_id == "A-INSPECT":
                target_options = sorted(
                    eligible_machines["machine_id"]
                    .astype(str)
                    .tolist()
                )
            else:
                target_options = sorted(
                    eligible_machines["machine_id"]
                    .astype(str)
                    .tolist()
                )

            if not target_options:
                st.warning(
                    "No July-eligible machine targets are available."
                )
                st.stop()

            default_machine = (
                st.session_state.selected_machine_id
                if st.session_state.selected_machine_id
                in target_options
                else target_options[0]
            )

            selected_target = st.selectbox(
                "Machine target",
                target_options,
                index=target_options.index(
                    default_machine
                ),
            )

            target_machine_ids = [selected_target]

            target_machine = (
                machine_summary.set_index("machine_id")
                .loc[selected_target]
            )

            target_title, target_reason, target_color = (
                recommendation_for_machine(target_machine)
            )

            st.markdown(
                f"""
                <div class="panel"
                     style="margin-top:.65rem;border-left:4px solid {target_color};">
                    <div class="eyebrow">Target evidence</div>
                    <h3>{html.escape(selected_target)}</h3>
                    <div class="subtle">
                        <strong>{html.escape(target_title)}</strong><br>
                        {html.escape(target_reason)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "bank":
            bank_options = (
                bank_summary.sort_values(
                    ["zone_name", "bank_id"]
                )
                .apply(
                    lambda row: (
                        f"{row['zone_name']} | {row['bank_id']}"
                    ),
                    axis=1,
                )
                .tolist()
            )

            selected_target = st.selectbox(
                "Bank target",
                bank_options,
            )

            selected_bank = selected_target.split(" | ")[-1]

            target_machine_ids = (
                machine_summary[
                    (
                        machine_summary["bank_id"]
                        .astype(str)
                        == selected_bank
                    )
                    & (
                        machine_summary["eligible_july"]
                    )
                ]["machine_id"]
                .astype(str)
                .tolist()
            )

            bank_evidence = bank_summary[
                bank_summary["bank_id"].astype(str)
                == selected_bank
            ]

            if not bank_evidence.empty:
                bank_row = bank_evidence.iloc[0]

                st.markdown(
                    f"""
                    <div class="panel" style="margin-top:.65rem;">
                        <div class="eyebrow">Bank evidence</div>
                        <h3>{html.escape(selected_target)}</h3>
                        <div class="subtle">
                            Machines: <strong>{int(bank_row['machine_count'])}</strong><br>
                            Availability: <strong>{pct(bank_row['availability_rate'])}</strong><br>
                            Wagers / available hour:
                            <strong>{money(bank_row['wagers_per_available_hour'], 2)}</strong><br>
                            Downtime opportunity:
                            <strong>{money(bank_row['downtime_opportunity'])}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        elif action_unit == "manufacturer":
            manufacturer_options = sorted(
                machine_summary[
                    machine_summary["eligible_july"]
                ]["manufacturer"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_target = st.selectbox(
                "Manufacturer target",
                manufacturer_options,
            )

            target_machine_ids = (
                machine_summary[
                    (
                        machine_summary["manufacturer"]
                        .astype(str)
                        == selected_target
                    )
                    & (
                        machine_summary["eligible_july"]
                    )
                ]["machine_id"]
                .astype(str)
                .tolist()
)

            manufacturer_daily = filtered_daily[
                filtered_daily["machine_id"]
                .astype(str)
                .isin(target_machine_ids)
            ]

            st.markdown(
                f"""
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Manufacturer evidence</div>
                    <h3>{html.escape(selected_target)}</h3>
                    <div class="subtle">
                        July-eligible machines:
                        <strong>{len(target_machine_ids):,}</strong><br>
                        Selected-period downtime:
                        <strong>{manufacturer_daily['down_hours'].sum():,.1f} hours</strong><br>
                        Midpoint theo opportunity:
                        <strong>{money(manufacturer_daily['missed_theo_mid'].sum())}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "zone":
            zone_options = sorted(
                zone_summary["zone_name"]
                .dropna()
                .astype(str)
                .unique()
            )

            selected_target = st.selectbox(
                "Zone target",
                zone_options,
            )

            target_machine_ids = (
                machine_summary[
                    (
                        machine_summary["zone_name"]
                        .astype(str)
                        == selected_target
                    )
                    & (
                        machine_summary["eligible_july"]
                    )
                ]["machine_id"]
                .astype(str)
                .tolist()
            )

            zone_evidence = zone_summary[
                zone_summary["zone_name"].astype(str)
                == selected_target
            ]

            if not zone_evidence.empty:
                zone_row = zone_evidence.iloc[0]

                st.markdown(
                    f"""
                    <div class="panel" style="margin-top:.65rem;">
                        <div class="eyebrow">Zone evidence</div>
                        <h3>{html.escape(selected_target)}</h3>
                        <div class="subtle">
                            Machines: <strong>{int(zone_row['machine_count'])}</strong><br>
                            Wagers / available hour:
                            <strong>{money(zone_row['wagers_per_available_hour'], 2)}</strong><br>
                            Availability:
                            <strong>{pct(zone_row['availability_rate'])}</strong><br>
                            Downtime opportunity:
                            <strong>{money(zone_row['downtime_opportunity'])}</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        elif action_unit == "technician_shift":
            selected_target = st.selectbox(
                "Shift package target",
                [
                    "One additional shift; roster assignment required",
                    "Priority: highest downtime-opportunity machines",
                    "Priority: highest repeat downtime zone",
                ],
            )

            target_machine_ids = (
                machine_summary.sort_values(
                    "estimated_downtime_opportunity",
                    ascending=False,
                )
                .head(40)["machine_id"]
                .astype(str)
                .tolist()
            )

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Operational targeting note</div>
                    <h3>Technician package</h3>
                    <div class="subtle">
                        The available local files do not include shift rosters or
                        repair-ticket timestamps. The target is therefore a
                        planning placeholder, not a verified shift assignment.
                        Measure response time and unavailable hours before scaling.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "policy":
            selected_target = st.selectbox(
                "Comp policy target",
                [
                    "Floor-wide: proposed 12 points per comp face-value dollar",
                    "Floor-wide: proposed 10 points per comp face-value dollar",
                    "Floor-wide: proposed 15 points per comp face-value dollar",
                ],
            )

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Ethical policy guardrail</div>
                    <h3>Floor-wide comp policy</h3>
                    <div class="subtle">
                        Do not target individual guests based on gambling losses.
                        Track hospitality, redemption, and comp-cost outcomes;
                        do not treat player-loss behavior as a marketing signal.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "pilot":
            selected_target = (
                "Randomized pilot with unchanged total comp budget"
            )

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Pilot design</div>
                    <h3>Comp policy pilot with control group</h3>
                    <div class="subtle">
                        The catalog identifies this as a learning action.
                        Preserve a clearly defined control group and avoid
                        targeting based on gambling-loss behavior.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "event":
            selected_target = st.selectbox(
                "Promotion target",
                [
                    "One July promotion weekend",
                    "One July weekday promotion test",
                ],
            )

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Promotion guardrail</div>
                    <h3>Promotion measurement</h3>
                    <div class="subtle">
                        Compare against matched historical weekdays or a
                        pre-registered baseline. Do not interpret higher gross
                        wagers alone as incremental contribution.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif action_unit == "month":
            selected_target = "July expanded guest intercept survey"

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Information action</div>
                    <h3>Expanded guest survey</h3>
                    <div class="subtle">
                        This creates information value rather than guaranteed
                        immediate cash contribution. Track response rate,
                        representation, and whether findings change a later decision.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            selected_target = "Preserve the $100,000 budget"

            st.markdown(
                """
                <div class="panel" style="margin-top:.65rem;">
                    <div class="eyebrow">Baseline</div>
                    <h3>Preserve Budget</h3>
                    <div class="subtle">
                        No July spending action is added. This is a valid portfolio
                        decision, not a claim that every future intervention is
                        unprofitable.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with control_right:
        st.slider(
            "Retained incremental play",
            min_value=.10,
            max_value=1.00,
            step=.05,
            key="retained_play",
            format="%.0f%%",
        )

        st.slider(
            "Maintenance recovery",
            min_value=.10,
            max_value=.85,
            step=.05,
            key="maintenance_recovery",
            format="%.0f%%",
        )

        st.slider(
            "New-title uplift",
            min_value=0.00,
            max_value=1.50,
            step=.05,
            key="lease_uplift",
            format="%.0f%%",
        )

        st.slider(
            "Location / signage uplift",
            min_value=-.10,
            max_value=.80,
            step=.05,
            key="move_uplift",
            format="%.0f%%",
        )

        st.slider(
            "Comp-cost savings",
            min_value=0.00,
            max_value=.25,
            step=.01,
            key="comp_savings",
            format="%.0f%%",
        )

    sandbox = estimate_action_sandbox(
        action_row=action_row,
        target=selected_target,
        target_machine_ids=target_machine_ids,
        machine_summary=machine_summary,
        zone_summary=zone_summary,
        filtered_daily=filtered_daily,
        filtered_property=filtered_property,
        retained_play=st.session_state.retained_play,
        maintenance_recovery=st.session_state.maintenance_recovery,
        lease_uplift=st.session_state.lease_uplift,
        move_uplift=st.session_state.move_uplift,
        comp_savings=st.session_state.comp_savings,
    )

    scenario_metrics = st.columns(6)

    scenario_metrics[0].metric(
        "Catalog cost",
        money(sandbox["action_cost"]),
    )
    scenario_metrics[1].metric(
        "Downtime cost",
        money(sandbox["downtime_cost"]),
    )
    scenario_metrics[2].metric(
        "Low case",
        money(sandbox["low"]),
    )
    scenario_metrics[3].metric(
        "Base case",
        money(sandbox["base"]),
    )
    scenario_metrics[4].metric(
        "High case",
        money(sandbox["high"]),
    )
    scenario_metrics[5].metric(
        "Uncertainty",
        sandbox["uncertainty"],
    )

    insight_bubble(
        sandbox["signal"],
        (
            f"<strong>Assumption:</strong> "
            f"{html.escape(sandbox['assumptions'])}<br><br>"
            f"<strong>Limitation:</strong> "
            f"{html.escape(sandbox['limitation'])}<br><br>"
            f"<strong>Measurement:</strong> "
            f"{html.escape(sandbox['measurement'])}"
        ),
        tone=(
            "warning"
            if sandbox["base"] < 0
            else "blue"
        ),
    )

    st.markdown(
        """
        <div class="warning">
            Sandbox benefits are sensitivity assumptions, not observed causal
            effects. Catalog costs, limits, lead times, and downtime minutes are
            local challenge inputs. The official precomputed simulation remains
            the portfolio decision reference.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    section_header(
        "Budget Controls",
        "July Action Tray",
        (
            "$100,000 maximum · no more than three action types · catalog "
            "quantity limits and incompatibility groups enforced."
        ),
    )

    tray_button_left, tray_button_center, _ = st.columns(
        [1, 1, 2]
    )

    with tray_button_left:
        if st.button(
            "Add to tray",
            type="primary",
            use_container_width=True,
        ):
            add_to_plan(
                action_row=action_row,
                target=selected_target,
                sandbox=sandbox,
                catalog=catalog,
            )

    with tray_button_center:
        if st.button(
            "Reset tray",
            use_container_width=True,
        ):
            st.session_state.july_plan = []
            st.session_state.plan_message = (
                "The July Action Tray was reset."
            )
            st.session_state.plan_message_type = "success"
            st.rerun()

    if st.session_state.plan_message:
        if st.session_state.plan_message_type == "error":
            st.error(st.session_state.plan_message)
        elif st.session_state.plan_message_type == "success":
            st.success(st.session_state.plan_message)
        else:
            st.info(st.session_state.plan_message)

    tray_metrics = st.columns(4)

    tray_metrics[0].metric(
        "Budget used",
        money(plan_budget_used()),
    )
    tray_metrics[1].metric(
        "Budget remaining",
        money(MAX_BUDGET - plan_budget_used()),
    )
    tray_metrics[2].metric(
        "Action types",
        f"{len(plan_action_types())} / {MAX_ACTION_TYPES}",
    )
    tray_metrics[3].metric(
        "Saved actions",
        f"{len(st.session_state.july_plan):,}",
    )

    if not st.session_state.july_plan:
        st.info(
            "No spending actions are saved. Preserve Budget remains the valid "
            "$0 reference portfolio."
        )

    else:
        for index, item in enumerate(
            st.session_state.july_plan
        ):
            row_info, row_cost, row_remove = st.columns(
                [2.35, 1, .55]
            )

            with row_info:
                st.write(
                    f"**{item['action']} · {item['target']}**"
                )
                st.caption(
                    f"Base sandbox net: {money(item['base_net'])} · "
                    f"Range: {money(item['low_net'])} to "
                    f"{money(item['high_net'])} · "
                    f"{item['uncertainty']} uncertainty"
                )

            with row_cost:
                st.write(
                    f"**{money(item['total_cost'])}**"
                )
                st.caption(
                    "Catalog + planned downtime"
                )

            with row_remove:
                if st.button(
                    "Remove",
                    key=f"remove-plan-item-{index}",
                ):
                    st.session_state.july_plan.pop(index)
                    st.rerun()

    if st.session_state.july_plan:
        plan_export = pd.DataFrame(
            st.session_state.july_plan
        ).copy()

        if "target_machine_ids" in plan_export.columns:
            plan_export["target_machine_ids"] = (
                plan_export["target_machine_ids"]
                .apply(
                    lambda values: ", ".join(
                        map(str, values)
                    )
                )
            )

        download_csv(
            plan_export,
            "aceiq_july_action_plan.csv",
            "Download July Action Tray CSV",
        )


# =============================================================================
# JULY DEMAND OUTLOOK
# =============================================================================

elif page == "July Demand Outlook":
    section_header(
        "July Demand Outlook",
        "Validate before forecasting.",
        (
            "January–April training · May–June frozen holdout · July planning "
            "scenario."
        ),
    )

    forecast = report.get("forecast", {})

    if not forecast:
        st.error(
            "analysis_results.json does not contain forecast results."
        )
        st.stop()

    forecast_metrics = st.columns(4)

    forecast_metrics[0].metric(
        "Weekday model MAE",
        money(forecast.get("weekday_mae")),
    )
    forecast_metrics[1].metric(
        "Constant baseline MAE",
        money(forecast.get("constant_mae")),
    )
    forecast_metrics[2].metric(
        "Holdout improvement",
        pct(forecast.get("improvement_pct")),
    )
    forecast_metrics[3].metric(
        "July planning baseline",
        money(
            forecast.get(
                "july_refit_baseline_wagers"
            )
        ),
    )

    test_rows = forecast.get("test_rows", [])

    if test_rows:
        validation = pd.DataFrame(test_rows)

        validation["gaming_date"] = pd.to_datetime(
            validation["gaming_date"],
            errors="coerce",
        )

        validation_figure = go.Figure()

        validation_figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["coin_in_usd"],
            mode="markers",
            marker=dict(
                color=GOLD,
                size=7,
                opacity=.8,
            ),
            name="Observed",
        )

        validation_figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["weekday_prediction"],
            mode="lines",
            line=dict(
                color=TEAL,
                width=2.8,
            ),
            name="Weekday model",
        )

        validation_figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["constant_prediction"],
            mode="lines",
            line=dict(
                color=PURPLE,
                width=2,
                dash="dot",
            ),
            name="Constant baseline",
        )

        validation_figure.update_yaxes(
            title="Daily wagers",
            tickprefix="$",
        )

        render_chart(
            validation_figure,
            "Frozen May–June holdout: observed versus prediction",
            "forecast-holdout-chart",
            height=440,
        )

        winner = forecast.get("winner", "weekday")
        improvement = safe_float(
            forecast.get("improvement_pct", 0)
        )

        insight_bubble(
            "Validation takeaway",
            (
                f"The precomputed <strong>{html.escape(str(winner))}</strong> "
                f"model had the lower time-based holdout MAE, improving on the "
                f"constant baseline by <strong>{pct(improvement)}</strong>. "
                "This supports weekday-aware planning. July remains a scenario, "
                "not observed performance."
            ),
        )

    if forecast_metadata:
        st.markdown("### Forecast method and leakage controls")

        metadata_left, metadata_right = st.columns(2)

        with metadata_left:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="eyebrow">Selection and test design</div>
                    <h3>{html.escape(str(forecast_metadata.get("model", "weekday")).title())} model</h3>
                    <div class="subtle">
                        <strong>Selection:</strong>
                        {html.escape(str(forecast_metadata.get("selection", "Not supplied")))}<br><br>
                        <strong>Frozen test:</strong>
                        {html.escape(str(forecast_metadata.get("test", "Not supplied")))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with metadata_right:
            st.markdown(
                f"""
                <div class="panel">
                    <div class="eyebrow">Forecast limitation</div>
                    <h3>July is not observed</h3>
                    <div class="subtle">
                        <strong>Future protocol:</strong>
                        {html.escape(str(forecast_metadata.get("future", "Not supplied")))}<br><br>
                        <strong>Intervals:</strong>
                        {html.escape(str(forecast_metadata.get("interval", "Not supplied")))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Demand context")

    event_associations = pd.DataFrame(
        report.get("event_associations", [])
    )

    traffic_context = pd.DataFrame(
        report.get("traffic", [])
    )

    context_left, context_right = st.columns(2)

    with context_left:
        if not event_associations.empty:
            event_associations["difference_pct"] = pd.to_numeric(
                event_associations["difference_pct"],
                errors="coerce",
            )

            event_associations = event_associations.sort_values(
                "difference_pct",
                ascending=True,
            )

            event_figure = go.Figure()

            event_figure.add_bar(
                x=event_associations["difference_pct"] * 100,
                y=event_associations["event"],
                orientation="h",
                marker_color=GOLD,
                customdata=np.column_stack(
                    [
                        event_associations["days"],
                        event_associations["wagers"],
                        event_associations["weekday_baseline"],
                    ]
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Difference vs weekday baseline: %{x:.1f}%<br>"
                    "Event days: %{customdata[0]:.0f}<br>"
                    "Observed wagers: $%{customdata[1]:,.0f}<br>"
                    "Weekday baseline: $%{customdata[2]:,.0f}"
                    "<extra></extra>"
                ),
                name="Association",
            )

            event_figure.update_xaxes(
                title="Observed difference from weekday baseline",
                ticksuffix="%",
            )

            render_chart(
                event_figure,
                "Event-period demand associations",
                "event-association-chart",
                height=400,
                legend=False,
            )

            insight_bubble(
                "Association, not causation",
                (
                    "Event comparisons use weekday baselines. They show that "
                    "observed demand coincided with certain event periods, but "
                    "they do not prove the event caused the difference."
                ),
                tone="warning",
            )

    with context_right:
        if not traffic_context.empty:
            traffic_context["entries_per_covered_hour"] = pd.to_numeric(
                traffic_context["entries_per_covered_hour"],
                errors="coerce",
            )

            traffic_figure = px.line(
                traffic_context,
                x="month",
                y="entries_per_covered_hour",
                color="zone_id",
                markers=True,
                color_discrete_sequence=[
                    GOLD,
                    TEAL,
                    PURPLE,
                    ORANGE,
                    BLUE,
                    GREEN,
                    RED,
                ],
            )

            traffic_figure.update_yaxes(
                title="Observed entries per covered hour",
            )

            render_chart(
                traffic_figure,
                "Zone traffic context",
                "traffic-context-chart",
                height=400,
            )

            min_coverage = traffic_context[
                "valid_interval_share"
            ].min()

            st.caption(
                f"Traffic counters measure entries, not unique visitors. "
                f"Minimum displayed interval coverage is {pct(min_coverage)}. "
                "Missing coverage is not interpreted as zero traffic."
            )

    if not demand_predictions.empty:
        st.markdown("### Machine-demand model diagnostics")

        phase_options = sorted(
            demand_predictions["phase"]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_phase = st.selectbox(
            "Prediction dataset phase",
            phase_options,
        )

        prediction_subset = demand_predictions[
            demand_predictions["phase"].astype(str)
            == selected_phase
        ].copy()

        prediction_daily = (
            prediction_subset.groupby(
                "gaming_date",
                as_index=False,
            )
            .agg(
                actual=("coin_in_usd", "sum"),
                weekday=("weekday", "sum"),
                constant=("constant", "sum"),
                prediction=("prediction", "sum"),
            )
            .sort_values("gaming_date")
        )

        prediction_figure = go.Figure()

        prediction_figure.add_scatter(
            x=prediction_daily["gaming_date"],
            y=prediction_daily["actual"],
            mode="lines",
            name="Observed",
            line=dict(color=GOLD, width=3),
        )

        prediction_figure.add_scatter(
            x=prediction_daily["gaming_date"],
            y=prediction_daily["prediction"],
            mode="lines",
            name="Chosen machine-level prediction",
            line=dict(color=TEAL, width=2.5),
        )

        prediction_figure.add_scatter(
            x=prediction_daily["gaming_date"],
            y=prediction_daily["constant"],
            mode="lines",
            name="Machine-level constant baseline",
            line=dict(color=PURPLE, width=2, dash="dot"),
        )

        prediction_figure.update_yaxes(
            title="Aggregated machine demand",
            tickprefix="$",
        )

        render_chart(
            prediction_figure,
            "Aggregated machine-demand diagnostics",
            "machine-demand-prediction-chart",
            height=410,
        )

        st.caption(
            "This diagnostic aggregates rows in demand_predictions.parquet. "
            "The report-level holdout MAE remains the official validation metric."
        )


# =============================================================================
# GUEST & LOYALTY INSIGHTS
# =============================================================================

elif page == "Guest & Loyalty Insights":
    section_header(
        "Guest & Loyalty Insights",
        "Tracked-player outcomes and comp economics.",
        (
            "Player tables represent loyalty-card activity only—not all casino "
            "play or all casino guests."
        ),
    )

    st.markdown(
        """
        <div class="warning">
            Do not use gambling-loss behavior to target guests or encourage harmful
            gambling. Any comp test should use a comparison group and focus on
            hospitality, service, redemption value, or guest experience.
        </div>
        """,
        unsafe_allow_html=True,
    )

    selected_months = [
        month
        for month in sorted(
            guests["period_month"]
            .astype(str)
            .unique()
        )
        if (
            start_date.strftime("%Y-%m")
            <= month
            <= end_date.strftime("%Y-%m")
        )
    ]

    guest_period = guests[
        guests["period_month"]
        .astype(str)
        .isin(selected_months)
    ].copy()

    partial_month_selection = (
        start_date.day != 1
        or end_date
        != (
            end_date
            + pd.offsets.MonthEnd(0)
        )
    )

    if partial_month_selection:
        st.markdown(
            """
            <div class="notice">
                <strong>Monthly-data disclosure:</strong> guest_groups.parquet is
                monthly. A partial-month evidence selection includes the full
                included calendar months for tracked-player charts.
            </div>
            """,
            unsafe_allow_html=True,
        )

    player_summary = report.get("players", {})

    if not guest_period.empty:
        guest_metrics = st.columns(6)

        guest_metrics[0].metric(
            "Tracked player-months",
            f"{guest_period['player_months'].sum():,}",
        )
        guest_metrics[1].metric(
            "Tracked wagers",
            money(guest_period["wagers"].sum()),
        )
        guest_metrics[2].metric(
            "Tracked payouts",
            money(guest_period["payouts"].sum()),
        )
        guest_metrics[3].metric(
            "Tracked player net",
            money(guest_period["player_net"].sum()),
        )
        guest_metrics[4].metric(
            "Expected player loss",
            money(guest_period["expected"].sum()),
        )
        guest_metrics[5].metric(
            "Comp cost",
            money(guest_period["comp_cost"].sum()),
        )

        st.caption(
            "Player net is expressed from the tracked player's perspective; "
            "a negative player net is a positive gaming result for the house. "
            "Tracked values should not be used to infer the full property total."
        )

    elif player_summary:
        st.warning(
            "No monthly guest-group rows match the selected evidence period."
        )

    group_options = [
        column
        for column in [
            "home_region",
            "age_band",
            "period_month",
        ]
        if column in guest_period.columns
    ]

    guest_left, guest_right = st.columns([1.05, .95])

    with guest_left:
        if not guest_period.empty and group_options:
            grouping = st.selectbox(
                "Compare tracked groups by",
                group_options,
                format_func=lambda value: (
                    value.replace("_", " ").title()
                ),
            )

            grouped_guests = (
                guest_period.groupby(grouping, as_index=False)
                .agg(
                    wagers=("wagers", "sum"),
                    payouts=("payouts", "sum"),
                    player_net=("player_net", "sum"),
                    expected=("expected", "sum"),
                    comp_cost=("comp_cost", "sum"),
                    player_months=("player_months", "sum"),
                )
                .sort_values("wagers", ascending=True)
            )

            grouped_guests["comp_cost_per_expected"] = (
                grouped_guests["comp_cost"]
                / grouped_guests["expected"].replace(
                    0,
                    np.nan,
                )
            )

            guest_figure = go.Figure()

            guest_figure.add_bar(
                x=grouped_guests["wagers"],
                y=grouped_guests[grouping].astype(str),
                orientation="h",
                marker_color=GOLD,
                customdata=np.column_stack(
                    [
                        grouped_guests["payouts"],
                        grouped_guests["player_net"],
                        grouped_guests["expected"],
                        grouped_guests["comp_cost"],
                        grouped_guests[
                            "comp_cost_per_expected"
                        ],
                    ]
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Tracked wagers: $%{x:,.0f}<br>"
                    "Tracked payouts: $%{customdata[0]:,.0f}<br>"
                    "Tracked player net: $%{customdata[1]:,.0f}<br>"
                    "Expected player loss: $%{customdata[2]:,.0f}<br>"
                    "Comp cost: $%{customdata[3]:,.0f}<br>"
                    "Comp cost / expected loss: %{customdata[4]:.2%}"
                    "<extra></extra>"
                ),
                name="Tracked wagers",
            )

            guest_figure.update_xaxes(
                title="Tracked wagers",
                tickprefix="$",
            )

            render_chart(
                guest_figure,
                "Where is tracked wagering concentrated?",
                "guest-group-wagers-chart",
                height=max(
                    340,
                    min(
                        560,
                        90 + len(grouped_guests) * 42,
                    ),
                ),
                legend=False,
            )

            top_group = grouped_guests.sort_values(
                "wagers",
                ascending=False,
            ).iloc[0]

            top_group_share = (
                top_group["wagers"]
                / grouped_guests["wagers"].sum()
                if grouped_guests["wagers"].sum() > 0
                else np.nan
            )

            insight_bubble(
                "Tracked-play takeaway",
                (
                    f"<strong>{html.escape(str(top_group[grouping]))}</strong> "
                    f"has the largest displayed tracked wager total at "
                    f"<strong>{money(top_group['wagers'])}</strong>, representing "
                    f"<strong>{pct(top_group_share)}</strong> of displayed tracked "
                    "wagers. This is carded play only and is not a guest-targeting "
                    "recommendation."
                ),
            )

            download_csv(
                grouped_guests,
                "aceiq_guest_group_evidence.csv",
                "Download guest-group evidence CSV",
            )

    with guest_right:
        loyalty_rows = pd.DataFrame(
            report.get("loyalty", [])
        )

        if not loyalty_rows.empty:
            loyalty_rows["gaming_month"] = (
                loyalty_rows["gaming_month"].astype(str)
            )

            loyalty_selected = loyalty_rows[
                loyalty_rows["gaming_month"].isin(
                    selected_months
                )
            ].copy()

            if loyalty_selected.empty:
                loyalty_selected = loyalty_rows.copy()

            loyalty_selected["face_value_usd"] = (
                loyalty_selected["face_cents"] / 100
            )
            loyalty_selected["cost_usd"] = (
                loyalty_selected["cost_cents"] / 100
            )
            loyalty_selected["cost_per_face"] = (
                loyalty_selected["cost_usd"]
                / loyalty_selected[
                    "face_value_usd"
                ].replace(0, np.nan)
            )

            loyalty_figure = go.Figure()

            loyalty_figure.add_bar(
                x=loyalty_selected["gaming_month"],
                y=loyalty_selected["cost_usd"],
                name="Comp cost",
                marker_color=GOLD,
            )

            loyalty_figure.add_scatter(
                x=loyalty_selected["gaming_month"],
                y=loyalty_selected["face_value_usd"],
                name="Comp face value",
                mode="lines+markers",
                line=dict(color=TEAL, width=3),
                marker=dict(size=7),
                yaxis="y2",
            )

            loyalty_figure.update_layout(
                yaxis=dict(
                    title="Comp cost",
                    tickprefix="$",
                ),
                yaxis2=dict(
                    title="Comp face value",
                    tickprefix="$",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                ),
            )

            render_chart(
                loyalty_figure,
                "Comp cost versus face value",
                "loyalty-comp-cost-chart",
                height=385,
            )

            latest_loyalty = loyalty_selected.iloc[-1]
            first_loyalty = loyalty_selected.iloc[0]

            change_points_per_face = (
                latest_loyalty[
                    "points_per_face_dollar"
                ]
                / first_loyalty[
                    "points_per_face_dollar"
                ]
                - 1
                if first_loyalty[
                    "points_per_face_dollar"
                ] != 0
                else np.nan
            )

            insight_bubble(
                "Loyalty economics takeaway",
                (
                    f"The latest displayed month has "
                    f"<strong>{latest_loyalty['points_per_face_dollar']:.2f}</strong> "
                    "points per comp face-value dollar. Relative to the first "
                    f"displayed month, that is a change of "
                    f"<strong>{pct(change_points_per_face)}</strong>. "
                    "Comp cost is already part of POS COGS in the challenge "
                    "accounting; do not subtract comp cost and linked POS COGS twice."
                ),
                tone="blue",
            )

    comp_monthly = (
        filtered_property.assign(
            month=filtered_property["gaming_date"]
            .dt.strftime("%Y-%m")
        )
        .groupby("month", as_index=False)
        .agg(
            comp_cost=("comp_cost_usd", "sum"),
            comp_face=("comp_face_value_usd", "sum"),
            theo=("theo_usd", "sum"),
            wagers=("coin_in_usd", "sum"),
        )
    )

    if not comp_monthly.empty:
        comp_monthly["comp_cost_per_theo"] = (
            comp_monthly["comp_cost"]
            / comp_monthly["theo"].replace(
                0,
                np.nan,
            )
        )
        comp_monthly["comp_cost_per_wager"] = (
            comp_monthly["comp_cost"]
            / comp_monthly["wagers"].replace(
                0,
                np.nan,
            )
        )

        comp_ratio_figure = go.Figure()

        comp_ratio_figure.add_scatter(
            x=comp_monthly["month"],
            y=comp_monthly["comp_cost_per_theo"],
            mode="lines+markers",
            line=dict(color=PURPLE, width=3),
            marker=dict(size=8),
            name="Comp cost / theo",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Comp cost / theo: %{y:.2%}"
                "<extra></extra>"
            ),
        )

        comp_ratio_figure.update_yaxes(
            title="Comp cost as share of theoretical earnings",
            tickformat=".2%",
        )

        render_chart(
            comp_ratio_figure,
            "How did comp economics change?",
            "comp-cost-ratio-chart",
            height=325,
            legend=False,
        )


# =============================================================================
# METHODS & EVIDENCE
# =============================================================================

else:
    section_header(
        "Methods & Evidence",
        "Trace recommendations back to evidence and limitations.",
        (
            "All calculations use local synthetic files or visibly labeled "
            "challenge planning assumptions."
        ),
    )

    (
        machine_tab,
        downtime_tab,
        simulation_tab,
        quality_tab,
        claims_tab,
        download_tab,
    ) = st.tabs(
        [
            "Machine Method",
            "Downtime",
            "Official Simulation",
            "Data Quality",
            "Claims Appendix",
            "Downloads",
        ]
    )

    with machine_tab:
        st.markdown(
            """
            <div class="warning">
                <strong>Actual earnings</strong> = coin-in − payouts.<br>
                <strong>Theoretical earnings</strong> = coin-in × (1 − configured RTP).<br>
                <strong>Actual − expected</strong> = actual earnings − theoretical earnings.<br><br>
                Exposure-adjusted comparisons use active days and available hours.
                Variance context uses supplied daily variance estimates aggregated
                by machine. A payout gap is an inspection lead—not proof of
                malfunction, fraud, tampering, cheating, or wrongdoing.
            </div>
            """,
            unsafe_allow_html=True,
        )

        method_columns = [
            "machine_id",
            "manufacturer",
            "theme",
            "install_date",
            "retire_date",
            "eligible_july",
            "active_days",
            "availability_rate",
            "actual_house_win",
            "expected_house_win",
            "actual_minus_expected",
            "actual_to_expected",
            "expected_per_available_hour",
            "actual_per_available_hour",
            "payout_sd_selected",
            "standardized_gap_selected",
            "standardized_gap",
            "classification",
        ]

        method_columns = [
            column
            for column in method_columns
            if column in machine_summary.columns
        ]

        st.dataframe(
            machine_summary[
                method_columns
            ].sort_values(
                "actual_house_win"
            ),
            use_container_width=True,
            hide_index=True,
        )

    with downtime_tab:
        downtime_metrics = st.columns(4)

        downtime_metrics[0].metric(
            "Downtime hours",
            f"{filtered_daily['down_hours'].sum():,.1f}",
        )
        downtime_metrics[1].metric(
            "Low opportunity",
            money(
                filtered_daily[
                    "missed_wagers_low"
                ].sum()
            ),
        )
        downtime_metrics[2].metric(
            "Midpoint wager opportunity",
            money(
                filtered_daily[
                    "missed_wagers_mid"
                ].sum()
            ),
        )
        downtime_metrics[3].metric(
            "Midpoint theo opportunity",
            money(
                filtered_daily[
                    "missed_theo_mid"
                ].sum()
            ),
        )

        downtime_daily = (
            filtered_daily.groupby(
                "gaming_date",
                as_index=False,
            )
            .agg(
                downtime_hours=("down_hours", "sum"),
                midpoint_theo=(
                    "missed_theo_mid",
                    "sum",
                ),
            )
            .sort_values("gaming_date")
        )

        downtime_left, downtime_right = st.columns(2)

        with downtime_left:
            downtime_time_figure = go.Figure()

            downtime_time_figure.add_bar(
                x=downtime_daily["gaming_date"],
                y=downtime_daily["downtime_hours"],
                marker_color=ORANGE,
                name="Downtime hours",
            )

            downtime_time_figure.update_yaxes(
                title="Downtime hours",
            )

            render_chart(
                downtime_time_figure,
                "When did downtime occur?",
                "downtime-time-chart",
                height=360,
                legend=False,
            )

        with downtime_right:
            zone_downtime = zone_summary.sort_values(
                "downtime_opportunity",
                ascending=True,
            )

            zone_downtime_figure = go.Figure()

            zone_downtime_figure.add_bar(
                x=zone_downtime[
                    "downtime_opportunity"
                ],
                y=zone_downtime["zone_name"],
                orientation="h",
                marker_color=ORANGE,
                customdata=np.column_stack(
                    [
                        zone_downtime["downtime_hours"],
                        zone_downtime["availability_rate"],
                        zone_downtime["missed_wagers"],
                    ]
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Theo opportunity: $%{x:,.0f}<br>"
                    "Downtime hours: %{customdata[0]:,.1f}<br>"
                    "Availability: %{customdata[1]:.1%}<br>"
                    "Midpoint wager opportunity: $%{customdata[2]:,.0f}"
                    "<extra></extra>"
                ),
            )

            zone_downtime_figure.update_xaxes(
                title="Estimated theoretical-earnings opportunity",
                tickprefix="$",
            )

            render_chart(
                zone_downtime_figure,
                "Where was downtime opportunity concentrated?",
                "downtime-zone-chart",
                height=360,
                legend=False,
            )

        downtime_report = report.get("downtime", {})

        if downtime_report:
            insight_bubble(
                "Downtime method",
                (
                    f"The full-period report estimates "
                    f"<strong>{money(downtime_report.get('missed_wagers_low'))}</strong> "
                    f"to <strong>{money(downtime_report.get('missed_wagers_high'))}</strong> "
                    "of missed wagering opportunity, with midpoint "
                    f"<strong>{money(downtime_report.get('missed_wagers_mid'))}</strong>. "
                    f"{html.escape(str(downtime_report.get('method', '')))}"
                ),
                tone="warning",
            )

    with simulation_tab:
        simulation = official["simulation"]
        recommendation = official["recommended"]
        portfolios = pd.DataFrame(
            simulation.get("portfolios", [])
        )

        heading = (
            "Preserve Budget ranks first under the official 30-day assumptions."
            if official["keep_budget"]
            else "Review the official recommended portfolio."
        )

        st.markdown(
            f"""
            <div class="hero">
                <div class="eyebrow" style="color:{TEAL};">
                    Official precomputed result
                </div>
                <h2>{html.escape(heading)}</h2>
                <div class="subtle">
                    Portfolio results are precomputed from local challenge data.
                    Effect probabilities remain conditional on model assumptions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        simulation_metrics = st.columns(5)

        simulation_metrics[0].metric(
            "Simulation scenarios",
            f"{simulation.get('scenarios', 0):,}",
        )
        simulation_metrics[1].metric(
            "Candidate actions",
            f"{simulation.get('candidate_count', 0):,}",
        )
        simulation_metrics[2].metric(
            "Feasible portfolios",
            f"{simulation.get('feasible_portfolios', 0):,}",
        )
        simulation_metrics[3].metric(
            "Recommended spend",
            money(recommendation.get("cost")),
        )
        simulation_metrics[4].metric(
            "Expected modeled net",
            money(recommendation.get("mean_net")),
        )

        if not portfolios.empty:
            portfolios["actions_label"] = portfolios["actions"].apply(
                lambda actions: (
                    "Preserve Budget"
                    if not actions
                    else " + ".join(actions)
                )
            )

            top_portfolios = portfolios.nlargest(
                min(12, len(portfolios)),
                "mean_net",
            ).sort_values(
                "mean_net",
                ascending=True,
            )

            portfolio_figure = go.Figure()

            portfolio_figure.add_bar(
                x=top_portfolios["mean_net"],
                y=top_portfolios["actions_label"],
                orientation="h",
                marker_color=[
                    TEAL
                    if value == 0
                    else (
                        GREEN
                        if value > 0
                        else ORANGE
                    )
                    for value in top_portfolios["mean_net"]
                ],
                customdata=np.column_stack(
                    [
                        top_portfolios["cost"],
                        top_portfolios["median_net"],
                        top_portfolios["p10"],
                        top_portfolios["p90"],
                        top_portfolios[
                            "probability_positive"
                        ],
                    ]
                ),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Mean net: $%{x:,.0f}<br>"
                    "Cost: $%{customdata[0]:,.0f}<br>"
                    "Median: $%{customdata[1]:,.0f}<br>"
                    "P10: $%{customdata[2]:,.0f}<br>"
                    "P90: $%{customdata[3]:,.0f}<br>"
                    "Probability positive: %{customdata[4]:.1%}"
                    "<extra></extra>"
                ),
                name="Mean modeled net",
            )

            portfolio_figure.add_vline(
                x=0,
                line_dash="dash",
                line_color=TEAL,
            )

            portfolio_figure.update_xaxes(
                title="Expected 30-day incremental contribution",
                tickprefix="$",
            )

            render_chart(
                portfolio_figure,
                "Official portfolio comparison",
                "official-portfolio-chart",
                height=460,
                legend=False,
            )

            display_portfolios = portfolios[
                [
                    "actions_label",
                    "cost",
                    "mean_net",
                    "median_net",
                    "p10",
                    "p90",
                    "probability_positive",
                    "conservative_net",
                ]
            ].sort_values(
                "mean_net",
                ascending=False,
            )

            with st.expander(
                "Open official portfolio scenarios"
            ):
                st.dataframe(
                    display_portfolios,
                    use_container_width=True,
                    hide_index=True,
                )

        if (
            isinstance(scenario_samples, np.ndarray)
            and scenario_samples.ndim == 2
            and scenario_samples.size > 0
        ):
            sample_summary = pd.DataFrame(
                {
                    "sample_row": np.arange(
                        scenario_samples.shape[0]
                    ),
                    "mean_net": scenario_samples.mean(axis=1),
                    "median_net": np.median(
                        scenario_samples,
                        axis=1,
                    ),
                    "p10": np.quantile(
                        scenario_samples,
                        .10,
                        axis=1,
                    ),
                    "p90": np.quantile(
                        scenario_samples,
                        .90,
                        axis=1,
                    ),
                    "probability_positive": (
                        scenario_samples > 0
                    ).mean(axis=1),
                }
            )

            sample_figure = go.Figure()

            for row_index in range(
                scenario_samples.shape[0]
            ):
                sample_figure.add_violin(
                    y=scenario_samples[row_index],
                    name=f"Sample row {row_index + 1}",
                    box_visible=True,
                    meanline_visible=True,
                    points=False,
                )

            sample_figure.add_hline(
                y=0,
                line_dash="dash",
                line_color=TEAL,
            )

            sample_figure.update_yaxes(
                title="Scenario-net outcome",
                tickprefix="$",
            )

            render_chart(
                sample_figure,
                "Precomputed scenario-net sample distributions",
                "scenario-net-samples-chart",
                height=430,
            )

            st.markdown(
                """
                <div class="notice">
                    <strong>Sample provenance disclosure:</strong>
                    scenario_net.npz contains 9 × 1,000 numerical sample outcomes,
                    while the JSON report contains 42 feasible portfolio rows.
                    No explicit file mapping identifies which sample row belongs to
                    which portfolio. The distributions are therefore shown as
                    unlabeled precomputed sample rows and are not falsely assigned
                    to named portfolios.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander(
                "Open scenario-net sample summary"
            ):
                st.dataframe(
                    sample_summary,
                    use_container_width=True,
                    hide_index=True,
                )

        limitations = simulation.get("limitations", [])

        if limitations:
            st.markdown("### Official model limitations")

            for limitation in limitations:
                st.write(f"• {limitation}")

    with quality_tab:
        st.markdown(
            """
            <div class="notice">
                These checks flag structural issues and unusual conditions. They do
                not automatically delete records because negative daily house win,
                large residuals, and low exposure can be real features of gaming
                data rather than data errors.
            </div>
            """,
            unsafe_allow_html=True,
        )

        quality_counts = quality_checks[
            "status"
        ].value_counts()

        quality_metrics = st.columns(3)

        quality_metrics[0].metric(
            "Passed checks",
            f"{quality_counts.get('PASS', 0):,}",
        )
        quality_metrics[1].metric(
            "Review flags",
            f"{quality_counts.get('REVIEW', 0):,}",
        )
        quality_metrics[2].metric(
            "Information flags",
            f"{quality_counts.get('INFO', 0):,}",
        )

        for row in quality_checks.itertuples():
            status_class = {
                "PASS": "quality-pass",
                "REVIEW": "quality-warn",
                "INFO": "quality-warn",
                "FAIL": "quality-fail",
            }.get(row.status, "quality-warn")

            st.markdown(
                f"""
                <div class="quality-row">
                    <span class="{status_class}">{html.escape(str(row.status))}</span>
                    · <strong>{html.escape(str(row.check))}</strong><br>
                    {html.escape(str(row.detail))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        download_csv(
            quality_checks,
            "aceiq_data_quality_checks.csv",
            "Download data-quality checks CSV",
        )

    with claims_tab:
        # One shared source for the visible table and downloadable evidence CSV.
        claims = pd.read_csv(ROOT / "docs" / "CLAIMS_AND_EVIDENCE.csv")

        st.dataframe(
            claims,
            use_container_width=True,
            hide_index=True,
        )

        download_csv(
            claims,
            "aceiq_claims_and_evidence.csv",
            "Download claims appendix CSV",
        )

    with download_tab:
        download_csv(
            machine_summary,
            "aceiq_machine_evidence.csv",
            "Download machine evidence CSV",
        )

        download_csv(
            zone_summary,
            "aceiq_zone_evidence.csv",
            "Download zone evidence CSV",
        )

        download_csv(
            bank_summary,
            "aceiq_bank_evidence.csv",
            "Download bank evidence CSV",
        )

        if not catalog.empty:
            download_csv(
                catalog,
                "aceiq_action_catalog.csv",
                "Download action catalog CSV",
            )

        if not floor_locations.empty:
            download_csv(
                floor_locations,
                "aceiq_floor_locations.csv",
                "Download floor locations CSV",
            )

        if not placements.empty:
            download_csv(
                placements,
                "aceiq_placements.csv",
                "Download placement evidence CSV",
            )

        st.markdown(
            """
            <div class="notice">
                <strong>Local-data disclosure:</strong> all displayed numerical
                results come from local synthetic Parquet, JSON, and NPZ files,
                or from visibly labeled July planning assumptions. No external API,
                internet request, or generative model is used at runtime.
            </div>
            """,
            unsafe_allow_html=True,
        )


# =============================================================================
# FOOTER
# =============================================================================

st.markdown(
    """
    <div class="footer">
        ACEIQ · THE GILDED ACE · Synthetic Dashboard Royale data only ·
        Descriptive and modeled results do not prove causality.
    </div>
    """,
    unsafe_allow_html=True,
)