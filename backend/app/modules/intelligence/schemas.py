import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class WeakConceptItem(BaseModel):
    concept_id: str
    mastery_score: float
    confidence: float
    status: str
    recent_errors_count: int
    recommendation: str


class StrengthConceptItem(BaseModel):
    concept_id: str
    mastery_score: float
    confidence: float
    status: str
    mastery_level: str


class RepeatedMistakeItem(BaseModel):
    concept_id: str
    topic_question: str
    mistake_count: int
    last_error_at: datetime
    suggested_fix: str


class NextActionItem(BaseModel):
    id: str
    action_type: Literal["review_document", "practice_quiz", "ask_tutor", "take_assessment"]
    title: str
    description: str
    concept_id: str
    priority: Literal["high", "medium", "low"]
    target_url: str | None = None
    page_reference: str | None = None


class LearningGoalItem(BaseModel):
    goal_id: str
    title: str
    target_mastery_pct: float
    current_mastery_pct: float
    is_achieved: bool
    progress_percentage: float


class LearningIntelligenceSummaryResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    weak_concepts: list[WeakConceptItem]
    strong_concepts: list[StrengthConceptItem]
    repeated_mistakes: list[RepeatedMistakeItem]
    next_actions: list[NextActionItem]
    learning_goals: list[LearningGoalItem]
    generated_at: datetime
