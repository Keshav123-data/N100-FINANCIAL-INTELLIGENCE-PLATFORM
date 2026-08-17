import sqlite3
import pandas as pd

DB_PATH = "DB/nifty100.db"

conn = sqlite3.connect(DB_PATH)


def show_schema(table):

    print("\n" + "=" * 80)
    print(f"{table.upper()} SCHEMA")
    print("=" * 80)

    df = pd.read_sql_query(
        f"PRAGMA table_info({table})",
        conn
    )

    print(df.to_string(index=False))


def show_company_data(table, company):

    print("\n" + "=" * 80)
    print(f"{table.upper()} DATA — {company}")
    print("=" * 80)

    df = pd.read_sql_query(
        f"""
        SELECT *
        FROM {table}
        WHERE company_id = ?
        ORDER BY rowid
        """,
        conn,
        params=(company,)
    )

    print(df.tail(15).to_string(index=False))


# ------------------------------------------------------------
# SCHEMAS
# ------------------------------------------------------------

show_schema("profitandloss")
show_schema("balancesheet")
show_schema("cashflow")


# ------------------------------------------------------------
# BEL SOURCE DATA
# ------------------------------------------------------------

show_company_data(
    "profitandloss",
    "BEL"
)

show_company_data(
    "balancesheet",
    "BEL"
)

show_company_data(
    "cashflow",
    "BEL"
)


# ------------------------------------------------------------
# HAL SOURCE DATA
# ------------------------------------------------------------

show_company_data(
    "profitandloss",
    "HAL"
)

show_company_data(
    "balancesheet",
    "HAL"
)


conn.close()

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)