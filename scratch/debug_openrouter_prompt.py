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
criteria = [
    {'name': 'Color', 'type': 'Enum', 'range': 'Navy Blue, Black, White, Red'},
    {'name': 'Defective?', 'type': 'Boolean', 'range': 'Yes / No'},
    {'name': 'Quality Score', 'type': 'Scale', 'range': '1-10'},
    {'name': 'Estimated Price', 'type': 'Range', 'range': '$100 - $1,000'}
]
prompt = f"""Evaluate the following document against the specified criteria.
Target Document:
\"\"\"Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected.\"\"\"

Criteria Specifications:
{json.dumps(criteria, indent=2)}

Respond with a strictly valid JSON object where keys are the exact criterion names.
Return ONLY valid JSON. Start directly with '{{' and end with '}}'. No preamble, no explanation, no thoughts."""

for model in ["nvidia/nemotron-3.5-lightning:free", "google/gemma-4-31b-it:free", "meta-llama/llama-3.3-70b-instruct:free"]:
    print(f"\n--- Testing Model: {model} ---")
    try:
        r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
            'model': model,
            'messages': [
                {'role': 'system', 'content': 'You are a deterministic JSON API. Output strictly valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.0,
            'max_tokens': 1500
        }, timeout=20.0)
        print('Status:', r.status_code)
        if r.status_code == 200:
            choice = r.json()['choices'][0]['message']
            content = choice.get('content')
            reasoning = choice.get('reasoning')
            print('Content received:', bool(content))
            if content:
                print('Content sample:', content[:200])
            else:
                print('Reasoning length:', len(reasoning or ''))
        else:
            print('Error:', r.text[:200])
    except Exception as e:
        print('Exception:', e)
