import os
import re
import sys
import json
import asyncio
import httpx
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

load_dotenv()
key = os.getenv("GROQ_API_KEY")

text = (
    "On 18 June 2024, at 09:14 AM, Horizon Bank customer service sent an urgent email from the address alerts@secure-update-portal.com to Mr. Samuel Ade. "
    "The email claimed that a suspicious login attempt was detected on 17 June 2024 at 02:45 AM from Lagos, Nigeria. "
    "The message stated that an unauthorized transfer of ₦450,000 had been blocked, but threatened that the account would be permanently frozen within 24 hours "
    "unless Mr. Ade verified his identity by clicking a link. Mr. Ade was instructed to pay a ₦15,000 security fee to reverse the block. "
    "The email was signed by Mr. David Okon, Head of Security, but Mr. Ade ignored it and reported the message to the real Horizon Bank fraud team at 11:00 AM."
)

criteria = [
    {"name": "PERSON", "type": "Free Text"},
    {"name": "ORGANIZATION", "type": "Free Text"},
    {"name": "DATE", "type": "Free Text"},
    {"name": "TIME", "type": "Free Text"},
    {"name": "MONEY", "type": "Free Text"},
    {"name": "POLICY/THREAT", "type": "Free Text"},
    {"name": "EVENT", "type": "Free Text"}
]

prompt_rules = """CRITICAL EVALUATION INSTRUCTIONS:
1. EXHAUSTIVE RECALL & EXTRACTION: Extract ALL relevant entities/instances present in the specimen for each criterion. Never stop at only the first instance. When multiple entities belong to a criterion, separate them with semicolons (;).
2. COMPLETE & VERBATIM STRINGS: Extract full, unabbreviated names (e.g. 'Mr. Samuel Ade' not 'Samuel'), exact amounts with currency signs (e.g. '₦450,000; ₦15,000'), and full dates/times.
3. TEMPORAL GROUNDING (TIME VS DURATION):
   - Clock Time (TIME / TIMESTAMP): Extract strictly clock-face or instant timestamps (e.g. '09:14 AM', '02:45 AM', '11:00 AM').
   - Duration / Elapsed Interval (e.g. '24 hours', '72 hours') are intervals/durations and must NOT be reported as clock time unless specifically requested.
4. MUTUAL EXCLUSIVITY PRINCIPLE: When multiple criteria headings are present, place each entity into its single most specific matching heading without duplicating the exact same entity across multiple headings:
   - Named proper individuals route strictly to PERSON / NAMES.
   - Professional titles, capacities, or occupations route strictly to ROLE / TITLE.
5. EPISTEMIC MODALITY & FACT STATUS: When extracting events, claims, or actions, distinguish factual reality from contested allegations, reported messages, or future intent:
   - Mark as [CONFIRMED] ONLY if the event is established as verified factual history by the narrator/document (e.g. 'reported message to fraud team at 11:00 AM', 'Mr. Ade ignored email').
   - Mark as [DISPUTED] or [CLAIM] for any statement, notification, allegation, or claim originating from an email, message, party assertion, or contested allegation (e.g. 'email claimed suspicious login attempt', 'alleged unauthorized transfer blocked'). Never mark third-party claims or email assertions as [CONFIRMED].
   - Mark as [INTENT] for threats, warnings, demands, or conditional future actions (e.g. 'threatened account would be frozen within 24 hours').
   - Mark as [ATTEMPTED] if an action was initiated or attempted but not completed.
   - Mark as [NEGATED] if refused, reversed, or explicitly did not occur.
   - For EVENT: Extract key actions/events concisely (under 10 words per event), each strictly tagged with its epistemic modality.
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

async def test_live():
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    models_config = [
        ("groq_oss120b", "openai/gpt-oss-120b", {"reasoning_effort": "low", "max_tokens": 1500}),
        ("groq_qwen27b", "qwen/qwen3.8-27b", {"max_tokens": 800}),
        ("groq_oss20b", "openai/gpt-oss-20b", {"reasoning_effort": "low", "max_tokens": 1200})
    ]
    results = {}
    for label, model, extra_params in models_config:
        payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0, **extra_params}
        async with httpx.AsyncClient(timeout=25.0) as client:
            try:
                r = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                if r.status_code == 200:
                    choice = r.json()["choices"][0]["message"]
                    content = choice.get("content") or choice.get("reasoning") or ""
                    # clean json
                    clean = re.sub(r"^```json\s*", "", content.strip())
                    clean = re.sub(r"\s*```$", "", clean)
                    results[label] = json.loads(clean)
                else:
                    print(f"Error {model}: {r.status_code} {r.text}")
            except Exception as e:
                print(f"Exception {model}: {e}")

    with open("scratch/job_441366_model_outputs.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Saved model outputs to scratch/job_441366_model_outputs.json")

if __name__ == "__main__":
    asyncio.run(test_live())
