from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ============================================================
# DATABASE PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
    )


# ============================================================
# GENERIC QUERY
# ============================================================

@st.cache_data(ttl=600)
def _query(query, params=None):

    conn = get_connection()

    try:

        if params is None:
            return pd.read_sql_query(
                query,
                conn,
            )

        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )

    finally:

        conn.close()


# ============================================================
# TABLE COLUMNS
# ============================================================

@st.cache_data(ttl=600)
def get_table_columns(table_name):

    allowed_tables = {
        "companies",
        "financial_ratios",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "sectors",
        "peer_groups",
        "peer_percentiles",
        "market_cap",
        "stock_prices",
        "documents",
        "analysis",
        "prosandcons",
    }

    if table_name not in allowed_tables:
        return []

    df = _query(
        f"PRAGMA table_info({table_name})"
    )

    if df.empty:
        return []

    return df["name"].tolist()


# ============================================================
# COMPANIES
# ============================================================

@st.cache_data(ttl=600)
def get_companies():

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            c.about_company,
            c.website,
            c.nse_profile,
            c.bse_profile,
            c.roce_percentage,
            c.roe_percentage,

            s.broad_sector AS sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category

        FROM companies c

        LEFT JOIN sectors s
            ON c.id = s.company_id

        ORDER BY c.company_name
    """

    return _query(query)


# ============================================================
# YEAR NORMALIZATION
# ============================================================

def normalize_year_column(df):

    if df.empty or "year" not in df.columns:
        return df

    df = df.copy()

    df["year_clean"] = pd.to_numeric(
        df["year"]
        .astype(str)
        .str.extract(r"(\d{4})")[0],
        errors="coerce",
    )

    return df


# ============================================================
# FINANCIAL RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):

    query = """
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
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,
            total_debt_cr,
            cash_from_operations_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            composite_quality_score

        FROM financial_ratios

        WHERE company_id = ?

        ORDER BY id
    """

    df = _query(
        query,
        (str(ticker),),
    )

    if df.empty:
        return df

    df = normalize_year_column(df)

    if year is not None:

        df = df[
            df["year_clean"] == int(year)
        ].copy()

    return df


# ============================================================
# ALL RATIOS FOR DASHBOARD
# ============================================================

@st.cache_data(ttl=600)
def get_all_ratios(year=None):

    query = """
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
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,
            total_debt_cr,
            cash_from_operations_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            composite_quality_score

        FROM financial_ratios

        ORDER BY company_id, id
    """

    df = _query(query)

    if df.empty:
        return df

    df = normalize_year_column(df)

    if year is not None:

        df = df[
            df["year_clean"] == int(year)
        ].copy()

    return df


# ============================================================
# PROFIT & LOSS
# ============================================================

@st.cache_data(ttl=600)
def get_pl(ticker):

    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY rowid
    """

    return _query(
        query,
        (str(ticker),),
    )


# ============================================================
# BALANCE SHEET
# ============================================================

@st.cache_data(ttl=600)
def get_bs(ticker):

    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY rowid
    """

    return _query(
        query,
        (str(ticker),),
    )


# ============================================================
# CASH FLOW
# ============================================================

@st.cache_data(ttl=600)
def get_cf(ticker):

    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY rowid
    """

    return _query(
        query,
        (str(ticker),),
    )


# ============================================================
# SECTORS
# ============================================================

@st.cache_data(ttl=600)
def get_sectors():

    query = """
        SELECT
            id,
            company_id,
            broad_sector,
            sub_sector,
            index_weight_pct,
            market_cap_category

        FROM sectors

        ORDER BY broad_sector, sub_sector
    """

    return _query(query)


# ============================================================
# PEER GROUPS
# ============================================================

@st.cache_data(ttl=600)
def get_peers(group_name):

    query = """
        SELECT *
        FROM peer_groups
        WHERE group_name = ?
    """

    return _query(
        query,
        (group_name,),
    )


# ============================================================
# VALUATION
# ============================================================

@st.cache_data(ttl=600)
def get_valuation(ticker):

    query = """
        SELECT *
        FROM market_cap
        WHERE company_id = ?
    """

    return _query(
        query,
        (str(ticker),),
    )


# ============================================================
# DATABASE TABLE LIST
# ============================================================

@st.cache_data(ttl=600)
def get_database_tables():

    query = """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
    """

    df = _query(query)

    if df.empty:
        return []

    return df["name"].tolist()