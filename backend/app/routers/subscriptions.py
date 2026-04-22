from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.database import get_db
from app.models.subscription import Subscription, PlanTier, SubscriptionStatus
from app.models.dealer import Dealer
from app.routers.auth import get_current_user_required
from app.services.stripe_service import (
    create_checkout_session, create_customer_portal,
    verify_webhook, get_plan_from_price_id,
)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class CheckoutRequest(BaseModel):
    plan: str  # hunter / hunter_pro / dealer


@router.post("/checkout")
async def create_checkout(
    data: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    try:
        plan = PlanTier(data.plan)
    except ValueError:
        raise HTTPException(status_code=400, detail="Plano inválido")

    url = await create_checkout_session(current_user.id, current_user.email, plan)
    if not url:
        raise HTTPException(status_code=500, detail="Erro ao criar sessão de pagamento. Verifique a configuração do Stripe.")
    return {"checkout_url": url}


@router.post("/portal")
async def customer_portal(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_required),
):
    sub = current_user.subscription
    if not sub or not sub.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura ativa encontrada")
    url = await create_customer_portal(sub.stripe_customer_id)
    if not url:
        raise HTTPException(status_code=500, detail="Erro ao acessar portal do cliente")
    return {"portal_url": url}


@router.get("/me")
async def my_subscription(current_user=Depends(get_current_user_required)):
    sub = current_user.subscription
    if not sub:
        return {"plan": "free", "status": "active"}
    return {
        "plan": sub.plan.value,
        "status": sub.status.value,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "searches_this_period": sub.searches_this_period,
    }


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
):
    payload = await request.body()
    event = verify_webhook(payload, stripe_signature or "")
    if not event:
        raise HTTPException(status_code=400, detail="Assinatura de webhook inválida")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data, db)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data, db)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(data, db)

    return {"received": True}


async def _handle_checkout_completed(session: dict, db: AsyncSession):
    user_id = int(session.get("metadata", {}).get("user_id", 0))
    plan_str = session.get("metadata", {}).get("plan", "free")
    stripe_sub_id = session.get("subscription")
    stripe_customer_id = session.get("customer")

    if not user_id:
        return

    try:
        plan = PlanTier(plan_str)
    except ValueError:
        return

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    sub = result.scalar_one_or_none()

    if sub:
        sub.plan = plan
        sub.status = SubscriptionStatus.active
        sub.stripe_subscription_id = stripe_sub_id
        sub.stripe_customer_id = stripe_customer_id
    else:
        sub = Subscription(
            user_id=user_id,
            plan=plan,
            status=SubscriptionStatus.active,
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=stripe_customer_id,
        )
        db.add(sub)

    # Se virou dealer, cria perfil de lojista (pode completar depois)
    if plan == PlanTier.dealer:
        existing = await db.execute(select(Dealer).where(Dealer.user_id == user_id))
        if not existing.scalar_one_or_none():
            db.add(Dealer(user_id=user_id, company_name="A preencher"))

    await db.commit()


async def _handle_subscription_updated(stripe_sub: dict, db: AsyncSession):
    stripe_sub_id = stripe_sub.get("id")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return

    status_map = {
        "active": SubscriptionStatus.active,
        "past_due": SubscriptionStatus.past_due,
        "canceled": SubscriptionStatus.canceled,
        "trialing": SubscriptionStatus.trialing,
    }
    sub.status = status_map.get(stripe_sub.get("status"), SubscriptionStatus.active)

    items = stripe_sub.get("items", {}).get("data", [])
    if items:
        price_id = items[0].get("price", {}).get("id")
        plan = get_plan_from_price_id(price_id)
        if plan:
            sub.plan = plan
            sub.stripe_price_id = price_id

    period_end = stripe_sub.get("current_period_end")
    if period_end:
        sub.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

    await db.commit()


async def _handle_subscription_deleted(stripe_sub: dict, db: AsyncSession):
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub.get("id"))
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.plan = PlanTier.free
        sub.status = SubscriptionStatus.canceled
        sub.canceled_at = datetime.now(timezone.utc)
        await db.commit()


async def _handle_payment_failed(invoice: dict, db: AsyncSession):
    stripe_customer_id = invoice.get("customer")
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == stripe_customer_id)
    )
    sub = result.scalar_one_or_none()
    if sub:
        sub.status = SubscriptionStatus.past_due
        await db.commit()
