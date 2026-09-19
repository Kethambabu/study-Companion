import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSubmissionError, EntityNotFoundError, TenantAccessDeniedError
from app.modules.assessment.engine import AdaptiveSelectionEngine
from app.modules.assessment.evaluator import QuestionEvaluator
from app.modules.assessment.generator import QuestionGenerator
from app.modules.assessment.models import AssessmentResult, QuestionAttempt, Quiz, QuizAttempt, QuizQuestion
from app.modules.assessment.schemas import (
    OpenEndedEvaluationSchema,
    QuestionAttemptResponse,
    QuizAttemptResponse,
    QuizCreateRequest,
    QuizQuestionPublicResponse,
    QuizResponse,
    QuizSummaryResponse,
    SubmitAnswerRequest,
)
from app.modules.auth.service import AuthService
from app.modules.events.publisher import DomainEventPublisher
from app.modules.knowledge.service import KnowledgeService
from app.modules.projects.service import ProjectsService

from app.modules.mastery.service import MasteryService
from app.modules.recommendations.service import RecommendationService

# In-memory storage structures for Assessment subsystem fallback
_IN_MEMORY_QUIZZES: dict[str, Quiz] = {}
_IN_MEMORY_QUESTIONS: dict[str, list[QuizQuestion]] = {}
_IN_MEMORY_ATTEMPTS: dict[str, QuizAttempt] = {}
_IN_MEMORY_Q_ATTEMPTS: dict[str, list[QuestionAttempt]] = {}
_IN_MEMORY_RESULTS: dict[str, AssessmentResult] = {}


