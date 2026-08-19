"""
Portfolio API router.

Sprint 6 — Days 39-40
Portfolio analytics and statistics.
"""

import sqlite3
from fastapi import APIRouter, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


@router.get("/portfolio/stats")
def get_portfolio_stats():
    """
    Return P10 through P90 percentile table for 10 core KPIs across all companies.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        kpis = [
            ("return_on_equity_pct", "ROE %"),
            ("debt_to_equity", "Debt/Equity"),
            ("free_cash_flow_cr", "Free Cash Flow"),
            ("revenue_cagr_5yr", "Revenue CAGR 5yr"),
            ("pat_cagr_5yr", "PAT CAGR 5yr"),
            ("asset_turnover", "Asset Turnover"),
            ("interest_coverage", "Interest Coverage"),
            ("net_profit_margin_pct", "Net Profit Margin %"),
            ("operating_profit_margin_pct", "Operating Profit Margin %"),
            ("composite_quality_score", "Quality Score"),
        ]
        
        results = {}
        
        for kpi_col, kpi_name in kpis:
            query = f"""
            SELECT 
                MIN({kpi_col}) as min_val,
                PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY {kpi_col}) as p10,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {kpi_col}) as p25,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {kpi_col}) as p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {kpi_col}) as p75,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY {kpi_col}) as p90,
                MAX({kpi_col}) as max_val,
                AVG({kpi_col}) as avg_val,
                STDEV({kpi_col}) as std_dev
            FROM financial_ratios
            WHERE {kpi_col} IS NOT NULL
            """
            
            try:
                cursor.execute(query)
                row = cursor.fetchone()
                
                if row:
                    results[kpi_name] = {
                        "min": round(row[0], 2) if row[0] else None,
                        "p10": round(row[1], 2) if row[1] else None,
                        "p25": round(row[2], 2) if row[2] else None,
                        "p50": round(row[3], 2) if row[3] else None,
                        "p75": round(row[4], 2) if row[4] else None,
                        "p90": round(row[5], 2) if row[5] else None,
                        "max": round(row[6], 2) if row[6] else None,
                        "mean": round(row[7], 2) if row[7] else None,
                        "std": round(row[8], 2) if row[8] else None,
                    }
            except:
                # Handle databases without PERCENTILE_CONT (SQLite)
                # Fallback to manual percentile calculation
                cursor.execute(f"SELECT {kpi_col} FROM financial_ratios WHERE {kpi_col} IS NOT NULL ORDER BY {kpi_col}")
                values = [row[0] for row in cursor.fetchall()]
                
                if values:
                    values_sorted = sorted(values)
                    n = len(values_sorted)
                    
                    def percentile(data, p):
                        k = (len(data) - 1) * p / 100
                        f = int(k)
                        c = k - f
                        if f + 1 < len(data):
                            return data[f] * (1 - c) + data[f + 1] * c
                        return data[f]
                    
                    results[kpi_name] = {
                        "min": round(values_sorted[0], 2),
                        "p10": round(percentile(values_sorted, 10), 2),
                        "p25": round(percentile(values_sorted, 25), 2),
                        "p50": round(percentile(values_sorted, 50), 2),
                        "p75": round(percentile(values_sorted, 75), 2),
                        "p90": round(percentile(values_sorted, 90), 2),
                        "max": round(values_sorted[-1], 2),
                        "mean": round(sum(values_sorted) / len(values_sorted), 2),
                        "std": round((sum((x - (sum(values_sorted) / len(values_sorted))) ** 2 for x in values_sorted) / len(values_sorted)) ** 0.5, 2),
                    }
        
        connection.close()
        
        return {
            "status": "success",
            "metrics": results,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))