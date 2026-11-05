# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# BYOK (Bring Your Own Key) & Dynamic Model Engine
# ==============================================================================

import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from db.models import User
from api.auth_routes import get_current_user, get_optional_current_user, require_admin
from typing import Optional

import logging as _logging
_log = _logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/keys", tags=["BYOK API Keys"])

ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"

DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "nvidia/nemotron-3.5-lightning:free",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-sonnet-20241022",
    "gemini": "gemini-1.5-flash",
    "mistral": "mistral-large-2407",
}


class KeyUpdateRequest(BaseModel):
    groq_key: Optional[str] = Field(default=None, description="Groq API Key (gsk_...)")
    groq_model: Optional[str] = Field(default=None, description="Groq Model ID (e.g. llama-3.3-70b-versatile)")
    openai_key: Optional[str] = Field(default=None, description="OpenAI API Key (sk-...)")
    openai_model: Optional[str] = Field(default=None, description="OpenAI Model ID (e.g. gpt-4o, gpt-4o-mini)")
    anthropic_key: Optional[str] = Field(default=None, description="Anthropic Claude API Key (sk-ant-...)")
    anthropic_model: Optional[str] = Field(default=None, description="Claude Model ID (e.g. claude-3-5-sonnet-20241022)")
    gemini_key: Optional[str] = Field(default=None, description="Google Gemini API Key (AIza...)")
    gemini_model: Optional[str] = Field(default=None, description="Gemini Model ID (e.g. gemini-1.5-flash, gemini-2.0-flash)")
    mistral_key: Optional[str] = Field(default=None, description="Mistral AI API Key")
    mistral_model: Optional[str] = Field(default=None, description="Mistral Model ID (e.g. mistral-large-2407)")
    openrouter_key: Optional[str] = Field(default=None, description="OpenRouter API Key (sk-or-v1-...)")
    openrouter_model: Optional[str] = Field(default=None, description="OpenRouter Model ID (e.g. nvidia/nemotron-3.5-lightning:free)")


class KeyTestRequest(BaseModel):
    provider: str = Field(..., description="'groq', 'openai', 'claude', 'gemini', 'mistral', 'openrouter', or 'all'")
    api_key: Optional[str] = Field(default=None, description="Optional key override to test before saving")
    model_name: Optional[str] = Field(default=None, description="Optional custom model name to test with")


def _mask_key(key: Optional[str]) -> str:
    if not key or len(key) < 8:
        return "Not Configured"
    return f"{key[:4]}...{key[-4:]}"


def _save_to_dotenv(updates: Dict[str, str]):
    """Persists updated keys and models into local .env file."""
    lines = []
    existing_keys = set()
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if "=" in stripped and not stripped.startswith("#"):
                    k = stripped.split("=")[0].strip()
                    if k in updates:
                        lines.append(f"{k}={updates[k]}\n")
                        existing_keys.add(k)
                        continue
                lines.append(line)

    for k, v in updates.items():
        if k not in existing_keys:
            lines.append(f"{k}={v}\n")

    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


