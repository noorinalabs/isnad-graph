"""Email verification logic: token/code generation, storage, validation, and email sending."""

from __future__ import annotations

import logging
import secrets
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import redis as redis_lib
from jose import JWTError, jwt

from src.config import get_settings
from src.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# In-memory fallback stores
_verification_store: dict[str, tuple[str, str, float]] = {}  # user_id -> (code, token, timestamp)
_resend_counts: dict[str, list[float]] = {}  # user_id -> [timestamps]

_CODE_LENGTH = 6
_RESEND_WINDOW_SECONDS = 3600  # 1 hour


def _generate_verification_code() -> str:
    """Generate a cryptographically random 6-digit code."""
    return "".join(secrets.choice("0123456789") for _ in range(_CODE_LENGTH))


def _create_verification_token(user_id: str) -> str:
    """Create a signed JWT verification token."""
    settings = get_settings()
    ttl_hours = settings.email.verification_token_ttl_hours
    payload = {
        "sub": user_id,
        "type": "email_verification",
        "exp": int(time.time()) + (ttl_hours * 3600),
        "iat": int(time.time()),
        "jti": secrets.token_hex(16),
    }
    return str(jwt.encode(payload, settings.auth.jwt_secret, algorithm=settings.auth.jwt_algorithm))


def _verify_verification_token(token: str) -> str:
    """Verify a verification token and return the user_id.

    Raises ValueError if the token is invalid or expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.auth.jwt_secret, algorithms=[settings.auth.jwt_algorithm]
        )
    except JWTError as exc:
        raise ValueError(f"Invalid verification token: {exc}") from exc

    if payload.get("type") != "email_verification":
        raise ValueError("Token is not a verification token")

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise ValueError("Invalid token payload")

    return user_id


def generate_and_store_verification(user_id: str) -> tuple[str, str]:
    """Generate a verification code and token, store them in Redis with TTL.

    Returns (code, token).
    """
    settings = get_settings()
    code = _generate_verification_code()
    token = _create_verification_token(user_id)
    ttl_seconds = settings.email.verification_token_ttl_hours * 3600

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(f"email_verify:{user_id}:code", ttl_seconds, code)
            redis_client.setex(f"email_verify:{user_id}:token", ttl_seconds, token)
            return code, token
        except (redis_lib.ConnectionError, redis_lib.TimeoutError, OSError):
            logger.warning("Redis store failed for verification, using in-memory fallback")

    _verification_store[user_id] = (code, token, time.time())
    return code, token


def validate_verification(token: str, code: str) -> str:
    """Validate both the verification token and the 6-digit code.

    Returns the user_id on success.
    Raises ValueError on any validation failure.
    """
    user_id = _verify_verification_token(token)

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            stored_code = redis_client.get(f"email_verify:{user_id}:code")
            stored_token = redis_client.get(f"email_verify:{user_id}:token")

            if stored_code is None or stored_token is None:
                raise ValueError("Verification code has expired or was already used")

            if stored_code != code:
                raise ValueError("Invalid verification code")

            if stored_token != token:
                raise ValueError("Invalid verification token")

            # Invalidate used code/token
            redis_client.delete(f"email_verify:{user_id}:code")
            redis_client.delete(f"email_verify:{user_id}:token")
            return user_id
        except (redis_lib.ConnectionError, redis_lib.TimeoutError, OSError):
            logger.warning("Redis validation failed, trying in-memory fallback")

    # In-memory fallback
    entry = _verification_store.get(user_id)
    if entry is None:
        raise ValueError("Verification code has expired or was already used")

    stored_code, stored_token, timestamp = entry
    settings = get_settings()
    ttl_seconds = settings.email.verification_token_ttl_hours * 3600
    if time.time() - timestamp > ttl_seconds:
        del _verification_store[user_id]
        raise ValueError("Verification code has expired")

    if stored_code != code:
        raise ValueError("Invalid verification code")

    if stored_token != token:
        raise ValueError("Invalid verification token")

    del _verification_store[user_id]
    return user_id


def check_resend_rate_limit(user_id: str) -> bool:
    """Check if the user is within the resend rate limit.

    Returns True if allowed, False if rate-limited.
    """
    settings = get_settings()
    max_resends = settings.email.resend_rate_limit
    now = time.time()

    redis_client = get_redis_client()
    if redis_client is not None:
        try:
            key = f"email_verify_resend:{user_id}"
            window_start = now - _RESEND_WINDOW_SECONDS
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, _RESEND_WINDOW_SECONDS + 1)
            results = pipe.execute()
            count: int = results[1]
            if count >= max_resends:
                redis_client.zrem(key, str(now))
                return False
            return True
        except (redis_lib.ConnectionError, redis_lib.TimeoutError, OSError):
            logger.warning("Redis rate limit check failed, using in-memory fallback")

    # In-memory fallback
    timestamps = _resend_counts.get(user_id, [])
    cutoff = now - _RESEND_WINDOW_SECONDS
    timestamps = [t for t in timestamps if t > cutoff]
    if len(timestamps) >= max_resends:
        _resend_counts[user_id] = timestamps
        return False
    timestamps.append(now)
    _resend_counts[user_id] = timestamps
    return True


def send_verification_email(email: str, name: str, code: str, token: str) -> None:
    """Send a branded verification email with the code and link."""
    settings = get_settings().email
    base_url = get_settings().auth.oauth_redirect_base_url.rstrip("/")
    verify_url = f"{base_url}/verify?token={token}"

    subject = "Verify your email \u2014 Noorina Labs"
    html_body = _render_verification_email(name, email, code, verify_url)
    text_body = (
        f"Hi {name},\n\n"
        f"Your verification code is: {code}\n\n"
        f"Or click this link to verify: {verify_url}\n\n"
        "This code expires in 24 hours.\n\n"
        "If you didn't create this account, you can safely ignore this email.\n\n"
        "- Noorina Labs"
    )

    if settings.provider == "sendgrid" and settings.api_key:
        _send_via_sendgrid(settings, email, subject, html_body, text_body)
    else:
        _send_via_smtp(settings, email, subject, html_body, text_body)


def _send_via_smtp(
    settings: object, to_email: str, subject: str, html_body: str, text_body: str
) -> None:
    """Send email via SMTP."""
    from src.config import EmailSettings

    cfg: EmailSettings = settings  # type: ignore[assignment]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{cfg.from_name} <{cfg.from_address}>"
    msg["To"] = to_email

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        if cfg.smtp_use_tls:
            server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(cfg.smtp_host, cfg.smtp_port)

        if cfg.smtp_user and cfg.smtp_password:
            server.login(cfg.smtp_user, cfg.smtp_password)

        server.sendmail(cfg.from_address, to_email, msg.as_string())
        server.quit()
        logger.info("verification_email_sent", extra={"to": to_email, "method": "smtp"})
    except Exception:
        logger.exception("smtp_send_failed", extra={"to": to_email})
        raise


def _send_via_sendgrid(
    settings: object, to_email: str, subject: str, html_body: str, text_body: str
) -> None:
    """Send email via SendGrid HTTP API."""
    from src.config import EmailSettings

    cfg: EmailSettings = settings  # type: ignore[assignment]

    import httpx

    response = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {cfg.api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": cfg.from_address, "name": cfg.from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body},
            ],
        },
    )
    if response.status_code >= 400:
        logger.error(
            "sendgrid_send_failed",
            extra={"status": response.status_code, "body": response.text},
        )
        raise RuntimeError(f"SendGrid API error: {response.status_code}")

    logger.info("verification_email_sent", extra={"to": to_email, "method": "sendgrid"})


def _render_verification_email(name: str, email: str, code: str, verify_url: str) -> str:
    """Render the branded HTML verification email template."""
    font = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif"
    body_style = f"margin:0;padding:0;background-color:#f4f4f5;font-family:{font};"
    outer_style = "background-color:#f4f4f5;padding:40px 20px;"
    card_style = (
        "background-color:#ffffff;border-radius:12px;"
        "overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);"
    )
    header_style = "background-color:#1a1a2e;padding:32px 40px;text-align:center;"
    h1_style = "margin:0;color:#ffffff;font-size:24px;font-weight:600;letter-spacing:-0.5px;"
    p_style = "margin:0 0 16px;color:#27272a;font-size:16px;line-height:1.5;"
    code_box = (
        "background-color:#f4f4f5;border-radius:8px;padding:24px;text-align:center;margin:0 0 24px;"
    )
    code_label = (
        "margin:0 0 8px;color:#71717a;font-size:13px;text-transform:uppercase;letter-spacing:1px;"
    )
    code_style = (
        "margin:0;color:#1a1a2e;font-size:36px;"
        "font-weight:700;letter-spacing:8px;font-family:monospace;"
    )
    btn_style = (
        "display:inline-block;background-color:#1a1a2e;"
        "color:#ffffff;text-decoration:none;font-size:16px;"
        "font-weight:600;padding:14px 32px;border-radius:8px;"
    )
    small = "margin:0;color:#71717a;font-size:13px;text-align:center;"
    footer_td = "background-color:#fafafa;padding:24px 40px;border-top:1px solid #e4e4e7;"
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Verify your email</title>
</head>
<body style="{body_style}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="{outer_style}">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0"
               cellspacing="0" style="{card_style}">
          <tr>
            <td style="{header_style}">
              <h1 style="{h1_style}">Noorina Labs</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:40px;">
              <p style="{p_style}">Hi {name},</p>
              <p style="margin:0 0 24px;color:#27272a;font-size:16px;">
                Please verify your email address
                (<strong>{email}</strong>) to complete setup.
              </p>
              <div style="{code_box}">
                <p style="{code_label}">Your verification code</p>
                <p style="{code_style}">{code}</p>
              </div>
              <table role="presentation" width="100%"
                     cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="padding:0 0 24px;">
                    <a href="{verify_url}" style="{btn_style}">
                      Verify Email
                    </a>
                  </td>
                </tr>
              </table>
              <p style="{small};margin:0 0 8px;">
                This code expires in 24 hours.
              </p>
              <p style="{small}">
                If you didn't create an account, ignore this email.
              </p>
            </td>
          </tr>
          <tr>
            <td style="{footer_td}">
              <p style="margin:0;color:#a1a1aa;font-size:12px;text-align:center;">
                Noorina Labs &mdash; Computational hadith analysis
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
