import base64
import functools
import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.config import settings

security = HTTPBearer()


@functools.lru_cache(maxsize=1)
def _fetch_jwks() -> dict:
    """Fetch Supabase public keys — cached for the lifetime of the process."""
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _key_for_token(token: str):
    """Return the appropriate verification key based on the JWT header."""
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "HS256")

    if alg in ("RS256", "ES256"):
        kid = header.get("kid")
        jwks = _fetch_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if key is None:
            raise JWTError(f"No JWKS key found for kid={kid}")
        return key, alg

    # HS256 fallback — secret is base64-encoded in Supabase dashboard
    try:
        secret = base64.b64decode(settings.supabase_jwt_secret)
    except Exception:
        secret = settings.supabase_jwt_secret.encode()
    return secret, alg


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> uuid.UUID:
    token = credentials.credentials
    try:
        key, alg = _key_for_token(token)
        payload = jwt.decode(
            token,
            key,
            algorithms=[alg],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return uuid.UUID(user_id)
    except JWTError as e:
        print(f"[auth] JWTError: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
