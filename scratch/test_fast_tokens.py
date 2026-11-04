import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import time

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
payload = {
    'model': 'nvidia/nemotron-3.5-lightning:free',
    'messages': [
        {'role': 'user', 'content': 'Evaluate: "Navy Blue Luxury Handbag". Output valid JSON ONLY: {"category": "Handbag", "color": "Navy Blue"}'}
    ],
    'temperature': 0.0,
    'max_tokens': 150
}

start = time.time()
r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload, timeout=20.0)
elapsed = round((time.time() - start) * 1000.0, 1)

print(f"Status: {r.status_code} in {elapsed}ms")
if r.status_code == 200:
    print("Content:", r.json()['choices'][0]['message']['content'])
else:
    print("Error:", r.text)
