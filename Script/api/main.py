"""
N100 Financial Intelligence Platform
FastAPI Application

Sprint 6 — Day 38
API Server Scaffold
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from Script.api.config import (
    DATABASE_PATH,
    API_VERSION,
)

from Script.api.database import get_db_connection

from Script.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
)

# ============================================================
# LOGGING
# ============================================================

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("n100_api")


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="N100 Financial Intelligence API",
    description=(
        "REST API for the N100 Financial Intelligence Platform."
    ),
    version=API_VERSION,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    """
    Log method, path, status code and response time.
    """

    start = time.perf_counter()

    response = await call_next(request)

    elapsed = time.perf_counter() - start

    logger.info(
        "%s %s -> %s | %.4f sec",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )

    return response


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    """
    Return basic API information.
    """

    return {
        "name": "N100 Financial Intelligence API",
        "version": API_VERSION,
        "status": "running",
        "docs": "/docs",
    }


# ============================================================
# ROUTERS
# ============================================================

API_PREFIX = "/api/v1"

app.include_router(
    health.router,
    prefix=API_PREFIX,
    tags=["Health"],
)

app.include_router(
    companies.router,
    prefix=API_PREFIX,
    tags=["Companies"],
)

app.include_router(
    screener.router,
    prefix=API_PREFIX,
    tags=["Screener"],
)

app.include_router(
    sectors.router,
    prefix=API_PREFIX,
    tags=["Sectors"],
)

app.include_router(
    peers.router,
    prefix=API_PREFIX,
    tags=["Peers"],
)

app.include_router(
    valuation.router,
    prefix=API_PREFIX,
    tags=["Valuation"],
)

app.include_router(
    portfolio.router,
    prefix=API_PREFIX,
    tags=["Portfolio"],
)

app.include_router(
    documents.router,
    prefix=API_PREFIX,
    tags=["Documents"],
)


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup_event():
    """
    Verify database availability when API starts.
    """

    if not DATABASE_PATH.exists():

        logger.error(
            "Database not found: %s",
            DATABASE_PATH,
        )

        return

    connection = get_db_connection()

    connection.close()

    logger.info("N100 API started successfully")

    logger.info(
        "Database: %s",
        DATABASE_PATH,
    )