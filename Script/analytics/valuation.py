import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# SPRINT 5 — DAY 34
# VALUATION INTELLIGENCE MODULE
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

VALUATION_FILE = OUTPUT_DIR / "valuation_intelligence.xlsx"
RANKING_FILE = OUTPUT_DIR / "valuation_ranking.csv"
SECTOR_FILE = OUTPUT_DIR / "valuation_sector_analysis.csv"
DASHBOARD_FILE = OUTPUT_DIR / "valuation_dashboard_dataset.csv"


# ======================================================================
# DATABASE
# ======================================================================

def get_connection():
    return sqlite3.connect(DATABASE_PATH)


# ======================================================================
# HELPERS
# ======================================================================

def safe_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def minmax_score(series, inverse=False):
    """
    Convert a metric into a 0-100 score.

    Higher value = better by default.
    inverse=True means lower value is better.
    """
    s = pd.to_numeric(series, errors="coerce")

    if inverse:
        s = -s

    valid = s.dropna()

    if len(valid) == 0:
        return pd.Series(np.nan, index=series.index)

    min_val = valid.min()
    max_val = valid.max()

    if np.isclose(min_val, max_val):
        result = pd.Series(50.0, index=series.index)
        result[s.isna()] = np.nan
        return result

    result = ((s - min_val) / (max_val - min_val)) * 100

    return result


def valuation_label(discount_pct, valuation_score):
    """
    Classification:

    >= 20% discount  -> Undervalued
    <= -20% discount -> Overvalued
    otherwise        -> Fair Value
    """

    if pd.isna(valuation_score):
        return np.nan

    if pd.notna(discount_pct):

        if discount_pct >= 20:
            return "Undervalued"

        if discount_pct <= -20:
            return "Overvalued"

    if valuation_score >= 70:
        return "Undervalued"

    if valuation_score <= 35:
        return "Overvalued"

    return "Fair Value"


# ======================================================================
# LOAD DATA
# ======================================================================

