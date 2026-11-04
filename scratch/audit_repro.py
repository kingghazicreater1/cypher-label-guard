import re

print("=== A. Binary-guard false positives (substring match, first 512 chars) ===")
sigs = ["ftyp", "moov", "mdat", "%PDF", "PK\x03\x04", "\x89PNG", "GIF8", "RIFF", "MZ"]
samples = [
    "Please review the tariff schedule attached.",          # 'riff'
    "Contact Hamza Khan about the invoice.",                # 'mz'
    "Amazon order summary: 3 items shipped.",               # 'mz'
    "Cinema review: the moovie was great",                  # 'moov'
    "Score GIF8 is not a thing but v-gif8 appears",         # 'gif8'
    "Patient notes: no complaints.",                        # clean
]
for s in samples:
    hit = [x for x in sigs if x.lower() in s[:512].lower()]
    print(("REJECTED " if hit else "ok       "), hit, "|", s)

print()
print("=== B. Dedup regression: distinct obligations merged by same_head_predicate/overlap ===")
def toks(s):
    core = re.sub(r'\[[A-Z_]+\]', '', s).strip().lower()
    stop = {'a','an','the','to','of','about','could','for','in','on','at','by','with','and','or','from','is'}
    out = set()
    for t in re.findall(r'\b\w+\b', core):
        if t in stop: continue
        t = re.sub(r'(ations|ation|ions|ion|ings|ing|ments|ment|ed|es)$', '', t)
        if t.endswith('s') and not t.endswith('ss'): t = t[:-1]
        if t: out.add(t)
    return out

def merged(a, b):
    pa, pb = toks(a), toks(b)
    ov = len(pa & pb) / min(len(pa), len(pb))
    ta = re.findall(r'\[([A-Z_]+)\]', a); tb = re.findall(r'\[([A-Z_]+)\]', b)
    ha = ' '.join(re.findall(r'\b\w+\b', re.sub(r'\[[A-Z_]+\]', '', a).lower())[:3])
    hb = ' '.join(re.findall(r'\b\w+\b', re.sub(r'\[[A-Z_]+\]', '', b).lower())[:3])
    return (ov >= 0.65 or (bool(ta) and ta == tb and ha == hb)), round(ov, 2)

pairs = [
    ("Tenant shall not sublet the premises [TENANT]", "Tenant shall not assign the lease [TENANT]"),
    ("Tenant shall pay rent of $2,500 [TENANT]", "Tenant shall pay late fee of $150 [TENANT]"),
    ("prescribed Atenolol 25mg once daily [CONFIRMED]", "prescribed Metoprolol 50mg twice daily [CONFIRMED]"),
    ("patient denied fever [NEGATED]", "patient denied chills [NEGATED]"),
]
for a, b in pairs:
    m, ov = merged(a, b)
    print(("DATA LOSS (merged) " if m else "kept separate      "), "overlap", ov, "|", a, "<->", b)

print()
print("=== C. Quorum rule with 2 voters (quorum=1 => union) ===")
total_voters = 2
quorum = max(2, int(round(total_voters / 2.0))) if total_voters > 2 else 1
print("quorum for 2 voters =", quorum, "-> any single-model hallucination is accepted into output")
