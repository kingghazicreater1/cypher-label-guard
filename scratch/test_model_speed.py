import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import time

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
for model in ['liquid/lfm-2.5-2.6b:free', 'dots-studio/dots-3-note-preview:free', 'google/gemma-4-26b-a4b-it:free']:
    t0 = time.time()
    try:
        r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
            'model': model,
            'messages': [{'role': 'user', 'content': 'Evaluate: "Luxury Leather Handbag". Respond with JSON: {"category": "Accessories", "confidence": 0.95}'}],
            'temperature': 0.0,
            'max_tokens': 100,
        }, timeout=8.0)
        dt = round(time.time() - t0, 2)
        print(f"Model: {model} -> Status: {r.status_code} in {dt}s")
        if r.status_code == 200:
            print("  Response:", r.json()['choices'][0]['message']['content'])
    except Exception as e:
        print(f"Model: {model} -> Error: {e}")
