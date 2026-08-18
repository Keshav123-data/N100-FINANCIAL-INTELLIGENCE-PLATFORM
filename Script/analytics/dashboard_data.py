import pandas as pd
import numpy as np
from pathlib import Path


# ======================================================================
# SPRINT 5 — DAY 35
# MASTER DASHBOARD DATA INTEGRATION
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"

CASHFLOW_FILE = OUTPUT_DIR / "cashflow_dashboard_dataset.csv"
HEALTH_FILE = OUTPUT_DIR / "financial_health_dashboard_dataset.csv"
VALUATION_FILE = OUTPUT_DIR / "valuation_dashboard_dataset.csv"

MASTER_FILE = OUTPUT_DIR / "master_dashboard_dataset.csv"
EXCEL_FILE = OUTPUT_DIR / "master_dashboard.xlsx"


# ======================================================================
# HELPERS
# ======================================================================

def clean_company_id(df):
    """Standardize company IDs."""
    df = df.copy()

    if "company_id" not in df.columns:
        raise ValueError("company_id column missing")

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df


def clean_text_columns(df):
    """Clean text fields without changing business values."""
    df = df.copy()

    for col in ["company_name", "sector", "sub_sector"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )

    return df


def numeric_columns(df, columns):
    """Convert available columns to numeric."""
    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ======================================================================
# LOAD DATA
# ======================================================================

def load_data():

    print()
    print("=" * 70)
    print("LOADING DAY 31–34 DASHBOARD DATASETS")
    print("=" * 70)

    required_files = [
        CASHFLOW_FILE,
        HEALTH_FILE,
        VALUATION_FILE,
    ]

    for file in required_files:
        if not file.exists():
            raise FileNotFoundError(
                f"Required file not found:\n{file}"
            )

    cashflow = pd.read_csv(CASHFLOW_FILE)
    health = pd.read_csv(HEALTH_FILE)
    valuation = pd.read_csv(VALUATION_FILE)

    print(f"Cash Flow rows      : {len(cashflow)}")
    print(f"Financial Health    : {len(health)}")
    print(f"Valuation rows      : {len(valuation)}")

    return cashflow, health, valuation


# ======================================================================
# PREPARE FINANCIAL HEALTH
# ======================================================================

def prepare_health(health):

    print()
    print("=" * 70)
    print("PREPARING FINANCIAL HEALTH DATA")
    print("=" * 70)

    health = clean_company_id(health)
    health = clean_text_columns(health)

    # --------------------------------------------------------------
    # Keep latest financial-health record per company
    # --------------------------------------------------------------

    if "year" in health.columns:

        health["year"] = pd.to_numeric(
            health["year"],
            errors="coerce"
        )

        health = (
            health
            .sort_values(
                ["company_id", "year"],
                ascending=[True, False]
            )
            .drop_duplicates(
                subset=["company_id"],
                keep="first"
            )
        )

    # --------------------------------------------------------------
    # Columns required for dashboard
    # --------------------------------------------------------------

    columns = [
        "company_id",
        "company_name",
        "sector",
        "financial_health_score",
        "health_label",
        "risk_label",
        "profitability_score",
        "leverage_score",
        "interest_coverage_score",
        "growth_score",
    ]

    available = [
        col for col in columns
        if col in health.columns
    ]

    health = health[available].copy()

    print(f"Latest health records: {len(health)}")

    return health


# ======================================================================
# PREPARE CASH FLOW
# ======================================================================

def prepare_cashflow(cashflow):

    print()
    print("=" * 70)
    print("PREPARING CASH FLOW DATA")
    print("=" * 70)

    cashflow = clean_company_id(cashflow)
    cashflow = clean_text_columns(cashflow)

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
        "cash_flow_quality_label",
    ]

    available = [
        col for col in columns
        if col in cashflow.columns
    ]

    cashflow = cashflow[available].copy()

    return cashflow


# ======================================================================
# PREPARE VALUATION
# ======================================================================

def prepare_valuation(valuation):

    print()
    print("=" * 70)
    print("PREPARING VALUATION DATA")
    print("=" * 70)

    valuation = clean_company_id(valuation)
    valuation = clean_text_columns(valuation)

    columns = [
        "company_id",
        "company_name",
        "sector",
        "sub_sector",
        "market_cap_category",
        "index_weight_pct",
        "close_price",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
        "calculated_pe",
        "calculated_pb",
        "fcf_yield_pct",
        "earnings_yield_pct",
        "dividend_yield_pct",
        "eps_growth_pct",
        "revenue_growth_pct",
        "profit_growth_pct",
        "sector_pe_median",
        "sector_pb_median",
        "sector_ev_ebitda_median",
        "pe_discount_vs_sector_pct",
        "pb_discount_vs_sector_pct",
        "ev_ebitda_discount_vs_sector_pct",
        "average_sector_discount_pct",
        "pe_score",
        "pb_score",
        "ev_ebitda_score",
        "peg_score",
        "fcf_yield_score",
        "dividend_score",
        "growth_score",
        "valuation_score",
        "growth_adjusted_score",
        "valuation_rank",
        "valuation_label",
        "valuation_interpretation",
    ]

    available = [
        col for col in columns
        if col in valuation.columns
    ]

    valuation = valuation[available].copy()

    return valuation


