"""Passwords, sessions and API keys. Secrets are only ever stored hashed."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jsonflow.server.db import Database, now

ROLES = ("admin", "super_admin")
SESSION_COOKIE = "jsonflow_session"
SESSION_HOURS = 12
MIN_PASSWORD = 10
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **_SCRYPT)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if algo != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), **_SCRYPT)
    return hmac.compare_digest(digest.hex(), digest_hex)


def check_password_strength(password: str) -> Optional[str]:
    if len(password) < MIN_PASSWORD:
        return f"Password must be at least {MIN_PASSWORD} characters."
    if password.lower() == password or password.upper() == password or not any(c.isdigit() for c in password):
        return "Password needs upper and lower case letters and a digit."
    return None


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ------------------------------------------------------------------ sessions
def create_session(db: Database, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    db.run("INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
           (_sha(token), user_id, now(), expires.isoformat(timespec="seconds")))
    db.run("UPDATE users SET last_login_at = ? WHERE id = ?", (now(), user_id))
    return token


def user_for_session(db: Database, token: Optional[str]) -> Optional[dict[str, Any]]:
    if not token:
        return None
    row = db.one(
        "SELECT u.id, u.username, u.display_name, u.role, u.active, s.expires_at FROM sessions s "
        "JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?", (_sha(token),))
    if not row or not row["active"] or row["expires_at"] < now():
        return None
    row.pop("expires_at")
    return row


def end_session(db: Database, token: Optional[str]) -> None:
    if token:
        db.run("DELETE FROM sessions WHERE token_hash = ?", (_sha(token),))


def end_user_sessions(db: Database, user_id: int) -> None:
    db.run("DELETE FROM sessions WHERE user_id = ?", (user_id,))


# ------------------------------------------------------------------ API keys
def create_api_key(db: Database, name: str, categories: list[str], actor: str) -> tuple[int, str]:
    key = "jfk_" + secrets.token_urlsafe(32)
    import json

    key_id = db.run(
        "INSERT INTO api_keys (name, prefix, key_hash, categories, created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, key[:10], _sha(key), json.dumps(categories), actor, now()))
    return key_id, key


def key_for_secret(db: Database, secret: Optional[str]) -> Optional[dict[str, Any]]:
    if not secret:
        return None
    row = db.one("SELECT * FROM api_keys WHERE key_hash = ? AND revoked = 0", (_sha(secret),))
    if row:
        db.run("UPDATE api_keys SET last_used_at = ? WHERE id = ?", (now(), row["id"]))
    return row
