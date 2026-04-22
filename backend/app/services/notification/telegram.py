import httpx
import logging
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TG_BASE = "https://api.telegram.org"


async def send_telegram_alert(chat_id: str, listings: list[dict], criteria: dict, fipe_value: float) -> bool:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN não configurado")
        return False
    try:
        text = _build_message(listings, criteria, fipe_value)
        url = f"{TG_BASE}/bot{settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True},
                timeout=10.0,
            )
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Falha Telegram para {chat_id}: {e}")
        return False


def _build_message(listings: list[dict], criteria: dict, fipe_value: float) -> str:
    model = criteria.get("model", "")
    location = criteria.get("location", "")
    lines = [
        f"🚗 *Alerta Busca Carros*",
        f"_{len(listings)} nova(s) oferta(s): {model} em {location}_",
        f"📊 FIPE: R$ {fipe_value:,.0f}\n",
    ]
    for i, l in enumerate(listings[:5], 1):
        diff = ((l["price"] - fipe_value) / fipe_value) * 100
        emoji = "🟢" if diff < -5 else "🟡" if diff <= 5 else "🔴"
        lines += [
            f"*#{i} {l.get('title','')}*",
            f"💰 R$ {l['price']:,.0f} {emoji} `{diff:+.1f}%`",
            f"📍 {l.get('location','')} | {l.get('year','—')} | {l.get('km',0):,} km",
            f"[Ver anúncio]({l.get('url','')})\n",
        ]
    lines.append(f"[Gerenciar alertas]({settings.app_url}/alerts)")
    return "\n".join(lines)
