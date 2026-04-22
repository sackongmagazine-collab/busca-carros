from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.alert import Alert
from app.models.subscription import PlanTier
from app.routers.auth import get_current_user_required
from app.config import get_settings

router = APIRouter(prefix="/alerts", tags=["alerts"])
settings = get_settings()

ALERT_LIMITS = {
    PlanTier.free.value: 0,
    PlanTier.hunter.value: settings.hunter_max_alerts,
    PlanTier.hunter_pro.value: settings.hunter_pro_max_alerts,
    PlanTier.dealer.value: settings.hunter_pro_max_alerts,
}


class AlertCreate(BaseModel):
    model: str
    max_price: float
    location: str
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    max_km: Optional[int] = None
    transmission: str = "indiferente"
    fuel: str = "indiferente"
    fipe_threshold_pct: float = 0.0
    channels: list[str] = ["email"]
    whatsapp_number: Optional[str] = None
    telegram_chat_id: Optional[str] = None


@router.get("")
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    result = await db.execute(select(Alert).where(Alert.user_id == current_user.id))
    alerts = result.scalars().all()
    return [_alert_dict(a) for a in alerts]


@router.post("", status_code=201)
async def create_alert(
    data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    plan = current_user.plan
    limit = ALERT_LIMITS.get(plan, 0)
    if limit == 0:
        raise HTTPException(
            status_code=403,
            detail="Alertas disponíveis apenas no plano Hunter ou superior. Faça upgrade em /pricing.",
        )

    result = await db.execute(select(Alert).where(Alert.user_id == current_user.id))
    existing = result.scalars().all()
    if len(existing) >= limit:
        raise HTTPException(status_code=403, detail=f"Limite de {limit} alertas atingido para o plano {plan}.")

    # Valida canais vs plano
    if "whatsapp" in data.channels or "telegram" in data.channels:
        if plan not in (PlanTier.hunter_pro.value, PlanTier.dealer.value):
            raise HTTPException(status_code=403, detail="WhatsApp/Telegram disponíveis apenas no plano Hunter Pro.")

    alert = Alert(
        user_id=current_user.id,
        model=data.model,
        max_price=data.max_price,
        location=data.location,
        year_min=data.year_min,
        year_max=data.year_max,
        max_km=data.max_km,
        transmission=data.transmission,
        fuel=data.fuel,
        fipe_threshold_pct=data.fipe_threshold_pct,
        channels=data.channels,
        whatsapp_number=data.whatsapp_number,
        telegram_chat_id=data.telegram_chat_id,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return _alert_dict(alert)


@router.patch("/{alert_id}/toggle")
async def toggle_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    alert = await _get_alert(alert_id, current_user.id, db)
    alert.is_active = not alert.is_active
    await db.commit()
    return {"id": alert.id, "is_active": alert.is_active}


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    await _get_alert(alert_id, current_user.id, db)
    await db.execute(delete(Alert).where(Alert.id == alert_id))
    await db.commit()


async def _get_alert(alert_id: int, user_id: int, db: AsyncSession) -> Alert:
    result = await db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == user_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado")
    return alert


def _alert_dict(a: Alert) -> dict:
    return {
        "id": a.id,
        "model": a.model,
        "max_price": a.max_price,
        "location": a.location,
        "year_min": a.year_min,
        "year_max": a.year_max,
        "max_km": a.max_km,
        "transmission": a.transmission,
        "fuel": a.fuel,
        "fipe_threshold_pct": a.fipe_threshold_pct,
        "channels": a.channels,
        "whatsapp_number": a.whatsapp_number,
        "telegram_chat_id": a.telegram_chat_id,
        "is_active": a.is_active,
        "last_triggered_at": a.last_triggered_at.isoformat() if a.last_triggered_at else None,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    }
