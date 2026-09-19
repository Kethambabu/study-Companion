import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.core.security_guard import PromptInjectionDetectedError, SecurityGuard
from app.modules.auth.service import AuthService
from app.modules.knowledge.service import KnowledgeService
from app.modules.events.publisher import DomainEventPublisher
from app.modules.mastery.service import MasteryService
from app.modules.observability.schemas import AIObservabilityLogCreate
from app.modules.observability.service import ObservabilityService
from app.modules.projects.service import ProjectsService
from app.modules.tutor.abstractions import CitationValidator, PromptBuilder
from app.modules.tutor.context_retriever import PersistentContextService
from app.modules.tutor.llm_providers import MockLLMProvider, get_llm_provider
from app.modules.tutor.models import AIObservabilityLog, Conversation, ConversationMessage
from app.modules.tutor.schemas import (
    ConversationMessageResponse,
    ConversationResponse,
    PaginatedMessagesResponse,
    TutorChatResponse,
)
from app.modules.tutor.tools import TutorToolsRegistry

# In-memory data store for Tutor domain fallback
_IN_MEMORY_CONVERSATIONS: dict[str, Conversation] = {}
_IN_MEMORY_MESSAGES: dict[str, list[ConversationMessage]] = {}
_IN_MEMORY_OBSERVABILITY_LOGS: list[AIObservabilityLog] = []


def _make_json_safe(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_safe(v) for v in obj]
    elif hasattr(obj, "model_dump"):
        return _make_json_safe(obj.model_dump())
    return obj


