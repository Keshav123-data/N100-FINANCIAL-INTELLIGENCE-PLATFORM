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

st.title("💰 Capital Allocation Map")

st.caption(
    "Analyze how NIFTY 100 companies allocate capital "
    "through capex, debt, cash generation and shareholder payouts."
)


# ============================================================
# LOAD DATA
# ============================================================

companies = get_companies()
ratios = get_all_ratios()


if companies.empty:

    st.error(
        "Company data could not be loaded."
    )

    st.stop()


# ============================================================
# GET LATEST FINANCIAL YEAR
# ============================================================

if ratios.empty:

    st.error(
        "Financial ratio data is not available."
    )

    st.stop()


ratios = ratios.copy()


if "year_clean" not in ratios.columns:

    ratios["year_clean"] = pd.to_numeric(
        ratios["year"],
        errors="coerce"
    )


ratios = ratios.dropna(
    subset=["year_clean"]
)


# Latest record for each company

latest_ratios = (
    ratios
    .sort_values(
        ["company_id", "year_clean"]
    )
    .groupby(
        "company_id",
        as_index=False
    )
    .tail(1)
)


# ============================================================
# MERGE
# ============================================================

dashboard = companies.merge(
    latest_ratios,
    on="company_id",
    how="left"
)


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [

    "free_cash_flow_cr",

    "capex_cr",

    "cash_from_operations_cr",

    "total_debt_cr",

    "dividend_payout_ratio_pct",

    "earnings_per_share",

    "book_value_per_share",

    "return_on_equity_pct",

    "debt_to_equity",

    "composite_quality_score",

]


for column in numeric_columns:

    if column in dashboard.columns:

        dashboard[column] = pd.to_numeric(
            dashboard[column],
            errors="coerce"
        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Capital Allocation Filters"
)


if "sector" in dashboard.columns:

    sectors = sorted(
        dashboard["sector"]
        .fillna("Unknown")
        .astype(str)
        .unique()
        .tolist()
    )

else:

    sectors = []


selected_sector = st.sidebar.selectbox(
    "Sector",
    ["All Sectors"] + sectors
)


# ============================================================
# FILTER
# ============================================================

if selected_sector == "All Sectors":

    filtered = dashboard.copy()

else:

    filtered = dashboard[
        dashboard["sector"].fillna("Unknown")
        == selected_sector
    ].copy()


# ============================================================
# PAGE KPI CARDS
# ============================================================

st.subheader(
    "Capital Allocation Overview"
)


total_companies = len(filtered)


total_capex = (
    filtered["capex_cr"].sum()
    if "capex_cr" in filtered.columns
    else 0
)


total_fcf = (
    filtered["free_cash_flow_cr"].sum()
    if "free_cash_flow_cr" in filtered.columns
    else 0
)


total_cfo = (
    filtered["cash_from_operations_cr"].sum()
    if "cash_from_operations_cr" in filtered.columns
    else 0
)


total_debt = (
    filtered["total_debt_cr"].sum()
    if "total_debt_cr" in filtered.columns
    else 0
)


c1, c2, c3, c4, c5 = st.columns(5)


with c1:

    st.metric(
        "Companies",
        total_companies
    )


with c2:

    st.metric(
        "Total Capex",
        f"₹{total_capex:,.0f} Cr"
    )


with c3:

    st.metric(
        "Total FCF",
        f"₹{total_fcf:,.0f} Cr"
    )


with c4:

    st.metric(
        "Cash From Operations",
        f"₹{total_cfo:,.0f} Cr"
    )


with c5:

    st.metric(
        "Total Debt",
        f"₹{total_debt:,.0f} Cr"
    )


# ============================================================
# CAPITAL ALLOCATION CLASSIFICATION
# ============================================================

st.divider()

st.subheader(
    "Capital Allocation Pattern"
)


def classify_company(row):

    fcf = row.get(
        "free_cash_flow_cr",
        float("nan")
    )

    capex = row.get(
        "capex_cr",
        float("nan")
    )

    debt = row.get(
        "total_debt_cr",
        float("nan")
    )

    payout = row.get(
        "dividend_payout_ratio_pct",
        float("nan")
    )


    # Safe numeric conversion

    try:
        fcf = float(fcf)
    except:
        fcf = float("nan")


    try:
        capex = float(capex)
    except:
        capex = float("nan")


    try:
        debt = float(debt)
    except:
        debt = float("nan")


    try:
        payout = float(payout)
    except:
        payout = float("nan")


    # --------------------------------------------------------
    # Growth oriented
    # --------------------------------------------------------

    if (
        pd.notna(capex)
        and pd.notna(fcf)
        and capex > 0
        and fcf > 0
        and capex >= abs(fcf) * 0.50
    ):

        return "Growth / Reinvestment"


    # --------------------------------------------------------
    # Shareholder return
    # --------------------------------------------------------

    if (
        pd.notna(payout)
        and payout >= 50
    ):

        return "Shareholder Distribution"


    # --------------------------------------------------------
    # Debt heavy
    # --------------------------------------------------------

    if (
        pd.notna(debt)
        and debt > 0
        and pd.notna(fcf)
        and fcf < 0
    ):

        return "Debt / Funding Pressure"


    # --------------------------------------------------------
    # Cash compounder
    # --------------------------------------------------------

    if (
        pd.notna(fcf)
        and fcf > 0
        and (
            pd.isna(capex)
            or capex < fcf
        )
    ):

        return "Cash Compounder"


    return "Balanced Allocation"


