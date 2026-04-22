"""
Dashboard administrativo.
Protegido por header X-Admin-Secret.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from typing import Optional
from datetime import datetime, timedelta, date

from app.database import get_db
from app.models.user import User, UserRole
from app.models.search import Search, SearchStatus
from app.models.subscription import Subscription, PlanTier
from app.models.fraud_report import FraudReport
from app.models.dealer import Dealer, DealerListing
from app.config import get_settings

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


def verify_admin(x_admin_secret: Optional[str] = Header(None)):
    if not x_admin_secret or x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=403, detail="Acesso negado")


# ─── Métricas gerais ──────────────────────────────────────────────────────────

@router.get("/metrics", dependencies=[Depends(verify_admin)])
async def get_metrics(db: AsyncSession = Depends(get_db)):
    today = datetime.combine(date.today(), datetime.min.time())
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Usuários
    total_users = await db.scalar(select(func.count(User.id)))
    new_users_today = await db.scalar(select(func.count(User.id)).where(User.created_at >= today))
    new_users_week = await db.scalar(select(func.count(User.id)).where(User.created_at >= week_ago))

    # Assinaturas por plano
    plan_counts = {}
    for plan in PlanTier:
        count = await db.scalar(
            select(func.count(Subscription.id)).where(Subscription.plan == plan)
        )
        plan_counts[plan.value] = count or 0
    plan_counts["free"] = (total_users or 0) - sum(plan_counts.values())

    # Receita estimada (mensal)
    from app.config import get_settings as gs
    s = gs()
    revenue_monthly = (
        (plan_counts.get("hunter", 0) * s.price_hunter) +
        (plan_counts.get("hunter_pro", 0) * s.price_hunter_pro) +
        (plan_counts.get("dealer", 0) * s.price_dealer)
    )

    # Buscas
    searches_today = await db.scalar(select(func.count(Search.id)).where(Search.created_at >= today))
    searches_week = await db.scalar(select(func.count(Search.id)).where(Search.created_at >= week_ago))
    searches_month = await db.scalar(select(func.count(Search.id)).where(Search.created_at >= month_ago))

    # Top modelos buscados (últimos 7 dias)
    top_models_result = await db.execute(
        select(Search.model, func.count(Search.id).label("cnt"))
        .where(Search.created_at >= week_ago)
        .group_by(Search.model)
        .order_by(func.count(Search.id).desc())
        .limit(10)
    )
    top_models = [{"model": row[0], "count": row[1]} for row in top_models_result]

    # Fraudes
    fraud_pending = await db.scalar(
        select(func.count(FraudReport.id)).where(FraudReport.resolved == False)
    )

    # Dealers
    total_dealers = await db.scalar(select(func.count(Dealer.id)))
    active_listings = await db.scalar(
        select(func.count(DealerListing.id)).where(DealerListing.is_active == True)
    )

    return {
        "users": {
            "total": total_users,
            "new_today": new_users_today,
            "new_week": new_users_week,
            "by_plan": plan_counts,
        },
        "revenue": {
            "mrr_estimated": round(revenue_monthly, 2),
            "arr_estimated": round(revenue_monthly * 12, 2),
        },
        "searches": {
            "today": searches_today,
            "this_week": searches_week,
            "this_month": searches_month,
        },
        "top_models": top_models,
        "fraud": {"pending_reviews": fraud_pending},
        "dealers": {"total": total_dealers, "active_listings": active_listings},
    }


# ─── Gestão de usuários ───────────────────────────────────────────────────────

@router.get("/users", dependencies=[Depends(verify_admin)])
async def list_users(
    page: int = 1,
    limit: int = 50,
    plan: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(User).order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "plan": u.plan,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.patch("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def update_user(user_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    allowed = {"is_active", "role"}
    values = {k: v for k, v in data.items() if k in allowed}
    if not values:
        raise HTTPException(status_code=400, detail="Nenhum campo válido para atualizar")
    await db.execute(update(User).where(User.id == user_id).values(**values))
    await db.commit()
    return {"updated": True}


# ─── Fila antifraude ──────────────────────────────────────────────────────────

@router.get("/fraud-queue", dependencies=[Depends(verify_admin)])
async def fraud_queue(
    resolved: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FraudReport)
        .where(FraudReport.resolved == resolved)
        .order_by(FraudReport.fraud_score.desc())
        .limit(limit)
    )
    reports = result.scalars().all()
    return [
        {
            "id": r.id,
            "listing_url": r.listing_url,
            "listing_title": r.listing_title,
            "listing_price": r.listing_price,
            "fipe_value": r.fipe_value,
            "fraud_score": r.fraud_score,
            "risk_level": r.risk_level,
            "flags": r.flags,
            "ai_analysis": r.ai_analysis,
            "resolved": r.resolved,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in reports
    ]


@router.patch("/fraud-queue/{report_id}/resolve", dependencies=[Depends(verify_admin)])
async def resolve_fraud_report(report_id: int, data: dict, db: AsyncSession = Depends(get_db)):
    await db.execute(
        update(FraudReport).where(FraudReport.id == report_id).values(
            resolved=True, admin_notes=data.get("notes", "")
        )
    )
    await db.commit()
    return {"resolved": True}


# ─── Lojistas ─────────────────────────────────────────────────────────────────

@router.patch("/dealers/{dealer_id}/verify", dependencies=[Depends(verify_admin)])
async def verify_dealer(dealer_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(update(Dealer).where(Dealer.id == dealer_id).values(is_verified=True))
    await db.commit()
    return {"verified": True}
