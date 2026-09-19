# AI Study Companion — Backend API Inventory

## Endpoint Reference List

| Method | Endpoint Path | Summary / Purpose | Auth Required | Role | Request Schema | Response Schema | DB / Background Interaction |
|--------|---------------|-------------------|---------------|------|----------------|-----------------|-----------------------------|
| **GET** | `/health` | Application health check | No | Public | None | `dict` | Database connectivity ping |
| **GET** | `/api/v1/health` | API V1 health check | No | Public | None | `dict` | Database & Redis status |
| **POST** | `/api/v1/auth/signup` | User account registration | No | Public | `UserSignupRequest` | `ApiResponse[AuthTokenResponse]` | Insert `profiles` |
| **POST** | `/api/v1/auth/login` | User login & JWT issuance | No | Public | `UserLoginRequest` | `ApiResponse[AuthTokenResponse]` | Select `profiles` & verify bcrypt hash |
| **GET** | `/api/v1/auth/me` | Retrieve current authenticated profile | Yes | User | None | `ApiResponse[UserProfileResponse]` | Select `profiles` by `user_id` |
| **POST** | `/api/v1/spaces` | Create multi-tenant Space | Yes | User | `SpaceCreateRequest` | `ApiResponse[SpaceResponse]` | Insert `spaces` & `space_members` (`role='owner'`) |
| **GET** | `/api/v1/spaces` | List accessible Spaces | Yes | User | None | `ApiResponse[list[SpaceResponse]]` | Select `spaces` joined with `space_members` |
| **GET** | `/api/v1/spaces/{space_id}` | Get Space details | Yes | Member | None | `ApiResponse[SpaceResponse]` | Select `spaces` with authorization check |
| **POST** | `/api/v1/projects` | Create Project inside Space | Yes | Member | `ProjectCreateRequest` | `ApiResponse[ProjectResponse]` | Insert `projects` |
| **GET** | `/api/v1/projects` | List Projects in Space | Yes | Member | Query `space_id` | `ApiResponse[list[ProjectResponse]]` | Select `projects` filtered by `space_id` |
| **GET** | `/api/v1/projects/{project_id}` | Get Project details | Yes | Member | None | `ApiResponse[ProjectResponse]` | Select `projects` with project-level auth |
| **POST** | `/api/v1/projects/{project_id}/materials` | Upload PDF Study Material | Yes | Member | Multipart File | `ApiResponse[MaterialResponse]` | Save file storage, SHA-256 checksum, enqueue Celery `material.process` |
| **GET** | `/api/v1/projects/{project_id}/materials` | List Project Materials | Yes | Member | Page/Limit | `ApiResponse[PaginatedMaterialsResponse]` | Select `materials` |
| **GET** | `/api/v1/projects/{project_id}/materials/{material_id}` | Get Material Details | Yes | Member | None | `ApiResponse[MaterialResponse]` | Select `materials` |
| **GET** | `/api/v1/projects/{project_id}/materials/{material_id}/pages` | Get Extracted PDF Pages | Yes | Member | Page/Limit | `ApiResponse[PaginatedPagesResponse]` | Select `material_pages` |
| **POST** | `/api/v1/projects/{project_id}/materials/{material_id}/retry` | Retry Failed Extraction Job | Yes | Member | None | `ApiResponse[MaterialRetryResponse]` | Reset material status, re-enqueue `material.process` |
| **POST** | `/api/v1/projects/{project_id}/knowledge/index/{material_id}` | Trigger Knowledge Indexing | Yes | Member | None | `ApiResponse[dict]` | Chunk pages, compute 384-dim vectors, populate vector store & concepts |
| **POST** | `/api/v1/projects/{project_id}/knowledge/search` | Project-Isolated RAG Search | Yes | Member | `RetrievalSearchRequest` | `ApiResponse[RetrievalSearchResponse]` | 9-stage RAG pipeline, vector cosine similarity search, reranking |
| **GET** | `/api/v1/projects/{project_id}/knowledge/chunks` | List Knowledge Chunks | Yes | Member | Page/Limit | `ApiResponse[PaginatedChunksResponse]` | Select `knowledge_chunks` |
| **GET** | `/api/v1/projects/{project_id}/knowledge/concepts` | List Project Concepts | Yes | Member | None | `ApiResponse[list[ConceptResponse]]` | Select `concepts` |
| **POST** | `/api/v1/projects/{project_id}/tutor/conversations` | Create Tutor Session | Yes | Member | `ConversationCreateRequest` | `ApiResponse[ConversationResponse]` | Insert `tutor_conversations` |
| **GET** | `/api/v1/projects/{project_id}/tutor/conversations` | List Tutor Sessions | Yes | Member | None | `ApiResponse[list[ConversationResponse]]` | Select `tutor_conversations` |
| **GET** | `/api/v1/projects/{project_id}/tutor/conversations/{conv_id}/messages` | Get Session Messages | Yes | Member | Page/Limit | `ApiResponse[PaginatedMessagesResponse]` | Select `tutor_messages` |
| **POST** | `/api/v1/projects/{project_id}/tutor/conversations/{conv_id}/messages` | Send Grounded Tutor Message | Yes | Member | `TutorChatRequest` | `ApiResponse[TutorChatResponse]` | RAG search, LLM completion, Citation validation, Insert `tutor_messages` & `ai_telemetry` |
| **POST** | `/api/v1/projects/{project_id}/quizzes` | Generate Adaptive Quiz | Yes | Member | `QuizCreateRequest` | `ApiResponse[QuizResponse]` | `AdaptiveSelectionEngine`, `QuestionGenerator`, Insert `quizzes` & `quiz_questions` |
| **GET** | `/api/v1/projects/{project_id}/quizzes` | List Project Quizzes | Yes | Member | None | `ApiResponse[list[QuizResponse]]` | Select `quizzes` |
| **GET** | `/api/v1/projects/{project_id}/quizzes/{quiz_id}` | Get Quiz Details | Yes | Member | None | `ApiResponse[QuizResponse]` | Select `quizzes` & `quiz_questions` |
| **POST** | `/api/v1/projects/{project_id}/quizzes/{quiz_id}/submit` | Submit Quiz Answers | Yes | Member | `SubmitAnswerRequest` | `ApiResponse[QuizAttemptResponse]` | `QuestionEvaluator`, Insert `quiz_submissions`, update mastery, trigger event |
| **GET** | `/api/v1/projects/{project_id}/mastery` | Get Concept Mastery List | Yes | Member | None | `ApiResponse[list[ConceptMasteryResponse]]` | Select `mastery_ratings` |
| **POST** | `/api/v1/projects/{project_id}/mastery/events` | Record Mastery Event | Yes | Member | `MasteryEventCreate` | `ApiResponse[MasteryEventResponse]` | `DeterministicMasteryEngine`, update mastery score, insert `mastery_snapshots` |
| **GET** | `/api/v1/projects/{project_id}/growth/summary` | Get Growth Summary | Yes | Member | None | `ApiResponse[GrowthSummaryResponse]` | Summarize concept mastery distribution (`mastered`, `improving`, `stable`, `weak`) |
| **GET** | `/api/v1/projects/{project_id}/growth/snapshots` | Get Growth Snapshots | Yes | Member | None | `ApiResponse[list[GrowthSnapshotResponse]]` | Select `mastery_snapshots` time series |
| **GET** | `/api/v1/projects/{project_id}/recommendations` | Get Next Study Actions | Yes | Member | None | `ApiResponse[list[RecommendationResponse]]` | `RuleBasedRecommendationEngine` prioritizing weak concepts |
| **POST** | `/api/v1/projects/{project_id}/recommendations/{rec_id}/dismiss` | Dismiss Recommendation | Yes | Member | None | `ApiResponse[dict]` | Update `recommendations` status |
| **POST** | `/api/v1/projects/{project_id}/events` | Record Domain Event | Yes | Member | `LearningEventCreate` | `ApiResponse[LearningEventResponse]` | Idempotent insert `learning_events` & async event processor |
| **GET** | `/api/v1/projects/{project_id}/analytics` | Get Project Analytics | Yes | Member | None | `ApiResponse[ProjectAnalyticsResponse]` | Aggregate activity counts, quiz average, mastery trends |
| **GET** | `/api/v1/admin/users` | List All Users | Yes | Admin | Page/Limit | `ApiResponse[dict]` | Select `profiles` |
| **GET** | `/api/v1/admin/ai-usage` | Get AI Usage Logs | Yes | Admin | Page/Limit | `ApiResponse[dict]` | Select `ai_telemetry` |
| **GET** | `/api/v1/admin/telemetry` | System Telemetry Dashboard | Yes | Admin | None | `ApiResponse[dict]` | Aggregate user, project, job, and LLM telemetry |
