import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class AdminDashboardJobsSummary(BaseModel):
    running: int = 0
    failed: int = 0


class AdminDashboardSummaryResponse(BaseModel):
    users: int
    activeUsers: int
    spaces: int
    projects: int
    materials: int
    tutorInteractions: int
    quizAttempts: int
    assessments: int
    aiRequests: int
    processingJobs: AdminDashboardJobsSummary


class AdminOverviewResponse(BaseModel):
    total_users: int
    total_spaces: int
    total_projects: int
    active_users_24h: int
    tutor_requests: int
    quiz_generations: int
    jobs_processing: int
    jobs_failed: int
    api_health: str = "✓"
    database_health: str = "✓"
    ai_provider_health: str = "✓"
    total_materials: int
    total_quizzes: int
    total_ai_tokens: int
    system_health_status: str = "healthy"


class AdminUserItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str = "Student"
    is_admin: bool
    projects_count: int = 0
    last_active: str = "Today"
    space_count: int = 0
    created_at: datetime


class AdminSpaceItem(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    owner_email: str
    project_count: int
    member_count: int
    created_at: datetime


class AdminSpaceDetailResponse(AdminSpaceItem):
    owner_name: str
    projects: list[dict[str, Any]] = Field(default_factory=list)
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)


class AdminProjectItem(BaseModel):
    id: uuid.UUID
    title: str
    space_id: uuid.UUID
    space_name: str
    owner_id: uuid.UUID
    material_count: int
    concept_count: int
    created_at: datetime


class AdminProjectDetailResponse(AdminProjectItem):
    owner_email: str
    owner_name: str
    materials_count: int
    knowledge_concepts_count: int
    tutor_activity_count: int
    quiz_activity_count: int
    assessments_count: int
    avg_mastery_pct: float
    growth_status: str
    recommendations_count: int


class AdminActivityItem(BaseModel):
    id: uuid.UUID
    event_type: str
    user_id: uuid.UUID | None = None
    user_name: str | None = None
    space_id: uuid.UUID | None = None
    space_name: str | None = None
    project_id: uuid.UUID | None = None
    project_title: str | None = None
    payload: dict[str, Any]
    created_at: datetime


class ProjectProgressItem(BaseModel):
    id: uuid.UUID
    title: str
    progress_percentage: int


class RecentActivityItem(BaseModel):
    id: uuid.UUID
    timestamp: str
    user_name: str
    activity: str
    project_title: str


class UserLearningJourneyResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    role: str
    total_projects: int
    active_projects: int
    assessments_count: int
    quiz_attempts_count: int
    tutor_chats_count: int
    overall_progress: int
    projects: list[ProjectProgressItem]
    recent_activity: list[RecentActivityItem]
    tutor_requests: int
    quiz_generations: int
    ai_evaluations: int
    concepts_improving: list[str] = Field(default_factory=list)
    concepts_requiring_attention: list[str] = Field(default_factory=list)


class EngagementTimeSeriesItem(BaseModel):
    day: str  # Mon, Tue, Wed, Thu, Fri, Sat, Sun
    date_str: str
    activity_count: int


class AdminEngagementAnalyticsResponse(BaseModel):
    daily_active_users: int
    weekly_active_users: int
    projects_created: int
    materials_uploaded: int
    tutor_conversations: int
    quiz_attempts: int
    assessments_completed: int
    activity_over_time: list[EngagementTimeSeriesItem]


class ConceptStatusDistribution(BaseModel):
    improving: int
    stable: int
    requiring_attention: int


class MasteryScoreDistribution(BaseModel):
    low_0_40: int
    mid_40_70: int
    high_70_100: int


class AdminLearningAnalyticsResponse(BaseModel):
    total_quiz_attempts: int
    avg_assessment_performance: float  # score %
    concept_status: ConceptStatusDistribution
    mastery_distribution: MasteryScoreDistribution
    mastery_changes_this_week: int
    total_learning_activity_events: int


class SystemHealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    vector_store: str
    event_stream: str
    uptime_seconds: float
    memory_usage_mb: float
    recent_failures_count: int = 0
    ai_errors_count: int = 0
    processing_failures_count: int = 0
    database_errors_count: int = 0
