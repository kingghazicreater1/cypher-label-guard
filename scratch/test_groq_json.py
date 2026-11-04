import os
import requests
from dotenv import load_dotenv

load_dotenv()
groq_key = os.getenv('GROQ_API_KEY')
headers = {'Authorization': 'Bearer ' + groq_key, 'Content-Type': 'application/json'}
payload = {
    'model': 'openai/gpt-oss-120b',
    'messages': [{'role': 'user', 'content': 'Evaluate heading product name: give a 2-word product title for 22.PNG. Output strictly valid JSON like {"product name": "..."}'}],
    'max_tokens': 600
}
r = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload)
print('Response code:', r.status_code)
choice = r.json()['choices'][0]['message']
content = choice.get('content') or ''
print('Content:', content.encode('ascii', errors='replace').decode('ascii'))
