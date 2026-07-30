import sqlite3
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import *

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT

p.company_id,

p.year,

p.sales,

p.net_profit,

p.operating_profit,

p.other_income,

p.opm_percentage,

b.equity_capital,

b.reserves,

b.borrowings,

b.total_assets,

s.broad_sector

FROM profitandloss p

JOIN balancesheet b
ON p.company_id=b.company_id
AND p.year=b.year

JOIN sectors s
ON p.company_id=s.company_id

LIMIT 20
"""

df = pd.read_sql(query, conn)

df["Net Profit Margin"] = df.apply(
    lambda x:
    net_profit_margin(
        x.net_profit,
        x.sales),
    axis=1
)

df["ROE"] = df.apply(
    lambda x:
    return_on_equity(
        x.net_profit,
        x.equity_capital,
        x.reserves),
    axis=1
)

print(df.head())