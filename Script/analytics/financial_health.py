import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ======================================================================
# SPRINT 5 — DAY 33
# FINANCIAL HEALTH & RISK INTELLIGENCE
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = PROJECT_ROOT / "DB" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HEALTH_FILE = OUTPUT_DIR / "financial_health.xlsx"
RANKING_FILE = OUTPUT_DIR / "financial_health_ranking.csv"
SECTOR_FILE = OUTPUT_DIR / "financial_risk_sector_analysis.csv"
DASHBOARD_FILE = OUTPUT_DIR / "financial_health_dashboard_dataset.csv"
ALERT_FILE = OUTPUT_DIR / "financial_risk_alerts.csv"


# ======================================================================
# DATABASE
# ======================================================================

def get_connection():
    return sqlite3.connect(DATABASE_PATH)


# ======================================================================
# SAFE NUMERIC HELPERS
# ======================================================================

def safe_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def safe_mean(values):
    values = pd.to_numeric(pd.Series(values), errors="coerce")
    values = values.replace([np.inf, -np.inf], np.nan).dropna()

    if len(values) == 0:
        return np.nan

    return values.mean()


# ======================================================================
# LOAD DATA
# ======================================================================

def load_data():

    print()
    print("=" * 70)
    print("LOADING FINANCIAL HEALTH DATA")
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
                broad_sector AS sector
            FROM sectors
            """,
            conn
        )

        pnl = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                sales,
                net_profit,
                operating_profit,
                interest
            FROM profitandloss
            """,
            conn
        )

    finally:
        conn.close()

    print(f"Companies       : {len(companies)}")
    print(f"Financial ratios: {len(ratios)}")
    print(f"Profit & Loss   : {len(pnl)}")
    print(f"Sectors         : {len(sectors)}")

    return companies, ratios, pnl, sectors


# ======================================================================
# PREPARE DATA
# ======================================================================

def prepare_data(ratios, pnl):

    print()
    print("=" * 70)
    print("PREPARING FINANCIAL DATA")
    print("=" * 70)

    ratios = ratios.copy()
    pnl = pnl.copy()

    ratio_numeric = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "total_debt_cr",
        "cash_from_operations_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "composite_quality_score",
    ]

    pnl_numeric = [
        "sales",
        "net_profit",
        "operating_profit",
        "interest",
    ]

    ratios = safe_numeric(ratios, ratio_numeric)
    pnl = safe_numeric(pnl, pnl_numeric)

    ratios["year"] = pd.to_numeric(
        ratios["year"],
        errors="coerce"
    )

    pnl["year"] = pd.to_numeric(
        pnl["year"],
        errors="coerce"
    )

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()
    pnl["company_id"] = pnl["company_id"].astype(str).str.strip()

    return ratios, pnl


# ======================================================================
# LATEST FINANCIAL POSITION
# ======================================================================

def calculate_latest_metrics(ratios):

    print()
    print("=" * 70)
    print("CALCULATING LATEST FINANCIAL METRICS")
    print("=" * 70)

    ratios = ratios.copy()

    ratios = ratios.dropna(
        subset=["company_id", "year"]
    )

    ratios = ratios.sort_values(
        ["company_id", "year"]
    )

    latest = (
        ratios
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )

    print(f"Companies with ratio data: {len(latest)}")

    return latest


# ======================================================================
# PROFITABILITY SCORE
# ======================================================================

def profitability_score(row):

    scores = []

    # Net profit margin
    npm = row.get("net_profit_margin_pct", np.nan)

    if pd.notna(npm):
        if npm >= 20:
            scores.append(100)
        elif npm >= 15:
            scores.append(85)
        elif npm >= 10:
            scores.append(70)
        elif npm >= 5:
            scores.append(50)
        elif npm >= 0:
            scores.append(30)
        else:
            scores.append(10)

    # ROE
    roe = row.get("return_on_equity_pct", np.nan)

    if pd.notna(roe):
        if roe >= 25:
            scores.append(100)
        elif roe >= 18:
            scores.append(85)
        elif roe >= 12:
            scores.append(70)
        elif roe >= 8:
            scores.append(50)
        elif roe >= 0:
            scores.append(30)
        else:
            scores.append(10)

    # Operating margin
    opm = row.get("operating_profit_margin_pct", np.nan)

    if pd.notna(opm):
        if opm >= 25:
            scores.append(100)
        elif opm >= 18:
            scores.append(85)
        elif opm >= 12:
            scores.append(70)
        elif opm >= 7:
            scores.append(50)
        elif opm >= 0:
            scores.append(30)
        else:
            scores.append(10)

    if not scores:
        return np.nan

    return round(float(np.mean(scores)), 2)


