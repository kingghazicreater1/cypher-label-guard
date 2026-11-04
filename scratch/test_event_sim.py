import re

def compute_sim(item1, item2):
    def normalize_clause(s):
        # 1. Strip epistemic tags: [CONFIRMED], [INTENT], etc.
        core = re.sub(r'\[[A-Z_]+\]', '', s).strip().lower()
        # 2. Extract tokens, stemming simple suffixes (e.g. progression -> progress, warned -> warn)
        raw_tokens = re.findall(r'\b\w+\b', core)
        STOP_WORDS = {"a", "an", "the", "to", "of", "about", "could", "for", "in", "on", "at", "by", "with"}
        stemmed = []
        for t in raw_tokens:
            if t in STOP_WORDS:
                continue
            # Simple universal suffix normalization
            if t.endswith("ion") and len(t) > 5:
                t = t[:-3] # progression -> progress
            elif t.endswith("ed") and len(t) > 4:
                t = t[:-2] # warned -> warn
            elif t.endswith("ing") and len(t) > 5:
                t = t[:-3] # warning -> warn
            elif t.endswith("s") and len(t) > 4:
                t = t[:-1] # risks -> risk
            stemmed.append(t)
        return set(stemmed)

    tokens_a = normalize_clause(item1)
    tokens_b = normalize_clause(item2)
    if tokens_a and tokens_b:
        inter = len(tokens_a & tokens_b)
        jaccard = inter / len(tokens_a | tokens_b)
        overlap = inter / min(len(tokens_a), len(tokens_b))
        sim = max(jaccard, overlap * 0.85)
        return sim, tokens_a, tokens_b
    return (1.0 if item1.lower() == item2.lower() else 0.0), tokens_a, tokens_b

item1 = "warned regurgitation could progress to heart failure [HYPOTHETICAL]"
item2 = "warned about progression to heart failure [INTENT]"

sim, t_a, t_b = compute_sim(item1, item2)
print("Tokens A:", t_a)
print("Tokens B:", t_b)
print("Intersection:", t_a & t_b)
print("Similarity:", sim)
