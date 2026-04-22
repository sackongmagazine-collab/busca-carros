"""
WhatsApp via Evolution API (open-source, auto-hospedável).
Docs: https://doc.evolution-api.com
Alternativa cloud: Z-API, WPP Connect.
"""
import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_whatsapp_alert(phone: str, listings: list[dict], criteria: dict, fipe_value: float) -> bool:
    if not settings.evolution_api_url or not settings.evolution_api_key:
        logger.warning("Evolution API não configurada")
        return False

    try:
        message = _build_message(listings, criteria, fipe_value)
        url = f"{settings.evolution_api_url}/message/sendText/{settings.evolution_instance}"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={"apikey": settings.evolution_api_key, "Content-Type": "application/json"},
                json={"number": phone, "text": message},
                timeout=15.0,
            )
            resp.raise_for_status()
            logger.info(f"WhatsApp enviado para {phone}")
            return True
    except Exception as e:
        logger.error(f"Falha WhatsApp para {phone}: {e}")
        return False


def _build_message(listings: list[dict], criteria: dict, fipe_value: float) -> str:
    model = criteria.get("model", "")
    location = criteria.get("location", "")
    lines = [
        f"🚗 *Alerta Busca Carros*",
        f"_{len(listings)} nova(s) oferta(s) de {model} em {location}_",
        f"FIPE: R$ {fipe_value:,.0f}",
        "",
    ]
    for i, l in enumerate(listings[:3], 1):
        diff = ((l["price"] - fipe_value) / fipe_value) * 100
        sign = "🟢" if diff < -5 else "🟡" if diff <= 5 else "🔴"
        lines += [
            f"*{i}. {l.get('title', '')}*",
            f"💰 R$ {l['price']:,.0f} {sign} ({diff:+.1f}% FIPE)",
            f"📍 {l.get('location', '')} · {l.get('year', '—')} · {l.get('km', 0):,} km",
            f"🔗 {l.get('url', '')}",
            "",
        ]
    lines.append(f"Gerencie seus alertas: {settings.app_url}/alerts")
    return "\n".join(lines)
