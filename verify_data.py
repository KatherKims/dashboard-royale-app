from pathlib import Path
import json

import numpy as np
import pandas as pd

DATA_DIR = Path("data")

daily = pd.read_parquet(
    DATA_DIR / "machine_daily.parquet"
)

machines = pd.read_parquet(
    DATA_DIR / "machines.parquet"
)

property_daily = pd.read_parquet(
    DATA_DIR / "property_daily.parquet"
)

variance = pd.read_parquet(
    DATA_DIR / "daily_variance.parquet"
)

report = json.loads(
    (
        DATA_DIR / "analysis_results.json"
    ).read_text(
        encoding="utf-8"
    )
)

for dataframe in [
    daily,
    property_daily,
    variance,
]:
    dataframe["gaming_date"] = pd.to_datetime(
        dataframe["gaming_date"],
        errors="coerce",
    )

daily["machine_id"] = daily[
    "machine_id"
].astype(str)

machines["machine_id"] = machines[
    "machine_id"
].astype(str)

variance["machine_id"] = variance[
    "machine_id"
].astype(str)

print("\n" + "=" * 72)
print("ACEIQ FINAL DATA VALIDATION")
print("=" * 72)

# =============================================================================
# 1. Date range and duplicate records
# =============================================================================

print("\n1. DATE RANGE AND DUPLICATES")

print(
    "Daily date range:",
    daily["gaming_date"].min().date(),
    "to",
    daily["gaming_date"].max().date(),
)

duplicate_count = int(
    daily.duplicated(
        subset=[
            "machine_id",
            "gaming_date",
        ],
        keep=False,
    ).sum()
)

print(
    "Duplicate machine-day rows:",
    duplicate_count,
)

# =============================================================================
# 2. Availability and downtime bounds
# =============================================================================

print("\n2. AVAILABILITY BOUNDS")

invalid_hours = int(
    (
        (daily["available_hours"] < 0)
        | (daily["scheduled_hours"] < 0)
        | (
            daily["available_hours"]
            > daily["scheduled_hours"] + 0.001
        )
        | (daily["down_hours"] < 0)
    ).sum()
)

print(
    "Invalid availability/downtime rows:",
    invalid_hours,
)

# =============================================================================
# 3. Property ledger reconciliation
# =============================================================================

print("\n3. PROPERTY LEDGER RECONCILIATION")

property_difference = (
    property_daily["house_win_usd"]
    - (
        property_daily["coin_in_usd"]
        - property_daily["payout_usd"]
    )
).abs()

property_bad_days = int(
    (property_difference > 0.05).sum()
)

print(
    "Property house-win reconciliation failures:",
    property_bad_days,
)

print(
    "Maximum property reconciliation difference:",
    round(
        float(property_difference.max()),
        6,
    ),
)

# =============================================================================
# 4. Machine-day totals versus property totals
# =============================================================================

print("\n4. MACHINE-TO-PROPERTY RECONCILIATION")

