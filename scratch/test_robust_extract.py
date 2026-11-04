import json
import re

def robust_json_extract(raw_text: str):
    if not raw_text:
        return None
    cleaned = raw_text.strip()
    
    # 1. Check for markdown code fences
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass

    # 2. Try direct load
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3. Use JSONDecoder scanning from every '{' position
    decoder = json.JSONDecoder()
    candidates = []
    pos = 0
    while True:
        pos = cleaned.find("{", pos)
        if pos == -1:
            break
        try:
            obj, _ = decoder.raw_decode(cleaned[pos:])
            if isinstance(obj, dict):
                candidates.append(obj)
        except Exception:
            pass
        pos += 1

    if candidates:
        return max(candidates, key=lambda d: len(d))

    return None

test1 = "Here is the response:\n```json\n{\n  \"Color\": \"Navy Blue\",\n  \"Quality\": 9.5\n}\n```\nHope that helps!"
print("Test 1:", robust_json_extract(test1))

test2 = "Thinking process: I should return {\"Color\": \"Blue\"}. Final output:\n{\n  \"Color\": \"Navy Blue\",\n  \"Quality\": 9.5,\n  \"Price\": 500\n}"
print("Test 2:", robust_json_extract(test2))
