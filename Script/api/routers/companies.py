from fastapi import APIRouter

router = APIRouter()


@router.get("/companies")
def companies_placeholder():
    """
    Placeholder for company endpoints.
    """

    return {
        "status": "ready",
        "message": "Companies API will be implemented on Day 39",
    }