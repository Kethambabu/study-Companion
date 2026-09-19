# Event-Driven Architecture & Background Job Processing

## Overview

AI Prof utilizes an asynchronous, event-driven domain architecture (`learning_events`) to decouple user-facing HTTP request/response loops from background processing workflows (quiz evaluation, mastery updates, weakness detection, recommendation ranking, and analytics aggregation).

## Domain Events Lifecycle

```text
quiz_completed
    │
    ├──> Evaluation Worker
    ├──> Mastery Engine Update
    ├──> Weakness Detection
    ├──> Growth Snapshot Generator
    ├──> Recommendation Engine Ranking
    └──> Analytics Telemetry Aggregation
```

### Event Schema Requirements
Every event emitted into the learning workflow contains:
- `event_id`: Unique UUID identifier.
- `user_id`: Target learner ID.
- `project_id`: Target project scope.
- `event_type`: Domain event name (e.g., `material_processed`, `quiz_completed`).
- `payload_json`: Dictionary payload.
- `status`: Processing state (`pending`, `processed`, `failed`).
- `idempotency_key`: Deduplication key (e.g., `quiz_attempt_id_mastery`).
- `timestamp`: Event creation timestamp.

## Idempotency & Retry Safety

1. **Deduplication**: `LearningEventService` checks `idempotency_key` prior to recording or triggering downstream events. Duplicate events are silently ignored.
2. **Worker Retries**: Jobs use exponential backoff (`retries=3`, backoff factor $2.0$).
3. **Error Classification**:
   - **Retryable Errors**: HTTP 429 RateLimit, HTTP 503 Service Unavailable, Database Lock Wait Timeout.
   - **Non-Retryable Errors**: HTTP 401 Unauthorized, HTTP 422 Validation Error.