# ======================================================================
# LEVERAGE SCORE
# ======================================================================

def leverage_score(row):

    de = row.get("debt_to_equity", np.nan)

    if pd.isna(de):
        return np.nan

    if de <= 0.25:
        return 100
    elif de <= 0.50:
        return 85
    elif de <= 1.00:
        return 70
    elif de <= 1.50:
        return 50
    elif de <= 2.00:
        return 30
    else:
        return 10


# ======================================================================
# INTEREST COVERAGE SCORE
# ======================================================================

def interest_coverage_score(row):

    ic = row.get("interest_coverage", np.nan)

    if pd.isna(ic):
        return np.nan

    if ic >= 8:
        return 100
    elif ic >= 5:
        return 85
    elif ic >= 3:
        return 70
    elif ic >= 2:
        return 50
    elif ic >= 1:
        return 30
    else:
        return 10


# ======================================================================
# CASH FLOW SCORE
# ======================================================================

def cash_flow_score(row):

    scores = []

    fcf = row.get("free_cash_flow_cr", np.nan)
    cfo = row.get("cash_from_operations_cr", np.nan)

    if pd.notna(fcf):
        scores.append(80 if fcf > 0 else 20)

    if pd.notna(cfo):
        scores.append(80 if cfo > 0 else 20)

    if not scores:
        return np.nan

    return round(float(np.mean(scores)), 2)


# ======================================================================
# GROWTH SCORE
# ======================================================================

def growth_score(row):

    scores = []

    revenue = row.get("revenue_cagr_5yr", np.nan)
    pat = row.get("pat_cagr_5yr", np.nan)
    eps = row.get("eps_cagr_5yr", np.nan)

    for growth in [revenue, pat, eps]:

        if pd.notna(growth):

            if growth >= 20:
                scores.append(100)

            elif growth >= 12:
                scores.append(85)

            elif growth >= 7:
                scores.append(70)

            elif growth >= 3:
                scores.append(55)

            elif growth >= 0:
                scores.append(40)

            else:
                scores.append(15)

    if not scores:
        return np.nan

    return round(float(np.mean(scores)), 2)


# ======================================================================
# RISK PENALTY
# ======================================================================

def calculate_risk_penalty(row):

    penalty = 0

    de = row.get("debt_to_equity", np.nan)
    ic = row.get("interest_coverage", np.nan)
    npm = row.get("net_profit_margin_pct", np.nan)
    roe = row.get("return_on_equity_pct", np.nan)

    # High leverage
    if pd.notna(de):

        if de > 2:
            penalty += 30
        elif de > 1.5:
            penalty += 20
        elif de > 1:
            penalty += 10

    # Weak interest coverage
    if pd.notna(ic):

        if ic < 1:
            penalty += 30
        elif ic < 2:
            penalty += 20
        elif ic < 3:
            penalty += 10

    # Negative profitability
    if pd.notna(npm) and npm < 0:
        penalty += 20

    if pd.notna(roe) and roe < 0:
        penalty += 20

    return penalty


# ======================================================================
# FINANCIAL HEALTH SCORE
# ======================================================================

def calculate_health_score(row):

    components = []

    for column, weight in [
        ("profitability_score", 0.30),
        ("leverage_score", 0.20),
        ("interest_coverage_score", 0.20),
        ("cash_flow_score", 0.15),
        ("growth_score", 0.15),
    ]:

        value = row.get(column, np.nan)

        if pd.notna(value):
            components.append((value, weight))

    if not components:
        return np.nan

    total_weight = sum(weight for _, weight in components)

    weighted_score = sum(
        value * weight
        for value, weight in components
    )

    score = weighted_score / total_weight

    score -= row.get("risk_penalty", 0)

    return round(float(np.clip(score, 0, 100)), 2)


