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
    get_valuation,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("🔎 Stock Screener")

st.caption(
    "Filter NIFTY 100 companies using financial, "
    "valuation and quality metrics."
)


# ============================================================
# LOAD COMPANY DATA
# ============================================================

companies = get_companies()

if companies.empty:

    st.error(
        "Company database could not be loaded."
    )

    st.stop()


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

ratios = get_all_ratios()

if ratios.empty:

    st.error(
        "Financial ratio data could not be loaded."
    )

    st.stop()


# ============================================================
# KEEP LATEST YEAR FOR EACH COMPANY
# ============================================================

ratios = ratios.copy()

ratios["year_num"] = pd.to_numeric(
    ratios["year"],
    errors="coerce"
)

ratios = ratios.sort_values(
    ["company_id", "year_num"]
)

latest_ratios = (
    ratios
    .groupby("company_id", as_index=False)
    .tail(1)
    .copy()
)


# ============================================================
# LOAD VALUATION DATA
# ============================================================

valuation_rows = []

for company_id in companies["company_id"]:

    try:

        valuation = get_valuation(
            company_id
        )

        if valuation is not None and not valuation.empty:

            valuation = valuation.copy()

            valuation["company_id"] = company_id

            valuation_rows.append(
                valuation
            )

    except Exception:
        continue


if valuation_rows:

    valuation_df = pd.concat(
        valuation_rows,
        ignore_index=True
    )

    if "year" in valuation_df.columns:

        valuation_df["year_num"] = pd.to_numeric(
            valuation_df["year"],
            errors="coerce"
        )

        valuation_df = (
            valuation_df
            .sort_values(
                ["company_id", "year_num"]
            )
            .groupby(
                "company_id",
                as_index=False
            )
            .tail(1)
        )

else:

    valuation_df = pd.DataFrame()


# ============================================================
# MERGE DATA
# ============================================================

screener = companies.merge(
    latest_ratios,
    on="company_id",
    how="left",
    suffixes=("", "_ratio")
)


