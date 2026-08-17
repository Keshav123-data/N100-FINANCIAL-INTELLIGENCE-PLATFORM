import sqlite3
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage,
    asset_turnover,
)

from Script.analytics.cashflow_kpis import free_cash_flow


# ============================================================
# DATABASE
# ============================================================

DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

conn = sqlite3.connect(DB_PATH)

print("=" * 80)
print("POPULATING FINANCIAL RATIOS")
print("=" * 80)


# ============================================================
# LOAD SOURCE TABLES
# ============================================================

profit = pd.read_sql(
    """
    SELECT *
    FROM profitandloss
    """,
    conn
)

balance = pd.read_sql(
    """
    SELECT *
    FROM balancesheet
    """,
    conn
)

cashflow = pd.read_sql(
    """
    SELECT *
    FROM cashflow
    """,
    conn
)

companies = pd.read_sql(
    """
    SELECT *
    FROM companies
    """,
    conn
)


# ============================================================
# CLEAN YEAR
# ============================================================

def extract_year(value):
    """
    Converts:
        Mar 2023 -> 2023
        Dec 2022 -> 2022
        2023     -> 2023
        TTM      -> NaN
    """
    if pd.isna(value):
        return np.nan

    value = str(value)

    import re

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    return np.nan


profit["year_clean"] = profit["year"].apply(extract_year)
balance["year_clean"] = balance["year"].apply(extract_year)
cashflow["year_clean"] = cashflow["year"].apply(extract_year)


# ============================================================
# REMOVE TTM FROM ANNUAL RATIO CALCULATION
# ============================================================

profit = profit[
    profit["year_clean"].notna()
].copy()

balance = balance[
    balance["year_clean"].notna()
].copy()

cashflow = cashflow[
    cashflow["year_clean"].notna()
].copy()


# ============================================================
# REMOVE DUPLICATE COMPANY/YEAR RECORDS
# ============================================================

print("\nRemoving duplicate records...")

profit = (
    profit
    .sort_values("id")
    .drop_duplicates(
        subset=["company_id", "year_clean"],
        keep="first"
    )
)

balance = (
    balance
    .sort_values("id")
    .drop_duplicates(
        subset=["company_id", "year_clean"],
        keep="first"
    )
)

cashflow = (
    cashflow
    .sort_values("id")
    .drop_duplicates(
        subset=["company_id", "year_clean"],
        keep="first"
    )
)

print("Profit & Loss rows :", len(profit))
print("Balance Sheet rows :", len(balance))
print("Cash Flow rows     :", len(cashflow))


# ============================================================
# MERGE FINANCIAL DATA
# ============================================================

df = profit.merge(
    balance,
    on=["company_id", "year_clean"],
    how="left",
    suffixes=("_pl", "_bs")
)


# ============================================================
# MERGE CASHFLOW
# ============================================================

cashflow_cols = [
    "company_id",
    "year_clean",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
]

if not cashflow.empty:

    df = df.merge(
        cashflow[cashflow_cols],
        on=["company_id", "year_clean"],
        how="left"
    )

else:

    for col in cashflow_cols[2:]:
        df[col] = np.nan


# ============================================================
# MERGE COMPANY DATA
# ============================================================

company_cols = [
    "id",
    "company_name",
    "book_value",
    "roe_percentage",
    "roce_percentage",
]

company_cols = [
    c for c in company_cols
    if c in companies.columns
]

company_df = companies[company_cols].copy()

company_df = company_df.rename(
    columns={"id": "company_id"}
)

df = df.merge(
    company_df,
    on="company_id",
    how="left"
)


# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["company_id", "year_clean"]
).reset_index(drop=True)


# ============================================================
# BASIC FINANCIAL RATIOS
# ============================================================

print("\nCalculating financial ratios...")


df["net_profit_margin_pct"] = df.apply(
    lambda x: net_profit_margin(
        x["net_profit"],
        x["sales"]
    ),
    axis=1
)


df["operating_profit_margin_pct"] = df.apply(
    lambda x: operating_profit_margin(
        x["operating_profit"],
        x["sales"]
    ),
    axis=1
)


# ============================================================
# ROE
# ============================================================