# ======================================================================
# BUILD MASTER DATASET
# ======================================================================

def build_master(cashflow, health, valuation):

    print()
    print("=" * 70)
    print("BUILDING MASTER DASHBOARD DATASET")
    print("=" * 70)

    # --------------------------------------------------------------
    # Prepare datasets
    # --------------------------------------------------------------

    cashflow = prepare_cashflow(cashflow)
    health = prepare_health(health)
    valuation = prepare_valuation(valuation)

    # --------------------------------------------------------------
    # Prevent duplicate keys
    # --------------------------------------------------------------

    cashflow = cashflow.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    health = health.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    valuation = valuation.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    # --------------------------------------------------------------
    # Remove duplicate metadata columns before merging
    # --------------------------------------------------------------

    health_merge = health.drop(
        columns=["company_name", "sector"],
        errors="ignore"
    )

    cashflow_merge = cashflow.drop(
        columns=["company_name", "sector"],
        errors="ignore"
    )

    valuation_merge = valuation.drop(
        columns=["company_name", "sector"],
        errors="ignore"
    )

    # --------------------------------------------------------------
    # Start with valuation dataset
    # --------------------------------------------------------------

    master = valuation.copy()

    # --------------------------------------------------------------
    # Merge Financial Health
    # --------------------------------------------------------------

    master = master.merge(
        health_merge,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Merge Cash Flow
    # --------------------------------------------------------------

    master = master.merge(
        cashflow_merge,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Ensure company metadata exists
    # --------------------------------------------------------------

    if "company_name" not in master.columns:
        master["company_name"] = np.nan

    if "sector" not in master.columns:
        master["sector"] = np.nan

    # --------------------------------------------------------------
    # Clean company names
    # --------------------------------------------------------------

    master = clean_text_columns(master)

    # --------------------------------------------------------------
    # Convert numeric fields
    # --------------------------------------------------------------

    numeric_cols = [
        "financial_health_score",
        "profitability_score",
        "leverage_score",
        "interest_coverage_score",
        "growth_score",

        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "cash_flow_quality_score",

        "index_weight_pct",
        "close_price",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
        "calculated_pe",
        "calculated_pb",
        "fcf_yield_pct",
        "earnings_yield_pct",
        "dividend_yield_pct",
        "eps_growth_pct",
        "revenue_growth_pct",
        "profit_growth_pct",
        "sector_pe_median",
        "sector_pb_median",
        "sector_ev_ebitda_median",
        "pe_discount_vs_sector_pct",
        "pb_discount_vs_sector_pct",
        "ev_ebitda_discount_vs_sector_pct",
        "average_sector_discount_pct",
        "pe_score",
        "pb_score",
        "ev_ebitda_score",
        "peg_score",
        "fcf_yield_score",
        "dividend_score",
        "growth_score",
        "valuation_score",
        "growth_adjusted_score",
        "valuation_rank",
    ]

    master = numeric_columns(
        master,
        numeric_cols
    )

    # --------------------------------------------------------------
    # Reorder columns
    # --------------------------------------------------------------

    preferred_columns = [
        "company_id",
        "company_name",
        "sector",

        # Financial Health
        "financial_health_score",
        "health_label",
        "risk_label",
        "profitability_score",
        "leverage_score",
        "interest_coverage_score",
        "growth_score",

        # Cash Flow
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
        "cash_flow_quality_label",

        # Valuation
        "sub_sector",
        "market_cap_category",
        "index_weight_pct",
        "close_price",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
        "calculated_pe",
        "calculated_pb",
        "fcf_yield_pct",
        "earnings_yield_pct",
        "dividend_yield_pct",
        "eps_growth_pct",
        "revenue_growth_pct",
        "profit_growth_pct",
        "sector_pe_median",
        "sector_pb_median",
        "sector_ev_ebitda_median",
        "pe_discount_vs_sector_pct",
        "pb_discount_vs_sector_pct",
        "ev_ebitda_discount_vs_sector_pct",
        "average_sector_discount_pct",
        "pe_score",
        "pb_score",
        "ev_ebitda_score",
        "peg_score",
        "fcf_yield_score",
        "dividend_score",
        "valuation_score",
        "growth_adjusted_score",
        "valuation_rank",
        "valuation_label",
        "valuation_interpretation",
    ]

    preferred_columns = [
        col for col in preferred_columns
        if col in master.columns
    ]

    master = master[preferred_columns]

    return master


# ======================================================================
# VALIDATION
# ======================================================================

def validate_master(master):

    print()
    print("=" * 70)
    print("DAY 35 VALIDATION")
    print("=" * 70)

    required = [
        "company_id",
        "company_name",
        "sector",
        "financial_health_score",
        "health_label",
        "risk_label",
        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "cash_flow_quality_score",
        "valuation_score",
        "valuation_label",
        "valuation_rank",
    ]

    print()
    print("Required columns:")

    missing = []

    for col in required:
        if col in master.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col}")
            missing.append(col)

    if missing:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    unique_companies = master["company_id"].nunique()
    duplicates = master["company_id"].duplicated().sum()

    print()
    print(f"Companies in output : {len(master)}")
    print(f"Unique companies    : {unique_companies}")
    print(f"Duplicate companies : {duplicates}")

    if len(master) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(master)}"
        )

    if unique_companies != 92:
        raise ValueError(
            f"Expected 92 unique companies, found {unique_companies}"
        )

    if duplicates != 0:
        raise ValueError(
            f"Duplicate companies detected: {duplicates}"
        )

    print()
    print("Sector distribution:")
    print(master["sector"].value_counts(dropna=False))

    print()
    print("Financial Health distribution:")
    print(master["health_label"].value_counts(dropna=False))

    print()
    print("Risk distribution:")
    print(master["risk_label"].value_counts(dropna=False))

    print()
    print("Valuation distribution:")
    print(master["valuation_label"].value_counts(dropna=False))

    print()
    print("Cash Flow Quality distribution:")
    print(
        master["cash_flow_quality_label"]
        .value_counts(dropna=False)
    )

    print()
    print("✓ DAY 35 VALIDATION PASSED")


