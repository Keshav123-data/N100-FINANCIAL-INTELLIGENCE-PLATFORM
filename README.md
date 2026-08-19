# N100 Financial Intelligence Platform

**Financial analysis and screening platform for NIFTY 100 companies**

## Overview

The N100 Financial Intelligence Platform is a comprehensive financial analysis system designed to analyze, screen, and profile 92 NIFTY 100 companies. It provides:

- **Financial Data ETL**: Automated extraction, normalization, and loading of P&L, balance sheet, cash flow, and market data
- **KPI Computation**: 19+ financial ratios and metrics (ROE, D/E, Free Cash Flow, CAGR, etc.)
- **Intelligence Analytics**: Clustering, profiling, outlier detection, and peer group analysis
- **REST API**: 16 FastAPI endpoints for programmatic access to all data
- **Interactive Dashboard**: Streamlit web interface with screener, tearsheets, and analytics
- **Quality Assurance**: 67+ unit tests covering ETL, KPI, and analytics

---

## Project Structure

```
N100 FINANCIAL INTELLIGENCE PLATFORM/
├── Data/                          # Raw & processed data
│   ├── raw/                       # Source Excel files
│   └── processed/                 # Cleaned CSV files
├── DB/                            # SQLite database
│   └── nifty100.db               # Main database (92 companies)
├── Script/                        # Python application
│   ├── ETL/                      # Data loading & transformation
│   │   ├── loader.py             # Excel to database loader
│   │   ├── validator.py          # Data quality validation
│   │   └── normaliser.py         # Column name standardization
│   ├── analytics/                # Financial analysis
│   │   ├── ratios.py             # Basic ratios (ROE, D/E, etc.)
│   │   ├── cagr.py               # CAGR calculations
│   │   ├── clustering.py         # KMeans clustering (5 archetypes)
│   │   ├── cashflow_kpis.py      # Cash flow analysis
│   │   └── populate_financial_ratios.py  # Ratio computation
│   ├── api/                      # REST API
│   │   ├── main.py               # FastAPI application
│   │   ├── database.py           # Database connection
│   │   ├── config.py             # API configuration
│   │   └── routers/              # 16 API endpoints
│   │       ├── companies.py      # Company CRUD + financials
│   │       ├── screener.py       # Financial screener
│   │       ├── sectors.py        # Sector analysis
│   │       ├── peers.py          # Peer group comparison
│   │       ├── valuation.py      # Valuation metrics
│   │       ├── portfolio.py      # Portfolio statistics
│   │       ├── documents.py      # Annual reports
│   │       └── health.py         # API health
│   └── dashboard/                # Streamlit UI
│       ├── app.py                # Main dashboard
│       └── pages/                # Dashboard screens
├── Tests/                        # Test suite (67+ tests)
│   ├── ETL/                      # ETL tests (35 passing)
│   ├── kpi/                      # KPI tests (26 passing)
│   └── test_screener.py          # API screener test
├── Output/                       # Generated reports
│   ├── cluster_labels.csv        # 92 companies + cluster assignment
│   ├── cluster_profile_*.csv     # Cluster statistics
│   ├── financial_ratios.csv      # All computed KPIs
│   ├── outlier_report.csv        # Z-score outliers
│   ├── portfolio_stats.csv       # Percentile distributions
│   └── (20+ more reports)
├── docs/                         # Documentation
│   └── openapi.json              # API specification
├── reports/                      # Analysis outputs
│   ├── elbow_plot.png            # K-means elbow curve
│   ├── correlation_heatmap.png   # KPI correlations
│   ├── radar_charts/             # Company radar plots
│   └── tearsheets/               # 92 PDF tearsheets
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── .env                          # Environment variables
```

---

## Quick Start

### Prerequisites
- Python 3.13+
- SQLite3
- Virtual environment recommended

### Installation

1. **Clone/extract the project**
```bash
cd "N100 FINANCIAL INTELLIGENCE PLATFORM"
```

2. **Set up virtual environment** (optional but recommended)
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Verify setup**
```bash
python -c "import Script.api.main; print('✓ Setup successful')"
```

---

## Usage

### Option 1: REST API

**Start the API server:**
```bash
uvicorn Script.api.main:app --host 0.0.0.0 --port 8000
```

**Access endpoints:**
- Health check: `GET http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/docs` (Swagger UI)
- OpenAPI spec: `http://localhost:8000/docs/openapi.json`

**Example API calls:**
```bash
# Get all companies
curl http://localhost:8000/api/v1/companies

# Get company details
curl http://localhost:8000/api/v1/companies/TCS

# Screen companies (ROE >= 15%)
curl "http://localhost:8000/api/v1/screener?min_roe=15"

# Get sector analysis
curl http://localhost:8000/api/v1/sectors

# Get portfolio statistics
curl http://localhost:8000/api/v1/portfolio/stats
```

