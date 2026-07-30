import sqlite3
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    debt_to_equity,
    interest_coverage,
    asset_turnover,
)

from Script.analytics.cashflow_kpis import (
    free_cash_flow,
)

DB_PATH = "db/nifty100.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT

p.company_id,
p.year,

p.sales,
p.net_profit,
p.operating_profit,
p.other_income,
p.interest,
p.eps,
p.dividend_payout,

b.equity_capital,
b.reserves,
b.borrowings,
b.total_assets,
b.investments,

cf.operating_activity,
cf.investing_activity,

c.book_value

FROM profitandloss p

JOIN balancesheet b
ON p.company_id=b.company_id
AND p.year=b.year

LEFT JOIN cashflow cf
ON p.company_id=cf.company_id
AND p.year=cf.year

JOIN companies c
ON p.company_id=c.id
"""

df = pd.read_sql(query, conn)

df["net_profit_margin_pct"] = df.apply(
    lambda x: net_profit_margin(
        x.net_profit,
        x.sales),
    axis=1)

df["operating_profit_margin_pct"] = df.apply(
    lambda x: operating_profit_margin(
        x.operating_profit,
        x.sales),
    axis=1)

df["return_on_equity_pct"] = df.apply(
    lambda x: return_on_equity(
        x.net_profit,
        x.equity_capital,
        x.reserves),
    axis=1)

df["debt_to_equity"] = df.apply(
    lambda x: debt_to_equity(
        x.borrowings,
        x.equity_capital,
        x.reserves),
    axis=1)

df["interest_coverage"] = df.apply(
    lambda x: interest_coverage(
        x.operating_profit,
        x.other_income,
        x.interest),
    axis=1)

df["asset_turnover"] = df.apply(
    lambda x: asset_turnover(
        x.sales,
        x.total_assets),
    axis=1)

df["free_cash_flow_cr"] = df.apply(
    lambda x: free_cash_flow(
        x.operating_activity,
        x.investing_activity),
    axis=1)

df["capex_cr"] = df["investing_activity"].abs()

df["earnings_per_share"] = df["eps"]

df["book_value_per_share"] = df["book_value"]

df["dividend_payout_ratio_pct"] = df["dividend_payout"]

df["total_debt_cr"] = df["borrowings"]

df["cash_from_operations_cr"] = df["operating_activity"]


df["composite_quality_score"] = (
    df["return_on_equity_pct"].fillna(0) * 0.40
    + df["net_profit_margin_pct"].fillna(0) * 0.30
    + df["asset_turnover"].fillna(0) * 10 * 0.30
).round(2)

cursor = conn.cursor()

cursor.execute("DELETE FROM financial_ratios")
conn.commit()

columns = [
    "company_id",
    "year",
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
    "composite_quality_score"
]

df[columns].to_sql(
    "financial_ratios",
    conn,
    if_exists="append",
    index=False
)

conn.commit()
conn.close()

print("financial_ratios populated successfully.")


