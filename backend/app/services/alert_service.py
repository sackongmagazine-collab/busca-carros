"""
Serviço de alertas: dispara notificações quando novos anúncios
correspondem aos critérios configurados pelo usuário.
Executado pelo worker Celery a cada 30 minutos.
"""
import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.alert import Alert
from app.models.subscription import PlanTier
from app.schemas.search import SearchRequest, TransmissionEnum, FuelEnum
from app.services.search_orchestrator import SearchOrchestrator
from app.services.notification.email import send_alert_email, build_alert_email
from app.services.notification.whatsapp import send_whatsapp_alert
from app.services.notification.telegram import send_telegram_alert

logger = logging.getLogger(__name__)


class AlertService:
    async def process_all(self, db: AsyncSession):
        result = await db.execute(
            select(Alert).where(Alert.is_active == True).join(Alert.user)
        )
        alerts = result.scalars().all()
        logger.info(f"Processando {len(alerts)} alertas ativos")

        for alert in alerts:
            try:
                await self._process_alert(alert, db)
            except Exception as e:
                logger.error(f"Erro no alerta {alert.id}: {e}", exc_info=True)

    async def _process_alert(self, alert: Alert, db: AsyncSession):
        criteria = SearchRequest(
            model=alert.model,
            max_price=alert.max_price,
            location=alert.location,
            year_min=alert.year_min,
            year_max=alert.year_max,
            max_km=alert.max_km,
            transmission=TransmissionEnum(alert.transmission),
            fuel=FuelEnum(alert.fuel),
        )

        orchestrator = SearchOrchestrator()
        try:
            # Cria uma busca fantasma (sem persistência) para obter resultados
            from app.services.fipe_service import FipeService
            from app.services.mercadolivre_service import MercadoLivreService
            from app.services.webmotors_scraper import WebmotorsScraper

            fipe_svc = FipeService()
            ml_svc = MercadoLivreService()
            wm_svc = WebmotorsScraper()

            fipe_value, ml_results, wm_results = await asyncio.gather(
                fipe_svc.get_fipe_value(criteria.model),
                ml_svc.search(criteria),
                wm_svc.search(criteria),
                return_exceptions=True,
            )

            fipe_value = fipe_value if isinstance(fipe_value, float) else 85000.0
            all_listings = (ml_results if isinstance(ml_results, list) else []) + \
                           (wm_results if isinstance(wm_results, list) else [])

            # Filtra pelo threshold da FIPE
            notified_ids = set(alert.notified_listing_ids or [])
            new_listings = []
            for l in all_listings:
                listing_id = self._listing_id(l)
                if listing_id in notified_ids:
                    continue
                if fipe_value > 0 and alert.fipe_threshold_pct != 0:
                    diff_pct = ((l.price - fipe_value) / fipe_value) * 100
                    if diff_pct > alert.fipe_threshold_pct:
                        continue
                new_listings.append(l)
                notified_ids.add(listing_id)

            if not new_listings:
                logger.debug(f"Alerta {alert.id}: sem novidades")
                return

            logger.info(f"Alerta {alert.id}: {len(new_listings)} novo(s) resultado(s)")
            listings_dicts = [l.model_dump() for l in new_listings[:10]]
            criteria_dict = {"model": alert.model, "location": alert.location}

            # Envia por todos os canais configurados
            channels = alert.channels or []
            tasks = []
            if "email" in channels and alert.user.email:
                html = build_alert_email(listings_dicts, criteria_dict, fipe_value)
                tasks.append(send_alert_email(
                    alert.user.email,
                    f"🚗 {len(new_listings)} nova(s) oferta(s) de {alert.model}",
                    html,
                ))
            if "whatsapp" in channels and alert.whatsapp_number:
                tasks.append(send_whatsapp_alert(alert.whatsapp_number, listings_dicts, criteria_dict, fipe_value))
            if "telegram" in channels and alert.telegram_chat_id:
                tasks.append(send_telegram_alert(alert.telegram_chat_id, listings_dicts, criteria_dict, fipe_value))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Atualiza o alerta com IDs notificados
            await db.execute(
                update(Alert).where(Alert.id == alert.id).values(
                    last_triggered_at=datetime.now(timezone.utc),
                    notified_listing_ids=list(notified_ids),
                )
            )
            await db.commit()

            await asyncio.gather(fipe_svc.close(), ml_svc.close(), wm_svc.close())
        finally:
            await orchestrator.close()

    def _listing_id(self, listing) -> str:
        key = f"{listing.url or ''}{listing.price}{listing.km or 0}"
        import hashlib
        return hashlib.md5(key.encode()).hexdigest()[:12]
