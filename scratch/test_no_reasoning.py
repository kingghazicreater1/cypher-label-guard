import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
payload = {
    'model': 'liquid/lfm-2.5-2.6b:free',
    'messages': [{'role': 'user', 'content': 'Evaluate: "Luxury Leather Handbag". Respond strictly with JSON: {"category": "Accessories", "confidence": 0.95}'}],
    'temperature': 0.0,
    'max_tokens': 200,
    'reasoning': {'max_tokens': 0}
}
r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload)
print("Status:", r.status_code)
data = r.json()
print("Choice:", json.dumps(data.get("choices", [{}])[0], indent=2))