if not valuation_df.empty:

    valuation_columns = [
        "company_id",
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    valuation_columns = [
        c
        for c in valuation_columns
        if c in valuation_df.columns
    ]

    screener = screener.merge(
        valuation_df[
            valuation_columns
        ],
        on="company_id",
        how="left"
    )


# ============================================================
# NUMERIC CONVERSION
# ============================================================

numeric_columns = [

    "return_on_equity_pct",
    "debt_to_equity",
    "net_profit_margin_pct",
    "operating_profit_margin_pct",

    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",

    "interest_coverage",
    "asset_turnover",

    "composite_quality_score",

    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",

]


for column in numeric_columns:

    if column in screener.columns:

        screener[column] = pd.to_numeric(
            screener[column],
            errors="coerce"
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Screener Filters")


# ============================================================
# PRESETS
# ============================================================

preset = st.sidebar.selectbox(
    "Preset",
    [
        "Custom",
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt-Free Blue Chip",
    ]
)


# ============================================================
# DEFAULT FILTER VALUES
# ============================================================

roe_min = 0.0
de_max = 999.0
fcf_min = -999999.0
revenue_cagr_min = -999.0
pat_cagr_min = -999.0
opm_min = -999.0
pe_max = 999.0
pb_max = 999.0
dividend_yield_min = 0.0
icr_min = -999.0


# ============================================================
# PRESET LOGIC
# ============================================================

if preset == "Quality Compounder":

    roe_min = 15
    de_max = 1.0
    fcf_min = 0


elif preset == "Value Pick":

    pe_max = 20
    pb_max = 3
    de_max = 2
    dividend_yield_min = 1


elif preset == "Growth Accelerator":

    pat_cagr_min = 20
    revenue_cagr_min = 15
    de_max = 2


elif preset == "Dividend Champion":

    dividend_yield_min = 2
    fcf_min = 0


elif preset == "Debt-Free Blue Chip":

    de_max = 0
    roe_min = 12


# ============================================================
# CUSTOM FILTERS
# ============================================================

if preset == "Custom":

    roe_min = st.sidebar.number_input(
        "Minimum ROE (%)",
        min_value=-100.0,
        max_value=200.0,
        value=0.0,
        step=1.0,
    )

    de_max = st.sidebar.number_input(
        "Maximum D/E",
        min_value=0.0,
        max_value=20.0,
        value=999.0,
        step=0.1,
    )

    fcf_min = st.sidebar.number_input(
        "Minimum FCF (₹ Cr)",
        value=-999999.0,
        step=100.0,
    )

    revenue_cagr_min = st.sidebar.number_input(
        "Minimum Revenue CAGR 5Y (%)",
        min_value=-100.0,
        max_value=200.0,
        value=-999.0,
        step=1.0,
    )

    pat_cagr_min = st.sidebar.number_input(
        "Minimum PAT CAGR 5Y (%)",
        min_value=-100.0,
        max_value=200.0,
        value=-999.0,
        step=1.0,
    )

    opm_min = st.sidebar.number_input(
        "Minimum OPM (%)",
        min_value=-100.0,
        max_value=200.0,
        value=-999.0,
        step=1.0,
    )

    pe_max = st.sidebar.number_input(
        "Maximum P/E",
        min_value=0.0,
        max_value=500.0,
        value=999.0,
        step=1.0,
    )

    pb_max = st.sidebar.number_input(
        "Maximum P/B",
        min_value=0.0,
        max_value=100.0,
        value=999.0,
        step=0.5,
    )

    dividend_yield_min = st.sidebar.number_input(
        "Minimum Dividend Yield (%)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=0.5,
    )

    icr_min = st.sidebar.number_input(
        "Minimum Interest Coverage",
        min_value=-100.0,
        max_value=100.0,
        value=-999.0,
        step=0.5,
    )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = screener.copy()


if "return_on_equity_pct" in filtered.columns:

    filtered = filtered[
        filtered["return_on_equity_pct"]
        .fillna(-999999)
        >= roe_min
    ]


if "debt_to_equity" in filtered.columns:

    filtered = filtered[
        filtered["debt_to_equity"]
        .fillna(999999)
        <= de_max
    ]


if "free_cash_flow_cr" in filtered.columns:

    filtered = filtered[
        filtered["free_cash_flow_cr"]
        .fillna(-999999)
        >= fcf_min
    ]


if "revenue_cagr_5yr" in filtered.columns:

    filtered = filtered[
        filtered["revenue_cagr_5yr"]
        .fillna(-999999)
        >= revenue_cagr_min
    ]


if "pat_cagr_5yr" in filtered.columns:

    filtered = filtered[
        filtered["pat_cagr_5yr"]
        .fillna(-999999)
        >= pat_cagr_min
    ]


if "operating_profit_margin_pct" in filtered.columns:

    filtered = filtered[
        filtered["operating_profit_margin_pct"]
        .fillna(-999999)
        >= opm_min
    ]


if "pe_ratio" in filtered.columns:

    filtered = filtered[
        (
            filtered["pe_ratio"].isna()
            |
            (
                filtered["pe_ratio"]
                <= pe_max
            )
        )
    ]


if "pb_ratio" in filtered.columns:

    filtered = filtered[
        (
            filtered["pb_ratio"].isna()
            |
            (
                filtered["pb_ratio"]
                <= pb_max
            )
        )
    ]


if "dividend_yield_pct" in filtered.columns:

    filtered = filtered[
        filtered["dividend_yield_pct"]
        .fillna(0)
        >= dividend_yield_min
    ]


if "interest_coverage" in filtered.columns:

    filtered = filtered[
        filtered["interest_coverage"]
        .fillna(-999999)
        >= icr_min
    ]


# ============================================================
# SEARCH
# ============================================================

search = st.sidebar.text_input(
    "Search company",
    placeholder="Example: TCS"
)


if search:

    search = search.strip().lower()

    filtered = filtered[
        filtered["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search,
            na=False
        )
        |
        filtered["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(
            search,
            na=False
        )
    ]


# ============================================================
# KPI SUMMARY
# ============================================================

st.divider()

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Companies Matched",
        len(filtered)
    )


with c2:

    if (
        "return_on_equity_pct"
        in filtered.columns
    ):

        value = filtered[
            "return_on_equity_pct"
        ].median()

        st.metric(
            "Median ROE",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%"
        )

    else:

        st.metric(
            "Median ROE",
            "N/A"
        )


with c3:

    if "pe_ratio" in filtered.columns:

        value = filtered[
            "pe_ratio"
        ].median()

        st.metric(
            "Median P/E",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}"
        )

    else:

        st.metric(
            "Median P/E",
            "N/A"
        )


