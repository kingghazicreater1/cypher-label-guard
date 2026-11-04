import httpx, json, asyncio, os
from dotenv import load_dotenv
load_dotenv()

async def test_universal_taxonomy():
    key = os.getenv("GROQ_API_KEY")
    text = """On March 15, 2024, Mr. Daniel Okafor visited the Lagos branch of FirstTrust Bank to open a savings account. He presented his national identity card and proof of address, as required by the bank's Know Your Customer (KYC) policy. The account officer, Ms. Adaeze Nwosu, explained that the account would attract a 4% annual interest rate and a minimum opening deposit of ₦50,000. Mr. Okafor deposited ₦75,000 and was issued an ATM card. However, he was informed that a monthly maintenance fee of ₦500 would be deducted if his balance fell below ₦20,000. He also opted for mobile banking, which required a one-time activation fee of ₦1,000. The transaction was completed at 11:45 AM, and a receipt was issued."""
    
    prompt = f"""Analyze this document across 8 dimensions:
\"\"\"{text}\"\"\"

For 'category', select the most accurate canonical domain from this universal taxonomy:
- Finance & Banking
- Legal & Compliance
- Medical & Healthcare
- E-Commerce & Retail
- Technology & Engineering
- Operations & Logistics
- Government & Public Sector
- Education & Research
- Media & Communications
- General & Personal

Return a strict JSON object with keys:
- category: one exact category from the universal taxonomy above
- confidence: float between 0.50 and 1.00
- subcategory: specific 1-3 words subtype
- anomaly: detected anomaly or 'None'
- sentiment: 'Positive', 'Neutral', 'Negative', or 'Critical'
- entity: primary entity or organization
- temporal: time sensitivity or date mentioned
- risk: 'SAFE', 'LOW RISK', 'MEDIUM RISK', 'HIGH RISK', or 'VIOLATION'
Return ONLY valid JSON.
"""
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    for m in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]:
        try:
            r = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json={"model": m, "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}, timeout=15.0)
            if r.status_code == 200:
                print(f"[{m}] -> {r.json()['choices'][0]['message']['content']}")
            else:
                print(f"[{m}] HTTP {r.status_code}")
        except Exception as e:
            print(f"[{m}] Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_universal_taxonomy())
