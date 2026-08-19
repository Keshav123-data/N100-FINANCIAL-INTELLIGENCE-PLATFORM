"""
Valuation API router.

Sprint 6 — Days 39-40
Valuation metrics and historical data.
"""

import sqlite3
from fastapi import APIRouter, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


@router.get("/market-cap/{company_id}")
def get_market_cap_history(company_id: str):
    """
    Return historical valuation multiples (P/E, P/B, EV/EBITDA, dividend yield).
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            m.company_id,
            m.date,
            m.pe_ratio,
            m.pb_ratio,
            m.ev_ebitda,
            m.dividend_yield,
            m.market_cap_cr
        FROM market_cap m
        WHERE m.company_id = ?
        ORDER BY m.date DESC
        LIMIT 100
        """
        
        cursor.execute(query, (company_id,))
        rows = cursor.fetchall()
        connection.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No market cap data for company {company_id}")
        
        results = [
            {
                "company_id": row[0],
                "date": row[1],
                "pe_ratio": row[2],
                "pb_ratio": row[3],
                "ev_ebitda": row[4],
                "dividend_yield": row[5],
                "market_cap_cr": row[6],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "company_id": company_id,
            "history_count": len(results),
            "history": results,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/valuation")
def get_valuation_dashboard():
    """
    Return valuation dashboard data with all companies ranked by valuation metrics.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            c.id,
            c.company_name,
            c.broad_sector,
            m.pe_ratio,
            m.pb_ratio,
            m.ev_ebitda,
            m.dividend_yield,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            m.market_cap_cr
        FROM companies c
        LEFT JOIN market_cap m ON c.id = m.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        WHERE m.pe_ratio IS NOT NULL
        ORDER BY m.pe_ratio ASC
        LIMIT 100
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        connection.close()
        
        results = [
            {
                "company_id": row[0],
                "company_name": row[1],
                "sector": row[2],
                "pe_ratio": row[3],
                "pb_ratio": row[4],
                "ev_ebitda": row[5],
                "dividend_yield": row[6],
                "revenue_cagr_5yr": row[7],
                "pat_cagr_5yr": row[8],
                "market_cap_cr": row[9],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "company_count": len(results),
            "companies": results,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))