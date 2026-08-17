import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

st.title("🏭 Sector Analysis")

st.caption(
    "Sector-wise financial performance and KPI comparison"
)


# ============================================================
# LOAD DATA
# ============================================================

companies = get_companies()
ratios = get_all_ratios()


if companies.empty:
    st.error("Company data could not be loaded.")
    st.stop()


# ============================================================
# MERGE
# ============================================================

if not ratios.empty:

    latest_ratios = (
        ratios
        .sort_values(
            ["company_id", "year_clean"]
            if "year_clean" in ratios.columns
            else ["company_id"]
        )
        .groupby("company_id", as_index=False)
        .tail(1)
    )

    dashboard = companies.merge(
        latest_ratios,
        on="company_id",
        how="left"
    )

else:

    dashboard = companies.copy()


# ============================================================
# CLEAN NUMERIC DATA
# ============================================================

numeric_columns = [
    "return_on_equity_pct",
    "debt_to_equity",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "free_cash_flow_cr",
    "cash_from_operations_cr",
    "total_debt_cr",
    "composite_quality_score",
]


for column in numeric_columns:

    if column in dashboard.columns:

        dashboard[column] = pd.to_numeric(
            dashboard[column],
            errors="coerce"
        )


# ============================================================
# SECTOR CLEANING
# ============================================================

if "sector" not in dashboard.columns:

    st.error(
        "Sector column is not available in the database."
    )

    st.stop()


dashboard["sector"] = (
    dashboard["sector"]
    .fillna("Unknown")
    .astype(str)
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("Sector Filters")


sectors = sorted(
    dashboard["sector"]
    .dropna()
    .unique()
    .tolist()
)


selected_sector = st.sidebar.selectbox(
    "Select Sector",
    ["All Sectors"] + sectors
)


# ============================================================
# FILTER
# ============================================================

if selected_sector == "All Sectors":

    filtered = dashboard.copy()

else:

    filtered = dashboard[
        dashboard["sector"] == selected_sector
    ].copy()


# ============================================================
# KPI CARDS
# ============================================================

st.subheader("Sector Overview")


total_companies = len(filtered)


average_roe = (
    filtered["return_on_equity_pct"].median()
    if "return_on_equity_pct" in filtered.columns
    else None
)


average_npm = (
    filtered["net_profit_margin_pct"].median()
    if "net_profit_margin_pct" in filtered.columns
    else None
)


average_de = (
    filtered["debt_to_equity"].median()
    if "debt_to_equity" in filtered.columns
    else None
)


average_revenue_cagr = (
    filtered["revenue_cagr_5yr"].median()
    if "revenue_cagr_5yr" in filtered.columns
    else None
)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Companies",
        total_companies
    )


with c2:

    st.metric(
        "Median ROE",
        (
            f"{average_roe:.2f}%"
            if pd.notna(average_roe)
            else "N/A"
        )
    )


with c3:

    st.metric(
        "Median Net Margin",
        (
            f"{average_npm:.2f}%"
            if pd.notna(average_npm)
            else "N/A"
        )
    )


with c4:

    st.metric(
        "Median D/E",
        (
            f"{average_de:.2f}"
            if pd.notna(average_de)
            else "N/A"
        )
    )


# ============================================================
# SECTOR COMPANY COUNT
# ============================================================

st.divider()

st.subheader("Companies by Sector")


sector_count = (
    dashboard
    .groupby("sector")
    .size()
    .reset_index(name="company_count")
    .sort_values(
        "company_count",
        ascending=False
    )
)


fig = px.bar(
    sector_count,
    x="sector",
    y="company_count",
    text="company_count",
    title="NIFTY 100 Companies by Sector",
)


fig.update_layout(
    height=500,
    xaxis_title="Sector",
    yaxis_title="Number of Companies",
)


st.plotly_chart(
    fig,
    width="stretch"
)


# ============================================================
# REVENUE GROWTH VS ROE
# ============================================================

st.divider()

st.subheader(
    "Revenue Growth vs ROE"
)


required = [
    "revenue_cagr_5yr",
    "return_on_equity_pct",
]


if all(
    column in filtered.columns
    for column in required
):

    scatter_df = filtered.dropna(
        subset=required
    ).copy()


    if not scatter_df.empty:

        hover_columns = [
            "company_name",
            "sector",
            "revenue_cagr_5yr",
            "return_on_equity_pct",
        ]


# ============================================================
# SAFE BUBBLE SIZE
# ============================================================

        if "free_cash_flow_cr" in scatter_df.columns:

            scatter_df["bubble_size"] = pd.to_numeric(
                scatter_df["free_cash_flow_cr"],
                errors="coerce"
            )

    # Negative FCF cannot be used as Plotly bubble size
            scatter_df["bubble_size"] = (
                scatter_df["bubble_size"]
                .abs()
                .fillna(1)
                .clip(lower=1)
            )

            size_column = "bubble_size"

        else:

            size_column = None


        fig = px.scatter(
            scatter_df,
            x="revenue_cagr_5yr",
            y="return_on_equity_pct",
            size=size_column,
            color="sector",
            hover_name="company_name",
            hover_data=hover_columns,
            title="Revenue CAGR vs ROE",
        )


        fig.update_layout(
            height=600,
            xaxis_title="Revenue CAGR 5Y (%)",
            yaxis_title="ROE (%)",
        )


        st.plotly_chart(
            fig,
            width="stretch"
        )

    else:

        st.info(
            "Insufficient data for Revenue CAGR vs ROE."
        )

else:

    st.info(
        "Required Revenue CAGR or ROE data is unavailable."
    )


# ============================================================
# SECTOR MEDIAN KPIs
# ============================================================

st.divider()

st.subheader(
    "Sector Median KPI Comparison"
)


kpi_columns = {
    "ROE (%)": "return_on_equity_pct",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Operating Margin (%)": "operating_profit_margin_pct",
    "D/E": "debt_to_equity",
    "Revenue CAGR 5Y (%)": "revenue_cagr_5yr",
    "PAT CAGR 5Y (%)": "pat_cagr_5yr",
    "EPS CAGR 5Y (%)": "eps_cagr_5yr",
}


available_kpis = {
    name: column
    for name, column in kpi_columns.items()
    if column in dashboard.columns
}


if available_kpis:

    sector_kpi = (
        dashboard
        .groupby("sector")[
            list(available_kpis.values())
        ]
        .median()
        .reset_index()
    )


    sector_kpi = sector_kpi.rename(
        columns={
            column: name
            for name, column in available_kpis.items()
        }
    )


    st.dataframe(
        sector_kpi,
        width="stretch",
        hide_index=True
    )

else:

    st.info(
        "No sector KPI data available."
    )


# ============================================================
# SELECTED SECTOR DETAILS
# ============================================================

if selected_sector != "All Sectors":

    st.divider()

    st.subheader(
        f"{selected_sector} — Company Analysis"
    )


    detail_columns = [
        "company_id",
        "company_name",
        "sector",
        "return_on_equity_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "composite_quality_score",
    ]


    detail_columns = [
        column
        for column in detail_columns
        if column in filtered.columns
    ]


    detail_df = (
        filtered[detail_columns]
        .sort_values(
            "composite_quality_score",
            ascending=False,
            na_position="last"
        )
    )


    st.dataframe(
        detail_df,
        width="stretch",
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Sector Analysis | "
    f"Companies displayed: {len(filtered)}"
)