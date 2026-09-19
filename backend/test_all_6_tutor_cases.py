import asyncio
import io
import json
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_pdf_bytes(title: str, text: str) -> bytes:
    # A valid, simple PDF file format generated in pure Python without dependencies
    clean_title = title.replace("(", "\\(").replace(")", "\\)")
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    stream_ops = [f"BT /F1 14 Tf 50 750 Td ({clean_title}) Tj ET"]
    y = 710
    for line in lines:
        clean_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_ops.append(f"BT /F1 10 Tf 50 {y} Td ({clean_line}) Tj ET")
        y -= 15
        
    stream_content = "\n".join(stream_ops)
    stream_len = len(stream_content)

    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length {stream_len} >>
stream
{stream_content}
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000244 00000 n 
0000000319 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
410
%%EOF"""
    return pdf.encode("utf-8")

async def run_e2e_tests():
    print("=========================================================================")
    print("STARTING E2E AUDIT OF ALL 6 TUTOR & EVIDENCE GATE TEST CASES")
    print("=========================================================================")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        # 1. Login
        login_res = await client.post("/auth/login", json={"email": "varshitha@example.com", "password": "password123"})
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get space
        space_res = await client.get("/spaces", headers=headers)
        space_data = space_res.json()["data"]
        items = space_data.get("items", [])
        if items:
            space_id = items[0]["id"]
        else:
            new_space = await client.post("/spaces", json={"name": "Test Space", "slug": f"test-space-{uuid.uuid4().hex[:6]}"}, headers=headers)
            space_id = new_space.json()["data"]["id"]

        # 3. Create Project A (Machine Learning Study Companion)
        proj_a_res = await client.post("/projects", json={"space_id": space_id, "name": "Machine Learning Companion"}, headers=headers)
        ml_project_id = proj_a_res.json()["data"]["id"]

        # 4. Upload ML Study PDF
        ml_pdf_text = """
Chapter 1: Well-Posed Learning Problems
A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P if its performance at tasks in T as measured by P improves with experience E.
Defining a learning problem therefore requires specifying task T performance measure P and experience E.

