import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.auth.models import Profile
from app.modules.projects.models import Project


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="uploaded"
    )  # uploaded, queued, processing, ready, failed
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False, default="QUEUED")
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_reading_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped["Project"] = relationship("Project")
    owner: Mapped["Profile"] = relationship("Profile")
    pages: Mapped[list["MaterialPage"]] = relationship("MaterialPage", back_populates="material", cascade="all, delete-orphan")
    jobs: Mapped[list["MaterialProcessingJob"]] = relationship("MaterialProcessingJob", back_populates="material", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_materials_project_id", "project_id"),
        Index("idx_materials_owner_id", "owner_id"),
        Index("idx_materials_checksum", "checksum"),
        Index("idx_materials_status", "status"),
    )


class MaterialProcessingJob(Base):
    __tablename__ = "material_processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, default="pdf_extraction")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, processing, completed, failed
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(100), nullable=False, default="QUEUED")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    material: Mapped["Material"] = relationship("Material", back_populates="jobs")

    __table_args__ = (
        Index("idx_jobs_material_id", "material_id"),
        Index("idx_jobs_status", "status"),
    )


class MaterialPage(Base):
    __tablename__ = "material_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    material: Mapped["Material"] = relationship("Material", back_populates="pages")

    __table_args__ = (
        Index("idx_pages_material_id", "material_id"),
        Index("idx_pages_material_page", "material_id", "page_number", unique=True),
    )
