import sqlite3
import pandas as pd
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from Script.analytics.cagr import revenue_cagr

conn = sqlite3.connect("DB/nifty100.db")

query = """
SELECT
company_id,
year,
sales,
net_profit,
eps
FROM profitandloss
ORDER BY company_id, year
"""

df = pd.read_sql(query, conn)

results = []

for company, group in df.groupby("company_id"):

    group = group.sort_values("year")

    if len(group) >= 6:

        start = group.iloc[-6]

        end = group.iloc[-1]

        value, flag = revenue_cagr(
            start["sales"],
            end["sales"],
            5
        )

        results.append({
            "company_id": company,
            "revenue_cagr_5yr": value,
            "flag": flag
        })

result_df = pd.DataFrame(results)

print(result_df.head())
