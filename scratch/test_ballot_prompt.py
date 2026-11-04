import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'HTTP-Referer': 'https://cypherlabelguard.ai',
    'X-Title': 'CypherLabelGuard',
    'Content-Type': 'application/json',
}
ballot_prompt = """Analyze this text: "Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected."
Keep your internal reasoning very brief (under 30 words).
Return a strict JSON object with keys:
- category: 1-3 words classification
- confidence: float between 0.50 and 1.00
- subcategory: 1-3 words subtype
- anomaly: detected anomaly or 'Normal'
- sentiment: 'Positive', 'Neutral', 'Negative', or 'Critical'
- entity: primary entity or 'None'
- temporal: time sensitivity or 'None'
- risk: 'SAFE', 'LOW RISK', 'MEDIUM RISK', 'HIGH RISK', or 'VIOLATION'
Return JSON ONLY."""

r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
    "model": "nvidia/nemotron-3.5-lightning:free",
    "messages": [{"role": "user", "content": ballot_prompt}],
    "temperature": 0.0,
    "max_tokens": 2500
})
print("Status:", r.status_code)
msg = r.json()["choices"][0]["message"]
print("Finish:", r.json()["choices"][0].get("finish_reason"))
print("Content:", msg.get("content"))
print("Reasoning len:", len(msg.get("reasoning") or ""))
