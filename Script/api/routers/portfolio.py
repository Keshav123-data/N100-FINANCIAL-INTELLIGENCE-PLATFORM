from fastapi import APIRouter

router = APIRouter()


@router.get("/portfolio/stats")
def portfolio_placeholder():
    """
    Placeholder for portfolio statistics endpoint.
    """

    return {
        "status": "ready",
        "message": "Portfolio API will be implemented on Day 40",
    }