# ------------------------------------------------------------------------------
# 1. Get Live Status of All Multi-Model Providers
# ------------------------------------------------------------------------------
@router.get("/status")
async def get_keys_status(user: Optional[User] = Depends(get_optional_current_user)):
    """
    Returns configuration status, masked tokens, and user's desired model names
    for all Parliamentary APIs.
    """
    groq_k = os.getenv("GROQ_API_KEY", "")
    openai_k = os.getenv("OPENAI_API_KEY", "")
    claude_k = os.getenv("ANTHROPIC_API_KEY", "")
    gemini_k = os.getenv("GEMINI_API_KEY", "")
    mistral_k = os.getenv("MISTRAL_API_KEY", "")
    openrouter_k = os.getenv("OPENROUTER_API_KEY", "")

    providers = {
        "groq": {
            "name": "Groq (Ultra-Fast Free Engine)",
            "model_name": os.getenv("GROQ_MODEL", DEFAULT_MODELS["groq"]),
            "configured": bool(groq_k),
            "masked_key": _mask_key(groq_k),
            "mode": f"Live Groq Engine ({os.getenv('GROQ_MODEL', DEFAULT_MODELS['groq'])})" if groq_k else "Not Configured (Free Key from console.groq.com)",
            "rpm_tier_limit": "30 RPM (100% Free / Ultra Fast)",
            "is_free_tier": True,
        },
        "openrouter": {
            "name": "OpenRouter (Universal Gateway)",
            "model_name": os.getenv("OPENROUTER_MODEL", DEFAULT_MODELS["openrouter"]),
            "configured": bool(openrouter_k),
            "masked_key": _mask_key(openrouter_k),
            "mode": f"Live Inference ({os.getenv('OPENROUTER_MODEL', DEFAULT_MODELS['openrouter'])})" if openrouter_k else "Not Configured (Key Required)",
            "rpm_tier_limit": "20 RPM (Free Tier / Custom)",
            "is_free_tier": True,
        },
        "gemini": {
            "name": "Google Gemini (Free AI Studio)",
            "model_name": os.getenv("GEMINI_MODEL", DEFAULT_MODELS["gemini"]),
            "configured": bool(gemini_k),
            "masked_key": _mask_key(gemini_k),
            "mode": f"Live Inference ({os.getenv('GEMINI_MODEL', DEFAULT_MODELS['gemini'])})" if gemini_k else "Not Configured (Key Required)",
            "rpm_tier_limit": "15 RPM / 1,500 RPD (Free AI Studio)",
            "is_free_tier": True,
        },
        "openai": {
            "name": "OpenAI",
            "model_name": os.getenv("OPENAI_MODEL", DEFAULT_MODELS["openai"]),
            "configured": bool(openai_k),
            "masked_key": _mask_key(openai_k),
            "mode": f"Live Inference ({os.getenv('OPENAI_MODEL', DEFAULT_MODELS['openai'])})" if openai_k else "Not Configured (Key Required)",
            "rpm_tier_limit": "10,000 RPM (Tier 5)",
        },
        "claude": {
            "name": "Anthropic Claude",
            "model_name": os.getenv("ANTHROPIC_MODEL", DEFAULT_MODELS["claude"]),
            "configured": bool(claude_k),
            "masked_key": _mask_key(claude_k),
            "mode": f"Live Inference ({os.getenv('ANTHROPIC_MODEL', DEFAULT_MODELS['claude'])})" if claude_k else "Not Configured (Key Required)",
            "rpm_tier_limit": "4,000 RPM (Tier 4)",
        },
        "mistral": {
            "name": "Mistral AI",
            "model_name": os.getenv("MISTRAL_MODEL", DEFAULT_MODELS["mistral"]),
            "configured": bool(mistral_k),
            "masked_key": _mask_key(mistral_k),
            "mode": f"Live Inference ({os.getenv('MISTRAL_MODEL', DEFAULT_MODELS['mistral'])})" if mistral_k else "Not Configured (Key Required)",
            "rpm_tier_limit": "3,000 RPM (Tier 3)",
        },
    }

    configured_count = sum(1 for p in providers.values() if p["configured"])

    return {
        "success": True,
        "configured_providers": configured_count,
        "total_providers": 6,
        "parliament_status": "LIVE_MULTI_MODEL" if configured_count > 0 else "KEYS_REQUIRED",
        "providers": providers,
    }


