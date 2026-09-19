# AI Study Companion — Backend Architecture Documentation

## 1. Architectural Blueprint

The backend is built as a high-performance, domain-driven FastAPI system supporting the complete learning loop:

```
Space Boundary
  └── Project Scope
        ├── PDF Upload & Storage → Storage Service
        ├── Background Document Processing → Celery Worker & PyMuPDF/OCR
        ├── Semantic Chunking & Vector Store → PgVector / Cosine Similarity Store
        ├── RAG Retrieval Engine → Reranker & Citation Mapping
        ├── AI Principal Tutor → Grounded Completion & Citation Validator
        ├── Adaptive Quiz Engine → Selection & Question Generation
        ├── Open-Ended Evaluation → Criteria Matching & Pydantic Schema
        ├── Concept Mastery Subsystem → Deterministic Decay & Growth Snapshots
        ├── Recommendation Engine → Prioritized Action Generation
        └── Domain Event Pipeline & AI Observability → Telemetry & Audit Logs
```

---

## 2. Core Subsystems

### 2.1 API Layer (`app/api/v1`)
- **Framework:** FastAPI (Python 3.12, AsyncIO)
- **Middleware:** CORS, Request Tracing (`x-request-id`), Centralized Exception Handlers
- **Authentication & Security:** JWT Token Bearer authentication (`app/modules/auth`)
- **Endpoints:** Health, Auth, Spaces, Projects, Materials, Knowledge, Tutor, Assessment, Mastery, Recommendations, Analytics, Admin

### 2.2 Domain Services & Modules (`app/modules`)
1. **Auth Service (`app/modules/auth`):** Profile management, password hashing, token issue, space member role verification.
2. **Space & Project Services (`app/modules/spaces`, `app/modules/projects`):** Multi-tenant organization boundaries and project-level resource containers.
3. **Materials & Storage Service (`app/modules/materials`):** Storage abstraction (Supabase / local disk), SHA-256 checksum deduplication, filename sanitization.
4. **Knowledge & Vector Subsystem (`app/modules/knowledge`):** `SemanticChunker`, `DeterministicEmbeddingProvider` (384-dim), `InMemoryVectorStore` / PgVector, `CosineSimilarityReranker`, project-isolated 9-stage retrieval pipeline.
5. **AI Tutor Engine (`app/modules/tutor`):** Multi-provider LLM abstraction (Gemini, Groq, Mock), `PromptBuilder` with prompt injection containment (`<untrusted_study_material>`), `CitationValidator` against retrieved evidence.
6. **Assessment Engine (`app/modules/assessment`):** `AdaptiveSelectionEngine` selecting concepts & difficulty based on mistake history, `QuestionGenerator` creating MCQ & Open-ended items, `QuestionEvaluator` scoring open-ended answers with structured feedback.
7. **Concept Mastery & Growth Engine (`app/modules/mastery`, `app/modules/growth`):** `DeterministicMasteryEngine` for score calculation, time-decay, mastery snapshot generation, status classification (`mastered`, `improving`, `stable`, `weak`).
8. **Recommendation Engine (`app/modules/recommendations`):** `RuleBasedRecommendationEngine` deriving explainable next steps ("What to do next?") based on weakness priority.
9. **Event Pipeline (`app/modules/events`):** `DomainEventPublisher` and `EventService` recording idempotent learning events.
10. **Analytics & Admin Capabilities (`app/modules/analytics`, `app/modules/admin`):** Project & global aggregated engagement stats, AI usage telemetry, platform administration.
11. **AI Observability (`app/modules/observability`):** Token tracking, latency ms, model provider, request ID, confidence status.

### 2.3 Background Jobs & Workers (`workers/`)
- **Task Queue:** Celery with Redis Broker (`redis://localhost:6379/0`)
- **Registered Tasks:**
  - `material.process` (`workers/tasks/material_tasks.py`): PDF text extraction, OCR fallback, indexing trigger.
  - `knowledge.index` (`workers/tasks/knowledge_tasks.py`): Vector store chunking & embedding generation.
  - `assessment.generate` (`workers/tasks/assessment_tasks.py`): Async quiz generation.
  - `mastery.recalculate` (`workers/tasks/mastery_tasks.py`): Async mastery score updates.
  - `recommendation.generate` (`workers/tasks/recommendation_tasks.py`): Async recommendation calculation.
  - `maintenance.cleanup` (`workers/tasks/maintenance_tasks.py`): Periodic garbage collection.
- **Resilience:** Automatic retry with exponential backoff (`countdown = 2 ** retries`), non-retryable error classification.

### 2.4 Database & Persistence Layer (`database/`)
- **Database Engine:** PostgreSQL + PgVector extension (or SQLite/In-memory fallback for test harnesses)
- **ORMs & Schema:** SQLAlchemy 2.0 Async Session
- **Tables:** `profiles`, `spaces`, `space_members`, `projects`, `materials`, `material_pages`, `material_processing_jobs`, `knowledge_chunks`, `concepts`, `quizzes`, `quiz_submissions`, `mastery_ratings`, `mastery_snapshots`, `learning_events`, `recommendations`, `tutor_conversations`, `tutor_messages`, `admin_logs`, `ai_telemetry`.
- **Security:** PostgreSQL Row Level Security (RLS) policies in `database/rls_policies.sql`.
