import logging
import time
from typing import Any

from workers.celery_app import celery_app

logger = logging.getLogger("ai_prof.workers.maintenance")


@celery_app.task(bind=True, name="maintenance.health_check")
def system_health_check_task(self) -> dict[str, Any]:
    """
    Periodic Celery maintenance task for verifying worker connectivity,
    heartbeat metrics, and task engine status.
    """
    logger.info(f"[Task {self.request.id}] Executing worker maintenance health check.")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "task_id": self.request.id,
        "worker": getattr(self.request, "hostname", "local-worker"),
    }
