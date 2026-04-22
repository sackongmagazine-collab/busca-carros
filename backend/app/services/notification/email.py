import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

RESEND_API = "https://api.resend.com/emails"


async def send_alert_email(to: str, subject: str, html_body: str) -> bool:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY não configurada — email não enviado")
        return False
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                RESEND_API,
                headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
                json={"from": settings.email_from, "to": [to], "subject": subject, "html": html_body},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Falha ao enviar email para {to}: {e}")
        return False


def build_alert_email(listings: list[dict], criteria: dict, fipe_value: float) -> str:
    items_html = ""
    for l in listings[:5]:
        diff = ((l["price"] - fipe_value) / fipe_value) * 100
        badge_color = "#16a34a" if diff < 0 else "#dc2626"
        items_html += f"""
        <div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;">
            <div style="font-size:16px;font-weight:bold;color:#111827;">{l.get("title","")}</div>
            <div style="font-size:22px;font-weight:900;color:#1d4ed8;margin:8px 0;">
                R$ {l["price"]:,.0f}
                <span style="font-size:13px;color:{badge_color};font-weight:600;margin-left:8px;">
                    {diff:+.1f}% vs FIPE
                </span>
            </div>
            <div style="font-size:13px;color:#6b7280;">
                {l.get("year","—")} · {l.get("km","—"):,} km · {l.get("location","")}
            </div>
            <a href="{l.get("url","#")}" style="display:inline-block;margin-top:10px;padding:8px 16px;
               background:#2563eb;color:#fff;text-decoration:none;border-radius:8px;font-size:13px;">
                Ver anúncio →
            </a>
        </div>"""

    return f"""
    <div style="font-family:-apple-system,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
        <div style="background:#1d4ed8;color:#fff;padding:20px 24px;border-radius:12px 12px 0 0;">
            <h1 style="margin:0;font-size:20px;">🚗 Alerta Busca Carros</h1>
            <p style="margin:4px 0 0;opacity:0.8;font-size:14px;">
                {len(listings)} nova(s) oferta(s) de <strong>{criteria.get("model","")}</strong>
                em {criteria.get("location","")}
            </p>
        </div>
        <div style="background:#f9fafb;padding:20px 24px;border-radius:0 0 12px 12px;">
            <p style="color:#374151;font-size:14px;">
                FIPE de referência: <strong>R$ {fipe_value:,.0f}</strong>
            </p>
            {items_html}
            <p style="font-size:12px;color:#9ca3af;margin-top:16px;">
                Você recebeu este alerta porque configurou uma busca no Busca Carros.
                <a href="{settings.app_url}/alerts" style="color:#2563eb;">Gerenciar alertas</a>
            </p>
        </div>
    </div>"""
