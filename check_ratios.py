import sqlite3
import pandas as pd

DB_PATH = "DB/nifty100.db"

conn = sqlite3.connect(DB_PATH)

df = pd.read_sql_query(
    """
    SELECT
        company_id,
        year,
        return_on_equity_pct,
        debt_to_equity,
        revenue_cagr_5yr,
        pat_cagr_5yr,
        composite_quality_score
    FROM financial_ratios
    ORDER BY company_id, year
    """,
    conn
)

print("=" * 80)
print("TOTAL FINANCIAL RATIO ROWS")
print("=" * 80)
print(len(df))

print("\n" + "=" * 80)
print("DUPLICATE COMPANY/YEAR RECORDS")
print("=" * 80)

duplicates = (
    df.groupby(["company_id", "year"])
      .size()
      .reset_index(name="count")
)

duplicates = duplicates[
    duplicates["count"] > 1
]

print(duplicates.head(30).to_string(index=False))

print("\nNumber of duplicate company/year combinations:")
print(len(duplicates))


print("\n" + "=" * 80)
print("EXTREME ROE VALUES")
print("=" * 80)

print(
    df.nlargest(
        20,
        "return_on_equity_pct"
    ).to_string(index=False)
)


print("\n" + "=" * 80)
print("EXTREME QUALITY SCORES")
print("=" * 80)

print(
    df.nlargest(
        20,
        "composite_quality_score"
    ).to_string(index=False)
)


print("\n" + "=" * 80)
print("REVENUE CAGR AVAILABILITY BY YEAR")
print("=" * 80)

df["year_clean"] = pd.to_numeric(
    df["year"]
      .astype(str)
      .str.extract(r"(\d{4})")[0],
    errors="coerce"
)

print(
    df.groupby("year_clean")["revenue_cagr_5yr"]
      .agg(
          total="count",
          available=lambda x: x.notna().sum()
      )
      .tail(15)
)


conn.close()