#!/usr/bin/env python3
"""
CypherLabelGuard accuracy benchmark (single file, stdlib only; `prepare` needs `pip install datasets`).
 
It calls YOUR running backend (POST /api/v2/infer), so it measures the real product:
  1. consensus accuracy (what the customer sees)
  2. each provider's own accuracy (from the per-model votes in the same response)
  3. simple majority-vote baseline
  4. accuracy by agreement level (does "4 of 4 agree" really mean "more likely correct"?)
  5. human-review savings if you only review the items the models disagree on
 
Setup (laptop, with your real provider keys in .env):
    ALLOW_GUEST_INFERENCE=true python run_backend.py        # local testing only, never in production
 
Run:
    python cypher_infer_benchmark.py prepare --n 500        # writes benchmark_items.csv (id,text,label)
    python cypher_infer_benchmark.py run --limit 20         # smoke test first (cheap)
    python cypher_infer_benchmark.py run                    # full run, resumable (Ctrl+C then rerun)
    python cypher_infer_benchmark.py report                 # prints + writes benchmark_report.md
 
Your own data instead of AG News (recommended for the customer pitch):
    make benchmark_items.csv with columns id,text,label and set --labels "Defective,No Defect"
    (the label names must be the exact strings you want the models to answer with)
 
Options for run:  --url  --token  --workers  --timeout  --labels  --limit
"""
import argparse
import csv
import json
import math
import random
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
 
ITEMS = "benchmark_items.csv"
RAW = "benchmark_raw.jsonl"
META = "benchmark_meta.json"
ERRORS = "benchmark_errors.csv"
REPORT = "benchmark_report.md"
DEFAULT_LABELS = ["World", "Sports", "Business", "Sci/Tech"]
 
 
# ---------------------------------------------------------------- helpers
def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())
 
 
def make_canon(labels):
    table = {norm(l): l for l in labels}
    # AG News friendly aliases
    aliases = {"scitech": "Sci/Tech", "science": "Sci/Tech", "technology": "Sci/Tech", "tech": "Sci/Tech",
               "sport": "Sports", "biz": "Business", "finance": "Business", "politics": "World"}
 
    def canon(value):
        n = norm(str(value))
        if n in table:
            return table[n]
        for key, lab in aliases.items():
            if key in n and lab in labels:
                return lab
        # label mentioned inside a longer answer, pick the earliest unique one
        hits = [(n.find(k), v) for k, v in table.items() if k and k in n]
        if hits:
            return min(hits)[1]
        return None
 
    return canon
 
 
def vote_text(v):
    if isinstance(v, dict):
        return v.get("value") or v.get("label") or v.get("vote") or ""
    return v
 
 
def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))
 
 
def sign_test_p(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * tail)
 
 
def read_items(path=ITEMS):
    try:
        with open(path, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        sys.exit(f"{path} nahi mili. Pehle `prepare` chalao (ya apni id,text,label CSV rakho).")
 
 
def read_raw(path=RAW):
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    r = json.loads(line)
                    out[str(r["id"])] = r
    except FileNotFoundError:
        pass
    return out
 
 
# ---------------------------------------------------------------- prepare
def cmd_prepare(a):
    try:
        from datasets import load_dataset
    except ImportError:
        sys.exit("Pehle: pip install datasets")
    try:
        ds = load_dataset("fancyzhx/ag_news", split="test")
    except Exception:
        ds = load_dataset("ag_news", split="test")
    names = ds.features["label"].names
    idx = random.Random(a.seed).sample(range(len(ds)), a.n)
    with open(ITEMS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "text", "label"])
        for k, i in enumerate(idx, 1):
            w.writerow([k, ds[i]["text"], names[ds[i]["label"]]])
    print(f"{ITEMS} bana ({a.n} items). Labels: {', '.join(names)}")
 
 
# ---------------------------------------------------------------- run
def call_api(url, token, text, labels, timeout):
    prompt = ("Classify the text into exactly one of: " + ", ".join(labels) +
              ". Answer with only the label.")
    body = json.dumps({
        "text": text,
        "criteria": [{
            "name": "Category",
            "type": "Enum",
            "range": ", ".join(labels),
            "description": prompt,
        }]
    }).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=body, headers=headers)
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    cr = (d.get("criteria_results") or (d.get("data") or {}).get("criteria_results") or [{}])[0]
    return {
        "value": cr.get("value"),
        "confidence": cr.get("confidence"),
        "agreement": cr.get("agreement"),
        "votes": {k: vote_text(v) for k, v in (cr.get("votes") or {}).items()},
        "anomaly": bool(cr.get("anomaly")),
        "decision": ((d.get("data") or {}).get("consensus") or {}).get("decision"),
        "latency_s": round(time.time() - t0, 2),
    }
 
 
