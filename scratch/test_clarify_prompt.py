import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")

def test_clarify(heading: str, modality: str = "IMAGE"):
    prompt = f"""You are the CypherLabelGuard Enterprise Schema Clarification AI.
A customer wrote this labeling heading for a {modality} specimen: "{heading}".

Determine if this heading is ambiguous (e.g. object vs environment), unresolvable in 2D, or has subjective phrasing.
Provide 2-3 crystal-clear options of what they might be asking, with suggested Types (Enum, Scale, Boolean, Free Text) and Choices.

Respond ONLY with a JSON object:
{{
  "is_ambiguous": true,
  "ambiguity_reason": "One clear sentence explaining the ambiguity.",
  "question": "What specifically are you trying to evaluate?",
  "options": [
    {{
      "key": "A",
      "label": "Short human description",
      "name": "clear_heading_name",
      "type": "Enum",
      "range": "Choice 1, Choice 2, Choice 3"
    }},
    {{
      "key": "B",
      "label": "Another interpretation",
      "name": "another_heading_name",
      "type": "Free Text",
      "range": "Open Free Text (no fixed options)"
    }}
  ]
}}"""
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": prompt}],
        "reasoning_effort": "low",
        "max_tokens": 600
    }
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json=payload, timeout=15.0)
    print(f"=== Heading: '{heading}' ===")
    content = r.json()["choices"][0]["message"]["content"]
    print(content)

if __name__ == "__main__":
    for h in ["surface material", "cap type", "bottle estimate size"]:
        test_clarify(h)
