import threading
import uuid
from time import monotonic
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.exceptions import JOSEError

from app.config import settings

# Supabase signs access tokens with ES256 (ECC P-256). The accepted algorithms never come
# from the token or the environment: changing this list requires a reviewed code change.
ALLOWED_ALGORITHMS = ["ES256"]

security = HTTPBearer()


# Minimum gap between two JWKS download attempts, failed ones included: tokens with invented
# kids can force at most one download per cooldown. Supabase's edge caches the JWKS for 10
# minutes, so refetching more often would rarely return new keys.
JWKS_REFETCH_COOLDOWN_SECONDS = 60


class JwksUnavailableError(RuntimeError):
    """The JWKS could not be downloaded: a server error, never an invalid token."""


def _download_jwks() -> dict[str | None, dict[str, Any]]:
    """Download Supabase public keys, indexed by kid."""
    url = f"{settings.supabase_auth_url}/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return {k.get("kid"): k for k in resp.json().get("keys", [])}


class _JwksCache:
    """Supabase public keys, downloaded again when a token names an unknown kid.

    FastAPI runs sync endpoints in a thread pool: lookups of a cached kid read an immutable
    snapshot without locking, and downloads happen under a lock, one at a time.
    """

    def __init__(self) -> None:
        self._keys: dict[str | None, dict[str, Any]] = {}
        self._last_attempt: float | None = None
        self._last_error: Exception | None = None
        self._lock = threading.Lock()

    def key(self, kid: str | None) -> dict[str, Any] | None:
        key = self._keys.get(kid)
        if key is not None:
            return key
        with self._lock:
            # Another thread may have downloaded the JWKS while this one waited for the lock.
            key = self._keys.get(kid)
            if key is not None:
                return key
            if self._in_cooldown():
                if self._last_error is not None:
                    raise JwksUnavailableError("JWKS download failed") from self._last_error
                return None
            self._last_attempt = monotonic()
            try:
                self._keys = _download_jwks()
            except Exception as error:
                self._last_error = error
                raise
            self._last_error = None
            return self._keys.get(kid)

    def _in_cooldown(self) -> bool:
        return (
            self._last_attempt is not None
            and monotonic() - self._last_attempt < JWKS_REFETCH_COOLDOWN_SECONDS
        )


_jwks_cache = _JwksCache()


def _key_for_token(token: str) -> dict[str, Any]:
    """Return the Supabase public key whose kid matches the token header."""
    kid = jwt.get_unverified_header(token).get("kid")
    key = _jwks_cache.key(kid)
    if key is None:
        raise JWTError(f"No JWKS key found for kid={kid}")
    return key


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            _key_for_token(token),
            algorithms=ALLOWED_ALGORITHMS,
            audience="authenticated",
            issuer=settings.supabase_auth_url,
            # python-jose only checks these claims when present; Supabase always sends them.
            options={
                "require_exp": True,
                "require_aud": True,
                "require_iss": True,
                "require_sub": True,
            },
        )
    # Any token python-jose cannot process is the client's fault. JWKS download errors
    # (httpx) are not caught here: a Supabase outage is a server error, not a 401.
    except JOSEError as e:
        print(f"[auth] JOSEError: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # require_sub guarantees the claim; an empty or malformed sub fails uuid.UUID below.
    user_id: str = payload["sub"]
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
