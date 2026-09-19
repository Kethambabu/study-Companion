import os
import sys
import uuid
from pathlib import Path

# Add project root to python path for workers module discovery
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import fitz  # PyMuPDF
import pytest
from httpx import AsyncClient

from app.modules.materials.service import _IN_MEMORY_MATERIALS, _IN_MEMORY_JOBS, _IN_MEMORY_PAGES
from workers.celery_app import celery_app
from workers.tasks.material_tasks import process_material_task
from workers.tasks.knowledge_tasks import index_material_knowledge_task
from workers.tasks.assessment_tasks import evaluate_quiz_submission_task
from workers.tasks.mastery_tasks import update_concept_mastery_task
from workers.tasks.recommendation_tasks import generate_recommendations_task
from workers.tasks.maintenance_tasks import system_health_check_task

# Enable eager execution for fast, deterministic unit test runs without requiring Redis daemon
celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True


def create_sample_pdf_bytes(title: str = "Test PDF", body: str = "Sample content") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"{title}\n{body}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_celery_app_configuration():
    """Verifies Celery application instance configuration and task registration."""
    assert celery_app.main == "ai_prof_workers"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.timezone == "UTC"

    registered_tasks = set(celery_app.tasks.keys())
    assert "material.process" in registered_tasks
    assert "knowledge.index" in registered_tasks
    assert "assessment.evaluate_quiz" in registered_tasks
    assert "mastery.update" in registered_tasks
    assert "recommendation.generate" in registered_tasks
    assert "maintenance.health_check" in registered_tasks


def test_maintenance_health_check_task():
    """Verifies execution of worker maintenance health check task."""
    result = system_health_check_task.apply()
    assert result.successful()
    res_data = result.result
    assert res_data["status"] == "healthy"
    assert "timestamp" in res_data


