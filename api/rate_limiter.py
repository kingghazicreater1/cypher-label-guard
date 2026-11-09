# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# In-Memory Sliding-Window Rate Limiter
# Protects LLM inference, batch queues, and auth endpoints from abuse
# ==============================================================================

import os
import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import HTTPException, Request


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def _cleanup(self, now: float):
        if now - self._last_cleanup < 120:
            return
        stale_cutoff = now - self.window_seconds
        keys_to_delete = []
        for key, timestamps in list(self._history.items()):
            active = [t for t in timestamps if t > stale_cutoff]
            if active:
                self._history[key] = active
            else:
                keys_to_delete.append(key)
        for k in keys_to_delete:
            self._history.pop(k, None)
        self._last_cleanup = now

    def check(self, identifier: str, limit: Optional[int] = None, window: Optional[int] = None) -> bool:
        if os.getenv("DISABLE_RATE_LIMITER", "").lower() in ("1", "true", "yes"):
            return True

        now = time.time()
        self._cleanup(now)

        eff_limit = limit or self.max_requests
        eff_window = window or self.window_seconds
        cutoff = now - eff_window

        timestamps = [t for t in self._history[identifier] if t > cutoff]
        if len(timestamps) >= eff_limit:
            return False

        timestamps.append(now)
        self._history[identifier] = timestamps
        return True


# Global rate limiter instances
infer_limiter = SlidingWindowRateLimiter(max_requests=60, window_seconds=60)
batch_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)


def check_rate_limit(request: Request, limiter: SlidingWindowRateLimiter, user_id: Optional[str] = None):
    """FastAPI helper to throttle abusive clients based on IP or User ID."""
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (request.client.host if request.client else "unknown")
    identifier = f"user:{user_id}" if user_id else f"ip:{client_ip}"

    if not limiter.check(identifier):
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests: Rate limit exceeded. Please slow down your requests.",
            headers={"Retry-After": "60"},
        )
