from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import re
import sqlite3

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/api/v1/companies",
    tags=["Companies"],
)


# ============================================================
# DATABASE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_CANDIDATES = [
    PROJECT_ROOT / "DB" / "nifty100.db",
    PROJECT_ROOT / "nifty100.db",
]

DB_PATH: Optional[Path] = None

for candidate in DB_CANDIDATES:
    if candidate.exists():
        DB_PATH = candidate
        break

if DB_PATH is None:
    DB_PATH = PROJECT_ROOT / "DB" / "nifty100.db"


def get_connection() -> sqlite3.Connection:
    """
    Create a SQLite connection.

    Row factory allows access using:
        row["column_name"]
    """

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# HELPERS
# ============================================================

def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def extract_year(value: Any) -> Optional[int]:
    """
    Convert different year formats into an integer.

    Supported examples:

        2024
        "2024"
        "Mar 2024"
        "Mar-24"
        "Mar-22"
        "Mar 22"
        "TTM"

    TTM returns None because it is not an annual year.
    """

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    # TTM is not a calendar/fiscal year.
    if text.upper() == "TTM":
        return None

    # Four-digit year anywhere in the string.
    match = re.search(r"(20\d{2}|19\d{2})", text)

    if match:
        return int(match.group(1))

    # Two-digit year, e.g. Mar-22 -> 2022
    match = re.search(r"(?:^|[-\s/])(\d{2})(?:$|[-\s/])", text)

    if match:
        yy = int(match.group(1))

        if yy <= 30:
            return 2000 + yy

        return 1900 + yy

    # Pure numeric value.
    try:
        numeric = int(float(text))

        if 1900 <= numeric <= 2100:
            return numeric

    except (TypeError, ValueError):
        pass

    return None


def normalize_year_for_response(value: Any) -> Any:
    """
    Preserve the original database year in the API response.

    This is intentional because existing P&L and BS APIs return
    values such as 'Mar 2024'.
    """

    return value


def year_matches(
    value: Any,
    from_year: Optional[int],
    to_year: Optional[int],
) -> bool:

    # No filters supplied.
    if from_year is None and to_year is None:
        return True

    year = extract_year(value)

    # TTM cannot be compared against numeric year filters.
    if year is None:
        return False

    if from_year is not None and year < from_year:
        return False

    if to_year is not None and year > to_year:
        return False

    return True


def clean_company_name(value: Any) -> Any:
    """
    Some company records contain newline descriptions, for example:

        Apollo Hospitals
        Chain of Indian private hospitals

    Do not modify the database. Clean the API output only.
    """

    if value is None:
        return None

    value = str(value)

    value = re.sub(r"\s+", " ", value).strip()

    return value


# ============================================================
# COMPANY LIST
# ============================================================

@router.get("")
@router.get("/")
def get_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sector: Optional[str] = None,
    sub_sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "company_name",
    sort_order: str = "asc",
):
    """
    Get paginated company list.
    """

    allowed_sort_columns = {
        "company_name": "c.company_name",
        "id": "c.id",
        "broad_sector": "c.broad_sector",
        "sub_sector": "c.sub_sector",
        "market_cap_category": "c.market_cap_category",
        "roe_pct": "fr.return_on_equity_pct",
        "roce_pct": "c.roce_percentage",
    }

    sort_column = allowed_sort_columns.get(
        sort_by,
        "c.company_name",
    )

    sort_direction = (
        "DESC"
        if str(sort_order).lower() == "desc"
        else "ASC"
    )

    conditions = []
    params: list[Any] = []

    if sector:
        conditions.append(
            "LOWER(c.broad_sector) = LOWER(?)"
        )
        params.append(sector.strip())

    if sub_sector:
        conditions.append(
            "LOWER(c.sub_sector) = LOWER(?)"
        )
        params.append(sub_sector.strip())

    if market_cap_category:
        conditions.append(
            "LOWER(c.market_cap_category) = LOWER(?)"
        )
        params.append(market_cap_category.strip())

    if search:
        conditions.append(
            """
            (
                LOWER(c.id) LIKE LOWER(?)
                OR LOWER(c.company_name) LIKE LOWER(?)
            )
            """
        )

        search_value = f"%{search.strip()}%"

        params.extend([
            search_value,
            search_value,
        ])

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    offset = (page - 1) * page_size

    with get_connection() as conn:

        count_query = f"""
            SELECT COUNT(*)
            FROM companies c
            {where_clause}
        """

        total_count = conn.execute(
            count_query,
            params,
        ).fetchone()[0]

        query = f"""
            SELECT
                c.id,
                c.company_name,
                c.broad_sector,
                c.sub_sector,
                c.market_cap_category,

                c.roce_percentage AS roce_pct,

                fr.return_on_equity_pct AS roe_pct

            FROM companies c

            LEFT JOIN financial_ratios fr
                ON fr.company_id = c.id

            {where_clause}

            ORDER BY {sort_column} {sort_direction}

            LIMIT ? OFFSET ?
        """

        query_params = params + [
            page_size,
            offset,
        ]

        rows = conn.execute(
            query,
            query_params,
        ).fetchall()

    data = []

    for row in rows:

        item = row_to_dict(row)

        item["company_name"] = clean_company_name(
            item.get("company_name")
        )

        data.append(item)

    total_pages = (
        (total_count + page_size - 1) // page_size
        if total_count
        else 0
    )

    return {
        "count": len(data),
        "total_count": total_count,

        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
        },

        "filters": {
            "sector": sector,
            "sub_sector": sub_sector,
            "market_cap_category": market_cap_category,
            "search": search,
        },

        "sorting": {
            "sort_by": sort_by,
            "sort_order": (
                "desc"
                if sort_direction == "DESC"
                else "asc"
            ),
        },

        "data": data,
    }


