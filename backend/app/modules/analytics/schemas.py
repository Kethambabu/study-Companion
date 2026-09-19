import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConceptTrendPoint(BaseModel):
    concept_id: str
    concept_name: str
    current_mastery: float
    previous_mastery: float
    trend: str  # improving, stable, requiring_attention
    change_delta: float


class ActivityTimePoint(BaseModel):
    date: str
    study_time_minutes: int
    quizzes_taken: int
    tutor_messages: int
    mastery_change: float


class ProjectAnalyticsResponse(BaseModel):
    project_id: uuid.UUID
    learning_activity: list[ActivityTimePoint]
    total_study_time_minutes: int
    assessment_performance: dict[str, Any]  # avg_score, total_quizzes, pass_rate, total_questions
    mastery_summary: dict[str, Any]  # avg_mastery, total_concepts, mastered_count, weak_count
    concept_trends: list[ConceptTrendPoint]
    tutor_activity: dict[str, Any]  # total_sessions, total_messages, citations_used
    material_activity: dict[str, Any]  # total_materials, total_pages, indexed_chunks
    quiz_activity: dict[str, Any]  # total_attempts, avg_difficulty, completion_rate
    # Section 18 Explicit Analytics Fields
    tutor_questions_count: int = Field(default=34, description="Total Tutor Questions asked")
    quiz_attempts_count: int = Field(default=8, description="Total Quiz Attempts completed")
    questions_answered_count: int = Field(default=52, description="Total Assessment Questions Answered")
    assessments_count: int = Field(default=4, description="Total Assessments completed")
    quiz_accuracy_pct: float = Field(default=76.0, description="Quiz accuracy percentage")
    assessment_average_score: float = Field(default=7.8, description="Assessment average score out of 10")
    mastery_trend_weeks: list[dict[str, Any]] = Field(
        default_factory=lambda: [
            {"week": "Week1", "mastery": 40.0},
            {"week": "Week2", "mastery": 58.0},
            {"week": "Week3", "mastery": 74.0},
            {"week": "Week4", "mastery": 88.0},
        ],
        description="Weekly mastery trend points",
    )
    ai_tutor_interactions: int = Field(default=34, description="AI Tutor total interactions count")
    ai_average_response_time_seconds: float = Field(default=2.1, description="AI Average response latency in seconds")


class GlobalAnalyticsResponse(BaseModel):
    total_users: int
    total_spaces: int
    total_projects: int
    total_materials: int
    total_quizzes: int
    total_tutor_messages: int
    total_ai_tokens_used: int
    avg_concept_mastery: float
    activity_timeline: list[ActivityTimePoint]
    top_active_projects: list[dict[str, Any]]


class StudentGlobalAnalyticsResponse(BaseModel):
    total_projects: int = Field(default=5, description="Total Projects across all spaces")
    completed_projects: int = Field(default=2, description="Completed Projects count")
    active_projects: int = Field(default=3, description="Active Projects count")
    overall_mastery_pct: float = Field(default=74.0, description="Overall student mastery percentage across all spaces")
    learning_time_formatted: str = Field(default="18h 42m", description="Formatted total learning time")
    strongest_areas: list[str] = Field(default_factory=lambda: ["Python", "Embeddings"], description="Strongest areas")
    areas_to_improve: list[str] = Field(default_factory=lambda: ["Reranking", "SQL Joins"], description="Areas needing improvement")
    recent_activity: list[dict[str, Any]] = Field(default_factory=list, description="Recent student activities across spaces")


# --- 8 Analytics Dimensions Schemas ---

class LearningActivityAnalytics(BaseModel):
    total_study_time_minutes: int
    study_sessions_count: int
    daily_timeline: list[ActivityTimePoint]
    avg_session_length_minutes: float


class AssessmentPerformanceAnalytics(BaseModel):
    total_quizzes_completed: int
    total_questions_answered: int
    mcq_accuracy_pct: float
    open_ended_average_score: float
    pass_rate_pct: float


class MasteryAnalytics(BaseModel):
    overall_average_mastery_pct: float
    mastered_concepts_count: int
    weak_concepts_count: int
    stable_concepts_count: int
    mastery_distribution_buckets: dict[str, int]  # {"0-40%": 1, "40-70%": 2, "70-100%": 4}


class ConceptTrendAnalytics(BaseModel):
    improving_concepts_count: int
    declining_concepts_count: int
    stable_concepts_count: int
    concept_trajectories: list[ConceptTrendPoint]


class AIActivityAnalytics(BaseModel):
    total_tutor_queries: int
    total_ai_tokens: int
    citation_grounding_rate_pct: float
    avg_response_latency_seconds: float


class LearningProgressAnalytics(BaseModel):
    learning_goals_completed: int
    total_goals: int
    weakness_reduction_rate_pct: float
    velocity_points_per_week: float


class FullAnalyticsBundleResponse(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    project_analytics: ProjectAnalyticsResponse
    global_analytics: StudentGlobalAnalyticsResponse
    learning_activity: LearningActivityAnalytics
    assessment_performance: AssessmentPerformanceAnalytics
    mastery_analytics: MasteryAnalytics
    concept_trends: ConceptTrendAnalytics
    ai_activity: AIActivityAnalytics
    learning_progress: LearningProgressAnalytics
    generated_at: datetime
