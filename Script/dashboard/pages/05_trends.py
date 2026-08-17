import sys
from pathlib import Path

import pandas as pd
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
    get_ratios,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("📈 Trend Analysis")

st.caption(
    "10-year financial performance and multi-metric trend analysis"
)


# ============================================================
# LOAD COMPANIES
# ============================================================

companies = get_companies()

if companies.empty:

    st.error("Company data could not be loaded.")

    st.stop()


# ============================================================
# HELPER
# ============================================================

def safe_numeric(series):

    return pd.to_numeric(
        series,
        errors="coerce"
    )


# ============================================================
# COMPANY SEARCH
# ============================================================

st.sidebar.header("Trend Filters")

search = st.sidebar.text_input(
    "Search Company",
    placeholder="Example: ABB / TCS / Reliance"
)


if search:

    search_value = search.strip().lower()

    mask = (
        companies["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False
        )
    )

    matches = companies[mask]

else:

    matches = companies.copy()


if matches.empty:

    st.warning(
        "No company found. Please try another company name."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

def company_label(index):

    row = matches.loc[index]

    name = row.get(
        "company_name",
        "Unknown"
    )

    company_id = row.get(
        "company_id",
        ""
    )

    return f"{name} ({company_id})"


selected_index = st.sidebar.selectbox(
    "Select Company",
    matches.index.tolist(),
    format_func=company_label
)


company = matches.loc[selected_index]

company_id = str(
    company["company_id"]
)

company_name = company.get(
    "company_name",
    company_id
)


# ============================================================
# COMPANY HEADER
# ============================================================

st.header(
    f"{company_name} — Financial Trends"
)

c1, c2, c3, c4 = st.columns(4)

with c1:

    st.metric(
        "Company ID",
        company_id
    )

with c2:

    st.metric(
        "Sector",
        company.get(
            "sector",
            "N/A"
        )
    )

with c3:

    st.metric(
        "Sub-Sector",
        company.get(
            "sub_sector",
            "N/A"
        )
    )

with c4:

    st.metric(
        "ROE",
        (
            f"{company.get('roe_percentage', 0):.2f}%"
            if pd.notna(
                company.get(
                    "roe_percentage",
                    None
                )
            )
            else "N/A"
        )
    )


# ============================================================
# LOAD RATIOS
# ============================================================

ratios = get_ratios(company_id)


if ratios.empty:

    st.warning(
        f"No financial ratio history available for {company_name}."
    )

    st.stop()


ratios = ratios.copy()


# ============================================================
# NORMALIZE YEAR
# ============================================================

if "year" not in ratios.columns:

    st.error(
        "Year column is missing from financial ratios."
    )

    st.stop()


ratios["Year"] = pd.to_numeric(
    ratios["year"],
    errors="coerce"
)


ratios = ratios.dropna(
    subset=["Year"]
)


ratios["Year"] = (
    ratios["Year"]
    .astype(int)
)


ratios = ratios.sort_values(
    "Year"
)


# ============================================================
# AVAILABLE METRICS
# ============================================================

metric_columns = {

    "ROE (%)":
        "return_on_equity_pct",

    "Net Profit Margin (%)":
        "net_profit_margin_pct",

    "Operating Profit Margin (%)":
        "operating_profit_margin_pct",

    "Debt to Equity":
        "debt_to_equity",

    "Interest Coverage":
        "interest_coverage",

    "Asset Turnover":
        "asset_turnover",

    "Revenue CAGR 5Y (%)":
        "revenue_cagr_5yr",

    "PAT CAGR 5Y (%)":
        "pat_cagr_5yr",

    "EPS CAGR 5Y (%)":
        "eps_cagr_5yr",

    "Composite Quality Score":
        "composite_quality_score",

    "Free Cash Flow (₹ Cr)":
        "free_cash_flow_cr",

    "Cash From Operations (₹ Cr)":
        "cash_from_operations_cr",

    "Total Debt (₹ Cr)":
        "total_debt_cr",

    "Capex (₹ Cr)":
        "capex_cr",

    "EPS":
        "earnings_per_share",

    "Book Value Per Share":
        "book_value_per_share",

    "Dividend Payout (%)":
        "dividend_payout_ratio_pct",
}


available_metrics = {
    label: column
    for label, column in metric_columns.items()
    if column in ratios.columns
}


# ============================================================
# METRIC SELECTOR
# ============================================================

st.divider()

st.subheader(
    "Select Financial Metrics"
)

default_metrics = [
    metric
    for metric in [
        "ROE (%)",
        "Net Profit Margin (%)",
        "Operating Profit Margin (%)",
    ]
    if metric in available_metrics
]


selected_metrics = st.multiselect(
    "Choose up to 3 metrics",
    options=list(available_metrics.keys()),
    default=default_metrics[:3],
    max_selections=3
)


if not selected_metrics:

    st.info(
        "Please select at least one financial metric."
    )

    st.stop()


# ============================================================
# TREND DATA
# ============================================================

trend = ratios[
    ["Year"] +
    [
        available_metrics[m]
        for m in selected_metrics
    ]
].copy()


# Rename columns

rename_map = {
    available_metrics[m]: m
    for m in selected_metrics
}

trend = trend.rename(
    columns=rename_map
)


for metric in selected_metrics:

    trend[metric] = safe_numeric(
        trend[metric]
    )


# ============================================================
# DISPLAY YEARS
# ============================================================

min_year = int(
    trend["Year"].min()
)

max_year = int(
    trend["Year"].max()
)


st.caption(
    f"Available financial history: {min_year} – {max_year}"
)


# ============================================================
# TREND CHART
# ============================================================

st.subheader(
    "Multi-Metric Financial Trend"
)


fig = go.Figure()


for metric in selected_metrics:

    fig.add_trace(
        go.Scatter(
            x=trend["Year"],
            y=trend[metric],
            mode="lines+markers",
            name=metric,
        )
    )


fig.update_layout(

    height=550,

    xaxis_title="Financial Year",

    yaxis_title="Metric Value",

    hovermode="x unified",

    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
    ),

    margin=dict(
        l=40,
        r=40,
        t=80,
        b=40,
    ),
)