with c4:

    if (
        "composite_quality_score"
        in filtered.columns
    ):

        value = filtered[
            "composite_quality_score"
        ].median()

        st.metric(
            "Median Quality Score",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}"
        )

    else:

        st.metric(
            "Median Quality Score",
            "N/A"
        )


# ============================================================
# RESULTS
# ============================================================

st.divider()

st.subheader(
    f"Screener Results — {preset}"
)


if filtered.empty:

    st.warning(
        "No companies match the selected filters."
    )

    st.stop()


# ============================================================
# SORT
# ============================================================

sort_options = [

    "composite_quality_score",
    "return_on_equity_pct",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "free_cash_flow_cr",
    "pe_ratio",
    "pb_ratio",
    "market_cap_crore",

]

available_sort_options = [
    c
    for c in sort_options
    if c in filtered.columns
]


sort_column = st.selectbox(
    "Rank companies by",
    available_sort_options,
    index=0
)


filtered = filtered.sort_values(
    sort_column,
    ascending=False,
    na_position="last"
).reset_index(drop=True)


# ============================================================
# DISPLAY TABLE
# ============================================================

display_columns = [

    "company_id",
    "company_name",
    "sector",

    "return_on_equity_pct",
    "debt_to_equity",

    "net_profit_margin_pct",
    "operating_profit_margin_pct",

    "revenue_cagr_5yr",
    "pat_cagr_5yr",

    "free_cash_flow_cr",

    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",

    "interest_coverage",
    "composite_quality_score",

]


display_columns = [
    c
    for c in display_columns
    if c in filtered.columns
]


display_df = filtered[
    display_columns
].copy()


# Rename for dashboard

display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sector": "Sector",

        "return_on_equity_pct": "ROE %",
        "debt_to_equity": "D/E",

        "net_profit_margin_pct": "NPM %",
        "operating_profit_margin_pct": "OPM %",

        "revenue_cagr_5yr": "Revenue CAGR 5Y %",
        "pat_cagr_5yr": "PAT CAGR 5Y %",

        "free_cash_flow_cr": "FCF ₹ Cr",

        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield %",

        "interest_coverage": "Interest Coverage",

        "composite_quality_score":
            "Quality Score",
    }
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# DOWNLOAD CSV
# ============================================================

csv = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇ Download Screener CSV",
    data=csv,
    file_name="nifty100_screener.csv",
    mime="text/csv",
)


# ============================================================
# QUALITY SCORE CHART
# ============================================================

if (
    "composite_quality_score"
    in filtered.columns
):

    st.divider()

    st.subheader(
        "Top Companies by Quality Score"
    )

    chart_df = (
        filtered[
            [
                "company_name",
                "composite_quality_score"
            ]
        ]
        .dropna()
        .sort_values(
            "composite_quality_score",
            ascending=False
        )
        .head(15)
    )

    if not chart_df.empty:

        fig = px.bar(
            chart_df,
            x="composite_quality_score",
            y="company_name",
            orientation="h",
            title="Top 15 Quality Companies",
            labels={
                "company_name": "Company",
                "composite_quality_score":
                    "Quality Score"
            },
        )

        fig.update_layout(
            height=600
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# ROE VS P/E
# ============================================================

if (
    "return_on_equity_pct" in filtered.columns
    and "pe_ratio" in filtered.columns
):

    st.divider()

    st.subheader(
        "ROE vs P/E"
    )

    scatter_df = filtered[
        [
            "company_name",
            "return_on_equity_pct",
            "pe_ratio",
            "composite_quality_score"
        ]
    ].dropna(
        subset=[
            "return_on_equity_pct",
            "pe_ratio"
        ]
    )

    if not scatter_df.empty:

        fig = px.scatter(
            scatter_df,
            x="pe_ratio",
            y="return_on_equity_pct",
            size="composite_quality_score"
            if "composite_quality_score"
            in scatter_df.columns
            else None,
            hover_name="company_name",
            title="ROE vs P/E Valuation",
            labels={
                "pe_ratio": "P/E",
                "return_on_equity_pct": "ROE (%)"
            },
        )

        fig.update_layout(
            height=600
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Showing {len(filtered)} of "
    f"{len(screener)} companies | "
    f"Screener: {preset}"
)