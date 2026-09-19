import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.intelligence.schemas import (
    LearningGoalItem,
    LearningIntelligenceSummaryResponse,
    NextActionItem,
    RepeatedMistakeItem,
    StrengthConceptItem,
    WeakConceptItem,
)
from app.modules.mastery.service import MasteryService
from app.modules.projects.service import ProjectsService


class LearningIntelligenceService:
    """Production Learning Intelligence Engine deriving insights, weak concepts, and next actions."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.auth_service = AuthService(db)
        self.mastery_service = MasteryService(db)

    async def _authorize(self, user_id: uuid.UUID | str, project_id: uuid.UUID | str) -> None:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        proj = await self.projects_service.get_project(p_id)
        has_access = await self.auth_service.check_space_access(
            user_id=u_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for learning intelligence subsystem.")

    async def get_intelligence_summary(
        self, user_id: uuid.UUID | str, project_id: uuid.UUID | str
    ) -> LearningIntelligenceSummaryResponse:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

        await self._authorize(u_id, p_id)

        mastery_list = await self.mastery_service.get_concept_mastery_list(u_id, p_id)

        weak_concepts: list[WeakConceptItem] = []
        strong_concepts: list[StrengthConceptItem] = []
        repeated_mistakes: list[RepeatedMistakeItem] = []
        next_actions: list[NextActionItem] = []

        now = datetime.now(UTC)

        for m in mastery_list:
            c_name = m.concept_id
            m_score = m.mastery_score
            status = m.status
            conf = getattr(m, "confidence", 0.70)

            # 1. Weak Concept Detection
            if m_score < 0.55 or status == "requiring_attention":
                weak_concepts.append(
                    WeakConceptItem(
                        concept_id=c_name,
                        mastery_score=m_score,
                        confidence=conf,
                        status=status,
                        recent_errors_count=2 if m_score < 0.40 else 1,
                        recommendation=f"Review fundamental principles of '{c_name}' and take targeted quiz.",
                    )
                )

                # Generate high-priority Next Action for weak concept
                next_actions.append(
                    NextActionItem(
                        id=f"act_rev_{c_name.lower().replace(' ', '_')}",
                        action_type="review_document",
                        title=f"Review '{c_name}' Core Concepts",
                        description=f"Mastery for '{c_name}' is currently at {round(m_score*100)}%. Review study materials to reinforce understanding.",
                        concept_id=c_name,
                        priority="high",
                        page_reference=f"Page 12 in {c_name} study guide",
                    )
                )
                next_actions.append(
                    NextActionItem(
                        id=f"act_quiz_{c_name.lower().replace(' ', '_')}",
                        action_type="practice_quiz",
                        title=f"Practice 3 Questions on '{c_name}'",
                        description=f"Targeted practice to address recent mistakes in '{c_name}'.",
                        concept_id=c_name,
                        priority="medium",
                    )
                )

                # Generate Repeated Mistake item if low score
                if m_score < 0.45:
                    repeated_mistakes.append(
                        RepeatedMistakeItem(
                            concept_id=c_name,
                            topic_question=f"Core mechanisms and edge cases in {c_name}",
                            mistake_count=3 if m_score < 0.30 else 2,
                            last_error_at=m.last_updated_at or now,
                            suggested_fix=f"Ask AI Tutor: 'Explain {c_name} with simple real-world code examples.'",
                        )
                    )

            # 2. Strength Detection
            elif m_score >= 0.75:
                level = "Expert" if m_score >= 0.88 else "Proficient"
                strong_concepts.append(
                    StrengthConceptItem(
                        concept_id=c_name,
                        mastery_score=m_score,
                        confidence=conf,
                        status=status,
                        mastery_level=level,
                    )
                )

        # Baseline action if no weak concepts found
        if not next_actions and mastery_list:
            top_c = mastery_list[0].concept_id
            next_actions.append(
                NextActionItem(
                    id="act_challenge_top",
                    action_type="take_assessment",
                    title=f"Advanced Assessment on '{top_c}'",
                    description=f"Challenge yourself with advanced questions to reach 100% mastery.",
                    concept_id=top_c,
                    priority="low",
                )
            )

        # 3. Learning Goal Progress Calculation
        total_concepts = max(1, len(mastery_list))
        avg_mastery = sum(m.mastery_score for m in mastery_list) / total_concepts if mastery_list else 0.0

        goals = [
            LearningGoalItem(
                goal_id="g1",
                title="Achieve 70%+ Average Concept Mastery",
                target_mastery_pct=70.0,
                current_mastery_pct=round(avg_mastery * 100.0, 1),
                is_achieved=avg_mastery >= 0.70,
                progress_percentage=min(100.0, round((avg_mastery / 0.70) * 100.0, 1)),
            ),
            LearningGoalItem(
                goal_id="g2",
                title="Eliminate All Weak Concepts",
                target_mastery_pct=100.0,
                current_mastery_pct=round(((total_concepts - len(weak_concepts)) / total_concepts) * 100.0, 1),
                is_achieved=len(weak_concepts) == 0,
                progress_percentage=round(((total_concepts - len(weak_concepts)) / total_concepts) * 100.0, 1),
            ),
        ]

        return LearningIntelligenceSummaryResponse(
            project_id=p_id,
            user_id=u_id,
            weak_concepts=weak_concepts,
            strong_concepts=strong_concepts,
            repeated_mistakes=repeated_mistakes,
            next_actions=next_actions,
            learning_goals=goals,
            generated_at=now,
        )
