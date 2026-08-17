from pathlib import Path
import sqlite3
from typing import Optional

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _get_connection():
    """
    Create a read-only SQLite connection.

    Streamlit creates a new connection when a cached query
    needs one, while the actual query results are cached.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    return sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True,
        check_same_thread=False,
    )


# ============================================================
# GENERIC QUERY
# ============================================================

@st.cache_data(ttl=600)
def _query(
    sql: str,
    params: tuple = (),
) -> pd.DataFrame:
    """
    Execute a read-only SQL query.

    Cached for 10 minutes as required by Sprint 4.
    """
    conn = _get_connection()

    try:
        return pd.read_sql_query(
            sql,
            conn,
            params=params,
        )
    finally:
        conn.close()


# ============================================================
# TABLE HELPERS
# ============================================================

@st.cache_data(ttl=600)
def get_table_columns(table_name: str) -> list[str]:
    """
    Return available columns for a SQLite table.
    """
    allowed_tables = {
        "companies",
        "financial_ratios",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "market_cap",
        "peer_groups",
        "peer_percentiles",
        "sectors",
        "stock_prices",
        "documents",
        "prosandcons",
        "analysis",
    }

    if table_name not in allowed_tables:
        return []

    df = _query(
        f"PRAGMA table_info({table_name})"
    )

    if df.empty or "name" not in df.columns:
        return []

    return df["name"].tolist()


def _existing_columns(
    table_name: str,
    requested_columns: list[str],
) -> list[str]:

    available = set(
        get_table_columns(table_name)
    )

    return [
        column
        for column in requested_columns
        if column in available
    ]


# ============================================================
# COMPANIES
# ============================================================

@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """
    Return master company information.

    Normalizes id -> company_id so dashboard code has
    one consistent company identifier.
    """

    columns = get_table_columns("companies")

    if not columns:
        return pd.DataFrame()

    preferred = [
        "id",
        "company_id",
        "company_name",
        "ticker",
        "nse_ticker",
        "sector",
        "sub_sector",
        "description",
        "about",
        "roce_percentage",
        "roe_percentage",
    ]

    selected = _existing_columns(
        "companies",
        preferred,
    )

    if not selected:
        return pd.DataFrame()

    sql = f"""
        SELECT {", ".join(selected)}
        FROM companies
        ORDER BY company_name
    """

    df = _query(sql)

    if "id" in df.columns and "company_id" not in df.columns:
        df = df.rename(
            columns={"id": "company_id"}
        )

    return df


# ============================================================
# FINANCIAL RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_ratios(
    ticker: str,
    year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Return financial ratio history for a company.
    """

    companies = get_companies()

    if companies.empty:
        return pd.DataFrame()

    ticker = str(ticker).strip().upper()

    company_id = None

    possible_ticker_columns = [
        "ticker",
        "nse_ticker",
    ]

    for col in possible_ticker_columns:
        if col in companies.columns:
            match = companies[
                companies[col]
                .astype(str)
                .str.upper()
                .eq(ticker)
            ]

            if not match.empty:
                company_id = match.iloc[0]["company_id"]
                break

    if company_id is None:

        if "company_name" in companies.columns:

            match = companies[
                companies["company_name"]
                .astype(str)
                .str.upper()
                .eq(ticker)
            ]

            if not match.empty:
                company_id = match.iloc[0]["company_id"]

    if company_id is None:
        return pd.DataFrame()

    columns = get_table_columns(
        "financial_ratios"
    )

    if not columns:
        return pd.DataFrame()

    selected = columns.copy()

    sql = f"""
        SELECT {", ".join(selected)}
        FROM financial_ratios
        WHERE company_id = ?
    """

    params = [company_id]

    if year is not None and "year" in columns:

        sql += """
            AND CAST(
                substr(CAST(year AS TEXT), -4)
                AS INTEGER
            ) = ?
        """

        params.append(int(year))

    if "year" in columns:
        sql += """
            ORDER BY year
        """

    return _query(
        sql,
        tuple(params),
    )


# ============================================================
# GENERIC COMPANY TABLE LOADER
# ============================================================

