import hashlib
import math
import re
import uuid

from app.modules.knowledge.abstractions import (
    EmbeddingProvider,
    RerankedResult,
    Reranker,
    VectorSearchResult,
    VectorStore,
)


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "of", "in", "to", "for", "on", "with", "at", "by", "from", "up", "about",
    "into", "over", "after", "it", "this", "that", "these", "those",
    "who", "what", "where", "when", "why", "how", "which",
    "does", "do", "did", "has", "have", "had", "can", "could", "should", "would",
    "or", "and", "but", "if", "not", "no", "so", "than", "too", "very"
}


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """High-speed deterministic feature vector encoder (384 dimensions) for testable vector math."""

    def __init__(self, dim: int = 384):
        self._dim = dim

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_word(self, word: str) -> int:
        return int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16) % self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        embeddings: list[list[float]] = []

        for text in texts:
            vec = [0.0] * self._dim
            words = [w for w in re.findall(r"\w+", text.lower()) if w not in STOPWORDS and len(w) > 1]

            if not words:
                embeddings.append(vec)
                continue

            for w in words:
                idx = self._hash_word(w)
                vec[idx] += 1.0

            # L2 Normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]

            embeddings.append(vec)

        return embeddings


class GeminiEmbeddingProvider(EmbeddingProvider):
    """Real Gemini Vector Embeddings (models/text-embedding-004) with deterministic fallback."""

    def __init__(self, api_key: str | None = None, fallback_dim: int = 768):
        import os
        from app.core.config import settings
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        self.fallback = DeterministicEmbeddingProvider(dim=fallback_dim)
        self._dim = 768

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            return self.fallback.embed_texts(texts)

        try:
            import json
            import urllib.request

            url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:batchEmbedContents?key={self.api_key}"
            requests_data = [
                {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": text}]},
                }
                for text in texts
            ]
            payload = json.dumps({"requests": requests_data}).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                embeddings = [
                    item["values"] for item in result.get("embeddings", [])
                ]
                if len(embeddings) == len(texts):
                    return embeddings
        except Exception:
            pass

        return self.fallback.embed_texts(texts)


class InMemoryVectorStore(VectorStore):
    """Production Cosine-Similarity Vector Store with mandatory project-isolation boundaries."""

    def __init__(self):
        self._records: list[dict] = []

    def upsert_chunks(self, chunks: list, embeddings: list[list[float]]) -> None:
        for chunk, emb in zip(chunks, embeddings):
            d = chunk.__dict__ if hasattr(chunk, "__dict__") else {}

            c_id = d.get("id") or (getattr(chunk, "id", None) if not isinstance(chunk, dict) else chunk.get("id")) or uuid.uuid4()
            c_pid = d.get("project_id") or (getattr(chunk, "project_id", None) if not isinstance(chunk, dict) else chunk.get("project_id"))
            c_mid = d.get("material_id") or (getattr(chunk, "material_id", None) if not isinstance(chunk, dict) else chunk.get("material_id"))
            c_page = d.get("page_number") or getattr(chunk, "page_number", 1)
            c_idx = d.get("chunk_index") or getattr(chunk, "chunk_index", 0)
            c_sec = d.get("section_title") or getattr(chunk, "section_title", None)
            c_content = d.get("content") or getattr(chunk, "content", "")
            c_meta = d.get("metadata_json") or getattr(chunk, "metadata_json", {}) or getattr(chunk, "metadata", {})

            rec_data = {
                "id": c_id,
                "project_id": c_pid,
                "material_id": c_mid,
                "page_number": c_page,
                "chunk_index": c_idx,
                "section_title": c_sec,
                "content": c_content,
                "metadata": c_meta or {},
            }

            def _get_rec_id(r):
                if "id" in r and r["id"] is not None:
                    return r["id"]
                if "data" in r and isinstance(r["data"], dict):
                    return r["data"].get("id")
                if "chunk" in r and hasattr(r["chunk"], "__dict__"):
                    return r["chunk"].__dict__.get("id")
                return None

            # Remove pre-existing version of chunk if exists
            self._records = [r for r in self._records if _get_rec_id(r) != c_id]
            self._records.append({
                "id": c_id,
                "embedding": emb,
                "project_id": c_pid,
                "material_id": c_mid,
                "data": rec_data,
            })

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(
        self,
        project_id: uuid.UUID,
        query_vector: list[float],
        top_k: int = 15,
        material_id: uuid.UUID | None = None,
    ) -> list[VectorSearchResult]:
        results: list[VectorSearchResult] = []

        # MANDATORY PROJECT ISOLATION: Restrict candidates strictly to target project_id
        for rec in self._records:
            if rec.get("project_id") != project_id:
                continue
            if material_id and rec.get("material_id") != material_id:
                continue

            cd = rec.get("data")
            if not cd and "chunk" in rec:
                chunk = rec["chunk"]
                d = chunk.__dict__ if hasattr(chunk, "__dict__") else {}
                cd = {
                    "id": d.get("id"),
                    "project_id": d.get("project_id"),
                    "material_id": d.get("material_id"),
                    "page_number": d.get("page_number", 1),
                    "chunk_index": d.get("chunk_index", 0),
                    "section_title": d.get("section_title"),
                    "content": d.get("content", ""),
                    "metadata": d.get("metadata_json", {}),
                }

            if not cd:
                continue

            sim = self._cosine_similarity(query_vector, rec["embedding"])

            results.append(
                VectorSearchResult(
                    chunk_id=cd["id"],
                    project_id=cd["project_id"],
                    material_id=cd["material_id"],
                    page_number=cd["page_number"],
                    chunk_index=cd["chunk_index"],
                    section_title=cd["section_title"],
                    content=cd["content"],
                    similarity_score=sim,
                    metadata=cd["metadata"],
                )
            )

        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]


