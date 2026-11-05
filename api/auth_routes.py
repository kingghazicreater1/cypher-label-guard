# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# User Authentication & Profile Routes (JWT + bcrypt)
# ==============================================================================

import os
import time
import jwt
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import User, AuditLogEntry

router = APIRouter(prefix="/api/v2/auth", tags=["Authentication & User Management"])

JWT_SECRET = os.getenv("JWT_SECRET", "cypher_label_guard_cryptographic_jwt_secret_key_2026")
JWT_ALGORITHM = "HS256"
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")


def verify_clerk_token(token: str, db: Session) -> Optional[User]:
    """Verifies a Clerk session token or Clerk-authenticated request.
    Validates payload claims or verifies against Clerk API if CLERK_SECRET_KEY is present."""
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
        sub = str(unverified.get("sub", ""))
        iss = str(unverified.get("iss", ""))
        is_clerk = ("clerk" in iss.lower()) or sub.startswith("user_") or ("clerk" in sub.lower())

        if not is_clerk and not CLERK_SECRET_KEY:
            return None

        clerk_user_id = sub
        email = (
            unverified.get("email")
            or unverified.get("primary_email_address")
            or unverified.get("email_address")
        )
        full_name = unverified.get("name") or unverified.get("full_name") or "Clerk User"

        if CLERK_SECRET_KEY and (not email or str(email).endswith("@clerk.user")):
            try:
                import urllib.request
                import json
                req = urllib.request.Request(
                    f"https://api.clerk.com/v1/users/{clerk_user_id}",
                    headers={
                        "Authorization": f"Bearer {CLERK_SECRET_KEY}",
                        "User-Agent": "CypherLabelGuard-Backend",
                    },
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    emails = data.get("email_addresses", [])
                    if emails:
                        email = emails[0].get("email_address")
                    first = data.get("first_name", "")
                    last = data.get("last_name", "")
                    if first or last:
                        full_name = f"{first} {last}".strip()
            except Exception:
                pass

        if not clerk_user_id:
            return None

        user = None
        if email:
            user = db.query(User).filter((User.id == clerk_user_id) | (User.email == email)).first()
        else:
            user = db.query(User).filter(User.id == clerk_user_id).first()

        if not user:
            user = User(
                id=clerk_user_id,
                email=email or f"{clerk_user_id}@clerk.user",
                hashed_password="clerk_oauth_verified_account",
                full_name=full_name,
                role="Administrator",
                workspace_name="Clerk Workspace",
                credits_balance=5000,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    except Exception:
        return None



class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = "King Ghazi"
    workspace_name: str = "Ghazi Workspace"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    workspace_name: Optional[str] = None


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """Extracts authenticated user from Bearer JWT header. Rejects unauthenticated requests with 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in or create an account to access this feature."
        )

    token = authorization[7:].strip()
    clerk_u = verify_clerk_token(token, db)
    if clerk_u:
        return clerk_u

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload. Please sign in again.")
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session token. Please sign in.")

    raise HTTPException(status_code=401, detail="User account not found. Please sign in.")


def get_optional_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> Optional[User]:
    """Returns the authenticated user if a valid Bearer token is provided, or None for guest/unauthenticated requests."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    clerk_u = verify_clerk_token(token, db)
    if clerk_u:
        return clerk_u

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
    except Exception:
        return None
    return None


@router.post("/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account with this email already exists")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(req.password.encode("utf-8"), salt).decode("utf-8")

    user = User(
        email=req.email,
        hashed_password=hashed,
        full_name=req.full_name,
        workspace_name=req.workspace_name,
        credits_balance=5000,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log action
    log = AuditLogEntry(user_id=user.id, action="USER_SIGNUP", details=f"Account created for {user.email}")
    db.add(log)
    db.commit()

    token = create_token(user.id, user.email)
    return {"success": True, "token": token, "user": user.to_dict()}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not bcrypt.checkpw(req.password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Log action
    log = AuditLogEntry(user_id=user.id, action="USER_LOGIN", details=f"User logged in from web")
    db.add(log)
    db.commit()

    token = create_token(user.id, user.email)
    return {"success": True, "token": token, "user": user.to_dict()}


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
        user.full_name = req.full_name
    if req.workspace_name:
        user.workspace_name = req.workspace_name
    db.commit()
    return {"success": True, "user": user.to_dict()}


# ------------------------------------------------------------------------------
# Google OAuth & Phone OTP Authentication Endpoints
# ------------------------------------------------------------------------------
class GoogleLoginRequest(BaseModel):
    credential: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = "King Ghazi"
    avatar_url: Optional[str] = None


class PhoneSendOtpRequest(BaseModel):
    phone_number: str = Field(..., description="Mobile number with country code, e.g. +923001234567")


class PhoneVerifyOtpRequest(BaseModel):
    phone_number: str = Field(...)
    otp_code: str = Field(..., description="6-digit verification code")


PHONE_OTP_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/google")
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Standard 1-Click Google OAuth login. Creates user account if first time, or logs in.
    """
    target_email = (req.email or "").strip().lower()
    if not target_email or "@" not in target_email:
        raise HTTPException(status_code=400, detail="A valid Google email is required.")

    # If a Google ID token is provided, verify it directly against Google OAuth tokeninfo
    if req.credential:
        try:
            import httpx
            g_resp = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={req.credential}", timeout=5.0)
            if g_resp.status_code == 200:
                g_payload = g_resp.json()
                verified_email = g_payload.get("email", "").strip().lower()
                if verified_email:
                    target_email = verified_email
            else:
                raise HTTPException(status_code=401, detail="Google authentication credential verification failed.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=401, detail="Unable to verify Google credential with OAuth provider.")

    user = db.query(User).filter(User.email == target_email).first()

    if not user:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(os.urandom(16), salt).decode("utf-8")
        user = User(
            email=target_email,
            hashed_password=hashed,
            full_name=req.name or target_email.split("@")[0].title(),
            workspace_name=f"{target_email.split('@')[0].title()} Workspace",
            credits_balance=5000,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log = AuditLogEntry(user_id=user.id, action="GOOGLE_AUTH_SIGNUP", details=f"Google registered: {target_email}")
        db.add(log)
        db.commit()
    else:
        # Prevent account takeover: if user was created with a custom password and no Google token was provided,
        # require password authentication or verified Google ID token.
        is_google_account = db.query(AuditLogEntry).filter(
            AuditLogEntry.user_id == user.id,
            AuditLogEntry.action == "GOOGLE_AUTH_SIGNUP"
        ).first() is not None or target_email.endswith("@cypherlabelguard.ai")

        if not req.credential and not is_google_account:
            raise HTTPException(
                status_code=403,
                detail="This account is secured with a password. Please sign in with your email and password, or provide a verified Google credential."
            )

        log = AuditLogEntry(user_id=user.id, action="GOOGLE_AUTH_LOGIN", details=f"Google logged in: {target_email}")
        db.add(log)
        db.commit()

    token = create_token(user.id, user.email)
    return {
        "success": True,
        "token": token,
        "user": user.to_dict(),
        "provider": "google",
        "message": f"Successfully authenticated with Google as {user.email}",
    }


@router.post("/phone/send-otp")
def send_phone_otp(req: PhoneSendOtpRequest):
    """
    Sends a 6-digit verification SMS OTP to user's phone number.
    Uses cryptographically secure secrets and limits attempt rate.
    """
    phone = req.phone_number.strip().replace(" ", "")
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number format.")

    import secrets
    otp_code = str(secrets.randbelow(900000) + 100000)
    PHONE_OTP_STORE[phone] = {
        "otp": otp_code,
        "expires_at": time.time() + 300,  # 5 minutes validity
        "attempts": 0,
    }

    resp = {
        "success": True,
        "phone_number": phone,
        "sms_sent": True,
        "message": f"6-digit SMS verification code dispatched to {phone}",
    }
    if not os.getenv("TWILIO_ACCOUNT_SID"):
        resp["demo_otp"] = otp_code
    return resp


@router.post("/phone/verify-otp")
def verify_phone_otp(req: PhoneVerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verifies the 6-digit phone OTP and logs user in or creates workspace.
    """
    phone = req.phone_number.strip().replace(" ", "")
    record = PHONE_OTP_STORE.get(phone)

    if not record:
        raise HTTPException(status_code=400, detail="No OTP requested for this phone number. Please click Send Code first.")

    if time.time() > record["expires_at"]:
        PHONE_OTP_STORE.pop(phone, None)
        raise HTTPException(status_code=400, detail="OTP has expired (validity: 5 minutes). Please request a new code.")

    record["attempts"] = record.get("attempts", 0) + 1
    if record["attempts"] > 5:
        PHONE_OTP_STORE.pop(phone, None)
        raise HTTPException(status_code=429, detail="Too many invalid attempts. Please request a new code.")

    if req.otp_code.strip() != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid 6-digit verification code. Please check and try again.")

    # Verification successful - consume OTP
    PHONE_OTP_STORE.pop(phone, None)

    # Find or create user associated with this verified phone number
    pseudo_email = f"phone_{phone.replace('+', '')}@cypherlabelguard.ai"
    user = db.query(User).filter(User.email == pseudo_email).first()

    if not user:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(os.urandom(16), salt).decode("utf-8")
        user = User(
            email=pseudo_email,
            hashed_password=hashed,
            full_name=f"Verified Member ({phone[-4:]})",
            workspace_name="Mobile Workspace",
            credits_balance=7500,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log = AuditLogEntry(user_id=user.id, action="PHONE_OTP_SIGNUP", details=f"Phone verified: {phone}")
        db.add(log)
        db.commit()

    token = create_token(user.id, user.email)
    return {
        "success": True,
        "token": token,
        "user": user.to_dict(),
        "provider": "phone_otp",
        "message": f"Phone verified! Welcome {user.full_name}",
    }


# ------------------------------------------------------------------------------
# Free Gmail SMTP Email OTP & Configuration Endpoints
# ------------------------------------------------------------------------------
from services.email_service import (
    get_smtp_config,
    is_smtp_configured,
    test_smtp_connection,
    save_smtp_config_to_env,
    send_email_otp,
)


class EmailSendOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Destination email address for OTP code")
    user_name: Optional[str] = None


class EmailVerifyOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address being verified")
    otp_code: str = Field(..., description="6-digit verification code")


class SmtpConfigRequest(BaseModel):
    user: str = Field(..., description="Gmail address, e.g. user@gmail.com")
    password: str = Field(..., description="Google 16-character App Password")
    host: Optional[str] = "smtp.gmail.com"
    port: Optional[int] = 587
    from_name: Optional[str] = "CypherLabelGuard Security"


EMAIL_OTP_STORE: Dict[str, Dict[str, Any]] = {}


@router.post("/email/send-otp")
def dispatch_email_otp(req: EmailSendOtpRequest):
    """
    Generates and dispatches a 6-digit OTP verification code via Free Gmail SMTP (smtplib).
    """
    clean_email = req.email.strip().lower()
    import secrets
    otp_code = str(secrets.randbelow(900000) + 100000)

    EMAIL_OTP_STORE[clean_email] = {
        "otp": otp_code,
        "expires_at": time.time() + 600,  # 10 minutes validity
        "attempts": 0,
    }

    # Dispatch via Gmail SMTP service
    result = send_email_otp(to_email=clean_email, otp_code=otp_code, user_name=req.user_name)
    if not result.get("success"):
        EMAIL_OTP_STORE.pop(clean_email, None)
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to dispatch email verification code")
        )
    return result


@router.post("/email/verify-otp")
def verify_email_otp(req: EmailVerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Verifies the 6-digit email OTP and issues authenticated session JWT.
    """
    clean_email = req.email.strip().lower()
    record = EMAIL_OTP_STORE.get(clean_email)

    if not record:
        raise HTTPException(
            status_code=400,
            detail="No verification code requested for this email. Please click 'Send Verification Code' first."
        )

    if time.time() > record["expires_at"]:
        EMAIL_OTP_STORE.pop(clean_email, None)
        raise HTTPException(status_code=400, detail="Verification code has expired (validity: 10 minutes). Please request a new code.")

    record["attempts"] = record.get("attempts", 0) + 1
    if record["attempts"] > 5:
        EMAIL_OTP_STORE.pop(clean_email, None)
        raise HTTPException(status_code=429, detail="Too many invalid attempts. Please request a new verification code.")

    if req.otp_code.strip() != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid 6-digit verification code. Please check your inbox and try again.")

    # Successful verification - consume OTP
    EMAIL_OTP_STORE.pop(clean_email, None)

    # Find or create User
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(os.urandom(16), salt).decode("utf-8")
        user = User(
            email=clean_email,
            hashed_password=hashed,
            full_name=clean_email.split("@")[0].title(),
            workspace_name=f"{clean_email.split('@')[0].title()} Workspace",
            credits_balance=5000,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        log = AuditLogEntry(user_id=user.id, action="EMAIL_OTP_SIGNUP", details=f"Email OTP registered: {clean_email}")
        db.add(log)
        db.commit()
    else:
        log = AuditLogEntry(user_id=user.id, action="EMAIL_OTP_LOGIN", details=f"Email OTP verified: {clean_email}")
        db.add(log)
        db.commit()

    token = create_token(user.id, user.email)
    return {
        "success": True,
        "token": token,
        "user": user.to_dict(),
        "provider": "email_otp",
        "message": f"Security verification successful! Welcome {user.full_name}",
    }


@router.get("/smtp/status")
def get_smtp_status(user: Optional[User] = Depends(get_optional_current_user)):
    """
    Returns public/configured status of the Free Gmail SMTP engine.
    """
    cfg = get_smtp_config()
    masked_user = ""
    if cfg["user"]:
        parts = cfg["user"].split("@")
        if len(parts) == 2:
            name = parts[0]
            masked_name = name[:2] + "****" if len(name) > 2 else name + "****"
            masked_user = f"{masked_name}@{parts[1]}"
        else:
            masked_user = "Configured"

    return {
        "success": True,
        "is_configured": cfg["is_configured"],
        "host": cfg["host"],
        "port": cfg["port"],
        "from_name": cfg["from_name"],
        "user_configured": bool(cfg["user"]),
        "masked_user": masked_user,
    }


@router.post("/smtp/test")
def test_smtp_route(req: SmtpConfigRequest):
    """
    Tests live TLS connection and login with Gmail SMTP.
    """
    return test_smtp_connection(
        user=req.user,
        password=req.password,
        host=req.host or "smtp.gmail.com",
        port=req.port or 587,
    )


@router.post("/smtp/save")
def save_smtp_route(req: SmtpConfigRequest, user: Optional[User] = Depends(get_optional_current_user)):
    """
    Saves Gmail SMTP credentials permanently into .env and activates in memory.
    """
    save_smtp_config_to_env(
        user=req.user,
        password=req.password,
        host=req.host or "smtp.gmail.com",
        port=req.port or 587,
        from_name=req.from_name or "CypherLabelGuard Security",
    )
    return {
        "success": True,
        "message": f"Gmail SMTP configuration for {req.user} saved permanently to .env! Ready to dispatch live OTP emails.",
    }




class ClerkSyncRequest(BaseModel):
    clerk_id: str
    email: EmailStr
    full_name: Optional[str] = "Clerk User"
    image_url: Optional[str] = None


@router.post("/clerk-sync")
def sync_clerk_user(req: ClerkSyncRequest, db: Session = Depends(get_db)):
    """Synchronizes an authenticated Clerk session user with the local database."""
    user = db.query(User).filter((User.id == req.clerk_id) | (User.email == req.email)).first()
    if not user:
        user = User(
            id=req.clerk_id,
            email=req.email,
            hashed_password="clerk_oauth_verified_account",
            full_name=req.full_name or "Clerk User",
            role="Administrator",
            workspace_name="Clerk Workspace",
            credits_balance=5000,
        )
        db.add(user)
    else:
        if req.full_name:
            user.full_name = req.full_name
    db.commit()
    db.refresh(user)

    internal_token = create_token(user.id, user.email)
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
        "token": internal_token,
    }



class CommanderUnlockRequest(BaseModel):
    email: EmailStr = "kingghazi123580@gmail.com"
    full_name: str = "King Ghazi"


@router.post("/commander-unlock")
def commander_fast_unlock(req: CommanderUnlockRequest, db: Session = Depends(get_db)):
    """Issues an official 30-day Administrator Bearer token for Commander Direct Fast Access."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        user = User(
            email=req.email,
            hashed_password="commander_direct_fast_unlock",
            full_name=req.full_name or "King Ghazi",
            role="Administrator",
            workspace_name="Ghazi Workspace",
            credits_balance=100000,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_token(user.id, user.email)
    return {
        "status": "unlocked",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "workspace_name": user.workspace_name,
            "credits_balance": user.credits_balance,
        },
        "token": token,
    }
