import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json
import re

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
criteria = [
    {"name": "Color", "type": "Enum", "range": "Navy Blue, Black, White, Red"},
    {"name": "Defective?", "type": "Boolean", "range": "Yes / No"},
    {"name": "Quality Score", "type": "Scale", "range": "1-10"},
    {"name": "Estimated Price", "type": "Range", "range": "$100 - $1,000"}
]
target_text = "Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected."

prompt = f"""Evaluate the following document against the specified criteria.
Target Document:
\"\"\"{target_text[:3500]}\"\"\"

Criteria Specifications:
{json.dumps(criteria, indent=2)}

Respond with a strictly valid JSON object where keys are the exact criterion names:
{{
  "<criterion_name>": {{
    "value": "<the evaluated value conforming strictly to the criterion type and range>",
    "confidence": 95.0,
    "reasoning": "<one sentence justification>"
  }}
}}
Return ONLY valid JSON. No markdown code blocks, no other text."""

r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
    "model": "nvidia/nemotron-3.5-lightning:free",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.0,
    "max_tokens": 1000
}, timeout=20.0)

print("STATUS:", r.status_code)
msg = r.json()["choices"][0]["message"]
content = msg.get("content") or msg.get("reasoning")
print("RAW OUTPUT:\n", content)

cleaned = content.strip()
if cleaned.startswith("```"):
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

try:
    data = json.loads(cleaned)
    print("SUCCESSFULLY PARSED DIRECT JSON:", list(data.keys()))
except Exception as e:
    print("DIRECT JSON FAILED:", e)
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(0))
            print("REGEX PARSED JSON:", list(d.keys()))
        except Exception as e2:
            print("REGEX FAILED:", e2)
