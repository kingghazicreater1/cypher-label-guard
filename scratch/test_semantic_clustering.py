import re
import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from collections import Counter

def token_similarity(a: str, b: str) -> float:
    tokens_a = set(re.findall(r'\b\w+\b', a.lower()))
    tokens_b = set(re.findall(r'\b\w+\b', b.lower()))
    if not tokens_a or not tokens_b:
        return 1.0 if a.strip().lower() == b.strip().lower() else 0.0
    inter = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    # Jaccard or high overlap containment
    jaccard = len(inter) / len(union)
    overlap = len(inter) / min(len(tokens_a), len(tokens_b))
    return max(jaccard, overlap * 0.8)

def cluster_semantic_items(voter_items: dict[str, list[str]], total_voters: int):
    # voter_items: { voter_id: [item1, item2, ...] }
    clusters = [] # list of {"canonical": str, "voters": set()}
    
    for v_id, items in voter_items.items():
        for item in items:
            item_clean = item.strip()
            if not item_clean:
                continue
            matched = False
            for c in clusters:
                if token_similarity(item_clean, c["canonical"]) >= 0.55:
                    c["voters"].add(v_id)
                    # keep more descriptive or canonical item
                    if len(item_clean) > len(c["canonical"]):
                        c["canonical"] = item_clean
                    matched = True
                    break
            if not matched:
                clusters.append({"canonical": item_clean, "voters": {v_id}})
                
    quorum = max(2, int(round(total_voters / 2.0))) if total_voters > 2 else 1
    accepted = [c["canonical"] for c in clusters if len(c["voters"]) >= quorum]
    support_ratios = [len(c["voters"]) / total_voters for c in clusters if len(c["voters"]) >= quorum]
    avg_support = sum(support_ratios) / len(support_ratios) if support_ratios else 0.0
    return accepted, avg_support

# Test with POLICY/THREAT from Job #441366:
v_votes = {
    "groq_oss120b": [
        "account would be permanently frozen within 24 hours unless Mr. Ade verified his identity",
        "pay a ₦15,000 security fee to reverse the block"
    ],
    "groq_oss20b": [
        "threatened that the account would be permanently frozen within 24 hours unless Mr. Ade verified his identity by clicking a link"
    ]
}

accepted, avg_support = cluster_semantic_items(v_votes, total_voters=2)
print("POLICY/THREAT accepted:", accepted)
print("Support:", avg_support)
