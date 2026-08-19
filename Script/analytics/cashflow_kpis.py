from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
import re


# ======================================================================
# PATHS
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INTELLIGENCE_FILE = (
    OUTPUT_DIR / "cashflow_intelligence.xlsx"
)

DISTRESS_FILE = (
    OUTPUT_DIR / "distress_alerts.csv"
)


# ======================================================================
# SIMPLE CASHFLOW KPI FUNCTIONS (For Tests & Quick Calculations)
# ======================================================================

def free_cash_flow(operating_activity, investing_activity):
    """
    Free Cash Flow = Operating Activity + Investing Activity
    (Investing activity is typically negative)
    
    Returns:
        float: FCF value
    """
    if operating_activity is None or investing_activity is None:
        return None
    
    return round(operating_activity + investing_activity, 2)


def cfo_quality_score(operating_activity, net_profit):
    """
    CFO Quality Score based on operating cash flow vs net profit
    
    Returns:
        tuple: (score, label)
    """
    if operating_activity is None or net_profit is None:
        return 0, "Insufficient Data"
    
    if net_profit == 0:
        return 0, "Invalid"
    
    ratio = operating_activity / net_profit
    score = min(100, max(0, ratio * 100))
    
    if score >= 80:
        label = "High Quality"
    elif score >= 60:
        label = "Good Quality"
    elif score >= 40:
        label = "Moderate Quality"
    else:
        label = "Low Quality"
    
    return round(score, 2), label


def capex_intensity(investing_activity, sales):
    """
    CapEx Intensity = Investing Activity / Sales
    
    Returns:
        tuple: (value, label)
    """
    if investing_activity is None or sales is None:
        return None, "Insufficient Data"
    
    if sales == 0:
        return None, "Invalid"
    
    intensity = abs(investing_activity) / sales
    
    if intensity >= 0.10:
        label = "Capital Intensive"
    elif intensity >= 0.05:
        label = "Moderate CapEx"
    else:
        label = "Low CapEx"
    
    return round(intensity, 4), label


def fcf_conversion_rate(free_cash_flow, net_profit):
    """
    FCF Conversion Rate = Free Cash Flow / Net Profit * 100
    
    Returns:
        float: Conversion rate %
    """
    if free_cash_flow is None or net_profit is None:
        return None
    
    if net_profit == 0:
        return None
    
    rate = (free_cash_flow / net_profit) * 100
    
    return round(rate, 2)


def capital_allocation_pattern(operating_activity, capex, dividends_paid, debt_level):
    """
    Analyze capital allocation pattern
    
    Returns:
        dict: Pattern analysis
    """
    if operating_activity is None or capex is None:
        return {"pattern_label": "Insufficient Data"}
    
    # After CapEx, what's left?
    after_capex = operating_activity + capex  # capex is typically negative
    
    if after_capex < 0:
        pattern = "Distressed"
    elif dividends_paid and abs(dividends_paid) > after_capex * 0.3:
        pattern = "Shareholder Returns"
    elif debt_level and debt_level > 0:
        pattern = "Debt Reduction"
    else:
        pattern = "Growth Reinvestment"
    
    return {
        "pattern_label": pattern,
        "operating_activity": operating_activity,
        "capex": capex,
        "dividends": dividends_paid,
        "debt": debt_level
    }


# ======================================================================
# DATABASE
# ======================================================================

def get_connection():
    return sqlite3.connect(DATABASE_PATH)


# ======================================================================
# LOAD DATA
# ======================================================================