def safe_roe(row):

    # Prefer company-level ROE if available
    company_roe = row.get("roe_percentage")

    if pd.notna(company_roe):
        try:
            value = float(company_roe)

            # Only accept realistic ROE
            if -200 <= value <= 200:
                return value
        except:
            pass

    equity = (
        row.get("equity_capital", 0)
        + row.get("reserves", 0)
    )

    net_profit = row.get("net_profit")

    if pd.isna(equity) or equity == 0:
        return np.nan

    if pd.isna(net_profit):
        return np.nan

    value = (net_profit / equity) * 100

    # Prevent clearly corrupted source values
    if abs(value) > 200:
        return np.nan

    return value


df["return_on_equity_pct"] = df.apply(
    safe_roe,
    axis=1
)


# ============================================================
# DEBT / EQUITY
# ============================================================

df["debt_to_equity"] = df.apply(
    lambda x: debt_to_equity(
        x["borrowings"],
        x["equity_capital"],
        x["reserves"]
    ),
    axis=1
)


# ============================================================
# INTEREST COVERAGE
# ============================================================

df["interest_coverage"] = df.apply(
    lambda x: interest_coverage(
        x["operating_profit"],
        x["other_income"],
        x["interest"]
    ),
    axis=1
)


# ============================================================
# ASSET TURNOVER
# ============================================================

df["asset_turnover"] = df.apply(
    lambda x: asset_turnover(
        x["sales"],
        x["total_assets"]
    ),
    axis=1
)


# ============================================================
# CASH FLOW METRICS
# ============================================================

df["free_cash_flow_cr"] = df.apply(
    lambda x: free_cash_flow(
        x["operating_activity"],
        x["investing_activity"]
    ),
    axis=1
)


df["capex_cr"] = df["investing_activity"].abs()


df["earnings_per_share"] = df["eps"]


df["book_value_per_share"] = df["book_value"]


df["dividend_payout_ratio_pct"] = df["dividend_payout"]


df["total_debt_cr"] = df["borrowings"]


df["cash_from_operations_cr"] = df["operating_activity"]


# ============================================================
# CAGR FUNCTION
# ============================================================

def calculate_cagr(group, column, years=5):

    group = group.sort_values("year_clean").copy()

    values = group[
        ["year_clean", column]
    ].dropna()

    result = pd.Series(
        np.nan,
        index=group.index,
        dtype=float
    )

    for idx in group.index:

        current_year = group.loc[idx, "year_clean"]

        current_rows = values[
            values["year_clean"] == current_year
        ]

        if current_rows.empty:
            continue

        current_value = current_rows.iloc[0][column]

        previous_year = current_year - years

        previous_rows = values[
            values["year_clean"] == previous_year
        ]

        if previous_rows.empty:
            continue

        previous_value = previous_rows.iloc[0][column]

        try:

            current_value = float(current_value)
            previous_value = float(previous_value)

            if previous_value <= 0 or current_value <= 0:
                continue

            cagr = (
                (current_value / previous_value)
                ** (1 / years)
                - 1
            ) * 100

            result.loc[idx] = round(cagr, 2)

        except:
            continue

    return result


# ============================================================
# 5 YEAR CAGR
# ============================================================

print("Calculating 5-year CAGR...")


df["revenue_cagr_5yr"] = (
    df.groupby("company_id", group_keys=False)
      .apply(
          lambda g: calculate_cagr(
              g,
              "sales",
              5
          ),
          include_groups=False
      )
      .reset_index(level=0, drop=True)
)


df["pat_cagr_5yr"] = (
    df.groupby("company_id", group_keys=False)
      .apply(
          lambda g: calculate_cagr(
              g,
              "net_profit",
              5
          ),
          include_groups=False
      )
      .reset_index(level=0, drop=True)
)


df["eps_cagr_5yr"] = (
    df.groupby("company_id", group_keys=False)
      .apply(
          lambda g: calculate_cagr(
              g,
              "eps",
              5
          ),
          include_groups=False
      )
      .reset_index(level=0, drop=True)
)


# ============================================================
# COMPOSITE QUALITY SCORE
# ============================================================

print("Calculating composite quality score...")


def percentile_score(series, ascending=True):

    return (
        series
        .rank(
            pct=True,
            ascending=ascending
        )
        * 100
    )


