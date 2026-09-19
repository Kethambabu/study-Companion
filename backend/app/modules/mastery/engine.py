from typing import Any, Literal
import math
from app.modules.mastery.schemas import MasteryExplanationResponse


class DeterministicMasteryEngine:
    """Configurable, deterministic multi-evidence mastery estimation engine."""

    DIFFICULTY_MULTIPLIERS = {
        "beginner": 0.85,
        "intermediate": 1.0,
        "advanced": 1.2,
    }

    SOURCE_WEIGHTS = {
        "open_ended_assessment": 1.20,
        "quiz_attempt": 1.00,
        "repeated_mistake": 0.80,
        "tutor_interaction": 0.60,
        "material_reading": 0.40,
    }

    @classmethod
    def calculate_confidence(cls, evidence_count: int, performance_variance: float = 0.05) -> float:
        """Calculates confidence score (0.0 to 1.0) based on evidence volume and consistency."""
        if evidence_count <= 0:
            return 0.30
        volume_factor = min(0.70, 0.20 + 0.10 * evidence_count)
        consistency_factor = max(0.0, 0.30 * (1.0 - min(1.0, performance_variance * 4.0)))
        return round(min(1.0, volume_factor + consistency_factor), 2)

    @classmethod
    def calculate_growth_trend(
        cls,
        history_scores: list[float],
        current_mastery: float,
    ) -> Literal["improving", "stable", "requiring_attention"]:
        """Calculates dynamic non-hardcoded growth status based on historical trajectory slope & thresholds."""
        if len(history_scores) < 2:
            if current_mastery >= 0.70:
                return "improving"
            elif current_mastery < 0.55:
                return "requiring_attention"
            return "stable"

        # Calculate linear trajectory delta between recent average and earlier average
        half = len(history_scores) // 2
        earlier_avg = sum(history_scores[:half]) / max(1, half)
        recent_avg = sum(history_scores[half:]) / max(1, len(history_scores) - half)

        delta = recent_avg - earlier_avg

        if current_mastery < 0.55 or delta <= -0.05:
            return "requiring_attention"
        elif delta >= 0.04 or (current_mastery >= 0.75 and delta >= 0.0):
            return "improving"
        else:
            return "stable"

    @classmethod
    def calculate_new_mastery(
        cls,
        previous_mastery: float,
        score_percentage: float,
        difficulty: str = "intermediate",
        repeated_mistakes_count: int = 0,
        source_type: str = "quiz_attempt",
        alpha: float = 0.3,
        mistake_penalty: float = 0.1,
    ) -> tuple[float, float, str, dict[str, Any]]:
        """Calculates updated mastery score deterministically based on weighted evidence.

        Returns:
            (new_mastery, delta, status, evidence_json)
        """
        # 1. Normalize performance signal [0.0 to 1.0] adjusted for question difficulty & source weight
        diff_mult = cls.DIFFICULTY_MULTIPLIERS.get(difficulty.lower(), 1.0)
        source_weight = cls.SOURCE_WEIGHTS.get(source_type, 1.0)
        raw_performance = (score_percentage / 100.0) * diff_mult * (0.8 + 0.2 * source_weight)

        # 2. Calculate repeated mistakes penalty
        penalty = max(0.0, min(0.3, repeated_mistakes_count * mistake_penalty))
        effective_signal = max(0.0, min(1.0, raw_performance - penalty))

        # 3. Exponential moving average (recency smoothing)
        if previous_mastery == 0.0 and score_percentage > 0:
            # Initial assessment baseline
            new_mastery = effective_signal
        else:
            new_mastery = (1.0 - alpha) * previous_mastery + alpha * effective_signal

        new_mastery = round(max(0.0, min(1.0, new_mastery)), 4)
        delta = round(new_mastery - previous_mastery, 4)

        # 4. Classify Concept Status
        if delta >= 0.03:
            status: Literal["improving", "stable", "requiring_attention"] = "improving"
        elif new_mastery < 0.55 or delta <= -0.03:
            status = "requiring_attention"
        else:
            status = "stable"

        # 5. Build Structured Evidence Log
        evidence_json = {
            "score_percentage": score_percentage,
            "source_type": source_type,
            "source_weight": source_weight,
            "difficulty": difficulty,
            "difficulty_multiplier": diff_mult,
            "repeated_mistakes_count": repeated_mistakes_count,
            "mistake_penalty_applied": penalty,
            "effective_performance_signal": round(effective_signal, 4),
            "previous_mastery": previous_mastery,
            "new_mastery": new_mastery,
            "delta": delta,
            "status": status,
        }

        return new_mastery, delta, status, evidence_json

    @classmethod
    def generate_explanation(
        cls,
        concept_id: str,
        current_mastery: float,
        previous_mastery: float,
        delta: float,
        status: str,
        recent_events: list[dict[str, Any]],
    ) -> MasteryExplanationResponse:
        """Generates human-readable explainability rationale ('Why did this change?')."""
        if not recent_events:
            explanation = (
                f"Mastery for '{concept_id}' is initialized at {current_mastery*100:.0f}%. "
                "Complete assessment quizzes to record historical mastery trends."
            )
        elif delta > 0:
            last_event = recent_events[0]
            ev = last_event.get("evidence", {})
            score = ev.get("score_percentage", 100.0)
            diff = ev.get("difficulty", "intermediate")
            explanation = (
                f"Mastery for '{concept_id}' increased by +{delta*100:.1f}% to {current_mastery*100:.0f}%. "
                f"Reason: Strong performance ({score:.0f}%) on {diff}-level assessment questions."
            )
        elif delta < 0:
            last_event = recent_events[0]
            ev = last_event.get("evidence", {})
            penalty = ev.get("mistake_penalty_applied", 0.0)
            explanation = (
                f"Mastery for '{concept_id}' decreased by {delta*100:.1f}% to {current_mastery*100:.0f}%. "
                f"Reason: Misunderstood questions or repeated mistakes penalty ({penalty*100:.0f}%) applied."
            )
        else:
            explanation = (
                f"Mastery for '{concept_id}' remains stable at {current_mastery*100:.0f}%. "
                "Recent assessment scores matched historical baseline performance."
            )

        return MasteryExplanationResponse(
            concept_id=concept_id,
            current_mastery=current_mastery,
            previous_mastery=previous_mastery,
            delta=delta,
            status=status,  # type: ignore
            explanation=explanation,
            evidence_breakdown=recent_events,
            last_updated_at=recent_events[0]["timestamp"] if recent_events else None,  # type: ignore
        )
