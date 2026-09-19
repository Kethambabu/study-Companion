import os
import httpx
import asyncio

async def test_groq():
    api_key = os.getenv("GROQ_API_KEY", "")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    for model in ["groq/compound-mini", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "What is vector indexing?"}],
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                print(f"Model {model} -> Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"Response: {resp.json()['choices'][0]['message']['content'][:200]}\n")
            except Exception as e:
                print(f"Model {model} Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())