# ======================================================================
# RISK LABEL
# ======================================================================

def risk_label(score):

    if pd.isna(score):
        return np.nan

    if score >= 80:
        return "Very Low Risk"

    if score >= 65:
        return "Low Risk"

    if score >= 50:
        return "Moderate Risk"

    if score >= 35:
        return "High Risk"

    return "Severe Risk"


# ======================================================================
# HEALTH LABEL
# ======================================================================

def health_label(score):

    if pd.isna(score):
        return np.nan

    if score >= 80:
        return "Excellent"

    if score >= 65:
        return "Good"

    if score >= 50:
        return "Average"

    if score >= 35:
        return "Weak"

    return "Critical"


# ======================================================================
# RISK ALERTS
# ======================================================================

def detect_risk_alerts(df):

    print()
    print("=" * 70)
    print("DETECTING FINANCIAL RISK ALERTS")
    print("=" * 70)

    alerts = []

    for _, row in df.iterrows():

        if pd.isna(row.get("financial_health_score")):
            continue

        reasons = []

        de = row.get("debt_to_equity", np.nan)
        ic = row.get("interest_coverage", np.nan)
        npm = row.get("net_profit_margin_pct", np.nan)
        roe = row.get("return_on_equity_pct", np.nan)

        if pd.notna(de) and de > 2:
            reasons.append("High Debt / Equity")

        if pd.notna(ic) and ic < 1.5:
            reasons.append("Weak Interest Coverage")

        if pd.notna(npm) and npm < 0:
            reasons.append("Negative Net Margin")

        if pd.notna(roe) and roe < 0:
            reasons.append("Negative ROE")

        score = row.get("financial_health_score")

        if pd.notna(score) and score < 35:
            reasons.append("Critical Financial Health")

        if reasons:

            alerts.append({
                "company_id": row["company_id"],
                "company_name": row["company_name"],
                "sector": row["sector"],
                "financial_health_score": score,
                "risk_label": row["risk_label"],
                "risk_reasons": "; ".join(reasons),
            })

    alerts_df = pd.DataFrame(alerts)

    print(f"Risk alerts detected: {len(alerts_df)}")

    return alerts_df


# ======================================================================
# SECTOR ANALYSIS
# ======================================================================

def sector_analysis(df):

    print()
    print("=" * 70)
    print("CALCULATING SECTOR FINANCIAL RISK ANALYSIS")
    print("=" * 70)

    valid = df.dropna(
        subset=["financial_health_score"]
    ).copy()

    if valid.empty:

        return pd.DataFrame(
            columns=[
                "sector",
                "companies_scored",
                "average_health_score",
                "average_debt_to_equity",
                "average_interest_coverage",
                "high_risk_companies",
                "severe_risk_companies",
            ]
        )

    result = (
        valid
        .groupby("sector")
        .agg(
            companies_scored=("company_id", "count"),
            average_health_score=(
                "financial_health_score",
                "mean"
            ),
            average_debt_to_equity=(
                "debt_to_equity",
                "mean"
            ),
            average_interest_coverage=(
                "interest_coverage",
                "mean"
            ),
            high_risk_companies=(
                "risk_label",
                lambda x: x.isin(
                    ["High Risk", "Severe Risk"]
                ).sum()
            ),
            severe_risk_companies=(
                "risk_label",
                lambda x: (x == "Severe Risk").sum()
            ),
        )
        .reset_index()
    )

    result["average_health_score"] = result[
        "average_health_score"
    ].round(2)

    result["average_debt_to_equity"] = result[
        "average_debt_to_equity"
    ].round(2)

    result["average_interest_coverage"] = result[
        "average_interest_coverage"
    ].round(2)

    result = result.sort_values(
        "average_health_score",
        ascending=False
    )

    print(f"Sectors analysed: {len(result)}")

    return result


# ======================================================================
# BUILD HEALTH DATASET
# ======================================================================

