# ==============================================================================
# CypherLabelGuard CORE EDITION v2.0
# Free Gmail SMTP Email Service (Standard Python smtplib - Zero Cost)
# ==============================================================================

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

logger = logging.getLogger("CYPHER_LABEL_GUARD.EmailService")

DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587
DEFAULT_FROM_NAME = "CypherLabelGuard Security"


def _get_registry_env(var_name: str) -> Optional[str]:
    """Reads user-level environment variables from Windows Registry (setx)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            val, _ = winreg.QueryValueEx(key, var_name)
            if val:
                return str(val).strip()
    except Exception:
        pass
    return None


def get_smtp_config() -> Dict[str, Any]:
    """Retrieves current SMTP configuration from environment or Windows Registry."""
    host = os.getenv("SMTP_HOST") or _get_registry_env("SMTP_HOST") or DEFAULT_SMTP_HOST
    try:
        raw_port = os.getenv("SMTP_PORT") or _get_registry_env("SMTP_PORT") or str(DEFAULT_SMTP_PORT)
        port = int(raw_port)
    except ValueError:
        port = DEFAULT_SMTP_PORT

    user = os.getenv("SMTP_USER") or os.getenv("GMAIL_ADDRESS") or _get_registry_env("SMTP_USER") or "kingghazi123580@gmail.com"
    # Strip spaces in app password (Google displays 16-char app passwords as 'xxxx xxxx xxxx xxxx')
    raw_pass = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or _get_registry_env("SMTP_PASSWORD") or ""
    password = raw_pass.replace(" ", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME") or _get_registry_env("SMTP_FROM_NAME") or DEFAULT_FROM_NAME

    return {
        "host": host,
        "port": port,
        "user": user.strip(),
        "password": password,
        "from_name": from_name,
        "is_configured": bool(user.strip() and password),
    }


def is_smtp_configured() -> bool:
    """Returns True if user and password credentials are set."""
    cfg = get_smtp_config()
    return cfg["is_configured"]


def test_smtp_connection(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Tests TLS handshake and login authentication with Gmail SMTP server.
    """
    cfg = get_smtp_config()
    target_host = host or cfg["host"]
    target_port = port or cfg["port"]
    target_user = (user or cfg["user"]).strip()
    raw_pass = password or cfg["password"]
    target_pass = raw_pass.replace(" ", "").strip()

    if not target_user or not target_pass:
        return {
            "success": False,
            "status": "NOT_CONFIGURED",
            "message": "Gmail address and Google 16-character App Password are required to test connection.",
        }

    try:
        logger.info(f"Initiating SMTP connection to {target_host}:{target_port}...")
        server = smtplib.SMTP(target_host, target_port, timeout=12)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(target_user, target_pass)
        server.quit()

        return {
            "success": True,
            "status": "LIVE_ONLINE",
            "message": f"Successfully authenticated with {target_host} as {target_user}! Ready to deliver real email OTPs.",
            "host": target_host,
            "port": target_port,
            "user": target_user,
        }
    except smtplib.SMTPAuthenticationError as e:
        logger.warning(f"SMTP Authentication failed: {e}")
        return {
            "success": False,
            "status": "AUTH_FAILED",
            "message": "Gmail authentication rejected. Make sure 2-Step Verification is enabled on your Google account and you are using a 16-character Google App Password (not your regular Gmail password).",
            "error_detail": str(e),
        }
    except Exception as e:
        logger.error(f"SMTP Connection failed: {e}")
        return {
            "success": False,
            "status": "CONNECTION_FAILED",
            "message": f"Could not connect to {target_host}:{target_port}: {str(e)}",
            "error_detail": str(e),
        }


def save_smtp_config_to_env(
    user: str,
    password: str,
    host: str = DEFAULT_SMTP_HOST,
    port: int = DEFAULT_SMTP_PORT,
    from_name: str = DEFAULT_FROM_NAME,
) -> bool:
    """
    Persists SMTP credentials to .env file and updates os.environ in memory.
    """
    clean_user = user.strip()
    clean_pass = password.replace(" ", "").strip()
    clean_host = host.strip() or DEFAULT_SMTP_HOST
    clean_port = str(port)

    # 1. Update active memory
    os.environ["SMTP_HOST"] = clean_host
    os.environ["SMTP_PORT"] = clean_port
    os.environ["SMTP_USER"] = clean_user
    os.environ["SMTP_PASSWORD"] = clean_pass
    os.environ["SMTP_FROM_NAME"] = from_name

    # 2. Update .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    keys_to_update = {
        "SMTP_HOST": clean_host,
        "SMTP_PORT": clean_port,
        "SMTP_USER": clean_user,
        "SMTP_PASSWORD": clean_pass,
        "SMTP_FROM_NAME": from_name,
    }

    new_lines = []
    seen = set()
    for line in lines:
        stripped = line.strip()
        if "=" in stripped and not stripped.startswith("#"):
            k = stripped.split("=")[0].strip()
            if k in keys_to_update:
                new_lines.append(f"{k}={keys_to_update[k]}\n")
                seen.add(k)
                continue
        new_lines.append(line)

    for k, v in keys_to_update.items():
        if k not in seen:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    logger.info(f"Saved SMTP configuration for {clean_user} to .env")
    return True


