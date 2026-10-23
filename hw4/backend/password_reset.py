"""Self-service password reset.

1. The shopper enters their email on "Forgot your password?". If it belongs to an account, a one-time
   reset link is emailed to that address (mailer.py). The response is the same either way, so the
   page never reveals which emails have accounts.
2. The link holds a random token. Only a SHA-256 hash of it is stored (password_resets table), it
   expires after 30 minutes, and it works once.
3. On the reset page the shopper chooses a new password (same rules as signup). It is hashed exactly
   like signup (auth.make_password_hash: PBKDF2-HMAC-SHA256, 120,000 iterations, new random salt),
   all of the account's reset links are cancelled, and every old login session ends.
"""

import hashlib
import os
import secrets
import sqlite3
import time

import auth
import mailer
from tools import get_db

RESET_TTL_SECONDS = 30 * 60
MAX_REQUESTS_PER_HOUR = 3
SITE_URL = os.getenv("SITE_URL", "http://localhost:5175")


def ensure_table() -> None:
    with get_db(writable=True) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                expires_at INTEGER NOT NULL,
                used_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def request_reset(email: str) -> None:
    """Email a reset link if the address has an account. Silently does nothing otherwise."""
    email = email.strip().lower()
    with get_db(writable=True) as conn:
        user = conn.execute("SELECT id, first_name, name, email FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if user is None:
            return
        recent = conn.execute(
            "SELECT count(*) FROM password_resets WHERE user_id = ? AND created_at >= datetime('now', '-1 hour')",
            (user["id"],),
        ).fetchone()[0]
        if recent >= MAX_REQUESTS_PER_HOUR:  # stop someone flooding a customer's inbox
            return
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user["id"], _hash(token), int(time.time()) + RESET_TTL_SECONDS),
        )
    link = f"{SITE_URL}/reset-password?token={token}"
    mailer.send_email(
        user["email"],
        "Reset your Campus Customs password",
        f"Hi {user['first_name'] or user['name']},\n\n"
        "We received a request to reset the password for your Campus Customs account.\n"
        f"Choose a new password here (this link works once and expires in {RESET_TTL_SECONDS // 60} minutes):\n\n"
        f"{link}\n\n"
        "If you didn't ask for this, you can ignore this email; your password won't change.\n\n"
        "Boola Boola!\nCampus Customs, 57 Broadway, New Haven",
    )


def _valid_reset(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM password_resets WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?",
        (_hash(token), int(time.time())),
    ).fetchone()


def token_is_valid(token: str) -> bool:
    with get_db() as conn:
        return _valid_reset(conn, token) is not None


def complete_reset(token: str, new_password: str) -> sqlite3.Row | None:
    """Set the new password if the token is valid. Returns the updated user row, or None."""
    with get_db(writable=True) as conn:
        reset = _valid_reset(conn, token)
        if reset is None:
            return None
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (auth.make_password_hash(new_password), reset["user_id"]),
        )
        # This link and any other outstanding links for the account stop working.
        conn.execute(
            "UPDATE password_resets SET used_at = datetime('now') WHERE user_id = ? AND used_at IS NULL",
            (reset["user_id"],),
        )
        return conn.execute("SELECT * FROM users WHERE id = ?", (reset["user_id"],)).fetchone()
