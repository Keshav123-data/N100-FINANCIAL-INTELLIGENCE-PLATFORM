"""
Screener API router.

Sprint 6 — Days 39-40
Financial screener with multiple filter criteria.
"""

import sqlite3
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


def row_to_dict(row: sqlite3.Row) -> dict:
    """Convert SQLite row to dictionary."""
    return dict(row) if row else None


@router.get("/screener")
def screener(
    min_roe: Optional[float] = Query(None, description="Minimum ROE %"),
    max_de: Optional[float] = Query(None, description="Maximum Debt-to-Equity"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    min_rev_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year revenue CAGR %"),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5-year PAT CAGR %"),
    max_pe: Optional[float] = Query(None, description="Maximum P/E ratio"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Screen companies based on financial metrics.
    
    Returns ranked company list with all filter metrics.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Base query
        query = """
        SELECT 
            c.id,
            c.company_name,
            c.broad_sector,
            c.sub_sector,
            fr.return_on_equity_pct as roe_pct,
            fr.debt_to_equity as de_ratio,
            fr.free_cash_flow_cr as fcf,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            m.pe_ratio
        FROM companies c
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        WHERE 1=1
        """
        
        params = []
        
        if min_roe is not None:
            query += " AND fr.return_on_equity_pct >= ?"
            params.append(min_roe)
        
        if max_de is not None:
            query += " AND fr.debt_to_equity <= ?"
            params.append(max_de)
        
        if min_fcf is not None:
            query += " AND fr.free_cash_flow_cr >= ?"
            params.append(min_fcf)
        
        if sector:
            query += " AND c.broad_sector = ?"
            params.append(sector)
        
        if min_rev_cagr_5yr is not None:
            query += " AND fr.revenue_cagr_5yr >= ?"
            params.append(min_rev_cagr_5yr)
        
        if min_pat_cagr_5yr is not None:
            query += " AND fr.pat_cagr_5yr >= ?"
            params.append(min_pat_cagr_5yr)
        
        if max_pe is not None:
            query += " AND m.pe_ratio <= ?"
            params.append(max_pe)
        
        query += " ORDER BY fr.return_on_equity_pct DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        connection.close()
        
        results = [
            {
                "company_id": row[0],
                "company_name": row[1],
                "broad_sector": row[2],
                "sub_sector": row[3],
                "roe_pct": row[4],
                "de_ratio": row[5],
                "fcf_cr": row[6],
                "revenue_cagr_5yr": row[7],
                "pat_cagr_5yr": row[8],
                "pe_ratio": row[9],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "filter_criteria": {
                "min_roe": min_roe,
                "max_de": max_de,
                "min_fcf": min_fcf,
                "sector": sector,
                "min_rev_cagr_5yr": min_rev_cagr_5yr,
                "min_pat_cagr_5yr": min_pat_cagr_5yr,
                "max_pe": max_pe,
            },
            "count": len(results),
            "results": results,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))