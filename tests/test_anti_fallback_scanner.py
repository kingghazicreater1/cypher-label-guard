import os
import re
import unittest

class TestAntiFallbackScanner(unittest.TestCase):
    """
    CI Automated Guard against Hardcoded Confidence Fallbacks & Falsy Coercion.
    Scans entire backend (api, core, features, db) and frontend (frontend/src)
    to ensure:
    1. Zero '?? 9X.X' or '|| 9X.X' in frontend.
    2. Zero 'or 9X.X' or 'else 9X.X' in backend.
    3. Zero '98.4' occurrences in production codebase.
    """

    def setUp(self):
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def test_no_falsy_fallbacks_in_frontend(self):
        frontend_src = os.path.join(self.root_dir, "frontend", "src")
        # Matches '?? 90', '?? 98.4', '|| 92.3', etc.
        pattern = re.compile(r'(\?\?|\|\|)\s*9[0-9](\.[0-9]+)?')
        violations = []

        for root, _, files in os.walk(frontend_src):
            for f in files:
                if f.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    path = os.path.join(root, f)
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                        for line_no, line in enumerate(fh, 1):
                            # Skip comments
                            stripped = line.strip()
                            if stripped.startswith('//') or stripped.startswith('*'):
                                continue
                            if pattern.search(line):
                                violations.append(f"{os.path.relpath(path, self.root_dir)}:{line_no}: {stripped}")

        self.assertEqual(
            len(violations),
            0,
            f"Found forbidden falsy confidence fallbacks in frontend:\n" + "\n".join(violations)
        )

    def test_no_falsy_or_else_fallbacks_in_backend(self):
        backend_dirs = ["api", "core", "features", "db"]
        # Matches 'or 9X', 'else 9X.X', 'return 9X.X', 'default=9X.X'
        pattern = re.compile(r'\b(or|else|return)\s+9[0-9](\.[0-9]+)?\b|default\s*=\s*9[0-9](\.[0-9]+)?')
        violations = []

        for b_dir in backend_dirs:
            full_dir = os.path.join(self.root_dir, b_dir)
            if not os.path.exists(full_dir):
                continue
            for root, _, files in os.walk(full_dir):
                for f in files:
                    if f.endswith('.py'):
                        path = os.path.join(root, f)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                            for line_no, line in enumerate(fh, 1):
                                stripped = line.strip()
                                if stripped.startswith('#'):
                                    continue
                                if pattern.search(line):
                                    violations.append(f"{os.path.relpath(path, self.root_dir)}:{line_no}: {stripped}")

        self.assertEqual(
            len(violations),
            0,
            f"Found forbidden hardcoded confidence fallbacks in backend (or/else/return/default=9X):\n" + "\n".join(violations)
        )

    def test_no_hardcoded_98_4_in_production(self):
        scan_dirs = ["api", "core", "features", "db", os.path.join("frontend", "src")]
        pattern = re.compile(r'98\.4')
        violations = []

        for d in scan_dirs:
            full_dir = os.path.join(self.root_dir, d)
            if not os.path.exists(full_dir):
                continue
            for root, _, files in os.walk(full_dir):
                for f in files:
                    if f.endswith(('.py', '.ts', '.tsx', '.js', '.jsx')):
                        path = os.path.join(root, f)
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
                            for line_no, line in enumerate(fh, 1):
                                stripped = line.strip()
                                if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*'):
                                    continue
                                if pattern.search(line):
                                    violations.append(f"{os.path.relpath(path, self.root_dir)}:{line_no}: {stripped}")

        self.assertEqual(
            len(violations),
            0,
            f"Found forbidden 98.4 hardcoding in production source:\n" + "\n".join(violations)
        )

if __name__ == "__main__":
    unittest.main()