filtered["allocation_pattern"] = (
    filtered.apply(
        classify_company,
        axis=1
    )
)


# ============================================================
# ALLOCATION PATTERN COUNT
# ============================================================

pattern_count = (
    filtered[
        "allocation_pattern"
    ]
    .value_counts()
    .reset_index()
)


pattern_count.columns = [
    "allocation_pattern",
    "company_count"
]


fig = px.bar(
    pattern_count,
    x="allocation_pattern",
    y="company_count",
    text="company_count",
    title="Companies by Capital Allocation Pattern",
)


fig.update_layout(
    height=500,
    xaxis_title="Capital Allocation Pattern",
    yaxis_title="Number of Companies",
)


st.plotly_chart(
    fig,
    width="stretch"
)


# ============================================================
# TREEMAP
# ============================================================

st.divider()

st.subheader(
    "Capital Allocation Treemap"
)


treemap_columns = [
    "sector",
    "allocation_pattern",
    "company_name",
]


treemap_df = filtered[
    [
        column
        for column in treemap_columns
        if column in filtered.columns
    ]
].copy()


if not treemap_df.empty:

    treemap_df["sector"] = (
        treemap_df["sector"]
        .fillna("Unknown")
    )

    treemap_df["allocation_pattern"] = (
        treemap_df["allocation_pattern"]
        .fillna("Unknown")
    )


    # Every company gets equal base weight.

    treemap_df["company_value"] = 1


    fig = px.treemap(
        treemap_df,
        path=[
            "sector",
            "allocation_pattern",
            "company_name",
        ],
        values="company_value",
        title="NIFTY 100 Capital Allocation Structure",
    )


    fig.update_layout(
        height=650
    )


    st.plotly_chart(
        fig,
        width="stretch"
    )


else:

    st.info(
        "Insufficient data for capital allocation treemap."
    )


# ============================================================
# CAPEX VS FREE CASH FLOW
# ============================================================

st.divider()

st.subheader(
    "Capex vs Free Cash Flow"
)


required_columns = [
    "capex_cr",
    "free_cash_flow_cr",
]


if all(
    column in filtered.columns
    for column in required_columns
):

    scatter_df = filtered.dropna(
        subset=required_columns
    ).copy()


    if not scatter_df.empty:

        hover_columns = [
            "company_name",
            "sector",
            "capex_cr",
            "free_cash_flow_cr",
        ]


        fig = px.scatter(
            scatter_df,
            x="capex_cr",
            y="free_cash_flow_cr",
            color="sector",
            hover_name="company_name",
            hover_data=hover_columns,
            title="Capital Expenditure vs Free Cash Flow",
        )


        fig.update_layout(
            height=600,
            xaxis_title="Capex (₹ Cr)",
            yaxis_title="Free Cash Flow (₹ Cr)",
        )


        st.plotly_chart(
            fig,
            width="stretch"
        )


    else:

        st.info(
            "Insufficient Capex / FCF data."
        )


else:

    st.info(
        "Capex or Free Cash Flow data is unavailable."
    )


# ============================================================
# COMPANY TABLE
# ============================================================

st.divider()

st.subheader(
    "Capital Allocation by Company"
)


display_columns = [

    "company_id",

    "company_name",

    "sector",

    "allocation_pattern",

    "capex_cr",

    "free_cash_flow_cr",

    "cash_from_operations_cr",

    "total_debt_cr",

    "dividend_payout_ratio_pct",

]


display_columns = [
    column
    for column in display_columns
    if column in filtered.columns
]


display_df = filtered[
    display_columns
].copy()


if "free_cash_flow_cr" in display_df.columns:

    display_df = display_df.sort_values(
        "free_cash_flow_cr",
        ascending=False,
        na_position="last"
    )


st.dataframe(
    display_df,
    width="stretch",
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

latest_year = int(
    latest_ratios["year_clean"].max()
)


st.caption(
    f"Capital Allocation Analysis | "
    f"Financial Year: {latest_year} | "
    f"Companies: {len(filtered)}"
)