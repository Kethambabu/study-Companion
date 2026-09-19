import os
import httpx
import asyncio

async def test_groq_models():
    api_key = os.getenv("GROQ_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get("https://api.groq.com/openai/v1/models", headers=headers)
            print(f"Groq Models Status: {resp.status_code}")
            if resp.status_code == 200:
                models = [m["id"] for m in resp.json().get("data", [])]
                print(f"Available Groq Models: {models}")
            else:
                print(f"Error response: {resp.text}")
        except Exception as e:
            print(f"Groq Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq_models())
