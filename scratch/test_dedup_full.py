import re

def normalize_clause_tokens(s: str) -> set[str]:
    core = re.sub(r'\[[A-Z_]+\]', '', s).strip().lower()
    raw_tokens = re.findall(r'\b\w+\b', core)
    STOP_WORDS = {"a", "an", "the", "to", "of", "about", "could", "for", "in", "on", "at", "by", "with", "and", "or"}
    stemmed = []
    for t in raw_tokens:
        if t in STOP_WORDS:
            continue
        if t.endswith("ion") and len(t) > 5:
            t = t[:-3]
        elif t.endswith("ed") and len(t) > 4:
            t = t[:-2]
        elif t.endswith("ing") and len(t) > 5:
            t = t[:-3]
        elif t.endswith("s") and len(t) > 4:
            t = t[:-1]
        stemmed.append(t)
    return set(stemmed)

def compute_clause_similarity(item_a: str, item_b: str) -> float:
    tokens_a = normalize_clause_tokens(item_a)
    tokens_b = normalize_clause_tokens(item_b)
    if tokens_a and tokens_b:
        inter = len(tokens_a & tokens_b)
        jaccard = inter / len(tokens_a | tokens_b)
        overlap = inter / min(len(tokens_a), len(tokens_b))
        return max(jaccard, overlap * 0.85)
    return 1.0 if item_a.lower() == item_b.lower() else 0.0

# Simulate Job #868294 events
item1 = "warned regurgitation could progress to heart failure [HYPOTHETICAL]"
item2 = "warned about progression to heart failure [INTENT]"
item3 = "patient agreed to try medication for 2 weeks and return for follow-up [INTENT]"

print("Sim item1 vs item2:", compute_clause_similarity(item1, item2))
print("Sim item1 vs item3:", compute_clause_similarity(item1, item3))

# Deduplication test on a list of accepted items
raw_accepted = [
    "evaluated for palpitations and chest discomfort [CONFIRMED]",
    "ECG performed showing normal sinus rhythm [CONFIRMED]",
    "echocardiogram revealed mild mitral valve regurgitation [CONFIRMED]",
    "prescribed Atenolol 25mg once daily [CONFIRMED]",
    "warned regurgitation could progress to heart failure [HYPOTHETICAL]",
    "patient agreed to try medication for 2 weeks and return for follow-up [INTENT]",
    "warned about progression to heart failure [INTENT]"
]

def deduplicate_propositions(items: list[str]) -> list[str]:
    deduped = []
    for it in items:
        is_dup = False
        for i, existing in enumerate(deduped):
            sim = compute_clause_similarity(it, existing)
            if sim >= 0.65:
                is_dup = True
                # If new item is more detailed, replace existing
                if len(it) > len(existing):
                    deduped[i] = it
                break
        if not is_dup:
            deduped.append(it)
    return deduped

final_deduped = deduplicate_propositions(raw_accepted)
print("\nBefore Dedup Count:", len(raw_accepted))
print("After Dedup Count:", len(final_deduped))
print("\nFinal Deduplicated Events:")
for e in final_deduped:
    print(" -", e)
