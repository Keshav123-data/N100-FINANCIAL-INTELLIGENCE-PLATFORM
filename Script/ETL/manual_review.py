import sqlite3
import pandas as pd

DB_PATH = "DB/nifty100.db"

conn = sqlite3.connect(DB_PATH)

query = """
SELECT id,
       company_name
FROM companies
ORDER BY RANDOM()
LIMIT 5;
"""

companies = pd.read_sql(query, conn)

print(companies)

query = """
SELECT
company_id,

MIN(year) First_Year,

MAX(year) Last_Year,

COUNT(*) Total_Years

FROM profitandloss

GROUP BY company_id

ORDER BY company_id;
"""

coverage = pd.read_sql(query, conn)

print(coverage.head())

query = """
SELECT

company_id,

COUNT(*) Total_Years

FROM profitandloss

GROUP BY company_id

HAVING COUNT(*)<5;
"""

few = pd.read_sql(query, conn)

print(few)

cursor = conn.cursor()

cursor.execute("PRAGMA foreign_key_check")

rows = cursor.fetchall()

print(rows)

query = """
SELECT

company_id,

year,

total_assets,

total_liabilities,

(total_liabilities) Difference

FROM balancesheet;
"""

balance = pd.read_sql(query, conn)

print(balance.head())

balance["Difference"] = (
    balance["total_assets"]
    - balance["total_liabilities"]
)

print(balance["Difference"].describe())

tables = [

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

for table in tables:

    df = pd.read_sql(f"SELECT * FROM {table}", conn)

    print("\n",table)

    print(df.isnull().sum())

query = """

SELECT

id,

COUNT(*)

FROM companies

GROUP BY id

HAVING COUNT(*)>1;

"""

duplicates = pd.read_sql(query,conn)

print(duplicates)

tables = [

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

for table in tables:

    count = pd.read_sql(

    f"SELECT COUNT(*) Total FROM {table}",

    conn

    )

    print(table)

    print(count)

summary = {

    "companies":92,

    "balancesheet":1312,

    "profitandloss":1276,

    "cashflow":1187,

    "stock_prices":5520,

    "fk_errors":len(rows),

    "duplicates":len(duplicates)

}

report = pd.DataFrame(summary.items(),

columns=["Metric","Value"])

report.to_csv(

"output/manual_review_report.csv",

index=False

)

print(report)

