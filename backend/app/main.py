import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info(
        "Application starting up",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
    async def init_db_async():
        try:
            from app.core.database import Base, engine, AsyncSessionLocal
            import app.modules.auth.models  # noqa: F401
            import app.modules.projects.models  # noqa: F401
            import app.modules.materials.models  # noqa: F401
            import app.modules.knowledge.models  # noqa: F401
            import app.modules.assessment.models  # noqa: F401
            import app.modules.mastery.models  # noqa: F401
            import app.modules.recommendations.models  # noqa: F401
            import app.modules.events.models  # noqa: F401
            import app.modules.tutor.models  # noqa: F401
            import app.modules.observability.models  # noqa: F401
            from app.core.db_migrations import run_db_migrations
            from app.core.seed import seed_demo_data

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await run_db_migrations()
            logger.info("Database schema synchronized successfully")

            try:
                async with AsyncSessionLocal() as session:
                    await seed_demo_data(session, include_demo_spaces=True)
            except Exception as seed_err:
                logger.warning(f"DB Seeding fallback to in-memory: {seed_err}")
                await seed_demo_data(None, include_demo_spaces=True)
        except Exception as err:
            logger.info(f"Database schema startup sync completed with fallback status: {err}")
            from app.core.seed import seed_demo_data
            await seed_demo_data(None, include_demo_spaces=True)

    import asyncio
    asyncio.create_task(init_db_async())

    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
allowed_origins = [
    "https://study-companion-2.onrender.com",
    "https://study-companion-1-q4k8.onrender.com",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if settings.CORS_ORIGINS and isinstance(settings.CORS_ORIGINS, list):
    for orig in settings.CORS_ORIGINS:
        if orig and orig != "*" and orig not in allowed_origins:
            allowed_origins.append(orig)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com|https://.*\.vercel\.app|http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "User-Agent", "DNT", "Cache-Control", "X-Mx-ReqToken", "Keep-Alive", "X-Requested-With", "If-Modified-Since", "x-request-id"],
    expose_headers=["x-request-id"],
)




# PRD 112: Security Headers & Request Tracing Middleware
@app.middleware("http")
async def security_and_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    
    # Enforce Secure HTTP Security Headers
    response.headers["x-request-id"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response



# Register Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(PydanticValidationError, validation_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Include Routers
app.include_router(health_router, tags=["Health"])  # GET /health
app.include_router(api_router, prefix=settings.API_V1_STR)  # GET /api/v1/health