# ======================================================================
# SAVE OUTPUTS
# ======================================================================

def save_outputs(master):

    print()
    print("=" * 70)
    print("SAVING DAY 35 OUTPUTS")
    print("=" * 70)

    master.to_csv(
        MASTER_FILE,
        index=False
    )

    print(f"✓ Saved: {MASTER_FILE}")
    print(f"  Rows    : {len(master)}")
    print(f"  Columns : {len(master.columns)}")

    with pd.ExcelWriter(
        EXCEL_FILE,
        engine="openpyxl"
    ) as writer:

        master.to_excel(
            writer,
            sheet_name="Master Dashboard",
            index=False
        )

        # Summary
        summary = pd.DataFrame({
            "Metric": [
                "Companies",
                "Unique Companies",
                "Columns",
                "Sectors",
                "Average Financial Health Score",
                "Average Valuation Score",
                "Companies with Cash Flow Score",
                "Risk Alerts",
                "Distress Flags",
                "Deleveraging Companies",
            ],
            "Value": [
                len(master),
                master["company_id"].nunique(),
                len(master.columns),
                master["sector"].nunique(),
                master["financial_health_score"].mean(),
                master["valuation_score"].mean(),
                master["cash_flow_quality_score"].notna().sum(),
                (master["risk_label"].isin(
                    ["High Risk", "Severe Risk"]
                )).sum(),
                master["distress_flag"].eq(True).sum()
                if "distress_flag" in master.columns
                else 0,
                master["deleveraging_flag"].eq(True).sum()
                if "deleveraging_flag" in master.columns
                else 0,
            ]
        })

        summary.to_excel(
            writer,
            sheet_name="Dashboard Summary",
            index=False
        )

        # Sector summary
        sector_summary = (
            master.groupby("sector", dropna=False)
            .agg(
                companies=("company_id", "nunique"),
                avg_health_score=(
                    "financial_health_score",
                    "mean"
                ),
                avg_valuation_score=(
                    "valuation_score",
                    "mean"
                ),
                avg_cashflow_score=(
                    "cash_flow_quality_score",
                    "mean"
                ),
            )
            .reset_index()
            .sort_values(
                "avg_health_score",
                ascending=False
            )
        )

        sector_summary.to_excel(
            writer,
            sheet_name="Sector Summary",
            index=False
        )

    print(f"✓ Saved: {EXCEL_FILE}")


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("=" * 70)
    print("SPRINT 5 — DAY 35")
    print("MASTER DASHBOARD DATA INTEGRATION")
    print("=" * 70)

    print()
    print(f"Project root : {PROJECT_ROOT}")
    print(f"Output       : {OUTPUT_DIR}")

    try:

        cashflow, health, valuation = load_data()

        master = build_master(
            cashflow,
            health,
            valuation
        )

        validate_master(master)

        save_outputs(master)

        print()
        print("=" * 70)
        print("SPRINT 5 — DAY 35 COMPLETED")
        print("=" * 70)

        print()
        print("Generated files:")
        print(f"  ✓ {MASTER_FILE}")
        print(f"  ✓ {EXCEL_FILE}")

        print()
        print(f"Companies processed : {len(master)}")
        print(f"Columns generated   : {len(master.columns)}")
        print(f"Sectors             : {master['sector'].nunique()}")

    except Exception as e:

        print()
        print("=" * 70)
        print("DAY 35 ERROR")
        print("=" * 70)

        print(
            f"{type(e).__name__} : {e}"
        )

        raise


if __name__ == "__main__":
    main()