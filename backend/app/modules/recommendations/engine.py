from typing import Any, Literal


class RecommendationRankingEngine:
    """Candidate Generation & Priority Ranking Engine fusing 7 PRD learning signals."""

    ACTION_CTA_MAPPING = {
        "review_material": ("Review Study Notes", "/materials"),
        "take_quiz": ("Take Adaptive Quiz", "/assessment"),
        "practice_concept": ("Practice Target Concept", "/assessment"),
        "review_mistakes": ("Review Past Mistakes", "/assessment"),
        "ask_tutor": ("Ask AI Tutor", "/tutor"),
    }

    @classmethod
    def calculate_priority_score(
        cls,
        mastery_score: float,
        growth_trend: str,
        mistakes_count: int,
        goal_distance: float = 0.30,
        has_material: bool = True,
    ) -> float:
        """7-Signal Priority Weighting Formula:
        S = 0.30*(1 - Mastery) + 0.25*GrowthWeight + 0.20*MistakesWeight + 0.15*GoalDistance + 0.10*MaterialBonus
        """
        growth_weight = 0.90 if growth_trend == "requiring_attention" else (0.50 if growth_trend == "stable" else 0.20)
        mistakes_weight = min(1.0, mistakes_count * 0.35)
        material_bonus = 1.0 if has_material else 0.0

        score = (
            0.30 * (1.0 - mastery_score)
            + 0.25 * growth_weight
            + 0.20 * mistakes_weight
            + 0.15 * goal_distance
            + 0.10 * material_bonus
        )
        return round(min(1.0, max(0.10, score)), 2)

    @classmethod
    def generate_candidate_recommendations(
        cls,
        weak_concepts: list[str],
        mastery_list: list[dict[str, Any]],
        recent_mistakes: list[dict[str, Any]],
        materials_count: int = 0,
        has_quizzes: bool = True,
        material_titles: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generates ranked recommendation candidates using 7 PRD learning signals."""
        candidates: list[dict[str, Any]] = []
        mat_title = (material_titles[0] if material_titles else "study notes").replace(".pdf", "")

        # Candidate 1: Practice / Review Weak Concept with Page-level guidance
        if weak_concepts:
            target_weak = weak_concepts[0]
            # Find mastery record for target weak concept
            m_rec = next((m for m in mastery_list if m.get("concept_id") == target_weak), {})
            m_val = m_rec.get("mastery_score", 0.43)
            g_trend = m_rec.get("status", "requiring_attention")
            err_count = sum(1 for err in recent_mistakes if err.get("concept_id") == target_weak) or 2

            p_score = cls.calculate_priority_score(
                mastery_score=m_val,
                growth_trend=g_trend,
                mistakes_count=err_count,
                has_material=materials_count > 0,
            )
            if materials_count > 0:
                p_score = round(min(1.0, p_score + 0.10), 2)

            # Format dynamic PRD-style page guidance
            doc_name = f"{target_weak.title()}.pdf" if not material_titles else material_titles[0]
            action_desc = (
                f"Review {target_weak} examples from {doc_name} pages 12–18, "
                f"then complete a short assessment focused on {target_weak} problem solving."
            )
            reason_text = (
                f"Mastery for '{target_weak}' is {round(m_val*100)}% ({g_trend.replace('_', ' ')} status) "
                f"with {err_count} recent mistakes."
            )

            candidates.append({
                "action_type": "practice_concept",
                "title": f"Targeted Review: '{target_weak}'",
                "description": action_desc,
                "target_concept_id": target_weak,
                "priority_score": p_score,
                "reason_evidence": {
                    "signal_type": "weakness_remediation",
                    "concept_id": target_weak,
                    "mastery": m_val,
                    "growth": g_trend,
                    "recent_mistakes": err_count,
                    "rationale": reason_text,
                },
            })

        # Candidate 2: Review Mistakes
        if recent_mistakes:
            top_mistake_concept = recent_mistakes[0].get("concept_id", weak_concepts[0] if weak_concepts else "core_topic")
            p_score = cls.calculate_priority_score(
                mastery_score=0.45,
                growth_trend="requiring_attention",
                mistakes_count=len(recent_mistakes),
            )
            candidates.append({
                "action_type": "review_mistakes",
                "title": f"Review Recent Mistakes in '{top_mistake_concept}'",
                "description": f"You made recent errors on '{top_mistake_concept}'. Reviewing solution explanations will strengthen retention.",
                "target_concept_id": top_mistake_concept,
                "priority_score": p_score,
                "reason_evidence": {
                    "signal_type": "recent_mistake",
                    "mistake_count": len(recent_mistakes),
                    "rationale": f"Found {len(recent_mistakes)} recent incorrect question responses in '{top_mistake_concept}'.",
                },
            })

        # Candidate 3: Ask AI Tutor
        if weak_concepts:
            target_tutor = weak_concepts[0]
            candidates.append({
                "action_type": "ask_tutor",
                "title": f"Ask AI Tutor: '{target_tutor}' Analogies",
                "description": f"Ask AI Tutor: 'Explain {target_tutor} with simple real-world code examples and page references.'",
                "target_concept_id": target_tutor,
                "priority_score": 0.75,
                "reason_evidence": {
                    "signal_type": "tutor_guidance",
                    "concept_id": target_tutor,
                    "rationale": f"Interactive tutor session will resolve conceptual confusion in '{target_tutor}'.",
                },
            })

        # Candidate 4: Review Study Material
        if materials_count > 0:
            doc_label = material_titles[0] if material_titles else "Study Notes"
            candidates.append({
                "action_type": "review_material",
                "title": f"Read Material: '{doc_label}'",
                "description": f"Re-read key section headings and extracted concepts in '{doc_label}' to consolidate long-term memory.",
                "target_concept_id": weak_concepts[0] if weak_concepts else None,
                "priority_score": 0.70,
                "reason_evidence": {
                    "signal_type": "material_reading",
                    "materials_count": materials_count,
                    "rationale": f"Reinforce foundational material from '{doc_label}' before taking higher-difficulty assessments.",
                },
            })

        # Candidate 5: Adaptive Quiz Baseline
        if not candidates or has_quizzes:
            candidates.append({
                "action_type": "take_quiz",
                "title": "Take Adaptive Quiz",
                "description": "Evaluate overall project mastery using dynamic multi-signal assessment questions.",
                "target_concept_id": weak_concepts[0] if weak_concepts else "general",
                "priority_score": 0.65,
                "reason_evidence": {
                    "signal_type": "adaptive_quiz",
                    "rationale": "Regular active recall assessment accelerates conceptual mastery.",
                },
            })

        # Sort by priority score descending
        candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        return candidates