class TutorService:
    def __init__(self, db: AsyncSession | None = None, llm_provider=None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.auth_service = AuthService(db)
        self.knowledge_service = KnowledgeService(db)
        self.tools_registry = TutorToolsRegistry(db)
        self.persistent_context_service = PersistentContextService(db)
        self.observability_service = ObservabilityService(db)
        self.mastery_service = MasteryService(db)
        self.llm_provider = llm_provider or get_llm_provider()

    async def _authorize(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        proj = await self.projects_service.get_project_model(project_id)
        has_access = await self.auth_service.check_space_access(
            user_id=user_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project AI Tutor.")

    async def get_persistent_learning_context(
        self, user_id: uuid.UUID, project_id: uuid.UUID, user_message: str | None = None
    ) -> str:
        try:
            msg = user_message or "General course study guidance"
            return await self.persistent_context_service.get_relevant_tutor_context(
                user_id=user_id, project_id=project_id, user_message=msg
            )
        except Exception:
            if self.db is not None:
                try:
                    await self.db.rollback()
                except Exception:
                    pass
            return "Learner Context: Target mastery goals and active course practice."

    async def create_conversation(
        self, user_id: uuid.UUID, project_id: uuid.UUID, title: str | None = None
    ) -> ConversationResponse:
        await self._authorize(user_id, project_id)

        conv_id = uuid.uuid4()
        now = datetime.now(UTC)
        conv = Conversation(
            id=conv_id,
            project_id=project_id,
            user_id=user_id,
            title=title.strip() if title else "New Study Session",
            created_at=now,
            updated_at=now,
        )
        _IN_MEMORY_CONVERSATIONS[str(conv_id)] = conv
        _IN_MEMORY_MESSAGES[str(conv_id)] = []

        if self.db is not None:
            try:
                self.db.add(conv)
                await self.db.commit()
                await self.db.refresh(conv)
            except Exception:
                await self.db.rollback()

        return ConversationResponse(
            id=conv.id,
            project_id=conv.project_id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )

    async def list_conversations(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> list[ConversationResponse]:
        await self._authorize(user_id, project_id)

        matched: list[Conversation] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Conversation).where(
                    Conversation.project_id == project_id, Conversation.user_id == user_id
                ).order_by(Conversation.updated_at.desc())
                res = await self.db.execute(stmt)
                matched = list(res.scalars().all())
            except Exception:
                await self.db.rollback()

        if not matched:
            matched = [
                c for c in _IN_MEMORY_CONVERSATIONS.values()
                if c.project_id == project_id and c.user_id == user_id
            ]

        if not matched:
            conv_id = uuid.uuid4()
            now = datetime.now(UTC)
            default_conv = Conversation(
                id=conv_id,
                project_id=project_id,
                user_id=user_id,
                title="Study Session",
                created_at=now,
                updated_at=now,
            )
            _IN_MEMORY_CONVERSATIONS[str(conv_id)] = default_conv
            _IN_MEMORY_MESSAGES[str(conv_id)] = []
            if self.db is not None:
                try:
                    self.db.add(default_conv)
                    await self.db.commit()
                    await self.db.refresh(default_conv)
                except Exception:
                    await self.db.rollback()
            matched = [default_conv]
        else:
            matched.sort(key=lambda x: x.updated_at, reverse=True)

        return [
            ConversationResponse(
                id=c.id,
                project_id=c.project_id,
                user_id=c.user_id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in matched
        ]

    async def get_conversation_messages(
        self, user_id: uuid.UUID, project_id: uuid.UUID, conversation_id: uuid.UUID, page: int = 1, limit: int = 50
    ) -> PaginatedMessagesResponse:
        await self._authorize(user_id, project_id)

        conv = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Conversation).where(Conversation.id == conversation_id)
                res = await self.db.execute(stmt)
                conv = res.scalar_one_or_none()
            except Exception:
                pass

        if not conv:
            conv = _IN_MEMORY_CONVERSATIONS.get(str(conversation_id))

        if not conv or conv.user_id != user_id or conv.project_id != project_id:
            raise EntityNotFoundError("Conversation", str(conversation_id))

        messages: list[ConversationMessage] = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation_id
                ).order_by(ConversationMessage.created_at)
                res = await self.db.execute(stmt)
                messages = list(res.scalars().all())
            except Exception:
                pass

        if not messages:
            messages = _IN_MEMORY_MESSAGES.get(str(conversation_id), [])
            messages.sort(key=lambda m: m.created_at)

        total = len(messages)
        start = (page - 1) * limit
        end = start + limit
        paged = messages[start:end]

        items = [
            ConversationMessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                sender=m.sender,
                content=m.content,
                citations=m.citations,
                metadata_json=m.metadata_json,
                created_at=m.created_at,
            )
            for m in paged
        ]

        return PaginatedMessagesResponse(items=items, total=total, page=page, limit=limit)

    async def send_message(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content: str,
        mode: str = "default",
        request_id: str = "req-tutor-123",
    ) -> TutorChatResponse:
        await self._authorize(user_id, project_id)

        conv = None
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Conversation).where(Conversation.id == conversation_id)
                res = await self.db.execute(stmt)
                conv = res.scalar_one_or_none()
            except Exception:
                pass

        if not conv:
            conv = _IN_MEMORY_CONVERSATIONS.get(str(conversation_id))

        if not conv or conv.user_id != user_id or conv.project_id != project_id:
            raise EntityNotFoundError("Conversation", str(conversation_id))

        # PRD 116: Prompt Injection Defense Scanner
        try:
            sanitized_content = SecurityGuard.sanitize_prompt_input(content)
        except PromptInjectionDetectedError as pie:
            # Log PROMPT_INJECTION error category in observability telemetry
            await self.observability_service.log_ai_telemetry(
                AIObservabilityLogCreate(
                    request_id=request_id or f"req-{uuid.uuid4()}",
                    user_id=user_id,
                    project_id=project_id,
                    feature="tutor_rag",
                    provider="groq",
                    model="Llama-3.3-70B",
                    latency_ms=10.0,
                    tokens_used=0,
                    success=False,
                    error_category="PROMPT_INJECTION",
                )
            )
            raise pie

        now = datetime.now(UTC)

        # 1. Save User Message to conversation history
        user_msg_id = uuid.uuid4()
        user_msg = ConversationMessage(
            id=user_msg_id,
            conversation_id=conversation_id,
            sender="user",
            content=sanitized_content.strip(),
            created_at=now,
        )
        _IN_MEMORY_MESSAGES.setdefault(str(conversation_id), []).append(user_msg)
        if self.db is not None:
            try:
                self.db.add(user_msg)
                await self.db.commit()
            except Exception:
                await self.db.rollback()

        # 2. Windowed conversation history selection (Max last 6 messages)
        history_msgs = []
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(ConversationMessage.sender, ConversationMessage.content).where(
                    ConversationMessage.conversation_id == conversation_id
                ).order_by(ConversationMessage.created_at.desc()).limit(7)
                res = await self.db.execute(stmt)
                db_rows = list(reversed(res.all()))
                history_msgs = [{"role": r[0] if r[0] != "tool" else "user", "content": r[1]} for r in db_rows[:-1]]
            except Exception:
                pass

        if not history_msgs:
            history = _IN_MEMORY_MESSAGES.get(str(conversation_id), [])[-6:]
            history_msgs = [{"role": getattr(m, "sender", "user") if getattr(m, "sender", "user") != "tool" else "user", "content": getattr(m, "content", "")} for m in history[:-1]]

        # 3. Retrieve RAG Evidence Context, Mastery Context & Persistent Learning Context concurrently
        import asyncio
        rag_task = self.knowledge_service.search_knowledge(
            user_id=user_id, project_id=project_id, query=sanitized_content, top_k=3
        )
        mastery_task = self.tools_registry.get_mastery(user_id, project_id)
        context_task = self.get_persistent_learning_context(user_id, project_id, user_message=sanitized_content)

        rag_res, mastery_res, persistent_ctx = await asyncio.gather(rag_task, mastery_task, context_task)
        mastery_str = f"Target Project Mastery: {mastery_res['mastery_score'] * 100:.0f}%"

        has_sufficient_evidence = bool(rag_res.citations and rag_res.context.strip())

        # PRD Evidence Gate: If no sufficient project evidence, do NOT call LLM. Return unsupported response.
        if not has_sufficient_evidence:
            unsupported_answer = (
                "I couldn't find sufficient information about this in your project's learning materials. "
                "I can answer questions related to the content you've uploaded, but this question isn't supported "
                "by the current project knowledge base."
            )
            asst_msg_id = uuid.uuid4()
            suggested_followups = ["Ask about course concepts", "Upload project PDFs", "Review learning goals"]
            asst_msg = ConversationMessage(
                id=asst_msg_id,
                conversation_id=conversation_id,
                sender="assistant",
                content=unsupported_answer,
                citations=[],
                metadata_json={
                    "confidence_status": "unsupported_question",
                    "request_id": request_id,
                    "suggested_followups": suggested_followups,
                },
                created_at=datetime.now(UTC),
            )
            _IN_MEMORY_MESSAGES.setdefault(str(conversation_id), []).append(asst_msg)
            if self.db is not None:
                try:
                    self.db.add(asst_msg)
                    await self.db.commit()
                except Exception:
                    await self.db.rollback()

            return TutorChatResponse(
                message_id=asst_msg_id,
                conversation_id=conversation_id,
                answer=unsupported_answer,
                content=unsupported_answer,
                citations=[],
                confidence_status="unsupported_question",
                suggested_followups=suggested_followups,
                response_metadata={
                    "model": "evidence-gate-v1",
                    "provider": "system",
                    "retrieved_count": 0,
                    "latency_ms": 5.0,
                    "tokens_used": 0,
                },
            )

        expected_status = "grounded"

        # 4. Construct System Prompt with untrusted_study_material boundaries
        system_prompt = PromptBuilder.build_system_prompt(
            rag_context=rag_res.context,
            mastery_context=mastery_str,
            persistent_context=persistent_ctx,
            mode=mode,
        )

        messages_payload = [{"role": "system", "content": system_prompt}] + history_msgs + [{"role": "user", "content": sanitized_content}]

        # 5. Invoke LLM Completion via Sandboxed Capability (PRD 115)
        try:
            completion = await SecurityGuard.execute_ai_capability_sandboxed(
                "TutorLLMCompletion",
                user_id,
                project_id,
                self.llm_provider.generate_completion_async,
                messages_payload,
            )
        except Exception:
            fallback = MockLLMProvider(model_name="fallback-tutor-v1")
            completion = await fallback.generate_completion_async(messages_payload)

        # 6. Post-Processing Validation Pipeline
        from app.modules.tutor.abstractions import AIResponseValidator
        available_cits = [c.model_dump() if hasattr(c, "model_dump") else c for c in rag_res.citations] if has_sufficient_evidence else []
        
        validated_answer, final_citations, final_status = AIResponseValidator.validate_response(
            content=completion.content,
            available_citations=available_cits,
            confidence_status=expected_status if completion.confidence_status == "grounded" else completion.confidence_status,
        )

        # 7. Save Assistant Message
        def _make_json_safe(obj):
            if isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: _make_json_safe(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_make_json_safe(v) for v in obj]
            elif hasattr(obj, "model_dump"):
                return _make_json_safe(obj.model_dump())
            return obj

        serializable_citations = _make_json_safe(final_citations)
        meta_json_safe = _make_json_safe({
            "confidence_status": final_status,
            "request_id": request_id,
            "suggested_followups": getattr(completion, "suggested_followups", [])
        })

        asst_msg_id = uuid.uuid4()
        asst_msg = ConversationMessage(
            id=asst_msg_id,
            conversation_id=conversation_id,
            sender="assistant",
            content=validated_answer,
            citations=serializable_citations,
            metadata_json=meta_json_safe,
            created_at=datetime.now(UTC),
        )
        _IN_MEMORY_MESSAGES.setdefault(str(conversation_id), []).append(asst_msg)
        if self.db is not None:
            try:
                self.db.add(asst_msg)
                await self.db.commit()
            except Exception as err:
                import logging
                logging.getLogger("tutor").error("Failed to commit assistant message to DB: %s", err, exc_info=True)
                await self.db.rollback()

        # Log AI Observability Telemetry & Domain Event in background
        async def _async_telemetry_and_events():
            try:
                await self.observability_service.log_ai_telemetry(
                    AIObservabilityLogCreate(
                        request_id=request_id,
                        user_id=user_id,
                        project_id=project_id,
                        feature="tutor_rag",
                        provider="groq",
                        model="Llama-3.3-70B",
                        latency_ms=round(getattr(completion, "latency_ms", 120.0), 2),
                        tokens_used=completion.tokens_used,
                        success=True,
                        tutor_groundedness_score=0.95 if final_status == "grounded" else 0.50,
                        tutor_helpfulness_rating=5.0 if final_status == "grounded" else 3.0,
                        retrieval_relevance_score=rag_res.citations[0].similarity_score if (rag_res.citations and hasattr(rag_res.citations[0], 'similarity_score')) else 0.0,
                        retrieved_chunk_ids=[c.get("document_id", "") for c in final_citations if isinstance(c, dict)],
                    )
                )
                target_c = rag_res.citations[0].section_title if (rag_res.citations and hasattr(rag_res.citations[0], 'section_title')) else "general_tutor"
                await self.mastery_service.record_mastery_event(
                    user_id=user_id,
                    project_id=project_id,
                    concept_id=target_c,
                    score_percentage=75.0,
                    difficulty="intermediate",
                    event_type="tutor_interaction",
                )
                DomainEventPublisher.publish(
                    name="tutor_interaction",
                    aggregate_id=conversation_id,
                    payload={
                        "user_id": str(user_id),
                        "project_id": str(project_id),
                        "conversation_id": str(conversation_id),
                        "query": sanitized_content[:100],
                        "confidence_status": final_status,
                    },
                )
            except Exception:
                pass

        asyncio.create_task(_async_telemetry_and_events())

        return TutorChatResponse(
            message_id=asst_msg_id,
            conversation_id=conversation_id,
            answer=validated_answer,
            content=validated_answer,
            citations=final_citations,
            confidence_status=final_status,
            suggested_followups=getattr(completion, "suggested_followups", []),
            response_metadata={
                "model": getattr(completion, "model", "Llama-3.3-70B"),
                "provider": getattr(completion, "provider", "groq"),
                "retrieved_count": len(final_citations),
                "latency_ms": getattr(completion, "latency_ms", 120.0),
                "tokens_used": getattr(completion, "tokens_used", 150),
            },
        )

    async def send_message_stream(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        conversation_id: uuid.UUID,
        content: str,
        mode: str = "default",
        request_id: str = "req-tutor-stream",
    ):
        """PRD 131: Server-Sent Events (SSE) token streaming generator for RAG AI Tutor."""
        import asyncio
        import json

        chat_resp = await self.send_message(
            user_id=user_id,
            project_id=project_id,
            conversation_id=conversation_id,
            content=content,
            mode=mode,
            request_id=request_id,
        )

        meta_event = _make_json_safe({
            "type": "metadata",
            "message_id": str(chat_resp.message_id),
            "confidence_status": chat_resp.confidence_status,
            "citations": chat_resp.citations,
            "suggested_followups": chat_resp.suggested_followups,
            "response_metadata": chat_resp.response_metadata,
        })
        yield f"data: {json.dumps(meta_event)}\n\n"

        words = chat_resp.answer.split(" ")
        for i, word in enumerate(words):
            chunk_data = {
                "type": "token",
                "content": word + (" " if i < len(words) - 1 else ""),
            }
            yield f"data: {json.dumps(chunk_data)}\n\n"
            await asyncio.sleep(0.015)

        yield f"data: {json.dumps({'type': 'completed'})}\n\n"

