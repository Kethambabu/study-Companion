import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.materials.models import Material
from app.modules.projects.models import Project


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    @property
    def embedding(self):
        return getattr(self, "_emb_vec", None)

    @embedding.setter
    def embedding(self, val):
        self._emb_vec = val

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    project: Mapped["Project"] = relationship("Project")
    material: Mapped["Material"] = relationship("Material")

    __table_args__ = (
        Index("idx_chunks_project_id", "project_id"),
        Index("idx_chunks_material_id", "material_id"),
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    domain: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    project: Mapped["Project"] = relationship("Project")

    __table_args__ = (
        Index("idx_concepts_project_id", "project_id"),
        Index("idx_concepts_name", "project_id", "name", unique=True),
    )


class ConceptRelationship(Base):
    __tablename__ = "concept_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    target_concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="related_to"
    )  # prerequisite, part_of, related_to

    __table_args__ = (
        Index("idx_rel_project_id", "project_id"),
        Index("idx_rel_source_target", "source_concept_id", "target_concept_id", unique=True),
    )


class MaterialConceptLink(Base):
    __tablename__ = "material_concept_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    __table_args__ = (
        Index("idx_link_mat_concept", "material_id", "concept_id", unique=True),
    )
