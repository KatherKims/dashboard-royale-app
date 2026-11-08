"""
AceIQ: Gilded Ace Decision Intelligence
========================================

Run locally:
    python -m streamlit run app.py

Uses only local precomputed files in data/.
No Databricks credentials, internet access, React, Node, or raw refresh required.
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

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

BG = "#0A1118"
PANEL = "#17222C"
WHITE = "#F8F3EA"
MUTED = "#A7B7C2"
GOLD = "#E8BD63"
GOLD_LIGHT = "#F8DA92"
TEAL = "#69D6CB"
GREEN = "#62CA85"
RED = "#F1786C"
ORANGE = "#F3A85B"
PURPLE = "#B88BFF"
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
            --white: {WHITE};
            --muted: {MUTED};
            --gold: {GOLD};
            --gold-light: {GOLD_LIGHT};
            --teal: {TEAL};
            --green: {GREEN};
            --red: {RED};
            --orange: {ORANGE};
            --purple: {PURPLE};
        }}

        .stApp {{
            background:
                radial-gradient(circle at 7% 0%, rgba(115,0,0,.35), transparent 24%),
                radial-gradient(circle at 95% 3%, rgba(232,189,99,.10), transparent 23%),
                linear-gradient(180deg, #0A1118 0%, #091017 100%);
            color: var(--white);
        }}

        .block-container {{
            max-width: 1450px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }}

        header[data-testid="stHeader"] {{
            background: rgba(10,17,24,.82);
        }}

        h1, h2, h3 {{
            color: var(--white) !important;
            letter-spacing: -0.035em;
        }}

        .topbar {{
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:1rem;
            padding:.9rem 1.15rem;
            margin-bottom:.9rem;
            border:1px solid rgba(232,189,99,.35);
            border-radius:16px;
            background:linear-gradient(105deg, rgba(94,0,0,.96), rgba(24,34,44,.98));
            box-shadow:0 14px 32px rgba(0,0,0,.22);
        }}

        .brand {{
            color:var(--gold);
            font-size:1.18rem;
            font-weight:950;
            letter-spacing:.15em;
        }}

        .brand-sub {{
            color:#E8DED0;
            font-size:.70rem;
            letter-spacing:.11em;
            text-transform:uppercase;
            margin-top:.18rem;
        }}

        .top-note {{
            color:#D5E0E4;
            text-align:right;
            font-size:.78rem;
            line-height:1.45;
        }}

        .eyebrow {{
            color:var(--gold);
            font-size:.70rem;
            font-weight:900;
            text-transform:uppercase;
            letter-spacing:.13em;
        }}

        .hero-answer {{
            position:relative;
            overflow:hidden;
            margin:.75rem 0 1rem;
            padding:1.25rem 1.35rem;
            border:1px solid rgba(105,214,203,.38);
            border-radius:16px;
            background:linear-gradient(135deg, rgba(16,79,73,.48), rgba(18,27,36,.96));
            color:#ECF8F6;
        }}

        .hero-answer:after {{
            content:"♠";
            position:absolute;
            right:1.4rem;
            top:-2.5rem;
            color:rgba(232,189,99,.11);
            font-size:9rem;
            pointer-events:none;
        }}

        .hero-answer h2 {{
            margin:.28rem 0 .45rem;
            max-width:850px;
        }}

        .machine-card {{
            padding:1rem;
            margin:.55rem 0 .9rem;
            border:1px solid rgba(232,189,99,.22);
            border-radius:14px;
            background:linear-gradient(145deg, rgba(28,40,52,.98), rgba(16,25,33,.98));
        }}

        .finding {{
            min-height:160px;
            padding:1rem;
            border-radius:13px;
            border:1px solid rgba(232,189,99,.18);
            background:rgba(24,36,47,.88);
            line-height:1.5;
        }}

        .finding-number {{
            color:var(--gold);
            font-size:.72rem;
            font-weight:950;
            letter-spacing:.11em;
            text-transform:uppercase;
        }}

        .warning {{
            margin:.75rem 0;
            padding:.82rem .98rem;
            border-left:4px solid var(--orange);
            border-radius:8px;
            background:rgba(243,168,91,.10);
            color:#F2E8DC;
            line-height:1.5;
        }}

        .success {{
            margin:.75rem 0;
            padding:.82rem .98rem;
            border-left:4px solid var(--teal);
            border-radius:8px;
            background:rgba(105,214,203,.10);
            color:#E4F8F4;
            line-height:1.5;
        }}

        .status-pill {{
            display:inline-block;
            margin-top:.35rem;
            padding:.27rem .62rem;
            border-radius:999px;
            font-size:.72rem;
            font-weight:900;
            letter-spacing:.05em;
        }}

        [data-testid="stMetric"] {{
            background:linear-gradient(145deg, rgba(27,39,50,.97), rgba(15,24,32,.97));
            border:1px solid rgba(232,189,99,.16);
            border-radius:12px;
            padding:.76rem .88rem;
        }}

        [data-testid="stMetricLabel"] {{
            color:var(--muted);
            font-size:.71rem;
            text-transform:uppercase;
            letter-spacing:.07em;
        }}

        [data-testid="stMetricValue"] {{
            color:var(--white);
            font-weight:850;
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap:.4rem;
            border-bottom:1px solid rgba(232,189,99,.18);
        }}

        .stTabs [data-baseweb="tab"] {{
            color:var(--muted);
            padding:.55rem .8rem;
            border-radius:7px 7px 0 0;
        }}

        .stTabs [aria-selected="true"] {{
            color:var(--gold) !important;
            background:rgba(232,189,99,.09);
        }}

        /* ===============================================================
           EVIDENCE CLAW
           Prize is nested inside carriage, so it moves with the claw.
           =============================================================== */

        .claw-cabinet {{
            position:relative;
            overflow:hidden;
            min-height:455px;
            padding:18px;
            border:8px solid #5B2B12;
            border-top-color:#A75F20;
            border-left-color:#A75F20;
            border-radius:25px 25px 14px 14px;
            background:
                radial-gradient(circle at 50% 15%, rgba(255,235,158,.18), transparent 24%),
                linear-gradient(145deg, #6E151E 0%, #350A13 47%, #171D29 100%);
            box-shadow:
                inset 0 0 0 3px rgba(255,208,103,.20),
                inset 0 -20px 40px rgba(0,0,0,.30),
                0 14px 34px rgba(0,0,0,.32);
        }}

        .claw-neon {{
            color:#FFE29A;
            text-shadow:
                0 0 6px rgba(255,205,92,.85),
                0 0 18px rgba(255,155,55,.32);
            font-size:.82rem;
            font-weight:950;
            letter-spacing:.15em;
            text-align:center;
        }}

        .claw-glass {{
            position:relative;
            min-height:286px;
            margin-top:12px;
            overflow:hidden;
            border:5px solid #7A9CAF;
            border-top-color:#C3E5F0;
            border-left-color:#C3E5F0;
            border-radius:10px;
            background:
                linear-gradient(115deg, rgba(255,255,255,.13), transparent 29%),
                linear-gradient(180deg, rgba(32,72,91,.72), rgba(9,20,29,.97));
        }}

        .claw-glass:after {{
            content:"";
            position:absolute;
            left:0;
            right:0;
            top:-80%;
            height:34%;
            background:linear-gradient(
                transparent,
                rgba(196,242,255,.10),
                transparent
            );
            transform:skewY(-8deg);
            pointer-events:none;
        }}

        .claw-rail {{
            position:absolute;
            top:17px;
            left:12%;
            width:76%;
            height:6px;
            background:#D0E4E7;
            box-shadow:0 0 8px rgba(204,238,247,.60);
        }}

        .claw-carriage {{
            position:absolute;
            top:23px;
            left:50%;
            width:90px;
            height:240px;
            transform:translateX(-50%);
            transform-origin:top center;
            z-index:4;
        }}

        .claw-cable {{
            position:absolute;
            top:0;
            left:43px;
            width:4px;
            height:88px;
            background:linear-gradient(#E5F4F4, #7895A1);
        }}

        .claw-arm {{
            position:absolute;
            top:80px;
            left:23px;
            width:44px;
            height:38px;
            transform:translateX(-50%);
            transform-origin:50% 0;
        }}

        .claw-arm:before {{
            content:"";
            position:absolute;
            left:18px;
            top:0;
            width:8px;
            height:13px;
            border-radius:4px;
            background:#E5F5F5;
            box-shadow:0 0 7px rgba(220,255,255,.55);
        }}

        .claw-arm .prong {{
            position:absolute;
            top:11px;
            width:16px;
            height:23px;
            border:4px solid #E5F5F5;
            border-top:none;
            border-radius:0 0 12px 12px;
        }}

        .claw-arm .left {{
            left:0;
            transform:rotate(22deg);
        }}

        .claw-arm .right {{
            right:0;
            transform:rotate(-22deg);
        }}

        .claw-carried-prize {{
            position:absolute;
            top:118px;
            left:50%;
            transform:translateX(-50%);
            width:88px;
            height:43px;
            border-radius:20px;
            border:3px solid #FFE9A7;
            background:linear-gradient(145deg, #D6A63B, #754711);
            color:#FFF7D8;
            font-family:monospace;
            font-size:10px;
            font-weight:950;
            line-height:37px;
            text-align:center;
            box-shadow:
                0 0 14px rgba(255,215,106,.72),
                0 8px 15px rgba(0,0,0,.30);
        }}

        .capsule {{
            position:absolute;
            bottom:22px;
            width:68px;
            height:40px;
            border-radius:18px;
            border:2px solid rgba(255,245,210,.52);
            color:#FFF3CC;
            background:linear-gradient(145deg, #C44550, #6E1620);
            box-shadow:0 5px 10px rgba(0,0,0,.28);
            font-family:monospace;
            font-size:10px;
            font-weight:900;
            text-align:center;
            line-height:36px;
            transform-origin:center bottom;
        }}

        .capsule.one {{
            left:8%;
            transform:rotate(-5deg);
        }}

        .capsule.two {{
            left:29%;
            bottom:48px;
            transform:rotate(4deg);
            background:linear-gradient(145deg, #7860C4, #362969);
        }}

        .capsule.three {{
            left:52%;
            transform:rotate(-3deg);
            background:linear-gradient(145deg, #D99E41, #765016);
        }}

        .capsule.four {{
            left:73%;
            bottom:47px;
            transform:rotate(5deg);
            background:linear-gradient(145deg, #3E9E92, #15564F);
        }}

        .claw-instructions {{
            margin-top:12px;
            color:#D9E4E6;
            font-size:.83rem;
            line-height:1.45;
            text-align:center;
        }}

        .claw-run-a .claw-carriage {{
            animation:clawCycleA 1.65s cubic-bezier(.20,.80,.20,1);
        }}

        .claw-run-b .claw-carriage {{
            animation:clawCycleB 1.65s cubic-bezier(.20,.80,.20,1);
        }}

        .claw-run-a .capsule {{
            animation:capsuleShakeA .85s ease-in-out .32s;
        }}

        .claw-run-b .capsule {{
            animation:capsuleShakeB .85s ease-in-out .32s;
        }}

        .claw-run-a .claw-carried-prize {{
            animation:grabPrizeA 1.65s ease-in-out;
        }}

        .claw-run-b .claw-carried-prize {{
            animation:grabPrizeB 1.65s ease-in-out;
        }}

        .claw-run-a .claw-neon {{
            animation:neonFlashA 1.1s ease-in-out;
        }}

        .claw-run-b .claw-neon {{
            animation:neonFlashB 1.1s ease-in-out;
        }}

        @keyframes clawCycleA {{
            0% {{ transform:translateX(-50%) translateY(0) rotate(0deg); }}
            25% {{ transform:translateX(-50%) translateY(12px) rotate(-3deg); }}
            48% {{ transform:translateX(-50%) translateY(103px) rotate(2deg); }}
            64% {{ transform:translateX(-50%) translateY(103px) rotate(-2deg) scale(.96); }}
            100% {{ transform:translateX(-50%) translateY(0) rotate(0deg); }}
        }}

        @keyframes clawCycleB {{
            0% {{ transform:translateX(-50%) translateY(0) rotate(0deg); }}
            25% {{ transform:translateX(-50%) translateY(12px) rotate(3deg); }}
            48% {{ transform:translateX(-50%) translateY(103px) rotate(-2deg); }}
            64% {{ transform:translateX(-50%) translateY(103px) rotate(2deg) scale(.96); }}
            100% {{ transform:translateX(-50%) translateY(0) rotate(0deg); }}
        }}

        @keyframes capsuleShakeA {{
            0%, 100% {{ transform:translateY(0) rotate(0deg); }}
            25% {{ transform:translateY(-8px) rotate(-6deg); }}
            50% {{ transform:translateY(3px) rotate(5deg); }}
            75% {{ transform:translateY(-4px) rotate(-3deg); }}
        }}

        @keyframes capsuleShakeB {{
            0%, 100% {{ transform:translateY(0) rotate(0deg); }}
            25% {{ transform:translateY(-7px) rotate(6deg); }}
            50% {{ transform:translateY(4px) rotate(-5deg); }}
            75% {{ transform:translateY(-3px) rotate(3deg); }}
        }}

        @keyframes grabPrizeA {{
            0%, 42% {{
                opacity:0;
                transform:translate(-50%, 22px) scale(.55);
            }}
            56% {{
                opacity:1;
                transform:translate(-50%, 0) scale(1.08);
            }}
            100% {{
                opacity:1;
                transform:translate(-50%, 0) scale(1);
            }}
        }}

        @keyframes grabPrizeB {{
            0%, 42% {{
                opacity:0;
                transform:translate(-50%, 22px) scale(.55);
            }}
            56% {{
                opacity:1;
                transform:translate(-50%, 0) scale(1.08);
            }}
            100% {{
                opacity:1;
                transform:translate(-50%, 0) scale(1);
            }}
        }}

        @keyframes neonFlashA {{
            0%, 100% {{ filter:brightness(1); transform:scale(1); }}
            35% {{ filter:brightness(1.75); transform:scale(1.05); }}
            60% {{ filter:brightness(.75); }}
        }}

        @keyframes neonFlashB {{
            0%, 100% {{ filter:brightness(1); transform:scale(1); }}
            35% {{ filter:brightness(1.75); transform:scale(1.05); }}
            60% {{ filter:brightness(.75); }}
        }}

        .footer {{
            color:#80919D;
            text-align:center;
            font-size:.75rem;
            padding:1rem 0 .2rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# DATA LOADING
# =============================================================================

@st.cache_data
def load_data():
    required = [
        DATA_DIR / "analysis_results.json",
        DATA_DIR / "machines.parquet",
        DATA_DIR / "machine_daily.parquet",
        DATA_DIR / "guest_groups.parquet",
        DATA_DIR / "property_daily.parquet",
        DATA_DIR / "scenario_net.npz",
    ]

    missing = [str(path) for path in required if not path.exists()]

    if missing:
        raise FileNotFoundError(
            "Missing required local data files:\n\n" + "\n".join(missing)
        )

    report = json.loads(
        (DATA_DIR / "analysis_results.json").read_text(encoding="utf-8")
    )

    machines = pd.read_parquet(DATA_DIR / "machines.parquet")
    daily = pd.read_parquet(DATA_DIR / "machine_daily.parquet")
    guests = pd.read_parquet(DATA_DIR / "guest_groups.parquet")
    property_daily = pd.read_parquet(DATA_DIR / "property_daily.parquet")
    scenario_samples = np.load(DATA_DIR / "scenario_net.npz")["net"]

    daily["gaming_date"] = pd.to_datetime(daily["gaming_date"])
    property_daily["gaming_date"] = pd.to_datetime(
        property_daily["gaming_date"]
    )

    return (
        report,
        machines,
        daily,
        guests,
        property_daily,
        scenario_samples,
    )


# =============================================================================
# HELPERS
# =============================================================================

def money(value, decimals=0):
    if value is None or pd.isna(value):
        return "—"

    value = float(value)
    display = f"${abs(value):,.{decimals}f}"
    return f"-{display}" if value < 0 else display


def pct(value, decimals=1):
    if value is None or pd.isna(value):
        return "—"

    return f"{float(value):.{decimals}%}"


def safe_divide(numerator, denominator):
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan

    return numerator / denominator


def section_header(kicker, title, subtitle=""):
    st.markdown(
        f"""
        <div class="eyebrow">{kicker}</div>
        <h2 style="margin:.12rem 0 .35rem;">{title}</h2>
        <div style="color:#C8D2D8;margin-bottom:.75rem;">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def chart(fig, title, key, height=410):
    fig.update_layout(
        title=dict(
            text=title,
            x=0.01,
            font=dict(color=WHITE, size=18),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=BG,
        font=dict(color=WHITE),
        margin=dict(l=25, r=25, t=70, b=42),
        height=height,
        legend=dict(orientation="h", y=1.02, x=0),
    )

    fig.update_xaxes(gridcolor=GRID, zerolinecolor="#485661")
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#485661")

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key,
        config={"displaylogo": False},
    )


