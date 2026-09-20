import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError, TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.knowledge.chunker import SemanticChunker
from app.modules.knowledge.models import Concept, KnowledgeChunk
from app.modules.knowledge.providers import (
    CosineSimilarityReranker,
    DeterministicEmbeddingProvider,
    InMemoryVectorStore,
)
from app.modules.knowledge.schemas import (
    ChunkResponse,
    CitationResponse,
    ConceptResponse,
    PaginatedChunksResponse,
    RetrievalDiagnosticsResponse,
    RetrievalSearchResponse,
)
from app.modules.materials.service import MaterialsService
from app.modules.projects.service import ProjectsService

# Global state / singletons for Knowledge & Vector domain
_IN_MEMORY_CHUNKS: dict[str, KnowledgeChunk] = {}
_IN_MEMORY_CONCEPTS: dict[str, Concept] = {}

_GLOBAL_VECTOR_STORE = InMemoryVectorStore()
_GLOBAL_EMBEDDING_PROVIDER = DeterministicEmbeddingProvider()
_GLOBAL_RERANKER = CosineSimilarityReranker()


class KnowledgeService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db
        self.materials_service = MaterialsService(db)
        self.projects_service = ProjectsService(db)

    async def index_material_knowledge(
        self, user_id: uuid.UUID, project_id: uuid.UUID, material_id: uuid.UUID
    ) -> int:
        """Chunks material pages, generates vectors, populates vector store, and extracts concepts."""
        material = await self.materials_service.get_material(user_id, material_id)
        if material.project_id != project_id:
            raise TenantAccessDeniedError("Material does not belong to target project.")
        if material.status != "ready":
            raise ValueError(f"Material '{material_id}' is not in 'ready' status for indexing.")

        # Get extracted pages
        pages_resp = await self.materials_service.get_material_pages(
            user_id=user_id, material_id=material_id, page=1, limit=500
        )
        if not pages_resp.items:
            return 0

        chunker = SemanticChunker()
        all_chunks: list[KnowledgeChunk] = []
        chunk_idx_counter = 0

        for page in pages_resp.items:
            chunk_outputs = chunker.chunk_page(
                page_number=page.page_number,
                text=page.extracted_text,
                starting_chunk_index=chunk_idx_counter,
            )

            for co in chunk_outputs:
                chunk_id = uuid.uuid4()
                now = datetime.now(UTC)
                kc = KnowledgeChunk(
                    id=chunk_id,
                    project_id=material.project_id,
                    material_id=material_id,
                    page_number=co.page_number,
                    chunk_index=co.chunk_index,
                    section_title=co.section_title,
                    content=co.content,
                    metadata_json=co.metadata,
                    created_at=now,
                )
                all_chunks.append(kc)
                _IN_MEMORY_CHUNKS[str(chunk_id)] = kc
                chunk_idx_counter += 1

        if not all_chunks:
            return 0

        if not all_chunks:
            return 0

        # Generate vector embeddings
        embeddings = _GLOBAL_EMBEDDING_PROVIDER.embed_texts([c.content for c in all_chunks])

        # Attach embeddings to chunk records & upsert to vector store
        for c, emb in zip(all_chunks, embeddings):
            _IN_MEMORY_CHUNKS[str(c.id)] = c

        _GLOBAL_VECTOR_STORE.upsert_chunks(all_chunks, embeddings)

        if self.db is not None:
            try:
                for c in all_chunks:
                    self.db.add(c)
                await self.db.commit()
            except Exception as e:
                import logging
                logging.getLogger("knowledge").error("Failed to commit chunks to DB: %s", e)
                await self.db.rollback()

        # Dynamic Concept Extraction from content (capitalized terms / key concepts)
        try:
            extracted_concepts = self._extract_concepts_from_chunks(material.project_id, material_id, all_chunks)
            if self.db is not None and extracted_concepts:
                try:
                    for conc in extracted_concepts:
                        self.db.add(conc)
                    await self.db.commit()
                except Exception:
                    await self.db.rollback()
        except Exception:
            pass

        return len(all_chunks)

    def _extract_concepts_from_chunks(
        self, project_id: uuid.UUID, material_id: uuid.UUID, chunks: list[KnowledgeChunk]
    ) -> list[Concept]:
        """Extracts key domain concepts dynamically from chunk text in chronological page order."""
        ordered_candidates: list[str] = []
        seen = set()
        # Sort chunks chronologically by page number and chunk index
        sorted_chunks = sorted(chunks, key=lambda c: (getattr(c, "page_number", 1), getattr(c, "chunk_index", 0)))
        for chunk in sorted_chunks:
            found = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", chunk.content)
            for term in found:
                term_clean = term.strip()
                if len(term_clean) > 3 and term_clean.lower() not in {"the", "this", "page", "quantum", "chapter", "section"}:
                    if term_clean.lower() not in seen:
                        seen.add(term_clean.lower())
                        ordered_candidates.append(term_clean)

        concept_list = ordered_candidates[:12]  # Keep sequential syllabus topics
        created_concepts: list[Concept] = []
        import time

        for idx, concept_name in enumerate(concept_list):
            cid_str = f"{project_id}_{concept_name.lower()}"
            if cid_str not in _IN_MEMORY_CONCEPTS:
                cid = uuid.uuid4()
                c = Concept(
                    id=cid,
                    project_id=project_id,
                    name=concept_name,
                    definition=f"Extracted domain concept: '{concept_name}' from project materials.",
                    domain="Extracted Knowledge",
                    created_at=datetime.now(UTC),
                )
                _IN_MEMORY_CONCEPTS[str(cid)] = c
                created_concepts.append(c)
            else:
                c = _IN_MEMORY_CONCEPTS[cid_str]

        return created_concepts

    async def _ensure_project_knowledge_indexed(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        """Ensures in-memory vector store has all indexed project chunks loaded from DB or indexes ready materials."""
        in_mem_records = [r for r in _GLOBAL_VECTOR_STORE._records if r["project_id"] == project_id]
        if in_mem_records:
            return

        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id)
                res = await self.db.execute(stmt)
                db_chunks = list(res.scalars().all())
                if db_chunks:
                    embeddings = _GLOBAL_EMBEDDING_PROVIDER.embed_texts([c.content for c in db_chunks])
                    for c, emb in zip(db_chunks, embeddings):
                        _IN_MEMORY_CHUNKS[str(c.id)] = c
                    _GLOBAL_VECTOR_STORE.upsert_chunks(db_chunks, embeddings)
                    return
            except Exception:
                await self.db.rollback()

            # If 0 chunks in DB, check for ready materials and index them
            try:
                from app.modules.materials.models import Material
                from sqlalchemy import select
                stmt_mats = select(Material).where(Material.project_id == project_id, Material.status == "ready")
                res_mats = await self.db.execute(stmt_mats)
                ready_mats = list(res_mats.scalars().all())
                for mat in ready_mats:
                    await self.index_material_knowledge(user_id=user_id, project_id=project_id, material_id=mat.id)
            except Exception:
                await self.db.rollback()

    async def search_knowledge(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        query: str,
        top_k: int = 5,
        threshold: float = 0.35,
        material_id: uuid.UUID | None = None,
    ) -> RetrievalSearchResponse:
        """Executes full 9-stage project-isolated RAG retrieval pipeline."""
        import logging
        logger = logging.getLogger("tutor.rag")

        # 1. Authorize project space access
        proj = await self.projects_service.get_project_model(project_id)
        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=user_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for target project search.")

        # Ensure chunks for project are populated
        await self._ensure_project_knowledge_indexed(user_id=user_id, project_id=project_id)

        # Fast-path: if project has no indexed chunks, return empty context immediately
        project_chunks = [r for r in _GLOBAL_VECTOR_STORE._records if r["project_id"] == project_id]
        if not project_chunks:
            return RetrievalSearchResponse(
                context="",
                citations=[],
                diagnostics=RetrievalDiagnosticsResponse(
                    query=query,
                    candidate_count=0,
                    selected_count=0,
                    similarity_scores=[],
                    reranking_scores=[],
                    source_pages=[],
                ),
            )

        # Stage 1: Query Preprocessing
        query_clean = query.strip()
        if not query_clean:
            return RetrievalSearchResponse(
                context="",
                citations=[],
                diagnostics=RetrievalDiagnosticsResponse(
                    query=query,
                    candidate_count=0,
                    selected_count=0,
                    similarity_scores=[],
                    reranking_scores=[],
                    source_pages=[],
                ),
            )

        # Stage 2: Query Embedding
        query_vector = _GLOBAL_EMBEDDING_PROVIDER.embed_texts([query_clean])[0]

        # Stage 3: Initial Vector Search (Project-isolated, overfetch candidates 3x top_k)
        candidates = _GLOBAL_VECTOR_STORE.search(
            project_id=project_id,
            query_vector=query_vector,
            top_k=top_k * 3,
            material_id=material_id,
        )

        # Stage 4: Reranking
        reranked = _GLOBAL_RERANKER.rerank(query_clean, candidates)

        # Stage 5: Threshold Filtering & Top-K Selection
        selected = [r for r in reranked if r.final_score >= threshold][:top_k]
        if not selected and reranked:
            selected = [r for r in reranked if r.final_score >= 0.15][:top_k]

        # Debug Logging for PRD Audit
        logger.info(
            "RAG Search Executed | User: %s | Project: %s | Query: '%s' | Candidates: %d | Selected: %d",
            user_id, project_id, query_clean, len(candidates), len(selected)
        )
        for idx, item in enumerate(selected[:5]):
            cand = item.candidate
            logger.info(
                "  Top Chunk #%d | ChunkID: %s | MaterialID: %s | Page: %d | SimScore: %.4f | RerankScore: %.4f | Preview: '%s'",
                idx + 1, cand.chunk_id, cand.material_id, cand.page_number, cand.similarity_score, item.final_score, cand.content[:100].replace('\n', ' ')
            )

        # Stage 6 & 7: Source Citation & Context Assembly
        import asyncio
        citations: list[CitationResponse] = []
        context_blocks: list[str] = []

        unique_mat_ids = list({item.candidate.material_id for item in selected})
        mat_map: dict[uuid.UUID, str] = {}
        if unique_mat_ids:
            async def _fetch_mat_name(m_id):
                try:
                    mat = await self.materials_service.get_material(user_id, m_id)
                    return m_id, mat.filename
                except Exception:
                    return m_id, "Document Material"

            mat_results = await asyncio.gather(*[_fetch_mat_name(mid) for mid in unique_mat_ids])
            mat_map = dict(mat_results)

        for idx, item in enumerate(selected):
            cand = item.candidate
            mat_name = mat_map.get(cand.material_id, "Document Material")

            cit_id = f"[{idx + 1}]"
            excerpt = cand.content[:300] + "..." if len(cand.content) > 300 else cand.content

            cit = CitationResponse(
                citation_id=cit_id,
                material_id=cand.material_id,
                material_name=mat_name,
                page_number=cand.page_number,
                chunk_id=cand.chunk_id,
                excerpt=excerpt,
            )
            citations.append(cit)

            block = (
                f"{cit_id} Source: {mat_name} (Page {cand.page_number})\n"
                f"{cand.content}"
            )
            context_blocks.append(block)

        context_str = "\n\n".join(context_blocks)

        # Stage 8: Diagnostics Construction
        diagnostics = RetrievalDiagnosticsResponse(
            query=query_clean,
            candidate_count=len(candidates),
            selected_count=len(selected),
            similarity_scores=[round(c.similarity_score, 4) for c in candidates],
            reranking_scores=[round(r.final_score, 4) for r in reranked],
            source_pages=[r.candidate.page_number for r in selected],
        )

        return RetrievalSearchResponse(
            context=context_str,
            citations=citations,
            diagnostics=diagnostics,
        )

    async def list_project_concepts(
        self, user_id: uuid.UUID | str, project_id: uuid.UUID | str
    ) -> list[ConceptResponse]:
        u_id = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        p_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
        proj = await self.projects_service.get_project_model(p_id)
        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=u_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project concepts.")

        matched_map: dict[str, Concept] = {k: v for k, v in _IN_MEMORY_CONCEPTS.items() if v.project_id == p_id}
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(Concept).where(Concept.project_id == p_id)
                res = await self.db.execute(stmt)
                db_concepts = res.scalars().all()
                for conc in db_concepts:
                    matched_map[str(conc.id)] = conc
            except Exception:
                pass

        matched = list(matched_map.values())
        matched.sort(key=lambda x: getattr(x, "created_at", datetime.now(UTC)))
        return [
            ConceptResponse(
                id=c.id,
                project_id=c.project_id,
                name=c.name,
                definition=c.definition,
                domain=c.domain,
                created_at=c.created_at,
            )
            for c in matched
        ]

    async def list_project_chunks(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
    ) -> PaginatedChunksResponse:
        proj = await self.projects_service.get_project_model(project_id)
        auth_service = AuthService(self.db)
        has_access = await auth_service.check_space_access(
            user_id=user_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Access denied for project chunks.")

        matched_map: dict[str, KnowledgeChunk] = {k: v for k, v in _IN_MEMORY_CHUNKS.items() if v.project_id == project_id}
        if self.db is not None:
            try:
                from sqlalchemy import select
                stmt = select(KnowledgeChunk).where(KnowledgeChunk.project_id == project_id)
                res = await self.db.execute(stmt)
                db_chunks = res.scalars().all()
                for kc in db_chunks:
                    matched_map[str(kc.id)] = kc
            except Exception:
                pass

        matched = list(matched_map.values())
        matched.sort(key=lambda x: (x.page_number, x.chunk_index))

        total = len(matched)
        start = (page - 1) * limit
        end = start + limit
        paged = matched[start:end]

        items = [
            ChunkResponse(
                id=c.id,
                project_id=c.project_id,
                material_id=c.material_id,
                page_number=c.page_number,
                chunk_index=c.chunk_index,
                section_title=c.section_title,
                content=c.content,
                metadata_json=c.metadata_json,
                created_at=c.created_at,
            )
            for c in paged
        ]

        return PaginatedChunksResponse(items=items, total=total, page=page, limit=limit)
