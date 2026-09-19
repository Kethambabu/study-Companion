import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.core.database import Base
from app.modules.auth.models import Profile
from app.modules.projects.models import Project


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Study Session")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    project: Mapped["Project"] = relationship("Project")
    user: Mapped["Profile"] = relationship("Profile")
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conv_project_user", "project_id", "user_id"),
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system, tool
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_msg_conversation_id", "conversation_id"),
        Index("idx_msg_conv_created", "conversation_id", "created_at"),
    )


from app.modules.observability.models import AIObservabilityLog

