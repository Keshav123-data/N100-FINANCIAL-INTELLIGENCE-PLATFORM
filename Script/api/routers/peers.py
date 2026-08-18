from fastapi import APIRouter

router = APIRouter()


@router.get("/peers/{group_name}")
def peers_placeholder(group_name: str):
    """
    Placeholder for peer endpoints.
    """

    return {
        "status": "ready",
        "group_name": group_name,
        "message": "Peer API will be implemented on Day 40",
    }