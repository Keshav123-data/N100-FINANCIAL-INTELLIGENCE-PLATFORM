SELECT COUNT(* ) AS TOTAL_COMPANIES
FROM companies;


SELECT broad_sector,
       COUNT(*) AS companies 
FROM sectors
GROUP by broad_sector
ORDER BY companies DESC;


SELECT companY_name,
    roe_percentage
FROM companies
order by roe_percentage DESC
limit 10;

select company_id,
    year,
    net_profit
from profitandloss
order by company_id,year;

SELECT company_id,
       MAX(sales) AS Highest_Sales
FROM profitandloss
GROUP BY company_id
ORDER BY Highest_Sales DESC
LIMIT 10;

SELECT company_id,
       year,
       market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;

SELECT s.broad_sector,
       AVG(c.roe_percentage) AS Avg_ROE
FROM companies c
JOIN sectors s
ON c.id = s.company_id
GROUP BY s.broad_sector
ORDER BY Avg_ROE DESC;

SELECT company_id,
       AVG(close_price) AS Avg_Close
FROM stock_prices
GROUP BY company_id
ORDER BY Avg_Close DESC;

SELECT
    (SELECT COUNT(*) FROM companies) AS companies,
    (SELECT COUNT(*) FROM profitandloss) AS profitandloss,
    (SELECT COUNT(*) FROM balancesheet) AS balancesheet,
    (SELECT COUNT(*) FROM cashflow) AS cashflow,
    (SELECT COUNT(*) FROM stock_prices) AS stock_prices;

SELECT COUNT(*) FROM companies;

PRAGMA foreign_key_check;

