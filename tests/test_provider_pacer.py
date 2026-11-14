import asyncio
import os
import time
import unittest
from unittest import mock

import httpx

from core import provider_pacer as pp


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestProviderPacer(unittest.TestCase):
    def setUp(self):
        pp.install()
        pp.pacer._next_slot.clear()
        pp.pacer.rate_limit_hits = 0
        pp.pacer.cooldown_until = 0.0
        self._env = mock.patch.dict(os.environ, {"PACER_GEMINI_RPM": "600", "PROVIDER_TIER": "free"})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        pp.pacing_active.set(False)

    def test_not_active_outside_batch_means_no_delay(self):
        async def run():
            pp.pacing_active.set(False)
            calls = []

            def handler(req):
                calls.append(time.monotonic())
                return httpx.Response(200, json={})
            with mock.patch.dict(os.environ, {"PACER_GEMINI_RPM": "6"}):  # 10s interval if it were active
                async with _client(handler) as c:
                    t0 = time.monotonic()
                    for _ in range(3):
                        await c.post("https://generativelanguage.googleapis.com/x")
                    return time.monotonic() - t0
        self.assertLess(asyncio.run(run()), 1.0)

    def test_calls_are_spaced_when_active(self):
        async def run():
            pp.pacing_active.set(True)
            stamps = []

            def handler(req):
                stamps.append(time.monotonic())
                return httpx.Response(200, json={})
            with mock.patch.dict(os.environ, {"PACER_GEMINI_RPM": "120"}):  # 0.5s interval
                async with _client(handler) as c:
                    for _ in range(3):
                        await c.post("https://generativelanguage.googleapis.com/x")
            return stamps
        s = asyncio.run(run())
        self.assertGreaterEqual(s[1] - s[0], 0.45)
        self.assertGreaterEqual(s[2] - s[1], 0.45)

    def test_429_is_retried_then_succeeds(self):
        async def run():
            pp.pacing_active.set(True)
            state = {"n": 0}

            def handler(req):
                state["n"] += 1
                if state["n"] == 1:
                    return httpx.Response(429, headers={"retry-after": "1"})
                return httpx.Response(200, json={"ok": True})
            async with _client(handler) as c:
                r = await c.post("https://generativelanguage.googleapis.com/x")
            return r.status_code, state["n"]
        status, n = asyncio.run(run())
        self.assertEqual(status, 200)
        self.assertEqual(n, 2)
        self.assertEqual(pp.pacer.rate_limit_hits, 1)

    def test_persistent_429_is_returned_not_hidden(self):
        async def run():
            pp.pacing_active.set(True)
            with mock.patch.dict(os.environ, {"PACER_MAX_429_RETRIES": "1"}):
                def handler(req):
                    return httpx.Response(429, headers={"retry-after": "1"})
                async with _client(handler) as c:
                    r = await c.post("https://generativelanguage.googleapis.com/x")
            return r.status_code
        self.assertEqual(asyncio.run(run()), 429)  # honest failure, never faked as success

    def test_paid_tier_disables_pacing(self):
        with mock.patch.dict(os.environ, {"PROVIDER_TIER": "paid"}):
            self.assertFalse(pp.activate_for_current_task())
            self.assertFalse(pp.pacing_active.get())

    def test_unknown_host_never_delayed(self):
        async def run():
            pp.pacing_active.set(True)

            def handler(req):
                return httpx.Response(200, json={})
            async with _client(handler) as c:
                t0 = time.monotonic()
                for _ in range(5):
                    await c.post("https://example.com/x")
                return time.monotonic() - t0
        self.assertLess(asyncio.run(run()), 1.0)

    def test_host_cooldown_tracking_and_half_speed_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PACER_GEMINI_RPM", None)
            os.environ.pop("PACER_GROQ_RPM", None)
            os.environ.pop("PACER_OPENROUTER_RPM", None)
            self.assertEqual(pp._rpm_for("generativelanguage.googleapis.com"), 6)
            self.assertEqual(pp._rpm_for("api.groq.com"), 12)
            self.assertEqual(pp._rpm_for("openrouter.ai"), 6)
        self.assertFalse(pp.pacer.is_host_cooling_down("openrouter.ai"))
        pp.pacer.cooldown("openrouter.ai", 5.0)
        self.assertTrue(pp.pacer.is_host_cooling_down("openrouter.ai"))
        self.assertFalse(pp.pacer.is_host_cooling_down("api.groq.com"))


class TestProgressMessageIsTruthful(unittest.TestCase):
    def test_message_makes_no_false_verification_claims(self):
        from api.batch_images_routes import _progress_message
        s = {"status": "PROCESSING", "total": 100, "done": 11, "failed": 0}
        msg = _progress_message(s, elapsed=66.0)
        self.assertIn("12/100", msg)
        for banned in ("free", "zero-hallucination", "cross-exam", "deep multi-model", "forensic"):
            self.assertNotIn(banned, msg.lower())

    def test_eta_unknown_before_first_item(self):
        from api.batch_images_routes import _eta_seconds
        self.assertIsNone(_eta_seconds({"status": "PROCESSING", "total": 10, "done": 0}, 5.0))


if __name__ == "__main__":
    unittest.main()
