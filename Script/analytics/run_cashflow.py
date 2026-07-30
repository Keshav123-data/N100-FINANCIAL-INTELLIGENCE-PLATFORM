import sqlite3
import pandas as pd

from Script.analytics.cashflow_kpis import *

conn = sqlite3.connect("db/nifty100.db")

query = """
SELECT
cf.company_id,
cf.year,
cf.operating_activity,
cf.investing_activity,
cf.financing_activity,
pl.net_profit,
pl.sales,
pl.operating_profit

FROM cashflow cf

JOIN profitandloss pl
ON cf.company_id = pl.company_id
AND cf.year = pl.year
"""

df = pd.read_sql(query, conn)

results = []

for _, row in df.iterrows():

    fcf = free_cash_flow(
        row.operating_activity,
        row.investing_activity
    )

    score, quality = cfo_quality_score(
        row.operating_activity,
        row.net_profit
    )

    capex, cap_label = capex_intensity(
        row.investing_activity,
        row.sales
    )

    conversion = fcf_conversion_rate(
        fcf,
        row.operating_profit
    )

    pattern = capital_allocation_pattern(
        row.operating_activity,
        row.investing_activity,
        row.financing_activity,
        score
    )

    results.append({

        "company_id": row.company_id,
        "year": row.year,

        "free_cash_flow": fcf,

        "cfo_quality_score": score,

        "cfo_quality_label": quality,

        "capex_intensity": capex,

        "capex_label": cap_label,

        "fcf_conversion": conversion,

        **pattern

    })

result = pd.DataFrame(results)

result.to_csv(
    "output/capital_allocation.csv",
    index=False
)

print(result.head())