import uuid
from datetime import UTC, datetime

from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import make_transient

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
                    # Expunge from session so a later rollback can't expire these attributes.
                    # make_transient() removes the instance from the identity map entirely,
                    # preventing any lazy-load attempts on the async engine.
                    try:
                        self.db.expunge(p)
                        make_transient(p)
                    except Exception:
                        pass
                    matched_map[str(p.id)] = p
            except Exception:
                try:
                    await self.db.rollback()
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

        # Batch fetch material counts and concept masteries for paged_items in 2 queries instead of N+1
        mat_counts: dict[uuid.UUID, int] = {}
        mastery_avgs: dict[uuid.UUID, float] = {}

        if self.db is not None and paged_items:
            try:
                from sqlalchemy import func, select
                from app.modules.materials.models import Material
                from app.modules.mastery.models import ConceptMastery

                p_ids = [p.id for p in paged_items]

                # Query 1: Count materials per project
                m_stmt = (
                    select(Material.project_id, func.count(Material.id))
                    .where(Material.project_id.in_(p_ids))
                    .group_by(Material.project_id)
                )
                m_res = await self.db.execute(m_stmt)
                for pid, cnt in m_res.all():
                    mat_counts[pid] = cnt

                # Query 2: Average concept mastery per project
                mast_stmt = (
                    select(ConceptMastery.project_id, func.avg(ConceptMastery.mastery_score))
                    .where(ConceptMastery.project_id.in_(p_ids))
                    .group_by(ConceptMastery.project_id)
                )
                mast_res = await self.db.execute(mast_stmt)
                for pid, avg_score in mast_res.all():
                    if avg_score is not None:
                        mastery_avgs[pid] = float(avg_score)
            except Exception:
                await self.db.rollback()

        from app.modules.materials.service import _IN_MEMORY_MATERIALS
        items: list[ProjectResponse] = []
        for p in paged_items:
            m_cnt = mat_counts.get(p.id, 0)
            in_mem_cnt = sum(1 for m in _IN_MEMORY_MATERIALS.values() if getattr(m, "project_id", None) == p.id)
            final_m_cnt = max(m_cnt, in_mem_cnt)

            m_avg = mastery_avgs.get(p.id)
            if m_avg is not None:
                prog_pct = int(round(m_avg * 100))
            elif final_m_cnt > 0:
                prog_pct = 25
            else:
                prog_pct = 0

            items.append(
                ProjectResponse(
                    id=p.id,
                    space_id=p.space_id,
                    owner_id=p.owner_id,
                    name=p.name,
                    description=p.description,
                    learning_goal=p.learning_goal,
                    status=p.status,
                    materials_count=final_m_cnt,
                    progress=prog_pct,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    archived_at=getattr(p, "archived_at", None),
                )
            )

        return PaginatedProjectsResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    async def get_project_model(self, project_id: uuid.UUID) -> Project:
        proj = _IN_MEMORY_PROJECTS.get(str(project_id))
        if proj:
            return proj

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Project).where(Project.id == project_id)
                res = await self.db.execute(stmt)
                db_proj = res.scalar_one_or_none()
                if db_proj:
                    _IN_MEMORY_PROJECTS[str(project_id)] = db_proj
                    return db_proj
            except Exception:
                await self.db.rollback()

        raise EntityNotFoundError("Project", str(project_id))

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
        # If the ORM instance is still attached to a session, expunge + make_transient
        # before touching any attributes to prevent lazy-load on async engine.
        try:
            state = sa_inspect(proj)
            if state.session_id is not None and self.db is not None:
                try:
                    self.db.expunge(proj)
                    make_transient(proj)
                except Exception:
                    pass
        except Exception:
            pass

        # Snapshot all scalar fields from __dict__ first (avoids any ORM descriptor call)
        _d = proj.__dict__
        proj_id = _d.get("id") or proj.id
        proj_space_id = _d.get("space_id") or proj.space_id
        proj_owner_id = _d.get("owner_id") or proj.owner_id
        proj_name = _d.get("name") or proj.name
        proj_description = _d.get("description", None)
        proj_learning_goal = _d.get("learning_goal", None)
        proj_status = _d.get("status") or proj.status
        proj_created_at = _d.get("created_at") or proj.created_at
        proj_updated_at = _d.get("updated_at") or proj.updated_at
        proj_archived_at = _d.get("archived_at", None)

        mats_count = 0
        from app.modules.materials.service import _IN_MEMORY_MATERIALS
        for m in list(_IN_MEMORY_MATERIALS.values()):
            try:
                m_pid = m.__dict__.get("project_id")
                if m_pid == proj_id:
                    mats_count += 1
            except Exception:
                pass

        if self.db is not None:
            try:
                from sqlalchemy import func, select
                from app.modules.materials.models import Material
                stmt = select(func.count(Material.id)).where(Material.project_id == proj_id)
                res = await self.db.execute(stmt)
                db_c = res.scalar() or 0
                mats_count = max(mats_count, db_c)
            except Exception:
                await self.db.rollback()

        progress_pct = 0
        if mats_count > 0:
            try:
                from app.modules.mastery.service import _IN_MEMORY_MASTERY
                masteries = [m for m in _IN_MEMORY_MASTERY.values() if str(m.project_id) == str(proj_id)]
                if self.db is not None:
                    try:
                        from sqlalchemy import select
                        from app.modules.mastery.models import ConceptMastery
                        stmt = select(ConceptMastery).where(ConceptMastery.project_id == proj_id)
                        res = await self.db.execute(stmt)
                        db_m = list(res.scalars().all())
                        if db_m:
                            masteries = db_m
                    except Exception:
                        await self.db.rollback()
                if masteries:
                    avg_m = sum(float(m.mastery_score) for m in masteries) / len(masteries)
                    progress_pct = int(round(avg_m * 100))
                else:
                    progress_pct = 25
            except Exception:
                progress_pct = 0

        return ProjectResponse(
            id=proj_id,
            space_id=proj_space_id,
            owner_id=proj_owner_id,
            name=proj_name,
            description=proj_description,
            learning_goal=proj_learning_goal,
            status=proj_status,
            materials_count=mats_count,
            progress=progress_pct,
            created_at=proj_created_at,
            updated_at=proj_updated_at,
            archived_at=proj_archived_at,
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
