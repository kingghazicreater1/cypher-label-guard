import os
from dotenv import load_dotenv
load_dotenv()
import httpx
import json

headers = {
    'Authorization': 'Bearer " + os.getenv("OPENROUTER_API_KEY", "")',
    'Content-Type': 'application/json',
}
r = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json={
    "model": "liquid/lfm-2.5-2.6b:free",
    "messages": [{"role": "user", "content": 'Evaluate: "Navy Blue Bag". Return JSON: {"color": "Navy Blue"}'}],
    "temperature": 0.0,
    "max_tokens": 500
})
choice = r.json()["choices"][0]
print("Finish Reason:", choice.get("finish_reason"))
msg = choice.get("message", {})
print("Content:", msg.get("content"))
reasoning = msg.get("reasoning")
print("Reasoning length:", len(reasoning) if reasoning else 0)
if reasoning:
    print("Reasoning end:", reasoning[-300:])
