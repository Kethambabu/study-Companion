import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # review_material, take_quiz, practice_concept, review_mistakes, ask_tutor
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_concept_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")  # active, completed, dismissed
    reason_evidence_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @property
    def reason(self) -> str:
        return self.reason_evidence_json.get("rationale", self.title)

    @property
    def action(self) -> str:
        return self.description

    @property
    def concept_id(self) -> str | None:
        return self.target_concept_id

    __table_args__ = (
        Index("ix_recommendations_project_user_status", "project_id", "user_id", "status"),
    )
