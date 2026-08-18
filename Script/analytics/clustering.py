"""
SPRINT 6 — DAY 36
KMEANS CLUSTERING & INVESTMENT ARCHETYPES

Creates:
    output/cluster_labels.csv
    reports/elbow_plot.png
"""

from pathlib import Path
import sys
import sqlite3

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_FILE = REPORTS_DIR / "elbow_plot.png"


# ============================================================
# CONFIGURATION
# ============================================================

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

N_CLUSTERS = 5
RANDOM_STATE = 42


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SPRINT 6 — DAY 36")
print("KMEANS CLUSTERING & INVESTMENT ARCHETYPES")
print("=" * 70)

print()
print("Project root :", PROJECT_ROOT)
print("Database     :", DB_PATH)
print("Output       :", OUTPUT_DIR)
print("Reports      :", REPORTS_DIR)


# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 70)
print("LOADING CLUSTERING DATA")
print("=" * 70)

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
        sub_sector,
        market_cap_category
    FROM sectors
    """,
    conn,
)

ratios = pd.read_sql_query(
    """
    SELECT
        company_id,
        year,
        net_profit_margin_pct,
        operating_profit_margin_pct,
        return_on_equity_pct,
        debt_to_equity,
        interest_coverage,
        asset_turnover,
        free_cash_flow_cr,
        revenue_cagr_5yr,
        pat_cagr_5yr,
        eps_cagr_5yr
    FROM financial_ratios
    """,
    conn,
)

conn.close()

print("Companies       :", len(companies))
print("Financial ratios:", len(ratios))
print("Sectors         :", len(sectors))


# ============================================================
# PREPARE LATEST YEAR DATA
# ============================================================

print()
print("=" * 70)
print("PREPARING LATEST FINANCIAL DATA")
print("=" * 70)

ratios["year"] = pd.to_numeric(ratios["year"], errors="coerce")

ratios = ratios.sort_values(
    ["company_id", "year"]
)

latest_ratios = (
    ratios
    .dropna(subset=["year"])
    .groupby("company_id", as_index=False)
    .tail(1)
    .copy()
)

print("Latest ratio records:", len(latest_ratios))


# ============================================================
# FCF CAGR
# ============================================================

print()
print("Calculating FCF CAGR where required...")

# The financial_ratios table does not contain fcf_cagr_5yr directly.
# Calculate it from historical FCF values when sufficient data exists.

fcf_history = ratios[
    ["company_id", "year", "free_cash_flow_cr"]
].copy()

fcf_history["free_cash_flow_cr"] = pd.to_numeric(
    fcf_history["free_cash_flow_cr"],
    errors="coerce",
)

fcf_history = fcf_history.dropna(
    subset=["company_id", "year", "free_cash_flow_cr"]
)

fcf_cagr_map = {}

for company_id, group in fcf_history.groupby("company_id"):

    group = group.sort_values("year")

    if len(group) < 2:
        continue

    latest_row = group.iloc[-1]

    target_year = latest_row["year"] - 5

    historical = group[
        group["year"] <= target_year
    ]

    if historical.empty:
        continue

    first_row = historical.iloc[-1]

    start_value = first_row["free_cash_flow_cr"]
    end_value = latest_row["free_cash_flow_cr"]

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
    ):
        continue

    years = latest_row["year"] - first_row["year"]

    if years <= 0:
        continue

    cagr = (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100

    fcf_cagr_map[company_id] = cagr


latest_ratios["fcf_cagr_5yr"] = latest_ratios[
    "company_id"
].map(fcf_cagr_map)


# ============================================================
# MERGE COMPANY + SECTOR + RATIOS
# ============================================================

print()
print("=" * 70)
print("MERGING COMPANY, SECTOR AND RATIO DATA")
print("=" * 70)

df = companies.merge(
    sectors,
    on="company_id",
    how="left",
)

df = df.merge(
    latest_ratios[
        ["company_id"] + [
            c for c in FEATURES
            if c != "fcf_cagr_5yr"
        ] + ["fcf_cagr_5yr"]
    ],
    on="company_id",
    how="left",
)

print("Companies after merge:", len(df))


# ============================================================
# CONVERT FEATURES TO NUMERIC
# ============================================================

print()
print("=" * 70)
print("PREPARING CLUSTER FEATURES")
print("=" * 70)

for feature in FEATURES:
    df[feature] = pd.to_numeric(
        df[feature],
        errors="coerce",
    )

print()
print("Missing values before sector imputation:")

print(
    df[FEATURES]
    .isna()
    .sum()
)


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

print()
print("=" * 70)
print("SECTOR MEDIAN IMPUTATION")
print("=" * 70)

for feature in FEATURES:

    sector_medians = (
        df.groupby("sector")[feature]
        .transform("median")
    )

    df[feature] = df[feature].fillna(
        sector_medians
    )

    # Final fallback if an entire sector is missing
    # a particular metric.
    df[feature] = df[feature].fillna(
        df[feature].median()
    )

print()
print("Missing values after imputation:")

print(
    df[FEATURES]
    .isna()
    .sum()
)


# ============================================================
# STANDARD SCALING
# ============================================================

print()
print("=" * 70)
print("STANDARD SCALING")
print("=" * 70)

scaler = StandardScaler()

X = scaler.fit_transform(
    df[FEATURES]
)

print("Feature matrix:", X.shape)
print("Mean approximately:", X.mean(axis=0))
print("Std approximately :", X.std(axis=0))


# ============================================================
# ELBOW ANALYSIS
# ============================================================

print()
print("=" * 70)
print("CALCULATING ELBOW CURVE")
print("=" * 70)

k_values = range(2, 11)
inertias = []

for k in k_values:

    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    model.fit(X)

    inertias.append(model.inertia_)

    print(
        f"k={k:<2} | inertia={model.inertia_:.4f}"
    )


# ============================================================
# SAVE ELBOW PLOT
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    list(k_values),
    inertias,
    marker="o",
)

plt.axvline(
    N_CLUSTERS,
    linestyle="--",
    label="Selected k=5",
)

plt.title(
    "KMeans Elbow Analysis — Nifty 100"
)

plt.xlabel("Number of Clusters (k)")
plt.ylabel("Inertia")

plt.xticks(list(k_values))
plt.grid(True, alpha=0.3)
plt.legend()

plt.tight_layout()

plt.savefig(
    ELBOW_FILE,
    dpi=150,
    bbox_inches="tight",
)

plt.close()

print()
print("✓ Saved:", ELBOW_FILE)


# ============================================================
# FINAL KMEANS MODEL
# ============================================================

print()
print("=" * 70)
print("RUNNING FINAL KMEANS MODEL")
print("=" * 70)

kmeans = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=RANDOM_STATE,
    n_init=20,
)

cluster_ids = kmeans.fit_predict(X)

df["cluster_id"] = cluster_ids

distances = kmeans.transform(X)

df["distance_from_centroid"] = distances.min(axis=1)


# ============================================================
# CLUSTER PROFILES
# ============================================================

print()
print("=" * 70)
print("CLUSTER PROFILES")
print("=" * 70)

profile = (
    df.groupby("cluster_id")[FEATURES]
    .mean()
    .round(2)
)

print(profile)


# ============================================================
# AUTOMATIC CLUSTER NAMING
# ============================================================

print()
print("=" * 70)
print("ASSIGNING CLUSTER ARCHETYPES")
print("=" * 70)


cluster_scores = (
    df.groupby("cluster_id")[FEATURES]
    .mean()
    .copy()
)

# Convert each metric to a standardized profile score.
profile_scaler = StandardScaler()

profile_scaled = pd.DataFrame(
    profile_scaler.fit_transform(cluster_scores),
    index=cluster_scores.index,
    columns=FEATURES,
)


def assign_cluster_names(profile_df):
    """
    Assign descriptive investment archetypes based on cluster profiles.
    """

    names = {}

    for cluster_id, row in profile_df.iterrows():

        quality = (
            row["return_on_equity_pct"]
            + row["operating_profit_margin_pct"]
        )

        growth = (
            row["revenue_cagr_5yr"]
            + row["fcf_cagr_5yr"]
        )

        leverage = row["debt_to_equity"]

        # Strong quality + strong growth
        if quality > 1.0 and growth > 1.0:
            name = "High-Quality Compounders"

        # Strong quality but lower growth
        elif quality > 0.5 and growth <= 1.0:
            name = "Defensive Quality"

        # Strong growth but weaker quality
        elif growth > 0.5 and quality <= 0.5:
            name = "Emerging Growth"

        # High leverage / weak financial profile
        elif leverage > 0.8 or (
            quality < -0.5 and growth < -0.5
        ):
            name = "Distressed / Turnaround"

        else:
            name = "Value Cyclicals"

        names[cluster_id] = name

    return names


cluster_names = assign_cluster_names(
    profile_scaled
)

df["cluster_name"] = df["cluster_id"].map(
    cluster_names
)


# ============================================================
# PREVENT DUPLICATE CLUSTER NAMES
# ============================================================

# If two clusters receive the same automatic name,
# append a profile-based suffix so every cluster has
# a unique descriptive label.

used_names = {}
final_names = {}

for cluster_id in sorted(cluster_names):

    name = cluster_names[cluster_id]

    if name not in used_names:
        used_names[name] = 1
        final_names[cluster_id] = name
    else:
        used_names[name] += 1
        final_names[cluster_id] = (
            f"{name} {used_names[name]}"
        )

df["cluster_name"] = df["cluster_id"].map(
    final_names
)


# ============================================================
# OUTPUT DATASET
# ============================================================

cluster_output = df[
    [
        "company_id",
        "cluster_id",
        "cluster_name",
        "distance_from_centroid",
    ]
].copy()

cluster_output["cluster_id"] = (
    cluster_output["cluster_id"]
    .astype(int)
)

cluster_output["distance_from_centroid"] = (
    cluster_output["distance_from_centroid"]
    .round(6)
)

cluster_output = cluster_output.sort_values(
    ["cluster_id", "distance_from_centroid"]
)

cluster_output.to_csv(
    OUTPUT_FILE,
    index=False,
)

print()
print("✓ Saved:", OUTPUT_FILE)


# ============================================================
# VALIDATION
# ============================================================

print()
print("=" * 70)
print("DAY 36 VALIDATION")
print("=" * 70)

print()
print("Required columns:")

required_columns = [
    "company_id",
    "cluster_id",
    "cluster_name",
    "distance_from_centroid",
]

for column in required_columns:

    if column in cluster_output.columns:
        print(f"  ✓ {column}")
    else:
        print(f"  ✗ {column}")


print()
print("Companies in output :", len(cluster_output))
print(
    "Unique companies    :",
    cluster_output["company_id"].nunique(),
)
print(
    "Duplicate companies :",
    cluster_output["company_id"].duplicated().sum(),
)
print(
    "Clusters generated  :",
    cluster_output["cluster_id"].nunique(),
)

print()
print("Cluster distribution:")

print(
    cluster_output["cluster_id"]
    .value_counts()
    .sort_index()
)

print()
print("Cluster names:")

for cluster_id, name in sorted(
    final_names.items()
):
    print(
        f"  Cluster {cluster_id}: {name}"
    )


# ============================================================
# FINAL CHECKS
# ============================================================

assert len(cluster_output) == 92, (
    f"Expected 92 companies, "
    f"got {len(cluster_output)}"
)

assert (
    cluster_output["company_id"].nunique()
    == 92
)

assert (
    cluster_output["cluster_id"]
    .between(0, 4)
    .all()
)

assert (
    cluster_output["cluster_name"]
    .notna()
    .all()
)

assert (
    cluster_output["distance_from_centroid"]
    .notna()
    .all()
)

print()
print("✓ All Day 36 validation checks passed")

print()
print("=" * 70)
print("SPRINT 6 — DAY 36 COMPLETED")
print("=" * 70)

print()
print("Generated files:")
print("  ✓", OUTPUT_FILE)
print("  ✓", ELBOW_FILE)

print()
print("Companies processed :", len(cluster_output))
print("Clusters generated  :", N_CLUSTERS)
print("Features used       :", len(FEATURES))