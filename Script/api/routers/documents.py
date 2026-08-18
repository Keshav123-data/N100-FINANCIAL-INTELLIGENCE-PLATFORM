from fastapi import APIRouter

router = APIRouter()


@router.get("/documents")
def documents_placeholder():
    """
    Placeholder for document endpoints.
    """

    return {
        "status": "ready",
        "message": "Documents API will be implemented on Day 40",
    }