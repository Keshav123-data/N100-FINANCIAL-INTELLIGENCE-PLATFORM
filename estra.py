import sqlite3
from pathlib import Path

# Always use the database inside DB/
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"

print("Using database:")
print(DB_PATH)
print()

conn = sqlite3.connect(DB_PATH)

# Check tables
tables = conn.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
    """
).fetchall()

print("Tables:")
for table in tables:
    print(" -", table[0])

# Check P&L
print("\n--- PROFIT AND LOSS: AXISBANK ---")

rows = conn.execute(
    """
    SELECT *
    FROM profitandloss
    WHERE company_id = ?
    """,
    ("AXISBANK",)
).fetchall()

print("Count:", len(rows))

for row in rows:
    print(row)

# Check Balance Sheet
print("\n--- BALANCE SHEET: AXISBANK ---")

rows = conn.execute(
    """
    SELECT *
    FROM balancesheet
    WHERE company_id = ?
    """,
    ("AXISBANK",)
).fetchall()

print("Count:", len(rows))

for row in rows:
    print(row)

# Check Cash Flow
print("\n--- CASH FLOW: AXISBANK ---")

rows = conn.execute(
    """
    SELECT *
    FROM cashflow
    WHERE company_id = ?
    """,
    ("AXISBANK",)
).fetchall()

print("Count:", len(rows))

for row in rows:
    print(row)

conn.close()