-- ====================================================================
-- AI STUDY COMPANION / AI PROF — FULL SUPABASE POSTGRESQL + PGVECTOR SCHEMA
-- ====================================================================

-- 0. ENABLE EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. PROFILES TABLE (Linked to auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 2. SPACES TABLE (Multi-Tenant Organization Boundaries)
CREATE TABLE IF NOT EXISTS public.spaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    visual_metadata JSONB,
    owner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMPTZ
);


-- 3. SPACE MEMBERS TABLE
CREATE TABLE IF NOT EXISTS public.space_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES public.spaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_space_member UNIQUE (space_id, user_id)
);

-- 4. PROJECTS TABLE
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    space_id UUID NOT NULL REFERENCES public.spaces(id) ON DELETE CASCADE,
    owner_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. MATERIALS TABLE (PDF / Study Documents)
CREATE TABLE IF NOT EXISTS public.materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    storage_path VARCHAR(512),
    mime_type VARCHAR(100) DEFAULT 'application/pdf',
    page_count INT DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. MATERIAL PAGES TABLE
CREATE TABLE IF NOT EXISTS public.material_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES public.materials(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    extracted_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_material_page UNIQUE (material_id, page_number)
);

-- 7. MATERIAL PROCESSING JOBS TABLE
CREATE TABLE IF NOT EXISTS public.material_processing_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_id UUID NOT NULL REFERENCES public.materials(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    attempts INT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. KNOWLEDGE CHUNKS TABLE (PGVECTOR VECTOR STORE)
CREATE TABLE IF NOT EXISTS public.knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    material_id UUID NOT NULL REFERENCES public.materials(id) ON DELETE CASCADE,
    page_number INT NOT NULL,
    chunk_index INT NOT NULL,
    section_title VARCHAR(255),
    content TEXT NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    embedding vector(384), -- 384-dimensional sentence-transformers/all-mpnet-base-v2 or local embeddings
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Vector Cosine Similarity Search Index
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding 
ON public.knowledge_chunks 
USING hnsw (embedding vector_cosine_ops);

-- 9. CONCEPTS TABLE
CREATE TABLE IF NOT EXISTS public.concepts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    definition TEXT,
    domain VARCHAR(100) DEFAULT 'General',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 10. QUIZZES TABLE
CREATE TABLE IF NOT EXISTS public.quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    difficulty_level VARCHAR(50) NOT NULL DEFAULT 'medium',
    questions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 11. QUIZ SUBMISSIONS TABLE
CREATE TABLE IF NOT EXISTS public.quiz_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES public.quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    score_percentage NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    answers_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    feedback_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 12. MASTERY RATINGS TABLE
CREATE TABLE IF NOT EXISTS public.mastery_ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    concept_id UUID NOT NULL REFERENCES public.concepts(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    mastery_score NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    confidence_level VARCHAR(50) DEFAULT 'medium',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_user_concept_mastery UNIQUE (user_id, concept_id)
);

-- 13. MASTERY SNAPSHOTS TABLE
CREATE TABLE IF NOT EXISTS public.mastery_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    overall_mastery NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    snapshot_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 14. LEARNING EVENTS TABLE
CREATE TABLE IF NOT EXISTS public.learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 15. RECOMMENDATIONS TABLE
CREATE TABLE IF NOT EXISTS public.recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(50) DEFAULT 'medium',
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 16. TUTOR CONVERSATIONS & MESSAGES TABLES
CREATE TABLE IF NOT EXISTS public.tutor_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'Tutor Conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.tutor_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.tutor_conversations(id) ON DELETE CASCADE,
    sender_role VARCHAR(50) NOT NULL CHECK (sender_role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations_json JSONB DEFAULT '[]'::jsonb,
    tokens_used INT DEFAULT 0,
    latency_ms NUMERIC(10,2) DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 17. ADMIN LOGS & TELEMETRY TABLES
CREATE TABLE IF NOT EXISTS public.admin_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    details_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.ai_telemetry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    tokens_used INT DEFAULT 0,
    latency_ms NUMERIC(10,2) DEFAULT 0.00,
    status VARCHAR(50) NOT NULL DEFAULT 'success',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES ON ALL TABLES
-- ====================================================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.spaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.space_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.materials ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.material_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.material_processing_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.concepts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quizzes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mastery_ratings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mastery_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tutor_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tutor_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_telemetry ENABLE ROW LEVEL SECURITY;
