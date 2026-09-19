import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.modules.events.publisher import DomainEventPublisher
from app.modules.projects.models import Project
from app.modules.projects.schemas import (
    PaginatedProjectsResponse,
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)

# In-memory repository for Projects domain
_IN_MEMORY_PROJECTS: dict[str, Project] = {}


class ProjectsService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def create_project(self, user_id: uuid.UUID, req: ProjectCreateRequest) -> ProjectResponse:
        project_id = uuid.uuid4()
        now = datetime.now(UTC)

        project = Project(
            id=project_id,
            space_id=req.space_id,
            owner_id=user_id,
            title=req.name.strip(),
            name=req.name.strip(),
            description=req.description.strip() if req.description else None,
            learning_goal=req.learning_goal.strip() if req.learning_goal else None,
            status="active",
            created_at=now,
            updated_at=now,
        )

        _IN_MEMORY_PROJECTS[str(project_id)] = project

        if self.db is not None:
            try:
                from sqlalchemy import select
                from app.modules.auth.models import Profile
                from app.modules.auth.service import _IN_MEMORY_PROFILES

                prof_stmt = select(Profile).where(Profile.id == user_id)
                prof_res = await self.db.execute(prof_stmt)
                if not prof_res.scalar_one_or_none():
                    in_mem_prof = _IN_MEMORY_PROFILES.get(str(user_id))
                    if in_mem_prof:
                        db_prof = Profile(
                            id=user_id,
                            email=in_mem_prof.email,
                            full_name=in_mem_prof.full_name,
                            password_hash=in_mem_prof.password_hash,
                            role=in_mem_prof.role,
                        )
                        self.db.add(db_prof)

                self.db.add(project)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        DomainEventPublisher.publish(
            name="project_created",
            aggregate_id=project_id,
            payload={
                "project_id": str(project_id),
                "space_id": str(req.space_id),
                "owner_id": str(user_id),
                "name": project.name,
            },
        )

        return await self._to_response_async(project)

    async def list_projects(
        self,
        user_id: uuid.UUID,
        space_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        search: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedProjectsResponse:
        from sqlalchemy import select
        from app.modules.auth.service import AuthService
        auth_service = AuthService(self.db)
        user_spaces = await auth_service.list_user_spaces(user_id)
        accessible_space_ids = {sp.id for sp in user_spaces}

        matched_map: dict[str, Project] = dict(_IN_MEMORY_PROJECTS)

        if self.db is not None:
            try:
                stmt = select(Project)
                res = await self.db.execute(stmt)
                db_projs = res.scalars().all()
                for p in db_projs:
                    matched_map[str(p.id)] = p
            except Exception:
                pass

        matched: list[Project] = []
        for proj in matched_map.values():
            if proj.space_id not in accessible_space_ids:
                continue
            if space_id and proj.space_id != space_id:
                continue
            if status_filter and proj.status != status_filter:
                continue
            if search:
                term = search.lower()
                if term not in proj.name.lower() and (not proj.description or term not in proj.description.lower()):
                    continue
            matched.append(proj)

        # Sort newest first
        matched.sort(key=lambda p: p.created_at, reverse=True)

        total = len(matched)
        start = (page - 1) * limit
        end = start + limit
        paged_items = matched[start:end]

        items = [await self._to_response_async(p) for p in paged_items]
        return PaginatedProjectsResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def get_project_model(self, project_id: uuid.UUID) -> Project:
        from sqlalchemy import select
        proj = None
        if self.db is not None:
            try:
                stmt = select(Project).where(Project.id == project_id)
                res = await self.db.execute(stmt)
                proj = res.scalar_one_or_none()
            except Exception:
                pass
        if not proj:
            proj = _IN_MEMORY_PROJECTS.get(str(project_id))
        if not proj:
            raise EntityNotFoundError("Project", str(project_id))
        return proj

    async def get_project(self, project_id: uuid.UUID) -> ProjectResponse:
        proj = await self.get_project_model(project_id)
        return await self._to_response_async(proj)

    async def update_project(
        self, user_id: uuid.UUID, project_id: uuid.UUID, req: ProjectUpdateRequest
    ) -> ProjectResponse:
        proj = await self.get_project_model(project_id)

        if req.name is not None:
            proj.name = req.name.strip()
        if req.description is not None:
            proj.description = req.description.strip() if req.description else None
        if req.learning_goal is not None:
            proj.learning_goal = req.learning_goal.strip() if req.learning_goal else None
        if req.status is not None:
            proj.status = req.status
            if req.status == "archived" and not proj.archived_at:
                proj.archived_at = datetime.now(UTC)

        proj.updated_at = datetime.now(UTC)
        _IN_MEMORY_PROJECTS[str(project_id)] = proj

        if self.db is not None:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        DomainEventPublisher.publish(
            name="project_updated",
            aggregate_id=project_id,
            payload={"project_id": str(project_id), "status": proj.status},
        )

        return await self._to_response_async(proj)

    async def archive_project(self, user_id: uuid.UUID, project_id: uuid.UUID) -> ProjectResponse:
        proj = await self.get_project_model(project_id)

        now = datetime.now(UTC)
        proj.status = "archived"
        proj.archived_at = now
        proj.updated_at = now
        _IN_MEMORY_PROJECTS[str(project_id)] = proj

        if self.db is not None:
            try:
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        DomainEventPublisher.publish(
            name="project_archived",
            aggregate_id=project_id,
            payload={"project_id": str(project_id), "archived_at": now.isoformat()},
        )

        return await self._to_response_async(proj)

    async def _to_response_async(self, proj: Project) -> ProjectResponse:
        mats_count = 0
        from app.modules.materials.service import _IN_MEMORY_MATERIALS
        for m in list(_IN_MEMORY_MATERIALS.values()):
            try:
                m_pid = m.__dict__.get("project_id")
                if m_pid == proj.id:
                    mats_count += 1
            except Exception:
                pass

        if self.db is not None:
            try:
                from sqlalchemy import func, select
                from app.modules.materials.models import Material
                stmt = select(func.count(Material.id)).where(Material.project_id == proj.id)
                res = await self.db.execute(stmt)
                db_c = res.scalar() or 0
                mats_count = max(mats_count, db_c)
            except Exception:
                pass

        progress_pct = 0
        if mats_count > 0:
            try:
                from app.modules.mastery.service import _IN_MEMORY_MASTERY
                masteries = [m for m in _IN_MEMORY_MASTERY.values() if str(m.project_id) == str(proj.id)]
                if self.db is not None:
                    try:
                        from sqlalchemy import select
                        from app.modules.mastery.models import ConceptMastery
                        stmt = select(ConceptMastery).where(ConceptMastery.project_id == proj.id)
                        res = await self.db.execute(stmt)
                        db_m = list(res.scalars().all())
                        if db_m:
                            masteries = db_m
                    except Exception:
                        pass
                if masteries:
                    avg_m = sum(float(m.mastery_score) for m in masteries) / len(masteries)
                    progress_pct = int(round(avg_m * 100))
                else:
                    progress_pct = 25
            except Exception:
                progress_pct = 0

        return ProjectResponse(
            id=proj.id,
            space_id=proj.space_id,
            owner_id=proj.owner_id,
            name=proj.name,
            description=proj.description,
            learning_goal=proj.learning_goal,
            status=proj.status,
            materials_count=mats_count,
            progress=progress_pct,
            created_at=proj.created_at,
            updated_at=proj.updated_at,
            archived_at=proj.archived_at,
        )

    def _to_response(self, proj: Project) -> ProjectResponse:
        mats_count = 0
        from app.modules.materials.service import _IN_MEMORY_MATERIALS
        for m in _IN_MEMORY_MATERIALS.values():
            if m.project_id == proj.id:
                mats_count += 1

        return ProjectResponse(
            id=proj.id,
            space_id=proj.space_id,
            owner_id=proj.owner_id,
            name=proj.name,
            description=proj.description,
            learning_goal=proj.learning_goal,
            status=proj.status,
            materials_count=mats_count,
            progress=25 if mats_count > 0 else 0,
            created_at=proj.created_at,
            updated_at=proj.updated_at,
            archived_at=proj.archived_at,
        )
