import glob, re

for p in glob.glob('frontend/src/**/*.tsx', recursive=True) + glob.glob('frontend/src/**/*.ts', recursive=True):
    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
        t = f.read()
        matches = re.findall(r'(\$\d+[\w\s/]+)', t)
        if any(w in t.lower() for w in ['500 items', 'basic', 'master', 'credit pack', 'tier']):
            relevant = [m for m in matches if any(x in m for x in ['19', '20', '49', '50', '99', '129', '499', '500'])]
            if relevant:
                print(f"{p}: {relevant[:5]}")
