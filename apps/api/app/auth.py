import threading
import uuid
from time import monotonic
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

# Supabase signs access tokens with ES256 (ECC P-256). The accepted algorithms never come
# from the token or the environment: changing this list requires a reviewed code change.
ALLOWED_ALGORITHMS = ["ES256"]

security = HTTPBearer()


# Minimum gap between two JWKS download attempts, failed ones included: tokens with invented
# kids can force at most one download per cooldown. Supabase's edge caches the JWKS for 10
# minutes, so refetching more often would rarely return new keys.
JWKS_REFETCH_COOLDOWN_SECONDS = 60
# Age after which the JWKS is downloaded again even for a known kid, so a key Supabase revokes
# stops being trusted. Matches the in-memory cache of the Supabase client libraries.
JWKS_MAX_AGE_SECONDS = 600


class JwksUnavailableError(RuntimeError):
    """The JWKS could not be downloaded: a server error, never an invalid token."""


def _download_jwks() -> dict[str | None, dict[str, Any]]:
    """Download Supabase public keys, indexed by kid."""
    url = f"{settings.supabase_auth_url}/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return {k.get("kid"): k for k in resp.json().get("keys", [])}


class _JwksCache:
    """Supabase public keys, downloaded again when they expire or a token names an unknown kid.

    FastAPI runs sync endpoints in a thread pool: lookups of a fresh cached kid read an
    immutable snapshot without locking, and downloads happen under a lock, one at a time.
    """

    def __init__(self) -> None:
        self._keys: dict[str | None, dict[str, Any]] = {}
        self._fetched_at: float | None = None
        self._last_attempt: float | None = None
        self._last_error: Exception | None = None
        self._lock = threading.Lock()

    def key(self, kid: str | None) -> dict[str, Any] | None:
        key = self._fresh_key(kid)
        if key is not None:
            return key
        with self._lock:
            # Another thread may have downloaded the JWKS while this one waited for the lock.
            key = self._fresh_key(kid)
            if key is not None:
                return key
            if self._in_cooldown():
                return self._key_without_download(kid)
            self._last_attempt = monotonic()
            try:
                keys = _download_jwks()
            except Exception as error:
                self._last_error = error
                # Logged once per failed attempt, not per request served with the old keys.
                print(f"[auth] JWKS refresh failed: {error!r}", flush=True)
                key = self._keys.get(kid)
                if key is None:
                    raise
                return key
            self._keys, self._fetched_at, self._last_error = keys, self._last_attempt, None
            return keys.get(kid)

    def _fresh_key(self, kid: str | None) -> dict[str, Any] | None:
        if self._fetched_at is None or monotonic() - self._fetched_at >= JWKS_MAX_AGE_SECONDS:
            return None
        return self._keys.get(kid)

    def _key_without_download(self, kid: str | None) -> dict[str, Any] | None:
        """Answer from the cached keys, even expired ones, when no download is allowed."""
        key = self._keys.get(kid)
        if key is None and self._last_error is not None:
            # The kid may be a new key Supabase published: unknown, not invalid.
            raise JwksUnavailableError("JWKS download failed") from self._last_error
        return key

    def _in_cooldown(self) -> bool:
        return (
            self._last_attempt is not None
            and monotonic() - self._last_attempt < JWKS_REFETCH_COOLDOWN_SECONDS
        )


_jwks_cache = _JwksCache()


def _key_for_token(token: str) -> jwt.PyJWK:
    """Return the Supabase public key whose kid matches the token header.

    PyJWT rejects a kid that is not a string as an invalid token. The key's algorithm comes
    from the JWK, not from the token: a kid naming a non-ES256 key fails the allowlist in
    jwt.decode (an invalid token), while a broken JWK raises PyJWKError (a server error).
    """
    kid = jwt.get_unverified_header(token).get("kid")
    key = _jwks_cache.key(kid)
    if key is None:
        raise jwt.InvalidTokenError(f"No JWKS key found for kid={kid}")
    return jwt.PyJWK.from_dict(key)


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
            # PyJWT accepts a token without exp unless it is required; Supabase always sends
            # all four. PyJWT also rejects a non-string sub and any crit header.
            options={"require": ["exp", "aud", "iss", "sub"]},
        )
    # Only invalid tokens are the client's fault. JWKS download errors (httpx,
    # JwksUnavailableError) and broken JWKs (PyJWKError, InvalidKeyError) are not
    # InvalidTokenError: they stay server errors, not a 401.
    except jwt.InvalidTokenError as e:
        print(f"[auth] InvalidTokenError: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # require guarantees sub is present and PyJWT that it is a string; an empty or malformed
    # sub fails uuid.UUID below.
    user_id: str = payload["sub"]
    try:
        return uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
