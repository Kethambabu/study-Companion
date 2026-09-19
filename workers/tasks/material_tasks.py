import logging
import uuid
from typing import Any

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.materials.service import (
    MaterialsService,
    _IN_MEMORY_JOBS,
    _IN_MEMORY_MATERIALS,
    _IN_MEMORY_PAGES,
)
from workers.celery_app import celery_app
from workers.utils import run_coro_sync

logger = logging.getLogger("ai_prof.workers.materials")


class NonRetryableError(Exception):
    """Exception indicating permanent processing failure that should not be retried."""
    pass


@celery_app.task(bind=True, name="material.process", max_retries=3)
def process_material_task(
    self,
    material_id_str: str,
    user_id_str: str | None = None,
    project_id_str: str | None = None,
) -> dict[str, Any]:
    """
    Celery background worker task for processing material document extraction.
    Performs real document extraction, page extraction, job status tracking,
    retry backoff for transient errors, and permanent failure marking.
    """
    logger.info(f"[Task {self.request.id}] Starting material processing for material_id={material_id_str}")

    mat_id = uuid.UUID(material_id_str)
    service = MaterialsService()

    # 1. Verify material existence
    mat = _IN_MEMORY_MATERIALS.get(str(mat_id))
    if not mat:
        logger.error(f"[Task {self.request.id}] Permanent failure: Material {material_id_str} not found.")
        return {"status": "failed", "material_id": material_id_str, "error": "Material not found"}

    # 2. Project isolation ownership verification
    if project_id_str and str(mat.project_id) != project_id_str:
        logger.error(
            f"[Task {self.request.id}] Security violation: Material {material_id_str} does not belong to project {project_id_str}."
        )
        return {"status": "failed", "material_id": material_id_str, "error": "Access denied for target project"}

    try:
        # Run process job safely using run_coro_sync
        processed_mat = run_coro_sync(service.process_material_job(mat_id))
        
        if processed_mat.status == "failed":
            error_msg = processed_mat.last_error or "Extraction failed"
            # Non-retryable error classification (invalid format, unreadable file)
            if any(term in error_msg.lower() for term in ["corrupt", "invalid", "unsupported", "permission"]):
                logger.warning(f"[Task {self.request.id}] Non-retryable failure: {error_msg}")
                return {
                    "status": "failed",
                    "material_id": material_id_str,
                    "error": error_msg,
                    "attempt": self.request.retries + 1,
                }
            else:
                # Transient error -> retry with exponential backoff
                countdown = 2 ** self.request.retries
                logger.warning(f"[Task {self.request.id}] Transient error: {error_msg}. Retrying in {countdown}s...")
                raise self.retry(exc=RuntimeError(error_msg), countdown=countdown)

        pages = _IN_MEMORY_PAGES.get(str(mat_id), [])
        logger.info(f"[Task {self.request.id}] Successfully processed material_id={material_id_str} with {len(pages)} pages")
        return {
            "status": "completed",
            "material_id": material_id_str,
            "page_count": len(pages),
            "attempt": self.request.retries + 1,
        }

    except Exception as exc:
        if "retry" in str(type(exc)).lower():
            raise exc
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(f"[Task {self.request.id}] Retrying due to exception: {exc} in {countdown}s")
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(f"[Task {self.request.id}] Max retries exceeded for material_id={material_id_str}: {exc}")
        return {"status": "failed", "material_id": material_id_str, "error": str(exc)}
