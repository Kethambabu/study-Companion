import sys
import asyncio
import httpx
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"

def p(msg):
    print(msg, flush=True)

async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        p("--- 1. Login as Student (varshitha@example.com) ---")
        login_res = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "varshitha@example.com", "password": "password123"}
        )
        p(f"Login Status: {login_res.status_code}")
        if login_res.status_code != 200:
            p(f"Login failed: {login_res.text}")
            return
        
        token = login_res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        p("Logged in successfully!")

        p("\n--- 2. Get User Spaces ---")
        spaces_res = await client.get(f"{BASE_URL}/spaces", headers=headers)
        p(f"Spaces Status: {spaces_res.status_code}")
        spaces_data = spaces_res.json()["data"]
        spaces_items = spaces_data if isinstance(spaces_data, list) else spaces_data.get("items", spaces_data)
        p(f"Spaces Count: {len(spaces_items)}")
        if not spaces_items:
            p("No spaces found!")
            return
        space_id = spaces_items[0]["id"]
        p(f"Using Space ID: {space_id}")

        p("\n--- 3. Get User Projects ---")
        projects_res = await client.get(f"{BASE_URL}/projects?space_id={space_id}", headers=headers)
        p(f"Projects Status: {projects_res.status_code}")
        projects_data = projects_res.json()["data"]
        items = projects_data.get("items", []) if isinstance(projects_data, dict) else projects_data
        p(f"Projects Count: {len(items)}")
        if not items:
            p("No projects found!")
            return
        project_id = items[0]["id"]
        p(f"Using Project ID: {project_id}")

        p("\n--- 4. List Tutor Conversations ---")
        convs_res = await client.get(f"{BASE_URL}/projects/{project_id}/tutor/conversations", headers=headers)
        p(f"List Conversations Status: {convs_res.status_code}")
        p(f"Conversations: {convs_res.text}")

        p("\n--- 5. Create Tutor Conversation ---")
        create_conv_res = await client.post(
            f"{BASE_URL}/projects/{project_id}/tutor/conversations",
            headers=headers,
            json={"title": "Test AI Tutor Session"}
        )
        p(f"Create Conversation Status: {create_conv_res.status_code}")
        p(f"Create Conv Response: {create_conv_res.text}")
        if create_conv_res.status_code != 201:
            return
        conv_id = create_conv_res.json()["data"]["id"]

        p("\n--- 6. Get Learning Context ---")
        ctx_res = await client.get(f"{BASE_URL}/projects/{project_id}/tutor/learning-context", headers=headers)
        p(f"Learning Context Status: {ctx_res.status_code}")
        p(f"Learning Context Response: {ctx_res.text}")

        p("\n--- 7. Send Non-Streaming Message ---")
        msg_res = await client.post(
            f"{BASE_URL}/projects/{project_id}/tutor/conversations/{conv_id}/messages",
            headers=headers,
            json={"content": "What is vector indexing?", "mode": "default"}
        )
        p(f"Send Message Status: {msg_res.status_code}")
        p(f"Send Message Response: {msg_res.text}")

        p("\n--- 8. Send Streaming Message (SSE) ---")
        async with client.stream(
            "POST",
            f"{BASE_URL}/projects/{project_id}/tutor/conversations/{conv_id}/stream",
            headers=headers,
            json={"content": "Can you give me an example of vector search?", "mode": "give_example"}
        ) as response:
            p(f"Stream Status: {response.status_code}")
            async for line in response.aiter_lines():
                if line:
                    p(f"SSE Line: {line}")

        p("\n--- 9. Get Messages History ---")
        hist_res = await client.get(
            f"{BASE_URL}/projects/{project_id}/tutor/conversations/{conv_id}/messages",
            headers=headers
        )
        p(f"History Status: {hist_res.status_code}")
        p(f"History Response: {hist_res.text}")

if __name__ == "__main__":
    asyncio.run(main())
