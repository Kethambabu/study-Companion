import asyncio
import sys
import uuid
import traceback

sys.path.insert(0, ".")

from app.core.database import AsyncSessionLocal
from app.modules.tutor.service import TutorService
from app.modules.auth.models import Profile
from app.modules.projects.models import Project
from sqlalchemy import select

async def debug_abort():
    async with AsyncSessionLocal() as session:
        user_res = await session.execute(select(Profile).where(Profile.email == "varshitha@example.com"))
        user = user_res.scalar_one_or_none()
        
        proj_res = await session.execute(select(Project).limit(1))
        proj = proj_res.scalar_one_or_none()

        print(f"Testing for User: {user.id}, Project: {proj.id}")

        service = TutorService(session)

        print("\n--- Detailed Step by Step inside get_persistent_learning_context ---")
        intel_service = service.persistent_context_service.intelligence_service

        try:
            print("1. intelligence_service._authorize...")
            await intel_service._authorize(user.id, proj.id)
            print("  _authorize succeeded")
        except Exception:
            traceback.print_exc()

        try:
            print("2. mastery_service.get_concept_mastery_list...")
            m_list = await intel_service.mastery_service.get_concept_mastery_list(user.id, proj.id)
            print(f"  get_concept_mastery_list succeeded! count: {len(m_list)}")
        except Exception:
            traceback.print_exc()

        try:
            await session.execute(select(1))
            print("Session clean after get_concept_mastery_list")
        except Exception as e:
            print(f"SESSION ABORTED after get_concept_mastery_list: {e}")
            await session.rollback()

        try:
            print("3. knowledge_service.list_project_concepts...")
            c_list = await service.knowledge_service.list_project_concepts(user_id=user.id, project_id=proj.id)
            print(f"  list_project_concepts succeeded! count: {len(c_list)}")
        except Exception:
            traceback.print_exc()

        try:
            await session.execute(select(1))
            print("Session clean after list_project_concepts")
        except Exception as e:
            print(f"SESSION ABORTED after list_project_concepts: {e}")

if __name__ == "__main__":
    asyncio.run(debug_abort())
