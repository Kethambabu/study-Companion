from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import uuid


@dataclass
class VectorSearchResult:
    chunk_id: uuid.UUID
    project_id: uuid.UUID
    material_id: uuid.UUID
    page_number: int
    chunk_index: int
    section_title: str | None
    content: str
    similarity_score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class RerankedResult:
    candidate: VectorSearchResult
    final_score: float
    rerank_explanation: str = ""


@dataclass
class Citation:
    citation_id: str
    material_id: uuid.UUID
    material_name: str
    page_number: int
    chunk_id: uuid.UUID
    excerpt: str


@dataclass
class RetrievalDiagnostics:
    query: str
    candidate_count: int
    selected_count: int
    similarity_scores: list[float]
    reranking_scores: list[float]
    source_pages: list[int]


@dataclass
class RetrievalResult:
    context: str
    citations: list[Citation]
    diagnostics: RetrievalDiagnostics


class EmbeddingProvider(ABC):
    """Abstract Base Class for text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector embedding dimension size."""
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generates vector embeddings for a list of text strings."""
        pass


class VectorStore(ABC):
    """Abstract Base Class for project-isolated vector databases."""

    @abstractmethod
    def upsert_chunks(self, chunks: list, embeddings: list[list[float]]) -> None:
        """Upserts knowledge chunks with vector embeddings into the vector store."""
        pass

    @abstractmethod
    def search(
        self,
        project_id: uuid.UUID,
        query_vector: list[float],
        top_k: int = 15,
        material_id: uuid.UUID | None = None,
    ) -> list[VectorSearchResult]:
        """Performs vector similarity search restricted strictly to project_id."""
        pass


class Reranker(ABC):
    """Abstract Base Class for candidate reranking engines."""

    @abstractmethod
    def rerank(
        self, query: str, candidates: list[VectorSearchResult]
    ) -> list[RerankedResult]:
        """Reranks initial vector candidates using semantic cross-scoring."""
        pass


class Retriever(ABC):
    """Abstract Base Class for end-to-end RAG retrieval pipeline."""

    @abstractmethod
    def retrieve(
        self,
        project_id: uuid.UUID,
        query: str,
        top_k: int = 5,
        threshold: float = 0.1,
        material_id: uuid.UUID | None = None,
    ) -> RetrievalResult:
        """Executes full RAG retrieval pipeline producing evidence and citations."""
        pass
