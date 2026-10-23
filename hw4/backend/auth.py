"""Password hashing and login sessions for Campus Customs.

Stored format (matches the seed database): pbkdf2_sha256$<salt>$<hex digest>
- PBKDF2-HMAC-SHA256, 120,000 iterations, salt string encoded as UTF-8.
- Signup and login both go through hash_password(), so the settings can never drift apart.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000
SALT_BYTES = 8  # 8 random bytes -> 16 hex characters, same shape as the seed users' salts
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS)
    return f"{ALGORITHM}${salt}${digest.hex()}"


def make_password_hash(password: str) -> str:
    """Signup: a fresh random salt per user, stored inside the hash string."""
    return hash_password(password, secrets.token_hex(SALT_BYTES))


def verify_password(password: str, stored: str) -> bool:
    """Login: never un-hash. Read the salt from the stored string, re-hash what was typed, compare."""
    try:
        algorithm, salt, _ = stored.split("$")
    except ValueError:
        return False
    if algorithm != ALGORITHM:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


# Used when an email isn't registered, so a login attempt costs the same either way
# and response time doesn't reveal which emails have accounts.
DUMMY_HASH = make_password_hash(secrets.token_hex(16))


# --- Sessions: a signed token "payload.signature" carrying the user id and expiry ---

def _load_secret() -> bytes:
    if env := os.environ.get("CC_SESSION_SECRET"):
        return env.encode()
    path = Path(__file__).resolve().parent / ".session_secret"
    if not path.exists():
        path.write_text(secrets.token_hex(32))
    return path.read_text().strip().encode()


SECRET = _load_secret()


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _sign(payload: str) -> str:
    return _b64(hmac.new(SECRET, payload.encode(), hashlib.sha256).digest())


def password_fingerprint(password_hash: str) -> str:
    """A short fingerprint of the stored hash. Sessions carry it, so changing the password ends old sessions."""
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def create_session_token(user_id: int, password_hash: str) -> str:
    claims = {"uid": user_id, "pv": password_fingerprint(password_hash), "exp": int(time.time()) + SESSION_TTL_SECONDS}
    payload = _b64(json.dumps(claims).encode())
    return f"{payload}.{_sign(payload)}"


def session_is_current(claims: dict, password_hash: str) -> bool:
    """False if the password changed (e.g. after a reset) since this session was created."""
    return hmac.compare_digest(str(claims.get("pv", "")), password_fingerprint(password_hash))


def read_session_token(token: str) -> dict | None:
    """Return the claims ({"uid", "pv", "exp"}) of a valid, unexpired token, else None."""
    try:
        payload, signature = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(payload), signature):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except ValueError:
        return None
    if data.get("exp", 0) < time.time() or "uid" not in data:
        return None
    return data
