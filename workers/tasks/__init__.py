from workers.tasks.assessment_tasks import evaluate_quiz_submission_task
from workers.tasks.knowledge_tasks import index_material_knowledge_task
from workers.tasks.maintenance_tasks import system_health_check_task
from workers.tasks.mastery_tasks import update_concept_mastery_task
from workers.tasks.material_tasks import process_material_task
from workers.tasks.recommendation_tasks import generate_recommendations_task

__all__ = [
    "process_material_task",
    "index_material_knowledge_task",
    "evaluate_quiz_submission_task",
    "update_concept_mastery_task",
    "generate_recommendations_task",
    "system_health_check_task",
]