def test_material_processing_task_execution():
    """Tests real background document extraction worker task."""
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    mat_id = uuid.uuid4()

    # Seed in-memory material record
    from app.modules.materials.models import Material
    from datetime import datetime, UTC

    now = datetime.now(UTC)
    pdf_bytes = create_sample_pdf_bytes("Worker Test", "Content for Celery processing")
    
    # Save file to storage
    from app.modules.materials.storage import SupabaseStorageService
    import asyncio
    storage = SupabaseStorageService()
    storage_path, checksum = asyncio.run(
        storage.save_material_file(space_id=uuid.uuid4(), project_id=project_id, filename="worker_test.pdf", content=pdf_bytes)
    )

    mat = Material(
        id=mat_id,
        project_id=project_id,
        owner_id=user_id,
        filename="worker_test.pdf",
        content_type="application/pdf",
        storage_path=storage_path,
        file_size=len(pdf_bytes),
        checksum=checksum,
        status="queued",
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    _IN_MEMORY_MATERIALS[str(mat_id)] = mat

    # Execute task synchronously using apply()
    task_res = process_material_task.apply(kwargs={
        "material_id_str": str(mat_id),
        "user_id_str": str(user_id),
        "project_id_str": str(project_id),
    })

    assert task_res.successful()
    res = task_res.result
    assert res["status"] == "completed"
    assert res["material_id"] == str(mat_id)

    # Verify material state updated to ready
    updated_mat = _IN_MEMORY_MATERIALS[str(mat_id)]
    assert updated_mat.status == "ready"
    assert len(_IN_MEMORY_PAGES.get(str(mat_id), [])) >= 1


def test_material_task_idempotency_duplicate_execution():
    """Verifies that running material processing twice does not produce duplicate page records."""
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    mat_id = uuid.uuid4()

    from app.modules.materials.models import Material
    from datetime import datetime, UTC
    now = datetime.now(UTC)
    pdf_bytes = create_sample_pdf_bytes("Idempotency Test", "Page content")

    from app.modules.materials.storage import SupabaseStorageService
    import asyncio
    storage = SupabaseStorageService()
    storage_path, checksum = asyncio.run(
        storage.save_material_file(space_id=uuid.uuid4(), project_id=project_id, filename="idempotent.pdf", content=pdf_bytes)
    )

    mat = Material(
        id=mat_id,
        project_id=project_id,
        owner_id=user_id,
        filename="idempotent.pdf",
        content_type="application/pdf",
        storage_path=storage_path,
        file_size=len(pdf_bytes),
        checksum=checksum,
        status="queued",
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    _IN_MEMORY_MATERIALS[str(mat_id)] = mat

    # First execution
    res1 = process_material_task.apply(kwargs={
        "material_id_str": str(mat_id),
        "user_id_str": str(user_id),
        "project_id_str": str(project_id),
    }).result
    count1 = len(_IN_MEMORY_PAGES.get(str(mat_id), []))

    # Second duplicate execution
    res2 = process_material_task.apply(kwargs={
        "material_id_str": str(mat_id),
        "user_id_str": str(user_id),
        "project_id_str": str(project_id),
    }).result
    count2 = len(_IN_MEMORY_PAGES.get(str(mat_id), []))

    assert res1["status"] == "completed"
    assert res2["status"] == "completed"
    assert count1 == count2, "Page count must remain identical on duplicate execution"


def test_material_task_project_isolation():
    """Verifies worker rejects execution if resource ownership/project check fails."""
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    other_project_id = uuid.uuid4()
    mat_id = uuid.uuid4()

    from app.modules.materials.models import Material
    from datetime import datetime, UTC
    now = datetime.now(UTC)

    mat = Material(
        id=mat_id,
        project_id=project_id,
        owner_id=user_id,
        filename="isolation.pdf",
        content_type="application/pdf",
        storage_path="some/path",
        file_size=100,
        checksum="hash",
        status="queued",
        attempt_count=0,
        created_at=now,
        updated_at=now,
    )
    _IN_MEMORY_MATERIALS[str(mat_id)] = mat

    res = process_material_task.apply(kwargs={
        "material_id_str": str(mat_id),
        "user_id_str": str(user_id),
        "project_id_str": str(other_project_id),  # Mismatched project
    }).result

    assert res["status"] == "failed"
    assert "Access denied" in res["error"]


def test_nonexistent_material_task_failure():
    """Verifies handling of non-existent material ID without infinite retry loop."""
    fake_id = str(uuid.uuid4())
    res = process_material_task.apply(kwargs={
        "material_id_str": fake_id,
        "user_id_str": str(uuid.uuid4()),
        "project_id_str": str(uuid.uuid4()),
    }).result

    assert res["status"] == "failed"
    assert res["error"] == "Material not found"


@pytest.mark.asyncio
async def test_fastapi_material_upload_triggers_queued_job(async_client: AsyncClient):
    """Verifies FastAPI upload endpoint enqueues job and returns queued status asynchronously."""
    suffix = uuid.uuid4().hex[:8]
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": f"worker_learner_{suffix}@example.com", "password": "Password123!", "full_name": "Worker Learner"},
    )
    assert u_resp.status_code == 201
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp_resp = await async_client.post(
        "/api/v1/spaces",
        json={"name": f"Worker Space {suffix}", "slug": f"worker-space-{suffix}"},
        headers=headers,
    )
    space_id = sp_resp.json()["data"]["id"]

    pj_resp = await async_client.post(
        "/api/v1/projects",
        json={"space_id": space_id, "name": "Async Worker Project"},
        headers=headers,
    )
    project_id = pj_resp.json()["data"]["id"]

    pdf_bytes = create_sample_pdf_bytes("Async PDF", "FastAPI enqueue test")
    mat_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/materials",
        files={"file": ("async_doc.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    assert mat_resp.status_code == 201
    mat_data = mat_resp.json()["data"]
    assert mat_data["status"] in ("queued", "ready", "processing")