Chapter 2: Supervised Learning Foundations
Supervised learning is the machine learning task of learning a function that maps an input to an output based on example input-output pairs.
It infers a function from labeled training data consisting of a set of training examples.
In supervised learning each example is a pair consisting of an input object and a desired output value.
        """
        ml_pdf_bytes = create_pdf_bytes("Machine Learning Textbook", ml_pdf_text)

        print("\n[SETUP] Uploading Machine Learning Study Companion PDF...")
        up_res = await client.post(
            f"/projects/{ml_project_id}/materials",
            files={"file": ("ml_course.pdf", ml_pdf_bytes, "application/pdf")},
            headers=headers
        )
        ml_material_id = up_res.json()["data"]["id"]

        # Index knowledge
        idx_res = await client.post(f"/projects/{ml_project_id}/knowledge/index/{ml_material_id}", headers=headers)
        print(" -> Machine Learning PDF Uploaded & Knowledge Chunks Index Complete!\n")

        # Create Tutor Conversation for ML Project
        conv_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations",
            json={"title": "ML Test Chat"},
            headers=headers
        )
        ml_conv_id = conv_res.json()["data"]["id"]

        # ---------------------------------------------------------------------
        # TEST 1: "What are Well posed learning problems?"
        # ---------------------------------------------------------------------
        print("--- TEST 1: 'What are Well posed learning problems?' ---")
        t1_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "What are Well posed learning problems?"},
            headers=headers
        )
        assert t1_res.status_code == 200, f"Expected 200 OK, got {t1_res.status_code}: {t1_res.text}"
        d1 = t1_res.json()["data"]
        print(f"Mode/Status: {d1['confidence_status']}")
        print(f"Citations: {len(d1['citations'])} citation(s)")
        clean_ans1 = d1['answer'][:120].encode('ascii', 'replace').decode('ascii')
        print(f"Answer Preview: {clean_ans1}...")
        assert d1["confidence_status"] == "grounded", f"Expected grounded, got {d1['confidence_status']}"
        assert len(d1["citations"]) >= 1, "Expected at least 1 citation"
        print("[SUCCESS] TEST 1 PASSED: Retested concept from ML PDF with grounded answer & citation!\n")

        # ---------------------------------------------------------------------
        # TEST 2: "What is supervised learning?"
        # ---------------------------------------------------------------------
        print("--- TEST 2: 'What is supervised learning?' ---")
        t2_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "What is supervised learning?"},
            headers=headers
        )
        assert t2_res.status_code == 200, f"Expected 200 OK, got {t2_res.status_code}: {t2_res.text}"
        d2 = t2_res.json()["data"]
        print(f"Mode/Status: {d2['confidence_status']}")
        print(f"Citations: {len(d2['citations'])} citation(s)")
        clean_ans2 = d2['answer'][:120].encode('ascii', 'replace').decode('ascii')
        print(f"Answer Preview: {clean_ans2}...")
        assert d2["confidence_status"] == "grounded", f"Expected grounded, got {d2['confidence_status']}"
        assert len(d2["citations"]) >= 1, "Expected at least 1 citation"
        print("[SUCCESS] TEST 2 PASSED: Grounded answer & citations for ML concepts!\n")

        # ---------------------------------------------------------------------
        # TEST 3: "Who is the current Prime Minister of India?"
        # ---------------------------------------------------------------------
        print("--- TEST 3: 'Who is the current Prime Minister of India?' ---")
        t3_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "Who is the current Prime Minister of India?"},
            headers=headers
        )
        assert t3_res.status_code == 200, f"Expected 200 OK, got {t3_res.status_code}: {t3_res.text}"
        d3 = t3_res.json()["data"]
        print(f"Mode/Status: {d3['confidence_status']}")
        print(f"Citations: {len(d3['citations'])} citation(s)")
        clean_ans3 = d3['answer'][:120].encode('ascii', 'replace').decode('ascii')
        print(f"Answer Preview: {clean_ans3}...")
        assert d3["confidence_status"] == "unsupported_question", f"Expected unsupported_question, got {d3['confidence_status']}"
        assert len(d3["citations"]) == 0, "Expected 0 citations"
        print("[SUCCESS] TEST 3 PASSED: Prime Minister question blocked by Evidence Gate!\n")

        # ---------------------------------------------------------------------
        # TEST 4: "How many legs does a dog have?"
        # ---------------------------------------------------------------------
        print("--- TEST 4: 'How many legs does a dog have?' ---")
        t4_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "How many legs does a dog have?"},
            headers=headers
        )
        assert t4_res.status_code == 200, f"Expected 200 OK, got {t4_res.status_code}: {t4_res.text}"
        d4 = t4_res.json()["data"]
        print(f"Mode/Status: {d4['confidence_status']}")
        print(f"Citations: {len(d4['citations'])} citation(s)")
        clean_ans4 = d4['answer'][:120].encode('ascii', 'replace').decode('ascii')
        print(f"Answer Preview: {clean_ans4}...")
        assert d4["confidence_status"] == "unsupported_question", f"Expected unsupported_question, got {d4['confidence_status']}"
        assert len(d4["citations"]) == 0, "Expected 0 citations"
        print("[SUCCESS] TEST 4 PASSED: General trivia question blocked by Evidence Gate!\n")

        # ---------------------------------------------------------------------
        # TEST 5: Cross-Project Knowledge Isolation
        # ---------------------------------------------------------------------
        print("--- TEST 5: Cross-Project Knowledge Isolation ---")
        proj_b_res = await client.post("/projects", json={"space_id": space_id, "name": "Biology Project"}, headers=headers)
        bio_project_id = proj_b_res.json()["data"]["id"]

        bio_pdf_text = "Cellular Biology: Mitochondria is the powerhouse of the cell."
        bio_pdf_bytes = create_pdf_bytes("Biology Notes", bio_pdf_text)
        bio_up = await client.post(
            f"/projects/{bio_project_id}/materials",
            files={"file": ("biology_notes.pdf", bio_pdf_bytes, "application/pdf")},
            headers=headers
        )
        bio_mat_id = bio_up.json()["data"]["id"]
        await client.post(f"/projects/{bio_project_id}/knowledge/index/{bio_mat_id}", headers=headers)

        t5_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "What is the powerhouse of the cell?"},
            headers=headers
        )
        assert t5_res.status_code == 200, f"Expected 200 OK, got {t5_res.status_code}: {t5_res.text}"
        d5 = t5_res.json()["data"]
        print(f"Mode/Status: {d5['confidence_status']}")
        print(f"Citations: {len(d5['citations'])} citation(s)")
        assert d5["confidence_status"] == "unsupported_question"
        assert len(d5["citations"]) == 0
        print("[SUCCESS] TEST 5 PASSED: ML Project strictly isolated; did NOT leak Biology material!\n")

        # ---------------------------------------------------------------------
        # TEST 6: Partially Related / Unsupported Question
        # ---------------------------------------------------------------------
        print("--- TEST 6: Partially Related / Unsupported Question ---")
        t6_res = await client.post(
            f"/projects/{ml_project_id}/tutor/conversations/{ml_conv_id}/messages",
            json={"content": "Can you provide a detailed proof of Quantum Entanglement in String Theory?"},
            headers=headers
        )
        assert t6_res.status_code == 200, f"Expected 200 OK, got {t6_res.status_code}: {t6_res.text}"
        d6 = t6_res.json()["data"]
        print(f"Mode/Status: {d6['confidence_status']}")
        print(f"Citations: {len(d6['citations'])} citation(s)")
        clean_ans6 = d6['answer'][:120].encode('ascii', 'replace').decode('ascii')
        print(f"Answer Preview: {clean_ans6}...")
        assert d6["confidence_status"] == "unsupported_question"
        assert len(d6["citations"]) == 0
        print("[SUCCESS] TEST 6 PASSED: Insufficient evidence returned without hallucination!\n")

        print("=========================================================================")
        print("ALL 6 TEST CASES PASSED WITH 100% SUCCESS!")
        print("=========================================================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
