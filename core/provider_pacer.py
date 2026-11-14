# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Provider Auto-Pacer: keeps batch jobs under each LLM provider's rate limit.
#
# Why: free/low tiers allow only N requests/minute per provider. A batch that fires
# dozens of calls at once gets HTTP 429 and loses votes (quorum collapse). The pacer
# spaces calls per provider host, honors Retry-After on 429, and retries instead of
# failing, so a batch of any size finishes slowly but completely.
#
# Scope: only active inside batch jobs (ContextVar `pacing_active`), so interactive
# /infer calls and unit tests are never delayed.
#
# Config (env):
#   PROVIDER_TIER=free|paid     default free. "paid" disables pacing entirely.
#   PACER_GEMINI_RPM            default 6   (half-speed safe margin; Gemini free limit is 15)
#   PACER_GROQ_RPM              default 12  (half-speed safe margin; Groq free limit is 30)
#   PACER_OPENROUTER_RPM        default 6   (half-speed safe margin; OpenRouter free limit is 20)
#   PACER_MAX_429_RETRIES       default 1
#   PACER_DAILY_WARN_GEMINI     default 1400 (free limit 1,500/day)
# ==============================================================================

import asyncio
import logging
import os
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

logger = logging.getLogger("CYPHER_LABEL_GUARD.Pacer")

pacing_active: ContextVar[bool] = ContextVar("pacing_active", default=False)

# host -> (env var name, default requests/minute)
_HOST_LIMITS = {
    "generativelanguage.googleapis.com": ("PACER_GEMINI_RPM", 6),
    "api.groq.com": ("PACER_GROQ_RPM", 12),
    "openrouter.ai": ("PACER_OPENROUTER_RPM", 6),
}


def pacing_enabled() -> bool:
    """Pacing is ON unless the operator declares paid-tier keys."""
    return os.getenv("PROVIDER_TIER", "free").strip().lower() != "paid"


def _rpm_for(host: str) -> int:
    spec = _HOST_LIMITS.get(host)
    if not spec:
        return 0  # unknown host -> never delayed
    try:
        return max(0, int(os.getenv(spec[0], str(spec[1]))))
    except ValueError:
        return spec[1]


class ProviderPacer:
    def __init__(self) -> None:
        self._next_slot: Dict[str, float] = {}
        self._host_cooldown_until: Dict[str, float] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._day: str = ""
        self._daily: Dict[str, int] = {}
        self.cooldown_until: float = 0.0  # any host currently cooling down after a 429
        self.rate_limit_hits: int = 0

    def _lock(self, host: str) -> asyncio.Lock:
        lock = self._locks.get(host)
        if lock is None:
            lock = self._locks[host] = asyncio.Lock()
        return lock

    def _count(self, host: str) -> None:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._day:
            self._day, self._daily = today, {}
        self._daily[host] = self._daily.get(host, 0) + 1
        warn_at = int(os.getenv("PACER_DAILY_WARN_GEMINI", "1400"))
        if host == "generativelanguage.googleapis.com" and self._daily[host] == warn_at:
            logger.warning("Gemini daily call count reached %d (free limit ~1,500/day).", warn_at)

    async def acquire(self, host: str) -> None:
        rpm = _rpm_for(host)
        if rpm <= 0:
            return
        interval = 60.0 / rpm
        async with self._lock(host):
            now = time.monotonic()
            slot = max(self._next_slot.get(host, 0.0), now)
            self._next_slot[host] = slot + interval
        wait = slot - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)
        self._count(host)

    def cooldown(self, host: str, seconds: float) -> None:
        """After a 429, push the whole host's schedule back so every waiter slows down."""
        until = time.monotonic() + seconds
        self._next_slot[host] = max(self._next_slot.get(host, 0.0), until)
        self._host_cooldown_until[host] = max(self._host_cooldown_until.get(host, 0.0), until)
        self.cooldown_until = max(self.cooldown_until, until)
        self.rate_limit_hits += 1

    def is_host_cooling_down(self, host: str) -> bool:
        if self.cooldown_until <= 0.0:
            return False
        return time.monotonic() < self._host_cooldown_until.get(host, 0.0)

    def in_cooldown(self) -> bool:
        return time.monotonic() < self.cooldown_until

    def stats(self) -> Dict[str, object]:
        return {
            "calls_today": dict(self._daily),
            "rate_limit_hits": self.rate_limit_hits,
            "in_cooldown": self.in_cooldown(),
        }


pacer = ProviderPacer()

_installed = False
_orig_send = httpx.AsyncClient.send


def _retry_after_seconds(resp: httpx.Response, attempt: int) -> float:
    raw = resp.headers.get("retry-after", "")
    try:
        return min(12.0, max(1.0, float(raw)))
    except ValueError:
        return min(8.0, 4.0 * (2 ** attempt))


async def _paced_send(self, request, *args, **kwargs):
    if not pacing_active.get():
        return await _orig_send(self, request, *args, **kwargs)

    host = request.url.host
    max_retries = int(os.getenv("PACER_MAX_429_RETRIES", "1"))
    resp: Optional[httpx.Response] = None
    for attempt in range(max_retries + 1):
        await pacer.acquire(host)
        resp = await _orig_send(self, request, *args, **kwargs)
        if resp.status_code != 429:
            return resp
        if attempt == max_retries:
            until = time.monotonic() + 20.0
            pacer._host_cooldown_until[host] = max(pacer._host_cooldown_until.get(host, 0.0), until)
            pacer.cooldown_until = max(pacer.cooldown_until, until)
            return resp
        delay = _retry_after_seconds(resp, attempt)
        logger.warning("429 from %s - cooling down %.0fs (retry %d/%d)", host, delay, attempt + 1, max_retries)
        pacer.cooldown(host, delay)
        await resp.aclose()
    return resp  # pragma: no cover


def install() -> None:
    """Idempotently wraps httpx.AsyncClient.send. Safe to call many times."""
    global _installed
    if _installed:
        return
    httpx.AsyncClient.send = _paced_send  # type: ignore[assignment]
    _installed = True


def activate_for_current_task() -> bool:
    """Call at the start of a batch job. Returns True if pacing is now active."""
    if not pacing_enabled():
        return False
    install()
    pacing_active.set(True)
    return True