# ============================================================
# COMPANY DETAIL
# ============================================================

@router.get("/{company_id}")
def get_company(company_id: str):

    company_id = company_id.strip().upper()

    with get_connection() as conn:

        company = conn.execute(
            """
            SELECT
                id,
                company_logo,
                company_name,
                chart_link,
                about_company,
                website,
                nse_profile,
                bse_profile,
                face_value,
                book_value,
                roce_percentage,
                roe_percentage,
                broad_sector,
                sub_sector,
                index_weight_pct,
                market_cap_category
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        kpi = conn.execute(
            """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    result = row_to_dict(company)

    result["company_name"] = clean_company_name(
        result.get("company_name")
    )

    result["latest_kpis"] = (
        row_to_dict(kpi)
        if kpi is not None
        else None
    )

    return result


# ============================================================
# GENERIC HISTORY FILTER
# ============================================================

def filter_history_by_year(
    rows: list[sqlite3.Row],
    from_year: Optional[int],
    to_year: Optional[int],
) -> list[dict[str, Any]]:

    filtered = []

    for row in rows:

        if not year_matches(
            row["year"],
            from_year,
            to_year,
        ):
            continue

        item = row_to_dict(row)

        item["year"] = normalize_year_for_response(
            item.get("year")
        )

        filtered.append(item)

    return filtered


# ============================================================
# PROFIT AND LOSS
# ============================================================

@router.get("/{company_id}/pl")
def get_profit_and_loss(
    company_id: str,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
):

    company_id = company_id.strip().upper()

    with get_connection() as conn:

        company = conn.execute(
            """
            SELECT company_name
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        rows = conn.execute(
            """
            SELECT *
            FROM profitandloss
            WHERE UPPER(company_id) = ?
            ORDER BY id ASC
            """,
            (company_id,),
        ).fetchall()

    history = filter_history_by_year(
        rows,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "company_name": clean_company_name(
            company["company_name"]
        ),
        "from_year": (
            str(from_year)
            if from_year is not None
            else None
        ),
        "to_year": (
            str(to_year)
            if to_year is not None
            else None
        ),
        "count": len(history),
        "history": history,
    }


# ============================================================
# BALANCE SHEET
# ============================================================

@router.get("/{company_id}/bs")
def get_balance_sheet(
    company_id: str,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
):

    company_id = company_id.strip().upper()

    with get_connection() as conn:

        company = conn.execute(
            """
            SELECT company_name
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        rows = conn.execute(
            """
            SELECT *
            FROM balancesheet
            WHERE UPPER(company_id) = ?
            ORDER BY id ASC
            """,
            (company_id,),
        ).fetchall()

    history = filter_history_by_year(
        rows,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "company_name": clean_company_name(
            company["company_name"]
        ),
        "from_year": (
            str(from_year)
            if from_year is not None
            else None
        ),
        "to_year": (
            str(to_year)
            if to_year is not None
            else None
        ),
        "count": len(history),
        "history": history,
    }


# ============================================================
# CASH FLOW
# ============================================================

@router.get("/{company_id}/cashflow")
def get_cashflow(
    company_id: str,
    from_year: Optional[int] = Query(None),
    to_year: Optional[int] = Query(None),
):

    company_id = company_id.strip().upper()

    with get_connection() as conn:

        company = conn.execute(
            """
            SELECT company_name
            FROM companies
            WHERE UPPER(id) = ?
            """,
            (company_id,),
        ).fetchone()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_id}' not found",
            )

        rows = conn.execute(
            """
            SELECT *
            FROM cashflow
            WHERE UPPER(company_id) = ?
            ORDER BY id ASC
            """,
            (company_id,),
        ).fetchall()

    history = filter_history_by_year(
        rows,
        from_year,
        to_year,
    )

    return {
        "company_id": company_id,
        "company_name": clean_company_name(
            company["company_name"]
        ),
        "from_year": (
            str(from_year)
            if from_year is not None
            else None
        ),
        "to_year": (
            str(to_year)
            if to_year is not None
            else None
        ),
        "count": len(history),
        "history": history,
    }