# Background Worker Subsystem (`workers/`)

This directory houses the asynchronous task queue subsystem for AI Prof, powered by **Celery** and **Redis**. It handles computationally intensive and I/O-bound background operations out-of-band from the main FastAPI HTTP request-response cycle.

---

## Architecture Overview

```
+------------------+         +-----------------+         +-------------------+
|  FastAPI App     |  --->   |  Redis Broker   |  --->   |  Celery Worker    |
| (HTTP Endpoints) |  delay  |  (Queue Engine) |  pop    | (ai_prof_workers) |
+------------------+         +-----------------+         +-------------------+
                                                                   |
                                                                   v
                                                         +-------------------+
                                                         |  Database / LLM   |
                                                         |  Vector Store     |
                                                         +-------------------+
```

### Components
- **`workers/config.py`**: Reads Celery and Redis configuration settings from environment variables (`REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `CELERY_TASK_ALWAYS_EAGER`).
- **`workers/celery_app.py`**: Initializes the Celery application (`ai_prof_workers`) with strict task routing, late acknowledgments (`task_acks_late=True`), task rejection on lost worker (`task_reject_on_worker_lost=True`), and JSON serialization.
- **`workers/utils.py`**: Provides `run_coro_sync` utility to safely invoke async database/service functions inside synchronous Celery worker tasks without event loop conflicts.
- **`workers/tasks/`**: Modularized task definitions.

---

## Task Catalogue

| Category | Module | Primary Task | Description |
|---|---|---|---|
| **Materials** | `workers.tasks.material_tasks` | `process_material_task` | Downloads material PDF/text, extracts content per page, generates semantic chunks, updates `MaterialProcessingJob` status, and triggers knowledge indexing. |
| **Knowledge** | `workers.tasks.knowledge_tasks` | `index_material_knowledge_task` | Generates text embeddings, populates vector store, and extracts key concepts for the knowledge graph. |
| **Assessment** | `workers.tasks.assessment_tasks` | `evaluate_quiz_submission_task` | Evaluates open-ended student submissions using LLM grading pipelines and scores response quality. |
| **Mastery** | `workers.tasks.mastery_tasks` | `update_concept_mastery_task` | Recalculates student concept mastery ratings deterministically and records explainable mastery snapshots. |
| **Recommendation** | `workers.tasks.recommendation_tasks` | `generate_recommendations_task` | Ranks weak concepts and generates tailored Next Action recommendations for learners. |
| **Maintenance** | `workers.tasks.maintenance_tasks` | `system_health_check_task` | Performs background health checks and system telemetry heartbeats. |

---

## Idempotency & Reliability Guarantees

1. **Strict Idempotency**:
   - `process_material_task` checks existing extracted pages and chunk count before inserting, ensuring duplicate processing requests do not duplicate pages or vector embeddings.
   - Database operations use upserts or existence checks before mutating state.

2. **Data & Project Isolation**:
   - Every background task verifies `user_id` and `project_id` access rights prior to processing.
   - Inaccessible or mismatched resources raise authorization errors and abort processing immediately.

3. **Retry & Backoff Policy**:
   - Transients errors (LLM rate limits, network timeouts, temporary DB disconnects) retry automatically up to **3 times** with exponential backoff (`countdown = 2 ** attempt`).
   - Non-retryable errors (e.g. `FileNotFoundError`, `ValueError`, corrupted file data, authorization failures) fail fast without infinite loops.

4. **Async Execution Safety**:
   - Synchronous task workers execute async application services via `run_coro_sync`, using dedicated single-thread event loops to prevent `RuntimeError: asyncio.run() cannot be called from a running event loop`.

---

## Local Development & Testing

### Running Celery Worker Locally
Ensure Redis is running (or set `CELERY_TASK_ALWAYS_EAGER=True` for inline testing):

```bash
# Start Redis container or local daemon
docker run -p 6379:6379 redis:alpine

# Start Celery Worker process
celery -A workers.celery_app worker --loglevel=INFO
```

### Running Automated Worker Tests
```bash
pytest backend/tests/test_workers.py -v
```

During test suite execution, `CELERY_TASK_ALWAYS_EAGER=True` runs tasks inline synchronously without requiring a live Redis connection.

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | Default Redis connection URI |
| `CELERY_BROKER_URL` | Defaults to `REDIS_URL` | Broker URL for task queueing |
| `CELERY_RESULT_BACKEND` | Defaults to `REDIS_URL` | Backend for storing task results |
| `CELERY_TASK_ALWAYS_EAGER` | `False` (`True` in test env) | If `True`, tasks execute locally synchronously |
