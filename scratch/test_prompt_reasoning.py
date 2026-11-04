import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")'}

prompt = """Analyze this product: "Luxury Italian Leather Handbag in Navy Blue. Flawlessly crafted, no defects detected."
Keep your internal reasoning extremely brief (under 30 words).
Then output strictly valid JSON matching this schema:
{
  "Color": {"value": "Navy Blue", "confidence": 95.0, "reasoning": "explicitly states Navy Blue"},
  "Defective?": {"value": "No", "confidence": 95.0, "reasoning": "states no defects"},
  "Quality Score": {"value": "10", "confidence": 95.0, "reasoning": "flawlessly crafted"},
  "Estimated Price": {"value": "$500", "confidence": 85.0, "reasoning": "luxury italian leather handbag"}
}
Output ONLY valid JSON."""

r = httpx.post('https://openrouter.ai/api/v1/chat/completions', headers=headers, json={
    'model': 'nvidia/nemotron-3.5-lightning:free',
    'messages': [{'role': 'user', 'content': prompt}],
    'temperature': 0.0,
    'max_tokens': 2500
})
print('Status:', r.status_code)
choice = r.json()['choices'][0]['message']
print('Finish reason:', r.json()['choices'][0].get('finish_reason'))
print('Content:', choice.get('content'))
print('Reasoning length:', len(choice.get('reasoning') or ''))
