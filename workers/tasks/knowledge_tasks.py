import logging
import uuid
from typing import Any

from app.modules.knowledge.service import KnowledgeService
from workers.celery_app import celery_app
from workers.utils import run_coro_sync

logger = logging.getLogger("ai_prof.workers.knowledge")


@celery_app.task(bind=True, name="knowledge.index", max_retries=3)
def index_material_knowledge_task(
    self,
    user_id_str: str,
    project_id_str: str,
    material_id_str: str,
) -> dict[str, Any]:
    """
    Celery background worker task for chunking material pages, embedding generation,
    vector store upserting, and dynamic concept extraction.
    """
    logger.info(f"[Task {self.request.id}] Starting knowledge indexing for material_id={material_id_str}")

    u_id = uuid.UUID(user_id_str)
    p_id = uuid.UUID(project_id_str)
    m_id = uuid.UUID(material_id_str)

    service = KnowledgeService()

    try:
        chunk_count = run_coro_sync(service.index_material_knowledge(u_id, p_id, m_id))
        logger.info(
            f"[Task {self.request.id}] Knowledge indexing completed for material_id={material_id_str}. Chunks indexed: {chunk_count}"
        )
        return {
            "status": "completed",
            "material_id": material_id_str,
            "project_id": project_id_str,
            "chunks_indexed": chunk_count,
        }
    except Exception as exc:
        if self.request.retries < self.max_retries:
            countdown = 2 ** self.request.retries
            logger.warning(f"[Task {self.request.id}] Retrying knowledge indexing due to exception: {exc}")
            raise self.retry(exc=exc, countdown=countdown)

        logger.error(f"[Task {self.request.id}] Knowledge indexing failed for material_id={material_id_str}: {exc}")
        return {
            "status": "failed",
            "material_id": material_id_str,
            "error": str(exc),
        }
