PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS balancesheet;
DROP TABLE IF EXISTS profitandloss;
DROP TABLE IF EXISTS cashflow;
DROP TABLE IF EXISTS analysis;
DROP TABLE IF EXISTS documents;
DROP TABLE IF EXISTS prosandcons;
DROP TABLE IF EXISTS financial_ratios;
DROP TABLE IF EXISTS market_cap;
DROP TABLE IF EXISTS peer_groups;
DROP TABLE IF EXISTS sectors;
DROP TABLE IF EXISTS stock_prices;

CREATE TABLE companies(

id INTEGER PRIMARY KEY,

company_logo TEXT,

company_name TEXT NOT NULL,

chart_link TEXT,

about_company TEXT,

website TEXT,

nse_profile TEXT,

bse_profile TEXT,

face_value REAL,

book_value REAL,

roce_percentage REAL,

roe_percentage REAL

);

CREATE TABLE balancesheet(

id INTEGER PRIMARY KEY,

company_id INTEGER,

year INTEGER,

equity_capital REAL,

reserves REAL,

borrowings REAL,

other_liabilities REAL,

total_liabilities REAL,

fixed_assets REAL,

cwip REAL,

investments REAL,

other_asset REAL,

total_assets REAL,

FOREIGN KEY(company_id)

REFERENCES companies(id)

);

CREATE TABLE profitandloss(

id INTEGER PRIMARY KEY,

company_id INTEGER,

year INTEGER,

sales REAL,

expenses REAL,

operating_profit REAL,

opm_percentage REAL,

other_income REAL,

interest REAL,

depreciation REAL,

profit_before_tax REAL,

tax_percentage REAL,

net_profit REAL,

eps REAL,

dividend_payout REAL,

FOREIGN KEY(company_id)

REFERENCES companies(id)

);

CREATE TABLE cashflow(

id INTEGER PRIMARY KEY,

company_id INTEGER,

year INTEGER,

operating_activity REAL,

investing_activity REAL,

financing_activity REAL,

net_cash_flow REAL,

FOREIGN KEY(company_id)

REFERENCES companies(id)

);


CREATE TABLE analysis (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    compounded_sales_growth TEXT,

    compounded_profit_growth TEXT,

    stock_price_cagr TEXT,

    roe TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE documents (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER,

    annual_report TEXT,

    concall_transcript TEXT,

    investor_presentation TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE prosandcons (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    category TEXT,

    description TEXT,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE financial_ratios (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER,

    pe_ratio REAL,

    pb_ratio REAL,

    debt_to_equity REAL,

    current_ratio REAL,

    quick_ratio REAL,

    return_on_assets REAL,

    return_on_equity REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE market_cap (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    year INTEGER,

    market_cap REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE peer_groups (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    peer_company TEXT,

    cmp REAL,

    pe REAL,

    market_cap REAL,

    dividend_yield REAL,

    np_qtr REAL,

    qtr_profit_var REAL,

    sales_qtr REAL,

    qtr_sales_var REAL,

    roce REAL,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);


CREATE TABLE sectors (

    id INTEGER PRIMARY KEY,

    sector_name TEXT,

    industry_name TEXT

);


CREATE TABLE stock_prices (

    id INTEGER PRIMARY KEY,

    company_id TEXT NOT NULL,

    trading_date DATE,

    open_price REAL,

    high_price REAL,

    low_price REAL,

    close_price REAL,

    adjusted_close REAL,

    volume INTEGER,

    FOREIGN KEY(company_id)
        REFERENCES companies(id)

);

