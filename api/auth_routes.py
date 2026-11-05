# ==============================================================================
# CypherLabelGuard: Authentication (Clerk-only, signature-verified)
#
# Needs: pip install "pyjwt[crypto]"
# Env:
#   CLERK_SECRET_KEY          sk_live_... / sk_test_...  (used to read the user's verified email)
#   CLERK_ISSUER              e.g. https://your-app.clerk.accounts.dev
#                             (optional: derived from VITE_CLERK_PUBLISHABLE_KEY / CLERK_PUBLISHABLE_KEY)
#   CLERK_AUTHORIZED_PARTIES  optional, comma list of your site origins (checks the `azp` claim)
#   ADMIN_EMAILS              comma list of verified emails that become Administrator
#   FREE_SIGNUP_CREDITS       default 500
#
# Removed on purpose: /signup, /login, /google, /phone/*, /commander-unlock and the
# app-issued HS256 tokens. Every request is authenticated ONLY by a Clerk session
# token whose RS256 signature, issuer and expiry are verified against Clerk's JWKS.
# Fail-closed: if Clerk is not configured on the server, nobody is authenticated.
# ==============================================================================
import base64
import json
import logging
import os
import threading
import time
import urllib.request
from typing import Any, Dict, Optional, Tuple

import jwt
from jwt import PyJWKClient
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import AuditLogEntry, User

logger = logging.getLogger("CYPHER_LABEL_GUARD.Auth")

router = APIRouter(prefix="/api/v2/auth", tags=["Authentication & User Management"])


# ------------------------------------------------------------------------------
# Configuration (read lazily so .env loading order and tests never matter)
# ------------------------------------------------------------------------------
def _clerk_secret() -> str:
    return os.getenv("CLERK_SECRET_KEY", "").strip()


def _free_credits() -> int:
    try:
        return int(os.getenv("FREE_SIGNUP_CREDITS", "500"))
    except ValueError:
        return 500


def _admin_emails() -> set:
    return {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}


def _authorized_parties() -> set:
    return {p.strip() for p in os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(",") if p.strip()}


def _issuer() -> Optional[str]:
    explicit = os.getenv("CLERK_ISSUER", "").strip().rstrip("/")
    if explicit:
        return explicit
    pk = os.getenv("CLERK_PUBLISHABLE_KEY") or os.getenv("VITE_CLERK_PUBLISHABLE_KEY") or ""
    parts = pk.split("_", 2)  # pk_test_<base64(domain$)>
    if len(parts) == 3 and parts[2]:
        try:
            raw = parts[2] + "=" * (-len(parts[2]) % 4)
            domain = base64.b64decode(raw).decode("utf-8").rstrip("$")
            if domain and "." in domain:
                return f"https://{domain}"
        except Exception:
            return None
    return None


_jwk_clients: Dict[str, PyJWKClient] = {}
_jwk_lock = threading.Lock()


def _jwk_client(issuer: str) -> PyJWKClient:
    with _jwk_lock:
        client = _jwk_clients.get(issuer)
        if client is None:
            client = PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_keys=True, lifespan=3600)
            _jwk_clients[issuer] = client
        return client


def _verify_clerk_jwt(token: str) -> Dict[str, Any]:
    """Verifies signature (RS256 via Clerk JWKS), issuer and expiry. Raises HTTPException on any failure."""
    issuer = _issuer()
    if not issuer:
        # Fail closed: without Clerk configured nobody is authenticated.
        raise HTTPException(status_code=503, detail="Authentication is not configured on the server.")
    try:
        signing_key = _jwk_client(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],  # never accept HS256 / none
            issuer=issuer,
            leeway=10,
            options={"require": ["exp", "iat", "sub", "iss"], "verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session token. Please sign in.")

    azp = claims.get("azp")
    parties = _authorized_parties()
    if parties and azp and azp not in parties:
        raise HTTPException(status_code=401, detail="Invalid session token origin.")
    return claims


_profile_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_PROFILE_TTL = 300.0


