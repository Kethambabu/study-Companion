import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ActivityEvent(Base):
    """PRD Compliant Activity Event DB Table ('activity_events')."""
    __tablename__ = "activity_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    space_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("spaces.id", ondelete="CASCADE"), nullable=True, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, processed, failed
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, default=lambda: f"evt_{uuid.uuid4()}", unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_activity_events_project_type", "project_id", "event_type"),
        Index("ix_activity_events_user_type", "user_id", "event_type"),
    )

    def __init__(self, **kwargs: Any):
        if "payload_json" in kwargs and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = kwargs.pop("payload_json")
        elif "payload_json" in kwargs:
            kwargs.pop("payload_json")
        if "idempotency_key" not in kwargs:
            kwargs["idempotency_key"] = f"evt_{uuid.uuid4()}"
        super().__init__(**kwargs)

    @property
    def payload_json(self) -> dict[str, Any]:
        return self.metadata_json

# Backward-compatibility alias
LearningEvent = ActivityEvent

