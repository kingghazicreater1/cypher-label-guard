"""Test package bootstrap.

Most legacy suites call /api/v2/infer without credentials. Production now requires login and
only honours the explicit ALLOW_GUEST_INFERENCE flag (no more sys.modules sniffing), so the
test package opts in here. Suites that verify auth enforcement clear the flag themselves.
"""
import os

os.environ.setdefault("ALLOW_GUEST_INFERENCE", "true")
