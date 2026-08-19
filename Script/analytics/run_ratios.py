import sqlite3
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.ratios import *

conn = sqlite3.connect("DB/nifty100.db")

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


from Tests.kpi.liquidity import *
from Tests.kpi.leverage import *
from Tests.kpi.profitability import *
from Tests.kpi.efficiency import *
from Tests.kpi.valuation import *

print("\nLiquidity")
print(current_ratio(500000,250000))
print(quick_ratio(500000,100000,250000))
print(cash_ratio(150000,250000))

print("\nLeverage")
print(debt_to_equity(300000,500000))
print(debt_ratio(300000,900000))
print(equity_ratio(500000,900000))

print("\nProfitability")
print(gross_margin(400000,1000000))
print(operating_margin(220000,1000000))
print(net_margin(150000,1000000))
print(roa(150000,900000))
print(roe(150000,500000))

print("\nEfficiency")
print(asset_turnover(1000000,900000))
print(inventory_turnover(600000,120000))
print(receivable_turnover(1000000,100000))

print("\nValuation")
print(eps(200000,10000))
print(pe_ratio(850,20))
print(book_value(500000,10000))
print(pb_ratio(850,50))