# AI Subsystem & Dual AI Model Usage Architecture

This document explicitly demarcates the dual role of Artificial Intelligence within the AI Prof platform:
1. **AI Used to Build the Product** (Development Phase via Antigravity).
2. **AI Operating Inside the Product** (Runtime Intelligence Engine).

---

## 1. AI Used to Build the Product (Development Phase)

The entire AI Prof SaaS platform was designed, engineered, and hardened using **Antigravity**, Google Deepmind's agentic AI pair programmer.

### Development Assistance Breakdown:
- **Architectural Design**: Domain-Driven Design (DDD) domain boundaries, database schema layout, and multi-tenant isolation patterns.
- **Backend Engineering**: FastAPI routes, Pydantic V2 validation schemas, SQLAlchemy ORM async database models, and custom middleware.
- **AI Subsystem Design**: RAG text chunking, ChromaDB vector store integration, grounded citation validator, and adaptive assessment generator.
- **Security Audit & Production Hardening**: RLS security verification, prompt injection defense, exception handling middleware, and E2E test suites.
- **Frontend Engineering**: Component hierarchy, TailwindCSS glassmorphism UI, Recharts data visualization dashboards, and error boundaries.

---

## 2. AI Operating Inside the Product (Runtime Engine)

The runtime application features an abstract multi-provider AI engine ([`AbstractLLMProvider`](file:///c:/Users/ADMIN/OneDrive/Desktop/ai_prof/backend/app/modules/tutor/abstractions.py)).

### Runtime Provider Architecture:
- **Primary Provider**: Groq API (`llama-3.3-70b-versatile`) for high-throughput, low-latency grounded tutor responses.
- **Secondary Provider**: Google Gemini API (`gemini-1.5-flash`) for complex structured question generation and evaluation.
- **Fallback Provider**: `MockLLMProvider` delivering deterministic grounded responses when external AI keys are unavailable.

### AI Core Functions:
1. **Grounded RAG Tutoring**: Takes retrieved study material chunks enclosed in `<untrusted_study_material>` tags and generates step-by-step explanations with citation tags (`[doc_X_chunk_Y]`).
2. **Citation Validation**: `CitationValidator` compares AI output citations against retrieved vector chunks, stripping hallucinated document references.
3. **Adaptive Quiz Generation**: Generates structured MCQ and open-ended questions calibrated against user concept mastery levels.
4. **Open-Ended Assessment Grading**: Evaluates student free-text responses against reference answers, providing score breakdowns and constructive feedback.
5. **Next Action Card Generation**: Analyzes weak concepts and mastery trends to recommend optimal next learning activities.