def cmd_run(a):
    items = read_items()
    if a.limit:
        items = items[: a.limit]
    labels = [l.strip() for l in a.labels.split(",") if l.strip()]
    done = read_raw()
    todo = [it for it in items if str(it["id"]) not in done or done[str(it["id"])].get("error")]
    print(f"Total {len(items)}, pehle se hue {len(items) - len(todo)}, ab chalenge {len(todo)}")
    if not todo:
        return
    t0 = time.time()
    ok = fail = 0
 
    def work(it):
        last = None
        for attempt in range(3):
            try:
                r = call_api(a.url, a.token, it["text"], labels, a.timeout)
                # If provider keys hit 429 rate limit (0 votes returned), back off and retry
                if r.get("agreement") and "0 of" in r["agreement"] and attempt < 2:
                    time.sleep(3.5 * (attempt + 1))
                    continue
                r["id"] = it["id"]
                if getattr(a, "delay", 0) > 0:
                    time.sleep(a.delay)
                return r
            except Exception as e:  # noqa: BLE001
                last = f"{type(e).__name__}: {e}"
                time.sleep(2.0 * (attempt + 1))
        return {"id": it["id"], "error": last}
 
    with open(RAW, "a", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(work, it) for it in todo]
        for n, fu in enumerate(as_completed(futs), 1):
            r = fu.result()
            out.write(json.dumps(r) + "\n")
            out.flush()
            if r.get("error"):
                fail += 1
            else:
                ok += 1
            if n % 10 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)}  ok={ok} fail={fail}  {n / (time.time() - t0):.2f} items/s")
    prev = {}
    try:
        prev = json.load(open(META))
    except Exception:  # noqa: BLE001
        pass
    prev["elapsed_s"] = round(prev.get("elapsed_s", 0) + time.time() - t0, 1)
    prev["labels"] = labels
    json.dump(prev, open(META, "w"))
    print("Run mukammal. Ab `report` chalao.")
 
 
