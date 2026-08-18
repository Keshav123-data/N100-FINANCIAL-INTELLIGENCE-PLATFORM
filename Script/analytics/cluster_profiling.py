"""
SPRINT 6 — DAY 37
CLUSTER PROFILING, CORRELATION, OUTLIER & PORTFOLIO STATISTICS
"""

from pathlib import Path
import sqlite3
import warnings

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


# ==============================================================
# PATHS
# ==============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


print("=" * 70)
print("SPRINT 6 — DAY 37")
print("CLUSTER PROFILING & FINANCIAL STATISTICS")
print("=" * 70)

print(f"\nProject root : {PROJECT_ROOT}")
print(f"Database     : {DB_PATH}")
print(f"Output       : {OUTPUT_DIR}")
print(f"Reports      : {REPORTS_DIR}")


# ==============================================================
# LOAD CLUSTER LABELS
# ==============================================================

print("\n" + "=" * 70)
print("LOADING CLUSTER DATA")
print("=" * 70)

cluster_file = OUTPUT_DIR / "cluster_labels.csv"

if not cluster_file.exists():
    raise FileNotFoundError(
        f"Missing {cluster_file}. Run Day 36 clustering first."
    )

clusters = pd.read_csv(cluster_file)

print(f"Cluster records : {len(clusters)}")
print(f"Columns         : {clusters.columns.tolist()}")


# ==============================================================
# LOAD DATABASE DATA
# ==============================================================

conn = sqlite3.connect(DB_PATH)

companies = pd.read_sql_query(
    """
    SELECT
        id AS company_id,
        company_name
    FROM companies
    """,
    conn,
)

sectors = pd.read_sql_query(
    """
    SELECT
        company_id,
        broad_sector AS sector,
        sub_sector
    FROM sectors
    """,
    conn,
)

ratios = pd.read_sql_query(
    """
    SELECT *
    FROM financial_ratios
    """,
    conn,
)

conn.close()

print(f"\nCompanies       : {len(companies)}")
print(f"Financial ratios: {len(ratios)}")
print(f"Sectors         : {len(sectors)}")


# ==============================================================
# PREPARE LATEST RATIOS
# ==============================================================

print("\n" + "=" * 70)
print("PREPARING LATEST FINANCIAL DATA")
print("=" * 70)

ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

latest_year = ratios.groupby("company_id")["year"].transform("max")

latest_ratios = ratios.loc[
    ratios["year"] == latest_year
].copy()

print(f"Latest ratio records : {len(latest_ratios)}")


# ==============================================================
# MERGE DATA
# ==============================================================

df = (
    companies
    .merge(sectors, on="company_id", how="left")
    .merge(
        latest_ratios,
        on="company_id",
        how="left",
        suffixes=("", "_ratio"),
    )
    .merge(
        clusters[
            [
                "company_id",
                "cluster_id",
                "cluster_name",
                "distance_from_centroid",
            ]
        ],
        on="company_id",
        how="left",
    )
)

print(f"Companies after merge : {len(df)}")


# ==============================================================
# FEATURES
# ==============================================================

# ==============================================================
# FEATURES
# ==============================================================

features = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

# Convert available ratio metrics to numeric
for col in [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "operating_profit_margin_pct",
]:
    if col in df.columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

# --------------------------------------------------------------
# FCF CAGR
# financial_ratios does not store fcf_cagr_5yr directly.
# Calculate it from historical free cash flow.
# --------------------------------------------------------------

print("\nCalculating FCF CAGR where required...")

fcf_history = ratios[
    [
        "company_id",
        "year",
        "free_cash_flow_cr"
    ]
].copy()

fcf_history["year"] = pd.to_numeric(
    fcf_history["year"],
    errors="coerce"
)

fcf_history["free_cash_flow_cr"] = pd.to_numeric(
    fcf_history["free_cash_flow_cr"],
    errors="coerce"
)

fcf_history = fcf_history.dropna(
    subset=[
        "company_id",
        "year",
        "free_cash_flow_cr"
    ]
)

fcf_history = fcf_history.sort_values(
    ["company_id", "year"]
)


def calculate_fcf_cagr(group):
    """
    Calculate five-year FCF CAGR where valid.
    """

    group = group.sort_values("year")

    latest_year = group["year"].max()
    target_year = latest_year - 5

    latest_rows = group[
        group["year"] == latest_year
    ]

    old_rows = group[
        group["year"] <= target_year
    ]

    if latest_rows.empty or old_rows.empty:
        return np.nan

    latest_fcf = latest_rows.iloc[-1][
        "free_cash_flow_cr"
    ]

    old_row = old_rows.iloc[-1]

    old_fcf = old_row[
        "free_cash_flow_cr"
    ]

    if pd.isna(latest_fcf) or pd.isna(old_fcf):
        return np.nan

    # CAGR is not mathematically meaningful when
    # the starting FCF is zero or negative.
    if old_fcf <= 0 or latest_fcf <= 0:
        return np.nan

    years = latest_year - old_row["year"]

    if years <= 0:
        return np.nan

    return (
        (latest_fcf / old_fcf) ** (1 / years) - 1
    ) * 100


