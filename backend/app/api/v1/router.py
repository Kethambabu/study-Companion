from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    assessment,
    auth,
    health,
    intelligence,
    jobs,
    knowledge,
    mastery,
    materials,
    projects,
    recommendations,
    spaces,
    tutor,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)
api_router.include_router(spaces.router)
api_router.include_router(projects.router)
api_router.include_router(materials.router)
api_router.include_router(knowledge.router)
api_router.include_router(tutor.router)
api_router.include_router(assessment.router)
api_router.include_router(mastery.router)
api_router.include_router(intelligence.router)
api_router.include_router(recommendations.router)
api_router.include_router(analytics.router)
api_router.include_router(jobs.router)
api_router.include_router(admin.router)
