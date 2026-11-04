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
r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
    'model': 'liquid/lfm-2.5-2.6b:free',
    'messages': [
        {'role': 'user', 'content': 'Analyze: "Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected."\nReturn JSON: {"Color": "Navy Blue", "Defective?": "No", "Quality Score": "10"}. Return JSON only.'}
    ],
    'temperature': 0.0,
    'max_tokens': 300
}, timeout=15.0)

print('Status:', r.status_code)
if r.status_code == 200:
    msg = r.json()['choices'][0]['message']
    print('Content:', msg.get('content'))
else:
    print('Error:', r.text)