machine_daily_totals = (
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
    machine_daily_totals,
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

reconciliation["maximum_difference"] = (
    reconciliation[
        [
            "coin_in_difference",
            "house_win_difference",
            "theo_difference",
        ]
    ]
    .abs()
    .max(axis=1)
)

machine_property_bad_days = int(
    (
        reconciliation["maximum_difference"]
        > 0.05
    ).sum()
)

print(
    "Unreconciled machine/property days:",
    machine_property_bad_days,
)

print(
    "Largest machine/property difference:",
    round(
        float(
            reconciliation[
                "maximum_difference"
            ].max()
        ),
        6,
    ),
)

# =============================================================================
# 5. Machine summary versus machine-day rollup
# =============================================================================

print("\n5. MACHINE SUMMARY RECONCILIATION")

machine_rollup = (
    daily.groupby(
        "machine_id",
        as_index=False,
    )
    .agg(
        daily_house_win=(
            "house_win_usd",
            "sum",
        ),
        daily_theo=(
            "theo_usd",
            "sum",
        ),
        daily_coin_in=(
            "coin_in_usd",
            "sum",
        ),
        daily_available_hours=(
            "available_hours",
            "sum",
        ),
        daily_scheduled_hours=(
            "scheduled_hours",
            "sum",
        ),
        daily_down_hours=(
            "down_hours",
            "sum",
        ),
    )
)

variance_rollup = (
    variance.groupby(
        "machine_id",
        as_index=False,
    )
    .agg(
        variance_usd2=(
            "variance_usd2",
            "sum",
        ),
    )
)

machine_rollup = machine_rollup.merge(
    variance_rollup,
    on="machine_id",
    how="left",
)

machine_compare = machines.merge(
    machine_rollup,
    on="machine_id",
    how="left",
    suffixes=(
        "_machine_summary",
        "_daily_rollup",
    ),
)

machine_compare["house_win_difference"] = (
    machine_compare["house_win_usd"]
    - machine_compare["daily_house_win"]
)

machine_compare["theo_difference"] = (
    machine_compare["theo_usd"]
    - machine_compare["daily_theo"]
)

machine_compare["coin_in_difference"] = (
    machine_compare["coin_in_usd"]
    - machine_compare["daily_coin_in"]
)

machine_compare["availability_difference"] = (
    machine_compare["available_hours"]
    - machine_compare["daily_available_hours"]
)

machine_compare["maximum_difference"] = (
    machine_compare[
        [
            "house_win_difference",
            "theo_difference",
            "coin_in_difference",
            "availability_difference",
        ]
    ]
    .abs()
    .max(axis=1)
)

machine_summary_bad = int(
    (
        machine_compare["maximum_difference"]
        > 0.05
    ).sum()
)

print(
    "Machines not reconciling to machine-day rollup:",
    machine_summary_bad,
)

print(
    "Largest machine-summary difference:",
    round(
        float(
            machine_compare[
                "maximum_difference"
            ].max()
        ),
        6,
    ),
)

# =============================================================================
# 6. Payout-gap and variance calculations
# =============================================================================

print("\n6. PAYOUT-GAP AND VARIANCE CHECKS")

machine_compare["calculated_payout_gap"] = (
    machine_compare["daily_house_win"]
    - machine_compare["daily_theo"]
)

machine_compare["payout_gap_difference"] = (
    machine_compare["payout_gap"]
    - machine_compare["calculated_payout_gap"]
)

payout_gap_bad = int(
    (
        machine_compare[
            "payout_gap_difference"
        ]
        .abs()
        > 0.05
    ).sum()
)

print(
    "Payout-gap mismatches:",
    payout_gap_bad,
)

machine_compare["calculated_payout_sd"] = np.sqrt(
    machine_compare[
        "variance_usd2_daily_rollup"
    ].clip(
        lower=0
    )
)

machine_compare["payout_sd_difference"] = (
    machine_compare["payout_sd"]
    - machine_compare["calculated_payout_sd"]
)

payout_sd_bad = int(
    (
        machine_compare[
            "payout_sd_difference"
        ]
        .abs()
        > 0.05
    ).sum()
)

print(
    "Payout-SD mismatches:",
    payout_sd_bad,
)

machine_compare["calculated_standardized_gap"] = (
    machine_compare["calculated_payout_gap"]
    / machine_compare[
        "calculated_payout_sd"
    ].replace(
        0,
        np.nan,
    )
)

machine_compare["standardized_gap_difference"] = (
    machine_compare["standardized_gap"]
    - machine_compare[
        "calculated_standardized_gap"
    ]
)

standardized_gap_bad = int(
    (
        machine_compare[
            "standardized_gap_difference"
        ]
        .abs()
        > 0.0001
    ).sum()
)

print(
    "Standardized-gap mismatches:",
    standardized_gap_bad,
)

# =============================================================================
# 7. Daily variance coverage
# =============================================================================

print("\n7. DAILY VARIANCE COVERAGE")

variance_key_check = daily.merge(
    variance[
        [
            "machine_id",
            "gaming_date",
            "variance_usd2",
        ]
    ],
    on=[
        "machine_id",
        "gaming_date",
    ],
    how="left",
)

missing_variance = int(
    variance_key_check[
        "variance_usd2"
    ].isna().sum()
)

print(
    "Machine-day records missing variance:",
    missing_variance,
)

# =============================================================================
# 8. Metadata coverage
# =============================================================================

print("\n8. METADATA COVERAGE")

missing_metadata = int(
    (
        ~daily["machine_id"].isin(
            machines["machine_id"]
        )
    ).sum()
)

print(
    "Machine-day records missing machine metadata:",
    missing_metadata,
)

# =============================================================================
# 9. Precomputed report validation
# =============================================================================

print("\n9. PRECOMPUTED REPORT CHECK")

validation = report.get("validation", {})

print(
    "Report active rows:",
    validation.get("active_rows"),
)

print(
    "Actual machine-day rows:",
    len(daily),
)

print(
    "Report ledger-reconciled flag:",
    validation.get(
        "money_and_ledger_reconciled"
    ),
)

print("\n" + "=" * 72)
print("DONE")
print("=" * 72)