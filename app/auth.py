from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt
import requests
from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jwt import PyJWKClient

from app.auth_db import auth_db
from app.config import settings


def now_utc() -> datetime:
    return datetime.now(UTC)


def _require_session_secret() -> str:
    if not settings.app_session_secret:
        raise HTTPException(status_code=503, detail="APP_SESSION_SECRET is not configured")
    return settings.app_session_secret


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_google_token(identity_token: str) -> dict:
    if not settings.google_android_client_id:
        raise HTTPException(status_code=503, detail="GOOGLE_ANDROID_CLIENT_ID is not configured")
    try:
        payload = google_id_token.verify_oauth2_token(
            identity_token,
            google_requests.Request(),
            settings.google_android_client_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {exc}") from exc
    return {
        "provider": "google",
        "provider_user_id": payload["sub"],
        "email": payload.get("email"),
        "display_name": payload.get("name"),
        "avatar_url": payload.get("picture"),
    }


def verify_apple_token(identity_token: str) -> dict:
    if not settings.apple_ios_audience:
        raise HTTPException(status_code=503, detail="APPLE_IOS_AUDIENCE is not configured")
    try:
        jwk_client = PyJWKClient("https://appleid.apple.com/auth/keys")
        signing_key = jwk_client.get_signing_key_from_jwt(identity_token)
        payload = jwt.decode(
            identity_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.apple_ios_audience,
            issuer="https://appleid.apple.com",
        )
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid Apple token: {exc}") from exc
    return {
        "provider": "apple",
        "provider_user_id": payload["sub"],
        "email": payload.get("email"),
        "display_name": payload.get("email") or "Apple User",
        "avatar_url": None,
    }


def verify_provider_token(provider: str, identity_token: str) -> dict:
    provider = provider.lower()
    if provider == "google":
        return verify_google_token(identity_token)
    if provider == "apple":
        return verify_apple_token(identity_token)
    raise HTTPException(status_code=400, detail="Unsupported provider")


def _upsert_user(identity: dict) -> dict:
    now_text = now_utc().isoformat()
    with auth_db() as conn:
        existing = conn.execute(
            """
            SELECT u.*
            FROM auth_identities ai
            JOIN users u ON u.id = ai.user_id
            WHERE ai.provider = ? AND ai.provider_user_id = ?
            """,
            (identity["provider"], identity["provider_user_id"]),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE users
                SET email = COALESCE(?, email),
                    display_name = COALESCE(?, display_name),
                    avatar_url = COALESCE(?, avatar_url),
                    last_login_at = ?
                WHERE id = ?
                """,
                (
                    identity.get("email"),
                    identity.get("display_name"),
                    identity.get("avatar_url"),
                    now_text,
                    existing["id"],
                ),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (existing["id"],)).fetchone()
            return dict(row)

        conn.execute(
            """
            INSERT INTO users (email, display_name, avatar_url, plan_tier, created_at, last_login_at)
            VALUES (?, ?, ?, 'free', ?, ?)
            """,
            (
                identity.get("email"),
                identity.get("display_name"),
                identity.get("avatar_url"),
                now_text,
                now_text,
            ),
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            """
            INSERT INTO auth_identities (user_id, provider, provider_user_id, provider_email, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                identity["provider"],
                identity["provider_user_id"],
                identity.get("email"),
                now_text,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row)


def _issue_access_token(user: dict) -> str:
    secret = _require_session_secret()
    exp = now_utc() + timedelta(minutes=settings.app_access_token_minutes)
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "email": user.get("email"),
            "plan_tier": user["plan_tier"],
            "type": "access",
            "exp": exp,
            "iat": now_utc(),
        },
        secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict:
    secret = _require_session_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"Invalid access token: {exc}") from exc
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token type")
    return payload


def _issue_refresh_session(user: dict, device_label: str | None) -> str:
    raw = secrets.token_urlsafe(48)
    token_hash = hash_refresh_token(raw)
    created_at = now_utc()
    expires_at = created_at + timedelta(days=settings.app_refresh_token_days)
    with auth_db() as conn:
        conn.execute(
            """
            INSERT INTO user_sessions (user_id, refresh_token_hash, device_label, created_at, expires_at, revoked_at)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (
                user["id"],
                token_hash,
                device_label,
                created_at.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()
    return raw


def login_with_provider(provider: str, identity_token: str, device_label: str | None = None) -> dict:
    identity = verify_provider_token(provider, identity_token)
    user = _upsert_user(identity)
    access_token = _issue_access_token(user)
    refresh_token = _issue_refresh_session(user, device_label)
    return {
        "user": user,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_session(refresh_token: str) -> dict:
    token_hash = hash_refresh_token(refresh_token)
    with auth_db() as conn:
        session = conn.execute(
            """
            SELECT us.*, u.email, u.display_name, u.avatar_url, u.plan_tier
            FROM user_sessions us
            JOIN users u ON u.id = us.user_id
            WHERE us.refresh_token_hash = ? AND us.revoked_at IS NULL
            """,
            (token_hash,),
        ).fetchone()
        if not session:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if datetime.fromisoformat(session["expires_at"]) < now_utc():
            raise HTTPException(status_code=401, detail="Refresh token expired")
        user = {
            "id": session["user_id"],
            "email": session["email"],
            "display_name": session["display_name"],
            "avatar_url": session["avatar_url"],
            "plan_tier": session["plan_tier"],
        }
    return {
        "user": user,
        "access_token": _issue_access_token(user),
        "token_type": "bearer",
    }


def revoke_refresh_token(refresh_token: str) -> None:
    token_hash = hash_refresh_token(refresh_token)
    with auth_db() as conn:
        conn.execute(
            "UPDATE user_sessions SET revoked_at = ? WHERE refresh_token_hash = ? AND revoked_at IS NULL",
            (now_utc().isoformat(), token_hash),
        )
        conn.commit()


def get_current_user_from_token(authorization: str | None) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user_id = payload["sub"]
    with auth_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        return dict(row)


def delete_current_user_account(authorization: str | None) -> dict:
    user = get_current_user_from_token(authorization)
    with auth_db() as conn:
        conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user["id"],))
        conn.execute("DELETE FROM auth_identities WHERE user_id = ?", (user["id"],))
        conn.execute("DELETE FROM users WHERE id = ?", (user["id"],))
        conn.commit()
    return {"status": "deleted"}
