import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_concept_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)  # mcq, open_ended
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # ["A", "B", "C", "D"] for MCQ
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)  # beginner, intermediate, advanced
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(nullable=False, default=0)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")  # in_progress, completed
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(nullable=False, default=0.0)


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False, default=False)
    score_percentage: Mapped[float] = mapped_column(nullable=False, default=0.0)
    feedback_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score: Mapped[float] = mapped_column(nullable=False, default=0.0)
    concepts_tested: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    weak_concepts: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    strong_concepts: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    recommendations: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


class QuestionBankItem(Base):
    __tablename__ = "question_bank_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False, default="intermediate")
    question_type: Mapped[str] = mapped_column(String(50), nullable=False, default="mcq")
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="unused")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False)


