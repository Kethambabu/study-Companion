import fitz
import pytest
from httpx import AsyncClient

from app.modules.knowledge.chunker import SemanticChunker
from app.modules.knowledge.providers import DeterministicEmbeddingProvider, InMemoryVectorStore


def create_sample_pdf_bytes(title: str, text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"{title}\n{text}")
    bytes_out = doc.tobytes()
    doc.close()
    return bytes_out


@pytest.mark.asyncio
async def test_chunking_and_indexing_pipeline(async_client: AsyncClient):
    # 1. Signup, space & project
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "know_u1@example.com", "password": "password123"},
    )
    assert u_resp.status_code == 201
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "Know Space", "slug": "know-space"}, headers=headers)
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post("/api/v1/projects", json={"space_id": sp_id, "name": "Know Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    # 2. Upload material
    pdf_content = (
        "Distributed Systems Consensus Protocols.\n"
        "Raft is a consensus algorithm designed to be easy to understand. "
        "It decomposes consensus into leader election, log replication, and safety. "
        "Paxos is another classic protocol for fault-tolerant state machine replication."
    )
    pdf_bytes = create_sample_pdf_bytes("Distributed Systems Textbook", pdf_content)

    up_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("distributed.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    mat_id = up_res.json()["data"]["id"]

    # 3. Index material into Knowledge Base
    idx_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/knowledge/index/{mat_id}",
        headers=headers,
    )
    assert idx_res.status_code == 200
    assert idx_res.json()["data"]["chunks_indexed"] >= 1

    # 4. List extracted concepts
    conc_res = await async_client.get(
        f"/api/v1/projects/{pj_id}/knowledge/concepts",
        headers=headers,
    )
    assert conc_res.status_code == 200
    concepts = conc_res.json()["data"]
    assert len(concepts) >= 1

    # 5. List vector chunks
    chunk_res = await async_client.get(
        f"/api/v1/projects/{pj_id}/knowledge/chunks",
        headers=headers,
    )
    assert chunk_res.status_code == 200
    assert chunk_res.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_rag_retrieval_and_citations(async_client: AsyncClient):
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "rag_u1@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "RAG Space", "slug": "rag-space"}, headers=headers)
    sp_id = sp.json()["data"]["id"]

    pj = await async_client.post("/api/v1/projects", json={"space_id": sp_id, "name": "RAG Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    pdf_text = (
        "Quantum Mechanics Wave Equations.\n"
        "Schrodinger equation governs the wave function of a quantum-mechanical system. "
        "The wave function amplitude squared represents probability density."
    )
    pdf_bytes = create_sample_pdf_bytes("Quantum Physics Notes", pdf_text)

    up_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/materials",
        files={"file": ("quantum.pdf", pdf_bytes, "application/pdf")},
        headers=headers,
    )
    mat_id = up_res.json()["data"]["id"]

    await async_client.post(f"/api/v1/projects/{pj_id}/knowledge/index/{mat_id}", headers=headers)

    # Search query relevant to Schrodinger equation
    search_res = await async_client.post(
        f"/api/v1/projects/{pj_id}/knowledge/search",
        json={"query": "Schrodinger equation wave function probability density", "top_k": 3},
        headers=headers,
    )
    assert search_res.status_code == 200
    data = search_res.json()["data"]

    assert len(data["citations"]) >= 1
    cit = data["citations"][0]
    assert cit["material_name"] == "quantum.pdf"
    assert cit["page_number"] == 1
    assert "Schrodinger" in cit["excerpt"]
    assert data["diagnostics"]["selected_count"] >= 1


@pytest.mark.asyncio
async def test_project_isolation_in_vector_search(async_client: AsyncClient):
    # User 1 creates Project 1 and indexes Secret Document
    u1_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "iso_v1@example.com", "password": "password123"},
    )
    h1 = {"Authorization": f"Bearer {u1_resp.json()['data']['access_token']}"}

    sp1 = await async_client.post("/api/v1/spaces", json={"name": "S1", "slug": "s1-iso"}, headers=h1)
    pj1 = await async_client.post("/api/v1/projects", json={"space_id": sp1.json()["data"]["id"], "name": "P1"}, headers=h1)
    pj1_id = pj1.json()["data"]["id"]

    doc1_bytes = create_sample_pdf_bytes("Top Secret P1", "Confidential Alpha Code Formula: 99887766.")
    up1 = await async_client.post(f"/api/v1/projects/{pj1_id}/materials", files={"file": ("p1.pdf", doc1_bytes, "application/pdf")}, headers=h1)
    await async_client.post(f"/api/v1/projects/{pj1_id}/knowledge/index/{up1.json()['data']['id']}", headers=h1)

    # User 2 creates Project 2
    u2_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "iso_v2@example.com", "password": "password123"},
    )
    h2 = {"Authorization": f"Bearer {u2_resp.json()['data']['access_token']}"}

    sp2 = await async_client.post("/api/v1/spaces", json={"name": "S2", "slug": "s2-iso"}, headers=h2)
    pj2 = await async_client.post("/api/v1/projects", json={"space_id": sp2.json()["data"]["id"], "name": "P2"}, headers=h2)
    pj2_id = pj2.json()["data"]["id"]

    # User 2 searches Project 2 for Confidential Alpha Code -> Must NOT return User 1's secret
    search_u2 = await async_client.post(
        f"/api/v1/projects/{pj2_id}/knowledge/search",
        json={"query": "Confidential Alpha Code Formula 99887766", "top_k": 5},
        headers=h2,
    )
    assert search_u2.status_code == 200
    data_u2 = search_u2.json()["data"]
    assert len(data_u2["citations"]) == 0
    assert data_u2["diagnostics"]["selected_count"] == 0

    # User 2 attempts to query Project 1's knowledge search endpoint -> 403 Forbidden
    unauth_search = await async_client.post(
        f"/api/v1/projects/{pj1_id}/knowledge/search",
        json={"query": "Alpha Code"},
        headers=h2,
    )
    assert unauth_search.status_code == 403


@pytest.mark.asyncio
async def test_unsupported_or_irrelevant_query_behavior(async_client: AsyncClient):
    u_resp = await async_client.post(
        "/api/v1/auth/signup",
        json={"email": "unsupp_u1@example.com", "password": "password123"},
    )
    token = u_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    sp = await async_client.post("/api/v1/spaces", json={"name": "Unsupp Space", "slug": "unsupp-space"}, headers=headers)
    pj = await async_client.post("/api/v1/projects", json={"space_id": sp.json()["data"]["id"], "name": "Unsupp Project"}, headers=headers)
    pj_id = pj.json()["data"]["id"]

    doc_bytes = create_sample_pdf_bytes("Organic Chemistry", "Alkanes, alkenes, functional groups, and carbon bonds.")
    up = await async_client.post(f"/api/v1/projects/{pj_id}/materials", files={"file": ("chem.pdf", doc_bytes, "application/pdf")}, headers=headers)
    await async_client.post(f"/api/v1/projects/{pj_id}/knowledge/index/{up.json()['data']['id']}", headers=headers)

    # Completely irrelevant query with high threshold cutoff
    res = await async_client.post(
        f"/api/v1/projects/{pj_id}/knowledge/search",
        json={"query": "Zookeeper leader election Paxos raft distributed consensus", "threshold": 0.8, "top_k": 3},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()["data"]
    # Should safely return 0 selected citations when threshold is not met
    assert len(data["citations"]) == 0
    assert data["context"] == ""