### Option 2: Interactive Dashboard

**Start Streamlit dashboard:**
```bash
streamlit run Script/dashboard/app.py
```

Access at `http://localhost:8501`

**Features:**
- **Screener**: Filter companies by financial metrics
- **Company Profile**: View detailed KPIs, financials, and tearsheet
- **Sector Analysis**: Compare sectors and companies
- **Clustering**: View company archetypes and profiles
- **Reports**: Download CSV exports and PDF tearsheets

### Option 3: Data Processing

**Reload financial data from source:**
```bash
python Script/ETL/load_database.py
```

**Recalculate financial ratios:**
```bash
python Script/analytics/populate_financial_ratios.py
```

**Re-run clustering analysis:**
```bash
python Script/analytics/clustering.py
```

---

## API Endpoints (16 Total)

### Health & Status
- `GET /api/v1/health` - API status, DB row counts, uptime

### Companies (6 endpoints)
- `GET /api/v1/companies` - List all companies (paginated, filterable)
- `GET /api/v1/companies/{id}` - Company profile with latest KPIs
- `GET /api/v1/companies/{id}/pl` - P&L history (multi-year)
- `GET /api/v1/companies/{id}/bs` - Balance sheet history
- `GET /api/v1/companies/{id}/cashflow` - Cash flow history
- `GET /api/v1/companies/{id}/ratios` - Financial ratios by year

### Screener
- `GET /api/v1/screener` - Screen companies by ROE, D/E, FCF, sector, CAGR, P/E

### Sectors (2 endpoints)
- `GET /api/v1/sectors` - All sectors with statistics
- `GET /api/v1/sectors/{sector}` - Companies in sector

### Peers (2 endpoints)
- `GET /api/v1/peers/{group}` - Peer group comparison
- `GET /api/v1/companies/{id}/peers/compare` - Radar chart data

### Valuation (2 endpoints)
- `GET /api/v1/market-cap/{id}` - Historical P/E, P/B, EV/EBITDA
- `GET /api/v1/valuation` - Valuation dashboard

### Portfolio
- `GET /api/v1/portfolio/stats` - P10-P90 percentile stats for 10 KPIs

### Documents
- `GET /api/v1/companies/{id}/documents` - Annual reports & links

---

## Financial Metrics & KPIs

### Basic Ratios
- **Return on Equity (ROE)**: Net Profit / (Equity Capital + Reserves) × 100
- **Debt-to-Equity (D/E)**: Borrowings / (Equity Capital + Reserves)
- **Net Profit Margin**: Net Profit / Sales × 100
- **Operating Profit Margin**: Operating Profit / Sales × 100
- **Asset Turnover**: Sales / Total Assets

### Advanced Metrics
- **Return on Capital Employed (ROCE)**: EBIT / (Equity + Borrowings) × 100
- **Interest Coverage Ratio**: EBIT / Interest Expense
- **Free Cash Flow**: Operating Cash Flow - Investing Cash Flow
- **Debt-free companies** flagged separately
- **High leverage** flagged for D/E > 5 (non-financial)

### Growth Metrics
- **Revenue CAGR 5yr**: 5-year compound annual growth rate
- **PAT CAGR 5yr**: 5-year profit after tax CAGR
- **EPS CAGR 5yr**: 5-year earnings per share CAGR
- **FCF CAGR 5yr**: 5-year free cash flow CAGR

### Quality Score
- **Composite Quality Score**: Weighted average of ROE (30%), NPM (25%), Asset Turnover (20%), Revenue CAGR (25%)

---

## Data Quality & Validation

### Checks Implemented
- ✅ **92 companies** loaded with confirmed data
- ✅ **≥90% of companies** have 10+ years of P&L, BS, CF records
- ✅ **0 foreign key violations** (PRAGMA foreign_key_check)
- ✅ **1,100+ financial ratio records** computed
- ✅ **All companies** assigned to one of 5 clusters
- ✅ **Zero parse failures** in annual reports

### Outlier Detection
- Z-score > 3 flagged per broad sector
- 23 outliers identified across metrics
- Stored in `Output/outlier_report.csv`

### Clustering (Day 36)
5 investment archetypes identified via KMeans clustering:
1. **Defensive Quality**: High ROE, low leverage, stable growth
2. **Value Cyclicals**: Moderate metrics, cyclical exposure
3. **Defensive Quality 2**: Utility-like characteristics
4. **Distressed/Turnaround**: Low profitability, high leverage, recovery potential
5. **Emerging Growth**: Strong revenue growth, high risk

---

## Test Suite

**Total Tests: 67 passing, 1 skipped**

