import sys, os
sys.path.insert(0, os.path.abspath("."))
from api.server import app

print("All App Routes:")
for r in app.routes:
    path = getattr(r, "path", None)
    methods = getattr(r, "methods", None)
    if path:
        print(f"  {methods or 'WS'} -> {path}")
