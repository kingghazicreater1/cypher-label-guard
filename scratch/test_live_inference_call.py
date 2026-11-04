import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
prompt = 'Classify this item into Category and Risk: "Luxury Italian Leather Handbag in Navy Blue". Respond ONLY with valid JSON: {"category": "...", "risk": "..."}'
payload = {
    'model': 'nvidia/nemotron-3.5-lightning:free',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0.0,
}

r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json=payload, timeout=12.0)
print('STATUS CODE:', r.status_code)
if r.status_code == 200:
    content = r.json()['choices'][0]['message']['content']
    print('REAL LIVE MODEL OUTPUT:\n', content)
else:
    print('ERROR:', r.text)
