import hashlib
import json
import logging
import random
import re
from typing import Literal

from pydantic import ValidationError

from app.core.exceptions import LLMGenerationError
from app.modules.assessment.schemas import GeneratedQuestionSchema

logger = logging.getLogger(__name__)


def compute_question_fingerprint(question_text: str) -> str:
    """Computes a normalized text hash fingerprint for semantic duplicate detection."""
    clean = re.sub(r"\[ref-\w+\]", "", question_text, flags=re.IGNORECASE)
    clean = re.sub(r"\(focus:.*?\)", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\(depth:.*?\)", "", clean, flags=re.IGNORECASE)
    clean_text = re.sub(r"[^\w\s]", "", clean.lower()).strip()
    return hashlib.sha256(clean_text.encode("utf-8")).hexdigest()[:32]


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
            cognitive_stems = [
                f"Which design principle best governs the application of '{concept_id}'",
                f"How should an engineer analyze the performance profile of '{concept_id}'",
                f"What key architectural pattern best optimizes '{concept_id}'",
                f"Which primary failure mode must be guarded against when operating '{concept_id}'",
                f"In a production system utilizing '{concept_id}'",
                f"How does state transformation proceed during execution of '{concept_id}'",
                f"Which deployment strategy minimizes risk when implementing '{concept_id}'",
                f"What fundamental tradeoff governs resource allocation for '{concept_id}'",
                f"How can runtime telemetry best detect anomalies in '{concept_id}'",
                f"Which misconception regarding '{concept_id}' often leads to runtime bugs",
                f"When refactoring critical components that handle '{concept_id}'",
                f"What validation check prevents data corruption during operations on '{concept_id}'",
                f"How does system scalability impact the behavior of '{concept_id}'",
                f"Which isolation boundary is recommended when configuring '{concept_id}'",
                f"What step-by-step mechanism drives the execution of '{concept_id}'",
                f"Which concurrency control mechanism protects shared resources in '{concept_id}'",
                f"How should backpressure be managed when processing stream events for '{concept_id}'",
                f"What strategy ensures zero-downtime database migration when modifying '{concept_id}'",
                f"Which security validation step is required to prevent injection attacks on '{concept_id}'",
                f"How does asynchronous execution alter the call stack during invocation of '{concept_id}'",
                f"Which caching policy minimizes memory churn for frequent reads of '{concept_id}'",
                f"What telemetry metric provides the earliest signal of degradation in '{concept_id}'",
                f"How should error handling be structured for idempotent retries of '{concept_id}'",
                f"Which API design pattern maintains backwards compatibility when updating '{concept_id}'",
                f"What invariant must hold true across all state transitions in '{concept_id}'",
            ]

            scenarios = [
                "in high-throughput real-time data pipelines",
                "within distributed state management workflows",
                "under memory-constrained execution environments",
                "for fault-tolerant disaster recovery architectures",
                "during API rate limiting and payload validation",
                "in concurrent thread synchronization tasks",
                "for database query optimization and indexing",
                "under strict security isolation and access control rules",
                "in event-driven microservices messaging",
                "during edge case handling and network partition recovery",
                "for automated schema evolution and regression testing",
                "in latency-sensitive batch processing workloads",
                "during active cluster failover and leader election",
                "within multi-tenant isolated container environments",
                "for asynchronous job queue execution and worker polling",
                "during high-concurrency peak load events",
                "for cross-region database replication and synchronization",
                "under strict zero-trust network policy enforcement",
                "in continuous integration and blue-green deployments",
                "for event sourcing and immutable audit log retention",
            ]

            seed_val = (variation_seed * 10007 + question_index * 37 + 13) & 0x7FFFFFFF
            rng = random.Random(seed_val)

            stem = rng.choice(cognitive_stems)
            scenario = rng.choice(scenarios)
            var_token = f"[Ref-{seed_val % 9999:04d}]"

            if question_type == "mcq":
                mcq_aspects = [
                    "core mechanism",
                    "practical workflow",
                    "anti-pattern avoidance",
                    "performance tradeoff",
                    "state integrity",
                    "production monitoring",
                    "security isolation",
                    "concurrency control",
                    "error recovery",
                    "scalability limits",
                ]
                aspect = rng.choice(mcq_aspects)
                q_text = f"{stem} {scenario}? {var_token} (Focus: {aspect.title()})"

                options_by_aspect = {
                    "core mechanism": {
                        "correct": f"Enforce deterministic input validation and verify operational invariants for '{concept_id}' {scenario}.",
                        "distractors": [
                            f"Rely on uninitialized global state memory without runtime validation.",
                            f"Suppress boundary exceptions and execute callbacks out of order.",
                            f"Hardcode volatile memory pointers directly in application logic.",
                            f"Bypass type safety checks and execute untyped binary streams.",
                        ],
                    },
                    "practical workflow": {
                        "correct": f"Structure modular data pipelines using validated request contracts for '{concept_id}' {scenario}.",
                        "distractors": [
                            f"Bypass input sanitization and execute raw unvalidated user payloads.",
                            f"Disable error handling and deploy uncompiled source code.",
                            f"Execute unsynchronized background threads without concurrency locks.",
                            f"Hardcode environment secrets directly in public repository files.",
                        ],
                    },
                    "anti-pattern avoidance": {
                        "correct": f"Avoid unvalidated state mutation and silent exception swallowing when using '{concept_id}'.",
                        "distractors": [
                            f"Enforce strict schema bounds and monitor error rate trends.",
                            f"Run comprehensive regression test suites before production deployment.",
                            f"Emit structured runtime metrics to telemetry collectors.",
                            f"Validate parameter bounds prior to processing state updates.",
                        ],
                    },
                    "performance tradeoff": {
                        "correct": f"Balance memory allocation and cache bounds against query latency for '{concept_id}' {scenario}.",
                        "distractors": [
                            f"Assume zero memory overhead regardless of dataset volume.",
                            f"Expect zero network latency across distributed geographical nodes.",
                            f"Disregard garbage collection pause times during peak workload processing.",
                            f"Assume infinite bandwidth across unmetered network sockets.",
                        ],
                    },
                    "state integrity": {
                        "correct": f"Transition state via atomic transactional steps and explicit rollback boundaries for '{concept_id}'.",
                        "distractors": [
                            f"Randomly overwrite shared state slots without concurrency locks.",
                            f"Purge audit logs prior to completing state persistence.",
                            f"Ignore failed state transitions and return uninitialized pointers.",
                            f"Bypass atomic locks during concurrent database writes.",
                        ],
                    },
                    "production monitoring": {
                        "correct": f"Configure real-time latency alerts, error rate metrics, and health probes for '{concept_id}'.",
                        "distractors": [
                            f"Suppress diagnostic logs and disable system health probes.",
                            f"Expose administrative credentials in plain text execution logs.",
                            f"Disable all telemetry metrics and trace sample collection.",
                            f"Mute all production alerts during active system outages.",
                        ],
                    },
                    "security isolation": {
                        "correct": f"Enforce strict tenant authorization bounds and encrypt sensitive data payloads for '{concept_id}'.",
                        "distractors": [
                            f"Grant unrestricted root permissions to all incoming API calls.",
                            f"Disable SSL/TLS encryption for internal service communications.",
                            f"Store API secrets in unencrypted client-side web storage.",
                            f"Bypass access tokens when performing administrative updates.",
                        ],
                    },
                    "concurrency control": {
                        "correct": f"Use optimistic locking or mutex synchronization to prevent data races on '{concept_id}'.",
                        "distractors": [
                            f"Allow uncoordinated write access across shared memory pointers.",
                            f"Disable thread locks during peak execution periods.",
                            f"Ignore data race warnings in concurrent worker loops.",
                            f"Execute non-atomic read-modify-write state updates.",
                        ],
                    },
                    "error recovery": {
                        "correct": f"Implement exponential backoff retries with circuit breaker pattern for '{concept_id}'.",
                        "distractors": [
                            f"Infinitely retry failing requests without backoff delays.",
                            f"Crash the host process immediately upon network timeout.",
                            f"Ignore failed API calls and return empty null payloads.",
                            f"Log errors to standard error without triggering alert thresholds.",
                        ],
                    },
                    "scalability limits": {
                        "correct": f"Partition state shards and implement horizontal worker scaling for '{concept_id}'.",
                        "distractors": [
                            f"Consolidate all system state into a single unindexed database table.",
                            f"Disable connection pooling and open new socket per request.",
                            f"Rely exclusively on vertical CPU scaling for peak workloads.",
                            f"Hardcode maximum worker limits to single-threaded capacity.",
                        ],
                    },
                }

                asp_data = options_by_aspect[aspect]
                correct_text = asp_data["correct"]
                raw_distractors = list(asp_data["distractors"])
                rng.shuffle(raw_distractors)
                selected_distractors = raw_distractors[:3]

                all_choices = [correct_text] + selected_distractors
                rng.shuffle(all_choices)

                letters = ["Option A", "Option B", "Option C", "Option D"]
                formatted_options = []
                correct_formatted = ""

                for ltr, text in zip(letters, all_choices):
                    opt_str = f"{ltr}: {text}"
                    formatted_options.append(opt_str)
                    if text == correct_text:
                        correct_formatted = opt_str

                explanation = f"Correct choice ({correct_formatted[:8]}). Grounded in {concept_id} best practices for {aspect}."

                raw_json = {
                    "question_type": "mcq",
                    "question_text": q_text,
                    "options": formatted_options,
                    "correct_answer": correct_formatted,
                    "concept_id": concept_id,
                    "difficulty": difficulty,
                    "explanation": explanation,
                }
            else:
                open_ended_stems = [
                    f"Explain how to implement and troubleshoot '{concept_id}'",
                    f"Describe the architecture and data integrity checks required for '{concept_id}'",
                    f"Detail the step-by-step failure recovery and rollback mechanism for '{concept_id}'",
                    f"Analyze the performance bottlenecks and scaling strategies associated with '{concept_id}'",
                    f"Outline the security controls and access boundaries necessary when operating '{concept_id}'",
                    f"How would you refactor a legacy implementation to safely incorporate '{concept_id}'",
                    f"Design an automated testing and validation harness to verify '{concept_id}'",
                    f"Compare the tradeoffs of alternative design patterns versus '{concept_id}'",
                    f"What telemetry indicators and logging patterns should be configured for '{concept_id}'",
                    f"Detail the end-to-end event lifecycle and state transitions when executing '{concept_id}'",
                    f"How would you handle unexpected network partitions and split-brain scenarios when running '{concept_id}'",
                    f"Formulate a zero-downtime migration plan for updating schemas dependent on '{concept_id}'",
                    f"Explain the memory management and garbage collection impact of using '{concept_id}'",
                    f"Describe how concurrency locks and optimistic transactions preserve state in '{concept_id}'",
                    f"Propose an SLA monitoring strategy and SLO alert threshold for services using '{concept_id}'",
                ]
                oe_stem = rng.choice(open_ended_stems)
                q_text = f"{oe_stem} {scenario}. What steps ensure correctness? {var_token} (Depth: {difficulty.title()})"
                raw_json = {
                    "question_type": "open_ended",
                    "question_text": q_text,
                    "options": None,
                    "correct_answer": f"Key criteria: Detail step-by-step execution for {concept_id}, scenario constraints ({scenario}), validation rules, and error recovery.",
                    "concept_id": concept_id,
                    "difficulty": difficulty,
                    "explanation": f"Open-ended grounded evaluation assessing synthesis of {concept_id} under {scenario}.",
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


