import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
criteria = [
    {'name': 'Color', 'type': 'Enum', 'range': 'Navy Blue, Black, White, Red'},
    {'name': 'Defective?', 'type': 'Boolean', 'range': 'Yes / No'},
    {'name': 'Estimated Price', 'type': 'Range', 'range': '$100 - $1,000'},
    {'name': 'Quality Score', 'type': 'Scale', 'range': '1-10'},
    {'name': 'Rejection Reason', 'type': 'Free Text', 'range': 'Max 200 chars'}
]
text = 'Luxury Italian Leather Handbag in Navy Blue. Handcrafted with flawless stitching, no defects detected.'

prompt = f"""Evaluate the following text against the specified criteria.
Text: "{text}"

Criteria:
{json.dumps(criteria, indent=2)}

Respond with a strictly valid JSON object where keys are the exact criterion names:
{{
  "<criterion_name>": {{
    "value": "<the evaluated value conforming strictly to type and range>",
    "confidence": 95.0,
    "reasoning": "<one sentence rationale>"
  }}
}}
Return ONLY valid JSON. No markdown ticks, no preamble."""

r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
    'model': 'nvidia/nemotron-3.5-lightning:free',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0.0
}, timeout=15.0)

print('STATUS:', r.status_code)
if r.status_code == 200:
    print('RESPONSE:\n', r.json()['choices'][0]['message']['content'])
else:
    print('ERROR:\n', r.text)
