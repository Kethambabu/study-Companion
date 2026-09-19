import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BackgroundJob(Base):
    """PRD Compliant Background Job Entity for Asynchronous Processing (PRD 81-84)."""
    __tablename__ = "background_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # 0.0 - 100.0

    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)  # OCR_ERROR, CORRUPTED_PDF, SYSTEM_ERROR, TIMEOUT
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_background_jobs_project_status", "project_id", "status"),
        Index("ix_background_jobs_user_status", "user_id", "status"),
    )
