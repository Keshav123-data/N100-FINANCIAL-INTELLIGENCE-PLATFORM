from fastapi import APIRouter

router = APIRouter()


@router.get("/sectors")
def sectors_placeholder():
    """
    Placeholder for sector endpoints.
    """

    return {
        "status": "ready",
        "message": "Sector API will be implemented on Day 40",
    }