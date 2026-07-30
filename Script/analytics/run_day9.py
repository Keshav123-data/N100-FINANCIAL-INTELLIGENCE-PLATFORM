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
p.operating_profit,
p.other_income,
p.interest,

b.borrowings,
b.reserves,
b.equity_capital,
b.investments,
b.total_assets,

s.broad_sector

FROM profitandloss p

JOIN balancesheet b
ON p.company_id=b.company_id
AND p.year=b.year

JOIN sectors s
ON p.company_id=s.company_id
"""

df = pd.read_sql(query, conn)

df["Debt_to_Equity"] = df.apply(
    lambda x:
    debt_to_equity(
        x.borrowings,
        x.equity_capital,
        x.reserves
    ),
    axis=1
)

df["Interest_Coverage"] = df.apply(
    lambda x:
    interest_coverage(
        x.operating_profit,
        x.other_income,
        x.interest
    ),
    axis=1
)

df["Net_Debt"] = df.apply(
    lambda x:
    net_debt(
        x.borrowings,
        x.investments
    ),
    axis=1
)

df["Asset_Turnover"] = df.apply(
    lambda x:
    asset_turnover(
        x.sales,
        x.total_assets
    ),
    axis=1
)

print(df.head())