def download_csv(df, filename, label):
    st.download_button(
        label=label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def build_machine_summary(filtered_daily, machines):
    grouped = (
        filtered_daily.groupby("machine_id", as_index=False)
        .agg(
            actual_house_win=("house_win_usd", "sum"),
            expected_house_win=("theo_usd", "sum"),
            total_wagers=("coin_in_usd", "sum"),
            available_hours=("available_hours", "sum"),
            scheduled_hours=("scheduled_hours", "sum"),
            downtime_hours=("down_hours", "sum"),
            estimated_downtime_opportunity=("missed_theo_mid", "sum"),
            active_days=("gaming_date", "nunique"),
        )
    )

    grouped["availability_rate"] = (
        grouped["available_hours"]
        / grouped["scheduled_hours"].replace(0, np.nan)
    )

    grouped["actual_per_active_day"] = (
        grouped["actual_house_win"]
        / grouped["active_days"].replace(0, np.nan)
    )

    grouped["expected_per_available_hour"] = (
        grouped["expected_house_win"]
        / grouped["available_hours"].replace(0, np.nan)
    )

    grouped["actual_per_available_hour"] = (
        grouped["actual_house_win"]
        / grouped["available_hours"].replace(0, np.nan)
    )

    grouped["actual_minus_expected"] = (
        grouped["actual_house_win"] - grouped["expected_house_win"]
    )

    metadata = [
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

    metadata = [
        col for col in metadata if col in machines.columns
    ]

    return grouped.merge(
        machines[metadata],
        on="machine_id",
        how="left",
    )


def add_location_context(machine_summary, filtered_daily):
    location = (
        filtered_daily.groupby(
            ["machine_id", "zone_name", "bank_id"],
            as_index=False,
        )
        .agg(available_hours=("available_hours", "sum"))
        .sort_values(
            ["machine_id", "available_hours"],
            ascending=[True, False],
        )
        .drop_duplicates("machine_id")
    )

    return machine_summary.merge(
        location[["machine_id", "zone_name", "bank_id"]],
        on="machine_id",
        how="left",
    )


def build_zone_summary(filtered_daily):
    zones = (
        filtered_daily.groupby("zone_name", as_index=False)
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
        / zones["available_hours"].replace(0, np.nan)
    )

    zones["availability_rate"] = (
        zones["available_hours"]
        / zones["scheduled_hours"].replace(0, np.nan)
    )

    zones["actual_minus_expected"] = (
        zones["actual"] - zones["expected"]
    )

    return zones


def build_bank_summary(filtered_daily):
    banks = (
        filtered_daily.groupby(
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
        banks["actual"] - banks["expected"]
    )

    return banks


def machine_category(row):
    if not bool(row.get("eligible_july", False)):
        return "Not a July action target"

    standardized_gap = row.get("standardized_gap", np.nan)
    availability = row.get("availability_rate", np.nan)
    actual_gap = row.get("actual_minus_expected", np.nan)
    downtime_opportunity = row.get(
        "estimated_downtime_opportunity",
        0,
    )
    expected = row.get("expected_house_win", 0)

    if pd.notna(standardized_gap) and standardized_gap <= -3:
        return "Inspection candidate"

    if pd.notna(availability) and availability < 0.90:
        return "Maintenance candidate"

    if expected > 0 and downtime_opportunity > expected * 0.10:
        return "Maintenance candidate"

    if pd.notna(actual_gap) and actual_gap < 0:
        return "Monitor payout variance"

    return "Monitor"


def recommendation_for_machine(row):
    category = machine_category(row)

    if category == "Not a July action target":
        return (
            "No July action",
            "This machine is not on the July floor and should not be selected as a July action target.",
            GRAY,
        )

    if category == "Inspection candidate":
        return (
            "Inspect configuration and meters first",
            "The actual-versus-expected gap is an unusual screening signal. Review configuration, game math, and meter history before considering relocation or replacement.",
            PURPLE,
        )

    if category == "Maintenance candidate":
        return (
            "Address availability before replacement",
            "Low availability or meaningful downtime opportunity means this machine may not have received a fair chance to earn.",
            ORANGE,
        )

    if category == "Monitor payout variance":
        return (
            "Monitor against exposure-adjusted peers",
            "The machine is below expected in this period, but payout variation remains a plausible explanation.",
            GOLD,
        )

    return (
        "Monitor before spending",
        "Current evidence does not establish that relocating or replacing this machine would outperform preserving budget.",
        GREEN,
    )


def sandbox_result(
    machine,
    zone_summary,
    selected_action,
    destination_zone,
    retained_play,
    maintenance_recovery,
    lease_uplift,
):
    """
    Interactive planning sandbox.

    It is separate from the official 1,000-scenario portfolio model.
    It reports low/base/high sensitivity under visible assumptions.
    """
    expected_hour = float(
        machine.get("expected_per_available_hour", 0) or 0
    )
    availability = float(
        machine.get("availability_rate", 0.90) or 0.90
    )
    downtime_opportunity = float(
        machine.get("estimated_downtime_opportunity", 0) or 0
    )

    origin_zone = str(machine.get("zone_name", "Unknown"))

    zone_rates = zone_summary.set_index("zone_name")[
        "wagers_per_available_hour"
    ]

    origin_rate = zone_rates.get(origin_zone, zone_rates.median())
    destination_rate = zone_rates.get(
        destination_zone,
        zone_rates.median(),
    )

    zone_factor = safe_divide(destination_rate, origin_rate)

    if pd.isna(zone_factor):
        zone_factor = 1.0

    july_baseline_theo = (
        expected_hour
        * min(max(availability, 0), 1)
        * 30
        * 24
    )

    action_cost = 0.0
    downtime_cost = 0.0
    low = 0.0
    base = 0.0
    high = 0.0
    assumptions = ""
    limitation = ""
    measurement = ""

    if selected_action == "Keep Budget":
        assumptions = "No intervention effect is credited."
        limitation = (
            "This is the baseline, not proof that every future intervention is unprofitable."
        )
        measurement = (
            "Continue monitoring availability, expected earnings per available hour, and actual-versus-expected results."
        )

    elif selected_action == "Inspect":
        action_cost = 1200.0
        downtime_cost = 2 * expected_hour
        low = -(action_cost + downtime_cost)
        base = low
        high = low

        assumptions = (
            "Inspection receives no unverified corrective cash benefit in the 30-day sandbox."
        )
        limitation = (
            "Information value is not monetized. Inspection may still affect a later repair or replacement decision."
        )
        measurement = (
            "Reconcile configured RTP, game math, meter history, and repair records. Estimate verified corrective value separately."
        )

    elif selected_action == "Move":
        action_cost = 1800.0
        downtime_cost = 3 * expected_hour

        uplift = zone_factor - 1.0
        low_retained = max(0.10, retained_play - 0.25)
        high_retained = min(1.00, retained_play + 0.25)

        low = (
            july_baseline_theo * uplift * low_retained
            - action_cost
            - downtime_cost
        )
        base = (
            july_baseline_theo * uplift * retained_play
            - action_cost
            - downtime_cost
        )
        high = (
            july_baseline_theo * uplift * high_retained
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"Observed destination/origin demand factor: {zone_factor:.2f}×. "
            f"Retained incremental-play assumption: {retained_play:.0%}."
        )
        limitation = (
            "Zone differences are observational, not causal proof. Some play may shift from nearby machines."
        )
        measurement = (
            "Compare expected earnings per available hour against a predefined untreated machine or bank and monitor displacement."
        )

    elif selected_action == "Maintain":
        action_cost = 9000.0
        downtime_cost = 1.5 * expected_hour

        july_opportunity = downtime_opportunity / 181 * 23
        low_recovery = max(0.05, maintenance_recovery - 0.20)
        high_recovery = min(0.95, maintenance_recovery + 0.25)

        low = (
            july_opportunity * low_recovery * retained_play
            - action_cost
            - downtime_cost
        )
        base = (
            july_opportunity * maintenance_recovery * retained_play
            - action_cost
            - downtime_cost
        )
        high = (
            july_opportunity * high_recovery * retained_play
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"Downtime recovery: {maintenance_recovery:.0%}; "
            f"retained incremental play: {retained_play:.0%}."
        )
        limitation = (
            "Recovered downtime opportunity is not guaranteed new floor revenue because guests may have played elsewhere."
        )
        measurement = (
            "Compare unavailable hours, repeat faults, repair turnaround, and expected earnings per scheduled hour against untreated peers."
        )

    elif selected_action == "Lease / Replace":
        action_cost = 3380.0
        downtime_cost = 6 * expected_hour

        low_uplift = -0.10
        high_uplift = min(2.0, lease_uplift + 0.65)

        low = (
            july_baseline_theo
            * (16 / 30)
            * low_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )
        base = (
            july_baseline_theo
            * (16 / 30)
            * lease_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )
        high = (
            july_baseline_theo
            * (16 / 30)
            * high_uplift
            * retained_play
            - action_cost
            - downtime_cost
        )

        assumptions = (
            f"New-title uplift assumption: {lease_uplift:.0%}; "
            "16 usable July days after lead time."
        )
        limitation = (
            "New-title uplift is a planning assumption, not an observed causal replacement effect."
        )
        measurement = (
            "Compare replacement performance with matched unchanged machines and monitor nearby machines for displacement."
        )

    spread = high - low

    if spread > 6000:
        uncertainty = "High"
    elif spread > 2000:
        uncertainty = "Medium"
    else:
        uncertainty = "Lower"

    if selected_action == "Inspect":
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
        "retained_play": 0.50,
        "maintenance_recovery": 0.50,
        "lease_uplift": 0.50,
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


def reset_sandbox(message):
    st.session_state.selected_action = "Keep Budget"
    st.session_state.destination_zone = None
    st.session_state.retained_play = 0.50
    st.session_state.maintenance_recovery = 0.50
    st.session_state.lease_uplift = 0.50
    st.session_state.july_plan = []
    st.session_state.plan_message = message
    st.session_state.plan_message_type = "info"
    st.session_state.claw_machine_id = None


def plan_budget_used():
    return float(
        sum(item["total_cost"] for item in st.session_state.july_plan)
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
            "Keep Budget is the $0 baseline. It does not need to be added to the spending tray."
        )
        st.session_state.plan_message_type = "info"
        return

    if not bool(machine.get("eligible_july", False)):
        st.session_state.plan_message = (
            "This machine is not eligible for a July action."
        )
        st.session_state.plan_message_type = "error"
        return

    if (
        action == "Move"
        and result["origin_zone"] == result["destination_zone"]
    ):
        st.session_state.plan_message = (
            "Choose a destination zone different from the current zone before adding a move."
        )
        st.session_state.plan_message_type = "error"
        return

    if any(
        item["machine_id"] == machine["machine_id"]
        for item in st.session_state.july_plan
    ):
        st.session_state.plan_message = (
            f"{machine['machine_id']} already has an action in the July plan. Remove it before assigning another action."
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

    total_cost = result["action_cost"] + result["downtime_cost"]

    if plan_budget_used() + total_cost > MAX_BUDGET:
        st.session_state.plan_message = (
            "Adding this action would exceed the $100,000 July budget."
        )
        st.session_state.plan_message_type = "error"
        return

    st.session_state.july_plan.append(
        {
            "machine_id": machine["machine_id"],
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
        f"{action} for {machine['machine_id']} was added to the July Action Tray."
    )
    st.session_state.plan_message_type = "success"


# =============================================================================
# LOAD DATA / FILTER
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
    st.error("AceIQ could not load its required data files.")
    st.code(str(error))
    st.stop()

initialize_state()

min_date = daily["gaming_date"].min().date()
max_date = daily["gaming_date"].max().date()


# =============================================================================
# TOP NAVIGATION / GLOBAL FILTER
# =============================================================================

st.markdown(
    """
    <div class="topbar">
        <div>
            <div class="brand">♠ ACEIQ</div>
            <div class="brand-sub">The Gilded Ace · Decision Intelligence</div>
        </div>
        <div class="top-note">
            Fictional casino · Synthetic data<br>
            July planning horizon: 30 days
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

nav_col, date_col, note_col = st.columns([1.85, 1.35, 2.15])

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

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)

signature = f"{start_date.date()}_{end_date.date()}"

if st.session_state.period_signature is None:
    st.session_state.period_signature = signature
elif st.session_state.period_signature != signature:
    st.session_state.period_signature = signature
    reset_sandbox(
        "Evidence period changed, so the interactive sandbox and July Action Tray were reset."
    )

with note_col:
    st.markdown(
        f"""
        <div style="padding-top:1.7rem;color:#D4DEE3;font-size:.82rem;">
            <strong>Active evidence period:</strong>
            {start_date.strftime("%b %d, %Y")} to
            {end_date.strftime("%b %d, %Y")}<br>
            This updates machine, zone, bank, demand, and guest evidence.
            Forecast validation stays fixed at Jan–Apr training / May–Jun holdout.
        </div>
        """,
        unsafe_allow_html=True,
    )

filtered_daily = daily[
    (daily["gaming_date"] >= start_date)
    & (daily["gaming_date"] <= end_date)
].copy()

filtered_property = property_daily[
    (property_daily["gaming_date"] >= start_date)
    & (property_daily["gaming_date"] <= end_date)
].copy()

if filtered_daily.empty:
    st.error("No machine data exists for the selected evidence period.")
    st.stop()

machine_summary = build_machine_summary(filtered_daily, machines)
machine_summary = add_location_context(machine_summary, filtered_daily)
machine_summary["classification"] = machine_summary.apply(
    machine_category,
    axis=1,
)

zone_summary = build_zone_summary(filtered_daily)
bank_summary = build_bank_summary(filtered_daily)

machine_ids = sorted(
    machine_summary["machine_id"].astype(str).tolist()
)

if (
    st.session_state.selected_machine_id is None
    or st.session_state.selected_machine_id not in machine_ids
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
        "Start with the recommendation. Then reveal only the evidence needed to understand it.",
    )

    st.markdown(
        """
        <div class="hero-answer">
            <div class="eyebrow" style="color:#69D6CB;">Executive recommendation</div>
            <h2>Do not automatically replace the ten lowest-earning machines.</h2>
            Low earnings can reflect short exposure, downtime, payout variation, or
            location context—not necessarily a weak machine. Under current official
            short-horizon assumptions, <strong>preserving the $100,000 budget ranks first.</strong>
            Targeted inspection remains useful as a learning action.
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_wagers = filtered_property["coin_in_usd"].sum()
    total_actual = filtered_property["house_win_usd"].sum()
    total_expected = filtered_property["theo_usd"].sum()

    metrics = st.columns(4)

    metrics[0].metric("Selected-period wagers", money(total_wagers))
    metrics[1].metric("Actual earnings", money(total_actual))
    metrics[2].metric(
        "Actual − expected",
        money(total_actual - total_expected),
    )
    metrics[3].metric(
        "Downtime opportunity",
        money(filtered_daily["missed_theo_mid"].sum()),
    )

    st.markdown("### Why the raw bottom-ten list can fail")

    card_one, card_two, card_three = st.columns(3)

    with card_one:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">1 · Exposure</div>
                <h3 style="margin:.35rem 0;">Not every machine had the same opportunity.</h3>
                Late installation, retirement, and downtime reduce a machine's chance
                to earn. Compare per active day or available hour—not totals alone.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card_two:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">2 · Luck</div>
                <h3 style="margin:.35rem 0;">Actual results can differ from expected results.</h3>
                Slot payouts vary. Compare actual house win with expected theoretical
                win before concluding that low earnings identify a weak machine.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with card_three:
        st.markdown(
            """
            <div class="finding">
                <div class="finding-number">3 · Context</div>
                <h3 style="margin:.35rem 0;">Location and demand are clues, not proof.</h3>
                Zone demand patterns may reflect traffic, machine mix, amenities, and
                guest behavior. Observed patterns are not causal effects.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    chart_col, claw_col = st.columns([1.28, 0.92])

    with chart_col:
        ranking_method = st.radio(
            "Compare bottom-ten machines using",
            [
                "Total actual earnings",
                "Actual earnings per active day",
                "Expected earnings per available hour",
            ],
            horizontal=True,
        )

        rank_column = {
            "Total actual earnings": "actual_house_win",
            "Actual earnings per active day": "actual_per_active_day",
            "Expected earnings per available hour": "expected_per_available_hour",
        }[ranking_method]

        bottom_ten = (
            machine_summary
            .sort_values([rank_column, "machine_id"])
            .head(10)
            .copy()
        )

        if ranking_method == "Total actual earnings":
            actual_values = bottom_ten["actual_house_win"]
            expected_values = bottom_ten["expected_house_win"]
            axis_title = "Earnings before baseline operating costs"

        elif ranking_method == "Actual earnings per active day":
            actual_values = bottom_ten["actual_per_active_day"]
            expected_values = (
                bottom_ten["expected_house_win"]
                / bottom_ten["active_days"].replace(0, np.nan)
            )
            axis_title = "Earnings per active day"

        else:
            actual_values = (
                bottom_ten["actual_house_win"]
                / bottom_ten["available_hours"].replace(0, np.nan)
            )
            expected_values = bottom_ten["expected_per_available_hour"]
            axis_title = "Earnings per available hour"

        actual_colors = [
            PURPLE if str(mid) == "M-1158" else GOLD
            for mid in bottom_ten["machine_id"]
        ]

        bottom_fig = go.Figure()

        bottom_fig.add_bar(
            y=bottom_ten["machine_id"],
            x=actual_values,
            orientation="h",
            name="Actual",
            marker_color=actual_colors,
        )

        bottom_fig.add_bar(
            y=bottom_ten["machine_id"],
            x=expected_values,
            orientation="h",
            name="Expected",
            marker_color=TEAL,
        )

        bottom_fig.update_layout(barmode="group")
        bottom_fig.update_yaxes(autorange="reversed")
        bottom_fig.update_xaxes(title=axis_title, tickprefix="$")

        chart(
            bottom_fig,
            "The bottom 10 changes when exposure is considered",
            "bottom_ten_chart",
            height=490,
        )

        st.caption(
            "M-1158 is purple because its actual-versus-expected screening gap is unusually negative. That supports inspection—not immediate replacement."
        )

    with claw_col:
        raw_bottom = (
            machine_summary
            .sort_values("actual_house_win")
            .head(10)["machine_id"]
            .astype(str)
            .tolist()
        )

        capsules = raw_bottom[:4]

        while len(capsules) < 4:
            capsules.append("ACEIQ")

        animation_class = ""

        if st.session_state.claw_machine_id:
            animation_class = st.session_state.claw_animation_mode

        prize_html = ""

        if st.session_state.claw_machine_id:
            prize_html = (
                '<div class="claw-carried-prize">'
                + html.escape(str(st.session_state.claw_machine_id))
                + "</div>"
            )

        cabinet_html = (
            '<div class="claw-cabinet '
            + animation_class
            + '">'
            + '<div class="claw-neon">✦ THE EVIDENCE CLAW ✦</div>'
            + '<div class="claw-glass">'
            + '<div class="claw-rail"></div>'
            + '<div class="claw-carriage">'
            + '<div class="claw-cable"></div>'
            + '<div class="claw-arm">'
            + '<div class="prong left"></div>'
            + '<div class="prong right"></div>'
            + '</div>'
            + prize_html
            + '</div>'
            + '<div class="capsule one">' + html.escape(capsules[0]) + '</div>'
            + '<div class="capsule two">' + html.escape(capsules[1]) + '</div>'
            + '<div class="capsule three">' + html.escape(capsules[2]) + '</div>'
            + '<div class="capsule four">' + html.escape(capsules[3]) + '</div>'
            + '</div>'
            + '<div class="claw-instructions">'
            + "Pick a machine from the GM's raw bottom-ten list, then reveal why "
            + "low total earnings may not justify replacement."
            + '</div>'
            + '</div>'
        )

        st.markdown(cabinet_html, unsafe_allow_html=True)

        if st.button(
            "🕹 Drop the Evidence Claw",
            type="primary",
            use_container_width=True,
        ):
            choices = [
                machine_id
                for machine_id in raw_bottom
                if machine_id != st.session_state.claw_machine_id
            ]

            if not choices:
                choices = raw_bottom

            rng = np.random.default_rng(
                2025 + st.session_state.claw_count
            )

            selected = rng.choice(choices)

            st.session_state.claw_machine_id = selected
            st.session_state.selected_machine_id = selected
            st.session_state.claw_count += 1

            st.session_state.claw_animation_mode = (
                "claw-run-b"
                if st.session_state.claw_animation_mode == "claw-run-a"
                else "claw-run-a"
            )

            st.rerun()

        if st.session_state.claw_machine_id:
            claw_machine = (
                machine_summary
                .set_index("machine_id")
                .loc[st.session_state.claw_machine_id]
                .copy()
            )

            rec_title, rec_text, rec_color = recommendation_for_machine(
                claw_machine
            )

            st.markdown(
                f"""
                <div class="machine-card" style="border-left:5px solid {rec_color};">
                    <div class="eyebrow">Claw result</div>
                    <h3 style="margin:.18rem 0;">♠ {st.session_state.claw_machine_id}</h3>
                    <strong>Raw result:</strong> bottom-ten total earnings.<br><br>
                    Active days: <strong>{int(claw_machine["active_days"])}</strong><br>
                    Availability: <strong>{pct(claw_machine["availability_rate"])}</strong><br>
                    Downtime: <strong>{claw_machine["downtime_hours"]:.1f} h</strong><br>
                    Actual − expected: <strong>{money(claw_machine["actual_minus_expected"])}</strong><br><br>
                    <strong>{rec_title}</strong><br>
                    {rec_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    demand_col, explanation_col = st.columns([1.15, 0.95])

    with demand_col:
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

        monthly["wagers_per_available_hour"] = (
            monthly["wagers"]
            / monthly["available_hours"].replace(0, np.nan)
        )

        demand_fig = px.line(
            monthly,
            x="month",
            y="wagers_per_available_hour",
            markers=True,
            color_discrete_sequence=[GOLD],
            labels={
                "month": "Month",
                "wagers_per_available_hour": "Wagers per available machine-hour",
            },
        )

        demand_fig.update_traces(
            line=dict(width=4),
            marker=dict(size=9),
        )

        demand_fig.update_yaxes(tickprefix="$")

        chart(
            demand_fig,
            "Demand softened after the early-year peak",
            "demand_chart",
            height=380,
        )

    with explanation_col:
        peak = monthly.loc[
            monthly["wagers_per_available_hour"].idxmax()
        ]
        latest = monthly.iloc[-1]

        st.markdown(
            f"""
            <div class="machine-card">
                <div class="eyebrow">So what?</div>
                <h3 style="margin:.3rem 0;">Demand changed after the peak.</h3>
                Peak visible demand was <strong>{peak["month"]}</strong> at
                <strong>{money(peak["wagers_per_available_hour"])}</strong>
                per available machine-hour.<br><br>
                The latest visible month was <strong>{latest["month"]}</strong>
                at <strong>{money(latest["wagers_per_available_hour"])}</strong>.<br><br>
                This supports staffing and promotion planning. It does not prove a
                specific event or zone caused the change.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="success">
            <strong>Official July decision:</strong> No shortlisted spending portfolio
            beats $0 over the current 30-day model horizon. Preserve budget, inspect
            M-1158 as a learning action if operationally justified, and evaluate future
            interventions using comparison groups.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# INVESTIGATE PAGE
# =============================================================================

elif page == "Investigate":
    section_header(
        "Machine Investigation",
        "Luck, location, downtime, or persistent gap?",
        "Inspect one machine at a time before recommending maintenance, inspection, relocation, replacement evaluation, or monitoring.",
    )

    filters = st.columns(3)
    pool = machine_summary.copy()

    with filters[0]:
        zone_filter = st.selectbox(
            "Zone",
            ["All zones"]
            + sorted(pool["zone_name"].dropna().astype(str).unique()),
        )

    if zone_filter != "All zones":
        pool = pool[
            pool["zone_name"].astype(str) == zone_filter
        ]

    with filters[1]:
        bank_filter = st.selectbox(
            "Bank",
            ["All banks"]
            + sorted(pool["bank_id"].dropna().astype(str).unique()),
        )

    if bank_filter != "All banks":
        pool = pool[
            pool["bank_id"].astype(str) == bank_filter
        ]

    with filters[2]:
        manufacturer_filter = st.selectbox(
            "Manufacturer",
            ["All manufacturers"]
            + sorted(pool["manufacturer"].dropna().astype(str).unique()),
        )

    if manufacturer_filter != "All manufacturers":
        pool = pool[
            pool["manufacturer"].astype(str)
            == manufacturer_filter
        ]

    options = sorted(pool["machine_id"].astype(str).tolist())

    if not options:
        st.warning("No machines match these filters.")
        st.stop()

    default_index = (
        options.index(st.session_state.selected_machine_id)
        if st.session_state.selected_machine_id in options
        else 0
    )

    selected_machine_id = st.selectbox(
        "Select machine",
        options,
        index=default_index,
    )

    st.session_state.selected_machine_id = selected_machine_id

    machine = (
        machine_summary
        .set_index("machine_id")
        .loc[selected_machine_id]
        .copy()
    )

    machine["machine_id"] = selected_machine_id

    rec_title, rec_text, rec_color = recommendation_for_machine(machine)

    st.markdown(
        f"""
        <div class="machine-card" style="border-left:5px solid {rec_color};">
            <div class="eyebrow">Machine conclusion</div>
            <h2 style="margin:.16rem 0;">♠ {selected_machine_id}</h2>
            <span class="status-pill"
                style="color:{rec_color};background:{rec_color}22;border:1px solid {rec_color}66;">
                {machine_category(machine)}
            </span>
            <div style="margin-top:.7rem;color:#D8E1E5;">
                <strong>{rec_title}</strong><br>
                {rec_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)

    metrics[0].metric(
        "Exposure",
        f"{int(machine['active_days'])} active days",
    )

    metrics[1].metric(
        "Availability",
        pct(machine["availability_rate"]),
    )

    metrics[2].metric(
        "Actual − expected",
        money(machine["actual_minus_expected"]),
    )

    standardized_gap = machine.get("standardized_gap", np.nan)

    metrics[3].metric(
        "Payout-gap screening",
        f"{standardized_gap:.2f}"
        if pd.notna(standardized_gap)
        else "—",
    )

    selected_daily = (
        filtered_daily[
            filtered_daily["machine_id"].astype(str)
            == selected_machine_id
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

    selected_daily["daily_availability"] = (
        selected_daily["available_hours"]
        / selected_daily["scheduled_hours"].replace(0, np.nan)
    )

    left, right = st.columns(2)

    with left:
        actual_fig = go.Figure()

        actual_fig.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_actual"],
            name="Cumulative actual",
            line=dict(color=GOLD, width=3),
        )

        actual_fig.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["cumulative_expected"],
            name="Cumulative expected",
            line=dict(color=TEAL, width=3),
        )

        actual_fig.update_yaxes(
            title="Cumulative earnings",
            tickprefix="$",
        )

        chart(
            actual_fig,
            "Did the actual-versus-expected gap persist?",
            "machine_actual_expected",
            height=420,
        )

    with right:
        availability_fig = go.Figure()

        availability_fig.add_bar(
            x=selected_daily["gaming_date"],
            y=selected_daily["daily_availability"],
            name="Availability",
            marker_color=TEAL,
            yaxis="y",
        )

        availability_fig.add_scatter(
            x=selected_daily["gaming_date"],
            y=selected_daily["down_hours"],
            name="Downtime hours",
            line=dict(color=ORANGE, width=2),
            yaxis="y2",
        )

        availability_fig.update_layout(
            yaxis=dict(
                title="Availability",
                tickformat=".0%",
                range=[0, 1.05],
            ),
            yaxis2=dict(
                title="Downtime hours",
                overlaying="y",
                side="right",
            ),
        )

        chart(
            availability_fig,
            "Was availability enough to explain performance?",
            "machine_availability",
            height=420,
        )

    peers = machine_summary[
        machine_summary["theme"].astype(str)
        == str(machine.get("theme", ""))
    ].copy()

    peer_title = "Same-theme peer context"

    if len(peers) < 2:
        peers = machine_summary[
            machine_summary["zone_name"].astype(str)
            == str(machine.get("zone_name", ""))
        ].copy()

        peer_title = "Same-zone peer context"

    peers = peers.sort_values(
        "expected_per_available_hour",
        ascending=False,
    )

    peer_fig = px.bar(
        peers.head(12),
        x="machine_id",
        y="expected_per_available_hour",
        color="machine_id",
        labels={
            "machine_id": "Machine",
            "expected_per_available_hour": "Expected earnings per available hour",
        },
        color_discrete_sequence=[GOLD, TEAL, PURPLE, ORANGE],
    )

    peer_fig.update_layout(showlegend=False)
    peer_fig.update_yaxes(tickprefix="$")

    chart(
        peer_fig,
        peer_title,
        "machine_peer_context",
        height=390,
    )

    st.markdown(
        """
        <div class="warning">
            <strong>Interpretation guardrail:</strong> Peer and location comparisons
            are descriptive. They do not fully adjust for denomination, machine mix,
            occupancy, guest mix, or every floor condition. A payout gap is an
            inspection lead—not proof of defect or wrongdoing.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Open detailed machine evidence"):
        st.dataframe(
            machine_summary.sort_values("actual_house_win"),
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
        "A simple validated time-series model for planning.",
        "The model uses a time-based holdout rather than a random split.",
    )

    forecast = report["forecast"]

    st.markdown(
        """
        <div class="machine-card">
            <div class="eyebrow">Validation timeline</div>
            <h3 style="margin:.3rem 0;">January–April → Train · May–June → Holdout · July → Planning</h3>
            Both models were trained on January–April and evaluated only on May–June.
            Future actual weather, tourism revisions, and May–June outcomes were not
            used to fit the January–April model.
        </div>
        """,
        unsafe_allow_html=True,
    )

    metrics = st.columns(4)

    metrics[0].metric(
        "Weekday model MAE",
        money(forecast["weekday_mae"]),
    )

    metrics[1].metric(
        "Constant baseline MAE",
        money(forecast["constant_mae"]),
    )

    metrics[2].metric(
        "Holdout improvement",
        pct(forecast["improvement_pct"]),
    )

    metrics[3].metric(
        "July planning baseline",
        money(forecast["july_refit_baseline_wagers"]),
    )

    validation = pd.DataFrame(forecast["test_rows"])
    validation["gaming_date"] = pd.to_datetime(
        validation["gaming_date"]
    )

    forecast_fig = go.Figure()

    forecast_fig.add_scatter(
        x=validation["gaming_date"],
        y=validation["coin_in_usd"],
        name="Observed daily wagers",
        line=dict(color=GOLD, width=3),
    )

    forecast_fig.add_scatter(
        x=validation["gaming_date"],
        y=validation["weekday_prediction"],
        name="Weekday model",
        line=dict(color=TEAL, width=2.5),
    )

    forecast_fig.add_scatter(
        x=validation["gaming_date"],
        y=validation["constant_prediction"],
        name="Constant baseline",
        line=dict(color=PURPLE, width=2, dash="dot"),
    )

    forecast_fig.update_yaxes(
        title="Daily coin-in / wagers",
        tickprefix="$",
    )

    chart(
        forecast_fig,
        "The weekday model tracks holdout demand better than a flat average",
        "forecast_chart",
        height=500,
    )

    st.markdown(
        """
        <div class="success">
            <strong>Decision implication:</strong> The weekday pattern supports July
            staffing and promotion planning better than assuming every day follows a
            constant average. July remains a planning scenario—not observed performance.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# GUEST & LOYALTY INSIGHTS
# =============================================================================

elif page == "Guest & Loyalty Insights":
    section_header(
        "Guest & Loyalty Insights",
        "Tracked-player outcomes and comp economics.",
        "These are descriptive loyalty-card insights, not the entire casino population.",
    )

    st.markdown(
        """
        <div class="warning">
            <strong>Ethical guardrail:</strong> Tracked/card-based data is not the
            full casino population. Do not use loss behavior to target guests or
            encourage harmful gambling. Any comp test should be ethical, randomized,
            opt-in where appropriate, and focused on non-gaming or hospitality value.
        </div>
        """,
        unsafe_allow_html=True,
    )

    player = report["players"]

    metrics = st.columns(5)

    metrics[0].metric(
        "Tracked players",
        f"{player['tracked_players']:,}",
    )

    metrics[1].metric(
        "Tracked wager coverage",
        pct(player["tracked_wager_coverage"]),
    )

    metrics[2].metric(
        "Tracked wagers",
        money(player["tracked_wagers"]),
    )

    metrics[3].metric(
        "Tracked payouts",
        money(player["tracked_payouts"]),
    )

    metrics[4].metric(
        "Tracked player net",
        money(player["player_net"]),
    )

    active_months = [
        month
        for month in sorted(guests["period_month"].astype(str).unique())
        if start_date.strftime("%Y-%m")
        <= month
        <= end_date.strftime("%Y-%m")
    ]

    guest_data = guests[
        guests["period_month"].astype(str).isin(active_months)
    ].copy()

    grouping = st.selectbox(
        "Compare tracked guest groups by",
        ["home_region", "age_band"],
        format_func=lambda value: value.replace("_", " ").title(),
    )

    grouped_guests = (
        guest_data.groupby(grouping, as_index=False)[
            ["wagers", "payouts", "player_net", "comp_cost"]
        ]
        .sum()
        .sort_values("wagers", ascending=False)
    )

    guest_fig = px.bar(
        grouped_guests,
        x=grouping,
        y="wagers",
        color="player_net",
        color_continuous_scale=[
            [0.0, RED],
            [0.5, GOLD],
            [1.0, TEAL],
        ],
        labels={
            grouping: grouping.replace("_", " ").title(),
            "wagers": "Tracked wagers",
            "player_net": "Tracked player net",
        },
    )

    guest_fig.update_yaxes(tickprefix="$")

    chart(
        guest_fig,
        f"Tracked wagers by {grouping.replace('_', ' ')}",
        "guest_group_chart",
        height=420,
    )

    loyalty = pd.DataFrame(report.get("loyalty", []))

    if not loyalty.empty:
        loyalty = loyalty[
            loyalty["gaming_month"].astype(str).between(
                start_date.strftime("%Y-%m"),
                end_date.strftime("%Y-%m"),
            )
        ]

    if not loyalty.empty:
        loyalty_fig = px.line(
            loyalty,
            x="gaming_month",
            y="points_per_face_dollar",
            markers=True,
            color_discrete_sequence=[GOLD],
            labels={
                "gaming_month": "Month",
                "points_per_face_dollar": (
                    "Redeemed points per $1 face value"
                ),
            },
        )

        loyalty_fig.update_traces(
            line=dict(width=3),
            marker=dict(size=9),
        )

        chart(
            loyalty_fig,
            "Observed comp redemption economics over time",
            "loyalty_chart",
            height=380,
        )


# =============================================================================
# METHODS & EVIDENCE
# =============================================================================

else:
    section_header(
        "Methods & Evidence",
        "Trace recommendations back to data, assumptions, and limitations.",
        "Detailed evidence is stored here so decision pages stay clear and readable.",
    )

    machine_tab, demand_tab, decision_tab, download_tab = st.tabs(
        [
            "Machine method",
            "Downtime & demand",
            "Official decision model",
            "Downloads & disclosure",
        ]
    )

    with machine_tab:
        st.markdown(
            """
            <div class="warning">
                <strong>Actual earnings:</strong> coin-in − payout.<br>
                <strong>Expected/theoretical earnings:</strong> coin-in ×
                (1 − configured RTP).<br>
                <strong>Actual minus expected:</strong> actual earnings − expected earnings.<br><br>
                Machine comparisons use active days, available hours, downtime,
                expected earnings per available hour, and payout-variance screening.
                An unusual payout pattern is an inspection lead—not proof of fraud,
                cheating, tampering, malfunction, or wrongdoing.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="success">
                <strong>M-1158:</strong> Its actual-versus-expected gap is unusually
                negative while downtime is low relative to the gap. The appropriate
                next step is to inspect configuration and meters first—not immediate replacement.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with demand_tab:
        metrics = st.columns(3)

        metrics[0].metric(
            "Selected-period downtime hours",
            f"{filtered_daily['down_hours'].sum():,.0f}",
        )

        metrics[1].metric(
            "Midpoint wagering opportunity",
            money(filtered_daily["missed_wagers_mid"].sum()),
        )

        metrics[2].metric(
            "Midpoint expected-earnings opportunity",
            money(filtered_daily["missed_theo_mid"].sum()),
        )

        st.markdown(
            """
            <div class="warning">
                Downtime opportunity uses historical machine-by-weekday operating rates.
                It is historical opportunity—not proven net floor loss or guaranteed
                recoverable revenue. Customers may have played another machine.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with decision_tab:
        portfolios = pd.DataFrame(report["simulation"]["portfolios"])
        recommendation = report["simulation"]["recommended"]

        st.markdown(
            """
            <div class="hero-answer">
                <div class="eyebrow" style="color:#69D6CB;">Official precomputed result</div>
                <h2>Keep Budget ranks first under current short-horizon assumptions.</h2>
                This does not prove every intervention is bad forever. Inspections and
                controlled pilots can provide information value beyond the 30-day model.
            </div>
            """,
            unsafe_allow_html=True,
        )

        metrics = st.columns(4)

        metrics[0].metric(
            "Shared scenarios",
            f"{report['simulation']['scenarios']:,}",
        )

        metrics[1].metric(
            "Feasible portfolios",
            f"{report['simulation']['feasible_portfolios']:,}",
        )

        metrics[2].metric(
            "Recommended spend",
            money(recommendation["cost"]),
        )

        metrics[3].metric(
            "Expected modeled net benefit",
            money(recommendation["mean_net"]),
        )

        with st.expander("Open official portfolio scenarios"):
            st.dataframe(
                portfolios,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Open official action catalog"):
            st.dataframe(
                pd.DataFrame(report["action_catalog"]),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("#### Official model limitations")

        for limitation in report["simulation"]["limitations"]:
            st.write(f"• {limitation}")

    with download_tab:
        download_csv(
            machine_summary,
            "aceiq_selected_period_machine_diagnostics.csv",
            "Download machine diagnostics CSV",
        )

        download_csv(
            zone_summary,
            "aceiq_selected_period_zone_evidence.csv",
            "Download zone evidence CSV",
        )

        download_csv(
            bank_summary,
            "aceiq_selected_period_bank_evidence.csv",
            "Download bank evidence CSV",
        )

        download_csv(
            pd.DataFrame(report["simulation"]["portfolios"]),
            "aceiq_official_portfolio_scenarios.csv",
            "Download official portfolio scenarios CSV",
        )

        with st.expander("AI-use disclosure"):
            st.write(
                "AI tools were used for coding assistance, UI ideation, and writing support. Numerical claims and analytical logic were checked against supplied synthetic-data outputs. No AI model made final unverified numerical conclusions."
            )


# =============================================================================
# FOOTER
# =============================================================================

st.markdown(
    """
    <div class="footer">
        ACEIQ · THE GILDED ACE · Synthetic Dashboard Royale data only ·
        Modeled scenarios support decisions under stated assumptions; they do not prove causality.
    </div>
    """,
    unsafe_allow_html=True,
)