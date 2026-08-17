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
    get_pl,
    get_cf,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("🏢 Company Profile")

st.caption(
    "Detailed financial analysis of NIFTY 100 companies"
)


# ============================================================
# LOAD COMPANIES
# ============================================================

companies = get_companies()

if companies.empty:

    st.error(
        "Company database could not be loaded."
    )

    st.stop()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_number(value):

    if value is None:
        return None

    try:

        value = float(value)

        if pd.isna(value):
            return None

        return value

    except (TypeError, ValueError):

        return None


def fmt(value, suffix=""):

    value = safe_number(value)

    if value is None:
        return "N/A"

    return f"{value:.2f}{suffix}"


def find_column(df, candidates):

    if df.empty:
        return None

    lower_map = {
        str(column).lower(): column
        for column in df.columns
    }

    for candidate in candidates:

        if candidate.lower() in lower_map:

            return lower_map[
                candidate.lower()
            ]

    return None


# ============================================================
# SIDEBAR SEARCH
# ============================================================

st.sidebar.header("Company Search")

search = st.sidebar.text_input(
    "Company name or NSE ticker",
    placeholder="Example: TCS / Tata Consultancy",
)


# ============================================================
# FILTER COMPANIES
# ============================================================

if search:

    search_value = search.strip().upper()

    mask = pd.Series(
        False,
        index=companies.index,
    )

    # Search company name
    if "company_name" in companies.columns:

        mask |= (
            companies["company_name"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.contains(
                search_value,
                na=False,
            )
        )

    # Search company ID / ticker
    if "company_id" in companies.columns:

        mask |= (
            companies["company_id"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.contains(
                search_value,
                na=False,
            )
        )

    matches = companies[mask].copy()

else:

    # IMPORTANT:
    # Show ALL companies instead of only first 20
    matches = companies.copy()


# ============================================================
# COMPANY COUNT
# ============================================================

st.sidebar.caption(
    f"Available companies: {len(matches)}"
)


# ============================================================
# NO MATCHES
# ============================================================

if matches.empty:

    st.error(
        "Company not found — please try another name or ticker."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

def company_label(index):

    row = matches.loc[index]

    name = row.get(
        "company_name",
        "Unknown Company",
    )

    company_id = row.get(
        "company_id",
        "",
    )

    return f"{name} ({company_id})"


selected_index = st.selectbox(
    "Select Company",
    matches.index.tolist(),
    format_func=company_label,
)


company = matches.loc[selected_index]


# ============================================================
# COMPANY ID
# ============================================================

company_id = str(
    company.get(
        "company_id",
        "",
    )
)


company_name = company.get(
    "company_name",
    "Company",
)


# ============================================================
# COMPANY HEADER
# ============================================================

st.divider()

st.header(
    f"🏢 {company_name}"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "NSE Ticker",
        company_id,
    )


with col2:

    st.metric(
        "Sector",
        company.get(
            "sector",
            "N/A",
        ),
    )


with col3:

    st.metric(
        "Sub-Sector",
        company.get(
            "sub_sector",
            "N/A",
        ),
    )


with col4:

    st.metric(
        "Company ID",
        company_id,
    )


# ============================================================
# COMPANY ABOUT
# ============================================================

about = company.get(
    "about_company",
    None,
)


if (
    about is not None
    and not pd.isna(about)
    and str(about).strip()
):

    st.info(
        str(about)
    )


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

ratios = get_ratios(
    company_id
)


if ratios.empty:

    st.warning(
        f"Financial ratio data is not available for {company_id}."
    )

    st.stop()


# ============================================================
# NORMALIZE YEAR
# ============================================================

if "year" in ratios.columns:

    ratios = ratios.copy()

    ratios["year_numeric"] = pd.to_numeric(
        ratios["year"],
        errors="coerce",
    )

    ratios = ratios.sort_values(
        "year_numeric"
    )


# ============================================================
# LATEST YEAR
# ============================================================

latest = ratios.iloc[-1]


def latest_value(candidates):

    column = find_column(
        ratios,
        candidates,
    )

    if column is None:
        return None

    return latest[column]


# ============================================================
# FINANCIAL METRICS
# ============================================================

roe = latest_value(
    [
        "return_on_equity_pct",
        "roe",
    ]
)


npm = latest_value(
    [
        "net_profit_margin_pct",
        "net_profit_margin",
        "npm",
    ]
)


de = latest_value(
    [
        "debt_to_equity",
        "de",
    ]
)


revenue_cagr = latest_value(
    [
        "revenue_cagr_5yr",
        "revenue_cagr_5y",
        "revenue_cagr",
    ]
)


fcf = latest_value(
    [
        "free_cash_flow_cr",
        "free_cash_flow",
        "fcf",
    ]
)


# ============================================================
# ROCE
# ============================================================

# ROCE is stored in companies table
roce = company.get(
    "roce_percentage",
    None,
)


# ============================================================
# KEY FINANCIAL METRICS
# ============================================================

st.subheader(
    "Key Financial Metrics"
)


c1, c2, c3, c4, c5, c6 = st.columns(6)


with c1:

    st.metric(
        "ROE",
        fmt(
            roe,
            "%",
        ),
    )


with c2:

    st.metric(
        "ROCE",
        fmt(
            roce,
            "%",
        ),
    )


with c3:

    st.metric(
        "Net Profit Margin",
        fmt(
            npm,
            "%",
        ),
    )


with c4:

    st.metric(
        "D/E",
        fmt(
            de,
        ),
    )


with c5:

    st.metric(
        "Revenue CAGR 5Y",
        fmt(
            revenue_cagr,
            "%",
        ),
    )


with c6:

    st.metric(
        "FCF",
        fmt(
            fcf,
        ),
    )


# ============================================================
# REVENUE + NET PROFIT
# ============================================================

st.divider()

st.subheader(
    "10-Year Revenue & Net Profit"
)


pl = get_pl(
    company_id
)


if not pl.empty:

    year_col = find_column(
        pl,
        [
            "year",
        ],
    )

    revenue_col = find_column(
        pl,
        [
            "revenue",
            "sales",
            "total_revenue",
        ],
    )

    profit_col = find_column(
        pl,
        [
            "net_profit",
            "net_profit_after_tax",
            "pat",
        ],
    )


    if (
        year_col
        and revenue_col
        and profit_col
    ):

        chart_df = pl[
            [
                year_col,
                revenue_col,
                profit_col,
            ]
        ].copy()


        chart_df["Year"] = (
            chart_df[year_col]
            .astype(str)
        )


        chart_df["Revenue"] = pd.to_numeric(
            chart_df[revenue_col],
            errors="coerce",
        )


        chart_df["Net Profit"] = pd.to_numeric(
            chart_df[profit_col],
            errors="coerce",
        )


        chart_df = chart_df.dropna(
            subset=[
                "Revenue",
                "Net Profit",
            ]
        )


        chart_df = chart_df.tail(10)


        if not chart_df.empty:

            fig = go.Figure()


            fig.add_trace(
                go.Bar(
                    x=chart_df["Year"],
                    y=chart_df["Revenue"],
                    name="Revenue",
                )
            )


            fig.add_trace(
                go.Bar(
                    x=chart_df["Year"],
                    y=chart_df["Net Profit"],
                    name="Net Profit",
                )
            )


            fig.update_layout(
                barmode="group",
                height=500,
                xaxis_title="Year",
                yaxis_title="Amount (₹ Crore)",
                hovermode="x unified",
            )


            st.plotly_chart(
                fig,
                width="stretch",
            )


        else:

            st.info(
                "Insufficient revenue/profit data."
            )


    else:

        st.info(
            "Revenue and Net Profit columns are not available."
        )


else:

    st.info(
        "Profit & Loss data is unavailable."
    )


# ============================================================
# ROE TREND
# ============================================================

st.divider()

st.subheader(
    "ROE Trend"
)


roe_column = find_column(
    ratios,
    [
        "return_on_equity_pct",
        "roe",
    ],
)


year_column = find_column(
    ratios,
    [
        "year",
    ],
)


if (
    roe_column
    and year_column
):

    trend = ratios[
        [
            year_column,
            roe_column,
        ]
    ].copy()


    trend["Year"] = (
        trend[year_column]
        .astype(str)
    )


    trend["ROE"] = pd.to_numeric(
        trend[roe_column],
        errors="coerce",
    )


    trend = trend.dropna(
        subset=[
            "ROE",
        ]
    ).tail(10)


    if not trend.empty:

        fig = go.Figure()


        fig.add_trace(
            go.Scatter(
                x=trend["Year"],
                y=trend["ROE"],
                mode="lines+markers",
                name="ROE",
            )
        )


        fig.update_layout(
            height=450,
            xaxis_title="Year",
            yaxis_title="ROE (%)",
            hovermode="x unified",
        )


        st.plotly_chart(
            fig,
            width="stretch",
        )


    else:

        st.info(
            "No sufficient ROE history."
        )


else:

    st.info(
        "ROE historical data unavailable."
    )


# ============================================================
# INVESTMENT VIEW
# ============================================================

st.divider()

st.subheader(
    "Investment View"
)


pros = []
cons = []


roe_value = safe_number(
    roe
)


de_value = safe_number(
    de
)


npm_value = safe_number(
    npm
)


revenue_value = safe_number(
    revenue_cagr
)


# ============================================================
# ROE
# ============================================================

if roe_value is not None:

    if roe_value >= 15:

        pros.append(
            f"Strong ROE of {roe_value:.2f}%"
        )

    elif roe_value < 8:

        cons.append(
            f"Low ROE of {roe_value:.2f}%"
        )


# ============================================================
# DEBT
# ============================================================

if de_value is not None:

    if de_value <= 0.5:

        pros.append(
            f"Moderate leverage with D/E of {de_value:.2f}"
        )

    elif de_value > 2:

        cons.append(
            f"High leverage with D/E of {de_value:.2f}"
        )


# ============================================================
# NET MARGIN
# ============================================================

if npm_value is not None:

    if npm_value >= 15:

        pros.append(
            f"Healthy net margin of {npm_value:.2f}%"
        )

    elif npm_value < 5:

        cons.append(
            f"Low net margin of {npm_value:.2f}%"
        )


# ============================================================
# REVENUE CAGR
# ============================================================

if revenue_value is not None:

    if revenue_value >= 10:

        pros.append(
            f"Strong 5-year revenue CAGR of {revenue_value:.2f}%"
        )

    elif revenue_value < 0:

        cons.append(
            f"Negative 5-year revenue CAGR of {revenue_value:.2f}%"
        )


# ============================================================
# DISPLAY PROS / CONS
# ============================================================

col1, col2 = st.columns(2)


with col1:

    st.markdown(
        "### ✅ Pros"
    )

    if pros:

        for item in pros:

            st.success(
                item
            )

    else:

        st.write(
            "No strong positive signals identified."
        )


with col2:

    st.markdown(
        "### ⚠️ Cons"
    )

    if cons:

        for item in cons:

            st.warning(
                item
            )

    else:

        st.write(
            "No major negative signals identified."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Company: {company_name} | "
    f"ID: {company_id} | "
    f"Financial records: {len(ratios)}"
)