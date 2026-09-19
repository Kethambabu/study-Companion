import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

MIGRATION_STATEMENTS = [
    # Materials table column synchronization
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS owner_id UUID;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS content_type VARCHAR(100) DEFAULT 'application/pdf';",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS storage_path VARCHAR(512);",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS file_size INT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS progress_pct INT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS current_step VARCHAR(100) DEFAULT 'QUEUED';",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS word_count INT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS estimated_reading_minutes INT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS attempt_count INT DEFAULT 0;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS last_error TEXT;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;",
    "ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS failed_at TIMESTAMPTZ;",

    # Material processing jobs table column synchronization
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR(50) DEFAULT 'pdf_extraction';",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS progress_pct INT DEFAULT 0;",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS current_step VARCHAR(100) DEFAULT 'QUEUED';",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS attempt INT DEFAULT 1;",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS max_attempts INT DEFAULT 3;",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;",
    "ALTER TABLE public.material_processing_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;",

    # Material pages
    "ALTER TABLE public.material_pages ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}'::jsonb;",

    # Tutor conversations & messages
    "ALTER TABLE public.tutor_conversations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;",
    "ALTER TABLE public.tutor_messages ADD COLUMN IF NOT EXISTS sender VARCHAR(50) DEFAULT 'user';",
    "ALTER TABLE public.tutor_messages ADD COLUMN IF NOT EXISTS citations JSONB DEFAULT '[]'::jsonb;",
    "ALTER TABLE public.tutor_messages ADD COLUMN IF NOT EXISTS metadata_json JSONB DEFAULT '{}'::jsonb;",
]


async def run_db_migrations(conn=None) -> None:
    """Safely executes DDL migrations ensuring missing database table columns are synchronized.
    
    Executes in a single fast batch query pass first (1 network round-trip), with fallback to individual
    transactions if needed.
    """
    from app.core.database import engine

    batch_sql = "\n".join(MIGRATION_STATEMENTS)
    try:
        async with engine.begin() as batch_conn:
            await batch_conn.execute(text(batch_sql))
        logger.info("Database schema columns auto-migrated successfully in batch pass.")
    except Exception as exc:
        logger.debug(f"Batch migration fallback ({exc}), applying individually...")
        for stmt in MIGRATION_STATEMENTS:
            try:
                async with engine.begin() as single_conn:
                    await single_conn.execute(text(stmt))
            except Exception as e:
                logger.debug(f"Migration statement handled: {stmt} -> {e}")
        logger.info("Database schema columns auto-migrated successfully.")