roe_score = percentile_score(
    df["return_on_equity_pct"],
    ascending=True
)

npm_score = percentile_score(
    df["net_profit_margin_pct"],
    ascending=True
)

asset_score = percentile_score(
    df["asset_turnover"],
    ascending=True
)

growth_score = percentile_score(
    df["revenue_cagr_5yr"],
    ascending=True
)


df["composite_quality_score"] = (
    roe_score.fillna(0) * 0.30
    + npm_score.fillna(0) * 0.25
    + asset_score.fillna(0) * 0.20
    + growth_score.fillna(0) * 0.25
).round(2)


# ============================================================
# FINAL COLUMNS
# ============================================================

columns = [
    "company_id",
    "year",

    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",

    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
    "dividend_payout_ratio_pct",

    "total_debt_cr",
    "cash_from_operations_cr",

    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",

    "composite_quality_score",
]


# ============================================================
# CLEAN NUMERIC VALUES
# ============================================================

for col in columns:

    if col in [
        "company_id",
        "year"
    ]:
        continue

    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# ============================================================
# REMOVE EXISTING FINANCIAL RATIOS
# ============================================================

print("\nUpdating database...")

conn.execute(
    "DELETE FROM financial_ratios"
)

conn.commit()


# ============================================================
# INSERT
# ============================================================

columns = [
    "company_id",
    "year",
    "net_profit_margin_pct",
    ...
]
# ---------------------------------------------------------
# FIX YEAR COLUMN
# ---------------------------------------------------------
if "year" not in df.columns:

    if "year_clean" in df.columns:
        df["year"] = df["year_clean"]

    elif "year_x" in df.columns:
        df["year"] = df["year_x"]

    elif "year_y" in df.columns:
        df["year"] = df["year_y"]

    else:
        raise ValueError(
            "YEAR COLUMN NOT FOUND.\n"
            "Available columns:\n"
            + "\n".join(df.columns.tolist())
        )

df["year"] = df["year"].astype(str).str.strip()

print("\nYEAR COLUMN FIXED")
print(df[["company_id", "year"]].head())


columns = [
    "company_id",
    "year",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "free_cash_flow_cr",
    "capex_cr",
    "earnings_per_share",
    "book_value_per_share",
    "dividend_payout_ratio_pct",
    "total_debt_cr",
    "cash_from_operations_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "composite_quality_score"
]

df[columns].to_sql(
    "financial_ratios",
    conn,
    if_exists="append",
    index=False
)

conn.commit()


# ============================================================
# SAVE CSV
# ============================================================

output_dir = PROJECT_ROOT / "Output"

output_dir.mkdir(
    exist_ok=True
)

output_file = output_dir / "financial_ratios.csv"

df[columns].to_csv(
    output_file,
    index=False
)


# Also save processed version
processed_dir = PROJECT_ROOT / "Data" / "processed"

processed_dir.mkdir(
    exist_ok=True
)

df[columns].to_csv(
    processed_dir / "financial_ratios.csv",
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print(
    "Financial ratio rows:",
    len(df)
)

duplicates = (
    df.groupby(
        ["company_id", "year"]
    )
    .size()
)

duplicate_count = (
    duplicates[duplicates > 1]
    .shape[0]
)

print(
    "Duplicate company/year records:",
    duplicate_count
)


print(
    "\nROE statistics:"
)

print(
    df["return_on_equity_pct"]
    .describe()
)


print(
    "\nCAGR availability:"
)

print(
    "Revenue CAGR:",
    df["revenue_cagr_5yr"].notna().sum()
)

print(
    "PAT CAGR:",
    df["pat_cagr_5yr"].notna().sum()
)

print(
    "EPS CAGR:",
    df["eps_cagr_5yr"].notna().sum()
)


print(
    "\nTop 10 quality scores:"
)

print(
    df[
        [
            "company_id",
            "year",
            "return_on_equity_pct",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "composite_quality_score"
        ]
    ]
    .sort_values(
        "composite_quality_score",
        ascending=False
    )
    .head(10)
    .to_string(index=False)
)


conn.close()


print("\n" + "=" * 80)
print("FINANCIAL RATIOS POPULATED SUCCESSFULLY")
print("=" * 80)

print(
    f"\nSaved to:\n{output_file}"
)