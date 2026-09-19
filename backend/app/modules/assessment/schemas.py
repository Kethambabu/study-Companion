import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# --- LLM Structured Output Validation Schemas ---

class GeneratedQuestionSchema(BaseModel):
    question_type: Literal["mcq", "open_ended"] = Field(..., description="Type of question")
    question_text: str = Field(..., min_length=10, description="Clear academic question text")
    options: list[str] | None = Field(default=None, description="4 answer choices for MCQ, null for open-ended")
    correct_answer: str = Field(..., min_length=1, description="Correct choice for MCQ or ideal answer snippet for open-ended")
    concept_id: str = Field(..., min_length=1, description="Target concept identifier")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(..., description="Assessed difficulty level")
    explanation: str = Field(..., min_length=10, description="Pedagogical explanation of the solution")


class OpenEndedEvaluationSchema(BaseModel):
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall answer score from 0.0 to 100.0")
    score_out_of_10: float = Field(default=7.5, description="Score formatted out of 10 (e.g. 7.5)")
    is_correct: bool = Field(..., description="Whether answer meets minimum mastery threshold (>= 60%)")
    understanding_level: Literal["excellent", "partial", "poor"] = Field(..., description="Level of conceptual understanding demonstrated")
    understanding_status: str = Field(default="Good", description="Understanding dimension rating (Good, Missing, Needs work)")
    accuracy_status: str = Field(default="Good", description="Accuracy dimension rating (Good, Missing, Needs work)")
    relevance_status: str = Field(default="Good", description="Relevance dimension rating (Good, Missing, Needs work)")
    key_concepts_status: str = Field(default="Missing", description="Key concepts dimension rating (Good, Missing, Needs work)")
    reasoning_status: str = Field(default="Good", description="Reasoning dimension rating (Good, Missing, Needs work)")
    key_concepts_demonstrated: list[str] = Field(default_factory=list, description="Concepts correctly identified/explained")
    missing_concepts: list[str] = Field(default_factory=list, description="Key concepts omitted or misunderstood")
    reasoning_quality: str = Field(..., description="Evaluation of logical reasoning")
    feedback_what_was_understood: str = Field(..., description="Explanation of what the student understood well")
    feedback_what_was_missing: str = Field(..., description="Explanation of what was missing or incorrect")
    feedback_how_to_improve: str = Field(..., description="Actionable advice for improvement")
    recommended_review_page: str = Field(default='Review "Retrieval Quality" — Page 19', description="Recommended document section and page")
    mastery_before: int | float | None = None
    mastery_after: int | float | None = None
    mastery_delta_str: str | None = None


class AdaptiveDecisionSchema(BaseModel):
    target_concept_id: str
    target_difficulty: Literal["beginner", "intermediate", "advanced"]
    reason_signals: list[str] = Field(default_factory=list, description="Explanatory signals for adaptive selection")


# --- API Request & Response DTOs ---

class QuizCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    target_concept_id: str | None = None
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty_preference: Literal["adaptive", "beginner", "intermediate", "advanced"] = "adaptive"


class QuizQuestionPublicResponse(BaseModel):
    id: uuid.UUID
    question_type: str
    question_text: str
    options: list[str] | None = None
    concept_id: str
    difficulty: str
    order_index: int
    # Note: correct_answer and explanation are deliberately omitted during active session quiz display!


class QuizQuestionFullResponse(QuizQuestionPublicResponse):
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None = None
    target_concept_id: str | None = None
    questions: list[QuizQuestionPublicResponse]
    created_at: datetime


class QuizAttemptResponse(BaseModel):
    id: uuid.UUID
    quiz_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    score: float
    max_score: float
    current_question_index: int = 0
    submitted_question_ids: list[uuid.UUID] = Field(default_factory=list)


class SubmitAnswerRequest(BaseModel):
    user_answer: str = Field(..., min_length=1, description="Student submitted answer string or selected option letter/text")


class QuestionAttemptResponse(BaseModel):
    id: uuid.UUID
    attempt_id: uuid.UUID
    question_id: uuid.UUID
    user_answer: str
    is_correct: bool
    score_percentage: float
    explanation: str
    correct_answer: str | None = None  # Revealed ONLY AFTER question answer is submitted!
    feedback: OpenEndedEvaluationSchema | dict[str, Any]
    submitted_at: datetime


class QuizSummaryResponse(BaseModel):
    attempt_id: uuid.UUID
    quiz_id: uuid.UUID
    project_id: uuid.UUID
    overall_score: float
    max_score: float
    score_percentage: float
    status: str
    completed_at: datetime | None = None
    concepts_tested: dict[str, Any]
    weak_concepts: list[str]
    strong_concepts: list[str]
    recommendations: list[str]
    question_attempts: list[QuestionAttemptResponse] = Field(default_factory=list)
