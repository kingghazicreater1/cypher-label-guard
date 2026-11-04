import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
    'model': 'liquid/lfm-2.5-2.6b:free',
    'messages': [{'role': 'user', 'content': 'Evaluate: "Luxury Leather Handbag". Respond strictly with JSON: {"category": "Accessories", "confidence": 0.95}'}],
    'temperature': 0.0,
    'max_tokens': 600,
}, timeout=15.0)

msg = r.json()['choices'][0]['message']
print("CONTENT:", msg.get("content"))
print("REASONING (first 100 chars):", str(msg.get("reasoning"))[:100])
