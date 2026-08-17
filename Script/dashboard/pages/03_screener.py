import sys
from pathlib import Path

import numpy as np
import pandas as pd
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
    get_sectors,
    get_valuation,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("🔎 Stock Screener")

st.caption(
    "Screen NIFTY 100 companies using profitability, "
    "growth, valuation, leverage and cash-flow metrics."
)


# ============================================================
# HELPERS
# ============================================================

def numeric(series):
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def clean_dataframe(df):

    if df.empty:
        return df

    df = df.copy()

    for column in df.columns:

        if column not in [
            "company_id",
            "company_name",
            "sector",
            "sub_sector",
        ]:

            try:
                df[column] = pd.to_numeric(
                    df[column],
                    errors="ignore",
                )
            except Exception:
                pass

    return df


def latest_by_company(df):

    if df.empty:
        return df

    df = df.copy()

    if "year_clean" in df.columns:

        df = df.sort_values(
            [
                "company_id",
                "year_clean",
            ]
        )

    elif "year" in df.columns:

        df["year_numeric"] = pd.to_numeric(
            df["year"],
            errors="coerce",
        )

        df = df.sort_values(
            [
                "company_id",
                "year_numeric",
            ]
        )

    return (
        df
        .drop_duplicates(
            subset=["company_id"],
            keep="last",
        )
        .reset_index(drop=True)
    )


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data(ttl=600)
def load_screener_data():

    companies = get_companies()

    ratios = get_all_ratios()

    sectors = get_sectors()

    if companies.empty:
        return pd.DataFrame()

    # --------------------------------------------------------
    # COMPANY DATA
    # --------------------------------------------------------

    company_columns = [
        "company_id",
        "company_name",
        "sector",
        "sub_sector",
        "market_cap_category",
    ]

    company_columns = [
        c
        for c in company_columns
        if c in companies.columns
    ]

    company_df = companies[
        company_columns
    ].drop_duplicates(
        subset=["company_id"]
    )

    # --------------------------------------------------------
    # RATIOS
    # --------------------------------------------------------

    if not ratios.empty:

        ratios = ratios.copy()

        if "year_clean" not in ratios.columns:

            ratios["year_clean"] = pd.to_numeric(
                ratios["year"]
                .astype(str)
                .str.extract(
                    r"(\d{4})"
                )[0],
                errors="coerce",
            )

        ratios = latest_by_company(
            ratios
        )

    # --------------------------------------------------------
    # SECTORS
    # --------------------------------------------------------

    if not sectors.empty:

        sector_columns = [
            "company_id",
            "broad_sector",
            "sub_sector",
        ]

        sector_columns = [
            c
            for c in sector_columns
            if c in sectors.columns
        ]

        sector_df = (
            sectors[sector_columns]
            .drop_duplicates(
                subset=["company_id"]
            )
        )

    else:

        sector_df = pd.DataFrame()

    # --------------------------------------------------------
    # MERGE
    # --------------------------------------------------------

    df = company_df.copy()

    if not ratios.empty:

        ratio_columns = [
            "company_id",
            "year",
            "year_clean",
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

        ratio_columns = [
            c
            for c in ratio_columns
            if c in ratios.columns
        ]

        df = df.merge(
            ratios[ratio_columns],
            on="company_id",
            how="left",
        )

    if not sector_df.empty:

        df = df.merge(
            sector_df,
            on="company_id",
            how="left",
            suffixes=("", "_sector"),
        )

    # --------------------------------------------------------
    # VALUATION DATA
    # --------------------------------------------------------

    valuation_frames = []

    for company_id in df["company_id"].dropna().unique():

        try:

            valuation = get_valuation(
                company_id
            )

            if not valuation.empty:

                valuation_frames.append(
                    valuation
                )

        except Exception:
            continue

    if valuation_frames:

        valuation_df = pd.concat(
            valuation_frames,
            ignore_index=True,
        )

        if "year" in valuation_df.columns:

            valuation_df["year_numeric"] = (
                pd.to_numeric(
                    valuation_df["year"],
                    errors="coerce",
                )
            )

            valuation_df = (
                valuation_df
                .sort_values(
                    [
                        "company_id",
                        "year_numeric",
                    ]
                )
                .drop_duplicates(
                    subset=["company_id"],
                    keep="last",
                )
            )

        valuation_columns = [
            "company_id",
            "year",
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

        df = df.merge(
            valuation_df[
                valuation_columns
            ],
            on="company_id",
            how="left",
            suffixes=("", "_valuation"),
        )

    # --------------------------------------------------------
    # NORMALIZE NUMERIC COLUMNS
    # --------------------------------------------------------

    numeric_columns = [
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
        "market_cap_crore",
        "enterprise_value_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "dividend_yield_pct",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = numeric(
                df[column]
            )

    # --------------------------------------------------------
    # FRIENDLY COLUMN NAMES
    # --------------------------------------------------------

    rename_map = {

        "return_on_equity_pct":
            "roe",

        "net_profit_margin_pct":
            "npm",

        "operating_profit_margin_pct":
            "opm",

        "free_cash_flow_cr":
            "fcf",

        "revenue_cagr_5yr":
            "revenue_cagr_5y",

        "pat_cagr_5yr":
            "pat_cagr_5y",

        "eps_cagr_5yr":
            "eps_cagr_5y",

        "dividend_payout_ratio_pct":
            "dividend_payout_pct",

        "market_cap_crore":
            "market_cap",

        "pe_ratio":
            "pe",

        "pb_ratio":
            "pb",

        "dividend_yield_pct":
            "dividend_yield",
    }

    df = df.rename(
        columns=rename_map
    )

    return clean_dataframe(df)


# ============================================================
# LOAD
# ============================================================

with st.spinner(
    "Loading NIFTY 100 financial data..."
):

    data = load_screener_data()


if data.empty:

    st.error(
        "Unable to load screener data."
    )

    st.stop()


# ============================================================
# HEADER KPIs
# ============================================================

total_companies = len(data)

quality_available = (
    data["composite_quality_score"]
    .notna()
    .sum()
    if "composite_quality_score" in data.columns
    else 0
)

growth_available = (
    data["revenue_cagr_5y"]
    .notna()
    .sum()
    if "revenue_cagr_5y" in data.columns
    else 0
)

valuation_available = (
    data["pe"]
    .notna()
    .sum()
    if "pe" in data.columns
    else 0
)


k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "Companies",
        total_companies,
    )

with k2:
    st.metric(
        "Quality Scores",
        quality_available,
    )

with k3:
    st.metric(
        "Growth Data",
        growth_available,
    )

with k4:
    st.metric(
        "Valuation Data",
        valuation_available,
    )


# ============================================================
# PRESETS
# ============================================================

st.divider()

st.subheader(
    "⭐ Preset Screeners"
)

preset_definitions = {

    "Custom": {},

    "Quality Compounder": {
        "roe_min": 15,
        "de_max": 1.0,
        "fcf_min": 0,
    },

    "Value Pick": {
        "pe_max": 20,
        "pb_max": 3.0,
        "de_max": 2.0,
        "dividend_yield_min": 1,
    },

    "Growth Accelerator": {
        "pat_cagr_5y_min": 20,
        "revenue_cagr_5y_min": 15,
        "de_max": 2.0,
    },

    "Dividend Champion": {
        "dividend_yield_min": 2,
        "dividend_payout_max": 80,
        "fcf_min": 0,
    },

    "Debt-Free Blue Chip": {
        "de_max": 0,
        "roe_min": 12,
    },

    "Turnaround Watch": {
        "revenue_cagr_3y_min": 10,
        "fcf_min": 0,
    },
}


preset = st.selectbox(
    "Choose a preset",
    list(preset_definitions.keys()),
)


preset_filters = preset_definitions[
    preset
]


if preset != "Custom":

    st.info(
        f"Preset loaded: **{preset}**"
    )


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header(
    "🔎 Screener Filters"
)


if st.sidebar.button(
    "Reset Filters",
    width="stretch",
):

    st.rerun()


# ------------------------------------------------------------
# Sector
# ------------------------------------------------------------

sector_values = ["All"]

if "sector" in data.columns:

    sector_values += sorted(
        data["sector"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )


selected_sector = st.sidebar.selectbox(
    "Sector",
    sector_values,
)


# ------------------------------------------------------------
# ROE
# ------------------------------------------------------------

roe_min = st.sidebar.number_input(
    "Minimum ROE (%)",
    min_value=-100.0,
    max_value=200.0,
    value=float(
        preset_filters.get(
            "roe_min",
            0,
        )
    ),
    step=1.0,
)


# ------------------------------------------------------------
# ROCE
# ------------------------------------------------------------

roce_min = st.sidebar.number_input(
    "Minimum ROCE (%)",
    min_value=-100.0,
    max_value=300.0,
    value=0.0,
    step=1.0,
)


# ------------------------------------------------------------
# D/E
# ------------------------------------------------------------

de_max = st.sidebar.number_input(
    "Maximum D/E",
    min_value=0.0,
    max_value=20.0,
    value=float(
        preset_filters.get(
            "de_max",
            20.0,
        )
    ),
    step=0.1,
)


# ------------------------------------------------------------
# P/E
# ------------------------------------------------------------

pe_max = st.sidebar.number_input(
    "Maximum P/E",
    min_value=0.0,
    max_value=500.0,
    value=float(
        preset_filters.get(
            "pe_max",
            500.0,
        )
    ),
    step=1.0,
)


# ------------------------------------------------------------
# P/B
# ------------------------------------------------------------

pb_max = st.sidebar.number_input(
    "Maximum P/B",
    min_value=0.0,
    max_value=100.0,
    value=float(
        preset_filters.get(
            "pb_max",
            100.0,
        )
    ),
    step=0.5,
)


# ------------------------------------------------------------
# Revenue CAGR
# ------------------------------------------------------------

revenue_cagr_min = st.sidebar.number_input(
    "Minimum Revenue CAGR 5Y (%)",
    min_value=-100.0,
    max_value=200.0,
    value=float(
        preset_filters.get(
            "revenue_cagr_5y_min",
            0,
        )
    ),
    step=1.0,
)


# ------------------------------------------------------------
# PAT CAGR
# ------------------------------------------------------------

pat_cagr_min = st.sidebar.number_input(
    "Minimum PAT CAGR 5Y (%)",
    min_value=-100.0,
    max_value=300.0,
    value=float(
        preset_filters.get(
            "pat_cagr_5y_min",
            0,
        )
    ),
    step=1.0,
)


# ------------------------------------------------------------
# EPS CAGR
# ------------------------------------------------------------

eps_cagr_min = st.sidebar.number_input(
    "Minimum EPS CAGR 5Y (%)",
    min_value=-100.0,
    max_value=300.0,
    value=0.0,
    step=1.0,
)


# ------------------------------------------------------------
# Dividend Yield
# ------------------------------------------------------------

dividend_yield_min = st.sidebar.number_input(
    "Minimum Dividend Yield (%)",
    min_value=0.0,
    max_value=50.0,
    value=float(
        preset_filters.get(
            "dividend_yield_min",
            0,
        )
    ),
    step=0.5,
)


# ------------------------------------------------------------
# FCF
# ------------------------------------------------------------

fcf_min = st.sidebar.number_input(
    "Minimum FCF (₹ Cr)",
    min_value=-100000.0,
    max_value=100000.0,
    value=float(
        preset_filters.get(
            "fcf_min",
            -100000,
        )
    ),
    step=100.0,
)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered = data.copy()


def apply_minimum(
    frame,
    column,
    minimum,
):

    if column not in frame.columns:
        return frame

    values = numeric(
        frame[column]
    )

    return frame[
        values.notna()
        & (values >= minimum)
    ].copy()


def apply_maximum(
    frame,
    column,
    maximum,
):

    if column not in frame.columns:
        return frame

    values = numeric(
        frame[column]
    )

    return frame[
        values.notna()
        & (values <= maximum)
    ].copy()


# Sector

if selected_sector != "All":

    filtered = filtered[
        filtered["sector"]
        .astype(str)
        == selected_sector
    ]


filtered = apply_minimum(
    filtered,
    "roe",
    roe_min,
)

filtered = apply_minimum(
    filtered,
    "roce",
    roce_min,
)

filtered = apply_maximum(
    filtered,
    "debt_to_equity",
    de_max,
)

filtered = apply_maximum(
    filtered,
    "pe",
    pe_max,
)

filtered = apply_maximum(
    filtered,
    "pb",
    pb_max,
)

filtered = apply_minimum(
    filtered,
    "revenue_cagr_5y",
    revenue_cagr_min,
)

filtered = apply_minimum(
    filtered,
    "pat_cagr_5y",
    pat_cagr_min,
)

filtered = apply_minimum(
    filtered,
    "eps_cagr_5y",
    eps_cagr_min,
)

filtered = apply_minimum(
    filtered,
    "dividend_yield",
    dividend_yield_min,
)

filtered = apply_minimum(
    filtered,
    "fcf",
    fcf_min,
)


# ============================================================
# RESULTS
# ============================================================

st.divider()

st.subheader(
    "📊 Screening Results"
)

result_count = len(filtered)

if result_count == 0:

    st.warning(
        "No companies match the selected criteria."
    )

elif result_count < 5:

    st.warning(
        f"{result_count} companies matched. "
        "Try relaxing some filters."
    )

elif result_count > 50:

    st.info(
        f"{result_count} companies matched. "
        "Consider tightening the filters."
    )

else:

    st.success(
        f"{result_count} companies matched."
    )


# ============================================================
# SORTING
# ============================================================

sort_options = {

    "Quality Score":
        "composite_quality_score",

    "ROE":
        "roe",

    "ROCE":
        "roce_percentage",

    "Revenue CAGR 5Y":
        "revenue_cagr_5y",

    "PAT CAGR 5Y":
        "pat_cagr_5y",

    "EPS CAGR 5Y":
        "eps_cagr_5y",

    "P/E":
        "pe",

    "P/B":
        "pb",

    "Dividend Yield":
        "dividend_yield",

    "Market Cap":
        "market_cap",
}


available_sort_options = {
    name: column
    for name, column in sort_options.items()
    if column in filtered.columns
}


sort_name = st.selectbox(
    "Sort results by",
    list(
        available_sort_options.keys()
    ),
)


ascending = st.checkbox(
    "Ascending order",
    value=False,
)


sort_column = available_sort_options[
    sort_name
]


if sort_column in filtered.columns:

    filtered = (
        filtered
        .sort_values(
            sort_column,
            ascending=ascending,
            na_position="last",
        )
        .reset_index(drop=True)
    )


# ============================================================
# DISPLAY COLUMNS
# ============================================================

display_columns = {

    "company_id":
        "Company ID",

    "company_name":
        "Company",

    "sector":
        "Sector",

    "sub_sector":
        "Sub-Sector",

    "roe":
        "ROE (%)",

    "debt_to_equity":
        "D/E",

    "net_profit_margin_pct":
        "NPM (%)",

    "revenue_cagr_5y":
        "Revenue CAGR 5Y (%)",

    "pat_cagr_5y":
        "PAT CAGR 5Y (%)",

    "eps_cagr_5y":
        "EPS CAGR 5Y (%)",

    "fcf":
        "FCF (₹ Cr)",

    "pe":
        "P/E",

    "pb":
        "P/B",

    "dividend_yield":
        "Dividend Yield (%)",

    "market_cap":
        "Market Cap (₹ Cr)",

    "composite_quality_score":
        "Quality Score",
}


available_display = {
    column: label
    for column, label in display_columns.items()
    if column in filtered.columns
}


table = filtered[
    list(available_display.keys())
].rename(
    columns=available_display
)


# ============================================================
# ROUND NUMBERS
# ============================================================

for column in table.columns:

    if column not in [
        "Company ID",
        "Company",
        "Sector",
        "Sub-Sector",
    ]:

        table[column] = pd.to_numeric(
            table[column],
            errors="coerce",
        ).round(2)


st.dataframe(
    table,
    width="stretch",
    hide_index=True,
    height=600,
)


# ============================================================
# CSV EXPORT
# ============================================================

st.divider()

st.subheader(
    "📥 Export Results"
)

csv_data = table.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Screener Results CSV",
    data=csv_data,
    file_name="nifty100_screener_results.csv",
    mime="text/csv",
    width="stretch",
)


# ============================================================
# TOP RESULTS
# ============================================================

if not filtered.empty:

    st.divider()

    st.subheader(
        "🏆 Top 10 Results"
    )

    top10 = filtered.head(10).copy()

    top_columns = [
        "company_id",
        "company_name",
        "sector",
        "roe",
        "debt_to_equity",
        "revenue_cagr_5y",
        "composite_quality_score",
    ]

    top_columns = [
        c
        for c in top_columns
        if c in top10.columns
    ]

    st.dataframe(
        top10[
            top_columns
        ].round(2)
        if top_columns
        else top10,
        width="stretch",
        hide_index=True,
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"NIFTY 100 Screener | "
    f"Universe: {total_companies} companies | "
    f"Results: {result_count}"
)