def send_email_otp(to_email: str, otp_code: str, user_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Dispatches a real HTML + Plaintext Email OTP verification message via Gmail SMTP.
    If SMTP is not configured, provides clear demo fallback so developer/tester is never locked out.
    """
    cfg = get_smtp_config()
    target_email = to_email.strip()
    name = user_name or target_email.split("@")[0].title()

    if not cfg["is_configured"]:
        logger.warning(f"SMTP not configured for {target_email}. Cannot dispatch real email.")
        return {
            "success": False,
            "smtp_sent": False,
            "message": "Gmail SMTP is not configured with an App Password. Please set your 16-character Google App Password via 'setx SMTP_PASSWORD \"your-password\"' in CMD.",
        }

    # Construct the Email Message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"CypherLabelGuard Verification Code: {otp_code}"
    msg["From"] = f"{cfg['from_name']} <{cfg['user']}>"
    msg["To"] = target_email

    # Plain text version
    text_content = f"""
CypherLabelGuard Core Edition Security Verification

Hello {name},

Your 6-digit verification code is: {otp_code}

This code will expire in 10 minutes.
If you did not request this code, please disregard this email.

--
CypherLabelGuard Cryptographic AI Labeling & Multi-Modal Verification Chamber
"""

    # Premium HTML version (Dark Forest Green & Emerald Cyber Theme)
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0d1210;
      color: #e5ece8;
      margin: 0;
      padding: 24px;
    }}
    .container {{
      max-width: 520px;
      margin: 0 auto;
      background-color: #121a16;
      border: 1px solid #1e2e26;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      background: linear-gradient(135deg, #0a3d24 0%, #0d1f17 100%);
      padding: 24px;
      text-align: center;
      border-bottom: 1px solid #1e3a2b;
    }}
    .brand {{
      font-size: 20px;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #ffffff;
    }}
    .brand span {{
      color: #10b981;
    }}
    .tagline {{
      font-size: 11px;
      color: #94a89d;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .content {{
      padding: 32px 28px;
      text-align: center;
    }}
    h2 {{
      font-size: 18px;
      font-weight: 600;
      margin-top: 0;
      color: #f1f7f3;
    }}
    p {{
      font-size: 14px;
      color: #9eb3a7;
      line-height: 1.6;
      margin: 12px 0;
    }}
    .code-box {{
      background-color: #0b1410;
      border: 1.5px solid #10b981;
      border-radius: 8px;
      padding: 18px 24px;
      margin: 24px 0;
      display: inline-block;
    }}
    .otp-code {{
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 34px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #10b981;
      padding-left: 8px;
    }}
    .badge {{
      display: inline-block;
      background-color: rgba(16, 185, 129, 0.15);
      color: #10b981;
      font-size: 11px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 20px;
      border: 1px solid rgba(16, 185, 129, 0.3);
      margin-top: 8px;
    }}
    .footer {{
      background-color: #0e1512;
      padding: 20px 24px;
      text-align: center;
      border-top: 1px solid #18241e;
      font-size: 11px;
      color: #63776c;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">Cypher<span>LabelGuard</span></div>
      <div class="tagline">Cryptographic AI Multi-Modal Verification</div>
    </div>
    <div class="content">
      <h2>One-Time Security Verification</h2>
      <p>Hello <strong>{name}</strong>,</p>
      <p>Use the following 6-digit verification code to complete your sign-in to the CypherLabelGuard workspace:</p>
      
      <div class="code-box">
        <div class="otp-code">{otp_code}</div>
      </div>
      
      <div>
        <span class="badge">Valid for 10 Minutes</span>
      </div>

      <p style="font-size: 12px; color: #788f82; margin-top: 24px;">
        For your security, never share this code with anyone. CypherLabelGuard engineers will never ask for your authentication code.
      </p>
    </div>
    <div class="footer">
      Sent automatically via Free Gmail SMTP Engine.<br>
      If you did not request this code, you can safely ignore this email.
    </div>
  </div>
</body>
</html>
"""

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        logger.info(f"Connecting to Gmail SMTP ({cfg['host']}:{cfg['port']}) to dispatch code to {target_email}...")
        server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(cfg["user"], cfg["password"])
        server.send_message(msg)
        server.quit()

        logger.info(f"Verification email dispatched successfully to {target_email} via {cfg['user']}")
        return {
            "success": True,
            "smtp_sent": True,
            "email": target_email,
            "message": f"Security verification code dispatched to your email inbox ({target_email}). Please check your inbox.",
        }
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Gmail SMTP authentication rejected: {e}")
        return {
            "success": False,
            "smtp_sent": False,
            "error_type": "AUTH_FAILED",
            "message": "Gmail rejected your credentials (535 Bad Credentials). Note: Google requires a 16-letter App Password (e.g. 'abcd efgh ijkl mnop' generated at myaccount.google.com/apppasswords), NOT numbers or account password.",
            "smtp_error": str(e),
        }
    except Exception as e:
        logger.error(f"Failed to dispatch email via Gmail SMTP: {e}")
        return {
            "success": False,
            "smtp_sent": False,
            "error_type": "DELIVERY_FAILED",
            "message": f"Failed to deliver email: {str(e)}",
            "smtp_error": str(e),
        }
