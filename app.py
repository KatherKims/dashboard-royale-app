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
"""

from __future__ import annotations

from pathlib import Path
import html
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


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


st.set_page_config(
    page_title="AceIQ | Gilded Ace Decision Intelligence",
    page_icon="♠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =============================================================================
# VISUAL STYLE
# =============================================================================

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
            background: linear-gradient(145deg, rgba(28,40,52,.98), rgba(16,25,33,.98));
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
            background: linear-gradient(135deg, rgba(22,69,70,.48), rgba(19,29,38,.90));
        }}

        .insight.warning {{
            border-left-color: var(--orange);
            background: linear-gradient(135deg, rgba(89,54,26,.44), rgba(25,29,34,.92));
        }}

        .insight.purple {{
            border-left-color: var(--purple);
            background: linear-gradient(135deg, rgba(61,39,98,.42), rgba(24,27,37,.92));
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
            background: linear-gradient(145deg, rgba(27,39,50,.98), rgba(15,24,32,.98));
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


# =============================================================================
# DISPLAY HELPERS
# =============================================================================

def money(value, decimals=0):
    if value is None or pd.isna(value):
        return "—"

    value = float(value)
    result = f"${abs(value):,.{decimals}f}"
    return f"-{result}" if value < 0 else result


def pct(value, decimals=1):
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.{decimals}%}"


def section_header(kicker, title, subtitle=""):
    st.markdown(
        f'<div class="eyebrow">{html.escape(kicker)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {title}")

    if subtitle:
        st.markdown(
            f'<div class="subtle">{html.escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def insight_bubble(label, message, tone="normal"):
    tone_class = ""

    if tone in {"warning", "purple"}:
        tone_class = f" {tone}"

    st.markdown(
        f"""
        <div class="insight{tone_class}">
            <div class="insight-label">
                {html.escape(label)}
            </div>
            {message}
        </div>
        """,
        unsafe_allow_html=True,
    )


def download_csv(df, filename, label):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def render_chart(fig, title, key, height=380):
    fig.update_layout(
        title=dict(
            text=title,
            x=0,
            xanchor="left",
            font=dict(
                color=WHITE,
                size=16,
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(
            color=WHITE,
            size=11,
        ),
        margin=dict(
            l=38,
            r=20,
            t=58,
            b=42,
        ),
        height=height,
        bargap=.28,
        bargroupgap=.08,
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

    fig.update_xaxes(
        gridcolor=GRID,
        zerolinecolor="#485661",
        tickfont=dict(size=10),
        automargin=True,
    )

    fig.update_yaxes(
        gridcolor=GRID,
        zerolinecolor="#485661",
        tickfont=dict(size=10),
        automargin=True,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        config={
            "displayModeBar": False,
            "responsive": True,
        },
    )


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data(show_spinner="Loading AceIQ data...")
def load_data():
    required = [
        DATA_DIR / "analysis_results.json",
        DATA_DIR / "machines.parquet",
        DATA_DIR / "machine_daily.parquet",
        DATA_DIR / "guest_groups.parquet",
        DATA_DIR / "property_daily.parquet",
        DATA_DIR / "scenario_net.npz",
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Missing required local data files:\n\n"
            + "\n".join(missing)
            + f"\n\nExpected location:\n{DATA_DIR}"
        )

    report = json.loads(
        (
            DATA_DIR / "analysis_results.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    machines = pd.read_parquet(
        DATA_DIR / "machines.parquet"
    )

    daily = pd.read_parquet(
        DATA_DIR / "machine_daily.parquet"
    )

    guests = pd.read_parquet(
        DATA_DIR / "guest_groups.parquet"
    )

    property_daily = pd.read_parquet(
        DATA_DIR / "property_daily.parquet"
    )

    scenario_samples = np.load(
        DATA_DIR / "scenario_net.npz"
    )["net"]

    daily["gaming_date"] = pd.to_datetime(
        daily["gaming_date"],
        errors="coerce",
    )

    property_daily["gaming_date"] = pd.to_datetime(
        property_daily["gaming_date"],
        errors="coerce",
    )

    machines["machine_id"] = machines[
        "machine_id"
    ].astype(str)

    daily["machine_id"] = daily[
        "machine_id"
    ].astype(str)

    guests["period_month"] = guests[
        "period_month"
    ].astype(str)

    return (
        report,
        machines,
        daily,
        guests,
        property_daily,
        scenario_samples,
    )


# =============================================================================
# ANALYTICS
# =============================================================================

def active_rows(data):
    """
    Use actual floor exposure for machine-level comparisons.

    machine_daily.parquet contains 55,092 active rows and 56,110 total rows.
    Rows with no available hours are excluded from machine rankings.
    """

    result = data.copy()

    if "available_hours" in result.columns:
        result = result[
            result["available_hours"].fillna(0) > 0
        ].copy()

    return result


def build_machine_summary(filtered_daily, machines):
    daily_active = active_rows(filtered_daily)

    summary = (
        daily_active.groupby(
            "machine_id",
            as_index=False,
        )
        .agg(
            actual_house_win=(
                "house_win_usd",
                "sum",
            ),
            expected_house_win=(
                "theo_usd",
                "sum",
            ),
            total_wagers=(
                "coin_in_usd",
                "sum",
            ),
            available_hours=(
                "available_hours",
                "sum",
            ),
            scheduled_hours=(
                "scheduled_hours",
                "sum",
            ),
            downtime_hours=(
                "down_hours",
                "sum",
            ),
            estimated_downtime_opportunity=(
                "missed_theo_mid",
                "sum",
            ),
            active_days=(
                "gaming_date",
                "nunique",
            ),
        )
    )

    summary["availability_rate"] = (
        summary["available_hours"]
        / summary["scheduled_hours"].replace(
            0,
            np.nan,
        )
    )

    summary["actual_per_active_day"] = (
        summary["actual_house_win"]
        / summary["active_days"].replace(
            0,
            np.nan,
        )
    )

    summary["expected_per_available_hour"] = (
        summary["expected_house_win"]
        / summary["available_hours"].replace(
            0,
            np.nan,
        )
    )

    summary["actual_per_available_hour"] = (
        summary["actual_house_win"]
        / summary["available_hours"].replace(
            0,
            np.nan,
        )
    )

    summary["actual_minus_expected"] = (
        summary["actual_house_win"]
        - summary["expected_house_win"]
    )

    metadata_columns = [
        "machine_id",
        "manufacturer",
        "theme",
        "install_date",
        "retire_date",
        "lease_class",
        "eligible_july",
        "standardized_gap",
        "peer_ratio",
        "payout_sd",
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

    if "standardized_gap" not in summary.columns:
        summary["standardized_gap"] = np.nan

    return summary


def add_location_context(summary, filtered_daily):
    daily_active = active_rows(filtered_daily)

    locations = (
        daily_active.groupby(
            [
                "machine_id",
                "zone_name",
                "bank_id",
            ],
            as_index=False,
        )
        .agg(
            available_hours=("available_hours", "sum")
        )
        .sort_values(
            [
                "machine_id",
                "available_hours",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop_duplicates(
            "machine_id"
        )
    )

    return summary.merge(
        locations[
            [
                "machine_id",
                "zone_name",
                "bank_id",
            ]
        ],
        on="machine_id",
        how="left",
    )


def build_zone_summary(filtered_daily):
    daily_active = active_rows(filtered_daily)

    zones = (
        daily_active.groupby(
            "zone_name",
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
            machine_count=("machine_id", "nunique"),
        )
    )

    zones["wagers_per_available_hour"] = (
        zones["wagers"]
        / zones["available_hours"].replace(
            0,
            np.nan,
        )
    )

    zones["availability_rate"] = (
        zones["available_hours"]
        / zones["scheduled_hours"].replace(
            0,
            np.nan,
        )
    )

    zones["actual_minus_expected"] = (
        zones["actual"]
        - zones["expected"]
    )

    return zones


def build_bank_summary(filtered_daily):
    daily_active = active_rows(filtered_daily)

    banks = (
        daily_active.groupby(
            [
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
            scheduled_hours=("scheduled_hours", "sum"),
            downtime_hours=("down_hours", "sum"),
            downtime_opportunity=("missed_theo_mid", "sum"),
            machine_count=("machine_id", "nunique"),
        )
    )

    banks["wagers_per_available_hour"] = (
        banks["wagers"]
        / banks["available_hours"].replace(
            0,
            np.nan,
        )
    )

    banks["availability_rate"] = (
        banks["available_hours"]
        / banks["scheduled_hours"].replace(
            0,
            np.nan,
        )
    )

    banks["actual_minus_expected"] = (
        banks["actual"]
        - banks["expected"]
    )

    return banks


def machine_category(row):
    if not bool(
        row.get(
            "eligible_july",
            False,
        )
    ):
        return "Not a July action target"

    standardized_gap = row.get(
        "standardized_gap",
        np.nan,
    )

    availability = row.get(
        "availability_rate",
        np.nan,
    )

    actual_gap = row.get(
        "actual_minus_expected",
        np.nan,
    )

    downtime_opportunity = row.get(
        "estimated_downtime_opportunity",
        0,
    )

    expected = row.get(
        "expected_house_win",
        0,
    )

    if (
        pd.notna(standardized_gap)
        and standardized_gap <= -3
    ):
        return "Inspection candidate"

    if (
        pd.notna(availability)
        and availability < .90
    ):
        return "Maintenance candidate"

    if (
        expected > 0
        and downtime_opportunity > expected * .10
    ):
        return "Maintenance candidate"

    if (
        pd.notna(actual_gap)
        and actual_gap < 0
    ):
        return "Monitor payout variance"

    return "Monitor"


def recommendation_for_machine(row):
    category = machine_category(row)

    if category == "Not a July action target":
        return (
            "No July action",
            "This machine is not eligible for a July action.",
            GRAY,
        )

    if category == "Inspection candidate":
        return (
            "Inspect configuration and meters first",
            "The actual-versus-expected gap is unusual. Review configuration, game math, and meter history before relocation or replacement.",
            PURPLE,
        )

    if category == "Maintenance candidate":
        return (
            "Address availability before replacement",
            "Low availability or downtime opportunity may mean the machine did not receive a fair chance to earn.",
            ORANGE,
        )

    if category == "Monitor payout variance":
        return (
            "Monitor against exposure-adjusted peers",
            "The machine is below expected, but payout variation remains plausible.",
            GOLD,
        )

    return (
        "Monitor before spending",
        "Current evidence does not establish that relocation or replacement would outperform preserving budget.",
        GREEN,
    )


# =============================================================================
# ACTION SANDBOX
# =============================================================================

def sandbox_result(
    machine,
    zone_summary,
    action,
    destination_zone,
    retained_play,
    maintenance_recovery,
    lease_uplift,
):
    expected_hour = float(
        machine.get(
            "expected_per_available_hour",
            0,
        )
        or 0
    )

    availability = float(
        machine.get(
            "availability_rate",
            .90,
        )
        or .90
    )

    availability = min(
        max(availability, 0.0),
        1.0,
    )

    downtime_opportunity = float(
        machine.get(
            "estimated_downtime_opportunity",
            0,
        )
        or 0
    )

    origin_zone = str(
        machine.get(
            "zone_name",
            "Unknown",
        )
    )

    if zone_summary.empty:
        origin_rate = 1.0
        destination_rate = 1.0
    else:
        rates = zone_summary.set_index(
            "zone_name"
        )["wagers_per_available_hour"]

        median_rate = rates.median()

        if pd.isna(median_rate) or median_rate <= 0:
            median_rate = 1.0

        origin_rate = rates.get(
            origin_zone,
            median_rate,
        )

        destination_rate = rates.get(
            destination_zone,
            median_rate,
        )

        if pd.isna(origin_rate) or origin_rate <= 0:
            origin_rate = median_rate

        if pd.isna(destination_rate) or destination_rate <= 0:
            destination_rate = median_rate

    zone_factor = destination_rate / origin_rate

    baseline = (
        expected_hour
        * availability
        * 24
        * 30
    )

    action_cost = 0.0
    downtime_cost = 0.0
    low = 0.0
    base = 0.0
    high = 0.0

    assumptions = ""
    limitation = ""
    measurement = ""

    if action == "Keep Budget":
        assumptions = (
            "No spending action. The $0 baseline is retained."
        )

        limitation = (
            "This is a financial baseline, not proof that future interventions are never worthwhile."
        )

        measurement = (
            "Continue monitoring availability, expected earnings per available hour, and actual-versus-expected results."
        )

    elif action == "Inspect":
        action_cost = 1_200
        downtime_cost = 2 * expected_hour

        low = -(action_cost + downtime_cost)
        base = low
        high = low

        assumptions = (
            "Inspection receives no unverified corrective cash benefit in the 30-day sandbox."
        )

        limitation = (
            "Information value is not monetized. Inspection may improve a later decision."
        )

        measurement = (
            "Reconcile configured RTP, game math, meter history, and repair records."
        )

    elif action == "Move":
        action_cost = 1_800
        downtime_cost = 3 * expected_hour

        uplift = zone_factor - 1
        low_retained = max(
            .10,
            retained_play - .25,
        )

        high_retained = min(
            1.00,
            retained_play + .25,
        )

        low = (
            baseline
            * uplift
            * low_retained
            - action_cost
            - downtime_cost
        )

        base = (
            baseline
            * uplift
            * retained_play
            - action_cost
            - downtime_cost
        )

        high = (
            baseline
            * uplift
            * high_retained
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"Observed destination/origin demand factor: {zone_factor:.2f}×. "
            f"Retained incremental play: {retained_play:.0%}."
        )

        limitation = (
            "Zone differences are observational, not causal proof. Some play may shift from nearby machines."
        )

        measurement = (
            "Compare expected earnings per available hour with a predefined untreated machine or bank."
        )

    elif action == "Maintain":
        action_cost = 9_000
        downtime_cost = 1.5 * expected_hour

        july_opportunity = (
            downtime_opportunity
            / 181
            * 23
        )

        low_recovery = max(
            .05,
            maintenance_recovery - .20,
        )

        high_recovery = min(
            .95,
            maintenance_recovery + .25,
        )

        low = (
            july_opportunity
            * low_recovery
            * retained_play
            - action_cost
            - downtime_cost
        )

        base = (
            july_opportunity
            * maintenance_recovery
            * retained_play
            - action_cost
            - downtime_cost
        )

        high = (
            july_opportunity
            * high_recovery
            * retained_play
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"Downtime recovery: {maintenance_recovery:.0%}; "
            f"retained incremental play: {retained_play:.0%}."
        )

        limitation = (
            "Recovered opportunity is not guaranteed new revenue because guests may have played elsewhere."
        )

        measurement = (
            "Compare unavailable hours, repeat faults, repair turnaround, and earnings against untreated peers."
        )

    else:
        action_cost = 3_380
        downtime_cost = 6 * expected_hour

        low_uplift = -.10
        high_uplift = min(
            2.0,
            lease_uplift + .65,
        )

        low = (
            baseline
            * (16 / 30)
            * low_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )

        base = (
            baseline
            * (16 / 30)
            * lease_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )

        high = (
            baseline
            * (16 / 30)
            * high_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"New-title uplift: {lease_uplift:.0%}; "
            "16 usable July days after lead time."
        )

        limitation = (
            "New-title uplift is a planning assumption, not causal evidence."
        )

        measurement = (
            "Compare replacement performance with matched unchanged machines and monitor displacement."
        )

    spread = high - low

    if spread > 6_000:
        uncertainty = "High"
    elif spread > 2_000:
        uncertainty = "Medium"
    else:
        uncertainty = "Lower"

    if action == "Inspect":
        signal = "Learning action"
    elif base > 0 and low >= 0:
        signal = "Favorable under sandbox assumptions"
    elif base > 0:
        signal = "Potential upside with meaningful uncertainty"
    else:
        signal = "Weak under sandbox assumptions"

    return {
        "action_cost": action_cost,
        "downtime_cost": downtime_cost,
        "low": low,
        "base": base,
        "high": high,
        "uncertainty": uncertainty,
        "signal": signal,
        "origin_zone": origin_zone,
        "destination_zone": destination_zone,
        "zone_factor": zone_factor,
        "assumptions": assumptions,
        "limitation": limitation,
        "measurement": measurement,
    }


# =============================================================================
# SESSION STATE
# =============================================================================

def initialize_state():
    defaults = {
        "selected_machine_id": None,
        "selected_action": "Keep Budget",
        "destination_zone": None,
        "retained_play": .50,
        "maintenance_recovery": .50,
        "lease_uplift": .50,
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


def plan_budget_used():
    return float(
        sum(
            item["total_cost"]
            for item in st.session_state.july_plan
        )
    )


def plan_action_types():
    return set(
        item["action_type"]
        for item in st.session_state.july_plan
    )


def action_type_key(action):
    return {
        "Keep Budget": "keep",
        "Inspect": "inspect",
        "Move": "move",
        "Maintain": "maintain",
        "Lease / Replace": "lease",
    }[action]


def add_to_plan(machine, action, result):
    if action == "Keep Budget":
        st.session_state.plan_message = (
            "Keep Budget is the $0 baseline and does not need to be added to the spending tray."
        )
        st.session_state.plan_message_type = "info"
        return

    if not bool(
        machine.get(
            "eligible_july",
            False,
        )
    ):
        st.session_state.plan_message = (
            "This machine is not eligible for a July action."
        )
        st.session_state.plan_message_type = "error"
        return

    if (
        action == "Move"
        and result["origin_zone"]
        == result["destination_zone"]
    ):
        st.session_state.plan_message = (
            "Choose a destination zone different from the current zone."
        )
        st.session_state.plan_message_type = "error"
        return

    machine_id = str(
        machine["machine_id"]
    )

    if any(
        str(item["machine_id"]) == machine_id
        for item in st.session_state.july_plan
    ):
        st.session_state.plan_message = (
            f"{machine_id} already has an action in the July plan."
        )
        st.session_state.plan_message_type = "error"
        return

    current_type = action_type_key(action)

    if (
        current_type not in plan_action_types()
        and len(plan_action_types()) >= MAX_ACTION_TYPES
    ):
        st.session_state.plan_message = (
            "The July plan allows at most three action types."
        )
        st.session_state.plan_message_type = "error"
        return

    total_cost = (
        result["action_cost"]
        + result["downtime_cost"]
    )

    if plan_budget_used() + total_cost > MAX_BUDGET:
        st.session_state.plan_message = (
            "Adding this action would exceed the $100,000 July budget."
        )
        st.session_state.plan_message_type = "error"
        return

    st.session_state.july_plan.append(
        {
            "machine_id": machine_id,
            "action": action,
            "action_type": current_type,
            "origin_zone": result["origin_zone"],
            "destination_zone": result["destination_zone"],
            "action_cost": result["action_cost"],
            "downtime_cost": result["downtime_cost"],
            "total_cost": total_cost,
            "base_net": result["base"],
            "uncertainty": result["uncertainty"],
        }
    )

    st.session_state.plan_message = (
        f"{action} for {machine_id} was added to the July Action Tray."
    )
    st.session_state.plan_message_type = "success"


# =============================================================================
# LOAD DATA
# =============================================================================

try:
    (
        report,
        machines,
        daily,
        guests,
        property_daily,
        scenario_samples,
    ) = load_data()

except Exception as error:
    st.error(
        "AceIQ could not load its required local data files."
    )
    st.code(str(error))
    st.stop()

initialize_state()

min_date = daily["gaming_date"].min().date()
max_date = daily["gaming_date"].max().date()


# =============================================================================
# HEADER AND NAVIGATION
# =============================================================================

st.markdown(
    """
    <div class="topbar">
        <div>
            <div class="brand">♠ ACEIQ</div>
            <div class="brand-sub">
                The Gilded Ace · Decision Intelligence
            </div>
        </div>
        <div class="top-note">
            Fictional casino · Synthetic data<br>
            July planning horizon: 30 days
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_col, date_col, note_col = st.columns(
    [1.9, 1.35, 2.0]
)

