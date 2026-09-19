# Study Companion (AI Prof) — Adaptive SaaS Learning & Mastery Platform

**Study Companion (AI Prof)** is an enterprise-grade, multi-tenant AI-powered learning and concept mastery platform. Built with FastAPI, React, PyMuPDF, ChromaDB, and Groq/Gemini LLM engines, Study Companion turns raw study materials (PDFs, notes, documents) into grounded interactive AI tutoring, sequential adaptive assessments, deterministic concept mastery estimates, and actionable learning growth paths.

---

## 🌟 Key Features

- **Structured Sequential Learning Journey**: Progresses learners step-by-step through project study concepts, with a mastery threshold gate ($\ge$ 65%) to advance or initiate targeted remediation.
- **Dynamic Question Pool & Semantic Deduplication**: Pre-generates grounded assessment questions across 6 cognitive aspects and normalizes text fingerprints to block duplicate or near-duplicate questions.
- **Multi-Tenant Workspace & Spaces**: Strict tenant isolation across user Spaces, Projects, Materials, Quizzes, Conversations, and Analytics.
- **RAG PDF Material Processing**: PyMuPDF OCR parsing, semantic chunking, ChromaDB vector indexing, and cosine similarity retrieval.
- **Grounded AI Tutor**: Interactive chat with grounded responses, inline source citations (`[doc_X_chunk_Y]`), and evidence validation gates.
- **Deterministic Concept Mastery**: Algorithmic mastery engine incorporating performance, difficulty, mistakes, recency, and explainability snapshots.
- **Event-Driven Recommendation Engine**: Action cards ranking weak concepts, mastery growth trajectories, and next recommended study actions.
- **Telemetry & AI Observability**: Token tracking, provider fallback metrics, background worker status, and global admin dashboard (`/admin`).

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite, TypeScript, TailwindCSS, Lucide Icons, Recharts
- **Backend**: FastAPI (Python 3.12+), Pydantic V2, SQLAlchemy AsyncIO, Uvicorn
- **Background Worker & Queue**: Celery 5.6+, Redis 8.0+ / `fakeredis`
- **Database & Storage**: PostgreSQL (Supabase), Local ChromaDB Vector Store
- **AI Models**: Groq (`llama-3.3-70b-versatile`), Gemini (`gemini-1.5-flash`), `MockLLMProvider` fallback
- **Event Bus**: Async domain event publisher/subscriber architecture with idempotency deduplication

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- Docker (optional, for Redis)

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev
```

### 4. Background Worker (Optional)
```bash
# Start Redis (in a separate terminal)
docker run -p 6379:6379 redis:alpine

# Start Celery Worker
celery -A workers.celery_app worker --loglevel=INFO
```

---

## 🧪 Testing & Verification

```bash
# Run pytest backend unit and integration tests
pytest tests/test_assessment.py tests/test_mastery.py -v

# Run 3-Connected Learning Loop End-to-End Test
python backend/test_learning_loop_e2e.py
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
