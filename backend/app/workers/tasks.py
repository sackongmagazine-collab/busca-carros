import asyncio
import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper para rodar coroutines async dentro de tasks Celery síncronas."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.tasks.process_alerts", bind=True, max_retries=2)
def process_alerts(self):
    """Processa todos os alertas ativos e envia notificações."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.alert_service import AlertService
        async with AsyncSessionLocal() as db:
            service = AlertService()
            await service.process_all(db)

    try:
        run_async(_run())
        logger.info("Alertas processados com sucesso")
    except Exception as exc:
        logger.error(f"Falha no processo de alertas: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=120)


@celery_app.task(name="app.workers.tasks.cleanup_old_searches")
def cleanup_old_searches():
    """Remove buscas com mais de 30 dias para economizar espaço."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.search import Search
        from sqlalchemy import delete
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                delete(Search).where(Search.created_at < cutoff)
            )
            await db.commit()
            logger.info(f"Removidas {result.rowcount} buscas antigas")

    run_async(_run())


@celery_app.task(name="app.workers.tasks.refresh_fipe_cache")
def refresh_fipe_cache():
    """Pré-aquece o cache FIPE para os modelos mais buscados."""
    async def _run():
        from app.services.fipe_service import FipeService
        from app.database import AsyncSessionLocal
        from app.models.search import Search
        from sqlalchemy import select, func

        async with AsyncSessionLocal() as db:
            # Pega os 20 modelos mais buscados nos últimos 7 dias
            result = await db.execute(
                select(Search.model, func.count(Search.id).label("cnt"))
                .group_by(Search.model)
                .order_by(func.count(Search.id).desc())
                .limit(20)
            )
            top_models = [row[0] for row in result]

        fipe = FipeService()
        for model in top_models:
            try:
                value = await fipe.get_fipe_value(model)
                logger.debug(f"FIPE cache: {model} = R$ {value:,.0f}")
            except Exception:
                pass
        await fipe.close()

    run_async(_run())
