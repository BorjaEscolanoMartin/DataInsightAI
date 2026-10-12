import functools
import uuid
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


@functools.lru_cache(maxsize=1)
def _fetch_jwks() -> dict:
    """Fetch Supabase public keys — cached for the lifetime of the process."""
    url = f"{settings.supabase_auth_url}/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _key_for_token(token: str) -> dict[str, Any]:
    """Return the Supabase public key whose kid matches the token header."""
    kid = jwt.get_unverified_header(token).get("kid")
    key = next((k for k in _fetch_jwks().get("keys", []) if k.get("kid") == kid), None)
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
