import os
import json
import httpx
from dotenv import load_dotenv
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")

for raw_h in ["PRODUCT", "LIABILITY", "DEFECT"]:
    prompt = f"""You are the CypherLabelGuard Enterprise Schema Clarification AI.
A user entered this custom labeling heading: "{raw_h}".

Task:
Analyze if this heading has:
1. Semantic Ambiguity (multiple meanings, object vs context).
2. Granularity / Level-of-Detail Ambiguity (Axiom 1: Constituent Boundary):
   - Does the user want just the bare canonical entity name/category (e.g. 'Sneakers', 'Indemnity', 'Crack')?
   - Or does the user want the complete maximal qualified constituent with immediate quantifiers, measurements, specifications, or operational constraints (e.g. 'Sneakers Size 10 Waterproof', 'Indemnity capped at $1,000,000', 'Hairline crack 2mm on upper rim')?

Generate 2-3 crystal-clear options representing these exact choices so the user has full permission and control over the level of detail extracted.

Respond ONLY with valid JSON:
{{
  "is_ambiguous": true,
  "ambiguity_reason": "One sentence explaining the granularity or semantic ambiguity.",
  "question": "What level of detail or specific aspect are you looking to extract?",
  "options": [
    {{
      "key": "A",
      "label": "Entity Name Only (Canonical Stem)",
      "name": "...",
      "type": "...",
      "range": "..."
    }},
    {{
      "key": "B",
      "label": "Full Qualified Entity (Name + Measurements / Constraints)",
      "name": "...",
      "type": "...",
      "range": "..."
    }}
  ]
}}"""

    r = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
        json={
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 600,
            "reasoning_effort": "low"
        },
        timeout=15.0
    )

    print(f"\n--- Testing '{raw_h}' ---")
    content = r.json()["choices"][0]["message"]["content"]
    clean = content.strip().removeprefix("```json").removesuffix("```").strip()
    data = json.loads(clean)
    print("Ambiguity Reason:", data.get("ambiguity_reason"))
    print("Question:", data.get("question"))
    for opt in data.get("options", []):
        print(f"  [{opt.get('key')}] {opt.get('label')} -> Name: '{opt.get('name')}' (Type: {opt.get('type')}, Range: {opt.get('range')})")
