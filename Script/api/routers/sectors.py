"""
Sectors API router.

Sprint 6 — Days 39-40
Sector analysis and grouping endpoints.
"""

import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


@router.get("/sectors")
def get_sectors():
    """
    Return all sectors with company count and median metrics.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            s.broad_sector,
            COUNT(DISTINCT c.id) as company_count,
            ROUND(AVG(fr.return_on_equity_pct), 2) as median_roe,
            ROUND(AVG(m.pe_ratio), 2) as median_pe,
            ROUND(AVG(fr.debt_to_equity), 2) as median_de
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        GROUP BY s.broad_sector
        ORDER BY company_count DESC
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        connection.close()
        
        results = [
            {
                "sector": row[0],
                "company_count": row[1],
                "median_roe": row[2],
                "median_pe": row[3],
                "median_de": row[4],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "sector_count": len(results),
            "sectors": results,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sectors/{sector_name}")
def get_sector_companies(sector_name: str):
    """
    Return all companies in a specific sector with latest KPIs.
    Returns HTTP 404 if sector not found.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # First check if sector exists
        cursor.execute(
            "SELECT COUNT(*) FROM companies WHERE broad_sector = ?",
            (sector_name,)
        )
        
        if cursor.fetchone()[0] == 0:
            connection.close()
            raise HTTPException(status_code=404, detail=f"Sector '{sector_name}' not found")
        
        # Get all companies in the sector
        query = """
        SELECT 
            c.id,
            c.company_name,
            c.broad_sector,
            c.sub_sector,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            m.pe_ratio
        FROM companies c
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        WHERE c.broad_sector = ?
        ORDER BY fr.return_on_equity_pct DESC
        """
        
        cursor.execute(query, (sector_name,))
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
                "pe_ratio": row[8],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "sector": sector_name,
            "company_count": len(results),
            "companies": results,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))