# AI Study Companion — Backend Failure Modes & Recovery Catalog

## Overview

This catalog documents failure scenarios, detection mechanisms, retry behaviors, and recovery strategies implemented across all backend subsystems.

---

## 1. AI Provider Failures

| Failure Scenario | Detection Mechanism | Mitigation & Fallback Behavior | Recovery / User Impact |
|------------------|---------------------|--------------------------------|------------------------|
| **LLM Provider API Timeout (>15s)** | `httpx.TimeoutException` | Primary provider times out; system catches exception and seamlessly routes request to `MockLLMProvider` or secondary provider (Gemini/Groq). | User receives grounded response from fallback provider without request drop (`504 Gateway Timeout` avoided). |
| **LLM Rate Limit Exceeded (HTTP 429)** | `httpx.HTTPStatusError` (429) | Provider router catches status code 429 and failover routes completion call to alternate tier. | Request succeeds; telemetry logs `status='rate_limited_fallback'`. |
| **Malformed LLM Output (JSON schema mismatch)** | `pydantic.ValidationError` / `json.JSONDecodeError` | `QuestionGenerator` and `QuestionEvaluator` trap validation exceptions, log error trace, and invoke safe structured fallback schema generator. | Student receives structured fallback evaluation; system state remains uncorrupted. |
| **Fabricated Citations (LLM hallucinating `[99]` tags)** | `CitationValidator.validate_citations` | Cross-checks generated citation tags against available retrieved chunks; strips unverified tags from response. | Untrusted citation tags removed; zero fake citations displayed to user. |

---

## 2. Document Processing & File Failures

| Failure Scenario | Detection Mechanism | Mitigation & Fallback Behavior | Recovery / User Impact |
|------------------|---------------------|--------------------------------|------------------------|
| **Empty or Corrupt PDF File** | PyMuPDF `fitz.open()` raise `fitz.FileDataError` | Caught in `PyMuPDFExtractor`; material status marked as `failed`, `MaterialProcessingJob` records error message. | Non-retryable error classification avoids worker loops; API returns user-facing error message explaining corrupt file. |
| **Scanned / Image-Only PDF Pages** | Text length check (`len(text.strip()) < 10`) | `PyMuPDFExtractor` automatically renders page pixmap to PNG and invokes `OCRProvider` fallback. | Text extracted via OCR engine; metadata flag set to `extraction_method='ocr_fallback'`. |
| **Duplicate PDF Upload** | SHA-256 Checksum matching on `(project_id, checksum)` | `MaterialsService` checks existing material checksums; returns pre-existing material record. | Duplicate file upload prevented; duplicate storage consumption eliminated. |

---

## 3. Background Workers & Redis Broker Failures

| Failure Scenario | Detection Mechanism | Mitigation & Fallback Behavior | Recovery / User Impact |
|------------------|---------------------|--------------------------------|------------------------|
| **Celery Broker / Redis Connection Offline** | `redis.exceptions.ConnectionError` | `_enqueue_material_processing_task` catches connection exception and falls back to non-blocking asyncio event loop inline task execution. | Document processing completes inline on API process without background task drop. |
| **Worker Process Crash Mid-Execution** | Celery task heartbeat timeout / task state tracking | Celery re-queues unacknowledged task (`acks_late = True`); task execution is idempotent. | Task re-executed by secondary worker upon restart. |
| **Transient Processing Error (Network glitch)** | Task raises transient `RuntimeError` | Celery retries task up to `max_retries=3` with exponential backoff (`countdown = 2 ** retries`). | Transient error resolves automatically on retry. |

---

## 4. Vector Search & RAG Failures

| Failure Scenario | Detection Mechanism | Mitigation & Fallback Behavior | Recovery / User Impact |
|------------------|---------------------|--------------------------------|------------------------|
| **Zero Relevant Chunks Retrieved (No Evidence)** | Similarity score below threshold (`score < 0.05`) | `KnowledgeService.search_knowledge` returns empty context; LLM provider sets `confidence_status = 'insufficient_evidence'`. | Tutor responds: *"I do not have sufficient evidence in your uploaded study materials..."* — preventing hallucination. |
| **Cross-Project Retrieval Attempt** | Candidate search loop checks `rec['project_id'] == target_project_id` | Candidate filtering strictly discards any vector match outside `target_project_id`. | Zero data leak between isolated projects. |

---

## 5. Multi-Tenancy & Authorization Violations

| Failure Scenario | Detection Mechanism | Mitigation & Fallback Behavior | Recovery / User Impact |
|------------------|---------------------|--------------------------------|------------------------|
| **User A accesses User B Resource** | `AuthService.check_space_access()` role check | Raises `TenantAccessDeniedError`; API exception handler returns `HTTP 403 Forbidden` / `404 Not Found`. | Unauthorized request blocked; audit log records security attempt. |
| **Non-Admin user accesses Admin API** | `require_admin_user` dependency | Verifies `current_user.role == 'admin'`; raises `TenantAccessDeniedError` if false (`HTTP 403`). | Admin APIs strictly protected. |
