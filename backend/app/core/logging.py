import logging
import sys

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """Configures structured JSON logging using structlog with Windows UTF-8 safety."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if settings.ENVIRONMENT.lower() == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "ai_study_companion") -> structlog.BoundLogger:
    return structlog.get_logger(name)