# ---------------------------------------------------------------- report
def cmd_report(a):
    items = read_items()
    raw = read_raw()
    try:
        meta = json.load(open(META))
    except Exception:  # noqa: BLE001
        meta = {}
    labels = meta.get("labels") or [l.strip() for l in a.labels.split(",")]
    canon = make_canon(labels)
 
    rows = []
    for it in items:
        r = raw.get(str(it["id"]))
        if r is None:
            continue
        rows.append((it, r))
    if not rows:
        sys.exit("Koi result nahi mila. Pehle `run` chalao.")
 
    n = len(rows)
    errors = [(it, r) for it, r in rows if r.get("error")]
    answered = [(it, r) for it, r in rows if not r.get("error")]
    na = len(answered)
 
    cons_ok = {}
    per_api = defaultdict(dict)  # api -> id -> correct(bool)
    maj_ok = {}
    tier = defaultdict(lambda: [0, 0])  # tier -> [count, correct]
    unanimous = [0, 0]
    review_items = 0
    nolabel = 0
    errs_out = []
    for it, r in answered:
        truth = it["label"]
        pred = canon(r.get("value"))
        if pred is None:
            nolabel += 1
        ok = pred == truth
        cons_ok[it["id"]] = ok
        votes = {k: canon(v) for k, v in (r.get("votes") or {}).items()}
        for api, v in votes.items():
            per_api[api][it["id"]] = (v == truth)
        counts = Counter(v for v in votes.values() if v)
        if counts:
            top, tc = counts.most_common(1)[0]
            tie = sum(1 for c in counts.values() if c == tc) > 1
            maj_ok[it["id"]] = (not tie) and top == truth
            key = f"{tc}/{len(votes)}"
        else:
            maj_ok[it["id"]] = False
            key = "0/0"
        tier[key][0] += 1
        tier[key][1] += ok
        if len(votes) >= 3 and key.split("/")[0] == key.split("/")[1]:
            unanimous[0] += 1
            unanimous[1] += ok
        else:
            review_items += 1
        if not ok:
            errs_out.append([it["id"], truth, r.get("value"), key, (it["text"] or "")[:120]])
 
    def pct(k, d):
        return 100.0 * k / d if d else 0.0
 
    cons_k = sum(cons_ok.values())
    lo, hi = wilson(cons_k, n)  # errors count as wrong
    lines = []
    P = lines.append
    P("# CypherLabelGuard benchmark report")
    P("")
    P(f"- Items: {n}   answered: {na}   api errors: {len(errors)}   unrecognised label: {nolabel}")
    if meta.get("elapsed_s"):
        P(f"- Wall time: {meta['elapsed_s']}s  ({n / meta['elapsed_s']:.2f} items/s)")
    P("")
    P("## Accuracy")
    P(f"- **Consensus: {pct(cons_k, n):.1f}%**  ({cons_k}/{n}, 95% CI {100 * lo:.1f}-{100 * hi:.1f}%)")
    best_name, best_k = None, -1
    api_rows = []
    for api, d in sorted(per_api.items()):
        k = sum(d.get(it["id"], False) for it, _ in rows)
        api_rows.append((api, k, len(d)))
        if k > best_k:
            best_name, best_k = api, k
    for api, k, voted in api_rows:
        P(f"- {api}: {pct(k, n):.1f}%  ({k}/{n}, voted on {voted})")
    maj_k = sum(maj_ok.get(it["id"], False) for it, _ in rows)
    P(f"- Simple majority of the provider votes: {pct(maj_k, n):.1f}%  ({maj_k}/{n})")
    P("")
 
    verdict = "Provider votes response mein nahi aaye, single-model comparison nahi ban saka."
    if best_name:
        wins = sum(1 for it, _ in rows if cons_ok.get(it["id"], False) and not per_api[best_name].get(it["id"], False))
        losses = sum(1 for it, _ in rows if (not cons_ok.get(it["id"], False)) and per_api[best_name].get(it["id"], False))
        p = sign_test_p(wins, losses)
        diff = pct(cons_k, n) - pct(best_k, n)
        P(f"## Consensus vs best single model ({best_name})")
        P(f"- Difference: {diff:+.1f} points. Consensus sahi/single galat: {wins}, single sahi/consensus galat: {losses}, sign-test p={p:.3f}")
        P("")
        if p < 0.05 and diff >= 1:
            verdict = "Consensus best single model se behtar hai (statistically significant). Pitch: 'X% vs Y%'."
        elif p < 0.05 and diff <= -1:
            verdict = "Best single model consensus se behtar hai. Consensus ko accuracy ke tor par mat becho, positioning badlo."
        else:
            verdict = ("Farq statistically saaf nahi. Accuracy barabar hai, to value 'agreement score + kam review' hai, "
                       "'zyada accurate' ka claim mat karo.")
 
    P("## Agreement vs correctness")
    P("| models agree | items | accuracy |")
    P("|---|---|---|")
    for key in sorted(tier, reverse=True):
        c, k = tier[key]
        P(f"| {key} | {c} | {pct(k, c):.1f}% |")
    P("")
    if unanimous[0]:
        auto = unanimous[0]
        P("## Human-review saving (sirf non-unanimous items insan dekhe)")
        P(f"- Auto-accept (sab models agree): {auto}/{na} = {pct(auto, na):.0f}% items, in ki accuracy {pct(unanimous[1], auto):.1f}%")
        P(f"- Insan ko dikhane wale items: {review_items}/{na} = {pct(review_items, na):.0f}%")
        final = unanimous[1] + review_items  # assumes the human is right
        P(f"- Agar insan bilkul sahi ho to final accuracy: {pct(final, na):.1f}%")
        P("")
    P("## Verdict")
    P(verdict)
    P("")
    P("Note: AG News public dataset hai aur models ne shayad dekha ho. Customer ko dikhane se pehle apne customer jaisa data (apni labels) par bhi chalao.")
 
    text = "\n".join(lines)
    print(text)
    open(REPORT, "w", encoding="utf-8").write(text + "\n")
    with open(ERRORS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "truth", "consensus_value", "agreement", "text"])
        w.writerows(errs_out)
    print(f"\nSaved: {REPORT}, {ERRORS}")
 
 
def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("prepare")
    sp.add_argument("--n", type=int, default=500)
    sp.add_argument("--seed", type=int, default=42)
    sr = sub.add_parser("run")
    sr.add_argument("--url", default="http://localhost:8000/api/v2/infer")
    sr.add_argument("--token", default="")
    sr.add_argument("--workers", type=int, default=4)
    sr.add_argument("--timeout", type=int, default=120)
    sr.add_argument("--delay", type=float, default=0.0)
    sr.add_argument("--limit", type=int, default=0)
    sr.add_argument("--labels", default=",".join(DEFAULT_LABELS))
    se = sub.add_parser("report")
    se.add_argument("--labels", default=",".join(DEFAULT_LABELS))
    a = p.parse_args()
    {"prepare": cmd_prepare, "run": cmd_run, "report": cmd_report}[a.cmd](a)
 
 
if __name__ == "__main__":
    main()