fcf_cagr = (
    fcf_history
    .groupby("company_id")
    .apply(calculate_fcf_cagr)
    .reset_index(name="fcf_cagr_5yr")
)

# Remove any accidental duplicate column
if "fcf_cagr_5yr" in df.columns:
    df = df.drop(
        columns=["fcf_cagr_5yr"]
    )

df = df.merge(
    fcf_cagr,
    on="company_id",
    how="left"
)

df["fcf_cagr_5yr"] = pd.to_numeric(
    df["fcf_cagr_5yr"],
    errors="coerce"
)

print(
    "Companies with calculated FCF CAGR:",
    df["fcf_cagr_5yr"].notna().sum()
)

print(
    "\nMissing feature values:"
)

print(
    df[features].isna().sum()
)

# ==============================================================
# CLUSTER PROFILE
# ==============================================================

print("\n" + "=" * 70)
print("CLUSTER PROFILING")
print("=" * 70)

cluster_profile_mean = (
    df.groupby(["cluster_id", "cluster_name"])[features]
    .mean()
    .round(2)
)

cluster_profile_median = (
    df.groupby(["cluster_id", "cluster_name"])[features]
    .median()
    .round(2)
)

cluster_profile = cluster_profile_mean.copy()

cluster_profile.to_csv(
    OUTPUT_DIR / "cluster_profile_mean.csv"
)

cluster_profile_median.to_csv(
    OUTPUT_DIR / "cluster_profile_median.csv"
)

print("\nMEAN PROFILE:")
print(cluster_profile)

print("\nMEDIAN PROFILE:")
print(cluster_profile_median)

print("\n✓ Saved cluster profile mean")
print("✓ Saved cluster profile median")


# ==============================================================
# CLUSTER COMPANY MEMBERS
# ==============================================================

cluster_members = (
    df[
        [
            "company_id",
            "company_name",
            "sector",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ]
    .sort_values(["cluster_id", "distance_from_centroid"])
)

cluster_members.to_csv(
    OUTPUT_DIR / "cluster_members.csv",
    index=False,
)

print("\n✓ Saved cluster_members.csv")


# ==============================================================
# 10 KPI CORRELATION MATRIX
# ==============================================================

print("\n" + "=" * 70)
print("CALCULATING KPI CORRELATION MATRIX")
print("=" * 70)

correlation_kpis = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
]

correlation_df = df[correlation_kpis].copy()

correlation_df = correlation_df.apply(
    pd.to_numeric,
    errors="coerce",
)

corr_matrix = correlation_df.corr(
    method="pearson"
)

corr_matrix.to_csv(
    OUTPUT_DIR / "kpi_correlation_matrix.csv"
)

plt.figure(figsize=(14, 11))

sns.heatmap(
    corr_matrix,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    square=True,
)

plt.title(
    "NIFTY 100 Financial KPI Correlation Matrix",
    fontsize=16,
    pad=15,
)

plt.xticks(rotation=45, ha="right")
plt.yticks(rotation=0)
plt.tight_layout()

correlation_plot = REPORTS_DIR / "correlation_heatmap.png"

plt.savefig(
    correlation_plot,
    dpi=200,
    bbox_inches="tight",
)

plt.close()

print(f"✓ Saved: {correlation_plot}")


# ==============================================================
# OUTLIER DETECTION
# ==============================================================
# Z-score calculated within broad sector.
# Flag if ABS(Z) > 3 for ANY KPI.
# ==============================================================

print("\n" + "=" * 70)
print("OUTLIER DETECTION")
print("=" * 70)

outlier_features = features + [
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
]

outlier_features = list(dict.fromkeys(outlier_features))

outlier_df = df[
    [
        "company_id",
        "company_name",
        "sector",
        "cluster_id",
        "cluster_name",
    ] + outlier_features
].copy()


def calculate_sector_zscore(group):
    result = group.copy()

    for col in outlier_features:
        values = pd.to_numeric(
            result[col],
            errors="coerce",
        )

        mean = values.mean()
        std = values.std(ddof=0)

        if pd.isna(std) or std == 0:
            result[f"{col}_z"] = 0.0
        else:
            result[f"{col}_z"] = (
                values - mean
            ) / std

    return result


# Calculate sector-wise Z-scores.
# Keep sector explicitly because newer pandas versions
# may remove the grouping column from apply() output.

zscore_parts = []

for sector_name, sector_group in outlier_df.groupby(
    "sector",
    dropna=False
):
    sector_result = calculate_sector_zscore(
        sector_group.copy()
    )

    # Explicitly restore sector
    sector_result["sector"] = sector_name

    zscore_parts.append(sector_result)

