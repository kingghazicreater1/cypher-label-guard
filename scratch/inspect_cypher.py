import sqlite3
import os

print("=== CHECKING DATABASES ===")
for db_name in ['cypher_label_guard.db', 'av_guardian.db', 'guardian.db']:
    if os.path.exists(db_name):
        size_mb = os.path.getsize(db_name) / (1024 * 1024)
        print(f"\nDatabase: {db_name} ({size_mb:.2f} MB)")
        try:
            conn = sqlite3.connect(db_name)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in c.fetchall()]
            print("  Tables:", tables)
            for t in tables:
                c.execute(f"SELECT count(*) FROM {t}")
                print(f"    - {t}: {c.fetchone()[0]} rows")
        except Exception as e:
            print("  Error reading db:", e)

print("\n=== CHECKING CORE FILES ===")
core_files = [
    'core/base_feature.py',
    'core/context.py',
    'core/registry.py',
    'core/orchestrator.py'
]
for cf in core_files:
    print(f"  {cf}: {'FOUND' if os.path.exists(cf) else 'MISSING'}")

print("\n=== CHECKING CONFIG FILES ===")
for cfg in ['config/registry.yaml', 'config/parliament_rules.yaml', 'config/connections.yaml']:
    print(f"  {cfg}: {'FOUND' if os.path.exists(cfg) else 'MISSING'}")

print("\n=== CHECKING FEATURE CATEGORIES ===")
feature_base = "features"
if os.path.exists(feature_base):
    for cat in sorted(os.listdir(feature_base)):
        cat_path = os.path.join(feature_base, cat)
        if os.path.isdir(cat_path):
            feats = [f for f in os.listdir(cat_path) if os.path.isdir(os.path.join(cat_path, f))]
            print(f"  {cat}: {len(feats)} features ({', '.join(feats[:3])}...)")