def build_health_dataset():

    companies, ratios, pnl, sectors = load_data()

    ratios, pnl = prepare_data(
        ratios,
        pnl
    )

    latest = calculate_latest_metrics(
        ratios
    )

    # --------------------------------------------------------------
    # Merge company information
    # --------------------------------------------------------------

    df = companies.merge(
        sectors,
        on="company_id",
        how="left"
    )

    df = df.merge(
        latest,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------------
    # Calculate component scores
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("CALCULATING PROFITABILITY SCORE")
    print("=" * 70)

    df["profitability_score"] = df.apply(
        profitability_score,
        axis=1
    )

    print(
        "Companies with profitability score:",
        df["profitability_score"].notna().sum()
    )

    print()
    print("=" * 70)
    print("CALCULATING LEVERAGE SCORE")
    print("=" * 70)

    df["leverage_score"] = df.apply(
        leverage_score,
        axis=1
    )

    print(
        "Companies with leverage score:",
        df["leverage_score"].notna().sum()
    )

    print()
    print("=" * 70)
    print("CALCULATING INTEREST COVERAGE SCORE")
    print("=" * 70)

    df["interest_coverage_score"] = df.apply(
        interest_coverage_score,
        axis=1
    )

    print(
        "Companies with interest coverage score:",
        df["interest_coverage_score"].notna().sum()
    )

    print()
    print("=" * 70)
    print("CALCULATING CASH FLOW SCORE")
    print("=" * 70)

    df["cash_flow_score"] = df.apply(
        cash_flow_score,
        axis=1
    )

    print(
        "Companies with cash-flow score:",
        df["cash_flow_score"].notna().sum()
    )

    print()
    print("=" * 70)
    print("CALCULATING GROWTH SCORE")
    print("=" * 70)

    df["growth_score"] = df.apply(
        growth_score,
        axis=1
    )

    print(
        "Companies with growth score:",
        df["growth_score"].notna().sum()
    )

    # --------------------------------------------------------------
    # Risk penalty
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("CALCULATING RISK PENALTY")
    print("=" * 70)

    df["risk_penalty"] = df.apply(
        calculate_risk_penalty,
        axis=1
    )

    # --------------------------------------------------------------
    # Final health score
    # --------------------------------------------------------------

    print()
    print("=" * 70)
    print("CALCULATING FINANCIAL HEALTH SCORE")
    print("=" * 70)

    df["financial_health_score"] = df.apply(
        calculate_health_score,
        axis=1
    )

    df["health_label"] = df[
        "financial_health_score"
    ].apply(health_label)

    df["risk_label"] = df[
        "financial_health_score"
    ].apply(risk_label)

    print(
        "Companies with health score:",
        df["financial_health_score"].notna().sum()
    )

    print(
        "Companies without health score:",
        df["financial_health_score"].isna().sum()
    )

    return df


# ======================================================================
# MAIN
# ======================================================================

def main():

    print()
    print("=" * 70)
    print("SPRINT 5 — DAY 33")
    print("FINANCIAL HEALTH & RISK INTELLIGENCE")
    print("=" * 70)

    print()
    print("Project root :", PROJECT_ROOT)
    print("Database     :", DATABASE_PATH)
    print("Output       :", OUTPUT_DIR)

    try:

        df = build_health_dataset()

        # ============================================================
        # RISK ALERTS
        # ============================================================

        alerts = detect_risk_alerts(df)

        # ============================================================
        # SECTOR ANALYSIS
        # ============================================================

        sector_df = sector_analysis(df)

        # ============================================================
        # RANKING
        # ============================================================

        ranking = df[
            df["financial_health_score"].notna()
        ].copy()

        ranking = ranking.sort_values(
            "financial_health_score",
            ascending=False
        )

        ranking["health_rank"] = range(
            1,
            len(ranking) + 1
        )

        # ============================================================
        # DASHBOARD DATASET
        # ============================================================

        dashboard_columns = [
            "company_id",
            "company_name",
            "sector",
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "free_cash_flow_cr",
            "total_debt_cr",
            "cash_from_operations_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",
            "profitability_score",
            "leverage_score",
            "interest_coverage_score",
            "cash_flow_score",
            "growth_score",
            "risk_penalty",
            "financial_health_score",
            "health_label",
            "risk_label",
        ]

        dashboard = df[
            [
                col
                for col in dashboard_columns
                if col in df.columns
            ]
        ].copy()

        # ============================================================
        # VALIDATION
        # ============================================================

        print()
        print("=" * 70)
        print("DAY 33 VALIDATION")
        print("=" * 70)

        required_columns = [
            "company_id",
            "sector",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "profitability_score",
            "leverage_score",
            "financial_health_score",
            "health_label",
            "risk_label",
        ]

        print()
        print("Required columns:")

        for column in required_columns:

            if column in df.columns:
                print(f"  ✓ {column}")
            else:
                print(f"  ✗ {column}")

        print()
        print(
            "Companies in output :",
            len(df)
        )

        print(
            "Duplicate companies :",
            df["company_id"].duplicated().sum()
        )

        print()
        print("Financial Health distribution:")

        print(
            df["health_label"]
            .value_counts(dropna=False)
        )

        print()
        print("Risk distribution:")

        print(
            df["risk_label"]
            .value_counts(dropna=False)
        )

        # ============================================================
        # SAVE EXCEL
        # ============================================================

        print()
        print("=" * 70)
        print("SAVING DAY 33 OUTPUTS")
        print("=" * 70)

        with pd.ExcelWriter(
            HEALTH_FILE,
            engine="openpyxl"
        ) as writer:

            dashboard.to_excel(
                writer,
                sheet_name="Financial Health",
                index=False
            )

            ranking.to_excel(
                writer,
                sheet_name="Health Ranking",
                index=False
            )

            sector_df.to_excel(
                writer,
                sheet_name="Sector Risk",
                index=False
            )

            alerts.to_excel(
                writer,
                sheet_name="Risk Alerts",
                index=False
            )

        print(
            f"✓ Saved: {HEALTH_FILE}"
        )

        # ============================================================
        # SAVE CSV FILES
        # ============================================================

        ranking.to_csv(
            RANKING_FILE,
            index=False
        )

        sector_df.to_csv(
            SECTOR_FILE,
            index=False
        )

        dashboard.to_csv(
            DASHBOARD_FILE,
            index=False
        )

        alerts.to_csv(
            ALERT_FILE,
            index=False
        )

        print(
            f"✓ Saved: {RANKING_FILE}"
        )

        print(
            f"✓ Saved: {SECTOR_FILE}"
        )

        print(
            f"✓ Saved: {DASHBOARD_FILE}"
        )

        print(
            f"✓ Saved: {ALERT_FILE}"
        )

        # ============================================================
        # SAMPLE
        # ============================================================

        print()
        print("=" * 70)
        print("SAMPLE FINANCIAL HEALTH")
        print("=" * 70)

        sample_columns = [
            "company_id",
            "company_name",
            "sector",
            "financial_health_score",
            "health_label",
            "risk_label",
            "debt_to_equity",
            "interest_coverage",
            "return_on_equity_pct",
            "net_profit_margin_pct",
        ]

        print(
            dashboard[
                [
                    col
                    for col in sample_columns
                    if col in dashboard.columns
                ]
            ]
            .head(10)
            .to_string(index=False)
        )

        # ============================================================
        # COMPLETION
        # ============================================================

        print()
        print("=" * 70)
        print("SPRINT 5 — DAY 33 COMPLETED")
        print("=" * 70)

        print()
        print("Generated files:")

        print(
            f"  ✓ {HEALTH_FILE}"
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

        print(
            f"  ✓ {ALERT_FILE}"
        )

        print()
        print(
            "Companies processed:",
            len(df)
        )

        print(
            "Companies with health score:",
            df["financial_health_score"].notna().sum()
        )

        print(
            "Risk alerts:",
            len(alerts)
        )

    except Exception as exc:

        print()
        print("=" * 70)
        print("DAY 33 ERROR")
        print("=" * 70)

        print(
            type(exc).__name__,
            ":",
            str(exc)
        )

        raise


if __name__ == "__main__":
    main()