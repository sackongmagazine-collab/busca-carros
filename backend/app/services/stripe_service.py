"""
Gerencia assinaturas via Stripe.
Suporta criação de checkout, portal do cliente e webhook de eventos.
"""
import stripe
import logging
from typing import Optional
from app.config import get_settings
from app.models.subscription import PlanTier

logger = logging.getLogger(__name__)
settings = get_settings()

stripe.api_key = settings.stripe_secret_key

PLAN_PRICE_MAP = {
    PlanTier.hunter: settings.stripe_price_hunter,
    PlanTier.hunter_pro: settings.stripe_price_hunter_pro,
    PlanTier.dealer: settings.stripe_price_dealer,
}


async def create_checkout_session(user_id: int, user_email: str, plan: PlanTier) -> Optional[str]:
    """Cria sessão de checkout do Stripe. Retorna a URL."""
    price_id = PLAN_PRICE_MAP.get(plan)
    if not price_id:
        logger.error(f"Stripe price_id não configurado para {plan}")
        return None
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user_email,
            line_items=[{"price": price_id, "quantity": 1}],
            metadata={"user_id": str(user_id), "plan": plan.value},
            success_url=f"{settings.app_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.app_url}/pricing",
            allow_promotion_codes=True,
        )
        return session.url
    except stripe.StripeError as e:
        logger.error(f"Stripe checkout error: {e}")
        return None


async def create_customer_portal(stripe_customer_id: str) -> Optional[str]:
    """Gera URL do portal para o cliente gerenciar/cancelar assinatura."""
    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=f"{settings.app_url}/dashboard",
        )
        return session.url
    except stripe.StripeError as e:
        logger.error(f"Portal error: {e}")
        return None


def verify_webhook(payload: bytes, sig_header: str) -> Optional[stripe.Event]:
    """Verifica e retorna o evento do webhook Stripe."""
    try:
        return stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except (stripe.SignatureVerificationError, ValueError) as e:
        logger.warning(f"Webhook inválido: {e}")
        return None


def get_plan_from_price_id(price_id: str) -> Optional[PlanTier]:
    for plan, pid in PLAN_PRICE_MAP.items():
        if pid == price_id:
            return plan
    return None
