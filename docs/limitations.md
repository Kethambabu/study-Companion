# Technical Limitations & Trade-Offs

## Overview

In the interest of full technical transparency, this document details the current engineering boundaries, OCR constraints, LLM rate limits, and operational trade-offs of the AI Prof platform.

---

## 1. Document Parsing & OCR Constraints
- **PyMuPDF Plain Text Engine**: Document text extraction currently relies on vector text extraction in PDFs. Complex scanned images without embedded text layers require Tesseract OCR pre-processing.
- **Large Document Processing**: PDF uploads over 50MB or 200 pages are rejected by current buffer limits to maintain fast response times.

---

## 2. LLM Context Window & Rate Limits
- **Free-Tier API Rate Limits**: When operating on free-tier Groq (`llama-3.3-70b-versatile`) or Gemini (`gemini-1.5-flash`) API keys, burst requests (>30 req/min) can trigger HTTP 429 RateLimitExceeded errors.
- **Fallback Engine**: The system recovers automatically using `MockLLMProvider`, but complex reasoning is reduced to template fallbacks during rate-limit windows.

---

## 3. Vector Search & RAG Boundaries
- **Chunk Size Bound**: Fixed 500-character chunking window may split complex mathematical proofs spanning multiple pages.
- **Local Embedding In-Memory Fallback**: Local ChromaDB instance operates in single-node mode. Clustering requires external vector services (e.g., Qdrant or Pgvector).

---

## 4. Background Job Worker Scale
- **In-Memory Worker Fallback**: When Redis is not configured, background tasks run on Python asyncio task loops. Multi-container production setups must attach external Redis message brokers.