def load_data():

    print()
    print("=" * 70)
    print("LOADING VALUATION DATA")
    print("=" * 70)

    conn = get_connection()

    try:

        companies = pd.read_sql_query(
            """
            SELECT
                id AS company_id,
                company_name,
                face_value,
                book_value,
                roe_percentage,
                roce_percentage
            FROM companies
            """,
            conn
        )

        market = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                market_cap_crore,
                enterprise_value_crore,
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield_pct
            FROM market_cap
            """,
            conn
        )

        ratios = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                earnings_per_share,
                book_value_per_share,
                free_cash_flow_cr,
                total_debt_cr,
                cash_from_operations_cr,
                revenue_cagr_5yr,
                pat_cagr_5yr,
                eps_cagr_5yr,
                composite_quality_score
            FROM financial_ratios
            """,
            conn
        )

        sectors = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector AS sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM sectors
            """,
            conn
        )

        prices = pd.read_sql_query(
            """
            SELECT
                company_id,
                date,
                close_price,
                adjusted_close
            FROM stock_prices
            """,
            conn
        )

    finally:
        conn.close()

    print(f"Companies       : {len(companies)}")
    print(f"Market records  : {len(market)}")
    print(f"Financial ratios: {len(ratios)}")
    print(f"Sectors         : {len(sectors)}")
    print(f"Stock prices    : {len(prices)}")

    return companies, market, ratios, sectors, prices


# ======================================================================
# PREPARE LATEST DATA
# ======================================================================

def prepare_latest_data(
    companies,
    market,
    ratios,
    sectors,
    prices
):

    print()
    print("=" * 70)
    print("PREPARING LATEST VALUATION DATA")
    print("=" * 70)

    # --------------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------------

    market = safe_numeric(
        market,
        [
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ],
    )

    ratios = safe_numeric(
        ratios,
        [
            "year",
            "earnings_per_share",
            "book_value_per_share",
            "free_cash_flow_cr",
            "total_debt_cr",
            "cash_from_operations_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "composite_quality_score",
        ],
    )

    prices["date"] = pd.to_datetime(
        prices["date"],
        errors="coerce"
    )

    prices["close_price"] = pd.to_numeric(
        prices["close_price"],
        errors="coerce"
    )

    prices["adjusted_close"] = pd.to_numeric(
        prices["adjusted_close"],
        errors="coerce"
    )

    # --------------------------------------------------------------
    # Latest market record per company
    # --------------------------------------------------------------

    market = market.sort_values(
        ["company_id", "year"]
    )

    latest_market = (
        market
        .drop_duplicates(
            subset=["company_id"],
            keep="last"
        )
        .copy()
    )

    # --------------------------------------------------------------
    # Latest ratio record per company
    # --------------------------------------------------------------

    ratios = ratios.sort_values(
        ["company_id", "year"]
    )

    latest_ratios = (
        ratios
        .drop_duplicates(
            subset=["company_id"],
            keep="last"
        )
        .copy()
    )

    # --------------------------------------------------------------
    # Latest stock price
    # --------------------------------------------------------------

    prices = prices.sort_values(
        ["company_id", "date"]
    )

    latest_prices = (
        prices
        .drop_duplicates(
            subset=["company_id"],
            keep="last"
        )
        .copy()
    )

    latest_prices = latest_prices[
        [
            "company_id",
            "date",
            "close_price",
            "adjusted_close",
        ]
    ]

    # --------------------------------------------------------------
    # Merge
    # --------------------------------------------------------------

    df = companies.merge(
        sectors,
        on="company_id",
        how="left"
    )

    df = df.merge(
        latest_market,
        on="company_id",
        how="left",
        suffixes=("", "_market")
    )

    df = df.merge(
        latest_ratios,
        on="company_id",
        how="left",
        suffixes=("", "_ratio")
    )

    df = df.merge(
        latest_prices,
        on="company_id",
        how="left"
    )

    print(f"Companies after merge: {len(df)}")

    return df


# ======================================================================
# CALCULATE VALUATION METRICS
# ======================================================================

def calculate_valuation_metrics(df):

    print()
    print("=" * 70)
    print("CALCULATING VALUATION METRICS")
    print("=" * 70)

    # --------------------------------------------------------------
    # P/E
    # --------------------------------------------------------------

    df["pe_valuation"] = pd.to_numeric(
        df["pe_ratio"],
        errors="coerce"
    )

    # --------------------------------------------------------------
    # P/B
    # --------------------------------------------------------------

    df["pb_valuation"] = pd.to_numeric(
        df["pb_ratio"],
        errors="coerce"
    )

    # --------------------------------------------------------------
    # EV / EBITDA
    # --------------------------------------------------------------

    df["ev_ebitda_valuation"] = pd.to_numeric(
        df["ev_ebitda"],
        errors="coerce"
    )

    # --------------------------------------------------------------
    # PEG
    # --------------------------------------------------------------

    df["peg_ratio"] = np.where(
        (
            df["pe_ratio"].notna()
            & df["eps_cagr_5yr"].notna()
            & (df["eps_cagr_5yr"] > 0)
        ),
        df["pe_ratio"] / df["eps_cagr_5yr"],
        np.nan,
    )

    # --------------------------------------------------------------
    # Price / Book using company book value
    # --------------------------------------------------------------

    df["calculated_pb"] = np.where(
        (
            df["close_price"].notna()
            & df["book_value_per_share"].notna()
            & (df["book_value_per_share"] > 0)
        ),
        df["close_price"]
        / df["book_value_per_share"],
        np.nan,
    )

    # --------------------------------------------------------------
    # Price / Earnings using price and EPS
    # --------------------------------------------------------------

    df["calculated_pe"] = np.where(
        (
            df["close_price"].notna()
            & df["earnings_per_share"].notna()
            & (df["earnings_per_share"] > 0)
        ),
        df["close_price"]
        / df["earnings_per_share"],
        np.nan,
    )

    # --------------------------------------------------------------
    # FCF yield
    #
    # FCF is in ₹ crore and market cap is ₹ crore.
    # --------------------------------------------------------------

    df["fcf_yield_pct"] = np.where(
        (
            df["free_cash_flow_cr"].notna()
            & df["market_cap_crore"].notna()
            & (df["market_cap_crore"] > 0)
        ),
        (
            df["free_cash_flow_cr"]
            / df["market_cap_crore"]
        ) * 100,
        np.nan,
    )

    # --------------------------------------------------------------
    # Earnings yield
    # --------------------------------------------------------------

    df["earnings_yield_pct"] = np.where(
        (
            df["pe_ratio"].notna()
            & (df["pe_ratio"] > 0)
        ),
        100 / df["pe_ratio"],
        np.nan,
    )

    # --------------------------------------------------------------
    # Dividend yield
    # --------------------------------------------------------------

    df["dividend_yield_pct"] = pd.to_numeric(
        df["dividend_yield_pct"],
        errors="coerce"
    )

    # --------------------------------------------------------------
    # Growth metrics
    # --------------------------------------------------------------

    df["eps_growth_pct"] = pd.to_numeric(
        df["eps_cagr_5yr"],
        errors="coerce"
    )

    df["revenue_growth_pct"] = pd.to_numeric(
        df["revenue_cagr_5yr"],
        errors="coerce"
    )

    df["profit_growth_pct"] = pd.to_numeric(
        df["pat_cagr_5yr"],
        errors="coerce"
    )

    print(
        "Companies with P/E:",
        df["pe_valuation"].notna().sum()
    )

    print(
        "Companies with P/B:",
        df["pb_valuation"].notna().sum()
    )

    print(
        "Companies with EV/EBITDA:",
        df["ev_ebitda_valuation"].notna().sum()
    )

    print(
        "Companies with PEG:",
        df["peg_ratio"].notna().sum()
    )

    print(
        "Companies with FCF yield:",
        df["fcf_yield_pct"].notna().sum()
    )

    return df


# ======================================================================
# SECTOR RELATIVE VALUATION
# ======================================================================

def calculate_sector_valuation(df):

    print()
    print("=" * 70)
    print("CALCULATING SECTOR RELATIVE VALUATION")
    print("=" * 70)

    sector_metrics = (
        df.groupby("sector", dropna=False)
        .agg(
            sector_pe_median=(
                "pe_valuation",
                "median"
            ),
            sector_pb_median=(
                "pb_valuation",
                "median"
            ),
            sector_ev_ebitda_median=(
                "ev_ebitda_valuation",
                "median"
            ),
            sector_peg_median=(
                "peg_ratio",
                "median"
            ),
            sector_fcf_yield_median=(
                "fcf_yield_pct",
                "median"
            ),
            sector_company_count=(
                "company_id",
                "count"
            ),
        )
        .reset_index()
    )

    df = df.merge(
        sector_metrics,
        on="sector",
        how="left"
    )

    # --------------------------------------------------------------
    # Discount / premium vs sector
    #
    # Positive = cheaper than sector
    # Negative = more expensive than sector
    # --------------------------------------------------------------

    df["pe_discount_vs_sector_pct"] = np.where(
        (
            df["pe_valuation"].notna()
            & df["sector_pe_median"].notna()
            & (df["sector_pe_median"] > 0)
        ),
        (
            1
            - (
                df["pe_valuation"]
                / df["sector_pe_median"]
            )
        ) * 100,
        np.nan,
    )

    df["pb_discount_vs_sector_pct"] = np.where(
        (
            df["pb_valuation"].notna()
            & df["sector_pb_median"].notna()
            & (df["sector_pb_median"] > 0)
        ),
        (
            1
            - (
                df["pb_valuation"]
                / df["sector_pb_median"]
            )
        ) * 100,
        np.nan,
    )

    df["ev_ebitda_discount_vs_sector_pct"] = np.where(
        (
            df["ev_ebitda_valuation"].notna()
            & df["sector_ev_ebitda_median"].notna()
            & (df["sector_ev_ebitda_median"] > 0)
        ),
        (
            1
            - (
                df["ev_ebitda_valuation"]
                / df["sector_ev_ebitda_median"]
            )
        ) * 100,
        np.nan,
    )

    print(
        "Sectors analysed:",
        sector_metrics["sector"].nunique()
    )

    return df, sector_metrics


# ======================================================================
# VALUATION SCORE
# ======================================================================

def calculate_valuation_score(df):

    print()
    print("=" * 70)
    print("CALCULATING VALUATION SCORE")
    print("=" * 70)

    # --------------------------------------------------------------
    # Individual valuation scores
    # Lower valuation multiple = better
    # --------------------------------------------------------------

    df["pe_score"] = minmax_score(
        df["pe_valuation"],
        inverse=True
    )

    df["pb_score"] = minmax_score(
        df["pb_valuation"],
        inverse=True
    )

    df["ev_ebitda_score"] = minmax_score(
        df["ev_ebitda_valuation"],
        inverse=True
    )

    df["peg_score"] = minmax_score(
        df["peg_ratio"],
        inverse=True
    )

    # Higher FCF yield = better
    df["fcf_yield_score"] = minmax_score(
        df["fcf_yield_pct"],
        inverse=False
    )

    # Higher dividend yield = better
    df["dividend_score"] = minmax_score(
        df["dividend_yield_pct"],
        inverse=False
    )

    # Higher EPS growth = better
    df["growth_score"] = minmax_score(
        df["eps_growth_pct"],
        inverse=False
    )

    # --------------------------------------------------------------
    # Weighted valuation score
    #
    # P/E          25%
    # P/B          15%
    # EV/EBITDA    20%
    # PEG          15%
    # FCF Yield    10%
    # Dividend      5%
    # Growth       10%
    # --------------------------------------------------------------

    components = pd.DataFrame(
        {
            "pe": df["pe_score"],
            "pb": df["pb_score"],
            "ev_ebitda": df["ev_ebitda_score"],
            "peg": df["peg_score"],
            "fcf": df["fcf_yield_score"],
            "dividend": df["dividend_score"],
            "growth": df["growth_score"],
        }
    )

    weights = pd.Series(
        {
            "pe": 0.25,
            "pb": 0.15,
            "ev_ebitda": 0.20,
            "peg": 0.15,
            "fcf": 0.10,
            "dividend": 0.05,
            "growth": 0.10,
        }
    )

    weighted_sum = components.mul(
        weights,
        axis=1
    ).sum(axis=1)

    available_weight = (
        components.notna()
        .mul(weights, axis=1)
        .sum(axis=1)
    )

    df["valuation_score"] = np.where(
        available_weight > 0,
        weighted_sum / available_weight,
        np.nan,
    )

    # --------------------------------------------------------------
    # Growth-adjusted valuation score
    # --------------------------------------------------------------

    df["growth_adjusted_score"] = (
        df["valuation_score"] * 0.70
        + df["growth_score"] * 0.30
    )

    print(
        "Companies with valuation score:",
        df["valuation_score"].notna().sum()
    )

    return df


# ======================================================================
# VALUATION CLASSIFICATION
# ======================================================================

def classify_valuation(df):

    print()
    print("=" * 70)
    print("CLASSIFYING VALUATION")
    print("=" * 70)

    discount_columns = [
        "pe_discount_vs_sector_pct",
        "pb_discount_vs_sector_pct",
        "ev_ebitda_discount_vs_sector_pct",
    ]

    df["average_sector_discount_pct"] = (
        df[discount_columns]
        .mean(axis=1, skipna=True)
    )

    df["valuation_label"] = df.apply(
        lambda row: valuation_label(
            row["average_sector_discount_pct"],
            row["valuation_score"],
        ),
        axis=1,
    )

    df["valuation_rank"] = (
        df["valuation_score"]
        .rank(
            ascending=False,
            method="min"
        )
    )

    # --------------------------------------------------------------
    # Investor interpretation
    # --------------------------------------------------------------

    def interpretation(row):

        label = row["valuation_label"]

        if label == "Undervalued":
            return "Attractive valuation relative to peers"

        if label == "Overvalued":
            return "Premium valuation relative to peers"

        if label == "Fair Value":
            return "Reasonably valued relative to peers"

        return np.nan

    df["valuation_interpretation"] = df.apply(
        interpretation,
        axis=1
    )

    counts = df["valuation_label"].value_counts(
        dropna=False
    )

    print("\nValuation distribution:")
    print(counts)

    return df


# ======================================================================
# SECTOR ANALYSIS
# ======================================================================

def build_sector_analysis(df):

    print()
    print("=" * 70)
    print("BUILDING SECTOR VALUATION ANALYSIS")
    print("=" * 70)

    sector = (
        df.groupby("sector", dropna=False)
        .agg(
            companies=(
                "company_id",
                "count"
            ),
            median_pe=(
                "pe_valuation",
                "median"
            ),
            median_pb=(
                "pb_valuation",
                "median"
            ),
            median_ev_ebitda=(
                "ev_ebitda_valuation",
                "median"
            ),
            median_peg=(
                "peg_ratio",
                "median"
            ),
            median_fcf_yield=(
                "fcf_yield_pct",
                "median"
            ),
            median_eps_growth=(
                "eps_growth_pct",
                "median"
            ),
            average_valuation_score=(
                "valuation_score",
                "mean"
            ),
            undervalued_count=(
                "valuation_label",
                lambda x: (x == "Undervalued").sum()
            ),
            fair_value_count=(
                "valuation_label",
                lambda x: (x == "Fair Value").sum()
            ),
            overvalued_count=(
                "valuation_label",
                lambda x: (x == "Overvalued").sum()
            ),
        )
        .reset_index()
    )

    sector["sector_valuation_label"] = np.select(
        [
            sector["average_valuation_score"] >= 70,
            sector["average_valuation_score"] <= 35,
        ],
        [
            "Attractive",
            "Expensive",
        ],
        default="Neutral",
    )

    sector = sector.sort_values(
        "average_valuation_score",
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

def build_dashboard_dataset(df):

    print()
    print("=" * 70)
    print("CREATING VALUATION DASHBOARD DATASET")
    print("=" * 70)

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

    columns = [
        col for col in columns
        if col in df.columns
    ]

    dashboard = df[columns].copy()

    dashboard = dashboard.sort_values(
        "valuation_score",
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

def validate_output(df, sector, dashboard):

    print()
    print("=" * 70)
    print("DAY 34 VALIDATION")
    print("=" * 70)

    required_columns = [
        "company_id",
        "sector",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
        "valuation_score",
        "valuation_label",
    ]

    print("\nRequired columns:")

    for column in required_columns:

        if column in df.columns:
            print(f"  ✓ {column}")
        else:
            print(f"  ✗ {column}")

    company_count = df["company_id"].nunique()

    duplicate_count = (
        df["company_id"].duplicated().sum()
    )

    print()
    print("Companies in output :", len(df))
    print("Unique companies    :", company_count)
    print("Duplicate companies :", duplicate_count)
    print("Sectors analysed    :", len(sector))
    print("Dashboard rows      :", len(dashboard))

    print("\nValuation distribution:")

    print(
        df["valuation_label"]
        .value_counts(dropna=False)
    )

    print("\nValuation score statistics:")

    print(
        df["valuation_score"]
        .describe()
    )

    print("\nTop 10 valuation scores:")

    preview_columns = [
        "company_id",
        "company_name",
        "sector",
        "valuation_score",
        "valuation_label",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
    ]

    preview_columns = [
        c for c in preview_columns
        if c in df.columns
    ]

    print(
        df[preview_columns]
        .sort_values(
            "valuation_score",
            ascending=False
        )
        .head(10)
        .to_string(index=False)
    )


# ======================================================================
# SAVE OUTPUTS
# ======================================================================

def save_outputs(
    df,
    sector,
    dashboard
):

    print()
    print("=" * 70)
    print("SAVING DAY 34 OUTPUTS")
    print("=" * 70)

    # --------------------------------------------------------------
    # Excel
    # --------------------------------------------------------------

    with pd.ExcelWriter(
        VALUATION_FILE,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Valuation Intelligence",
            index=False
        )

        dashboard.to_excel(
            writer,
            sheet_name="Dashboard",
            index=False
        )

        sector.to_excel(
            writer,
            sheet_name="Sector Analysis",
            index=False
        )

    print(
        f"✓ Saved: {VALUATION_FILE}"
    )

    # --------------------------------------------------------------
    # Ranking
    # --------------------------------------------------------------

    ranking_columns = [
        "company_id",
        "company_name",
        "sector",
        "valuation_score",
        "growth_adjusted_score",
        "valuation_rank",
        "valuation_label",
        "pe_valuation",
        "pb_valuation",
        "ev_ebitda_valuation",
        "peg_ratio",
        "fcf_yield_pct",
        "eps_growth_pct",
        "average_sector_discount_pct",
    ]

    ranking_columns = [
        c for c in ranking_columns
        if c in df.columns
    ]

    ranking = (
        df[ranking_columns]
        .sort_values(
            "valuation_score",
            ascending=False,
            na_position="last"
        )
    )

    ranking.to_csv(
        RANKING_FILE,
        index=False
    )

    print(
        f"✓ Saved: {RANKING_FILE}"
    )

    # --------------------------------------------------------------
    # Sector
    # --------------------------------------------------------------

    sector.to_csv(
        SECTOR_FILE,
        index=False
    )

    print(
        f"✓ Saved: {SECTOR_FILE}"
    )

    # --------------------------------------------------------------
    # Dashboard
    # --------------------------------------------------------------

    dashboard.to_csv(
        DASHBOARD_FILE,
        index=False
    )

    print(
        f"✓ Saved: {DASHBOARD_FILE}"
    )


# ======================================================================
# MAIN
# ======================================================================

def main():

    print("=" * 70)
    print("SPRINT 5 — DAY 34")
    print("VALUATION INTELLIGENCE MODULE")
    print("=" * 70)

    print()
    print("Project root :", PROJECT_ROOT)
    print("Database     :", DATABASE_PATH)
    print("Output       :", OUTPUT_DIR)

    try:

        (
            companies,
            market,
            ratios,
            sectors,
            prices,
        ) = load_data()

        df = prepare_latest_data(
            companies,
            market,
            ratios,
            sectors,
            prices,
        )

        df = calculate_valuation_metrics(df)

        (
            df,
            sector_metrics,
        ) = calculate_sector_valuation(df)

        df = calculate_valuation_score(df)

        df = classify_valuation(df)

        sector_analysis = build_sector_analysis(df)

        dashboard = build_dashboard_dataset(df)

        validate_output(
            df,
            sector_analysis,
            dashboard,
        )

        save_outputs(
            df,
            sector_analysis,
            dashboard,
        )

        print()
        print("=" * 70)
        print("SPRINT 5 — DAY 34 COMPLETED")
        print("=" * 70)

        print()
        print("Generated files:")

        print(
            f"  ✓ {VALUATION_FILE}"
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
            len(df)
        )

        print(
            "Companies with valuation score:",
            df["valuation_score"].notna().sum()
        )

        print(
            "Sectors analysed:",
            sector_analysis["sector"].nunique()
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("DAY 34 ERROR")
        print("=" * 70)

        print(
            f"{type(exc).__name__} : {exc}"
        )

        raise


if __name__ == "__main__":
    main()