def _get_company_table(
    table_name: str,
    ticker: str,
) -> pd.DataFrame:

    companies = get_companies()

    if companies.empty:
        return pd.DataFrame()

    ticker = str(ticker).strip().upper()

    company_id = None

    for col in ["ticker", "nse_ticker"]:

        if col not in companies.columns:
            continue

        match = companies[
            companies[col]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]

        if not match.empty:
            company_id = match.iloc[0]["company_id"]
            break

    if company_id is None:
        return pd.DataFrame()

    columns = get_table_columns(
        table_name
    )

    if "company_id" not in columns:
        return pd.DataFrame()

    sql = f"""
        SELECT *
        FROM {table_name}
        WHERE company_id = ?
    """

    return _query(
        sql,
        (company_id,),
    )


# ============================================================
# P&L
# ============================================================

@st.cache_data(ttl=600)
def get_pl(
    ticker: str,
) -> pd.DataFrame:

    return _get_company_table(
        "profitandloss",
        ticker,
    )


# ============================================================
# BALANCE SHEET
# ============================================================

@st.cache_data(ttl=600)
def get_bs(
    ticker: str,
) -> pd.DataFrame:

    return _get_company_table(
        "balancesheet",
        ticker,
    )


# ============================================================
# CASH FLOW
# ============================================================

@st.cache_data(ttl=600)
def get_cf(
    ticker: str,
) -> pd.DataFrame:

    return _get_company_table(
        "cashflow",
        ticker,
    )


# ============================================================
# SECTORS
# ============================================================

@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:

    columns = get_table_columns(
        "sectors"
    )

    if not columns:
        return pd.DataFrame()

    return _query(
        f"""
        SELECT *
        FROM sectors
        """
    )


# ============================================================
# PEER GROUPS
# ============================================================

@st.cache_data(ttl=600)
def get_peers(
    group_name: str,
) -> pd.DataFrame:

    columns = get_table_columns(
        "peer_groups"
    )

    if not columns:
        return pd.DataFrame()

    if "group_name" not in columns:
        return pd.DataFrame()

    return _query(
        """
        SELECT *
        FROM peer_groups
        WHERE group_name = ?
        """,
        (group_name,),
    )


# ============================================================
# VALUATION
# ============================================================

@st.cache_data(ttl=600)
def get_valuation(
    ticker: str,
) -> pd.DataFrame:

    """
    Load valuation-related data.

    Uses market_cap and financial_ratios tables because
    Sprint 4 valuation is based on these datasets.
    """

    companies = get_companies()

    if companies.empty:
        return pd.DataFrame()

    ticker = str(ticker).strip().upper()

    company_id = None

    for col in ["ticker", "nse_ticker"]:

        if col not in companies.columns:
            continue

        match = companies[
            companies[col]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]

        if not match.empty:
            company_id = match.iloc[0]["company_id"]
            break

    if company_id is None:
        return pd.DataFrame()

    ratios = _query(
        """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
        """,
        (company_id,),
    )

    market = _query(
        """
        SELECT *
        FROM market_cap
        WHERE company_id = ?
        ORDER BY year
        """,
        (company_id,),
    )

    if ratios.empty and market.empty:
        return pd.DataFrame()

    if ratios.empty:
        return market

    if market.empty:
        return ratios

    if "year" in ratios.columns and "year" in market.columns:

        ratios = ratios.copy()
        market = market.copy()

        ratios["year_key"] = (
            ratios["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
        )

        market["year_key"] = (
            market["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
        )

        merged = ratios.merge(
            market,
            on=[
                "company_id",
                "year_key",
            ],
            how="outer",
            suffixes=(
                "_ratio",
                "_market",
            ),
        )

        return merged

    return ratios.merge(
        market,
        on="company_id",
        how="outer",
        suffixes=(
            "_ratio",
            "_market",
        ),
    )


# ============================================================
# DATABASE HEALTH CHECK
# ============================================================

@st.cache_data(ttl=600)
def get_database_tables() -> list[str]:

    df = _query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    )

    if df.empty:
        return []

    return df["name"].tolist()