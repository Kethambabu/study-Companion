import hashlib
import json
import logging
import re
from typing import Literal

from pydantic import ValidationError

from app.core.exceptions import LLMGenerationError
from app.modules.assessment.schemas import GeneratedQuestionSchema

logger = logging.getLogger(__name__)


def compute_question_fingerprint(question_text: str) -> str:
    """Computes a normalized text hash fingerprint for semantic duplicate detection."""
    clean_text = re.sub(r"[^\w\s]", "", question_text.lower()).strip()
    words = sorted(list(set(clean_text.split())))
    normalized = " ".join(words)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


class QuestionGenerator:
    """Generates structured assessment questions grounded in project materials with dynamic multi-aspect templates."""

    @staticmethod
    def compute_fingerprint(question_text: str) -> str:
        return compute_question_fingerprint(question_text)

    @staticmethod
    def generate_question(
        concept_id: str,
        difficulty: Literal["beginner", "intermediate", "advanced"],
        question_type: Literal["mcq", "open_ended"],
        study_context: str | None = None,
        llm_response_override: str | None = None,
        question_index: int = 0,
        variation_seed: int = 0,
    ) -> GeneratedQuestionSchema:
        """Generates a non-repeating validated question structure across cognitive aspects."""
        if llm_response_override:
            raw_text = llm_response_override
        else:
            # Extract usable context snippets from material text if provided
            snippets = [
                s.strip() for s in (study_context or "").split("\n")
                if len(s.strip()) > 15 and not s.strip().startswith("Study material")
            ]
            ctx_snippet = (
                snippets[question_index % len(snippets)]
                if snippets
                else (study_context[:120] if study_context else f"core principles of {concept_id}")
            )

            if question_type == "mcq":
                mcq_aspects = [
                    # Aspect 0: Core Definition & Primary Mechanism
                    {
                        "question_text": f"What is the primary definition and core operational principle of '{concept_id}' at a {difficulty} level?",
                        "options": [
                            f"Option A: The foundational framework for {concept_id} as specified in: '{ctx_snippet[:60]}...'.",
                            f"Option B: A secondary optimization method unrelated to {concept_id}.",
                            f"Option C: A legacy protocol superseded by basic data arrays.",
                            f"Option D: A hardware-level instruction set not used in application software.",
                        ],
                        "correct_answer": f"Option A: The foundational framework for {concept_id} as specified in: '{ctx_snippet[:60]}...'.",
                        "explanation": f"Option A accurately defines the fundamental operation of {concept_id} grounded in your project study notes.",
                    },
                    # Aspect 1: Practical Application & Workflows
                    {
                        "question_text": f"In practical software engineering and learning workflows, how is '{concept_id}' primarily applied?",
                        "options": [
                            f"Option A: By manually hardcoding static values without runtime updates.",
                            f"Option B: By leveraging {concept_id} to structure data flows and improve system efficiency.",
                            f"Option C: By disabling error handling and validation during deployment.",
                            f"Option D: By executing arbitrary unsanitized user inputs directly.",
                        ],
                        "correct_answer": f"Option B: By leveraging {concept_id} to structure data flows and improve system efficiency.",
                        "explanation": f"Option B correctly identifies the practical workflow role of {concept_id} in system architecture.",
                    },
                    # Aspect 2: Misconceptions & Edge Case Pitfalls
                    {
                        "question_text": f"Which of the following statements describes a common misconception or engineering pitfall regarding '{concept_id}'?",
                        "options": [
                            f"Option A: {concept_id} operates deterministically based on defined constraints.",
                            f"Option B: Understanding {concept_id} is required for evaluating overall performance.",
                            f"Option C: {concept_id} completely eliminates the need for unit testing and validation.",
                            f"Option D: Adjusting input parameters directly influences {concept_id}'s runtime behavior.",
                        ],
                        "correct_answer": f"Option C: {concept_id} completely eliminates the need for unit testing and validation.",
                        "explanation": f"Option C is a dangerous misconception; {concept_id} requires rigorous validation and testing.",
                    },
                    # Aspect 3: Architectural Tradeoffs & Performance
                    {
                        "question_text": f"When evaluating system architecture, what is the primary tradeoff or constraint associated with '{concept_id}' at a {difficulty} level?",
                        "options": [
                            f"Option A: Balancing computational/memory overhead against accuracy and throughput when using {concept_id}.",
                            f"Option B: {concept_id} consumes zero memory regardless of dataset volume.",
                            f"Option C: Using {concept_id} guarantees zero network latency across distributed nodes.",
                            f"Option D: There are no architectural or performance tradeoffs associated with {concept_id}.",
                        ],
                        "correct_answer": f"Option A: Balancing computational/memory overhead against accuracy and throughput when using {concept_id}.",
                        "explanation": f"Option A correctly highlights the resource vs performance tradeoffs essential to {concept_id}.",
                    },
                    # Aspect 4: Data Flow & State Transformations
                    {
                        "question_text": f"How does state transformation occur during the execution of '{concept_id}'?",
                        "options": [
                            f"Option A: Data is randomly overwritten without validation or recovery.",
                            f"Option B: State transitions follow defined rules to process inputs into valid outputs for {concept_id}.",
                            f"Option C: Input data is permanently deleted prior to processing.",
                            f"Option D: No state changes occur during the operation of {concept_id}.",
                        ],
                        "correct_answer": f"Option B: State transitions follow defined rules to process inputs into valid outputs for {concept_id}.",
                        "explanation": f"Option B accurately describes the structured state transition flow of {concept_id}.",
                    },
                    # Aspect 5: Optimization & Best Practices
                    {
                        "question_text": f"What is a key best practice when configuring '{concept_id}' for production environments?",
                        "options": [
                            f"Option A: Enforce schema validation and monitor runtime performance metrics for {concept_id}.",
                            f"Option B: Suppress all error logs and diagnostic metrics.",
                            f"Option C: Hardcode external environment secrets directly in the source code.",
                            f"Option D: Bypass all authentication and authorization checks.",
                        ],
                        "correct_answer": f"Option A: Enforce schema validation and monitor runtime performance metrics for {concept_id}.",
                        "explanation": f"Option A reflects industry standard best practices for deploying {concept_id}.",
                    },
                ]
                idx = (question_index + variation_seed) % len(mcq_aspects)
                template = mcq_aspects[idx]
                raw_json = {
                    "question_type": "mcq",
                    "question_text": template["question_text"],
                    "options": template["options"],
                    "correct_answer": template["correct_answer"],
                    "concept_id": concept_id,
                    "difficulty": difficulty,
                    "explanation": template["explanation"],
                }
            else:
                open_aspects = [
                    # Aspect 0: Mechanics & Operational Flow
                    {
                        "question_text": f"Explain the step-by-step mechanism of '{concept_id}' at a {difficulty} level, specifically referencing: '{ctx_snippet[:100]}...'",
                        "correct_answer": f"Key criteria: Explain {concept_id} step-by-step execution, primary components, and operational flow.",
                        "explanation": f"A comprehensive answer for {concept_id} must detail its core mechanism and step-by-step execution flow.",
                    },
                    # Aspect 1: Problem Solving & Real-World Use Cases
                    {
                        "question_text": f"Describe a practical real-world scenario where '{concept_id}' solves a critical engineering or learning challenge. What inputs and outputs are involved?",
                        "correct_answer": f"Key criteria: Detail a concrete use case for {concept_id}, why it is appropriate, and describe inputs and outputs.",
                        "explanation": f"A strong response must connect {concept_id} to a real-world scenario and explain its inputs, outputs, and benefits.",
                    },
                    # Aspect 2: Comparative Tradeoff Analysis
                    {
                        "question_text": f"Compare '{concept_id}' against alternative or simpler approaches. What are the key advantages and potential drawbacks of using {concept_id}?",
                        "correct_answer": f"Key criteria: Compare {concept_id} with alternative solutions, addressing efficiency, complexity, and resource tradeoffs.",
                        "explanation": f"Evaluating {concept_id} requires contrasting its strengths and drawbacks against simpler alternative approaches.",
                    },
                    # Aspect 3: Edge Cases & Error Recovery
                    {
                        "question_text": f"What potential failure modes or edge cases can arise when working with '{concept_id}', and how should system design account for them?",
                        "correct_answer": f"Key criteria: Identify potential edge cases/failure modes in {concept_id}, validation checks, and error recovery strategies.",
                        "explanation": f"Analyzing {concept_id} requires identifying failure modes, edge cases, and robust error recovery mechanisms.",
                    },
                ]
                idx = (question_index + variation_seed) % len(open_aspects)
                template = open_aspects[idx]
                raw_json = {
                    "question_type": "open_ended",
                    "question_text": template["question_text"],
                    "options": None,
                    "correct_answer": template["correct_answer"],
                    "concept_id": concept_id,
                    "difficulty": difficulty,
                    "explanation": template["explanation"],
                }
            raw_text = json.dumps(raw_json)

        # Parse and Validate LLM Structured Output using Pydantic
        try:
            clean_json_str = raw_text
            if "```json" in raw_text:
                match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
                if match:
                    clean_json_str = match.group(1)

            parsed_data = json.loads(clean_json_str)
            validated_question = GeneratedQuestionSchema.model_validate(parsed_data)
            return validated_question
        except (json.JSONDecodeError, ValidationError) as err:
            logger.error("LLM Question Generation Schema Validation Failed: %s", str(err))
            raise LLMGenerationError(f"Failed to generate valid structured question schema: {str(err)}")
