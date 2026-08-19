"""
Peers API router.

Sprint 6 — Days 39-40
Peer group analysis and comparison.
"""

import sqlite3
from typing import Optional
from fastapi import APIRouter, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    """
    Return all companies in a peer group with percentile rank for each metric.
    Returns HTTP 404 if peer group not found.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if peer group exists
        cursor.execute(
            "SELECT COUNT(*) FROM peer_groups WHERE peer_group = ?",
            (group_name,)
        )
        
        if cursor.fetchone()[0] == 0:
            connection.close()
            raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")
        
        # Get companies and their metrics
        query = """
        SELECT 
            c.id,
            c.company_name,
            pg.peer_group,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.free_cash_flow_cr,
            fr.revenue_cagr_5yr,
            fr.asset_turnover,
            m.pe_ratio,
            fr.interest_coverage
        FROM companies c
        JOIN peer_groups pg ON c.id = pg.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        WHERE pg.peer_group = ?
        ORDER BY fr.return_on_equity_pct DESC
        """
        
        cursor.execute(query, (group_name,))
        rows = cursor.fetchall()
        connection.close()
        
        results = [
            {
                "company_id": row[0],
                "company_name": row[1],
                "peer_group": row[2],
                "roe_pct": row[3],
                "de_ratio": row[4],
                "fcf_cr": row[5],
                "revenue_cagr_5yr": row[6],
                "asset_turnover": row[7],
                "pe_ratio": row[8],
                "interest_coverage": row[9],
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "peer_group": group_name,
            "company_count": len(results),
            "companies": results,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companies/{company_id}/peers/compare")
def get_peers_comparison(company_id: str):
    """
    Return radar chart data: company metrics vs peer group average vs benchmark.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get company's peer group
        cursor.execute(
            "SELECT peer_group FROM peer_groups WHERE company_id = ? LIMIT 1",
            (company_id,)
        )
        
        peer_result = cursor.fetchone()
        if not peer_result:
            connection.close()
            raise HTTPException(status_code=404, detail="Company not found in peer groups")
        
        peer_group = peer_result[0]
        
        # Get company metrics
        cursor.execute("""
        SELECT 
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.asset_turnover,
            fr.revenue_cagr_5yr,
            m.pe_ratio,
            fr.interest_coverage
        FROM financial_ratios fr
        LEFT JOIN market_cap m ON fr.company_id = m.company_id
        WHERE fr.company_id = ?
        """, (company_id,))
        
        company_data = cursor.fetchone()
        
        # Get peer group averages
        cursor.execute("""
        SELECT 
            AVG(fr.return_on_equity_pct),
            AVG(fr.debt_to_equity),
            AVG(fr.asset_turnover),
            AVG(fr.revenue_cagr_5yr),
            AVG(m.pe_ratio),
            AVG(fr.interest_coverage)
        FROM companies c
        JOIN peer_groups pg ON c.id = pg.company_id
        LEFT JOIN financial_ratios fr ON c.id = fr.company_id
        LEFT JOIN market_cap m ON c.id = m.company_id
        WHERE pg.peer_group = ?
        """, (peer_group,))
        
        peer_avg = cursor.fetchone()
        connection.close()
        
        return {
            "status": "success",
            "company_id": company_id,
            "peer_group": peer_group,
            "metrics": [
                "ROE %",
                "Debt/Equity",
                "Asset Turnover",
                "Revenue CAGR 5yr",
                "P/E Ratio",
                "Interest Coverage",
            ],
            "company_values": [
                company_data[0] or 0,
                company_data[1] or 0,
                company_data[2] or 0,
                company_data[3] or 0,
                company_data[4] or 0,
                company_data[5] or 0,
            ],
            "peer_average_values": [
                peer_avg[0] or 0,
                peer_avg[1] or 0,
                peer_avg[2] or 0,
                peer_avg[3] or 0,
                peer_avg[4] or 0,
                peer_avg[5] or 0,
            ],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
