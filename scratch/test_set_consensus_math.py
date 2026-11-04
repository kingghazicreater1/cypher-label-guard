import re

def compute_set_consensus(crit_votes):
    total_voters = len(crit_votes)
    active_values = list(crit_votes.values())
    
    voter_items = {}
    for v_label, raw_val in crit_votes.items():
        raw_str = str(raw_val)
        parts = [p.strip() for p in raw_str.split(";") if p.strip()]
        voter_items[v_label] = parts if parts else [raw_str.strip()]

    clusters = []  # list of {"canonical": str, "voters": set()}
    for v_id, items in voter_items.items():
        for item in items:
            if not item:
                continue
            matched = False
            for c in clusters:
                tokens_a = set(re.findall(r'\b\w+\b', item.lower()))
                tokens_b = set(re.findall(r'\b\w+\b', c["canonical"].lower()))
                if tokens_a and tokens_b:
                    inter = len(tokens_a & tokens_b)
                    jaccard = inter / len(tokens_a | tokens_b)
                    overlap = inter / min(len(tokens_a), len(tokens_b))
                    sim = max(jaccard, overlap * 0.8)
                else:
                    sim = 1.0 if item.lower() == c["canonical"].lower() else 0.0

                if sim >= 0.55:
                    c["voters"].add(v_id)
                    if len(item) > len(c["canonical"]):
                        c["canonical"] = item
                    matched = True
                    break
            if not matched:
                clusters.append({"canonical": item, "voters": {v_id}})

    quorum = max(2, int(round(total_voters / 2.0))) if total_voters > 2 else 1
    accepted_items = [c["canonical"] for c in clusters if len(c["voters"]) >= quorum]

    if accepted_items:
        chosen_val = "; ".join(accepted_items)
        support_ratios = [len(c["voters"]) / total_voters for c in clusters if len(c["voters"]) >= quorum]
        concordance_ratio = round(sum(support_ratios) / len(support_ratios), 2)
        unanimous_items_count = len([c for c in clusters if len(c["voters"]) == total_voters])
        total_items_count = len(accepted_items)
        pct_int = int(round(concordance_ratio * 100))

        if concordance_ratio >= 0.85:
            agree_str = f"{total_voters} of {total_voters} APIs concordant (Supermajority Set Consensus)"
        elif total_voters <= 2:
            agree_str = f"{total_voters} of {total_voters} APIs concordant ({pct_int}% Set Overlap: {unanimous_items_count}/{total_items_count} items unanimous)"
        else:
            effective_affirmative = max(1, int(round(concordance_ratio * total_voters)))
            agree_str = f"{effective_affirmative} of {total_voters} APIs concordant ({pct_int}% Set Concordance)"
        computed_conf = round(100.0 * concordance_ratio, 1)
    else:
        chosen_val = ""
        computed_conf = 0.0
        agree_str = "0 of 0"

    return chosen_val, computed_conf, agree_str

# Test 1: Full 5 items agreed by 2 voters
v_full = "persistent cough [CONFIRMED]; pneumonia [RULED_OUT]; fever [NEGATED]; chills [NEGATED]; shortness of breath [NEGATED]"
val1, conf1, agree1 = compute_set_consensus({"voter1": v_full, "voter2": v_full})
print("Test 1 (Unanimous 2 voters):")
print("  Value:", val1)
print("  Confidence:", conf1)
print("  Agreement:", agree1)

# Test 2: Voter 1 had all 5 items, Voter 2 had only 2 items
v_partial = "persistent cough [CONFIRMED]; pneumonia [RULED_OUT]"
val2, conf2, agree2 = compute_set_consensus({"voter1": v_full, "voter2": v_partial})
print("\nTest 2 (Partial 2 voters: 5 vs 2 items):")
print("  Value:", val2)
print("  Confidence:", conf2)
print("  Agreement:", agree2)

# Test 3: 5 voters all returning the full string
val3, conf3, agree3 = compute_set_consensus({
    "groq": v_full, "openai": v_full, "claude": v_full, "gemini": v_full, "mistral": v_full
})
print("\nTest 3 (5 voters unanimous):")
print("  Value:", val3)
print("  Confidence:", conf3)
print("  Agreement:", agree3)
