import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.auth.service import AuthService
from app.modules.materials.models import Material
from app.modules.knowledge.models import KnowledgeChunk
from app.modules.knowledge.service import KnowledgeService, _GLOBAL_VECTOR_STORE
from app.modules.projects.service import ProjectsService

async def debug_pipeline():
    async with AsyncSessionLocal() as db:
        from app.modules.auth.models import Profile
        auth_service = AuthService(db)
        projects_service = ProjectsService(db)
        knowledge_service = KnowledgeService(db)

        # 1. Get Varshitha user
        stmt_user = select(Profile).where(Profile.email == "varshitha@example.com")
        user_res = await db.execute(stmt_user)
        user = user_res.scalar_one_or_none()
        if not user:
            print("User varshitha@example.com NOT found!")
            return
        print(f"1. Authenticated User ID: {user.id} ({user.email})")

        # 2. Get Student's Projects
        spaces = await auth_service.list_user_spaces(user.id)
        if not spaces:
            print("No spaces found for user!")
            return
        space_id = spaces[0].id
        projects_resp = await projects_service.list_projects(user.id, space_id)
        if not projects_resp.items:
            print("No projects found for user space!")
            return
        
        project = projects_resp.items[0]
        project_id = project.id
        print(f"2. Target Project ID: {project_id} (Name: '{project.name}')")

        # 3. Check Materials in Project
        stmt_mats = select(Material).where(Material.project_id == project_id)
        mats_res = await db.execute(stmt_mats)
        materials = list(mats_res.scalars().all())
        print(f"3. Found {len(materials)} materials for project:")
        for m in materials:
            print(f"   - Material ID: {m.id} | Name: {m.filename} | Status: {m.status}")

        # 4. Check Knowledge Chunks in DB
        stmt_chunks = select(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id)
        chunks_res = await db.execute(stmt_chunks)
        db_chunks = list(chunks_res.scalars().all())
        print(f"4. Found {len(db_chunks)} chunks in PostgreSQL for project.")
        for idx, c in enumerate(db_chunks[:5]):
            print(f"   Chunk {idx+1}: ID={c.id} | MaterialID={c.material_id} | Page={c.page_number} | Text Preview: {c.content[:80]}...")

        # 5. Check InMemoryVectorStore state BEFORE DB sync
        in_mem_count = len([r for r in _GLOBAL_VECTOR_STORE._records if r["project_id"] == project_id])
        print(f"5. InMemoryVectorStore has {in_mem_count} records for project {project_id} BEFORE sync.")

        # 6. Test RAG Search Queries
        test_queries = [
            "what are Well posed learning problems:",
            "who is the current prime minister of india",
            "how many legs does a dog have",
        ]

        print("\n=======================================================")
        print("EXECUTING RAG RETRIEVAL PIPELINE DIAGNOSTICS")
        print("=======================================================")

        user_id_val = user.id
        for q in test_queries:
            print(f"\n--- QUERY: '{q}' ---")
            res = await knowledge_service.search_knowledge(user_id=user_id_val, project_id=project_id, query=q, top_k=5)
            print(f"Context Length: {len(res.context)}")
            print(f"Citations Count: {len(res.citations)}")
            print(f"Diagnostics: CandidateCount={res.diagnostics.candidate_count}, SelectedCount={res.diagnostics.selected_count}")
            print(f"Similarity Scores: {res.diagnostics.similarity_scores}")
            print(f"Reranking Scores: {res.diagnostics.reranking_scores}")

            for idx, cit in enumerate(res.citations):
                print(f"   Cit {idx+1}: Source={cit.material_name} (Page {cit.page_number}) | ID={cit.chunk_id} | Excerpt={cit.excerpt[:100]}...")

if __name__ == "__main__":
    asyncio.run(debug_pipeline())
