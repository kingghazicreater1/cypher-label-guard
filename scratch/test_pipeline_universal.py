import re

def _extract_prop_tokens(s: str) -> set:
    core = re.sub(r'\[[A-Z_]+\]', '', s).strip().lower()
    tokens = re.findall(r'\b\w+\b', core)
    stop_words = {'a', 'an', 'the', 'to', 'of', 'about', 'could', 'for', 'in', 'on', 'at', 'by', 'with', 'and', 'or', 'from'}
    res = set()
    for t in tokens:
        if t in stop_words:
            continue
        t = re.sub(r'(ations|ation|ions|ion|ings|ing|ments|ment|ed|es)$', '', t)
        if t.endswith('s') and not t.endswith('ss'):
            t = t[:-1]
        if t:
            res.add(t)
    return res

voter_items = {
    "model_1": [
        "evaluated for palpitations and chest discomfort [CONFIRMED]",
        "ECG performed showing normal sinus rhythm [CONFIRMED]",
        "echocardiogram revealed mild mitral valve regurgitation [CONFIRMED]",
        "prescribed Atenolol 25mg once daily [CONFIRMED]",
        "warned regurgitation could progress to heart failure [HYPOTHETICAL]",
        "patient agreed to try medication for 2 weeks and return for follow-up [CONFIRMED]"
    ],
    "model_2": [
        "evaluated for palpitations and chest discomfort [CONFIRMED]",
        "ECG performed showing normal sinus rhythm [CONFIRMED]",
        "echocardiogram revealed mild mitral valve regurgitation [CONFIRMED]",
        "prescribed Atenolol 25mg once daily [CONFIRMED]",
        "warned about progression to heart failure [INTENT]",
        "patient agreed to try medication for 2 weeks and return for follow-up [INTENT]"
    ]
}

clusters = []
for v_id, items in voter_items.items():
    for item in items:
        if not item:
            continue
        matched = False
        prop_a = _extract_prop_tokens(item)
        for c in clusters:
            prop_b = _extract_prop_tokens(c["canonical"])
            if prop_a and prop_b:
                inter = len(prop_a & prop_b)
                jaccard = inter / len(prop_a | prop_b)
                overlap = inter / min(len(prop_a), len(prop_b))
                sim = max(jaccard, overlap * 0.85)
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

total_voters = len(voter_items)
quorum = max(2, int(round(total_voters / 2.0))) if total_voters > 2 else 1
raw_accepted = [c for c in clusters if len(c["voters"]) >= quorum]

# Deduplicate
accepted_clusters = []
for c in raw_accepted:
    is_dup = False
    prop_c = _extract_prop_tokens(c["canonical"])
    for ac in accepted_clusters:
        prop_ac = _extract_prop_tokens(ac["canonical"])
        if prop_c and prop_ac:
            inter = len(prop_c & prop_ac)
            overlap = inter / min(len(prop_c), len(prop_ac))
            if overlap >= 0.75:
                is_dup = True
                ac["voters"].update(c["voters"])
                if len(c["canonical"]) > len(ac["canonical"]):
                    ac["canonical"] = c["canonical"]
                break
    if not is_dup:
        accepted_clusters.append(c)

print(f"Total clusters accepted: {len(accepted_clusters)} (from {len(clusters)} raw)")
support_ratios = [len(c["voters"]) / total_voters for c in accepted_clusters]
concordance_ratio = round(sum(support_ratios) / len(support_ratios), 2)
unanimous_items = len([c for c in accepted_clusters if len(c["voters"]) == total_voters])
print("Concordance Ratio:", concordance_ratio)
print(f"Unanimous Items: {unanimous_items}/{len(accepted_clusters)}")
for c in accepted_clusters:
    print(f" - [{len(c['voters'])}/{total_voters} votes] {c['canonical']}")