st.plotly_chart(
    fig,
    width="stretch"
)


# ============================================================
# YEAR-ON-YEAR TABLE
# ============================================================

st.divider()

st.subheader(
    "Historical Financial Metrics"
)


display_df = trend.copy()

display_df = display_df.sort_values(
    "Year",
    ascending=False
)


st.dataframe(
    display_df,
    width="stretch",
    hide_index=True
)


# ============================================================
# LATEST VS EARLIEST
# ============================================================

st.divider()

st.subheader(
    "Performance Change"
)


first_row = trend.iloc[0]

last_row = trend.iloc[-1]


columns = st.columns(
    len(selected_metrics)
)


for i, metric in enumerate(
    selected_metrics
):

    first_value = pd.to_numeric(
        first_row[metric],
        errors="coerce"
    )

    last_value = pd.to_numeric(
        last_row[metric],
        errors="coerce"
    )


    with columns[i]:

        if (
            pd.notna(first_value)
            and pd.notna(last_value)
        ):

            change = (
                last_value
                - first_value
            )

            st.metric(
                metric,
                f"{last_value:.2f}",
                delta=f"{change:+.2f}"
            )

        else:

            st.metric(
                metric,
                "N/A"
            )


# ============================================================
# INDIVIDUAL METRIC TRENDS
# ============================================================

st.divider()

st.subheader(
    "Individual Metric Analysis"
)


for metric in selected_metrics:

    metric_df = trend[
        [
            "Year",
            metric
        ]
    ].dropna()


    if metric_df.empty:
        continue


    with st.expander(
        f"{metric} — Detailed Trend",
        expanded=False
    ):

        fig_metric = go.Figure()


        fig_metric.add_trace(
            go.Scatter(
                x=metric_df["Year"],
                y=metric_df[metric],
                mode="lines+markers",
                name=metric,
            )
        )


        fig_metric.update_layout(
            height=400,
            xaxis_title="Financial Year",
            yaxis_title=metric,
            hovermode="x unified",
        )


        st.plotly_chart(
            fig_metric,
            width="stretch"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Company: {company_name} | "
    f"Company ID: {company_id} | "
    f"History: {min_year}–{max_year} | "
    f"Metrics displayed: {len(selected_metrics)}"
)