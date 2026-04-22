from celery import Celery
from celery.schedules import crontab
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "buscacarros",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    beat_schedule={
        # Processa alertas a cada 30 minutos
        "process-alerts": {
            "task": "app.workers.tasks.process_alerts",
            "schedule": crontab(minute="*/30"),
        },
        # Limpa buscas antigas a cada dia às 3h
        "cleanup-old-searches": {
            "task": "app.workers.tasks.cleanup_old_searches",
            "schedule": crontab(hour=3, minute=0),
        },
        # Atualiza cache FIPE diariamente às 6h
        "refresh-fipe-cache": {
            "task": "app.workers.tasks.refresh_fipe_cache",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)
