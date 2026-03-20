import hashlib
import secrets
from datetime import datetime, timedelta, timezone


def generate_invite_token() -> str:
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def utc_now():
    return datetime.now(timezone.utc)


def utc_plus_hours(hours: int):
    return utc_now() + timedelta(hours=hours)