import sqlite3
import pandas as pd
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH")
PROCESSED_DATA = os.getenv("PROCESSED_DATA")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

TABLE_ORDER = [
    "companies",
    "balancesheet",
    "profitandloss",
    "cashflow",
    "analysis",
    "documents",
    "prosandcons",
    "financial_ratios",
    "market_cap",
    "peer_groups",
    "sectors",
    "stock_prices"
]

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys = ON")

audit = []

for table in TABLE_ORDER:

    file_path = Path(PROCESSED_DATA) / f"{table}.csv"

    print(f"Loading {table}...")

    if not file_path.exists():
        print(f"{file_path} not found")
        continue

    df = pd.read_csv(file_path)

    for index, row in df.iterrows():
        try:
            row.to_frame().T.to_sql(
                table,
                connection,
                if_exists="append",
                index=False
            )
        except Exception as e:
            print("=" * 70)
            print("Table:", table)
            print("Row:", index)
            print(row)
            print("Error:", e)
            break

    audit.append({
        "Table": table,
        "Rows Loaded": len(df),
        "Rejected": 0
    })

    print(f"{len(df)} rows inserted")

connection.commit()

audit_df = pd.DataFrame(audit)

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

audit_df.to_csv(
    Path(OUTPUT_DIR) / "load_audit.csv",
    index=False
)

connection.close()

print("\nAll tables loaded successfully.")