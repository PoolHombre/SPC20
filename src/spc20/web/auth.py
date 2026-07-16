"""Dashboard authentication.

Password is stored as a bcrypt hash in the DASHBOARD_PASSWORD_HASH env var.
If bcrypt is not available, falls back to a constant-time HMAC comparison
against the raw password in DASHBOARD_PASSWORD env var (not recommended for
production but acceptable for bench/lab environments).

SECURITY: Never log or return the password hash or raw password.
"""
from __future__ import annotations
import functools
import hashlib
import hmac
import logging
import os
from typing import Callable

from flask import request, Response

log = logging.getLogger(__name__)

_BCRYPT_AVAILABLE = False
try:
    import bcrypt as _bcrypt  # type: ignore
    _BCRYPT_AVAILABLE = True
except ImportError:
    pass


def _check_bcrypt(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode(), hashed.encode())


def _check_hmac(password: str, expected: str) -> bool:
    """Constant-time comparison — resistant to timing attacks."""
    return hmac.compare_digest(
        hashlib.sha256(password.encode()).digest(),
        hashlib.sha256(expected.encode()).digest(),
    )


def verify_password(password: str) -> bool:
    """Return True if the provided password matches the configured credential."""
    stored_hash = os.getenv("DASHBOARD_PASSWORD_HASH", "")
    if stored_hash and _BCRYPT_AVAILABLE:
        try:
            return _check_bcrypt(password, stored_hash)
        except Exception:
            log.warning("bcrypt check failed — falling back to hmac comparison")

    # Fallback: compare against raw password env var (constant-time)
    raw_password = os.getenv("DASHBOARD_PASSWORD", "")
    if not raw_password:
        # No credentials configured — allow access (local-only, no external access assumed)
        log.warning("No DASHBOARD_PASSWORD_HASH or DASHBOARD_PASSWORD set — dashboard is open.")
        return True
    return _check_hmac(password, raw_password)


def require_auth(f: Callable) -> Callable:
    """Decorator: require HTTP Basic Auth for protected routes."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and verify_password(auth.password):
            return f(*args, **kwargs)
        return Response(
            "Authentication required.",
            401,
            {"WWW-Authenticate": 'Basic realm="SPC 2.0 Dashboard"'},
        )
    return decorated
