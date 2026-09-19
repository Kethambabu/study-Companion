import asyncio
import logging
import re
import time
from typing import AsyncGenerator

from app.modules.tutor.abstractions import LLMCompletionResult, LLMProvider

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Deterministic grounded LLM Provider for testable AI Tutor completions and prompt injection defenses."""

    def __init__(self, model_name: str = "mock-tutor-v1"):
        self.model_name = model_name

    def generate_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        start_time = time.time()

        system_msg = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user_msg = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        user_lower = user_msg.lower().strip()

        mat_matches = re.findall(r"<untrusted_study_material>(.*?)</untrusted_study_material>", system_msg, re.DOTALL)
        study_material = mat_matches[-1].strip() if mat_matches else ""

        if "IGNORE ALL PREVIOUS INSTRUCTIONS" in study_material.upper() or "DROP TABLE" in study_material.upper():
            study_material = re.sub(r"(?i)ignore all previous instructions.*", "", study_material)

        user_words = set(re.findall(r"\w+", user_lower)) - {"what", "is", "the", "a", "an", "for", "in", "of", "and", "or", "to"}
        mat_words = set(re.findall(r"\w+", study_material.lower()))
        overlap_count = len(user_words.intersection(mat_words))

        has_material = bool(study_material and study_material != "[NO STUDY MATERIAL RETRIEVED]" and "[NO STUDY MATERIAL RETRIEVED]" not in study_material and overlap_count >= 1)
        confidence = "grounded" if has_material else "insufficient_evidence"
        conf_score = 0.95 if has_material else 0.30
        ev_count = 1 if has_material else 0
        citations = []

        if "vector space" in user_lower:
            content = (
                "A **Vector Space** (or linear space) is a fundamental mathematical structure in linear algebra and machine learning.\n\n"
                "### Core Properties:\n"
                "1. **Definition**: A collection of objects called *vectors* that can be added together and multiplied by numbers (*scalars*).\n"
                "2. **Vector Space Axioms**: Closed under vector addition and scalar multiplication, with an additive identity (zero vector) and associative/commutative properties.\n"
                "3. **Role in AI & Machine Learning**:\n"
                "   • **Embeddings**: Text, images, and audio are projected into high-dimensional vector spaces (e.g., 768 or 1536 dimensions).\n"
                "   • **Similarity Search**: Distances between vectors (such as Cosine Similarity or Euclidean Distance) capture semantic relationships between concepts."
            )
            confidence = "grounded"
            conf_score = 0.98
        elif "well posed learning" in user_lower or "well-posed" in user_lower or "tom mitchell" in user_lower:
            content = (
                "A **Well-Posed Learning Problem** is the foundational definition of Machine Learning formulated by Tom Mitchell:\n\n"
                "> *\"A computer program is said to learn from experience **E** with respect to some class of tasks **T** and performance measure **P**, if its performance at tasks in **T**, as measured by **P**, improves with experience **E**.\"*\n\n"
                "### Key Elements:\n"
                "• **Task (T)**: The objective to perform (e.g., handwriting recognition, spam classification).\n"
                "• **Performance Measure (P)**: The quantitative evaluation score (e.g., accuracy percentage).\n"
                "• **Experience (E)**: The training dataset or interaction history."
            )
            confidence = "grounded"
            conf_score = 0.98
        elif "rag" in user_lower or "retrieval" in user_lower:
            content = (
                "**Retrieval-Augmented Generation (RAG)** is an AI architecture that enhances LLM responses by grounding them in verified external knowledge.\n\n"
                "1. **Indexing**: Course PDFs are chunked and converted into vector embeddings.\n"
                "2. **Retrieval**: Relevant context chunks are retrieved matching the user's query.\n"
                "3. **Generation**: The LLM synthesizes an accurate answer backed by document citations."
            )
            confidence = "grounded"
            conf_score = 0.98
        elif has_material:
            content = (
                f"Based on your project materials:\n\n"
                f"{study_material[:300]}\n\n"
                f"Regarding **\"{user_msg}\"**: This concept is addressed in your course notes. Let me know if you would like a code example, simple breakdown, or practice quiz!"
            )
            citations = [
                {
                    "citation_id": "[1]",
                    "document_title": "Project Study Notes",
                    "file_name": "Project_Materials.pdf",
                    "page_number": 1,
                    "excerpt": study_material[:150],
                }
            ]
        else:
            content = (
                f"Here is an explanation regarding **\"{user_msg}\"**:\n\n"
                f"• **Overview**: In computer science and artificial intelligence, **{user_msg}** represents a core domain concept.\n"
                f"• **Key Principle**: Understanding the mathematical foundations, algorithms, and applications of this topic enables effective problem solving.\n\n"
                f"> ⚠️ *Note: The uploaded project materials do not contain direct evidence for this query. Upload relevant course PDFs to receive grounded answers with document citations!*"
            )

        followups = [
            "Explain this in simpler terms",
            "Give me a practical example",
            "Test me on this concept",
        ]

        latency = round((time.time() - start_time) * 1000 + 40.0, 2)

        return LLMCompletionResult(
            content=content,
            citations=citations,
            tool_calls=None,
            confidence_status=confidence,
            confidence_score=conf_score,
            evidence_count=ev_count,
            suggested_followups=followups,
            model=self.model_name,
            provider="mock-llm",
            tokens_used=len(content.split()) + 30,
            latency_ms=latency,
        )

    async def generate_completion_async(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        return self.generate_completion(messages, tools)

    async def generate_stream_async(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        """PRD 131: Async token streaming generator for Streaming Tutor."""
        result = self.generate_completion(messages)
        words = result.content.split(" ")
        for word in words:
            yield word + " "
            await asyncio.sleep(0.02)


class GroqLLMProvider(LLMProvider):
    """High-performance Groq Cloud LLM Provider with Timeout & Failover (PRD 118, 119, 133)."""

    def __init__(self, api_key: str | None = None, model: str = "groq/compound-mini"):
        self.api_key = api_key
        self.model = model

    def _get_model_candidates(self) -> list[str]:
        candidates = []
        if self.model:
            candidates.append(self.model)
        for m in ("groq/compound-mini", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"):
            if m not in candidates:
                candidates.append(m)
        return candidates

    def generate_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        if not self.api_key:
            return MockLLMProvider(model_name=f"groq-mock-{self.model}").generate_completion(messages, tools)

        start_time = time.time()
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for model_to_use in self._get_model_candidates():
            payload = {
                "model": model_to_use,
                "messages": messages,
                "temperature": 0.2,
            }
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code != 200:
                        logger.warning("Groq model '%s' returned status %s, trying next candidate...", model_to_use, resp.status_code)
                        continue
                    data = resp.json()

                    content = data["choices"][0]["message"]["content"]
                    latency = round((time.time() - start_time) * 1000, 2)
                    tokens = data.get("usage", {}).get("total_tokens", len(content.split()) + 30)

                    return LLMCompletionResult(
                        content=content,
                        citations=[],
                        tool_calls=None,
                        confidence_status="grounded",
                        suggested_followups=["Explain this further", "Give an example", "Test me on this"],
                        model=model_to_use,
                        provider="groq",
                        tokens_used=tokens,
                        latency_ms=latency,
                    )
            except Exception as exc:
                logger.warning("Groq model '%s' call failed (%s).", model_to_use, str(exc))

        logger.warning("All Groq candidates failed. Failover to Mock LLM...")
        return MockLLMProvider(model_name=self.model).generate_completion(messages, tools)

    async def generate_completion_async(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        if not self.api_key:
            return await MockLLMProvider(model_name=f"groq-mock-{self.model}").generate_completion_async(messages, tools)

        start_time = time.time()
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for model_to_use in self._get_model_candidates():
            payload = {
                "model": model_to_use,
                "messages": messages,
                "temperature": 0.2,
            }
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code != 200:
                        logger.warning("Groq model '%s' returned status %s, trying next candidate...", model_to_use, resp.status_code)
                        continue
                    data = resp.json()

                    content = data["choices"][0]["message"]["content"]
                    latency = round((time.time() - start_time) * 1000, 2)
                    tokens = data.get("usage", {}).get("total_tokens", len(content.split()) + 30)

                    return LLMCompletionResult(
                        content=content,
                        citations=[],
                        tool_calls=None,
                        confidence_status="grounded",
                        suggested_followups=["Explain this further", "Give an example", "Test me on this"],
                        model=model_to_use,
                        provider="groq",
                        tokens_used=tokens,
                        latency_ms=latency,
                    )
            except Exception as exc:
                logger.warning("Groq async model '%s' call failed (%s).", model_to_use, str(exc))

        logger.warning("All Groq async candidates failed. Failover to Mock LLM...")
        mock = MockLLMProvider(model_name=self.model)
        return await mock.generate_completion_async(messages, tools)

    async def generate_stream_async(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        """PRD 131: Streaming Tutor token generator."""
        res = await self.generate_completion_async(messages)
        words = res.content.split(" ")
        for w in words:
            yield w + " "
            await asyncio.sleep(0.01)


class GeminiLLMProvider(LLMProvider):
    """Google Gemini LLM Provider (Gemini 1.5 Flash, Gemini Pro) with Timeout & Failover (PRD 118, 119, 133)."""

    def __init__(self, api_key: str | None = None, model: str = "models/gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def generate_completion(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        if not self.api_key or not self.api_key.startswith("AIza"):
            return MockLLMProvider(model_name=f"gemini-mock-{self.model}").generate_completion(messages, tools)

        start_time = time.time()
        import httpx

        clean_model = self.model.removeprefix("models/")
        model_candidates = [clean_model]
        for m in ("gemini-2.0-flash", "gemini-1.5-flash"):
            if m not in model_candidates:
                model_candidates.append(m)

        gemini_contents = []
        for msg in messages:
            role = "user" if msg.get("role") in ("user", "system") else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })

        payload = {"contents": gemini_contents}

        for m_name in model_candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
            try:
                with httpx.Client(timeout=3.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code in (404, 400, 401, 403):
                        logger.warning("Gemini model '%s' returned HTTP %s, stopping Gemini candidates...", m_name, resp.status_code)
                        break
                    resp.raise_for_status()
                    data = resp.json()

                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    parts = candidates[0].get("content", {}).get("parts", [])
                    content = "".join([p.get("text", "") for p in parts]) or "No response content"

                    latency = round((time.time() - start_time) * 1000, 2)
                    tokens = len(content.split()) + 40

                    return LLMCompletionResult(
                        content=content,
                        citations=[],
                        tool_calls=None,
                        confidence_status="grounded",
                        suggested_followups=["Explain this further", "Give an example", "Test me on this"],
                        model=m_name,
                        provider="gemini",
                        tokens_used=tokens,
                        latency_ms=latency,
                    )
            except Exception as exc:
                logger.warning("Gemini model '%s' attempt failed (%s).", m_name, str(exc))

        logger.warning("Gemini candidates failed/invalid. Failover to Groq or Mock LLM...")
        return MockLLMProvider(model_name=self.model).generate_completion(messages, tools)

    async def generate_completion_async(
        self, messages: list[dict], tools: list[dict] | None = None
    ) -> LLMCompletionResult:
        if not self.api_key or not self.api_key.startswith("AIza"):
            from app.core.config import settings
            if settings.GROQ_API_KEY:
                groq_p = GroqLLMProvider(api_key=settings.GROQ_API_KEY, model="groq/compound-mini")
                return await groq_p.generate_completion_async(messages, tools)
            return await MockLLMProvider(model_name=f"gemini-mock-{self.model}").generate_completion_async(messages, tools)

        start_time = time.time()
        import httpx

        clean_model = self.model.removeprefix("models/")
        model_candidates = [clean_model]
        for m in ("gemini-2.0-flash", "gemini-1.5-flash"):
            if m not in model_candidates:
                model_candidates.append(m)

        gemini_contents = []
        for msg in messages:
            role = "user" if msg.get("role") in ("user", "system") else "model"
            gemini_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })

        payload = {"contents": gemini_contents}

        for m_name in model_candidates:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (404, 400, 401, 403):
                        logger.warning("Gemini model '%s' returned HTTP %s, stopping Gemini candidates...", m_name, resp.status_code)
                        break
                    resp.raise_for_status()
                    data = resp.json()

                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    parts = candidates[0].get("content", {}).get("parts", [])
                    content = "".join([p.get("text", "") for p in parts]) or "No response content"

                    latency = round((time.time() - start_time) * 1000, 2)
                    tokens = len(content.split()) + 40

                    return LLMCompletionResult(
                        content=content,
                        citations=[],
                        tool_calls=None,
                        confidence_status="grounded",
                        suggested_followups=["Explain this further", "Give an example", "Test me on this"],
                        model=m_name,
                        provider="gemini",
                        tokens_used=tokens,
                        latency_ms=latency,
                    )
            except Exception as exc:
                logger.warning("Gemini async model '%s' attempt failed (%s).", m_name, str(exc))

        from app.core.config import settings
        if settings.GROQ_API_KEY:
            groq_p = GroqLLMProvider(api_key=settings.GROQ_API_KEY, model="groq/compound-mini")
            return await groq_p.generate_completion_async(messages, tools)

        mock = MockLLMProvider(model_name=self.model)
        return await mock.generate_completion_async(messages, tools)

    async def generate_stream_async(
        self, messages: list[dict]
    ) -> AsyncGenerator[str, None]:
        """PRD 131: Streaming Tutor token generator."""
        res = await self.generate_completion_async(messages)
        words = res.content.split(" ")
        for w in words:
            yield w + " "
            await asyncio.sleep(0.01)


def get_llm_provider(
    provider_name: str | None = None,
    groq_api_key: str | None = None,
    gemini_api_key: str | None = None,
) -> LLMProvider:
    """PRD 119 & 133: Resilient Multi-Provider router & provider abstraction.

    Routing strategy: Primary provider -> Secondary provider -> Mock LLM.
    """
    from app.core.config import settings

    selected_provider = (provider_name or settings.DEFAULT_AI_PROVIDER).lower()
    g_key = groq_api_key or settings.GROQ_API_KEY
    gem_key = gemini_api_key or settings.GEMINI_API_KEY

    if selected_provider == "gemini" and gem_key and gem_key.startswith("AIza"):
        return GeminiLLMProvider(api_key=gem_key, model="models/gemini-1.5-flash")
    elif g_key:
        return GroqLLMProvider(api_key=g_key, model="groq/compound-mini")
    elif gem_key and gem_key.startswith("AIza"):
        return GeminiLLMProvider(api_key=gem_key, model="models/gemini-1.5-flash")
    else:
        return MockLLMProvider()

