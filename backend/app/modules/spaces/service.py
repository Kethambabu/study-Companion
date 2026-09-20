import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.auth.models import Space
from app.modules.auth.service import _IN_MEMORY_MEMBERS, _IN_MEMORY_SPACES


class SpaceUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = None
    visual_metadata: dict | None = None


class DetailedSpaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    visual_metadata: dict | None = None
    owner_id: uuid.UUID
    role: str = "owner"
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class PaginatedSpacesResponse(BaseModel):
    items: list[DetailedSpaceResponse]
    total: int
    page: int
    limit: int


class SpacesService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def list_spaces(
        self, user_id: uuid.UUID, search: str | None = None, page: int = 1, limit: int = 20
    ) -> PaginatedSpacesResponse:
        matched: list[tuple[Space, str]] = []

        # 1. Check in-memory repository first for fast 0ms response
        for space_id, members in _IN_MEMORY_MEMBERS.items():
            for m in members:
                if m.user_id == user_id:
                    sp = _IN_MEMORY_SPACES.get(space_id)
                    if sp and not sp.archived_at:
                        if search:
                            term = search.lower()
                            if term not in sp.name.lower() and (not sp.description or term not in sp.description.lower()):
                                continue
                        matched.append((sp, m.role))

        # 2. Query database if memory cache yielded no spaces
        if not matched and self.db:
            try:
                from sqlalchemy import select, or_
                from app.modules.auth.models import SpaceMember

                stmt = (
                    select(Space, SpaceMember.role)
                    .join(SpaceMember, Space.id == SpaceMember.space_id)
                    .where(SpaceMember.user_id == user_id, Space.archived_at.is_(None))
                )
                if search:
                    term = f"%{search.strip()}%"
                    stmt = stmt.where(or_(Space.name.ilike(term), Space.description.ilike(term)))

                res = await self.db.execute(stmt)
                for sp, role in res.all():
                    matched.append((sp, role))
                    _IN_MEMORY_SPACES[str(sp.id)] = sp
                    if str(sp.id) not in _IN_MEMORY_MEMBERS:
                        _IN_MEMORY_MEMBERS[str(sp.id)] = []
                    if not any(m.user_id == user_id for m in _IN_MEMORY_MEMBERS[str(sp.id)]):
                        _IN_MEMORY_MEMBERS[str(sp.id)].append(SpaceMember(id=uuid.uuid4(), space_id=sp.id, user_id=user_id, role=role))
            except Exception as err:
                import logging
                logging.warning(f"Database list_spaces query failed ({err}). Operating in in-memory mode.")


        total = len(matched)
        start = (page - 1) * limit
        end = start + limit
        paged = matched[start:end]

        items = [
            DetailedSpaceResponse(
                id=sp.id,
                name=sp.name,
                slug=sp.slug,
                description=sp.description,
                visual_metadata=sp.visual_metadata,
                owner_id=sp.owner_id,
                role=role,
                created_at=sp.created_at,
                updated_at=sp.updated_at,
                archived_at=sp.archived_at,
            )
            for sp, role in paged
        ]

        return PaginatedSpacesResponse(items=items, total=total, page=page, limit=limit)

    async def get_space(self, user_id: uuid.UUID, space_id: uuid.UUID) -> DetailedSpaceResponse:
        user_role = None
        sp = None

        if self.db:
            from sqlalchemy import select
            from app.modules.auth.models import SpaceMember

            stmt = (
                select(Space, SpaceMember.role)
                .join(SpaceMember, Space.id == SpaceMember.space_id)
                .where(Space.id == space_id, SpaceMember.user_id == user_id, Space.archived_at.is_(None))
            )
            res = await self.db.execute(stmt)
            row = res.first()
            if not row:
                # Check if space exists at all to differentiate 404 vs 403
                sp_stmt = select(Space).where(Space.id == space_id, Space.archived_at.is_(None))
                sp_res = await self.db.execute(sp_stmt)
                if not sp_res.scalar_one_or_none():
                    raise EntityNotFoundError("Space", str(space_id))
                raise TenantAccessDeniedError("Access denied for requested space.")
            sp, user_role = row[0], row[1]
        else:
            sp = _IN_MEMORY_SPACES.get(str(space_id))
            if not sp or sp.archived_at:
                raise EntityNotFoundError("Space", str(space_id))

            members = _IN_MEMORY_MEMBERS.get(str(space_id), [])
            for m in members:
                if m.user_id == user_id:
                    user_role = m.role
                    break

            if not user_role:
                raise TenantAccessDeniedError("Access denied for requested space.")

        return DetailedSpaceResponse(
            id=sp.id,
            name=sp.name,
            slug=sp.slug,
            description=sp.description,
            visual_metadata=sp.visual_metadata,
            owner_id=sp.owner_id,
            role=user_role,
            created_at=sp.created_at,
            updated_at=sp.updated_at,
            archived_at=sp.archived_at,
        )

    async def update_space(
        self, user_id: uuid.UUID, space_id: uuid.UUID, req: SpaceUpdateRequest
    ) -> DetailedSpaceResponse:
        if self.db:
            from sqlalchemy import select
            stmt = select(Space).where(Space.id == space_id, Space.archived_at.is_(None))
            res = await self.db.execute(stmt)
            sp = res.scalar_one_or_none()
            if not sp:
                raise EntityNotFoundError("Space", str(space_id))
            if sp.owner_id != user_id:
                raise TenantAccessDeniedError("Only space owner can update space settings.")

            if req.name is not None:
                sp.name = req.name.strip()
            if req.description is not None:
                sp.description = req.description.strip() if req.description else None
            if req.visual_metadata is not None:
                sp.visual_metadata = req.visual_metadata

            sp.updated_at = datetime.now(UTC)
            await self.db.commit()
            await self.db.refresh(sp)
        else:
            sp = _IN_MEMORY_SPACES.get(str(space_id))
            if not sp or sp.archived_at:
                raise EntityNotFoundError("Space", str(space_id))

            if sp.owner_id != user_id:
                raise TenantAccessDeniedError("Only space owner can update space settings.")

            if req.name is not None:
                sp.name = req.name.strip()
            if req.description is not None:
                sp.description = req.description.strip() if req.description else None
            if req.visual_metadata is not None:
                sp.visual_metadata = req.visual_metadata

            sp.updated_at = datetime.now(UTC)
            _IN_MEMORY_SPACES[str(space_id)] = sp

        return DetailedSpaceResponse(
            id=sp.id,
            name=sp.name,
            slug=sp.slug,
            description=sp.description,
            visual_metadata=sp.visual_metadata,
            owner_id=sp.owner_id,
            role="owner",
            created_at=sp.created_at,
            updated_at=sp.updated_at,
            archived_at=sp.archived_at,
        )

    async def archive_space(self, user_id: uuid.UUID, space_id: uuid.UUID) -> DetailedSpaceResponse:
        now = datetime.now(UTC)
        if self.db:
            from sqlalchemy import select
            stmt = select(Space).where(Space.id == space_id, Space.archived_at.is_(None))
            res = await self.db.execute(stmt)
            sp = res.scalar_one_or_none()
            if not sp:
                raise EntityNotFoundError("Space", str(space_id))
            if sp.owner_id != user_id:
                raise TenantAccessDeniedError("Only space owner can archive or delete space.")

            sp.archived_at = now
            sp.updated_at = now
            await self.db.commit()
            await self.db.refresh(sp)
        else:
            sp = _IN_MEMORY_SPACES.get(str(space_id))
            if not sp or sp.archived_at:
                raise EntityNotFoundError("Space", str(space_id))

            if sp.owner_id != user_id:
                raise TenantAccessDeniedError("Only space owner can archive or delete space.")

            sp.archived_at = now
            sp.updated_at = now
            _IN_MEMORY_SPACES[str(space_id)] = sp

        return DetailedSpaceResponse(
            id=sp.id,
            name=sp.name,
            slug=sp.slug,
            description=sp.description,
            visual_metadata=sp.visual_metadata,
            owner_id=sp.owner_id,
            role="owner",
            created_at=sp.created_at,
            updated_at=sp.updated_at,
            archived_at=sp.archived_at,
        )