if zscore_parts:
    zscore_df = pd.concat(
        zscore_parts,
        ignore_index=True
    )
else:
    zscore_df = outlier_df.copy()

print(
    f"Companies with Z-scores: {len(zscore_df)}"
)


z_columns = [
    f"{col}_z"
    for col in outlier_features
]

zscore_df["max_abs_zscore"] = (
    zscore_df[z_columns]
    .abs()
    .max(axis=1)
)

zscore_df["outlier_flag"] = (
    zscore_df["max_abs_zscore"] > 3
)


def get_outlier_metrics(row):
    metrics = []

    for col in outlier_features:
        z = row[f"{col}_z"]

        if pd.notna(z) and abs(z) > 3:
            metrics.append(
                f"{col}: {z:.2f}"
            )

    return "; ".join(metrics)


zscore_df["outlier_metrics"] = zscore_df.apply(
    get_outlier_metrics,
    axis=1,
)


outlier_report = zscore_df[
    zscore_df["outlier_flag"]
].copy()

outlier_report = outlier_report[
    [
        "company_id",
        "company_name",
        "sector",
        "cluster_id",
        "cluster_name",
        "max_abs_zscore",
        "outlier_metrics",
    ]
].sort_values(
    "max_abs_zscore",
    ascending=False,
)


outlier_report.to_csv(
    OUTPUT_DIR / "outlier_report.csv",
    index=False,
)

print(
    f"Outliers detected : {len(outlier_report)}"
)

print(
    f"✓ Saved: {OUTPUT_DIR / 'outlier_report.csv'}"
)


# ==============================================================
# PORTFOLIO STATISTICS
# ==============================================================

print("\n" + "=" * 70)
print("CALCULATING PORTFOLIO STATISTICS")
print("=" * 70)

portfolio_kpis = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "interest_coverage",
    "asset_turnover",
]

portfolio_df = df[portfolio_kpis].copy()

portfolio_df = portfolio_df.apply(
    pd.to_numeric,
    errors="coerce",
)


stats = pd.DataFrame(
    {
        "P10": portfolio_df.quantile(0.10),
        "P25": portfolio_df.quantile(0.25),
        "P50": portfolio_df.quantile(0.50),
        "P75": portfolio_df.quantile(0.75),
        "P90": portfolio_df.quantile(0.90),
        "Mean": portfolio_df.mean(),
        "Std": portfolio_df.std(),
    }
)

stats = stats.round(4)

stats.index.name = "KPI"

stats.to_csv(
    OUTPUT_DIR / "portfolio_stats.csv"
)

print(stats)

print(
    f"\n✓ Saved: {OUTPUT_DIR / 'portfolio_stats.csv'}"
)


# ==============================================================
# DAY 37 VALIDATION
# ==============================================================

print("\n" + "=" * 70)
print("DAY 37 VALIDATION")
print("=" * 70)

checks = {
    "Cluster profile mean": cluster_profile.shape[0] == 5,
    "Cluster profile median": cluster_profile_median.shape[0] == 5,
    "KPI correlation matrix": corr_matrix.shape == (10, 10),
    "Outlier report exists": (
        OUTPUT_DIR / "outlier_report.csv"
    ).exists(),
    "Portfolio stats exists": (
        OUTPUT_DIR / "portfolio_stats.csv"
    ).exists(),
    "92 companies": len(df) == 92,
    "Unique companies": df["company_id"].nunique() == 92,
    "5 clusters": df["cluster_id"].nunique() == 5,
}

for name, passed in checks.items():
    print(
        f"  {'✓' if passed else '✗'} {name}"
    )

if not all(checks.values()):
    raise RuntimeError(
        "Day 37 validation failed."
    )

print("\n✓ ALL DAY 37 VALIDATION CHECKS PASSED")


# ==============================================================
# FINAL SUMMARY
# ==============================================================

print("\n" + "=" * 70)
print("SPRINT 6 — DAY 37 COMPLETED")
print("=" * 70)

print("\nGenerated files:")

generated = [
    OUTPUT_DIR / "cluster_profile_mean.csv",
    OUTPUT_DIR / "cluster_profile_median.csv",
    OUTPUT_DIR / "cluster_members.csv",
    OUTPUT_DIR / "kpi_correlation_matrix.csv",
    OUTPUT_DIR / "outlier_report.csv",
    OUTPUT_DIR / "portfolio_stats.csv",
    REPORTS_DIR / "correlation_heatmap.png",
]

for path in generated:
    print(f"  ✓ {path}")

print(f"\nCompanies processed : {len(df)}")
print(f"Clusters profiled   : {df['cluster_id'].nunique()}")
print(f"Outliers detected   : {len(outlier_report)}")
print("Correlation KPIs    : 10")
print("Portfolio KPIs      : 10")