def load_data():

    print()
    print("=" * 70)
    print("LOADING CASH FLOW DATA")
    print("=" * 70)

    conn = get_connection()

    try:

        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            """,
            conn
        )

        cashflow = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            """,
            conn
        )

        pnl = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                sales,
                net_profit
            FROM profitandloss
            """,
            conn
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                free_cash_flow_cr,
                revenue_cagr_5yr,
                pat_cagr_5yr,
                total_debt_cr
            FROM financial_ratios
            """,
            conn
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector AS sector
            FROM sectors
            """,
            conn
        )

    finally:
        conn.close()

    # ============================================================
    # NORMALIZE FINANCIAL YEARS
    # ============================================================

    def normalize_financial_year(value):

        if pd.isna(value):
            return pd.NA

        value = str(value).strip()

        # Ignore TTM
        if value.upper() == "TTM":
            return pd.NA

        # Four-digit year anywhere in the string
        match = re.search(r"(20\d{2})", value)

        if match:
            return int(match.group(1))

        # Two-digit year such as Mar-13
        match = re.search(r"[-/](\d{2})$", value)

        if match:
            return 2000 + int(match.group(1))

        return pd.NA

    # ============================================================
    # APPLY YEAR NORMALIZATION
    # ============================================================

    cashflow["year"] = cashflow["year"].apply(
        normalize_financial_year
    )

    pnl["year"] = pnl["year"].apply(
        normalize_financial_year
    )

    ratios["year"] = ratios["year"].apply(
        normalize_financial_year
    )

    # ============================================================
    # CONVERT YEAR TO INTEGER
    # ============================================================

    for df in [cashflow, pnl, ratios]:

        df["year"] = pd.to_numeric(
            df["year"],
            errors="coerce"
        )

        df.dropna(
            subset=["year"],
            inplace=True
        )

        df["year"] = df["year"].astype(int)

    # ============================================================
    # CLEAN COMPANY IDs
    # ============================================================

    for df in [companies, cashflow, pnl, ratios, sectors]:

        if "company_id" in df.columns:

            df["company_id"] = (
                df["company_id"]
                .astype(str)
                .str.strip()
            )

    # ============================================================
    # NUMERIC CONVERSION
    # ============================================================

    cashflow_columns = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow"
    ]

    for column in cashflow_columns:

        cashflow[column] = pd.to_numeric(
            cashflow[column],
            errors="coerce"
        )

    pnl_columns = [
        "sales",
        "net_profit"
    ]

    for column in pnl_columns:

        pnl[column] = pd.to_numeric(
            pnl[column],
            errors="coerce"
        )

    ratio_columns = [
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "total_debt_cr"
    ]

    for column in ratio_columns:

        ratios[column] = pd.to_numeric(
            ratios[column],
            errors="coerce"
        )

    # ============================================================
    # CLEAN SECTORS
    # ============================================================

    sectors["sector"] = (
        sectors["sector"]
        .astype(str)
        .str.strip()
    )

    # ============================================================
    # LOADING SUMMARY
    # ============================================================

    print(f"Companies       : {len(companies)}")
    print(f"Cash Flow rows  : {len(cashflow)}")
    print(f"Profit & Loss   : {len(pnl)}")
    print(f"Financial ratios: {len(ratios)}")
    print(f"Sectors         : {len(sectors)}")

    # ============================================================
    # RETURN DATA
    # ============================================================

    return (
        companies,
        cashflow,
        pnl,
        ratios,
        sectors
    )

# ======================================================================
# CFO QUALITY
# ======================================================================

def calculate_cfo_quality(
    cashflow,
    pnl
):

    print()
    print("=" * 70)
    print("CALCULATING CFO QUALITY")
    print("=" * 70)

    df = cashflow.merge(
        pnl[
            [
                "company_id",
                "year",
                "sales",
                "net_profit"
            ]
        ],
        on=[
            "company_id",
            "year"
        ],
        how="left"
    )

    # --------------------------------------------------------------
    # CFO / PAT
    # --------------------------------------------------------------

    df["cfo_pat_ratio"] = np.where(
        df["net_profit"].abs() > 1e-9,
        df["operating_activity"] /
        df["net_profit"],
        np.nan
    )

    # Remove infinite values

    df["cfo_pat_ratio"] = (
        df["cfo_pat_ratio"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

    # --------------------------------------------------------------
    # Latest 5 years
    # --------------------------------------------------------------

    df = (
        df
        .sort_values(
            ["company_id", "year"]
        )
        .groupby("company_id", group_keys=False)
        .tail(5)
    )

    # --------------------------------------------------------------
    # Average CFO / PAT
    # --------------------------------------------------------------

    quality = (
        df
        .groupby("company_id")
        .agg(
            cfo_quality_score=(
                "cfo_pat_ratio",
                "mean"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------------
    # Labels
    # --------------------------------------------------------------

    def quality_label(value):

        if pd.isna(value):
            return "Accrual Risk"

        if value > 1.0:
            return "High Quality"

        if value >= 0.5:
            return "Moderate"

        return "Accrual Risk"

    quality["cfo_quality_label"] = (
        quality[
            "cfo_quality_score"
        ].apply(quality_label)
    )

    print(
        "CFO quality calculated for "
        f"{len(quality)} companies."
    )

    return quality, df


# ======================================================================
# CAPEX INTENSITY
# ======================================================================

def calculate_capex_intensity(
    cashflow,
    pnl
):

    print()
    print("=" * 70)
    print("CALCULATING CAPEX INTENSITY")
    print("=" * 70)

    df = cashflow.merge(
        pnl[
            [
                "company_id",
                "year",
                "sales"
            ]
        ],
        on=[
            "company_id",
            "year"
        ],
        how="left"
    )

    # --------------------------------------------------------------
    # CapEx proxy
    #
    # investing_activity is used because the database does not have
    # a separate capex column.
    # --------------------------------------------------------------

    df["capex_intensity_pct"] = np.where(
        df["sales"].abs() > 1e-9,
        (
            df["investing_activity"].abs()
            /
            df["sales"].abs()
        ) * 100,
        np.nan
    )

    # --------------------------------------------------------------
    # Latest year
    # --------------------------------------------------------------

    latest = (
        df
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------------
    # Labels
    # --------------------------------------------------------------

    def capex_label(value):

        if pd.isna(value):
            return "Unknown"

        if value < 3:
            return "Asset Light"

        if value <= 8:
            return "Moderate"

        return "Capital Intensive"

    latest["capex_label"] = (
        latest[
            "capex_intensity_pct"
        ].apply(capex_label)
    )

    result = latest[
        [
            "company_id",
            "capex_intensity_pct",
            "capex_label"
        ]
    ].copy()

    print(
        f"CapEx intensity calculated for "
        f"{len(result)} companies."
    )

    return result


# ======================================================================
# FCF METRICS
# ======================================================================

def calculate_fcf_metrics(
    cashflow,
    pnl,
    ratios
):

    print()
    print("=" * 70)
    print("CALCULATING FCF METRICS")
    print("=" * 70)

    # --------------------------------------------------------------
    # Latest ratio record
    # --------------------------------------------------------------

    latest_ratios = (
        ratios
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------------
    # Latest P&L
    # --------------------------------------------------------------

    latest_pnl = (
        pnl
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------------
    # Latest cash flow
    # --------------------------------------------------------------

    latest_cf = (
        cashflow
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    result = latest_ratios[
        [
            "company_id",
            "free_cash_flow_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "total_debt_cr"
        ]
    ].copy()

    result = result.merge(
        latest_pnl[
            [
                "company_id",
                "sales",
                "net_profit"
            ]
        ],
        on="company_id",
        how="left"
    )

    result = result.merge(
        latest_cf[
            [
                "company_id",
                "operating_activity"
            ]
        ],
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # FCF conversion
    #
    # FCF / Net Profit * 100
    # --------------------------------------------------------------

    result["fcf_conversion_pct"] = np.where(
        result["net_profit"].abs() > 1e-9,
        (
            result["free_cash_flow_cr"]
            /
            result["net_profit"]
        ) * 100,
        np.nan
    )

    result["fcf_conversion_pct"] = (
        result["fcf_conversion_pct"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
    )

    return result


# ======================================================================
# DISTRESS SIGNAL
# ======================================================================

def calculate_distress(
    cashflow,
    pnl
):

    print()
    print("=" * 70)
    print("DETECTING DISTRESS SIGNALS")
    print("=" * 70)

    latest_cf = (
        cashflow
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    latest_pnl = (
        pnl
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    result = latest_cf[
        [
            "company_id",
            "year",
            "operating_activity",
            "financing_activity"
        ]
    ].copy()

    result = result.merge(
        latest_pnl[
            [
                "company_id",
                "net_profit"
            ]
        ],
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # CFO < 0 AND CFF > 0
    # --------------------------------------------------------------

    result["distress_flag"] = (
        (
            result["operating_activity"] < 0
        )
        &
        (
            result["financing_activity"] > 0
        )
    )

    distress_count = int(
        result["distress_flag"].sum()
    )

    print(
        f"Distress signals detected: "
        f"{distress_count}"
    )

    return result


# ======================================================================
# DELEVERAGING
# ======================================================================

def calculate_deleveraging(
    cashflow,
    ratios
):

    print()
    print("=" * 70)
    print("DETECTING DELEVERAGING")
    print("=" * 70)

    df = cashflow.merge(
        ratios[
            [
                "company_id",
                "year",
                "total_debt_cr"
            ]
        ],
        on=[
            "company_id",
            "year"
        ],
        how="left"
    )

    df = df.sort_values(
        [
            "company_id",
            "year"
        ]
    )

    df["previous_debt"] = (
        df
        .groupby("company_id")[
            "total_debt_cr"
        ]
        .shift(1)
    )

    df["debt_declining"] = (
        df["total_debt_cr"]
        <
        df["previous_debt"]
    )

    # CFF < 0 + debt declining

    df["deleveraging_flag"] = (
        (
            df["financing_activity"] < 0
        )
        &
        df["debt_declining"]
    )

    latest = (
        df
        .groupby("company_id")
        .tail(1)
        [
            [
                "company_id",
                "deleveraging_flag"
            ]
        ]
        .copy()
    )

    print(
        "Deleveraging companies:",
        int(
            latest[
                "deleveraging_flag"
            ].sum()
        )
    )

    return latest


# ======================================================================
# CAPITAL ALLOCATION
# ======================================================================

def calculate_capital_allocation(
    cashflow,
    pnl
):

    print()
    print("=" * 70)
    print("CALCULATING CAPITAL ALLOCATION")
    print("=" * 70)

    df = cashflow.merge(
        pnl[
            [
                "company_id",
                "year",
                "sales",
                "net_profit"
            ]
        ],
        on=[
            "company_id",
            "year"
        ],
        how="left"
    )

    # --------------------------------------------------------------
    # FCF proxy
    # --------------------------------------------------------------

    df["fcf"] = (
        df["operating_activity"]
        +
        df["investing_activity"]
    )

    # --------------------------------------------------------------
    # Classification
    # --------------------------------------------------------------

    def classify(row):

        cfo = row["operating_activity"]
        cfi = row["investing_activity"]
        cff = row["financing_activity"]
        profit = row["net_profit"]

        if (
            cfo < 0
            and cff > 0
        ):
            return "Distress Signal"

        if (
            cfo > 0
            and cfi < 0
            and cff < 0
        ):
            return "Reinvestor"

        if (
            cfo > 0
            and cfi > 0
            and cff < 0
        ):
            return "Cash Generator"

        if (
            cfo > 0
            and cff > 0
        ):
            return "Debt / Capital Raiser"

        if (
            cfo > 0
            and cfi < 0
            and cff >= 0
        ):
            return "Growth Investor"

        if (
            cfo > 0
            and cfi >= 0
            and cff >= 0
        ):
            return "Cash Accumulator"

        if (
            cfo < 0
            and profit > 0
        ):
            return "Accrual Risk"

        return "Mixed"

    df["capital_allocation_label"] = (
        df.apply(
            classify,
            axis=1
        )
    )

    latest = (
        df
        .sort_values("year")
        .groupby("company_id")
        .tail(1)
        [
            [
                "company_id",
                "capital_allocation_label"
            ]
        ]
        .copy()
    )

    print(
        "Capital allocation classified for:",
        len(latest),
        "companies"
    )

    return latest


# ======================================================================
# MAIN INTELLIGENCE DATASET
# ======================================================================

def build_intelligence():

    (
        companies,
        cashflow,
        pnl,
        ratios,
        sectors
    ) = load_data()

    # --------------------------------------------------------------
    # CFO quality
    # --------------------------------------------------------------

    cfo_quality, cfo_history = (
        calculate_cfo_quality(
            cashflow,
            pnl
        )
    )

    # --------------------------------------------------------------
    # CapEx
    # --------------------------------------------------------------

    capex = calculate_capex_intensity(
        cashflow,
        pnl
    )

    # --------------------------------------------------------------
    # FCF
    # --------------------------------------------------------------

    fcf = calculate_fcf_metrics(
        cashflow,
        pnl,
        ratios
    )

    # --------------------------------------------------------------
    # Distress
    # --------------------------------------------------------------

    distress = calculate_distress(
        cashflow,
        pnl
    )

    # --------------------------------------------------------------
    # Deleveraging
    # --------------------------------------------------------------

    deleveraging = calculate_deleveraging(
        cashflow,
        ratios
    )

    # --------------------------------------------------------------
    # Capital allocation
    # --------------------------------------------------------------

    capital = calculate_capital_allocation(
        cashflow,
        pnl
    )

    # --------------------------------------------------------------
    # Company base
    # --------------------------------------------------------------

    result = companies[
        [
            "company_id",
            "company_name"
        ]
    ].copy()

    # --------------------------------------------------------------
    # Sector
    # --------------------------------------------------------------

    if not sectors.empty:

        sectors_clean = (
            sectors
            .drop_duplicates(
                subset=["company_id"]
            )
        )

        result = result.merge(
            sectors_clean,
            on="company_id",
            how="left"
        )

    else:

        result["sector"] = "Unknown"

    # --------------------------------------------------------------
    # Merge all intelligence
    # --------------------------------------------------------------

    result = result.merge(
        cfo_quality,
        on="company_id",
        how="left"
    )

    result = result.merge(
        capex,
        on="company_id",
        how="left"
    )

    result = result.merge(
        fcf[
            [
                "company_id",
                "free_cash_flow_cr",
                "revenue_cagr_5yr",
                "pat_cagr_5yr",
                "fcf_conversion_pct"
            ]
        ],
        on="company_id",
        how="left"
    )

    result = result.merge(
        distress[
            [
                "company_id",
                "operating_activity",
                "financing_activity",
                "net_profit",
                "distress_flag"
            ]
        ],
        on="company_id",
        how="left"
    )

    result = result.merge(
        deleveraging,
        on="company_id",
        how="left"
    )

    result = result.merge(
        capital,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Final column names
    # --------------------------------------------------------------

    result = result.rename(
        columns={
            "free_cash_flow_cr":
                "fcf_cagr_5yr"
        }
    )

    # IMPORTANT:
    # The database contains free_cash_flow_cr, but not a dedicated
    # fcf_cagr_5yr column. Therefore we preserve the requested
    # output name only as a placeholder when CAGR is unavailable.
    #
    # Better approach: calculate actual CAGR below.

    # --------------------------------------------------------------
    # Calculate actual 5-year FCF CAGR
    # --------------------------------------------------------------

    fcf_history = ratios[
        [
            "company_id",
            "year",
            "free_cash_flow_cr"
        ]
    ].copy()

    fcf_history = (
        fcf_history
        .sort_values(
            [
                "company_id",
                "year"
            ]
        )
    )

    def fcf_cagr(group):

        group = group.dropna(
            subset=["free_cash_flow_cr"]
        )

        if len(group) < 2:
            return np.nan

        start = group.iloc[0][
            "free_cash_flow_cr"
        ]

        end = group.iloc[-1][
            "free_cash_flow_cr"
        ]

        years = (
            group.iloc[-1]["year"]
            -
            group.iloc[0]["year"]
        )

        if (
            years <= 0
            or start <= 0
            or end <= 0
        ):
            return np.nan

        return (
            (
                end / start
            )
            **
            (1 / years)
            - 1
        ) * 100

    cagr_df = (
        fcf_history
        .groupby("company_id")
        .apply(
            fcf_cagr,
            include_groups=False
        )
        .reset_index(
            name="fcf_cagr_5yr"
        )
    )

    # Replace placeholder

    if "fcf_cagr_5yr" in result.columns:
        result = result.drop(
            columns=["fcf_cagr_5yr"]
        )

    result = result.merge(
        cagr_df,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Fill boolean columns
    # --------------------------------------------------------------

    result["distress_flag"] = (
        result["distress_flag"]
        .fillna(False)
        .astype(bool)
    )

    result["deleveraging_flag"] = (
        result["deleveraging_flag"]
        .fillna(False)
        .astype(bool)
    )

    # --------------------------------------------------------------
    # Round values
    # --------------------------------------------------------------

    numeric_columns = [
        "cfo_quality_score",
        "capex_intensity_pct",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "revenue_cagr_5yr",
        "pat_cagr_5yr"
    ]

    for col in numeric_columns:

        if col in result.columns:

            result[col] = pd.to_numeric(
                result[col],
                errors="coerce"
            ).round(2)

    # --------------------------------------------------------------
    # Required output order
    # --------------------------------------------------------------

    preferred_columns = [

        "company_id",
        "company_name",
        "sector",

        "cfo_quality_score",
        "cfo_quality_label",

        "capex_intensity_pct",
        "capex_label",

        "fcf_cagr_5yr",
        "fcf_conversion_pct",

        "distress_flag",
        "deleveraging_flag",

        "capital_allocation_label"
    ]

    columns = [
        c
        for c in preferred_columns
        if c in result.columns
    ]

    result = result[
        columns
    ].copy()

    return (
        result,
        distress
    )


# ======================================================================
# SAVE EXCEL
# ======================================================================

def save_intelligence(
    intelligence_df
):

    print()
    print("=" * 70)
    print("SAVING CASH FLOW INTELLIGENCE")
    print("=" * 70)

    intelligence_df.to_excel(
        INTELLIGENCE_FILE,
        index=False,
        engine="openpyxl"
    )

    print(
        f"✓ Saved: {INTELLIGENCE_FILE}"
    )

    print(
        f"  Rows: {len(intelligence_df)}"
    )

    print(
        f"  Columns: {len(intelligence_df.columns)}"
    )


# ======================================================================
# SAVE DISTRESS ALERTS
# ======================================================================

def save_distress_alerts(
    distress_df
):

    print()
    print("=" * 70)
    print("SAVING DISTRESS ALERTS")
    print("=" * 70)

    alerts = distress_df[
        distress_df["distress_flag"]
    ].copy()

    alerts = alerts[
        [
            "company_id",
            "year",
            "operating_activity",
            "financing_activity",
            "net_profit",
            "distress_flag"
        ]
    ]

    alerts.to_csv(
        DISTRESS_FILE,
        index=False
    )

    print(
        f"✓ Saved: {DISTRESS_FILE}"
    )

    print(
        f"  Alerts: {len(alerts)}"
    )

    return alerts


# ======================================================================
# VALIDATION
# ======================================================================

def validate(
    intelligence_df
):

    print()
    print("=" * 70)
    print("DAY 31 VALIDATION")
    print("=" * 70)

    company_count = (
        intelligence_df[
            "company_id"
        ]
        .nunique()
    )

    print(
        f"Companies in output : {company_count}"
    )

    required_columns = [

        "company_id",
        "sector",

        "cfo_quality_score",
        "cfo_quality_label",

        "capex_intensity_pct",
        "capex_label",

        "fcf_cagr_5yr",
        "fcf_conversion_pct",

        "distress_flag",
        "deleveraging_flag",

        "capital_allocation_label"
    ]

    print()
    print("Required columns:")

    missing = []

    for column in required_columns:

        if column in intelligence_df.columns:

            print(
                f"  ✓ {column}"
            )

        else:

            print(
                f"  ✗ {column}"
            )

            missing.append(column)

    if missing:

        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------------
    # Coverage
    # --------------------------------------------------------------

    if company_count < 92:

        print()
        print(
            f"WARNING: Expected 92 companies, "
            f"found {company_count}"
        )

    else:

        print()
        print(
            "✓ All 92 companies represented."
        )

    # --------------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------------

    duplicates = (
        intelligence_df[
            "company_id"
        ].duplicated()
        .sum()
    )

    print(
        f"Duplicate companies : {duplicates}"
    )

    if duplicates > 0:

        raise ValueError(
            "Duplicate company records detected."
        )

    # --------------------------------------------------------------
    # Labels
    # --------------------------------------------------------------

    print()
    print("CFO Quality distribution:")

    print(
        intelligence_df[
            "cfo_quality_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print("CapEx distribution:")

    print(
        intelligence_df[
            "capex_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print()
    print("Capital allocation distribution:")

    print(
        intelligence_df[
            "capital_allocation_label"
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )


# ======================================================================
# MAIN
# ======================================================================

def main():

    print()
    print("=" * 70)
    print("SPRINT 5 — DAY 31")
    print("CASH FLOW INTELLIGENCE MODULE")
    print("=" * 70)

    print()
    print(
        f"Project root : {PROJECT_ROOT}"
    )

    print(
        f"Database     : {DATABASE_PATH}"
    )

    print(
        f"Output       : {OUTPUT_DIR}"
    )

    try:

        # ----------------------------------------------------------
        # Build
        # ----------------------------------------------------------

        (
            intelligence,
            distress
        ) = build_intelligence()

        # ----------------------------------------------------------
        # Validate
        # ----------------------------------------------------------

        validate(
            intelligence
        )

        # ----------------------------------------------------------
        # Save Excel
        # ----------------------------------------------------------

        save_intelligence(
            intelligence
        )

        # ----------------------------------------------------------
        # Save distress
        # ----------------------------------------------------------

        alerts = save_distress_alerts(
            distress
        )

        # ----------------------------------------------------------
        # Preview
        # ----------------------------------------------------------

        print()
        print("=" * 70)
        print("SAMPLE CASH FLOW INTELLIGENCE")
        print("=" * 70)

        print(
            intelligence
            .head(10)
            .to_string(
                index=False
            )
        )

        # ----------------------------------------------------------
        # Final
        # ----------------------------------------------------------

        print()
        print("=" * 70)
        print("SPRINT 5 — DAY 31 COMPLETED")
        print("=" * 70)

        print()
        print("Generated files:")

        print(
            f"  ✓ {INTELLIGENCE_FILE}"
        )

        print(
            f"  ✓ {DISTRESS_FILE}"
        )

        print()
        print(
            f"Companies processed: "
            f"{len(intelligence)}"
        )

        print(
            f"Distress alerts: "
            f"{len(alerts)}"
        )

    except Exception as e:

        print()
        print("=" * 70)
        print("DAY 31 ERROR")
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            e
        )

        import traceback

        traceback.print_exc()

        raise


# ======================================================================
# COMMAND LINE
# ======================================================================

if __name__ == "__main__":
    main()