# Future Product Roadmap & Architectural Improvements

## Overview

This roadmap outlines planned post-MVP enhancements to scale AI Prof into an enterprise learning ecosystem.

---

## 1. Multi-Node Asynchronous Infrastructure
- **Distributed Task Queue**: Migrate in-memory background task processor to Celery / ARQ backed by Redis and RabbitMQ.
- **Distributed Vector Engine**: Upgrade local ChromaDB instance to Qdrant Cloud or Pgvector on Supabase for vector search scaling.

---

## 2. Advanced AI Capabilities
- **Real-Time Audio / Voice Tutor**: Add WebRTC streaming audio tutoring sessions using Gemini Live API or Whisper TTS/STT pipelines.
- **Multi-Modal Document Parsing**: Integrate vision models (e.g., LLaVA or GPT-4o-vision) to index handwritten diagrams, flowcharts, and technical schematics.
- **Web-Search Grounding**: Augment RAG retrieval with real-time web search grounding for fast-evolving fields.

---

## 3. Collaborative Learning Features
- **Shared Team Spaces**: Real-time collaborative study rooms with shared document annotation and live group quizzes via WebSockets.
- **LMS Integrations**: Support LTI (Learning Tools Interoperability) integration with Canvas, Moodle, and Blackboard.
