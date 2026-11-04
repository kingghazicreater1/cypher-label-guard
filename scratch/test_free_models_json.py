import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
prompt = 'Evaluate: "Navy Blue Bag". Output valid JSON ONLY: {"Color": "Navy Blue", "Quality": 9}'

models_to_test = [
    'liquid/lfm-2.5-2.6b:free',
    'dots-studio/dots-3-note-preview:free',
    'thinkingmachines/inkling-small:free',
    'google/gemma-4-31b-it:free',
    'meta-llama/llama-3.3-70b-instruct:free',
]

for m in models_to_test:
    try:
        r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
            "model": m,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 500
        }, timeout=8.0)
        print(f"Model: {m} -> Status: {r.status_code}")
        if r.status_code == 200:
            msg = r.json()["choices"][0]["message"]
            print("  CONTENT:", msg.get("content"))
            if not msg.get("content"):
                print("  REASONING (first 80):", str(msg.get("reasoning"))[:80])
    except Exception as e:
        print(f"Model: {m} -> Error: {e}")
