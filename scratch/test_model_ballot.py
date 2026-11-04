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
text = "The supplier agrees to unlimited indemnification for all direct and indirect losses, without an explicit liability cap."
prompt = f"""You are the parliamentary evaluator in CypherLabelGuard.
Analyze this target clause across 8 dimensions:
\"\"\"{text}\"\"\"

Return a strictly valid JSON object with keys:
- "category": (1-3 words classification)
- "confidence": (float between 0.50 and 1.00)
- "subcategory": (1-3 words subtype)
- "anomaly": (detected anomaly or "Normal")
- "sentiment": ("Positive", "Neutral", "Negative", or "Critical")
- "entity": (primary entity or "None")
- "temporal": (time sensitivity or "None")
- "risk": ("SAFE", "LOW RISK", "MEDIUM RISK", "HIGH RISK", or "VIOLATION")

Return JSON ONLY. No markdown backticks, no other text."""

start = time.time()
r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
    'model': 'nvidia/nemotron-3.5-lightning:free',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0.0
}, timeout=12.0)
elapsed = round((time.time() - start) * 1000.0, 1)

print(f"Status: {r.status_code} in {elapsed}ms")
if r.status_code == 200:
    print("Content:\n", r.json()['choices'][0]['message']['content'])
else:
    print("Error:", r.text)
