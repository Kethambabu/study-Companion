import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.intelligence.service import LearningIntelligenceService
from app.modules.mastery.service import MasteryService


class PersistentContextRetrieverEngine:
    """Selective Persistent Learning Context Retrieval Engine.
    Filters learner context to inject ONLY items relevant to the current user query.
    """

    @classmethod
    def extract_query_terms(cls, text: str) -> set[str]:
        """Extracts normalized key terms from user query."""
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {
            "what", "how", "why", "when", "where", "which", "who", "whom",
            "is", "are", "was", "were", "be", "been", "being", "have", "has",
            "had", "do", "does", "did", "can", "could", "should", "would",
            "the", "and", "a", "an", "in", "on", "of", "to", "for", "with",
            "explain", "tell", "show", "give", "example", "please", "help", "me", "about"
        }
        return set(words) - stopwords

    @classmethod
    def compute_relevance_score(cls, query_terms: set[str], context_text: str) -> float:
        """Computes keyword overlap relevance score between query terms and context snippet."""
        if not query_terms:
            return 0.10
        ctx_terms = set(re.findall(r"\b[a-zA-Z]{3,}\b", context_text.lower()))
        overlap = query_terms.intersection(ctx_terms)
        return len(overlap) / max(1, len(query_terms))

    @classmethod
    def select_relevant_learning_context(
        cls,
        user_message: str,
        weak_concepts: list[dict[str, Any]],
        strong_concepts: list[dict[str, Any]],
        repeated_mistakes: list[dict[str, Any]],
        learning_goals: list[dict[str, Any]],
        max_context_items: int = 4,
    ) -> list[str]:
        """Filters learner persistent context items and selects top N relevant lines for current message."""
        query_terms = cls.extract_query_terms(user_message)
        scored_snippets: list[tuple[float, str]] = []

        # 1. Scored Repeated Mistakes (High priority if relevant)
        for err in repeated_mistakes:
            concept = err.get("concept_id", "")
            if not concept or concept.lower() == "general knowledge":
                continue
            topic = err.get("topic_question", "")
            fix = err.get("suggested_fix", "")
            ctx_str = f"{concept} {topic} {fix}"
            rel = cls.compute_relevance_score(query_terms, ctx_str)

            snippet = (
                f"Learner Context (Known Confusion): Learner previously made repeated mistakes on '{concept}' "
                f"({topic}). Please explicitly address and contrast this topic to clear known confusion."
            )
            scored_snippets.append((rel + 0.30, snippet))

        # 2. Scored Weak Concepts
        for weak in weak_concepts:
            concept = weak.get("concept_id", "")
            if not concept or concept.lower() == "general knowledge":
                continue
            rec = weak.get("recommendation", "")
            ctx_str = f"{concept} {rec}"
            rel = cls.compute_relevance_score(query_terms, ctx_str)

            snippet = (
                f"Learner Weakness: Learner has low mastery ({round(weak.get('mastery_score', 0.4)*100)}%) in '{concept}'. "
                f"Use simpler step-by-step explanations for '{concept}' concepts."
            )
            scored_snippets.append((rel + 0.20, snippet))

        # 3. Scored Strong Concepts
        for strong in strong_concepts:
            concept = strong.get("concept_id", "")
            if not concept or concept.lower() == "general knowledge":
                continue
            ctx_str = concept
            rel = cls.compute_relevance_score(query_terms, ctx_str)

            snippet = (
                f"Learner Strength: Learner is proficient in '{concept}'. "
                f"You can use analogies comparing new concepts to '{concept}'."
            )
            scored_snippets.append((rel, snippet))

        # 4. Scored Learning Goals
        for goal in learning_goals:
            title = goal.get("title", "")
            if not title:
                continue
            rel = cls.compute_relevance_score(query_terms, title)
            snippet = f"Target Learning Goal: {title}"
            scored_snippets.append((rel, snippet))

        # Sort by relevance score descending
        scored_snippets.sort(key=lambda x: x[0], reverse=True)

        # Select top N items with relevance > 0.15
        selected = [s[1] for s in scored_snippets if s[0] >= 0.15][:max_context_items]

        return selected


class PersistentContextService:
    """Service retrieving persistent context for DB-connected Tutor sessions."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.mastery_service = MasteryService(db)
        self.intelligence_service = LearningIntelligenceService(db)

    async def get_relevant_tutor_context(
        self, user_id: uuid.UUID | str, project_id: uuid.UUID | str, user_message: str
    ) -> str:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id

        # Fetch intelligence summary
        summary = await self.intelligence_service.get_intelligence_summary(u_id, p_id)
        weak_dicts = [w.model_dump() for w in summary.weak_concepts]
        strong_dicts = [s.model_dump() for s in summary.strong_concepts]
        mistake_dicts = [m.model_dump() for m in summary.repeated_mistakes]
        goal_dicts = [g.model_dump() for g in summary.learning_goals]

        relevant_snippets = PersistentContextRetrieverEngine.select_relevant_learning_context(
            user_message=user_message,
            weak_concepts=weak_dicts,
            strong_concepts=strong_dicts,
            repeated_mistakes=mistake_dicts,
            learning_goals=goal_dicts,
            max_context_items=4,
        )

        return "\n".join(relevant_snippets)
