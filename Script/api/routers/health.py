"""
Health API router.

Sprint 6 — Day 38
"""

import time

import sqlite3

from fastapi import APIRouter

from Script.api.config import (
    API_VERSION,
    START_TIME,
)

from Script.api.database import get_db_connection


router = APIRouter()


# ============================================================
# HEALTH CHECK
# ============================================================

@router.get("/health")
def health_check():
    """
    Return API health and SQLite table row counts.
    """

    connection = get_db_connection()

    cursor = connection.cursor()

    tables = [
        "companies",
        "sectors",
        "market_cap",
        "financial_ratios",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "stock_prices",
        "peer_groups",
        "documents",
    ]

    db_row_counts = {}

    for table in tables:

        try:

            cursor.execute(
                f"SELECT COUNT(*) FROM {table}"
            )

            db_row_counts[table] = cursor.fetchone()[0]

        except sqlite3.Error:

            db_row_counts[table] = None

    connection.close()

    return {
        "status": "ok",
        "db_row_counts": db_row_counts,
        "uptime_seconds": round(
            time.time() - START_TIME,
            2,
        ),
        "version": API_VERSION,
    }