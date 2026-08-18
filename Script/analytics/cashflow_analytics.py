import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# SPRINT 5 — DAY 32
# CASH FLOW ANALYTICS & DASHBOARD DATASET
# ======================================================================

print()
print("=" * 70)
print("SPRINT 5 — DAY 32")
print("CASH FLOW ANALYTICS & DASHBOARD DATASET")
print("=" * 70)


# ======================================================================
# PATHS
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INPUT_FILE = OUTPUT_DIR / "cashflow_intelligence.xlsx"

OUTPUT_FILE = OUTPUT_DIR / "cashflow_analytics.xlsx"

RANKING_FILE = OUTPUT_DIR / "cashflow_quality_ranking.csv"

SECTOR_FILE = OUTPUT_DIR / "cashflow_sector_analysis.csv"

DASHBOARD_FILE = OUTPUT_DIR / "cashflow_dashboard_dataset.csv"


# ======================================================================
# LOAD DAY 31 DATA
# ======================================================================

def load_data():

    print()
    print("=" * 70)
    print("LOADING DAY 31 CASH FLOW INTELLIGENCE")
    print("=" * 70)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Day 31 output not found: {INPUT_FILE}"
        )

    df = pd.read_excel(INPUT_FILE)

    print(f"Rows loaded    : {len(df)}")
    print(f"Columns loaded : {len(df.columns)}")

    return df


# ======================================================================
# CLEAN DATA
# ======================================================================

