import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from Script.dashboard.utils.db import (
    get_companies,
    get_all_ratios,
)


# ============================================================
# PAGE
# ============================================================

st.title("🏠 Nifty 100 Analytics")

st.caption(
    "NIFTY 100 Financial Intelligence Platform"
)


# ============================================================
# YEAR SELECTOR
# ============================================================

st.sidebar.header("Dashboard Filters")

selected_year = st.sidebar.selectbox(
    "Select Financial Year",
    list(range(2024, 2018, -1)),
    index=0,
)


# ============================================================
# LOAD DATA
# ============================================================

companies = get_companies()

ratios = get_all_ratios(
    selected_year
)


if companies.empty:

    st.error(
        "Company data could not be loaded."
    )

    st.stop()


# ============================================================
# MERGE
# ============================================================

if not ratios.empty:

    dashboard = companies.merge(
        ratios,
        on="company_id",
        how="left",
    )

else:

    dashboard = companies.copy()


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "return_on_equity_pct",
    "debt_to_equity",
    "net_profit_margin_pct",
    "revenue_cagr_5yr",
    "composite_quality_score",
    "free_cash_flow_cr",
    "earnings_per_share",
    "book_value_per_share",
]


for column in numeric_columns:

    if column in dashboard.columns:

        dashboard[column] = pd.to_numeric(
            dashboard[column],
            errors="coerce",
        )


# ============================================================
# HELPERS
# ============================================================

def median(column):

    if column not in dashboard.columns:
        return None

    values = dashboard[column].dropna()

    if values.empty:
        return None

    return values.median()


def mean(column):

    if column not in dashboard.columns:
        return None

    values = dashboard[column].dropna()

    if values.empty:
        return None

    return values.mean()


def format_value(value, suffix=""):

    if value is None or pd.isna(value):
        return "N/A"

    return f"{value:.2f}{suffix}"


# ============================================================
# KPI VALUES
# ============================================================

average_roe = mean(
    "return_on_equity_pct"
)

median_de = median(
    "debt_to_equity"
)

median_revenue_cagr = median(
    "revenue_cagr_5yr"
)

total_companies = len(companies)


# Debt-free = D/E <= 0.05

if "debt_to_equity" in dashboard.columns:

    debt_free = int(
        (
            dashboard["debt_to_equity"]
            .fillna(float("inf"))
            <= 0.05
        ).sum()
    )

else:

    debt_free = 0


# ============================================================
# P/E
# ============================================================
#
# P/E is NOT present in financial_ratios.
# It will be handled properly in the valuation module.
# For Day 23, display N/A rather than inventing a value.
# ============================================================

median_pe = None


# ============================================================
# KPI CARDS
# ============================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)


with c1:

    st.metric(
        "Average ROE",
        format_value(
            average_roe,
            "%",
        ),
    )


with c2:

    st.metric(
        "Median P/E",
        format_value(
            median_pe
        ),
    )


with c3:

    st.metric(
        "Median D/E",
        format_value(
            median_de
        ),
    )


with c4:

    st.metric(
        "Total Companies",
        total_companies,
    )


with c5:

    st.metric(
        "Median Revenue CAGR 5Y",
        format_value(
            median_revenue_cagr,
            "%",
        ),
    )


with c6:

    st.metric(
        "Debt-Free Companies",
        debt_free,
    )


# ============================================================
# SECTOR BREAKDOWN
# ============================================================

st.divider()

st.subheader(
    f"Sector Breakdown — {selected_year}"
)


if "sector" in dashboard.columns:

    sector_data = (
        dashboard[
            "sector"
        ]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    sector_data.columns = [
        "sector",
        "company_count",
    ]

    fig = px.pie(
        sector_data,
        names="sector",
        values="company_count",
        hole=0.45,
        title="Companies by Sector",
    )

    fig.update_layout(
        height=500,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

else:

    st.warning(
        "Sector information is unavailable."
    )


# ============================================================
# TOP 5 QUALITY COMPANIES
# ============================================================

st.divider()

st.subheader(
    f"Top 5 Companies by Composite Quality Score — "
    f"{selected_year}"
)


if "composite_quality_score" in dashboard.columns:

    top5 = (
        dashboard[
            dashboard[
                "composite_quality_score"
            ].notna()
        ]
        .sort_values(
            "composite_quality_score",
            ascending=False,
        )
        .head(5)
        .copy()
    )

    if not top5.empty:

        output = pd.DataFrame()

        output["Company ID"] = (
            top5["company_id"]
        )

        output["Company Name"] = (
            top5["company_name"]
        )

        output["Sector"] = (
            top5["sector"]
        )

        output["Quality Score"] = (
            top5[
                "composite_quality_score"
            ]
        )

        output["ROE"] = (
            top5[
                "return_on_equity_pct"
            ]
        )

        output["D/E"] = (
            top5[
                "debt_to_equity"
            ]
        )

        st.dataframe(
            output,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            f"No quality-score data available "
            f"for {selected_year}."
        )

else:

    st.info(
        "Composite quality score is unavailable."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Database: nifty100.db | "
    f"Financial Year: {selected_year} | "
    f"Companies: {total_companies}"
)