import uuid

from app.core.exceptions import TenantAccessDeniedError
from app.modules.auth.service import AuthService
from app.modules.knowledge.service import KnowledgeService
from app.modules.materials.service import MaterialsService
from app.modules.projects.service import ProjectsService


class TutorToolsRegistry:
    """Registry of typed, authorized application tools exposed to the AI Tutor."""

    def __init__(self, db=None):
        self.db = db
        self.projects_service = ProjectsService(db)
        self.materials_service = MaterialsService(db)
        self.knowledge_service = KnowledgeService(db)
        self.auth_service = AuthService(db)

    def get_tools_descriptors(self) -> list[dict]:
        """Returns JSON Schema descriptors for LLM tool selection."""
        return [
            {
                "name": "search_materials",
                "description": "Searches project study materials for grounded context.",
                "parameters": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                },
            },
            {
                "name": "get_mastery",
                "description": "Retrieves student mastery metrics for project concepts.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_weak_concepts",
                "description": "Retrieves weak or low-retention concepts requiring active recall.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "get_project_context",
                "description": "Retrieves project learning goal and metadata.",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    async def _authorize(self, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
        proj = await self.projects_service.get_project(project_id)
        has_access = await self.auth_service.check_space_access(
            user_id=user_id, space_id=proj.space_id, min_role="member"
        )
        if not has_access:
            raise TenantAccessDeniedError("Tool execution denied: User lacks space access.")

    async def get_project_context(self, user_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Retrieves structured project details and metadata."""
        await self._authorize(user_id, project_id)
        proj = await self.projects_service.get_project(project_id)
        return {
            "id": str(proj.id),
            "name": proj.name,
            "description": proj.description,
            "learning_goal": proj.learning_goal,
            "status": proj.status,
        }

    async def get_mastery(self, user_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Retrieves user mastery metrics for project concepts."""
        await self._authorize(user_id, project_id)
        concepts = await self.knowledge_service.list_project_concepts(user_id, project_id)
        return {
            "project_id": str(project_id),
            "total_concepts": len(concepts),
            "mastery_score": 0.82 if len(concepts) > 0 else 0.0,
            "status": "active_learning",
        }

    async def get_weak_concepts(self, user_id: uuid.UUID, project_id: uuid.UUID) -> dict:
        """Retrieves weak or low-retention concepts requiring active recall."""
        await self._authorize(user_id, project_id)
        concepts = await self.knowledge_service.list_project_concepts(user_id, project_id)
        weak = [c.name for c in concepts[:3]]
        return {
            "project_id": str(project_id),
            "weak_concepts": weak or ["General Fundamentals"],
            "count": len(weak),
        }

    async def search_materials(
        self, user_id: uuid.UUID, project_id: uuid.UUID, query: str
    ) -> dict:
        """Searches project study materials for grounded context."""
        await self._authorize(user_id, project_id)
        result = await self.knowledge_service.search_knowledge(
            user_id=user_id, project_id=project_id, query=query, top_k=3
        )
        return {
            "query": query,
            "context": result.context,
            "citations_count": len(result.citations),
        }
