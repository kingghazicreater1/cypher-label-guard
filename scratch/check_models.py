import os, httpx, asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_groq():
    key = os.getenv('GROQ_API_KEY')
    models = ['openai/gpt-oss-120b', 'qwen/qwen3.8-27b', 'openai/gpt-oss-20b']
    for m in models:
        payload = {
            'model': m,
            'messages': [{'role': 'user', 'content': 'respond with JSON {"test": 1}'}],
            'temperature': 0.0,
            'max_tokens': 100
        }
        if 'oss' in m:
            payload['reasoning_effort'] = 'low'
        headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                r = await client.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=payload)
                print(m, 'status:', r.status_code, r.json()['choices'][0]['message'].get('content'))
            except Exception as e:
                print(m, 'err:', e)

asyncio.run(test_groq())
