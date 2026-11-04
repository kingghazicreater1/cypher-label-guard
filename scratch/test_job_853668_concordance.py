import re

crit_votes = {
    "groq_oss120b": "persistent cough [CONFIRMED]; pneumonia [RULED_OUT]; fever [NEGATED]; chills [NEGATED]; shortness of breath [NEGATED]",
    "openrouter": "persistent cough [CONFIRMED]; pneumonia [RULED_OUT]; fever [NEGATED]; chills [NEGATED]; shortness of breath [NEGATED]"
}
total_voters = len(crit_votes)
print("total_voters:", total_voters)

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

print("Number of clusters:", len(clusters))
for c in clusters:
    print("Cluster:", c["canonical"], "Voters:", c["voters"], "len:", len(c["voters"]))

quorum = max(2, int(round(total_voters / 2.0))) if total_voters > 2 else 1
print("quorum:", quorum)
accepted_items = [c["canonical"] for c in clusters if len(c["voters"]) >= quorum]
print("accepted_items count:", len(accepted_items))

support_ratios = [len(c["voters"]) / total_voters for c in clusters if len(c["voters"]) >= quorum]
print("support_ratios:", support_ratios)
concordance_ratio = round(sum(support_ratios) / len(support_ratios), 2)
print("concordance_ratio:", concordance_ratio)
effective_affirmative = int(round(concordance_ratio * total_voters))
print("effective_affirmative:", effective_affirmative)
agree_str = f"{effective_affirmative} of {total_voters} APIs concordant (Supermajority Set Consensus)" if concordance_ratio >= 0.85 else f"{effective_affirmative} of {total_voters} APIs concordant"
print("agree_str:", agree_str)
