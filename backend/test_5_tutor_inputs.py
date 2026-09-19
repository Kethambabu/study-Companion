import asyncio
import io
import json
import httpx
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_pdf_bytes(title: str, text: str) -> bytes:
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

async def test_5_tutor_inputs():
    print("=========================================================================")
    print("TESTING AI TUTOR WITH 5 INPUTS END-TO-END (NON-STREAM + SSE STREAM)")
    print("=========================================================================")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Login
        login_res = await client.post("/auth/login", json={"email": "varshitha@example.com", "password": "password123"})
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Space
        new_space = await client.post("/spaces", json={"name": f"Test Space {uuid.uuid4().hex[:4]}", "slug": f"test-space-{uuid.uuid4().hex[:6]}"}, headers=headers)
        space_id = new_space.json()["data"]["id"]

        # 3. Create Project
        proj_res = await client.post("/projects", json={"space_id": space_id, "name": "5 Inputs ML Test Project"}, headers=headers)
        project_id = proj_res.json()["data"]["id"]

        # 4. Upload PDF Material
        ml_pdf_text = """
Chapter 1: Well-Posed Learning Problems
A computer program is said to learn from experience E with respect to some class of tasks T and performance measure P if its performance at tasks in T as measured by P improves with experience E.
Defining a learning problem therefore requires specifying task T performance measure P and experience E.

Chapter 2: Supervised vs Unsupervised Learning Foundations
Supervised learning is the machine learning task of learning a function that maps an input to an output based on example input-output pairs.
It infers a function from labeled training data consisting of a set of training examples.
In contrast unsupervised learning finds hidden patterns or intrinsic structures in input data without explicit output labels.
        """
        pdf_bytes = create_pdf_bytes("Machine Learning Fundamentals", ml_pdf_text)

        print("\n[SETUP] Uploading Machine Learning Material PDF...")
        up_res = await client.post(
            f"/projects/{project_id}/materials",
            files={"file": ("ml_fundamentals.pdf", pdf_bytes, "application/pdf")},
            headers=headers
        )
        if up_res.status_code != 201:
            print(f"Material upload status {up_res.status_code}: {up_res.text}")
        assert up_res.status_code == 201, f"Expected 201, got {up_res.status_code}: {up_res.text}"
        material_id = up_res.json()["data"]["id"]
        
        idx_res = await client.post(f"/projects/{project_id}/knowledge/index/{material_id}", headers=headers)
        assert idx_res.status_code == 200, f"Indexing failed: {idx_res.text}"
        print(" -> Knowledge Indexing Complete!\n")

        # Create Conversation
        conv_res = await client.post(f"/projects/{project_id}/tutor/conversations", json={"title": "5 Inputs Chat"}, headers=headers)
        assert conv_res.status_code == 201, f"Conversation creation failed: {conv_res.text}"
        conv_id = conv_res.json()["data"]["id"]

        test_inputs = [
            {
                "id": 1,
                "prompt": "What are Well posed learning problems?",
                "expected_status": "grounded",
                "min_citations": 1
            },
            {
                "id": 2,
                "prompt": "What is supervised learning?",
                "expected_status": "grounded",
                "min_citations": 1
            },
            {
                "id": 3,
                "prompt": "Who is the current Prime Minister of India?",
                "expected_status": "unsupported_question",
                "min_citations": 0
            },
            {
                "id": 4,
                "prompt": "Explain the difference between supervised and unsupervised learning",
                "expected_status": "grounded",
                "min_citations": 1
            },
            {
                "id": 5,
                "prompt": "How many legs does a dog have?",
                "expected_status": "unsupported_question",
                "min_citations": 0
            }
        ]

        for item in test_inputs:
            print(f"--- INPUT #{item['id']}: '{item['prompt']}' ---")
            
            # Test POST non-stream endpoint
            res = await client.post(
                f"/projects/{project_id}/tutor/conversations/{conv_id}/messages",
                json={"content": item["prompt"]},
                headers=headers
            )
            assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
            data = res.json()["data"]
            print(f"  [POST] Status: {data['confidence_status']} | Citations: {len(data['citations'])}")
            clean_preview = data['answer'][:100].encode('ascii', 'replace').decode('ascii')
            print(f"  [POST] Answer: {clean_preview}...")
            assert data["confidence_status"] == item["expected_status"], f"Expected {item['expected_status']}, got {data['confidence_status']}"
            assert len(data["citations"]) >= item["min_citations"]

            # Test SSE Stream endpoint
            stream_res = await client.post(
                f"/projects/{project_id}/tutor/conversations/{conv_id}/stream",
                json={"content": item["prompt"]},
                headers=headers
            )
            assert stream_res.status_code == 200, f"Expected 200 on stream, got {stream_res.status_code}: {stream_res.text}"
            stream_text = stream_text_chunks = stream_res.text
            assert "data: {" in stream_text, "Expected SSE data frame in stream response"
            print(f"  [SSE] Stream Response verified successfully!")
            print(f"  [PASSED] INPUT #{item['id']} PASSED!\n")

        print("=========================================================================")
        print("ALL 5 TUTOR INPUTS PASSED END-TO-END WITH ZERO ERRORS!")
        print("=========================================================================")

if __name__ == "__main__":
    asyncio.run(test_5_tutor_inputs())
