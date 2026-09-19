# Database Schema & Data Isolation Model

## Overview

AI Prof uses PostgreSQL (managed via Supabase in production) with SQLAlchemy ORM models. Strict Row Level Security (RLS) and application-level tenant filters ensure User A cannot access User B's resources.

## Tables & Entity Relationships

| Table Name | Primary Key | Foreign Keys | Key Attributes & Description |
| :--- | :--- | :--- | :--- |
| `profiles` | `id` (UUID) | - | `email`, `full_name`, `hashed_password`, `created_at` |
| `spaces` | `id` (UUID) | `owner_id` $\rightarrow$ `profiles.id` | `name`, `slug` (unique), `description`, `created_at` |
| `space_memberships` | `id` (UUID) | `space_id` $\rightarrow$ `spaces.id`, `user_id` $\rightarrow$ `profiles.id` | `role` (`owner`, `admin`, `member`), `created_at` |
| `projects` | `id` (UUID) | `space_id` $\rightarrow$ `spaces.id`, `user_id` $\rightarrow$ `profiles.id` | `name`, `description`, `status`, `created_at` |
| `materials` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id`, `user_id` $\rightarrow$ `profiles.id` | `title`, `file_type`, `checksum`, `file_size`, `status` |
| `material_chunks` | `id` (UUID) | `material_id` $\rightarrow$ `materials.id` | `chunk_index`, `content`, `page_number`, `token_count` |
| `tutor_conversations` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id`, `user_id` $\rightarrow$ `profiles.id` | `title`, `created_at` |
| `tutor_messages` | `id` (UUID) | `conversation_id` $\rightarrow$ `tutor_conversations.id` | `sender` (`user`/`assistant`), `content`, `citations_json`, `confidence_status` |
| `quizzes` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id`, `user_id` $\rightarrow$ `profiles.id` | `title`, `difficulty`, `num_questions`, `created_at` |
| `quiz_questions` | `id` (UUID) | `quiz_id` $\rightarrow$ `quizzes.id` | `question_text`, `question_type`, `options_json`, `correct_answer` |
| `quiz_attempts` | `id` (UUID) | `quiz_id` $\rightarrow$ `quizzes.id`, `user_id` $\rightarrow$ `profiles.id` | `score`, `passed`, `feedback_json`, `submitted_at` |
| `concepts` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id` | `name`, `slug`, `description` |
| `concept_mastery` | `id` (UUID) | `concept_id` $\rightarrow$ `concepts.id`, `user_id` $\rightarrow$ `profiles.id` | `mastery_score`, `status` (`improving`/`stable`/`requiring_attention`) |
| `mastery_events` | `id` (UUID) | `concept_id` $\rightarrow$ `concepts.id`, `user_id` $\rightarrow$ `profiles.id` | `previous_score`, `new_score`, `evidence_type`, `idempotency_key` |
| `growth_snapshots` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id`, `user_id` $\rightarrow$ `profiles.id` | `overall_mastery`, `weak_concepts_json`, `created_at` |
| `learning_events` | `id` (UUID) | `user_id` $\rightarrow$ `profiles.id`, `project_id` $\rightarrow$ `projects.id` | `event_type`, `payload_json`, `status`, `idempotency_key` |
| `recommendations` | `id` (UUID) | `project_id` $\rightarrow$ `projects.id`, `user_id` $\rightarrow$ `profiles.id` | `title`, `description`, `action_type`, `priority_score` |

## Tenant Isolation Strategy

Every multi-tenant query evaluates `AuthService.check_space_access(user_id, space_id)`. Direct resource lookups enforce `WHERE project_id = :p_id AND user_id = :u_id` parameter bindings.
