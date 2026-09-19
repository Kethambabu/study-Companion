import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class AIObservabilityLogCreate(BaseModel):
    request_id: str
    user_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    feature: str  # tutor, assessment_generation, question_evaluation, recommendation_generation, retrieval_rag
    provider: str  # groq, gemini, mock, openai
    model: str
    latency_ms: float
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost_usd: float | None = None
    success: bool = True
    error_category: str | None = None
    
    # Evaluation Metrics (PRD 92-95)
    retrieval_relevance_score: float | None = None
    retrieval_mrr: float | None = None
    retrieval_precision_at_k: float | None = None
    retrieved_chunk_ids: list[str] | None = None
    retrieval_stats: dict[str, Any] | None = None

    tutor_groundedness_score: float | None = None
    tutor_helpfulness_rating: float | None = None

    assessment_quality_score: float | None = None
    assessment_calibration_error: float | None = None

    recommendation_relevance_score: float | None = None
    recommendation_actionability_score: float | None = None


class AIObservabilityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_id: str
    user_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    feature: str
    provider: str
    model: str
    latency_ms: float
    tokens_used: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    success: bool
    error_category: str | None = None

    retrieval_relevance_score: float | None = None
    retrieval_mrr: float | None = None
    retrieval_precision_at_k: float | None = None
    tutor_groundedness_score: float | None = None
    tutor_helpfulness_rating: float | None = None
    assessment_quality_score: float | None = None
    assessment_calibration_error: float | None = None
    recommendation_relevance_score: float | None = None
    recommendation_actionability_score: float | None = None

    retrieval_stats: dict[str, Any] | None = Field(default=None, alias="retrieval_stats_json")
    created_at: datetime


class SingleAIRequestDetailResponse(AIObservabilityLogResponse):
    retrieved_chunk_ids: list[str] | None = None
    diagnostic_insights: list[str] = Field(default_factory=list)


class SlowRequestsSummaryResponse(BaseModel):
    threshold_ms: float
    slow_request_count: int
    avg_slow_latency_ms: float
    bottlenecks_by_feature: dict[str, int]
    bottlenecks_by_model: dict[str, int]
    slow_requests: list[AIObservabilityLogResponse]


class CostSummaryResponse(BaseModel):
    total_requests: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float
    cost_by_provider: dict[str, float]
    cost_by_model: dict[str, float]
    cost_by_feature: dict[str, float]


class JobLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_type: str
    status: str
    attempts: int
    duration_ms: float | None = None
    error_message: str | None = None
    payload: dict[str, Any] | None = Field(default=None, alias="payload_json")
    created_at: datetime
    completed_at: datetime | None = None


class RetrievalEvaluationMetrics(BaseModel):
    relevance_score: float  # 0.0 - 100.0%
    mrr: float  # Mean Reciprocal Rank
    precision_at_k: float  # Precision@K
    context_match_ratio: float


class TutorEvaluationMetrics(BaseModel):
    groundedness: float
    citation_correctness: float
    accuracy: float
    unsupported_handling: float
    avg_helpfulness_rating: float  # 1.0 - 5.0


class AssessmentEvaluationMetrics(BaseModel):
    question_quality: float
    grading_quality: float
    structured_output: float
    avg_calibration_error: float


class RecommendationEvaluationMetrics(BaseModel):
    relevance: float
    actionability: float
    goal_alignment: float
    adoption_rate: float


class AIEvaluationDetailsResponse(BaseModel):
    total_evaluations: int
    overall_quality_score: float
    retrieval_eval: RetrievalEvaluationMetrics
    tutor_eval: TutorEvaluationMetrics
    assessment_eval: AssessmentEvaluationMetrics
    recommendations_eval: RecommendationEvaluationMetrics


class AIEvaluationMetrics(BaseModel):
    total_requests: int
    success_rate: float
    avg_latency_ms: float
    groundedness_ratio: float
    citation_accuracy: float
    prompt_injection_attempts: int
    error_breakdown: dict[str, int]
    provider_token_share: dict[str, int]
    tutor_eval: dict[str, float]
    retrieval_eval: dict[str, float]
    assessment_eval: dict[str, float]
    recommendations_eval: dict[str, float]
