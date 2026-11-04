import os
from dotenv import load_dotenv
load_dotenv()
import numpy as np
import cv2
import base64
import httpx
import json

img = np.full((400, 600, 3), 240, dtype=np.uint8)
cv2.rectangle(img, (50, 100), (350, 300), (80, 80, 80), -1)
cv2.rectangle(img, (70, 120), (330, 260), (30, 30, 30), -1)
cv2.circle(img, (450, 200), 50, (30, 30, 210), -1)
cv2.rectangle(img, (380, 270), (430, 370), (20, 20, 20), -1)
cv2.circle(img, (500, 320), 25, (25, 25, 25), -1)
_, buf = cv2.imencode('.jpg', img)
b64_str = base64.b64encode(buf.tobytes()).decode('utf-8')

key = os.getenv("OPENROUTER_API_KEY", "")

prompt = """Identify all distinct physical objects and products visible in this image.
Return strictly valid JSON:
{"primary_product": "Main entity", "objects": ["item1", "item2"]}"""

r = httpx.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={
        'model': 'google/gemini-2.5-flash',
        'messages': [{
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64_str}'}}
            ]
        }],
        'max_tokens': 120,
    },
    timeout=10.0
)

print('Status:', r.status_code)
print('Reply:', r.json()['choices'][0]['message']['content'])