class AssessmentService:
    """Production Adaptive Assessment Domain Service."""

    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.auth_service = AuthService(db)
        self.knowledge_service = KnowledgeService(db)
        self.mastery_service = MasteryService(db)
        self.recommendations_service = RecommendationService(db)

    async def _authorize(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        proj = await self.projects_service.get_project_model(project_id)
        has_access = await self.auth_service.check_space_access(
            user_id=user_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project assessment subsystem.")

    async def _bg_generate_recommendations(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        try:
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as bg_db:
                rec_svc = RecommendationService(bg_db)
                await rec_svc.generate_recommendations(user_id=user_id, project_id=project_id)
        except Exception:
            try:
                rec_svc = RecommendationService(None)
                await rec_svc.generate_recommendations(user_id=user_id, project_id=project_id)
            except Exception:
                pass

    async def get_learning_progress(self, user_id: uuid.UUID, project_id: uuid.UUID) -> dict[str, Any]:
        await self._authorize(user_id, project_id)
        concepts_res = await self.knowledge_service.list_project_concepts(user_id=user_id, project_id=project_id)
        available_concepts = [c.name for c in concepts_res] if concepts_res else ["Core Concepts"]

        masteries = await self.mastery_service.get_concept_mastery_list(user_id=user_id, project_id=project_id)
        mastery_map = {m.concept_id: m.mastery_score for m in masteries}

        completed = [c for c in available_concepts if mastery_map.get(c, 0.0) >= 0.65]

        # Determine current concept position
        curr_concept = available_concepts[0]
        curr_pos = 1
        for idx, c in enumerate(available_concepts):
            if mastery_map.get(c, 0.0) >= 0.65:
                if idx + 1 < len(available_concepts):
                    curr_concept = available_concepts[idx + 1]
                    curr_pos = idx + 2
            else:
                curr_concept = c
                curr_pos = idx + 1
                break

        return {
            "project_id": str(project_id),
            "user_id": str(user_id),
            "current_concept_id": curr_concept,
            "current_position": curr_pos,
            "total_concepts": len(available_concepts),
            "completed_concepts": completed,
            "all_concepts": available_concepts,
            "learning_status": "completed" if len(completed) == len(available_concepts) else "in_progress",
        }

    async def create_quiz(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        req: QuizCreateRequest,
    ) -> QuizResponse:
        await self._authorize(user_id, project_id)

        # 1. Fetch learning progress & ordered concept list
        progress = await self.get_learning_progress(user_id=user_id, project_id=project_id)
        available_concept_ids = progress["all_concepts"]

        # 2. Collect historical user question attempts & compute mastery map
        history_attempts: list[dict] = []
        concept_scores_hist: dict[str, list[float]] = {}
        for att in _IN_MEMORY_Q_ATTEMPTS.values():
            for qa in att:
                attempt_obj = _IN_MEMORY_ATTEMPTS.get(str(qa.attempt_id))
                if attempt_obj and attempt_obj.user_id == user_id and attempt_obj.project_id == project_id:
                    q_list = _IN_MEMORY_QUESTIONS.get(str(attempt_obj.quiz_id), [])
                    matched_q = next((q for q in q_list if q.id == qa.question_id), None)
                    if matched_q:
                        history_attempts.append({
                            "concept_id": matched_q.concept_id,
                            "is_correct": qa.is_correct,
                            "difficulty": matched_q.difficulty,
                        })
                        concept_scores_hist.setdefault(matched_q.concept_id, []).append(qa.score_percentage)

        concept_mastery_map: dict[str, float] = {}
        for c_id in available_concept_ids:
            scores = concept_scores_hist.get(c_id, [])
            concept_mastery_map[c_id] = round(sum(scores) / (len(scores) * 100.0), 2) if scores else 0.50

        # 3. Sequential Adaptive Engine decision
        adaptive_decision = AdaptiveSelectionEngine.select_adaptive_target(
            history_attempts=history_attempts,
            available_concepts=available_concept_ids,
            requested_concept_id=req.target_concept_id or progress["current_concept_id"],
            requested_difficulty=req.difficulty_preference,
            concept_mastery_map=concept_mastery_map,
        )

        # Collect existing question fingerprints across project to prevent duplicates
        used_fingerprints: set[str] = set()
        for q_list in _IN_MEMORY_QUESTIONS.values():
            for q_item in q_list:
                used_fingerprints.add(QuestionGenerator.compute_fingerprint(q_item.question_text))

        # 4. Search study context text snippet for target concept
        rag_res = await self.knowledge_service.search_knowledge(
            user_id=user_id, project_id=project_id, query=adaptive_decision.target_concept_id, top_k=2
        )
        study_context = rag_res.context if rag_res and rag_res.context else f"Study material for {adaptive_decision.target_concept_id}."

        # 5. Generate Questions (Mix of MCQ and Open-ended with Fingerprint Deduplication)
        quiz_id = uuid.uuid4()
        now = datetime.now(UTC)
        quiz_title = req.title or f"Learning Journey: Concept {progress['current_position']}/{progress['total_concepts']} - {adaptive_decision.target_concept_id.title()}"

        quiz = Quiz(
            id=quiz_id,
            project_id=project_id,
            user_id=user_id,
            title=quiz_title,
            description=f"Sequential learning assessment targeting {adaptive_decision.target_concept_id} at {adaptive_decision.target_difficulty} difficulty. Signals: {'; '.join(adaptive_decision.reason_signals)}",
            target_concept_id=adaptive_decision.target_concept_id,
            created_at=now,
        )

        questions: list[QuizQuestion] = []
        num_q = req.num_questions
        variation_seed = len(_IN_MEMORY_QUIZZES) * 3 + int(quiz_id.hex[:4], 16)
        for i in range(num_q):
            # Alternating MCQ and Open-ended questions
            q_type = "mcq" if i % 2 == 0 else "open_ended"
            
            # Semantic Deduplication Retry Loop
            gen_q = None
            for retry in range(10):
                candidate_q = QuestionGenerator.generate_question(
                    concept_id=adaptive_decision.target_concept_id,
                    difficulty=adaptive_decision.target_difficulty,
                    question_type=q_type,  # type: ignore
                    study_context=study_context,
                    question_index=i,
                    variation_seed=variation_seed + retry * 7,
                )
                fp = QuestionGenerator.compute_fingerprint(candidate_q.question_text)
                if fp not in used_fingerprints:
                    used_fingerprints.add(fp)
                    gen_q = candidate_q
                    break

            if not gen_q:
                gen_q = candidate_q  # Fallback to last generated

            q_obj = QuizQuestion(
                id=uuid.uuid4(),
                quiz_id=quiz_id,
                question_type=gen_q.question_type,
                question_text=gen_q.question_text,
                options=gen_q.options,
                correct_answer=gen_q.correct_answer,
                concept_id=gen_q.concept_id,
                difficulty=gen_q.difficulty,
                explanation=gen_q.explanation,
                order_index=i + 1,
            )
            questions.append(q_obj)

        _IN_MEMORY_QUIZZES[str(quiz_id)] = quiz
        _IN_MEMORY_QUESTIONS[str(quiz_id)] = questions

        if self.db is not None:
            try:
                self.db.add(quiz)
                for q_item in questions:
                    self.db.add(q_item)
                await self.db.commit()
                await self.db.refresh(quiz)
            except Exception:
                await self.db.rollback()

        # Public response conceals correct answers during active quiz session display!
        public_questions = [
            QuizQuestionPublicResponse(
                id=q.id,
                question_type=q.question_type,
                question_text=q.question_text,
                options=q.options,
                concept_id=q.concept_id,
                difficulty=q.difficulty,
                order_index=q.order_index,
            )
            for q in questions
        ]

        return QuizResponse(
            id=quiz.id,
            project_id=quiz.project_id,
            user_id=quiz.user_id,
            title=quiz.title,
            description=quiz.description,
            target_concept_id=quiz.target_concept_id,
            questions=public_questions,
            created_at=quiz.created_at,
        )

    async def list_quizzes(self, user_id: uuid.UUID, project_id: uuid.UUID) -> list[QuizResponse]:
        await self._authorize(user_id, project_id)
        matched_map: dict[str, Quiz] = {k: v for k, v in _IN_MEMORY_QUIZZES.items() if v.project_id == project_id and v.user_id == user_id}

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Quiz).where(Quiz.project_id == project_id, Quiz.user_id == user_id).order_by(Quiz.created_at.desc())
                res = await self.db.execute(stmt)
                db_quizzes = res.scalars().all()
                for qz in db_quizzes:
                    matched_map[str(qz.id)] = qz
            except Exception:
                pass

        matched = list(matched_map.values())
        matched.sort(key=lambda x: x.created_at, reverse=True)

        quiz_questions_map: dict[str, list[QuizQuestion]] = {}
        if self.db is not None and matched:
            try:
                from sqlalchemy import select
                quiz_ids = [q.id for q in matched]
                stmt = select(QuizQuestion).where(QuizQuestion.quiz_id.in_(quiz_ids)).order_by(QuizQuestion.order_index)
                q_res = await self.db.execute(stmt)
                for qq in q_res.scalars().all():
                    quiz_questions_map.setdefault(str(qq.quiz_id), []).append(qq)
            except Exception:
                pass

        res: list[QuizResponse] = []
        for q in matched:
            q_list = quiz_questions_map.get(str(q.id))
            if not q_list:
                q_list = _IN_MEMORY_QUESTIONS.get(str(q.id), [])

            public_q = [
                QuizQuestionPublicResponse(
                    id=item.id,
                    question_type=item.question_type,
                    question_text=item.question_text,
                    options=item.options,
                    concept_id=item.concept_id,
                    difficulty=item.difficulty,
                    order_index=item.order_index,
                )
                for item in q_list
            ]
            res.append(
                QuizResponse(
                    id=q.id,
                    project_id=q.project_id,
                    user_id=q.user_id,
                    title=q.title,
                    description=q.description,
                    target_concept_id=q.target_concept_id,
                    questions=public_q,
                    created_at=q.created_at,
                )
            )
        return res

    async def start_or_get_attempt(
        self, user_id: uuid.UUID, project_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> tuple[QuizResponse, QuizAttemptResponse]:
        await self._authorize(user_id, project_id)

        quiz = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Quiz).where(Quiz.id == quiz_id)
                res = await self.db.execute(stmt)
                quiz = res.scalar_one_or_none()
            except Exception:
                pass

        if not quiz:
            quiz = _IN_MEMORY_QUIZZES.get(str(quiz_id))

        if not quiz or str(quiz.project_id) != str(project_id) or str(quiz.user_id) != str(user_id):
            raise EntityNotFoundError("Quiz", str(quiz_id))

        q_list: list[QuizQuestion] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index)
                res = await self.db.execute(stmt)
                q_list = list(res.scalars().all())
            except Exception:
                pass

        if not q_list:
            q_list = _IN_MEMORY_QUESTIONS.get(str(quiz_id), [])

        # Check for active in-progress attempt for safe refresh recovery
        existing_attempt = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizAttempt).where(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.user_id == user_id,
                    QuizAttempt.status == "in_progress"
                )
                res = await self.db.execute(stmt)
                existing_attempt = res.scalar_one_or_none()
            except Exception:
                pass

        if not existing_attempt:
            existing_attempt = next(
                (
                    a for a in _IN_MEMORY_ATTEMPTS.values()
                    if str(a.quiz_id) == str(quiz_id) and str(a.user_id) == str(user_id) and a.status == "in_progress"
                ),
                None,
            )

        if not existing_attempt:
            att_id = uuid.uuid4()
            now = datetime.now(UTC)
            attempt = QuizAttempt(
                id=att_id,
                quiz_id=quiz_id,
                project_id=project_id,
                user_id=user_id,
                status="in_progress",
                started_at=now,
                score=0.0,
                max_score=float(len(q_list) * 100),
            )
            _IN_MEMORY_ATTEMPTS[str(att_id)] = attempt
            _IN_MEMORY_Q_ATTEMPTS[str(att_id)] = []

            if self.db is not None:
                try:
                    self.db.add(attempt)
                    await self.db.commit()
                    await self.db.refresh(attempt)
                except Exception:
                    await self.db.rollback()
        else:
            attempt = existing_attempt

        q_attempts: list[QuestionAttempt] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuestionAttempt).where(QuestionAttempt.attempt_id == attempt.id)
                res = await self.db.execute(stmt)
                q_attempts = list(res.scalars().all())
            except Exception:
                pass

        if not q_attempts:
            q_attempts = _IN_MEMORY_Q_ATTEMPTS.get(str(attempt.id), [])

        submitted_ids = [qa.question_id for qa in q_attempts]
        curr_index = len(submitted_ids)

        public_q = [
            QuizQuestionPublicResponse(
                id=item.id,
                question_type=item.question_type,
                question_text=item.question_text,
                options=item.options,
                concept_id=item.concept_id,
                difficulty=item.difficulty,
                order_index=item.order_index,
            )
            for item in q_list
        ]

        quiz_resp = QuizResponse(
            id=quiz.id,
            project_id=quiz.project_id,
            user_id=quiz.user_id,
            title=quiz.title,
            description=quiz.description,
            target_concept_id=quiz.target_concept_id,
            questions=public_q,
            created_at=quiz.created_at,
        )

        att_resp = QuizAttemptResponse(
            id=attempt.id,
            quiz_id=attempt.quiz_id,
            project_id=attempt.project_id,
            user_id=attempt.user_id,
            status=attempt.status,
            started_at=attempt.started_at,
            completed_at=attempt.completed_at,
            score=attempt.score,
            max_score=attempt.max_score,
            current_question_index=curr_index,
            submitted_question_ids=submitted_ids,
        )

        return quiz_resp, att_resp

    async def submit_answer(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        quiz_id: uuid.UUID,
        attempt_id: uuid.UUID,
        question_id: uuid.UUID,
        req: SubmitAnswerRequest,
    ) -> QuestionAttemptResponse:
        await self._authorize(user_id, project_id)

        attempt = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizAttempt).where(QuizAttempt.id == attempt_id)
                res = await self.db.execute(stmt)
                attempt = res.scalar_one_or_none()
            except Exception:
                pass

        if not attempt:
            attempt = _IN_MEMORY_ATTEMPTS.get(str(attempt_id))

        if not attempt or str(attempt.user_id) != str(user_id) or str(attempt.project_id) != str(project_id):
            raise EntityNotFoundError("QuizAttempt", str(attempt_id))

        if attempt.status == "completed":
            raise DuplicateSubmissionError("This quiz attempt is already completed.")

        question = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizQuestion).where(QuizQuestion.id == question_id)
                res = await self.db.execute(stmt)
                question = res.scalar_one_or_none()
            except Exception:
                pass

        if not question:
            q_list = _IN_MEMORY_QUESTIONS.get(str(quiz_id), [])
            question = next((q for q in q_list if q.id == question_id), None)

        if not question:
            raise EntityNotFoundError("QuizQuestion", str(question_id))

        # Check duplicate answer submission defense
        existing_q_attempts: list[QuestionAttempt] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuestionAttempt).where(
                    QuestionAttempt.attempt_id == attempt_id,
                    QuestionAttempt.question_id == question_id
                )
                res = await self.db.execute(stmt)
                existing_q_attempts = list(res.scalars().all())
            except Exception:
                pass

        if not existing_q_attempts:
            existing_q_attempts = _IN_MEMORY_Q_ATTEMPTS.get(str(attempt_id), [])

        if any(qa.question_id == question_id for qa in existing_q_attempts):
            raise DuplicateSubmissionError(f"Answer has already been submitted for question '{question_id}'.")

        # Evaluate Answer
        if question.question_type == "mcq":
            is_correct, score_pct, feedback_data = QuestionEvaluator.evaluate_mcq(
                user_answer=req.user_answer,
                correct_answer=question.correct_answer,
                explanation=question.explanation,
            )
        else:
            eval_schema: OpenEndedEvaluationSchema = QuestionEvaluator.evaluate_open_ended(
                question_text=question.question_text,
                user_answer=req.user_answer,
                correct_answer_criteria=question.correct_answer,
                concept_id=question.concept_id,
            )
            is_correct = eval_schema.is_correct
            score_pct = eval_schema.score_percentage
            feedback_data = eval_schema.model_dump()

        # 1. Fetch concept mastery BEFORE evaluating this attempt (fast single-concept lookup)
        m_before_val = 50
        try:
            m_before_score = await self.mastery_service.get_single_concept_mastery(
                user_id=user_id, project_id=project_id, concept_id=question.concept_id
            )
            m_before_val = round(m_before_score * 100)
        except Exception:
            pass

        # 2. Record mastery event deterministically via MasteryService
        m_after_val = m_before_val
        try:
            updated_m = await self.mastery_service.record_mastery_event(
                user_id=user_id,
                project_id=project_id,
                concept_id=question.concept_id,
                score_percentage=score_pct,
                difficulty=question.difficulty,
                event_type="open_ended_assessment" if question.question_type == "open_ended" else "quiz_attempt",
                assessment_id=str(quiz_id),
            )
            m_after_val = round(updated_m.mastery_score * 100)
        except Exception:
            pass

        feedback_data["mastery_before"] = m_before_val
        feedback_data["mastery_after"] = m_after_val
        feedback_data["mastery_delta_str"] = f"{m_before_val}% -> {m_after_val}%"
        feedback_data["concept_id"] = question.concept_id

        qa_id = uuid.uuid4()
        now = datetime.now(UTC)
        qa_obj = QuestionAttempt(
            id=qa_id,
            attempt_id=attempt_id,
            question_id=question_id,
            user_answer=req.user_answer,
            is_correct=is_correct,
            score_percentage=score_pct,
            feedback_json=feedback_data,
            submitted_at=now,
        )
        _IN_MEMORY_Q_ATTEMPTS.setdefault(str(attempt_id), []).append(qa_obj)

        # Update attempt score aggregate
        attempt.score += score_pct
        _IN_MEMORY_ATTEMPTS[str(attempt_id)] = attempt

        if self.db is not None:
            try:
                await self.db.merge(attempt)
                self.db.add(qa_obj)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        # Publish domain events & update recommendations
        try:
            DomainEventPublisher.publish(
                name="question_answered",
                aggregate_id=question_id,
                payload={
                    "user_id": str(user_id),
                    "project_id": str(project_id),
                    "quiz_id": str(quiz_id),
                    "attempt_id": str(attempt_id),
                    "question_id": str(question_id),
                    "concept_id": question.concept_id,
                    "is_correct": is_correct,
                    "score_percentage": score_pct,
                },
            )
            import asyncio
            asyncio.create_task(self._bg_generate_recommendations(user_id, project_id))
        except Exception:
            pass

        return QuestionAttemptResponse(
            id=qa_obj.id,
            attempt_id=qa_obj.attempt_id,
            question_id=qa_obj.question_id,
            user_answer=qa_obj.user_answer,
            is_correct=qa_obj.is_correct,
            score_percentage=qa_obj.score_percentage,
            explanation=question.explanation,
            correct_answer=question.correct_answer,  # Revealed ONLY AFTER answer submission!
            feedback=feedback_data,
            submitted_at=qa_obj.submitted_at,
        )

    async def finish_attempt(
        self, user_id: uuid.UUID, project_id: uuid.UUID, quiz_id: uuid.UUID, attempt_id: uuid.UUID
    ) -> QuizSummaryResponse:
        await self._authorize(user_id, project_id)

        attempt = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizAttempt).where(QuizAttempt.id == attempt_id)
                res = await self.db.execute(stmt)
                attempt = res.scalar_one_or_none()
            except Exception:
                pass

        if not attempt:
            attempt = _IN_MEMORY_ATTEMPTS.get(str(attempt_id))

        if not attempt or str(attempt.user_id) != str(user_id) or str(attempt.project_id) != str(project_id):
            raise EntityNotFoundError("QuizAttempt", str(attempt_id))

        now = datetime.now(UTC)
        attempt.status = "completed"
        attempt.completed_at = now
        _IN_MEMORY_ATTEMPTS[str(attempt_id)] = attempt

        q_list: list[QuizQuestion] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id).order_by(QuizQuestion.order_index)
                res = await self.db.execute(stmt)
                q_list = list(res.scalars().all())
            except Exception:
                pass

        if not q_list:
            q_list = _IN_MEMORY_QUESTIONS.get(str(quiz_id), [])

        q_attempts: list[QuestionAttempt] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(QuestionAttempt).where(QuestionAttempt.attempt_id == attempt_id)
                res = await self.db.execute(stmt)
                q_attempts = list(res.scalars().all())
            except Exception:
                pass

        if not q_attempts:
            q_attempts = _IN_MEMORY_Q_ATTEMPTS.get(str(attempt_id), [])

        # Build concepts breakdown
        concepts_tested: dict[str, Any] = {}
        weak_set: set[str] = set()
        strong_set: set[str] = set()

        for qa in q_attempts:
            q_match = next((q for q in q_list if q.id == qa.question_id), None)
            c_id = q_match.concept_id if q_match else "general"
            concepts_tested.setdefault(c_id, []).append(qa.score_percentage)

        for c_id, scores in concepts_tested.items():
            avg = sum(scores) / len(scores)
            if avg >= 75.0:
                strong_set.add(c_id)
            else:
                weak_set.add(c_id)

        recommendations = []
        if weak_set:
            recommendations.append(f"Review study material for weak concepts: {', '.join(weak_set)}.")
            recommendations.append("Ask the AI Tutor to 'explain simpler' or 'give an example' for missed questions.")
        else:
            recommendations.append("Excellent mastery! Proceed to advanced topics or generate another adaptive quiz.")

        res_id = uuid.uuid4()
        res_obj = AssessmentResult(
            id=res_id,
            attempt_id=attempt_id,
            project_id=project_id,
            user_id=user_id,
            overall_score=attempt.score,
            concepts_tested=concepts_tested,
            weak_concepts=list(weak_set),
            strong_concepts=list(strong_set),
            recommendations=recommendations,
            created_at=now,
        )
        _IN_MEMORY_RESULTS[str(attempt_id)] = res_obj

        if self.db is not None:
            try:
                self.db.add(res_obj)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        # Publish quiz_completed learning domain event
        DomainEventPublisher.publish(
            name="quiz_completed",
            aggregate_id=quiz_id,
            payload={
                "user_id": str(user_id),
                "project_id": str(project_id),
                "attempt_id": str(attempt_id),
                "score_percentage": (attempt.score / max(attempt.max_score, 1.0)) * 100.0,
                "weak_concepts": list(weak_set),
            },
        )

        qa_responses: list[QuestionAttemptResponse] = []
        for qa in q_attempts:
            q_match = next((q for q in q_list if q.id == qa.question_id), None)
            qa_responses.append(
                QuestionAttemptResponse(
                    id=qa.id,
                    attempt_id=qa.attempt_id,
                    question_id=qa.question_id,
                    user_answer=qa.user_answer,
                    is_correct=qa.is_correct,
                    score_percentage=qa.score_percentage,
                    explanation=q_match.explanation if q_match else "",
                    correct_answer=q_match.correct_answer if q_match else "",
                    feedback=qa.feedback_json,
                    submitted_at=qa.submitted_at,
                )
            )

        pct = (attempt.score / max(attempt.max_score, 1.0)) * 100.0 if attempt.max_score > 0 else 0.0

        return QuizSummaryResponse(
            attempt_id=attempt.id,
            quiz_id=quiz_id,
            project_id=project_id,
            overall_score=attempt.score,
            max_score=attempt.max_score,
            score_percentage=round(pct, 1),
            status=attempt.status,
            completed_at=attempt.completed_at,
            concepts_tested=concepts_tested,
            weak_concepts=list(weak_set),
            strong_concepts=list(strong_set),
            recommendations=recommendations,
            question_attempts=qa_responses,
        )

    async def get_summary(
        self, user_id: uuid.UUID, project_id: uuid.UUID, quiz_id: uuid.UUID, attempt_id: uuid.UUID
    ) -> QuizSummaryResponse:
        return await self.finish_attempt(user_id, project_id, quiz_id, attempt_id)
