import sys
import sqlite3
from pathlib import Path

import numpy as np
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
    get_all_ratios,
    get_valuation,
)


# ============================================================
# DATABASE
# ============================================================

DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"


def query_db(query, params=None):

    conn = sqlite3.connect(str(DB_PATH))

    try:

        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )

    finally:

        conn.close()


# ============================================================
# PAGE CONFIG
# ============================================================

st.title("📊 Peer Comparison")

st.caption(
    "Compare companies against their industry peers "
    "using financial metrics and percentile rankings."
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
# SIDEBAR FILTER
# ============================================================

st.sidebar.header("Peer Comparison Filters")


search = st.sidebar.text_input(
    "Search company",
    placeholder="Example: TCS / ABB / Reliance",
)


# ============================================================
# FILTER COMPANY LIST
# ============================================================

filtered = companies.copy()


if search:

    search_value = search.strip().lower()

    mask = (
        filtered["company_name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False,
        )
    )

    mask |= (
        filtered["company_id"]
        .astype(str)
        .str.lower()
        .str.contains(
            search_value,
            na=False,
        )
    )

    filtered = filtered[mask]


if filtered.empty:

    st.warning(
        "No company found. Try another company name or ticker."
    )

    st.stop()


# ============================================================
# COMPANY SELECTOR
# ============================================================

def company_label(index):

    row = filtered.loc[index]

    return (
        f"{row['company_name']} "
        f"({row['company_id']})"
    )


selected_index = st.selectbox(
    "Select Company",
    filtered.index.tolist(),
    format_func=company_label,
)


company = filtered.loc[selected_index]


company_id = str(
    company["company_id"]
)


company_name = company.get(
    "company_name",
    company_id,
)


sector = company.get(
    "sector",
    "N/A",
)


sub_sector = company.get(
    "sub_sector",
    "N/A",
)


# ============================================================
# COMPANY HEADER
# ============================================================

st.divider()

st.header(
    f"{company_name} — Peer Analysis"
)


# ============================================================
# COMPANY INFORMATION
# ============================================================

c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(
        "Ticker",
        company_id,
    )


with c2:

    st.metric(
        "Sector",
        sector if pd.notna(sector) else "N/A",
    )


with c3:

    st.metric(
        "Sub-Sector",
        sub_sector
        if pd.notna(sub_sector)
        else "N/A",
    )


with c4:

    st.metric(
        "Company ID",
        company_id,
    )


# ============================================================
# LOAD PEER GROUP DATA
# ============================================================

peer_groups = pd.DataFrame()
peer_percentiles = pd.DataFrame()


try:

    peer_groups = query_db(
        "SELECT * FROM peer_groups"
    )

except Exception:

    peer_groups = pd.DataFrame()


try:

    peer_percentiles = query_db(
        "SELECT * FROM peer_percentiles"
    )

except Exception:

    peer_percentiles = pd.DataFrame()


# ============================================================
# FIND PEER GROUP
# ============================================================

actual_peer_group = None
peer_group_source = None


if not peer_groups.empty:

    peer_groups.columns = [
        str(c).strip()
        for c in peer_groups.columns
    ]

    # --------------------------------------------------------
    # Detect company ID column
    # --------------------------------------------------------

    company_column = None

    for candidate in [
        "company_id",
        "id",
        "ticker",
    ]:

        if candidate in peer_groups.columns:

            company_column = candidate
            break


    # --------------------------------------------------------
    # Detect peer group name column
    # --------------------------------------------------------

    group_column = None

    for candidate in [
        "peer_group_name",
        "group_name",
        "peer_group",
        "group",
    ]:

        if candidate in peer_groups.columns:

            group_column = candidate
            break


    if (
        company_column is not None
        and group_column is not None
    ):

        company_rows = peer_groups[
            peer_groups[company_column]
            .astype(str)
            .str.upper()
            == company_id.upper()
        ]


        if not company_rows.empty:

            actual_peer_group = str(
                company_rows.iloc[0][
                    group_column
                ]
            )

            peer_group_source = (
                "Sprint 3 predefined peer group"
            )


# ============================================================
# FALLBACK PEER GROUP
# ============================================================
#
# Some companies are not part of the 11 Sprint 3 groups.
# Example: ABB / Abbott India.
#
# Use Sub-Sector first, then Sector.
# ============================================================

if actual_peer_group is None:

    if (
        pd.notna(sub_sector)
        and str(sub_sector).strip()
        and str(sub_sector).lower()
        != "nan"
    ):

        actual_peer_group = str(
            sub_sector
        )

        peer_group_source = (
            "Sub-Sector fallback"
        )

    elif (
        pd.notna(sector)
        and str(sector).strip()
        and str(sector).lower()
        != "nan"
    ):

        actual_peer_group = str(
            sector
        )

        peer_group_source = (
            "Sector fallback"
        )


# ============================================================
# SHOW PEER GROUP
# ============================================================

if actual_peer_group:

    st.success(
        f"Peer Group: **{actual_peer_group}**  "
        f"({peer_group_source})"
    )

else:

    st.warning(
        "No suitable peer group could be determined."
    )

    st.stop()


# ============================================================
# LOAD ALL FINANCIAL RATIOS
# ============================================================

ratios = get_all_ratios()


if ratios.empty:

    st.warning(
        "Financial ratio data is unavailable."
    )

    st.stop()


# ============================================================
# NORMALIZE RATIO DATA
# ============================================================

ratios = ratios.copy()


ratios["company_id"] = (
    ratios["company_id"]
    .astype(str)
)


if "year_clean" in ratios.columns:

    ratios["year_num"] = pd.to_numeric(
        ratios["year_clean"],
        errors="coerce",
    )

else:

    ratios["year_num"] = pd.to_numeric(
        ratios["year"],
        errors="coerce",
    )


# ============================================================
# GET LATEST RECORD PER COMPANY
# ============================================================

ratios = (
    ratios
    .sort_values(
        [
            "company_id",
            "year_num",
        ]
    )
    .groupby(
        "company_id",
        as_index=False,
    )
    .tail(1)
    .copy()
)


# ============================================================
# MERGE COMPANY INFORMATION
# ============================================================

peer_data = ratios.merge(
    companies[
        [
            "company_id",
            "company_name",
            "sector",
            "sub_sector",
        ]
    ],
    on="company_id",
    how="left",
)


# ============================================================
# DETERMINE PEER COMPANIES
# ============================================================

# ------------------------------------------------------------
# If predefined peer group exists
# ------------------------------------------------------------

if peer_group_source == "Sprint 3 predefined peer group":

    group_column = None

    for candidate in [
        "peer_group_name",
        "group_name",
        "peer_group",
        "group",
    ]:

        if candidate in peer_groups.columns:

            group_column = candidate
            break


    company_column = None

    for candidate in [
        "company_id",
        "id",
        "ticker",
    ]:

        if candidate in peer_groups.columns:

            company_column = candidate
            break


    if (
        group_column is not None
        and company_column is not None
    ):

        group_members = peer_groups[
            peer_groups[group_column]
            .astype(str)
            .str.lower()
            == actual_peer_group.lower()
        ][
            company_column
        ].astype(str).tolist()


        peer_data = peer_data[
            peer_data["company_id"]
            .isin(group_members)
        ].copy()


# ------------------------------------------------------------
# Otherwise use Sub-Sector
# ------------------------------------------------------------

elif peer_group_source == "Sub-Sector fallback":

    peer_data = peer_data[
        peer_data["sub_sector"]
        .astype(str)
        .str.lower()
        == str(sub_sector).lower()
    ].copy()


# ------------------------------------------------------------
# Otherwise use Sector
# ------------------------------------------------------------

elif peer_group_source == "Sector fallback":

    peer_data = peer_data[
        peer_data["sector"]
        .astype(str)
        .str.lower()
        == str(sector).lower()
    ].copy()


# ============================================================
# GUARANTEE SELECTED COMPANY IS PRESENT
# ============================================================

if company_id not in (
    peer_data["company_id"]
    .astype(str)
    .tolist()
):

    selected_row = ratios[
        ratios["company_id"]
        == company_id
    ]

    if not selected_row.empty:

        selected_row = selected_row.merge(
            companies[
                [
                    "company_id",
                    "company_name",
                    "sector",
                    "sub_sector",
                ]
            ],
            on="company_id",
            how="left",
        )

        peer_data = pd.concat(
            [
                peer_data,
                selected_row,
            ],
            ignore_index=True,
        )


# ============================================================
# LIMIT TO VALID PEERS
# ============================================================

peer_data = (
    peer_data
    .drop_duplicates(
        subset=["company_id"]
    )
    .copy()
)


if peer_data.empty:

    st.warning(
        "No peer companies are available."
    )

    st.stop()


# ============================================================
# METRIC DEFINITIONS
# ============================================================

metric_map = {

    "ROE": "return_on_equity_pct",

    "Net Profit Margin":
        "net_profit_margin_pct",

    "Operating Margin":
        "operating_profit_margin_pct",

    "Revenue CAGR 5Y":
        "revenue_cagr_5yr",

    "PAT CAGR 5Y":
        "pat_cagr_5yr",

    "EPS CAGR 5Y":
        "eps_cagr_5yr",

    "Interest Coverage":
        "interest_coverage",

    "Asset Turnover":
        "asset_turnover",

    "FCF":
        "free_cash_flow_cr",

    "D/E":
        "debt_to_equity",
}


# ============================================================
# AVAILABLE METRICS
# ============================================================

available_metrics = [
    name
    for name, column in metric_map.items()
    if column in peer_data.columns
]


# ============================================================
# PEER METRIC PERCENTILES
# ============================================================

for metric_name in available_metrics:

    column = metric_map[
        metric_name
    ]

    peer_data[column] = pd.to_numeric(
        peer_data[column],
        errors="coerce",
    )


# ============================================================
# SELECTED COMPANY
# ============================================================

selected_peer = peer_data[
    peer_data["company_id"]
    == company_id
]


if selected_peer.empty:

    st.warning(
        "Selected company financial data "
        "is unavailable."
    )

    st.stop()


selected_peer = selected_peer.iloc[0]


# ============================================================
# KPI COMPARISON
# ============================================================

st.divider()

st.subheader(
    "Key Peer Comparison"
)


def get_value(column):

    if column not in selected_peer.index:
        return None

    value = selected_peer[column]

    try:

        value = float(value)

        if np.isnan(value):
            return None

        return value

    except Exception:

        return None


roe_value = get_value(
    "return_on_equity_pct"
)

npm_value = get_value(
    "net_profit_margin_pct"
)

de_value = get_value(
    "debt_to_equity"
)

revenue_cagr_value = get_value(
    "revenue_cagr_5yr"
)


k1, k2, k3, k4 = st.columns(4)


with k1:

    st.metric(
        "ROE",
        (
            f"{roe_value:.2f}%"
            if roe_value is not None
            else "N/A"
        ),
    )


with k2:

    st.metric(
        "Net Profit Margin",
        (
            f"{npm_value:.2f}%"
            if npm_value is not None
            else "N/A"
        ),
    )


with k3:

    st.metric(
        "D/E",
        (
            f"{de_value:.2f}"
            if de_value is not None
            else "N/A"
        ),
    )


with k4:

    st.metric(
        "Revenue CAGR 5Y",
        (
            f"{revenue_cagr_value:.2f}%"
            if revenue_cagr_value is not None
            else "N/A"
        ),
    )


# ============================================================
# RADAR CHART
# ============================================================

st.divider()

st.subheader(
    "Peer Percentile Radar"
)


radar_metrics = [
    "ROE",
    "Net Profit Margin",
    "Operating Margin",
    "Revenue CAGR 5Y",
    "PAT CAGR 5Y",
    "EPS CAGR 5Y",
    "Interest Coverage",
    "Asset Turnover",
]


radar_metrics = [
    metric
    for metric in radar_metrics
    if metric in available_metrics
]


radar_values = []


for metric in radar_metrics:

    column = metric_map[metric]

    values = pd.to_numeric(
        peer_data[column],
        errors="coerce",
    )


    current_value = pd.to_numeric(
        pd.Series(
            [selected_peer[column]]
        ),
        errors="coerce",
    ).iloc[0]


    if pd.isna(current_value):

        radar_values.append(0)
        continue


    valid = values.dropna()


    if len(valid) <= 1:

        percentile = 100

    else:

        percentile = (
            valid
            .rank(
                pct=True,
                method="average",
            )
            .loc[
                values.index[
                    values
                    == current_value
                ]
            ]
            .iloc[0]
            * 100
        )


    radar_values.append(
        round(
            float(percentile),
            2,
        )
    )


# ============================================================
# RADAR CHART
# ============================================================

if radar_metrics:

    radar_categories = (
        radar_metrics
        + [
            radar_metrics[0]
        ]
    )

    radar_plot_values = (
        radar_values
        + [
            radar_values[0]
        ]
    )


    fig = go.Figure()


    fig.add_trace(
        go.Scatterpolar(
            r=radar_plot_values,
            theta=radar_categories,
            fill="toself",
            name=company_name,
        )
    )


    fig.update_layout(

        polar=dict(

            radialaxis=dict(
                visible=True,
                range=[
                    0,
                    100,
                ],
            )

        ),

        showlegend=True,

        height=550,

        title=(
            f"{company_name} "
            f"vs {actual_peer_group}"
        ),
    )


    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# PEER BENCHMARK TABLE
# ============================================================

st.divider()

st.subheader(
    "Peer Benchmark Table"
)


table_columns = [
    "company_id",
    "company_name",
]


for metric in [
    "ROE",
    "Net Profit Margin",
    "Operating Margin",
    "Revenue CAGR 5Y",
    "PAT CAGR 5Y",
    "D/E",
]:

    column = metric_map.get(
        metric
    )

    if (
        column
        and column in peer_data.columns
    ):

        table_columns.append(
            column
        )


benchmark = peer_data[
    table_columns
].copy()


# Rename columns

rename_map = {

    "company_id":
        "Ticker",

    "company_name":
        "Company",

    "return_on_equity_pct":
        "ROE (%)",

    "net_profit_margin_pct":
        "Net Profit Margin (%)",

    "operating_profit_margin_pct":
        "Operating Margin (%)",

    "revenue_cagr_5yr":
        "Revenue CAGR 5Y (%)",

    "pat_cagr_5yr":
        "PAT CAGR 5Y (%)",

    "debt_to_equity":
        "D/E",
}


benchmark = benchmark.rename(
    columns=rename_map
)


# ============================================================
# SORT BY ROE
# ============================================================

if "ROE (%)" in benchmark.columns:

    benchmark = benchmark.sort_values(
        "ROE (%)",
        ascending=False,
        na_position="last",
    )


# ============================================================
# HIGHLIGHT SELECTED COMPANY
# ============================================================

def highlight_selected(
    row
):

    if row["Ticker"] == company_id:

        return [
            "font-weight: bold"
            for _ in row
        ]

    return [
        ""
        for _ in row
    ]


styled = benchmark.style.apply(
    highlight_selected,
    axis=1,
)


st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# PEER COUNT
# ============================================================

st.caption(
    f"Peer companies compared: "
    f"{len(peer_data)}"
)


# ============================================================
# PERCENTILE DETAILS
# ============================================================

st.divider()

st.subheader(
    "Selected Company Percentile Ranking"
)


percentile_rows = []


# ------------------------------------------------------------
# First try Sprint 3 stored percentile data
# ------------------------------------------------------------

if not peer_percentiles.empty:

    peer_percentiles.columns = [
        str(c).strip()
        for c in peer_percentiles.columns
    ]


    required = {
        "company_id",
        "metric",
        "percentile_rank",
    }


    if required.issubset(
        peer_percentiles.columns
    ):

        stored = peer_percentiles[
            peer_percentiles["company_id"]
            .astype(str)
            .str.upper()
            == company_id.upper()
        ].copy()


        for _, row in stored.iterrows():

            percentile_rows.append({

                "Metric":
                    str(row["metric"])
                    .replace("_", " ")
                    .title(),

                "Percentile":
                    round(
                        float(
                            row[
                                "percentile_rank"
                            ]
                        ),
                        2,
                    ),

                "Source":
                    "Sprint 3 Peer Percentiles",
            })


# ============================================================
# FALLBACK CALCULATION
# ============================================================

if not percentile_rows:

    for metric_name in available_metrics:

        column = metric_map[
            metric_name
        ]


        values = pd.to_numeric(
            peer_data[column],
            errors="coerce",
        )


        current_value = pd.to_numeric(
            pd.Series(
                [selected_peer[column]]
            ),
            errors="coerce",
        ).iloc[0]


        if pd.isna(current_value):

            continue


        valid = values.dropna()


        if len(valid) <= 1:

            percentile = 100.0

        else:

            ranks = valid.rank(
                pct=True,
                method="average",
            )

            matching = ranks[
                valid == current_value
            ]


            if matching.empty:

                continue


            percentile = (
                float(
                    matching.iloc[0]
                )
                * 100
            )


        # D/E is inverse:
        # lower D/E = better percentile

        if metric_name == "D/E":

            de_ranks = (
                valid.rank(
                    pct=True,
                    method="average",
                    ascending=False,
                )
            )

            matching = de_ranks[
                valid == current_value
            ]

            if not matching.empty:

                percentile = (
                    float(
                        matching.iloc[0]
                    )
                    * 100
                )


        percentile_rows.append({

            "Metric":
                metric_name,

            "Percentile":
                round(
                    percentile,
                    2,
                ),

            "Source":
                "Calculated from peer group",
        })


# ============================================================
# DISPLAY PERCENTILES
# ============================================================

if percentile_rows:

    percentile_df = pd.DataFrame(
        percentile_rows
    )


    percentile_df = (
        percentile_df
        .drop_duplicates(
            subset=["Metric"]
        )
    )


    percentile_df[
        "Percentile"
    ] = pd.to_numeric(
        percentile_df[
            "Percentile"
        ],
        errors="coerce",
    )


    st.dataframe(
        percentile_df,
        use_container_width=True,
        hide_index=True,
    )


else:

    st.info(
        "Percentile ranking data is unavailable."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    f"Peer Group: {actual_peer_group} | "
    f"Company: {company_id} | "
    f"Peer Count: {len(peer_data)}"
)