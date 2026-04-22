from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date, timezone
from typing import Optional

from app.database import get_db
from app.models.search import Search, SearchStatus
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_orchestrator import SearchOrchestrator
from app.routers.auth import get_current_user
from app.config import get_settings

router = APIRouter(prefix="/search", tags=["search"])
settings = get_settings()


async def check_rate_limit(user: Optional[User], db: AsyncSession):
    if user and user.is_premium:
        return
    user_id = user.id if user else None
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    query = select(func.count()).select_from(Search).where(Search.created_at >= today_start)
    if user_id:
        query = query.where(Search.user_id == user_id)
    count = await db.scalar(query)
    if count >= settings.free_searches_per_day:
        raise HTTPException(
            status_code=429,
            detail=f"Limite de {settings.free_searches_per_day} buscas/dia atingido. Assine o Premium para buscas ilimitadas.",
        )


@router.post("", response_model=dict, status_code=202)
async def create_search(
    criteria: SearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    await check_rate_limit(current_user, db)

    search = Search(
        user_id=current_user.id if current_user else None,
        model=criteria.model,
        max_price=criteria.max_price,
        location=criteria.location,
        year_min=criteria.year_min,
        year_max=criteria.year_max,
        max_km=criteria.max_km,
        transmission=criteria.transmission.value,
        fuel=criteria.fuel.value,
        status=SearchStatus.pending,
    )
    db.add(search)
    await db.commit()
    await db.refresh(search)

    background_tasks.add_task(_run_search, search.id, criteria)
    return {"search_id": search.id, "status": "pending"}


async def _run_search(search_id: int, criteria: SearchRequest):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        orchestrator = SearchOrchestrator()
        try:
            await orchestrator.run(search_id, criteria, db)
        finally:
            await orchestrator.close()


@router.get("/history/me", response_model=list[dict])
async def my_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Login necessário")
    result = await db.execute(
        select(Search)
        .where(Search.user_id == current_user.id)
        .order_by(Search.created_at.desc())
        .limit(20)
    )
    searches = result.scalars().all()
    return [
        {
            "id": s.id,
            "model": s.model,
            "location": s.location,
            "max_price": s.max_price,
            "status": s.status.value,
            "total_found": s.total_found,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in searches
    ]


@router.get("/{search_id}", response_model=SearchResponse)
async def get_search_results(
    search_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Search).where(Search.id == search_id))
    search = result.scalar_one_or_none()
    if not search:
        raise HTTPException(status_code=404, detail="Busca não encontrada")

    if search.status in (SearchStatus.pending, SearchStatus.running):
        return SearchResponse(search_id=search_id, status=search.status.value)

    if search.status == SearchStatus.failed:
        raise HTTPException(status_code=500, detail="A busca falhou. Tente novamente.")

    results = search.results or {}
    return SearchResponse(**{**results, "search_id": search_id, "status": "completed"})
