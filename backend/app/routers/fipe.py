from fastapi import APIRouter
from app.services.fipe_service import FipeService

router = APIRouter(prefix="/fipe", tags=["fipe"])
_fipe = FipeService()


@router.get("/models")
async def model_suggestions(q: str = ""):
    if len(q) < 2:
        return []
    suggestions = await _fipe.get_model_suggestions(q)
    return suggestions
