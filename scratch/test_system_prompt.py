import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json
import time

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
prompt = """Target: "Navy Blue Luxury Handbag. Pristine, no defects."
Criteria:
- Color (Navy Blue, Black, Red)
- Defective? (Yes/No)
- Quality (1-10)

Output strict JSON: {"Color": {"value": "..."}, "Defective?": {"value": "..."}, "Quality": {"value": "..."}}"""

t0 = time.time()
r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
    "model": "nvidia/nemotron-3.5-lightning:free",
    "messages": [
        {"role": "system", "content": "/no_thinking\nYou are a deterministic parser. Output JSON directly starting with { and ending with }."},
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.0,
    "max_tokens": 500
}, timeout=15.0)

print(f"Status: {r.status_code} in {round(time.time() - t0, 2)}s")
msg = r.json()["choices"][0]["message"]
print("CONTENT:", msg.get("content"))
print("REASONING:", str(msg.get("reasoning"))[:120])
