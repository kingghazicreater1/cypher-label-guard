import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")

for p in [
    {"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}], "max_tokens": 500},
    {"model": "openai/gpt-oss-20b", "messages": [{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}], "reasoning_format": "hidden", "max_tokens": 1000},
    {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Respond with JSON: {\"status\": \"ok\"}"}], "reasoning_format": "hidden", "max_tokens": 1500},
]:
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=p)
    data = r.json()
    choice = data.get("choices", [{}])[0].get("message", {})
    print("Payload keys:", list(p.keys()), "Status:", r.status_code)
    print("Content:", choice.get("content"))
    print("Reasoning len:", len(choice.get("reasoning") or ""))