with nav_col:
    page = st.radio(
        "Navigation",
        [
            "Decision Center",
            "Investigate",
            "July Demand Outlook",
            "Guest & Loyalty Insights",
            "Methods & Evidence",
        ],
        horizontal=True,
        label_visibility="collapsed",
    )

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
    st.session_state.july_plan = []
    st.session_state.claw_machine_id = None
    st.session_state.plan_message = (
        "Evidence period changed. The July Action Tray was reset."
    )
    st.session_state.plan_message_type = "info"

with note_col:
    st.markdown(
        f"""
        <div style="padding-top:1.65rem;color:#D4DEE3;font-size:.76rem;">
            <strong>Active period:</strong>
            {start_date.strftime("%b %d, %Y")} –
            {end_date.strftime("%b %d, %Y")}<br>
            All dashboard calculations use the local synthetic data files.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# FILTER DATA
# =============================================================================

filtered_daily = daily[
    (
        daily["gaming_date"]
        >= start_date
    )
    & (
        daily["gaming_date"]
        <= end_date
    )
].copy()

filtered_property = property_daily[
    (
        property_daily["gaming_date"]
        >= start_date
    )
    & (
        property_daily["gaming_date"]
        <= end_date
    )
].copy()

if filtered_daily.empty:
    st.error(
        "No machine data exists for the selected evidence period."
    )
    st.stop()

machine_summary = build_machine_summary(
    filtered_daily,
    machines,
)

machine_summary = add_location_context(
    machine_summary,
    filtered_daily,
)

machine_summary["classification"] = machine_summary.apply(
    machine_category,
    axis=1,
)

zone_summary = build_zone_summary(
    filtered_daily
)

bank_summary = build_bank_summary(
    filtered_daily
)

machine_ids = sorted(
    machine_summary["machine_id"]
    .astype(str)
    .tolist()
)

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
        "Start with the recommendation, then reveal the evidence behind it.",
    )

    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow" style="color:#69D6CB;">
                Executive recommendation
            </div>
            <h2>
                Do not automatically replace the ten lowest-earning machines.
            </h2>
            <div class="subtle">
                Low earnings can reflect short exposure, downtime, payout
                variation, or location context—not necessarily a weak machine.
                Under the official short-horizon result,
                <strong>preserving the $100,000 budget ranks first.</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_wagers = filtered_property[
        "coin_in_usd"
    ].sum()

    total_actual = filtered_property[
        "house_win_usd"
    ].sum()

    total_expected = filtered_property[
        "theo_usd"
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
        money(
            filtered_daily[
                "missed_theo_mid"
            ].sum()
        ),
    )

    st.markdown(
        "### Why the raw bottom-ten list can fail"
    )

    one, two, three = st.columns(3)

    with one:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">1 · Exposure</div>
                <h3>Not every machine had the same opportunity.</h3>
                Installation timing, retirement, and downtime affect raw totals.
                Compare active days and available-hour rates.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with two:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">2 · Luck</div>
                <h3>Actual results can differ from expected results.</h3>
                Slot payouts vary. Compare actual house win with theo before calling
                a machine weak.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with three:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">3 · Context</div>
                <h3>Location and demand are clues, not proof.</h3>
                Zone patterns may reflect traffic, mix, and guest behavior.
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
        "Expected earnings per available hour": "expected_per_available_hour",
    }[ranking_method]

    bottom_ten = (
        machine_summary
        .sort_values(
            [
                ranking_column,
                "machine_id",
            ]
        )
        .head(10)
        .copy()
    )

    if ranking_method == "Total actual earnings":
        actual_values = bottom_ten[
            "actual_house_win"
        ]

        expected_values = bottom_ten[
            "expected_house_win"
        ]

        axis_title = "Total house earnings"

    elif ranking_method == "Actual earnings per active day":
        actual_values = bottom_ten[
            "actual_per_active_day"
        ]

        expected_values = (
            bottom_ten["expected_house_win"]
            / bottom_ten["active_days"].replace(
                0,
                np.nan,
            )
        )

        axis_title = "House earnings per active day"

    else:
        actual_values = (
            bottom_ten["actual_house_win"]
            / bottom_ten["available_hours"].replace(
                0,
                np.nan,
            )
        )

        expected_values = bottom_ten[
            "expected_per_available_hour"
        ]

        axis_title = "House earnings per available hour"

    bottom_ten["actual_value"] = actual_values
    bottom_ten["expected_value"] = expected_values
    bottom_ten["gap_value"] = (
        bottom_ten["actual_value"]
        - bottom_ten["expected_value"]
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            y=bottom_ten["machine_id"],
            x=bottom_ten["actual_value"],
            orientation="h",
            name="Actual",
            marker_color=[
                PURPLE
                if str(machine_id) == "M-1158"
                else GOLD
                for machine_id in bottom_ten["machine_id"]
            ],
            customdata=np.column_stack(
                [
                    bottom_ten["expected_value"],
                    bottom_ten["gap_value"],
                ]
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Actual: $%{x:,.0f}<br>"
                "Expected: $%{customdata[0]:,.0f}<br>"
                "Actual − expected: $%{customdata[1]:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Bar(
            y=bottom_ten["machine_id"],
            x=bottom_ten["expected_value"],
            orientation="h",
            name="Expected",
            marker_color=TEAL,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Expected: $%{x:,.0f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        barmode="group",
        bargap=.30,
        bargroupgap=.08,
    )

    figure.update_yaxes(
        autorange="reversed",
        title=None,
    )

    figure.update_xaxes(
        title=axis_title,
        tickprefix="$",
        separatethousands=True,
    )

    render_chart(
        figure,
        "Bottom-ten machines: actual versus expected",
        "bottom-ten-chart",
        height=430,
    )

    most_negative = (
        bottom_ten
        .sort_values("gap_value")
        .iloc[0]
    )

    insight_bubble(
        "What this chart says",
        (
            f"<strong>{html.escape(str(most_negative['machine_id']))}</strong> "
            f"has the largest negative actual-versus-expected gap among the "
            f"displayed machines: "
            f"<strong>{money(most_negative['gap_value'])}</strong>. "
            "That supports inspection of configuration and meters. It does not "
            "establish a defect or wrongdoing."
        ),
        tone="purple",
    )

    st.markdown("### Evidence Claw")

    insight_bubble(
        "How to use it",
        (
            "Grab a machine from the raw bottom-ten list. The claw reveals "
            "metrics calculated from the local machine data. It does not modify "
            "the rankings or add outside information."
        ),
    )

    raw_bottom = (
        machine_summary
        .sort_values(
            [
                "actual_house_win",
                "machine_id",
            ]
        )
        .head(10)["machine_id"]
        .astype(str)
        .tolist()
    )

    capsules = raw_bottom[:4]

    while len(capsules) < 4:
        capsules.append("ACEIQ")

    selected_prize = (
        st.session_state.claw_machine_id
    )

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
            2025
            + st.session_state.claw_count
        )

        selected = str(
            rng.choice(choices)
        )

        st.session_state.claw_machine_id = selected
        st.session_state.selected_machine_id = selected
        st.session_state.claw_count += 1

        st.session_state.claw_animation_mode = (
            "claw-run-b"
            if (
                st.session_state.claw_animation_mode
                == "claw-run-a"
            )
            else "claw-run-a"
        )

        st.rerun()

    if selected_prize:
        picked = (
            machine_summary
            .set_index("machine_id")
            .loc[selected_prize]
        )

        title, reason, accent = (
            recommendation_for_machine(picked)
        )

        st.markdown(
            f"""
            <div class="panel"
                 style="margin-top:.7rem;border-left:4px solid {accent};">
                <div class="eyebrow">Claw result</div>
                <h3>♠ {html.escape(str(selected_prize))}</h3>
                <div class="subtle">
                    Active days:
                    <strong>{int(picked["active_days"])}</strong><br>
                    Availability:
                    <strong>{pct(picked["availability_rate"])}</strong><br>
                    Downtime:
                    <strong>{picked["downtime_hours"]:.1f} hours</strong><br>
                    Actual − expected:
                    <strong>{money(picked["actual_minus_expected"])}</strong><br><br>
                    <strong>{html.escape(title)}</strong><br>
                    {html.escape(reason)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    monthly = (
        filtered_property.assign(
            month=filtered_property[
                "gaming_date"
            ].dt.strftime("%Y-%m")
        )
        .groupby(
            "month",
            as_index=False,
        )
        .agg(
            wagers=("coin_in_usd", "sum"),
            available_hours=(
                "available_machine_hours",
                "sum",
            ),
        )
    )

    if not monthly.empty:
        monthly["wagers_per_available_hour"] = (
            monthly["wagers"]
            / monthly["available_hours"].replace(
                0,
                np.nan,
            )
        )

        figure = px.line(
            monthly,
            x="month",
            y="wagers_per_available_hour",
            markers=True,
            color_discrete_sequence=[GOLD],
        )

        figure.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
        )

        figure.update_yaxes(
            tickprefix="$",
            separatethousands=True,
        )

        render_chart(
            figure,
            "Demand over time",
            "demand-chart",
            height=320,
        )

        peak = monthly.loc[
            monthly["wagers_per_available_hour"].idxmax()
        ]

        latest = monthly.iloc[-1]

        insight_bubble(
            "Demand takeaway",
            (
                f"Demand peaked in <strong>{peak['month']}</strong> at "
                f"<strong>{money(peak['wagers_per_available_hour'])}</strong> "
                f"per available machine-hour. The latest visible month, "
                f"<strong>{latest['month']}</strong>, was "
                f"<strong>{money(latest['wagers_per_available_hour'])}</strong>. "
                "Use the observed weekday pattern for planning rather than a "
                "single flat daily assumption."
            ),
        )

    st.markdown(
        """
        <div class="success">
            <strong>Official July decision:</strong> Preserve budget under the
            current official model assumptions. Use inspection as a learning action
            when the evidence supports it.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# INVESTIGATE
# =============================================================================

elif page == "Investigate":
    section_header(
        "Machine Investigation",
        "Luck, location, downtime, or persistent gap?",
        "Inspect one machine at a time before recommending action.",
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

    options = sorted(
        pool["machine_id"]
        .astype(str)
        .tolist()
    )

    if not options:
        st.warning(
            "No machines match these filters."
        )
        st.stop()

    selected_index = (
        options.index(
            st.session_state.selected_machine_id
        )
        if st.session_state.selected_machine_id in options
        else 0
    )

    selected_machine_id = st.selectbox(
        "Select machine",
        options,
        index=selected_index,
    )

    st.session_state.selected_machine_id = (
        selected_machine_id
    )

    machine = (
        machine_summary
        .set_index("machine_id")
        .loc[selected_machine_id]
        .copy()
    )

    machine["machine_id"] = selected_machine_id

    title, reason, accent = (
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
                <strong>{html.escape(title)}</strong><br>
                {html.escape(reason)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)

    metrics[0].metric(
        "Active days",
        int(machine["active_days"]),
    )

    metrics[1].metric(
        "Availability",
        pct(machine["availability_rate"]),
    )

    metrics[2].metric(
        "Actual − expected",
        money(machine["actual_minus_expected"]),
    )

    metrics[3].metric(
        "Downtime",
        f"{machine['downtime_hours']:.1f} hours",
    )

    selected_daily = filtered_daily[
        filtered_daily["machine_id"].astype(str)
        == selected_machine_id
    ].sort_values(
        "gaming_date"
    ).copy()

    selected_daily["cumulative_actual"] = (
        selected_daily[
            "house_win_usd"
        ].cumsum()
    )

    selected_daily["cumulative_expected"] = (
        selected_daily[
            "theo_usd"
        ].cumsum()
    )

    left, right = st.columns(2)

    with left:
        figure = go.Figure()

        figure.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_actual"],
            name="Actual",
            line=dict(
                color=GOLD,
                width=3,
            ),
        )

        figure.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_expected"],
            name="Expected",
            line=dict(
                color=TEAL,
                width=3,
            ),
        )

        figure.update_yaxes(
            title="Cumulative earnings",
            tickprefix="$",
            separatethousands=True,
        )

        render_chart(
            figure,
            "Actual versus expected",
            "actual-expected-chart",
            height=370,
        )

    with right:
        downtime_days = selected_daily[
            selected_daily["down_hours"] > 0
        ].copy()

        if downtime_days.empty:
            st.markdown(
                """
                <div class="panel" style="min-height:300px;">
                    <div class="eyebrow">Downtime evidence</div>
                    <h3>No downtime incidents in this period.</h3>
                    <div class="subtle">
                        There are no positive downtime observations for this
                        machine in the selected evidence period.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            figure = px.scatter(
                downtime_days,
                x="gaming_date",
                y="down_hours",
                size="down_hours",
                color_discrete_sequence=[ORANGE],
                labels={
                    "gaming_date": "Gaming date",
                    "down_hours": "Downtime hours",
                },
            )

            figure.update_traces(
                marker=dict(
                    line=dict(
                        color=WHITE,
                        width=1,
                    )
                )
            )

            render_chart(
                figure,
                "Downtime incidents only",
                "downtime-incidents-chart",
                height=370,
            )

    availability_value = machine[
        "availability_rate"
    ]

    gap_value = machine[
        "actual_minus_expected"
    ]

    if availability_value >= .95 and gap_value < 0:
        message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> was available "
            f"{pct(availability_value)} of scheduled time but finished "
            f"<strong>{money(gap_value)}</strong> below expected. Downtime alone "
            "does not explain the result, so configuration and meter verification "
            "should come first."
        )

        tone = "purple"

    elif availability_value < .90:
        message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> had "
            f"<strong>{pct(availability_value)}</strong> availability. "
            "Maintenance should be addressed before interpreting low earnings "
            "as a machine-quality problem."
        )

        tone = "warning"

    else:
        message = (
            f"<strong>{html.escape(selected_machine_id)}</strong> finished "
            f"{money(gap_value)} versus expected. Compare it with similar "
            "machines over a longer period before taking an irreversible action."
        )

        tone = "normal"

    insight_bubble(
        "Investigation takeaway",
        message,
        tone=tone,
    )

    st.markdown(
        """
        <div class="warning">
            A payout gap is an inspection lead. It is not proof of malfunction,
            fraud, tampering, cheating, or wrongdoing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "Open detailed machine evidence"
    ):
        st.dataframe(
            machine_summary.sort_values(
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
# JULY DEMAND OUTLOOK
# =============================================================================

elif page == "July Demand Outlook":
    section_header(
        "July Demand Outlook",
        "A simple validated model for planning.",
        "January–April training, May–June holdout, July planning.",
    )

    forecast = report.get(
        "forecast",
        {}
    )

    if not forecast:
        st.error(
            "The forecast section is missing from analysis_results.json."
        )
        st.stop()

    metrics = st.columns(4)

    metrics[0].metric(
        "Weekday model MAE",
        money(
            forecast.get(
                "weekday_mae"
            )
        ),
    )

    metrics[1].metric(
        "Constant baseline MAE",
        money(
            forecast.get(
                "constant_mae"
            )
        ),
    )

    metrics[2].metric(
        "Holdout improvement",
        pct(
            forecast.get(
                "improvement_pct"
            )
        ),
    )

    metrics[3].metric(
        "July planning baseline",
        money(
            forecast.get(
                "july_refit_baseline_wagers"
            )
        ),
    )

    test_rows = forecast.get(
        "test_rows",
        []
    )

    if test_rows:
        validation = pd.DataFrame(
            test_rows
        )

        validation["gaming_date"] = pd.to_datetime(
            validation["gaming_date"]
        )

        figure = go.Figure()

        figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["coin_in_usd"],
            name="Observed",
            line=dict(
                color=GOLD,
                width=3,
            ),
        )

        figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["weekday_prediction"],
            name="Weekday model",
            line=dict(
                color=TEAL,
                width=2.5,
            ),
        )

        figure.add_scatter(
            x=validation["gaming_date"],
            y=validation["constant_prediction"],
            name="Constant baseline",
            line=dict(
                color=PURPLE,
                width=2,
                dash="dot",
            ),
        )

        figure.update_yaxes(
            title="Daily wagers",
            tickprefix="$",
            separatethousands=True,
        )

        render_chart(
            figure,
            "Time-based holdout forecast",
            "forecast-chart",
            height=440,
        )

        weekday_mae = forecast.get(
            "weekday_mae",
            np.nan,
        )

        constant_mae = forecast.get(
            "constant_mae",
            np.nan,
        )

        if (
            pd.notna(weekday_mae)
            and pd.notna(constant_mae)
        ):
            best_model = (
                "weekday model"
                if weekday_mae < constant_mae
                else "constant baseline"
            )

            insight_bubble(
                "Planning takeaway",
                (
                    f"The precomputed holdout results show that the "
                    f"<strong>{best_model}</strong> had the lower MAE. "
                    "Use that result for staffing and promotion planning. "
                    "July remains a forecast, not observed performance."
                ),
            )

    st.markdown(
        """
        <div class="success">
            Use the validated model for planning, while keeping forecast uncertainty
            visible to decision-makers.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# GUEST AND LOYALTY INSIGHTS
# =============================================================================

elif page == "Guest & Loyalty Insights":
    section_header(
        "Guest & Loyalty Insights",
        "Tracked-player outcomes and comp economics.",
        "Tracked/card-based data is not the full casino population.",
    )

    st.markdown(
        """
        <div class="warning">
            Do not use gambling-loss behavior to target guests or encourage harmful
            gambling. Any comp test should be ethical, opt-in where appropriate,
            and use a comparison group.
        </div>
        """,
        unsafe_allow_html=True,
    )

    player = report.get(
        "players",
        {}
    )

    if player:
        metrics = st.columns(5)

        metrics[0].metric(
            "Tracked players",
            f"{player.get('tracked_players', 0):,}",
        )

        metrics[1].metric(
            "Tracked wager coverage",
            pct(
                player.get(
                    "tracked_wager_coverage"
                )
            ),
        )

        metrics[2].metric(
            "Tracked wagers",
            money(
                player.get(
                    "tracked_wagers"
                )
            ),
        )

        metrics[3].metric(
            "Tracked payouts",
            money(
                player.get(
                    "tracked_payouts"
                )
            ),
        )

        metrics[4].metric(
            "Tracked player net",
            money(
                player.get(
                    "player_net"
                )
            ),
        )

    available_groups = [
        column
        for column in [
            "home_region",
            "age_band",
            "period_month",
        ]
        if column in guests.columns
    ]

    if available_groups:
        grouping = st.selectbox(
            "Compare tracked guest groups by",
            available_groups,
            format_func=lambda value: value.replace(
                "_",
                " ",
            ).title(),
        )

        grouped = (
            guests.groupby(
                grouping,
                as_index=False,
            )[
                [
                    "wagers",
                    "payouts",
                    "player_net",
                    "comp_cost",
                ]
            ]
            .sum()
            .sort_values(
                "wagers",
                ascending=False,
            )
        )

        figure = px.bar(
            grouped,
            x=grouping,
            y="wagers",
            color="player_net",
            color_continuous_scale=[
                [0.0, RED],
                [0.5, GOLD],
                [1.0, TEAL],
            ],
        )

        figure.update_yaxes(
            tickprefix="$",
            separatethousands=True,
        )

        render_chart(
            figure,
            "Tracked wagers by guest group",
            "guest-chart",
            height=390,
        )

        highest_group = grouped.iloc[0]

        insight_bubble(
            "Guest-data takeaway",
            (
                f"<strong>{html.escape(str(highest_group[grouping]))}</strong> "
                "has the largest tracked wager volume in the selected grouping. "
                "This describes carded activity only and should not be treated as "
                "the full casino population."
            ),
        )

        download_csv(
            grouped,
            "aceiq_guest_groups.csv",
            "Download guest-group CSV",
        )

    else:
        st.warning(
            "No supported guest grouping fields were found."
        )


# =============================================================================
# METHODS AND EVIDENCE
# =============================================================================

else:
    section_header(
        "Methods & Evidence",
        "Trace recommendations back to data and assumptions.",
        "Detailed evidence is stored here so the decision page stays readable.",
    )

    machine_tab, downtime_tab, decision_tab, download_tab = st.tabs(
        [
            "Machine method",
            "Downtime & demand",
            "Official decision model",
            "Downloads",
        ]
    )

    with machine_tab:
        st.markdown(
            """
            <div class="warning">
                <strong>Actual earnings:</strong> coin-in − payout.<br>
                <strong>Expected earnings:</strong> coin-in × (1 − configured RTP).<br>
                <strong>Actual minus expected:</strong> actual earnings − expected earnings.<br><br>
                A payout gap is an inspection lead—not proof of malfunction,
                fraud, tampering, cheating, or wrongdoing.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.dataframe(
            machine_summary.sort_values(
                "actual_house_win"
            ),
            use_container_width=True,
            hide_index=True,
        )

    with downtime_tab:
        metrics = st.columns(3)

        metrics[0].metric(
            "Downtime hours",
            f"{filtered_daily['down_hours'].sum():,.0f}",
        )

        metrics[1].metric(
            "Midpoint wagering opportunity",
            money(
                filtered_daily[
                    "missed_wagers_mid"
                ].sum()
            ),
        )

        metrics[2].metric(
            "Midpoint theo opportunity",
            money(
                filtered_daily[
                    "missed_theo_mid"
                ].sum()
            ),
        )

        zone_figure = px.bar(
            zone_summary.sort_values(
                "downtime_opportunity"
            ),
            y="zone_name",
            x="downtime_opportunity",
            orientation="h",
            color_discrete_sequence=[ORANGE],
        )

        zone_figure.update_xaxes(
            tickprefix="$",
            separatethousands=True,
        )

        render_chart(
            zone_figure,
            "Estimated downtime opportunity by zone",
            "downtime-zone-chart",
            height=360,
        )

        insight_bubble(
            "Downtime interpretation",
            (
                "Downtime opportunity is a historical estimate based on observed "
                "operating rates. It is not guaranteed recoverable revenue because "
                "guests may have played elsewhere."
            ),
            tone="warning",
        )

    with decision_tab:
        simulation = report.get(
            "simulation",
            {}
        )

        recommendation = simulation.get(
            "recommended",
            {}
        )

        st.markdown(
            """
            <div class="hero">
                <div class="eyebrow" style="color:#69D6CB;">
                    Official precomputed result
                </div>
                <h2>
                    Keep Budget ranks first under current short-horizon assumptions.
                </h2>
                Inspection and controlled pilots may provide information value
                beyond the 30-day monetary model.
            </div>
            """,
            unsafe_allow_html=True,
        )

        metrics = st.columns(4)

        metrics[0].metric(
            "Shared scenarios",
            f"{simulation.get('scenarios', 0):,}",
        )

        metrics[1].metric(
            "Feasible portfolios",
            f"{simulation.get('feasible_portfolios', 0):,}",
        )

        metrics[2].metric(
            "Recommended spend",
            money(
                recommendation.get(
                    "cost"
                )
            ),
        )

        metrics[3].metric(
            "Expected modeled net",
            money(
                recommendation.get(
                    "mean_net"
                )
            ),
        )

        portfolios = pd.DataFrame(
            simulation.get(
                "portfolios",
                []
            )
        )

        if not portfolios.empty:
            with st.expander(
                "Open official portfolio scenarios"
            ):
                st.dataframe(
                    portfolios,
                    use_container_width=True,
                    hide_index=True,
                )

        action_catalog = pd.DataFrame(
            report.get(
                "action_catalog",
                []
            )
        )

        if not action_catalog.empty:
            with st.expander(
                "Open official action catalog"
            ):
                st.dataframe(
                    action_catalog,
                    use_container_width=True,
                    hide_index=True,
                )

        limitations = simulation.get(
            "limitations",
            []
        )

        if limitations:
            st.markdown(
                "### Official model limitations"
            )

            for limitation in limitations:
                st.write(
                    f"• {limitation}"
                )

    with download_tab:
        download_csv(
            machine_summary,
            "aceiq_machine_diagnostics.csv",
            "Download machine diagnostics CSV",
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

        st.markdown(
            """
            <div class="notice">
                This dashboard uses only the local precomputed synthetic data files.
                No external API, internet source, or generative model is used to
                calculate the displayed results.
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
        All displayed calculations use local precomputed data and stated assumptions.
    </div>
    """,
    unsafe_allow_html=True,
)