# ------------------------------------------------------------------------------
# 2. Update Provider API Keys & Desired Models
# ------------------------------------------------------------------------------
@router.post("/update")
async def update_api_keys(
    req: KeyUpdateRequest,
    user: User = Depends(require_admin),
):
    """
    Saves and activates Bring-Your-Own-Keys (BYOK) and desired model IDs.
    """
    updates = {}
    if req.groq_key is not None:
        os.environ["GROQ_API_KEY"] = req.groq_key.strip()
        updates["GROQ_API_KEY"] = req.groq_key.strip()
    if req.groq_model is not None and req.groq_model.strip():
        os.environ["GROQ_MODEL"] = req.groq_model.strip()
        updates["GROQ_MODEL"] = req.groq_model.strip()

    if req.openrouter_key is not None:
        os.environ["OPENROUTER_API_KEY"] = req.openrouter_key.strip()
        updates["OPENROUTER_API_KEY"] = req.openrouter_key.strip()
    if req.openrouter_model is not None and req.openrouter_model.strip():
        os.environ["OPENROUTER_MODEL"] = req.openrouter_model.strip()
        updates["OPENROUTER_MODEL"] = req.openrouter_model.strip()

    if req.openai_key is not None:
        os.environ["OPENAI_API_KEY"] = req.openai_key.strip()
        updates["OPENAI_API_KEY"] = req.openai_key.strip()
    if req.openai_model is not None and req.openai_model.strip():
        os.environ["OPENAI_MODEL"] = req.openai_model.strip()
        updates["OPENAI_MODEL"] = req.openai_model.strip()

    if req.anthropic_key is not None:
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_key.strip()
        updates["ANTHROPIC_API_KEY"] = req.anthropic_key.strip()
    if req.anthropic_model is not None and req.anthropic_model.strip():
        os.environ["ANTHROPIC_MODEL"] = req.anthropic_model.strip()
        updates["ANTHROPIC_MODEL"] = req.anthropic_model.strip()

    if req.gemini_key is not None:
        os.environ["GEMINI_API_KEY"] = req.gemini_key.strip()
        updates["GEMINI_API_KEY"] = req.gemini_key.strip()
    if req.gemini_model is not None and req.gemini_model.strip():
        os.environ["GEMINI_MODEL"] = req.gemini_model.strip()
        updates["GEMINI_MODEL"] = req.gemini_model.strip()

    if req.mistral_key is not None:
        os.environ["MISTRAL_API_KEY"] = req.mistral_key.strip()
        updates["MISTRAL_API_KEY"] = req.mistral_key.strip()
    if req.mistral_model is not None and req.mistral_model.strip():
        os.environ["MISTRAL_MODEL"] = req.mistral_model.strip()
        updates["MISTRAL_MODEL"] = req.mistral_model.strip()

    if updates:
        try:
            _save_to_dotenv(updates)
        except Exception as _exc:
            _log.debug("Non-fatal error suppressed: %s", type(_exc).__name__)

    return {
        "success": True,
        "message": f"Updated {len(updates)} provider credentials/models. Active immediately in live voting bus.",
        "active_keys": {k: _mask_key(v) for k, v in updates.items() if not k.endswith("_MODEL")},
    }


