import asyncio
import httpx
import fitz

def create_pdf_bytes(title: str, content: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"{title}\n\n{content}")
    res = doc.tobytes()
    doc.close()
    return res

async def test_evidence_gate():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=30.0) as client:
        # 1. Login as student
        login_res = await client.post("/auth/login", json={"email": "varshitha@example.com", "password": "password123"})
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get or create space & project
        spaces_res = await client.get("/spaces", headers=headers)
        sp_data = spaces_res.json()["data"]
        spaces_list = sp_data.get("items", sp_data) if isinstance(sp_data, dict) else sp_data
        
        if not spaces_list:
            sp = await client.post("/spaces", json={"name": "Gate Space", "slug": "gate-space"}, headers=headers)
            space_id = sp.json()["data"]["id"]
        else:
            space_id = spaces_list[0]["id"]

        projects_res = await client.get(f"/projects?space_id={space_id}", headers=headers)
        pj_data = projects_res.json()["data"]
        projects_list = pj_data.get("items", pj_data) if isinstance(pj_data, dict) else pj_data

        if not projects_list:
            pj = await client.post("/projects", json={"space_id": space_id, "name": "Gate ML Project"}, headers=headers)
            project_id = pj.json()["data"]["id"]
        else:
            project_id = projects_list[0]["id"]

        # 3. Create conversation
        conv_res = await client.post(f"/projects/{project_id}/tutor/conversations", json={"title": "Strict Evidence Gate Test"}, headers=headers)
        conv_id = conv_res.json()["data"]["id"]

        # 4. Test Unsupported Query (General Knowledge)
        print("\n--- Testing Unsupported General Knowledge Question ---")
        q1_res = await client.post(
            f"/projects/{project_id}/tutor/conversations/{conv_id}/messages",
            json={"content": "who is the current prime minister of india"},
            headers=headers
        )
        data1 = q1_res.json()["data"]
        print("Confidence Status:", data1["confidence_status"])
        print("Answer Text:", data1["answer"])
        print("Citations Count:", len(data1["citations"]))
        assert data1["confidence_status"] == "unsupported_question", f"Expected unsupported_question, got {data1['confidence_status']}"
        assert "couldn't find sufficient information" in data1["answer"].lower(), "Expected unsupported message"
        assert len(data1["citations"]) == 0, "Citations should be empty"
        print("SUCCESS: Unsupported question correctly rejected by Evidence Gate!")

        # 5. Upload ML document & index
        print("\n--- Uploading & Indexing Machine Learning Document ---")
        pdf_bytes = create_pdf_bytes("Machine Learning Vector Search", "Vector search transforms text into dense high-dimensional vectors and retrieves top-k nearest neighbors using cosine similarity.")
        up_res = await client.post(
            f"/projects/{project_id}/materials",
            files={"file": ("ml_vector_search.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        mat_id = up_res.json()["data"]["id"]
        await client.post(f"/projects/{project_id}/knowledge/index/{mat_id}", headers=headers)

        # 6. Test Supported ML Query
        print("\n--- Testing Supported ML Question ---")
        q2_res = await client.post(
            f"/projects/{project_id}/tutor/conversations/{conv_id}/messages",
            json={"content": "How does vector search retrieve nearest neighbors?"},
            headers=headers
        )
        data2 = q2_res.json()["data"]
        print("Confidence Status:", data2["confidence_status"])
        clean_ans = data2["answer"].replace("‑", "-").replace("—", "-")
        print("Answer Excerpt:", clean_ans[:120])
        print("Citations Count:", len(data2["citations"]))
        assert data2["confidence_status"] == "grounded", f"Expected grounded, got {data2['confidence_status']}"
        assert len(data2["citations"]) >= 1, "Expected at least 1 citation"
        print("SUCCESS: Supported ML question answered with grounded evidence!")

if __name__ == "__main__":
    asyncio.run(test_evidence_gate())
