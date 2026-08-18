from fastapi import APIRouter

router = APIRouter()


@router.get("/screener")
def screener_placeholder():
    """
    Placeholder for screener endpoint.
    """

    return {
        "status": "ready",
        "message": "Screener API will be implemented on Day 40",
    }