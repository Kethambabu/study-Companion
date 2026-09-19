# Antigravity Agent Development Prompts

## Overview

This document records the actual agentic prompts used during the development of AI Prof with **Antigravity** (Google Deepmind's Agentic Coding Assistant).

---

## Prompt Categories

### 1. Architecture & Domain Design
> "Design a multi-tenant SaaS learning platform architecture using FastAPI, PostgreSQL, ChromaDB, and React. Include Domain-Driven Design (DDD) module boundaries for auth, spaces, projects, materials, tutor, assessment, mastery, and recommendations. Enforce strict tenant isolation where User A cannot access User B's resources."

### 2. Database & Data Isolation
> "Create SQLAlchemy ORM models for profiles, spaces, memberships, projects, materials, material_chunks, tutor_conversations, quizzes, concept_mastery, mastery_events, and learning_events. Implement Row Level Security (RLS) policies and tenant isolation checks via AuthService.check_space_access."

### 3. AI & RAG Subsystem
> "Build a grounded RAG pipeline using PyMuPDF for text extraction, recursive 500-character chunking, ChromaDB for vector indexing, and Groq/Gemini API providers. Wrap untrusted study document text in <untrusted_study_material> tags to prevent prompt injection and add a CitationValidator to strip hallucinated citations."

### 4. Deterministic Concept Mastery Engine
> "Build a testable, deterministic concept mastery engine that incorporates evidence such as assessment performance, question difficulty, repeated mistakes, recent activity, and open-ended evaluation scores. Store explainable mastery snapshots with previous score, new score, and evidence type."

### 5. Event-Driven Workflow & Worker Reliability
> "Implement an asynchronous event-driven workflow using learning_events. Deduplicate events via idempotency keys, create a retry classifier for retryable vs non-retryable errors, and ensure background workers recover cleanly from partial failures."

### 6. Security Audit & Hardening
> "Perform a senior staff engineer security audit of the backend. Verify JWT authentication, RBAC authorization, prompt injection containment, CORS configuration, exception handling middleware, and add security test cases proving tenant isolation across all endpoints."

### 7. Evaluation & Observability
> "Build an AI system evaluation subsystem in evaluation/ with benchmark datasets for tutor groundedness, retrieval recall, assessment schemas, and recommendation alignment. Create an automated CLI evaluation script run_eval.py that calculates quantitative benchmark scores."

### 8. Production SaaS Readiness & Documentation
> "Prepare Phase 11 SaaS productization pass. Implement production health check endpoints, configure Vercel, Render, and Supabase environment templates, compile complete technical documentation suite in docs/, and build an end-to-end integration test suite."
