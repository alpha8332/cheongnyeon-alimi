"""Central Celery application backed by Redis and PostgreSQL run state."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "cheongnyeon_alimi_collection",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=("app.worker.tasks",),
)

celery_app.conf.update(
    accept_content=("json",),
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": 1200},
    enable_utc=True,
    result_accept_content=("json",),
    task_acks_late=True,
    task_default_queue=settings.COLLECTION_QUEUE_NAME,
    task_ignore_result=True,
    task_annotations={
        "collection.collect_source": {
            "rate_limit": settings.COLLECTION_TASK_RATE_LIMIT,
        }
    },
    task_reject_on_worker_lost=True,
    task_serializer="json",
    timezone="Asia/Seoul",
    worker_prefetch_multiplier=1,
)

if settings.COLLECTION_SCHEDULE_ENABLED:
    celery_app.conf.beat_schedule = {
        "scheduled-policy-collection": {
            "task": "collection.enqueue_scheduled_source",
            "schedule": crontab(
                hour=settings.COLLECTION_SCHEDULE_CRON_HOUR,
                minute=settings.COLLECTION_SCHEDULE_CRON_MINUTE,
            ),
            "options": {"queue": settings.COLLECTION_QUEUE_NAME},
        }
    }
