"""
Documents API router.

Sprint 6 — Days 39-40
Annual reports and document links.
"""

import sqlite3
import requests
from fastapi import APIRouter, HTTPException

from Script.api.database import get_db_connection


router = APIRouter()


def is_url_valid(url: str) -> bool:
    """Check if URL is accessible."""
    if not url:
        return False
    
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except:
        return False


@router.get("/companies/{company_id}/documents")
def get_company_documents(company_id: str):
    """
    Return annual report links with is_url_valid boolean flag.
    """
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            d.company_id,
            d.report_year,
            d.document_url,
            d.document_type
        FROM documents d
        WHERE d.company_id = ?
        ORDER BY d.report_year DESC
        """
        
        cursor.execute(query, (company_id,))
        rows = cursor.fetchall()
        connection.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"No documents found for company {company_id}")
        
        results = [
            {
                "company_id": row[0],
                "report_year": row[1],
                "document_url": row[2],
                "document_type": row[3],
                "is_url_valid": is_url_valid(row[2]),
            }
            for row in rows
        ]
        
        return {
            "status": "success",
            "company_id": company_id,
            "document_count": len(results),
            "documents": results,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))