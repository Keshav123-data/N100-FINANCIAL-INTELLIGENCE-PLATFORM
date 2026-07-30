import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT

c.id,
c.company_name,
c.roce_percentage AS source_roce,
c.roe_percentage AS source_roe,

s.broad_sector,

fr.return_on_equity_pct,

fr.composite_quality_score,

b.borrowings,
b.equity_capital,
b.reserves,

p.operating_profit,
p.interest

FROM companies c

LEFT JOIN sectors s

ON c.id=s.company_id

LEFT JOIN financial_ratios fr

ON c.id=fr.company_id

LEFT JOIN balancesheet b

ON c.id=b.company_id

AND fr.year=b.year

LEFT JOIN profitandloss p

ON c.id=p.company_id

AND fr.year=p.year
"""

df = pd.read_sql(query, conn)


def calculate_roce(row):

    capital = (
        row["equity_capital"]
        + row["reserves"]
        + row["borrowings"]
    )

    if capital <= 0:
        return None

    ebit = row["operating_profit"]

    return round((ebit / capital) * 100, 2)


df["calculated_roce"] = df.apply(
    calculate_roce,
    axis=1
)


log_path = Path("output/ratio_edge_cases.log")

log_file = open(log_path, "w", encoding="utf-8")

for _, row in df.iterrows():

    if row["broad_sector"] == "Financials":

        log_file.write(
            f"{row['id']} | "
            f"Financial Sector | "
            f"High leverage warning suppressed\n"
        )



for _, row in df.iterrows():

    if pd.isna(row["source_roce"]):
        continue

    if row["calculated_roce"] is None:
        continue

    diff = abs(
        row["source_roce"] -
        row["calculated_roce"]
    )

    if diff > 5:

        log_file.write(

            f"{row['id']} | "

            f"ROCE mismatch | "

            f"Source={row['source_roce']} "

            f"Calculated={row['calculated_roce']} "

            f"Difference={diff:.2f}\n"

        )


for _, row in df.iterrows():

    if pd.isna(row["source_roe"]):
        continue

    if pd.isna(row["return_on_equity_pct"]):
        continue

    diff = abs(
        row["source_roe"] -
        row["return_on_equity_pct"]
    )

    if diff > 5:

        log_file.write(

            f"{row['id']} | "

            f"ROE mismatch | "

            f"Source={row['source_roe']} "

            f"Calculated={row['return_on_equity_pct']} "

            f"Difference={diff:.2f}\n"

        )


def classify_difference(source, calculated):

    diff = abs(source - calculated)

    if diff <= 5:
        return "OK"

    if source < 1:
        return "Data Source Issue"

    if diff <= 15:
        return "Version Difference"

    return "Formula Discrepancy"


category = classify_difference(
    row["source_roce"],
    row["calculated_roce"]
)

log_file.write(

    f"{row['id']} | "

    f"ROCE | "

    f"{category}\n"

)


log_file.close()

conn.close()

print("ratio_edge_cases.log created successfully.")