### ETL Tests (35 tests)
```bash
pytest Tests/ETL/test_normaliser.py -v
```
- Year normalization: Mar 2023 → 2023, FY2021 → 2021, etc.
- Ticker normalization: abb → ABB, tcs → TCS, etc.
- 20 variants tested

### KPI Tests (26 tests)
```bash
pytest Tests/kpi/ -v
```
- CAGR: Normal, turnaround, decline, zero-base scenarios
- Ratios: ROE with positive/negative equity, D/E for debt-free, ICR, ROA, ROCE
- Cash Flow: FCF, quality, capex, conversion rate, capital allocation

### Run All Tests
```bash
pytest Tests/ -v
```

Expected output:
```
67 passed, 1 skipped in 3.00s
```

---

## Environment Configuration

**.env file settings:**
```env
DATABASE_PATH=DB/nifty100.db
PROCESSED_DATA=Data/processed
RAW_DATA=Data/raw
OUTPUT_DIR=output
LOG_LEVEL=INFO
```

---

## Deliverables (Sprint 6)

### Day 36-37: Clustering & Profiling ✅
- [x] Elbow plot confirming k=5
- [x] 5 cluster archetypes with descriptive names
- [x] Cluster profile statistics (mean/median)
- [x] Correlation heatmap (10 KPIs)
- [x] Outlier detection (Z-score > 3)
- [x] Portfolio statistics (P10-P90)

### Day 38: FastAPI Scaffold ✅
- [x] FastAPI server with CORS & logging middleware
- [x] 13 routes configured with proper imports
- [x] OpenAPI documentation auto-generated
- [x] Health endpoint with DB row counts & uptime

### Days 39-40: API Endpoints ✅
- [x] 16 endpoints implemented (6 companies + 10 specialized)
- [x] Screener with multi-parameter filtering
- [x] Sector analysis and peer group comparison
- [x] Valuation metrics and market cap history
- [x] Portfolio statistics endpoint
- [x] Document links with URL validation

### Days 41-42: Tests ✅
- [x] 35 ETL tests (100% passing)
- [x] 26 KPI tests (100% passing)
- [x] 6 Cashflow KPI tests (100% passing)
- [x] Total: 67 tests passing, 1 skipped

### Day 44: Documentation ✅
- [x] README.md (this file)
- [x] OpenAPI specification
- [x] API endpoint documentation
- [x] Database schema documentation

### Day 45: Acceptance Gates
- ✅ AC-01: 92 companies in database
- ✅ AC-02: 90%+ with 10+ year records
- ✅ AC-03: 0 foreign key violations
- ✅ AC-04: 1,100+ financial ratio records
- ✅ AC-15: All 92 companies clustered
- ✅ AC-18: 67+ tests, 0 failures

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"
```bash
pip install -r requirements.txt
```

### Database connection errors
- Verify DB path in `.env` is correct
- Check file permissions: `DB/nifty100.db` must be readable

### Screener returns no results
- Ensure `Output/financial_ratios.csv` exists (run ETL first)
- Check filter parameters are realistic for the data

### API won't start on port 8000
```bash
# Try different port
uvicorn Script.api.main:app --port 8001
```

### Tests failing
```bash
# Use venv Python explicitly
.\venv\Scripts\python.exe -m pytest Tests/ -v
```

---

## Technology Stack

**Backend:**
- FastAPI 0.141.1 - REST API framework
- SQLite3 - Database
- Pandas 3.0.3 - Data processing
- NumPy 2.5.1 - Numerical computation
- Scikit-learn 1.9.0 - Machine learning (clustering)

**Frontend:**
- Streamlit 1.61.1 - Interactive dashboard
- Plotly 6.9.0 - Interactive charts
- Seaborn 0.13.2 - Statistical visualization

**Testing & Quality:**
- Pytest 9.1.1 - Test framework
- Black 26.5.1 - Code formatting
- Flake8 7.3.0 - Linting

**Data Processing:**
- Openpyxl 3.1.5 - Excel reading
- Python-dotenv 1.2.2 - Environment variables

---

## Performance

### Typical Response Times (on venv)
- Company list: ~200ms
- Screener (100 companies): ~500ms
- Sector analysis: ~300ms
- API health: ~50ms
- Financial ratios query: ~150ms

### Database Statistics
- Total companies: 92
- Total financial records: 1,100+
- Years of history: 10+ per company
- Total sectors: 11
- Total peer groups: Multiple per sector

---

## Support & Issues

For issues or questions:
1. Check test suite results: `pytest Tests/ -v`
2. Review API docs: Visit `/docs` endpoint
3. Check database integrity: `python Script/ETL/validator.py`
4. Verify environment: `python -c "import Script.api.main; print('OK')"`

---

## License

Internal use only - N100 Financial Intelligence Platform

---

**Last Updated:** 2026-08-19  
**Project Status:** Active  
**Sprint 6 Completion:** ~95%