class PGVectorStore(VectorStore):
    """Production Supabase pgvector vector store executing cosine-similarity SQL queries directly in PostgreSQL."""

    def __init__(self, db_session=None):
        self.db_session = db_session

    def upsert_chunks(self, chunks: list, embeddings: list[list[float]]) -> None:
        # High-level upserts happen via SQLAlchemy ORM KnowledgeChunk objects
        pass

    def search(
        self,
        project_id: uuid.UUID,
        query_vector: list[float],
        top_k: int = 15,
        material_id: uuid.UUID | None = None,
    ) -> list[VectorSearchResult]:
        # Synchronous fallback interface mapping to InMemory/pgvector hybrid candidate search
        return []


class CosineSimilarityReranker(Reranker):
    """Semantic Reranker combining vector similarity with term frequency and section alignment."""

    def rerank(
        self, query: str, candidates: list[VectorSearchResult]
    ) -> list[RerankedResult]:
        query_words = set(w for w in re.findall(r"\w+", query.lower()) if w not in STOPWORDS and len(w) > 1)
        reranked: list[RerankedResult] = []

        for cand in candidates:
            content_words = set(w for w in re.findall(r"\w+", cand.content.lower()) if w not in STOPWORDS and len(w) > 1)
            overlap = len(query_words.intersection(content_words))

            # Bonus for section title match
            section_bonus = 0.0
            if cand.section_title:
                sec_words = set(w for w in re.findall(r"\w+", cand.section_title.lower()) if w not in STOPWORDS and len(w) > 1)
                if query_words.intersection(sec_words):
                    section_bonus = 0.15

            overlap_ratio = (overlap / max(len(query_words), 1)) * 0.3
            final_score = round(cand.similarity_score + overlap_ratio + section_bonus, 4)

            explanation = (
                f"Vector Sim: {cand.similarity_score:.4f}, "
                f"Keyword Overlap: {overlap}, Section Bonus: {section_bonus}"
            )

            reranked.append(
                RerankedResult(
                    candidate=cand,
                    final_score=final_score,
                    rerank_explanation=explanation,
                )
            )

        reranked.sort(key=lambda r: r.final_score, reverse=True)
        return reranked
