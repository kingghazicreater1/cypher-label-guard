import os
import sys
from dotenv import load_dotenv
load_dotenv()
import json
import asyncio
import httpx

text = (
    "On 12 June 2024, a customer, Mrs. Amara Obi, attempted to transfer ₦1,500,000 from her current account "
    "at Horizon Bank to a beneficiary, Mr. Femi Adeleke. The transfer was initiated via mobile banking but was "
    "blocked by the bank's anti-fraud policy because the beneficiary account had been flagged for suspicious activity "
    "on 9 June 2024. Mrs. Obi was informed that the funds would not be released unless she visited a branch and "
    "provided additional identification. She argued that she had made similar transfers before without issues and "
    "claimed the bank's SMS notification system had never alerted her to the flag. Horizon Bank's compliance officer, "
    "Ms. Ngozi Okoro, stated that the alert had been sent and that a charge of ₦2,500 had been deducted for the manual "
    "review. Mrs. Obi threatened to close her account if the matter was not resolved within 72 hours. The compliance "
    "officer agreed to expedite the review but confirmed that no refund of the ₦2,500 charge would be issued unless the "
    "flag was proven to be an error. A complaint was filed at 3:15 PM, and Mrs. Obi left without the transfer being completed."
)

criteria = [
    {"name": "PERSON", "type": "Free Text"},
    {"name": "ORGANIZATIONS", "type": "Free Text"},
    {"name": "DATE", "type": "Free Text"},
    {"name": "TIME", "type": "Free Text"},
    {"name": "MONEY", "type": "Free Text"},
    {"name": "ROLE", "type": "Free Text"},
    {"name": "EVENT", "type": "Free Text"}
]

prompt_rules = """CRITICAL EVALUATION INSTRUCTIONS:
1. EXHAUSTIVE RECALL & EXTRACTION: Extract ALL relevant entities/instances present in the specimen for each criterion. Never stop at only the first instance. When multiple entities belong to a criterion, separate them with semicolons (;).
2. COMPLETE & VERBATIM STRINGS: Extract full, unabbreviated names (e.g. 'Mrs. Amara Obi' not 'Mrs. Obi'), exact amounts with currency signs (e.g. '₦1,500,000; ₦2,500'), and full dates/times.
3. TEMPORAL GROUNDING (TIME VS DURATION):
   - Clock Time (TIME / TIMESTAMP): Extract strictly clock-face or instant timestamps (e.g. '3:15 PM', '14:30:00').
   - Duration / Elapsed Interval (e.g. '72 hours', '3 days') are intervals/durations and must NOT be reported as clock time unless specifically requested.
4. MUTUAL EXCLUSIVITY PRINCIPLE: When multiple criteria headings are present, place each entity into its single most specific matching heading without duplicating the exact same entity across multiple headings:
   - Named proper individuals (e.g. 'Mrs. Amara Obi', 'Mr. Femi Adeleke') route strictly to PERSON / NAMES.
   - Professional titles, organizational roles, capacities, or occupations (e.g. 'customer', 'beneficiary', 'compliance officer', 'bank manager') route strictly to ROLE / TITLE.
5. EPISTEMIC MODALITY & FACT STATUS: When extracting events, claims, or actions, distinguish factual reality from contested allegations or future intent:
   - Mark as [CONFIRMED] if the text establishes it definitely occurred as a verified fact.
   - Mark as [ATTEMPTED] if an action was initiated or attempted but not completed (e.g. 'attempted transfer of ₦1,500,000').
   - Mark as [DISPUTED] if asserted by one party and denied by another (e.g. 'SMS notification sent').
   - Mark as [INTENT] if expressing a threat, warning, conditional intent, or future action (e.g. 'threatened to close account within 72 hours').
   - Mark as [NEGATED] if refused, reversed, or explicitly did not occur (e.g. 'no refund of charge').
6. Comply strictly with the requested Type (Boolean, Enum, Scale, Free Text) and Range options if provided.
7. Keep your internal reasoning concise (under 25 words)."""

prompt = f"""Evaluate the following specimen/document against the specified criteria.
Target Document:
\"\"\"{text}\"\"\"

Criteria Specifications:
{json.dumps(criteria, indent=2)}

{prompt_rules}

Respond with a strictly valid JSON object where keys are the exact criterion names:
{{
  "<criterion_name>": {{
    "value": "<exhaustive semicolon-separated list of ALL extracted entities matching this heading from the target document>",
    "confidence": 100.0,
    "reasoning": "<one sentence justification>"
  }}
}}
Return ONLY valid JSON. No markdown code blocks, no other text."""

async def main():
    key = os.environ.get("GROQ_API_KEY")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    results = {}
    models_config = [
        ("openai/gpt-oss-120b", {"reasoning_format": "hidden", "max_tokens": 1500}),
        ("qwen/qwen3.8-27b", {"max_tokens": 800}),
        ("openai/gpt-oss-20b", {"reasoning_format": "hidden", "max_tokens": 1200})
    ]
    for model, extra_params in models_config:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0, **extra_params}
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                r = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if r.status_code == 200:
                    raw_content = r.json()["choices"][0]["message"]["content"]
                    results[model] = raw_content
                else:
                    results[model] = f"Error {r.status_code}: {r.text}"
            except Exception as e:
                results[model] = f"Exception: {e}"

    with open("scratch/model_responses.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Responses written to scratch/model_responses.json")

if __name__ == "__main__":
    asyncio.run(main())
