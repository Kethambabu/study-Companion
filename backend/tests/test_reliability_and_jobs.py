import pytest
import uuid
from app.core.exceptions import AIProviderError, RateLimitExceededError
from app.modules.events.models import LearningEvent
from app.modules.events.processor import EventProcessor
from app.modules.events.schemas import LearningEventCreate
from app.modules.events.service import EventService
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import SignupRequest


@pytest.mark.asyncio
async def test_error_classification_retryable_vs_non_retryable():
    err_retryable = RateLimitExceededError("Groq free tier RPM limit reached.")
    assert err_retryable.status_code == 429

    err_provider = AIProviderError(provider="gemini", message="Service unavailable", status_code=503)
    assert err_provider.status_code == 503

    err_non_retryable = AIProviderError(provider="groq", message="Invalid API key", status_code=401)
    assert err_non_retryable.status_code == 401


@pytest.mark.asyncio
async def test_event_processor_retry_safety_and_idempotency():
    auth_service = AuthService()
    user = await auth_service.signup(
        SignupRequest(email="event_user@example.com", password="Password123!", full_name="Event User")
    )
    u_id = user.user.id

    event_service = EventService()

    # Create dummy space & project for authorization
    sp = await auth_service.create_space(u_id, type("Req", (), {"name": "Evt Space", "slug": "evt-space"})())
    proj = await event_service.projects_service.create_project(
        u_id, type("Req", (), {"space_id": sp.id, "name": "Evt Proj", "description": None, "learning_goal": None})()
    )

    idempotency_key = f"quiz_comp:{proj.id}:{uuid.uuid4()}"

    event_data = LearningEventCreate(
        project_id=proj.id,
        event_type="quiz_completed",
        payload={
            "quiz_id": str(uuid.uuid4()),
            "score_percentage": 85.0,
            "weak_concepts": ["consensus_protocols"],
        },
        idempotency_key=idempotency_key,
    )

    # First event publishing -> recorded & processed successfully
    evt1 = await event_service.record_event(user_id=u_id, req=event_data)
    assert evt1.status == "processed"

    # Second identical event publishing -> duplicate prevented via idempotency key
    evt2 = await event_service.record_event(user_id=u_id, req=event_data)
    assert evt2.id == evt1.id


@pytest.mark.asyncio
async def test_worker_failure_and_partial_processing_containment():
    processor = EventProcessor()
    
    corrupted_event = LearningEvent(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        event_type="unknown_corrupted_type",
        payload_json={"corrupted": True},
        status="pending",
    )

    # Process event with unknown event type gracefully without throwing unhandled exception
    res = await processor.process_event(corrupted_event)
    assert res is True
    assert corrupted_event.status == "processed"