def clean_data(df):

    print()
    print("=" * 70)
    print("CLEANING CASH FLOW DATA")
    print("=" * 70)

    df = df.copy()

    # --------------------------------------------------------------
    # Company ID
    # --------------------------------------------------------------

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------------
    # Sector
    # --------------------------------------------------------------

    df["sector"] = (
        df["sector"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------------
    # Numeric columns
    # --------------------------------------------------------------

    numeric_columns = [
        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------------
    # Boolean columns
    # --------------------------------------------------------------

    for column in [
        "distress_flag",
        "deleveraging_flag"
    ]:

        if column in df.columns:

            df[column] = (
                df[column]
                .fillna(False)
                .astype(bool)
            )

    print("✓ Data cleaned")

    return df


# ======================================================================
# CFO QUALITY RANKING
# ======================================================================

def calculate_cfo_ranking(df):

    print()
    print("=" * 70)
    print("CALCULATING CFO QUALITY RANKING")
    print("=" * 70)

    result = df.copy()

    result["cfo_quality_rank"] = (
        result["cfo_quality_score"]
        .rank(
            ascending=False,
            method="min",
            na_option="bottom"
        )
    )

    result["cfo_quality_percentile"] = (
        result["cfo_quality_score"]
        .rank(
            ascending=True,
            pct=True
        )
        * 100
    )

    print(
        "Companies with CFO score:",
        result["cfo_quality_score"].notna().sum()
    )

    return result


# ======================================================================
# CAPEX ANALYSIS
# ======================================================================

def calculate_capex_analysis(df):

    print()
    print("=" * 70)
    print("CALCULATING CAPEX ANALYSIS")
    print("=" * 70)

    result = df.copy()

    # Lower CapEx intensity is generally less capital intensive.
    result["capex_intensity_rank"] = (
        result["capex_intensity_pct"]
        .rank(
            ascending=True,
            method="min",
            na_option="bottom"
        )
    )

    result["capex_efficiency_percentile"] = (
        result["capex_intensity_pct"]
        .rank(
            ascending=False,
            pct=True
        )
        * 100
    )

    print(
        "Companies with CapEx data:",
        result["capex_intensity_pct"].notna().sum()
    )

    return result


# ======================================================================
# FCF ANALYSIS
# ======================================================================

def calculate_fcf_analysis(df):

    print()
    print("=" * 70)
    print("CALCULATING FCF ANALYSIS")
    print("=" * 70)

    result = df.copy()

    result["fcf_cagr_rank"] = (
        result["fcf_cagr_5yr"]
        .rank(
            ascending=False,
            method="min",
            na_option="bottom"
        )
    )

    result["fcf_conversion_rank"] = (
        result["fcf_conversion_pct"]
        .rank(
            ascending=False,
            method="min",
            na_option="bottom"
        )
    )

    return result


# ======================================================================
# CAPITAL ALLOCATION SCORE
# ======================================================================

def calculate_capital_allocation_score(df):

    print()
    print("=" * 70)
    print("CALCULATING CAPITAL ALLOCATION SCORE")
    print("=" * 70)

    result = df.copy()

    allocation_score = {

        "Cash Generator": 100,

        "Reinvestor": 80,

        "Debt / Capital Raiser": 50,

        "Capital Distributor": 70,

        "Balanced": 70,

    }

    result["capital_allocation_score"] = (
        result["capital_allocation_label"]
        .map(allocation_score)
    )

    return result


# ======================================================================
# DELEVERAGING SCORE
# ======================================================================

def calculate_deleveraging_score(df):

    print()
    print("=" * 70)
    print("CALCULATING DELEVERAGING ANALYSIS")
    print("=" * 70)

    result = df.copy()

    result["deleveraging_score"] = np.where(
        result["deleveraging_flag"],
        100,
        50
    )

    print(
        "Deleveraging companies:",
        result["deleveraging_flag"].sum()
    )

    return result


# ======================================================================
# DISTRESS SCORE
# ======================================================================

def calculate_distress_score(df):

    print()
    print("=" * 70)
    print("CALCULATING DISTRESS SCORE")
    print("=" * 70)

    result = df.copy()

    result["distress_score"] = np.where(
        result["distress_flag"],
        0,
        100
    )

    print(
        "Distressed companies:",
        result["distress_flag"].sum()
    )

    return result


# ======================================================================
# OVERALL CASH FLOW QUALITY SCORE
# ======================================================================

def calculate_overall_score(df):

    print()
    print("=" * 70)
    print("CALCULATING OVERALL CASH FLOW QUALITY SCORE")
    print("=" * 70)

    result = df.copy()

    # --------------------------------------------------------------
    # Only companies having actual CFO quality data are eligible
    # for cash-flow quality scoring.
    # --------------------------------------------------------------

    eligible = result["cfo_quality_score"].notna()

    result["cash_flow_quality_score"] = np.nan

    if eligible.sum() == 0:

        result["cash_flow_quality_label"] = np.nan

        print("Companies scored: 0")

        return result

    # --------------------------------------------------------------
    # CFO QUALITY SCORE
    # --------------------------------------------------------------

    cfo_score = (
        result.loc[eligible, "cfo_quality_score"]
        .rank(
            ascending=True,
            pct=True
        )
        * 100
    )

    # --------------------------------------------------------------
    # FCF CONVERSION SCORE
    # --------------------------------------------------------------

    fcf_conversion_score = pd.Series(
        np.nan,
        index=result.index,
        dtype=float
    )

    valid_fcf_conversion = (
        eligible
        & result["fcf_conversion_pct"].notna()
    )

    if valid_fcf_conversion.any():

        fcf_conversion_score.loc[
            valid_fcf_conversion
        ] = (
            result.loc[
                valid_fcf_conversion,
                "fcf_conversion_pct"
            ]
            .rank(
                ascending=True,
                pct=True
            )
            * 100
        )

    # --------------------------------------------------------------
    # FCF CAGR SCORE
    # --------------------------------------------------------------

    fcf_growth_score = pd.Series(
        np.nan,
        index=result.index,
        dtype=float
    )

    valid_fcf_growth = (
        eligible
        & result["fcf_cagr_5yr"].notna()
    )

    if valid_fcf_growth.any():

        fcf_growth_score.loc[
            valid_fcf_growth
        ] = (
            result.loc[
                valid_fcf_growth,
                "fcf_cagr_5yr"
            ]
            .rank(
                ascending=True,
                pct=True
            )
            * 100
        )

    # --------------------------------------------------------------
    # COMBINE AVAILABLE REAL METRICS
    # --------------------------------------------------------------

    component_df = pd.DataFrame(
        {
            "cfo": cfo_score,
            "fcf_conversion": fcf_conversion_score,
            "fcf_growth": fcf_growth_score
        },
        index=result.index
    )

    # Score only companies with real CFO data.
    result.loc[eligible, "cash_flow_quality_score"] = (
        component_df.loc[eligible]
        .mean(
            axis=1,
            skipna=True
        )
    )

    # --------------------------------------------------------------
    # CAPITAL ALLOCATION CONTRIBUTION
    # --------------------------------------------------------------

    allocation_available = (
        eligible
        & result["capital_allocation_score"].notna()
        & result["cash_flow_quality_score"].notna()
    )

    result.loc[
        allocation_available,
        "cash_flow_quality_score"
    ] = (
        result.loc[
            allocation_available,
            "cash_flow_quality_score"
        ] * 0.80
        +
        result.loc[
            allocation_available,
            "capital_allocation_score"
        ] * 0.20
    )

    # --------------------------------------------------------------
    # DISTRESS PENALTY
    # --------------------------------------------------------------

    distressed = (
        eligible
        & result["distress_flag"]
        & result["cash_flow_quality_score"].notna()
    )

    result.loc[
        distressed,
        "cash_flow_quality_score"
    ] *= 0.50

    # --------------------------------------------------------------
    # QUALITY LABEL
    # --------------------------------------------------------------

    def quality_label(score):

        if pd.isna(score):
            return np.nan

        if score >= 80:
            return "Excellent"

        if score >= 65:
            return "Good"

        if score >= 50:
            return "Average"

        return "Weak"

    result["cash_flow_quality_label"] = (
        result["cash_flow_quality_score"]
        .apply(quality_label)
    )

    print(
        "Companies scored:",
        result["cash_flow_quality_score"].notna().sum()
    )

    print(
        "Companies without cash-flow score:",
        result["cash_flow_quality_score"].isna().sum()
    )

    return result


# ======================================================================
# SECTOR ANALYSIS
# ======================================================================

def calculate_sector_analysis(df):

    print()
    print("=" * 70)
    print("CALCULATING SECTOR CASH FLOW ANALYSIS")
    print("=" * 70)

    valid = df[
        df["cash_flow_quality_score"].notna()
    ].copy()

    if valid.empty:

        return pd.DataFrame(
            columns=[
                "sector",
                "companies",
                "avg_cfo_quality",
                "avg_capex_intensity",
                "avg_fcf_cagr",
                "avg_fcf_conversion",
                "deleveraging_companies",
                "distress_companies",
                "avg_cash_flow_quality_score"
            ]
        )

    sector = (
        valid
        .groupby("sector", dropna=False)
        .agg(
            companies=("company_id", "nunique"),

            avg_cfo_quality=(
                "cfo_quality_score",
                "mean"
            ),

            avg_capex_intensity=(
                "capex_intensity_pct",
                "mean"
            ),

            avg_fcf_cagr=(
                "fcf_cagr_5yr",
                "mean"
            ),

            avg_fcf_conversion=(
                "fcf_conversion_pct",
                "mean"
            ),

            deleveraging_companies=(
                "deleveraging_flag",
                "sum"
            ),

            distress_companies=(
                "distress_flag",
                "sum"
            ),

            avg_cash_flow_quality_score=(
                "cash_flow_quality_score",
                "mean"
            )
        )
        .reset_index()
    )

    sector = sector.sort_values(
        "avg_cash_flow_quality_score",
        ascending=False
    )

    print(
        "Sectors analysed:",
        len(sector)
    )

    return sector


# ======================================================================
# DASHBOARD DATASET
# ======================================================================

def create_dashboard_dataset(df):

    print()
    print("=" * 70)
    print("CREATING DASHBOARD DATASET")
    print("=" * 70)

    columns = [
        "company_id",
        "company_name",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "capital_allocation_label",
        "deleveraging_flag",
        "distress_flag",
        "cash_flow_quality_score",
        "cash_flow_quality_label"
    ]

    available = [
        column
        for column in columns
        if column in df.columns
    ]

    dashboard = df[available].copy()

    dashboard = dashboard.sort_values(
        "cash_flow_quality_score",
        ascending=False,
        na_position="last"
    )

    print(
        "Dashboard rows:",
        len(dashboard)
    )

    return dashboard


# ======================================================================
# VALIDATION
# ======================================================================

def validate(df, sector_df, dashboard_df):

    print()
    print("=" * 70)
    print("DAY 32 VALIDATION")
    print("=" * 70)

    required = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "capital_allocation_label",
        "deleveraging_flag",
        "distress_flag",
        "cash_flow_quality_score",
        "cash_flow_quality_label"
    ]

    print()
    print("Required columns:")

    for column in required:

        if column in df.columns:
            print(f"  ✓ {column}")

        else:
            print(f"  ✗ {column}")

    print()
    print("Companies in output :", df["company_id"].nunique())

    print(
        "Duplicate companies :",
        df["company_id"].duplicated().sum()
    )

    print(
        "Sectors analysed    :",
        len(sector_df)
    )

    print(
        "Dashboard rows      :",
        len(dashboard_df)
    )

    print()
    print("Cash Flow Quality distribution:")

    print(
        df["cash_flow_quality_label"]
        .value_counts(dropna=False)
    )

    print()
    print("Capital Allocation distribution:")

    print(
        df["capital_allocation_label"]
        .value_counts(dropna=False)
    )

    print()
    print("Deleveraging companies:")

    print(
        df["deleveraging_flag"].sum()
    )

    print()
    print("Distress companies:")

    print(
        df["distress_flag"].sum()
    )


# ======================================================================
# SAVE OUTPUT
# ======================================================================

def save_outputs(
    df,
    ranking_df,
    sector_df,
    dashboard_df
):

    print()
    print("=" * 70)
    print("SAVING DAY 32 OUTPUTS")
    print("=" * 70)

    # --------------------------------------------------------------
    # Excel workbook
    # --------------------------------------------------------------

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Company Analytics",
            index=False
        )

        ranking_df.to_excel(
            writer,
            sheet_name="Quality Ranking",
            index=False
        )

        sector_df.to_excel(
            writer,
            sheet_name="Sector Analysis",
            index=False
        )

        dashboard_df.to_excel(
            writer,
            sheet_name="Dashboard Dataset",
            index=False
        )

    print(f"✓ Saved: {OUTPUT_FILE}")

    # --------------------------------------------------------------
    # Ranking CSV
    # --------------------------------------------------------------

    ranking_df.to_csv(
        RANKING_FILE,
        index=False
    )

    print(f"✓ Saved: {RANKING_FILE}")

    # --------------------------------------------------------------
    # Sector CSV
    # --------------------------------------------------------------

    sector_df.to_csv(
        SECTOR_FILE,
        index=False
    )

    print(f"✓ Saved: {SECTOR_FILE}")

    # --------------------------------------------------------------
    # Dashboard CSV
    # --------------------------------------------------------------

    dashboard_df.to_csv(
        DASHBOARD_FILE,
        index=False
    )

    print(f"✓ Saved: {DASHBOARD_FILE}")


# ======================================================================
# MAIN
# ======================================================================

def main():

    try:

        df = load_data()

        df = clean_data(df)

        df = calculate_cfo_ranking(df)

        df = calculate_capex_analysis(df)

        df = calculate_fcf_analysis(df)

        df = calculate_capital_allocation_score(df)

        df = calculate_deleveraging_score(df)

        df = calculate_distress_score(df)

        df = calculate_overall_score(df)

        sector_df = calculate_sector_analysis(df)

        dashboard_df = create_dashboard_dataset(df)

        ranking_df = df[
            [
                "company_id",
                "company_name",
                "sector",
                "cash_flow_quality_score",
                "cash_flow_quality_label",
                "cfo_quality_score",
                "cfo_quality_label",
                "capex_intensity_pct",
                "capex_label",
                "fcf_cagr_5yr",
                "fcf_conversion_pct",
                "capital_allocation_label",
                "deleveraging_flag",
                "distress_flag"
            ]
        ].copy()

        ranking_df = ranking_df.sort_values(
            "cash_flow_quality_score",
            ascending=False,
            na_position="last"
        )

        validate(
            df,
            sector_df,
            dashboard_df
        )

        save_outputs(
            df,
            ranking_df,
            sector_df,
            dashboard_df
        )

        print()
        print("=" * 70)
        print("SPRINT 5 — DAY 32 COMPLETED")
        print("=" * 70)

        print()
        print("Generated files:")

        print(
            f"  ✓ {OUTPUT_FILE}"
        )

        print(
            f"  ✓ {RANKING_FILE}"
        )

        print(
            f"  ✓ {SECTOR_FILE}"
        )

        print(
            f"  ✓ {DASHBOARD_FILE}"
        )

        print()
        print(
            "Companies processed:",
            df["company_id"].nunique()
        )

        print(
            "Companies with cash-flow score:",
            df["cash_flow_quality_score"].notna().sum()
        )

        print(
            "Sectors analysed:",
            len(sector_df)
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("DAY 32 ERROR")
        print("=" * 70)

        print(
            f"{type(exc).__name__} : {exc}"
        )

        raise


if __name__ == "__main__":
    main()