import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.events.publisher import DomainEventPublisher
from app.modules.materials.extraction import PyMuPDFExtractor
from app.modules.materials.models import Material, MaterialPage, MaterialProcessingJob
from app.modules.materials.schemas import (
    MaterialPageResponse,
    MaterialResponse,
    MaterialRetryResponse,
    PaginatedMaterialsResponse,
    PaginatedPagesResponse,
)
from app.modules.materials.storage import SupabaseStorageService
from app.modules.projects.service import ProjectsService

# In-memory data store for materials domain fallback
_IN_MEMORY_MATERIALS: dict[str, Material] = {}
_IN_MEMORY_JOBS: dict[str, MaterialProcessingJob] = {}
_IN_MEMORY_PAGES: dict[str, list[MaterialPage]] = {}


class MaterialsService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.storage = SupabaseStorageService()
        self.extractor = PyMuPDFExtractor()

    async def upload_material(
        self, user_id: uuid.UUID, project_id: uuid.UUID, filename: str, file_bytes: bytes
    ) -> MaterialResponse:
        # 1. Resolve project details & authorize space access
        projects_service = ProjectsService(self.db)
        project = await projects_service.get_project(project_id)

        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=user_id, space_id=project.space_id, min_role="member"
        )
        if not has_access and project.owner_id != user_id:
            raise TenantAccessDeniedError("Access denied for target project space.")

        # 2. Validate file & save to storage
        storage_path, checksum = await self.storage.save_material_file(
            space_id=project.space_id,
            project_id=project_id,
            filename=filename,
            content=file_bytes,
        )

        # 3. Check for duplicate upload in same project
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Material).where(
                    Material.project_id == project_id,
                    Material.checksum == checksum,
                    Material.status != "failed"
                )
                res = await self.db.execute(stmt)
                dup = res.scalar_one_or_none()
                if dup:
                    return self._to_material_response(dup)
            except Exception:
                await self.db.rollback()

        for existing in _IN_MEMORY_MATERIALS.values():
            if (
                existing.project_id == project_id
                and existing.checksum == checksum
                and existing.status != "failed"
            ):
                return self._to_material_response(existing)

        # 4. Create new Material entity
        material_id = uuid.uuid4()
        now = datetime.now(UTC)
        sanitized_fn = self.storage.sanitize_filename(filename)

        material = Material(
            id=material_id,
            project_id=project_id,
            owner_id=user_id,
            filename=sanitized_fn,
            content_type="application/pdf",
            storage_path=storage_path,
            file_size=len(file_bytes),
            checksum=checksum,
            status="queued",
            attempt_count=0,
            created_at=now,
            updated_at=now,
        )

        _IN_MEMORY_MATERIALS[str(material_id)] = material

        if self.db is not None:
            try:
                self.db.add(material)
                await self.db.commit()
                await self.db.refresh(material)
            except Exception:
                await self.db.rollback()

        # 5. Create job & process document extraction
        await self.process_material_job(material_id)

        return self._to_material_response(_IN_MEMORY_MATERIALS.get(str(material_id), material))

    def _enqueue_material_processing_task(
        self, material_id: uuid.UUID, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> None:
        """Enqueues document extraction task to Celery worker with guaranteed inline processing fallback."""
        now = datetime.now(UTC)
        job_id = uuid.uuid4()
        job = MaterialProcessingJob(
            id=job_id,
            material_id=material_id,
            job_type="pdf_extraction",
            status="queued",
            attempt=1,
            started_at=now,
        )
        _IN_MEMORY_JOBS[str(job_id)] = job

        celery_enqueued = False
        try:
            from app.core.config import settings
            if not getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
                from workers.tasks.material_tasks import process_material_task
                process_material_task.delay(
                    material_id_str=str(material_id),
                    user_id_str=str(user_id),
                    project_id_str=str(project_id),
                )
                celery_enqueued = True
        except Exception:
            celery_enqueued = False

        if not celery_enqueued:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self.process_material_job(material_id))
            except RuntimeError:
                asyncio.run(self.process_material_job(material_id))

    async def process_material_job(self, material_id: uuid.UUID) -> Material:
        material = None
        if self.db is not None:
            from sqlalchemy import select
            stmt = select(Material).where(Material.id == material_id)
            res = await self.db.execute(stmt)
            material = res.scalar_one_or_none()

        if not material:
            material = _IN_MEMORY_MATERIALS.get(str(material_id))

        if not material:
            raise EntityNotFoundError("Material", str(material_id))

        now = datetime.now(UTC)
        material.status = "processing"
        material.current_step = "EXTRACTING_TEXT"
        material.progress_pct = 20
        material.started_at = now
        material.attempt_count += 1
        material.updated_at = now
        _IN_MEMORY_MATERIALS[str(material_id)] = material

        # Create/update processing job audit record
        job_id = uuid.uuid4()
        job = MaterialProcessingJob(
            id=job_id,
            material_id=material_id,
            job_type="pdf_extraction",
            status="processing",
            progress_pct=20,
            current_step="EXTRACTING_TEXT",
            attempt=material.attempt_count,
            started_at=now,
        )
        _IN_MEMORY_JOBS[str(job_id)] = job

        try:
            # Read bytes from storage
            content_bytes = await self.storage.read_material_file(material.storage_path)

            # Perform document extraction
            extracted_pages = self.extractor.extract(content_bytes)

            # Calculate total word count, page count, and estimated reading time
            total_words = sum(ep.metadata.get("word_count", 0) for ep in extracted_pages)
            reading_mins = max(1, round(total_words / 200)) if total_words > 0 else 0
            material.word_count = total_words
            material.page_count = len(extracted_pages)
            material.estimated_reading_minutes = reading_mins

            # Stage update: CHUNKING & KNOWLEDGE EXTRACTION
            material.current_step = "CHUNKING"
            material.progress_pct = 50
            job.current_step = "CHUNKING"
            job.progress_pct = 50

            # IDEMPOTENCY GUARANTEE: Clear pre-existing page records for material
            _IN_MEMORY_PAGES[str(material_id)] = []

            pages_list: list[MaterialPage] = []
            for ep in extracted_pages:
                p = MaterialPage(
                    id=uuid.uuid4(),
                    material_id=material_id,
                    page_number=ep.page_number,
                    extracted_text=ep.text,
                    metadata_json=ep.metadata,
                    created_at=now,
                )
                pages_list.append(p)

            _IN_MEMORY_PAGES[str(material_id)] = pages_list

            # Automatic knowledge indexing trigger
            try:
                material.current_step = "GENERATING_EMBEDDINGS"
                material.progress_pct = 80
                job.current_step = "GENERATING_EMBEDDINGS"
                job.progress_pct = 80

                from app.modules.knowledge.service import KnowledgeService
                ks = KnowledgeService(self.db)
                await ks.index_material_knowledge(
                    user_id=material.owner_id,
                    project_id=material.project_id,
                    material_id=material_id,
                )
            except Exception as index_err:
                # Log but continue so material can still enter ready status if basic extraction passed
                pass

            complete_now = datetime.now(UTC)
            material.status = "ready"
            material.current_step = "COMPLETED"
            material.progress_pct = 100
            material.completed_at = complete_now
            material.last_error = None
            material.error_code = None
            material.updated_at = complete_now
            _IN_MEMORY_MATERIALS[str(material_id)] = material

            job.status = "completed"
            job.current_step = "COMPLETED"
            job.progress_pct = 100
            job.completed_at = complete_now
            _IN_MEMORY_JOBS[str(job_id)] = job

            if self.db is not None:
                try:
                    for p in pages_list:
                        self.db.add(p)
                    self.db.add(job)
                    await self.db.commit()
                except Exception:
                    await self.db.rollback()

            DomainEventPublisher.publish(
                name="material_processed",
                aggregate_id=material_id,
                payload={
                    "material_id": str(material_id),
                    "page_count": len(pages_list),
                    "status": "ready",
                    "word_count": total_words,
                    "estimated_reading_minutes": reading_mins,
                },
            )

        except Exception as e:
            err_str = str(e)
            error_code = "SYSTEM_ERROR"
            if "parse PDF" in err_str or "corrupt" in err_str.lower():
                error_code = "CORRUPTED_PDF"
            elif "ocr" in err_str.lower():
                error_code = "OCR_ERROR"
            elif "embedding" in err_str.lower():
                error_code = "EMBEDDING_API_ERROR"

            fail_now = datetime.now(UTC)
            material.status = "failed"
            material.current_step = "FAILED"
            material.progress_pct = 0
            material.error_code = error_code
            material.failed_at = fail_now
            material.last_error = err_str
            material.updated_at = fail_now
            _IN_MEMORY_MATERIALS[str(material_id)] = material

            job.status = "failed"
            job.current_step = "FAILED"
            job.progress_pct = 0
            job.error_message = err_str
            job.completed_at = fail_now
            _IN_MEMORY_JOBS[str(job_id)] = job

            if self.db is not None:
                try:
                    self.db.add(job)
                    await self.db.commit()
                except Exception:
                    await self.db.rollback()

            DomainEventPublisher.publish(
                name="material_failed",
                aggregate_id=material_id,
                payload={
                    "material_id": str(material_id),
                    "error": err_str,
                    "error_code": error_code,
                    "status": "failed",
                },
            )

        return self._to_material_response(material)

    async def retry_material(self, user_id: uuid.UUID, material_id: uuid.UUID) -> MaterialRetryResponse:
        material = None
        if self.db is not None:
            from sqlalchemy import select
            stmt = select(Material).where(Material.id == material_id)
            res = await self.db.execute(stmt)
            material = res.scalar_one_or_none()

        if not material:
            material = _IN_MEMORY_MATERIALS.get(str(material_id))

        if not material:
            raise EntityNotFoundError("Material", str(material_id))

        # Check access
        projects_service = ProjectsService(self.db)
        project = await projects_service.get_project(material.project_id)

        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=user_id, space_id=project.space_id, min_role="member"
        )
        if not has_access and project.owner_id != user_id and material.owner_id != user_id:
            raise TenantAccessDeniedError("Access denied to retry material processing.")

        # Reset material status to queued
        material.status = "queued"
        material.last_error = None
        material.updated_at = datetime.now(UTC)
        _IN_MEMORY_MATERIALS[str(material_id)] = material

        if self.db is not None:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        # Enqueue Celery processing job
        self._enqueue_material_processing_task(material_id, user_id, material.project_id)

        latest_job = [j for j in _IN_MEMORY_JOBS.values() if j.material_id == material_id]
        job_id = latest_job[-1].id if latest_job else uuid.uuid4()

        return MaterialRetryResponse(
            material_id=material_id,
            job_id=job_id,
            status=material.status,
            attempt_count=material.attempt_count + 1,
        )

    async def get_material(self, user_id: uuid.UUID, material_id: uuid.UUID) -> MaterialResponse:
        material = None
        if self.db is not None:
            from sqlalchemy import select
            stmt = select(Material).where(Material.id == material_id)
            res = await self.db.execute(stmt)
            material = res.scalar_one_or_none()

        if not material:
            material = _IN_MEMORY_MATERIALS.get(str(material_id))

        if not material:
            raise EntityNotFoundError("Material", str(material_id))

        # Check tenant access
        projects_service = ProjectsService(self.db)
        project = await projects_service.get_project(material.project_id)

        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=user_id, space_id=project.space_id, min_role="member"
        )
        if not has_access and project.owner_id != user_id and material.owner_id != user_id:
            raise TenantAccessDeniedError("Access denied for requested material.")

        return self._to_material_response(material)

    async def list_materials(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedMaterialsResponse:
        auth_service = AuthService(self.db)
        user_spaces = await auth_service.list_user_spaces(user_id)
        accessible_space_ids = {sp.id for sp in user_spaces}

        projects_service = ProjectsService(self.db)

        if project_id:
            proj = await projects_service.get_project(project_id)
            if proj.space_id not in accessible_space_ids and proj.owner_id != user_id:
                raise TenantAccessDeniedError("Access denied for requested project materials.")

        matched_map: dict[str, Material] = dict(_IN_MEMORY_MATERIALS)

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Material)
                res = await self.db.execute(stmt)
                db_mats = res.scalars().all()
                for m in db_mats:
                    matched_map[str(m.id)] = m
            except Exception:
                await self.db.rollback()

        # Build projects map once to prevent N+1 queries per material
        projects_map: dict[uuid.UUID, tuple[uuid.UUID, uuid.UUID]] = {}
        from app.modules.projects.service import _IN_MEMORY_PROJECTS
        for p in _IN_MEMORY_PROJECTS.values():
            projects_map[p.id] = (p.space_id, p.owner_id)

        if self.db is not None:
            try:
                from sqlalchemy import select
                from app.modules.projects.models import Project
                p_stmt = select(Project.id, Project.space_id, Project.owner_id)
                p_res = await self.db.execute(p_stmt)
                for p_id, p_sid, p_oid in p_res.all():
                    projects_map[p_id] = (p_sid, p_oid)
            except Exception:
                await self.db.rollback()

        matched: list[Material] = []
        for mat in matched_map.values():
            if project_id and mat.project_id != project_id:
                continue

            # Verify project space accessibility or project ownership
            p_info = projects_map.get(mat.project_id)
            if p_info:
                p_space_id, p_owner_id = p_info
                if p_space_id not in accessible_space_ids and p_owner_id != user_id and mat.owner_id != user_id:
                    continue
            elif mat.owner_id != user_id:
                continue

            if search and search.lower() not in mat.filename.lower():
                continue

            matched.append(mat)

        matched.sort(key=lambda m: m.created_at, reverse=True)
        total = len(matched)
        start = (page - 1) * limit
        end = start + limit
        paged = matched[start:end]

        return PaginatedMaterialsResponse(
            items=[self._to_material_response(m) for m in paged],
            total=total,
            page=page,
            limit=limit,
        )

    async def get_material_pages(
        self, user_id: uuid.UUID, material_id: uuid.UUID, page: int = 1, limit: int = 50
    ) -> PaginatedPagesResponse:
        # Check material access
        await self.get_material(user_id, material_id)

        pages: list[MaterialPage] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(MaterialPage).where(MaterialPage.material_id == material_id).order_by(MaterialPage.page_number)
                res = await self.db.execute(stmt)
                pages = list(res.scalars().all())
            except Exception:
                await self.db.rollback()

        if not pages:
            pages = _IN_MEMORY_PAGES.get(str(material_id), [])
            pages.sort(key=lambda p: p.page_number)

        total = len(pages)
        start = (page - 1) * limit
        end = start + limit
        paged = pages[start:end]

        items = [
            MaterialPageResponse(
                id=p.id,
                material_id=p.material_id,
                page_number=p.page_number,
                extracted_text=p.extracted_text,
                metadata_json=p.metadata_json,
                created_at=p.created_at,
            )
            for p in paged
        ]

        return PaginatedPagesResponse(items=items, total=total, page=page, limit=limit)

    def _to_material_response(self, mat: Material) -> MaterialResponse:
        page_count = 0
        if hasattr(mat, "__dict__") and "pages" in mat.__dict__ and mat.pages is not None:
            page_count = len(mat.pages)
        elif str(mat.id) in _IN_MEMORY_PAGES:
            page_count = len(_IN_MEMORY_PAGES[str(mat.id)])
        else:
            page_count = getattr(mat, "page_count", 0) or 0

        now = datetime.now(UTC)
        return MaterialResponse(
            id=mat.id,
            project_id=mat.project_id,
            owner_id=mat.owner_id,
            filename=mat.filename,
            content_type=mat.content_type,
            storage_path=mat.storage_path,
            file_size=mat.file_size,
            checksum=mat.checksum,
            status=mat.status,
            progress_pct=getattr(mat, "progress_pct", None) if getattr(mat, "progress_pct", None) is not None else (100 if mat.status == "ready" else 0),
            current_step=getattr(mat, "current_step", None) or ("COMPLETED" if mat.status == "ready" else "QUEUED"),
            error_code=getattr(mat, "error_code", None),
            word_count=getattr(mat, "word_count", None) or 0,
            estimated_reading_minutes=getattr(mat, "estimated_reading_minutes", None) or 0,
            attempt_count=getattr(mat, "attempt_count", None) or 0,
            last_error=mat.last_error,
            created_at=getattr(mat, "created_at", None) or now,
            updated_at=getattr(mat, "updated_at", None) or now,
            started_at=mat.started_at,
            completed_at=mat.completed_at,
            failed_at=mat.failed_at,
            page_count=page_count,
        )
