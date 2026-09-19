import uuid
from typing import Literal
from app.modules.assessment.schemas import AdaptiveDecisionSchema


class AdaptiveSelectionEngine:
    """Adaptive Assessment Selection Engine combining multiple learning signals:
    Concept Mastery + Recent Mistakes + Recent Answers + Question History + Difficulty + Recent Activity.
    """

    @staticmethod
    def select_adaptive_target(
        history_attempts: list[dict],
        available_concepts: list[str],
        requested_concept_id: str | None = None,
        requested_difficulty: str = "adaptive",
        concept_mastery_map: dict[str, float] | None = None,
    ) -> AdaptiveDecisionSchema:
        """Analyzes multi-signal learner metrics to determine target concept, cognitive aspect, and difficulty level."""
        reason_signals: list[str] = []
        mastery_map = concept_mastery_map or {}

        # 1. Multi-Signal Concept Selection (Sequential Curriculum Progression + Adaptive Remediation)
        if requested_concept_id and requested_concept_id in available_concepts:
            target_concept = requested_concept_id
            reason_signals.append(f"User explicitly selected concept: '{requested_concept_id}'.")
        elif not available_concepts:
            target_concept = "general_knowledge"
            reason_signals.append("Initial session signal: Selecting introductory baseline concept.")
        else:
            # Find current position in ordered concepts
            current_concept = available_concepts[0]
            if history_attempts:
                # Find last attempted concept or highest position attempted
                attempted_set = {a.get("concept_id") for a in history_attempts if a.get("concept_id")}
                for c in available_concepts:
                    if c in attempted_set:
                        current_concept = c

            c_idx = available_concepts.index(current_concept) if current_concept in available_concepts else 0
            curr_mastery = mastery_map.get(current_concept, 0.50)

            # Sequential Advancement Rule: Advance if mastery >= 65% (0.65)
            if curr_mastery >= 0.65 and c_idx + 1 < len(available_concepts):
                target_concept = available_concepts[c_idx + 1]
                reason_signals.append(
                    f"Sequential Curriculum Advancement: Mastered '{current_concept}' ({round(curr_mastery*100)}% >= 65%). Advancing learning journey to concept '{target_concept}'."
                )
            else:
                target_concept = current_concept
                if curr_mastery < 0.65:
                    reason_signals.append(
                        f"Targeted Remediation: Concept '{current_concept}' mastery is {round(curr_mastery*100)}% (< 65%). Retaining learning position for targeted practice."
                    )
                else:
                    reason_signals.append(f"Curriculum Progression: Continuing practice on '{target_concept}'.")

        # 2. Multi-Aspect Difficulty & Remediation Strategy
        if requested_difficulty in ("beginner", "intermediate", "advanced"):
            target_difficulty: Literal["beginner", "intermediate", "advanced"] = requested_difficulty  # type: ignore
            reason_signals.append(f"Difficulty explicitly set to '{requested_difficulty}'.")
        else:
            recent_all = history_attempts[-5:] if history_attempts else []
            if not recent_all:
                target_difficulty = "beginner"
                reason_signals.append("Baseline assessment: Starting at 'beginner' difficulty.")
            else:
                overall_acc = sum(1 for a in recent_all if a.get("is_correct", False)) / len(recent_all)
                concept_recent = [a for a in history_attempts if a.get("concept_id") == target_concept][-3:]
                concept_acc = (
                    sum(1 for a in concept_recent if a.get("is_correct", False)) / len(concept_recent)
                    if concept_recent
                    else overall_acc
                )

                if concept_acc == 0.0 and len(concept_recent) >= 2:
                    # Multi-Aspect Adaptive Strategy: Learner gets concept wrong repeatedly.
                    # Maintain moderate difficulty but test a different conceptual aspect / breakdown instead of just dropping to naive easy.
                    target_difficulty = "intermediate"
                    reason_signals.append(
                        f"Multi-Aspect Adaptive Strategy: Learner repeatedly missed '{target_concept}'. Selecting question testing an alternate aspect/analogy at 'intermediate' difficulty."
                    )
                elif overall_acc >= 0.8:
                    target_difficulty = "advanced"
                    reason_signals.append(f"High overall performance ({overall_acc*100:.0f}%): Scaling to 'advanced' cognitive depth.")
                elif overall_acc >= 0.5:
                    target_difficulty = "intermediate"
                    reason_signals.append(f"Steady performance ({overall_acc*100:.0f}%): Maintained at 'intermediate' difficulty.")
                else:
                    target_difficulty = "beginner"
                    reason_signals.append(f"Scaffolding active ({overall_acc*100:.0f}%): Setting difficulty to 'beginner'.")

        return AdaptiveDecisionSchema(
            target_concept_id=target_concept,
            target_difficulty=target_difficulty,
            reason_signals=reason_signals,
        )