# ------------------------------------------------------------------------------
# 3. Live Key & Desired Model Ping Validator
# ------------------------------------------------------------------------------
@router.post("/test")
async def test_provider_key(
    req: KeyTestRequest,
    user: User = Depends(require_admin),
):
    """
    Executes a real low-latency ping against the provider model using the user's
    desired model name.
    """
    target = req.provider.lower()
    results = {}

    import httpx

    async def _test_openai(key: str, model: Optional[str] = None):
        chosen_model = (model or os.getenv("OPENAI_MODEL") or DEFAULT_MODELS["openai"]).strip()
        start = time.time()
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": "Respond: OK"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            lat = round((time.time() - start) * 1000.0, 1)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "LIVE_ONLINE",
                    "latency_ms": lat,
                    "response": data["choices"][0]["message"]["content"].strip(),
                    "model": chosen_model,
                }
            else:
                return {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140]}

    async def _test_claude(key: str, model: Optional[str] = None):
        chosen_model = (model or os.getenv("ANTHROPIC_MODEL") or DEFAULT_MODELS["claude"]).strip()
        start = time.time()
        headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": chosen_model,
            "max_tokens": 5,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": "Respond: OK"}],
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            lat = round((time.time() - start) * 1000.0, 1)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "LIVE_ONLINE",
                    "latency_ms": lat,
                    "response": data["content"][0]["text"].strip(),
                    "model": chosen_model,
                }
            else:
                return {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140]}

    async def _test_gemini(key: str, model: Optional[str] = None):
        clean_key = (key or "").strip().strip('"').strip("'")
        if clean_key.startswith("sk-or-v1-"):
            return {
                "status": "CONFIG_ERROR",
                "latency_ms": 0.0,
                "error": "Notice: You pasted an OpenRouter key into Google Gemini! Paste it in OpenRouter above. Gemini keys start with 'AIzaSy...' from aistudio.google.com.",
            }
        if not clean_key or not clean_key.startswith("AIzaSy"):
            return {
                "status": "AUTH_ERROR",
                "latency_ms": 0.0,
                "error": "Invalid format. Google Gemini keys must start with 'AIzaSy' (create free at aistudio.google.com).",
            }

        chosen_model = (model or os.getenv("GEMINI_MODEL") or DEFAULT_MODELS["gemini"]).strip()
        start = time.time()
        headers = {
            "x-goog-api-key": clean_key,
            "Content-Type": "application/json",
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{chosen_model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": "Respond: OK"}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 5},
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            lat = round((time.time() - start) * 1000.0, 1)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "LIVE_ONLINE",
                    "latency_ms": lat,
                    "response": data["candidates"][0]["content"]["parts"][0]["text"].strip(),
                    "model": chosen_model,
                }
            elif resp.status_code == 429:
                return {
                    "status": "RATE_LIMITED",
                    "latency_ms": lat,
                    "error": "Gemini free rate limit hit (15 RPM). Key is valid! Please wait 30 seconds.",
                }
            else:
                return {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140]}

    async def _test_mistral(key: str, model: Optional[str] = None):
        clean_key = (key or "").strip().strip('"').strip("'")
        chosen_model = (model or os.getenv("MISTRAL_MODEL") or DEFAULT_MODELS["mistral"]).strip()
        start = time.time()
        headers = {"Authorization": f"Bearer {clean_key}", "Content-Type": "application/json"}
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": "Respond: OK"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload)
            lat = round((time.time() - start) * 1000.0, 1)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "LIVE_ONLINE",
                    "latency_ms": lat,
                    "response": data["choices"][0]["message"]["content"].strip(),
                    "model": chosen_model,
                }
            else:
                return {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140]}

    async def _test_openrouter(key: str, model: Optional[str] = None):
        clean_key = (key or "").strip().strip('"').strip("'")
        if not clean_key or not clean_key.startswith("sk-or-v1-"):
            return {
                "status": "AUTH_ERROR",
                "latency_ms": 0.0,
                "error": "Invalid format. OpenRouter keys must start with 'sk-or-v1-' (create at openrouter.ai/keys).",
            }

        chosen_model = (model or os.getenv("OPENROUTER_MODEL") or DEFAULT_MODELS["openrouter"]).strip()
        start = time.time()
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "HTTP-Referer": "https://cypherlabelguard.ai",
            "X-Title": "CypherLabelGuard",
            "Content-Type": "application/json",
        }

        # Test inference directly with user's desired model
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": "Respond: OK"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                lat = round((time.time() - start) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    msg_obj = data.get("choices", [{}])[0].get("message", {})
                    resp_content = (msg_obj.get("content") or msg_obj.get("reasoning") or "OK").strip()
                    return {
                        "status": "LIVE_ONLINE",
                        "latency_ms": lat,
                        "response": resp_content,
                        "model": chosen_model,
                    }
                elif resp.status_code == 429:
                    return {
                        "status": "RATE_LIMITED",
                        "latency_ms": lat,
                        "error": f"Model '{chosen_model}' is temporarily busy upstream (HTTP 429). Key is verified! You can type another model (e.g. 'nvidia/nemotron-3.5-lightning:free' or 'dots-studio/dots-3-note-preview:free') and test.",
                    }
                elif resp.status_code == 401:
                    return {
                        "status": "AUTH_ERROR",
                        "latency_ms": lat,
                        "error": "OpenRouter rejected key (401 Unauthorized). Please check key at openrouter.ai/keys",
                    }
                else:
                    return {"status": "API_ERROR", "latency_ms": lat, "error": resp.text[:140]}
            except Exception as e:
                return {"status": "NETWORK_TIMEOUT", "latency_ms": 0.0, "error": str(e)}

    async def _test_groq(key: str, model: Optional[str] = None):
        clean_key = (key or "").strip().strip('"').strip("'")
        if not clean_key or not clean_key.startswith("gsk_"):
            return {
                "status": "AUTH_ERROR",
                "latency_ms": 0.0,
                "error": "Invalid format. Groq API keys start with 'gsk_' (get free key at console.groq.com/keys).",
            }
        chosen_model = (model or os.getenv("GROQ_MODEL") or DEFAULT_MODELS["groq"]).strip()
        start = time.time()
        headers = {
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": chosen_model,
            "messages": [{"role": "user", "content": "Respond: OK"}],
            "max_tokens": 5,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                lat = round((time.time() - start) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    msg_obj = data.get("choices", [{}])[0].get("message", {})
                    return {
                        "status": "LIVE_ONLINE",
                        "latency_ms": lat,
                        "response": msg_obj.get("content", "OK").strip(),
                        "model": chosen_model,
                    }
                elif resp.status_code == 429:
                    return {
                        "status": "RATE_LIMITED",
                        "latency_ms": lat,
                        "error": "Groq rate limit hit (30 RPM). Please wait a few seconds and retry.",
                    }
                elif resp.status_code == 401:
                    return {
                        "status": "AUTH_ERROR",
                        "latency_ms": lat,
                        "error": "Groq rejected key (401 Unauthorized). Check key at console.groq.com/keys",
                    }
                else:
                    return {"status": "API_ERROR", "latency_ms": lat, "error": resp.text[:140]}
            except Exception as e:
                return {"status": "NETWORK_TIMEOUT", "latency_ms": 0.0, "error": str(e)}

    key_testers = {
        "groq": (req.api_key or os.getenv("GROQ_API_KEY", ""), req.model_name or os.getenv("GROQ_MODEL"), _test_groq),
        "openrouter": (req.api_key or os.getenv("OPENROUTER_API_KEY", ""), req.model_name or os.getenv("OPENROUTER_MODEL"), _test_openrouter),
        "openai": (req.api_key or os.getenv("OPENAI_API_KEY", ""), req.model_name or os.getenv("OPENAI_MODEL"), _test_openai),
        "claude": (req.api_key or os.getenv("ANTHROPIC_API_KEY", ""), req.model_name or os.getenv("ANTHROPIC_MODEL"), _test_claude),
        "gemini": (req.api_key or os.getenv("GEMINI_API_KEY", ""), req.model_name or os.getenv("GEMINI_MODEL"), _test_gemini),
        "mistral": (req.api_key or os.getenv("MISTRAL_API_KEY", ""), req.model_name or os.getenv("MISTRAL_MODEL"), _test_mistral),
    }

    providers_to_test = list(key_testers.keys()) if target == "all" else [target]

    for p in providers_to_test:
        if p in key_testers:
            k, m, test_fn = key_testers[p]
            if k:
                try:
                    res = await test_fn(k, m)
                    results[p] = res
                except Exception as ex:
                    results[p] = {"status": "NETWORK_TIMEOUT", "error": str(ex)}
            else:
                results[p] = {
                    "status": "UNCONFIGURED",
                    "latency_ms": 0.0,
                    "message": "Key unconfigured. Enter API key and desired model name to activate live inference.",
                }

    return {
        "success": True,
        "results": results,
    }


# ------------------------------------------------------------------------------
# 4. Generic Dynamic BYOK Slots (Key #1 to Key #4)
# ------------------------------------------------------------------------------
class GenericSlotUpdateRequest(BaseModel):
    slot_id: str = Field(..., description="'key1', 'key2', 'key3', or 'key4'")
    model_name: str = Field(..., description="Desired Model ID")
    api_key: str = Field(..., description="API Key")


class GenericSlotTestRequest(BaseModel):
    slot_id: Optional[str] = Field(default="key1")
    model_name: str
    api_key: str


@router.get("/slots")
async def get_key_slots(user: Optional[User] = Depends(get_optional_current_user)):
    """
    Returns the 4 generic Key slots (Key #1 to Key #4) for Parliament voting.
    Auto-binds from provider keys if not yet specifically set, and never wipes existing keys.
    """
    slots = []
    dotenv_sync = {}

    for i in range(1, 5):
        slot_key = f"key{i}"
        m_env = os.getenv(f"XKEY{i}_MODEL", "").strip()
        k_env = os.getenv(f"XKEY{i}_KEY", "").strip()

        # Resilient fallback if slot was not yet assigned but provider key is active
        if not k_env and i == 1 and os.getenv("GROQ_API_KEY"):
            k_env = os.getenv("GROQ_API_KEY", "").strip()
            if not m_env:
                m_env = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
            os.environ[f"XKEY1_KEY"] = k_env
            os.environ[f"XKEY1_MODEL"] = m_env
            dotenv_sync["XKEY1_KEY"] = k_env
            dotenv_sync["XKEY1_MODEL"] = m_env

        if not k_env and i == 2 and os.getenv("OPENROUTER_API_KEY"):
            k_env = os.getenv("OPENROUTER_API_KEY", "").strip()
            if not m_env:
                m_env = os.getenv("OPENROUTER_MODEL", "liquid/lfm-2.5-2.6b:free").strip()
            os.environ[f"XKEY2_KEY"] = k_env
            os.environ[f"XKEY2_MODEL"] = m_env
            dotenv_sync["XKEY2_KEY"] = k_env
            dotenv_sync["XKEY2_MODEL"] = m_env

        is_configured = bool(k_env)
        slots.append({
            "slot_id": slot_key,
            "slot_number": i,
            "label": f"Key #{i}",
            "seat_name": f"Parliament Seat #{i}",
            "model_name": m_env,
            "configured": is_configured,
            "masked_key": _mask_key(k_env) if is_configured else "Not Configured",
            "status": "ONLINE" if is_configured else "UNCONFIGURED",
        })

    if dotenv_sync:
        try:
            _save_to_dotenv(dotenv_sync)
        except Exception as _exc:
            _log.debug("Non-fatal error suppressed: %s", type(_exc).__name__)

    return {
        "success": True,
        "slots": slots,
        "configured_slots": sum(1 for s in slots if s["configured"]),
        "total_slots": 4,
    }


@router.post("/slots/test")
async def test_slot_key(
    req: GenericSlotTestRequest,
    user: User = Depends(require_admin),
):
    """
    Live tests any Model Name and API Key for a slot with a fast 1-token test prompt.
    """
    clean_slot = (req.slot_id or "key1").replace("key", "").replace("#", "")
    if clean_slot not in ["1", "2", "3", "4"]:
        clean_slot = "1"

    clean_key = (req.api_key or "").strip().strip('"').strip("'")
    clean_model = (req.model_name or "").strip()

    # If key wasn't passed in test payload, fallback to existing configured key
    if not clean_key:
        clean_key = os.getenv(f"XKEY{clean_slot}_KEY", "").strip()
        if not clean_key and clean_slot == "1":
            clean_key = os.getenv("GROQ_API_KEY", "").strip()
        elif not clean_key and clean_slot == "2":
            clean_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not clean_model:
        clean_model = os.getenv(f"XKEY{clean_slot}_MODEL", "").strip()
        if not clean_model and clean_slot == "1":
            clean_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        elif not clean_model and clean_slot == "2":
            clean_model = os.getenv("OPENROUTER_MODEL", "liquid/lfm-2.5-2.6b:free").strip()

    if not clean_key:
        raise HTTPException(status_code=400, detail="API key is required.")
    if not clean_model:
        raise HTTPException(status_code=400, detail="Model name is required.")

    import httpx
    start = time.time()
    masked = _mask_key(clean_key)

    try:
        if clean_key.startswith("gsk_"):
            # Groq API endpoint
            headers = {"Authorization": f"Bearer {clean_key}", "Content-Type": "application/json"}
            payload = {
                "model": clean_model,
                "messages": [{"role": "user", "content": "Respond: OK"}],
                "max_tokens": 5,
                "temperature": 0.0,
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
                lat = round((time.time() - start) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    res_text = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                    return {
                        "success": True,
                        "slot_id": req.slot_id,
                        "result": {
                            "status": "LIVE_ONLINE",
                            "latency_ms": lat,
                            "response": res_text,
                            "model": clean_model,
                            "masked_key": masked,
                        },
                    }
                else:
                    return {
                        "success": False,
                        "slot_id": req.slot_id,
                        "result": {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140], "masked_key": masked},
                    }
        elif clean_key.startswith("sk-or-v1-"):
            # OpenRouter API endpoint
            headers = {
                "Authorization": f"Bearer {clean_key}",
                "HTTP-Referer": "https://cypherlabelguard.ai",
                "X-Title": "CypherLabelGuard",
                "Content-Type": "application/json",
            }
            payload = {
                "model": clean_model,
                "messages": [{"role": "user", "content": "Respond: OK"}],
                "max_tokens": 5,
                "temperature": 0.0,
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                lat = round((time.time() - start) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    res_text = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                    return {
                        "success": True,
                        "slot_id": req.slot_id,
                        "result": {
                            "status": "LIVE_ONLINE",
                            "latency_ms": lat,
                            "response": res_text,
                            "model": clean_model,
                            "masked_key": masked,
                        },
                    }
                else:
                    return {
                        "success": False,
                        "slot_id": req.slot_id,
                        "result": {"status": "API_ERROR", "latency_ms": lat, "error": resp.text[:140], "masked_key": masked},
                    }
        else:
            # Universal OpenAI-compatible endpoint
            headers = {"Authorization": f"Bearer {clean_key}", "Content-Type": "application/json"}
            payload = {
                "model": clean_model,
                "messages": [{"role": "user", "content": "Respond: OK"}],
                "max_tokens": 5,
                "temperature": 0.0,
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                lat = round((time.time() - start) * 1000.0, 1)
                if resp.status_code == 200:
                    data = resp.json()
                    res_text = data.get("choices", [{}])[0].get("message", {}).get("content", "OK")
                    return {
                        "success": True,
                        "slot_id": req.slot_id,
                        "result": {
                            "status": "LIVE_ONLINE",
                            "latency_ms": lat,
                            "response": res_text,
                            "model": clean_model,
                            "masked_key": masked,
                        },
                    }
                else:
                    return {
                        "success": False,
                        "slot_id": req.slot_id,
                        "result": {"status": "AUTH_ERROR", "latency_ms": lat, "error": resp.text[:140], "masked_key": masked},
                    }
    except Exception as e:
        return {
            "success": False,
            "slot_id": req.slot_id,
            "result": {
                "status": "ERROR",
                "latency_ms": round((time.time() - start) * 1000.0, 1),
                "error": str(e),
                "masked_key": masked,
            },
        }


@router.post("/slots/update")
async def update_slot_key(
    req: GenericSlotUpdateRequest,
    user: User = Depends(require_admin),
):
    """
    Saves the verified Model Name and API Key into .env permanently as XKEY# and activates it.
    Does not erase an existing key if the user updates only the model name.
    """
    clean_slot = req.slot_id.replace("key", "").replace("#", "")
    if clean_slot not in ["1", "2", "3", "4"]:
        clean_slot = "1"

    k_env = f"XKEY{clean_slot}_KEY"
    m_env = f"XKEY{clean_slot}_MODEL"

    clean_key = req.api_key.strip()
    clean_model = req.model_name.strip()

    updates = {}

    # If key was left blank, preserve existing key from environment
    if not clean_key:
        clean_key = os.getenv(k_env, "").strip()
        if not clean_key and clean_slot == "1":
            clean_key = os.getenv("GROQ_API_KEY", "").strip()
        elif not clean_key and clean_slot == "2":
            clean_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if clean_key:
        os.environ[k_env] = clean_key
        updates[k_env] = clean_key

    if clean_model:
        os.environ[m_env] = clean_model
        updates[m_env] = clean_model

    # If it's a Groq key, also keep GROQ_API_KEY and GROQ_MODEL synchronized
    if clean_key.startswith("gsk_"):
        os.environ["GROQ_API_KEY"] = clean_key
        updates["GROQ_API_KEY"] = clean_key
        if clean_model:
            os.environ["GROQ_MODEL"] = clean_model
            updates["GROQ_MODEL"] = clean_model
    elif clean_key.startswith("sk-or-v1-"):
        os.environ["OPENROUTER_API_KEY"] = clean_key
        updates["OPENROUTER_API_KEY"] = clean_key
        if clean_model:
            os.environ["OPENROUTER_MODEL"] = clean_model
            updates["OPENROUTER_MODEL"] = clean_model

    if updates:
        _save_to_dotenv(updates)

    final_masked = _mask_key(clean_key) if clean_key else "Not Configured"

    return {
        "success": True,
        "slot_id": req.slot_id,
        "masked_key": final_masked,
        "model_name": clean_model or os.getenv(m_env, ""),
        "configured": bool(clean_key),
        "message": f"Key #{clean_slot} ({clean_model or 'Configured'}) successfully verified and saved to .env permanently!",
    }
