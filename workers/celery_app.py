import logging
import os
from celery import Celery
from workers.config import worker_settings

logger = logging.getLogger("ai_prof.workers")

broker_url = worker_settings.CELERY_BROKER_URL
result_backend = worker_settings.CELERY_RESULT_BACKEND

celery_app = Celery(
    "ai_prof_workers",
    broker=broker_url,
    backend=result_backend,
    include=[
        "workers.tasks.material_tasks",
        "workers.tasks.knowledge_tasks",
        "workers.tasks.assessment_tasks",
        "workers.tasks.mastery_tasks",
        "workers.tasks.recommendation_tasks",
        "workers.tasks.maintenance_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=worker_settings.TIMEZONE,
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    result_expires=3600,
    task_always_eager=worker_settings.CELERY_TASK_ALWAYS_EAGER,
    task_eager_propagates=worker_settings.CELERY_TASK_ALWAYS_EAGER,
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