def _clerk_profile(clerk_user_id: str, claims: Dict[str, Any]) -> Dict[str, Any]:
    """Returns {'email', 'name'} for a verified Clerk user. The email must be verified by Clerk."""
    cached = _profile_cache.get(clerk_user_id)
    if cached and time.time() - cached[0] < _PROFILE_TTL:
        return cached[1]

    email = None
    name = claims.get("name") or claims.get("full_name")

    # Signed custom claim (only present if added in the Clerk session token template).
    claim_email = claims.get("email") or claims.get("primary_email_address")
    if claim_email and claims.get("email_verified", True):
        email = str(claim_email).strip().lower()

    secret = _clerk_secret()
    if not email and secret:
        try:
            req = urllib.request.Request(
                f"https://api.clerk.com/v1/users/{clerk_user_id}",
                headers={"Authorization": f"Bearer {secret}", "User-Agent": "CypherLabelGuard-Backend"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            primary_id = data.get("primary_email_address_id")
            for item in data.get("email_addresses", []):
                verified = (item.get("verification") or {}).get("status") == "verified"
                if verified and (item.get("id") == primary_id or email is None):
                    email = str(item.get("email_address", "")).strip().lower() or email
            first, last = data.get("first_name") or "", data.get("last_name") or ""
            if first or last:
                name = f"{first} {last}".strip()
        except Exception as exc:
            logger.warning("Clerk user lookup failed: %s", type(exc).__name__)

    if not email:
        raise HTTPException(status_code=401, detail="No verified email on this account.")

    profile = {"email": email, "name": name or email.split("@")[0]}
    _profile_cache[clerk_user_id] = (time.time(), profile)
    return profile


def _apply_admin_policy(user: User, db: Session) -> User:
    """Promotes (never auto-demotes) accounts whose Clerk-verified email is in ADMIN_EMAILS."""
    if user.role != "Administrator" and (user.email or "").lower() in _admin_emails():
        user.role = "Administrator"
        db.commit()
    return user


def _resolve_user(claims: Dict[str, Any], db: Session) -> User:
    clerk_id = str(claims["sub"])
    user = db.query(User).filter(User.id == clerk_id).first()
    if user:
        # Admin promotion needs the verified email, which is only fetched if a match is possible.
        if user.role != "Administrator" and _admin_emails():
            profile = _clerk_profile(clerk_id, claims)
            if profile["email"] in _admin_emails():
                user.role = "Administrator"
                db.commit()
        return user

    profile = _clerk_profile(clerk_id, claims)
    email = profile["email"]

    # Existing legacy account with the same Clerk-VERIFIED email: reuse it.
    user = db.query(User).filter(User.email == email).first()
    if user:
        return _apply_admin_policy(user, db)

    user = User(
        id=clerk_id,
        email=email,
        hashed_password="!clerk-managed",  # unusable as a password hash
        full_name=profile["name"][:100],
        role="Administrator" if email in _admin_emails() else "User",
        workspace_name=f"{profile['name'].split(' ')[0]}'s Workspace"[:100],
        credits_balance=_free_credits(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # two parallel first requests
        db.rollback()
        user = db.query(User).filter((User.id == clerk_id) | (User.email == email)).first()
        if not user:
            raise HTTPException(status_code=500, detail="Could not create account.")
        return user
    db.refresh(user)
    try:
        db.add(AuditLogEntry(user_id=user.id, action="USER_SIGNUP", details="Account created via Clerk"))
        db.commit()
    except Exception:
        db.rollback()
    return user


# ------------------------------------------------------------------------------
# Dependencies used by the other route modules
# ------------------------------------------------------------------------------
def _bearer(authorization: Optional[str]) -> Optional[str]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return token or None


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    token = _bearer(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required. Please sign in.")
    return _resolve_user(_verify_clerk_jwt(token), db)


def get_optional_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """No header -> guest (None). A header that is present but invalid is rejected, never silently treated as guest."""
    token = _bearer(authorization)
    if not token:
        return None
    return _resolve_user(_verify_clerk_jwt(token), db)


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "Administrator":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------
class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    workspace_name: Optional[str] = None


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    sub = user.subscriptions[0] if user.subscriptions else None
    return {
        "success": True,
        "user": user.to_dict(),
        "subscription": sub.to_dict() if sub else {"plan_name": "Core", "status": "Active"},
        "credits_balance": user.credits_balance,
        "payment_methods_count": len(user.payment_methods),
    }


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.full_name:
        user.full_name = req.full_name.strip()[:100]
    if req.workspace_name:
        user.workspace_name = req.workspace_name.strip()[:100]
    db.commit()
    return {"success": True, "user": user.to_dict()}


@router.post("/clerk-sync")
def sync_clerk_user(user: User = Depends(get_current_user)):
    """Identity comes ONLY from the verified Clerk token in the Authorization header; the request
    body is ignored and no app-issued token is returned. The frontend uses the Clerk session
    token (getToken()) as its Bearer token."""
    return {
        "status": "synchronized",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "workspace_name": user.workspace_name,
            "role": user.role,
            "credits_balance": user.credits_balance,
        },
    }
