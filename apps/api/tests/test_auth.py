import base64
import copy
import hashlib
import hmac
import json
import threading
import time
import uuid
from typing import Any

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app import auth
from app.config import settings

KID = "test-es256-key"
# conftest.py sets SUPABASE_URL to https://example.supabase.co.
ISSUER = "https://example.supabase.co/auth/v1"
# Minimum gap between two JWKS download attempts (S3).
COOLDOWN_SECONDS = 60
# Age after which the cached JWKS is downloaded again even for a known kid (S4).
MAX_AGE_SECONDS = 600
STALE_KEYS_WARNING = "[auth] JWKS refresh failed"


def _b64url_uint(value: int, length: int) -> str:
    return base64.urlsafe_b64encode(value.to_bytes(length, "big")).rstrip(b"=").decode()


def _private_pem(key: ec.EllipticCurvePrivateKey | rsa.RSAPrivateKey) -> str:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def _ec_public_jwk(key: ec.EllipticCurvePrivateKey, kid: str) -> dict[str, str]:
    numbers = key.public_key().public_numbers()
    return {
        "kty": "EC",
        "crv": "P-256",
        "alg": "ES256",
        "use": "sig",
        "kid": kid,
        "x": _b64url_uint(numbers.x, 32),
        "y": _b64url_uint(numbers.y, 32),
    }


def _rsa_public_jwk(key: rsa.RSAPrivateKey, kid: str) -> dict[str, str]:
    numbers = key.public_key().public_numbers()
    return {
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "kid": kid,
        "n": _b64url_uint(numbers.n, (numbers.n.bit_length() + 7) // 8),
        "e": _b64url_uint(numbers.e, (numbers.e.bit_length() + 7) // 8),
    }


def _claims(**overrides: Any) -> dict[str, Any]:
    claims: dict[str, Any] = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "exp": int(time.time()) + 300,
        "iss": ISSUER,
    }
    claims.update(overrides)
    return claims


def _unsigned_token(header: dict[str, Any], claims: dict[str, Any]) -> str:
    def segment(data: dict[str, Any]) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    return f"{segment(header)}.{segment(claims)}."


def _hmac_token(claims: dict[str, Any], secret: bytes, kid: str) -> str:
    """Sign HS256 by hand: python-jose refuses PEM public keys as HMAC secrets."""
    signing_input = _unsigned_token({"alg": "HS256", "typ": "JWT", "kid": kid}, claims)[:-1]
    digest = hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return f"{signing_input}.{signature}"


def _es256_token(
    claims: dict[str, Any], key: ec.EllipticCurvePrivateKey, kid: str | None = KID
) -> str:
    headers = {"kid": kid} if kid is not None else None
    return jwt.encode(claims, _private_pem(key), algorithm="ES256", headers=headers)


def _authenticate(token: str) -> uuid.UUID:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return auth.get_current_user(credentials)


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


@pytest.fixture
def signing_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


class _JwksServer:
    """Fake Supabase JWKS endpoint that counts downloads and serves a fresh copy each time."""

    def __init__(self, keys: dict[str, Any]) -> None:
        self.keys = keys
        self.downloads = 0
        self.error: Exception | None = None
        # When set, a download blocks until the test releases it.
        self.gate: threading.Event | None = None
        self.entered = threading.Event()
        self._lock = threading.Lock()

    def get(self, *args: Any, **kwargs: Any) -> _FakeResponse:
        with self._lock:
            self.downloads += 1
        self.entered.set()
        if self.gate is not None:
            self.gate.wait(timeout=5)
        if self.error is not None:
            raise self.error
        return _FakeResponse(copy.deepcopy(self.keys))


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    """Control the monotonic clock the JWKS cache uses for its cooldown."""
    fake = _Clock()
    monkeypatch.setattr(auth, "monotonic", fake)
    return fake


@pytest.fixture
def jwks_server(
    monkeypatch: pytest.MonkeyPatch, signing_key: ec.EllipticCurvePrivateKey
) -> _JwksServer:
    """Serve a JWKS with the test ES256 key instead of calling Supabase."""
    server = _JwksServer({"keys": [_ec_public_jwk(signing_key, KID)]})
    monkeypatch.setattr(auth.httpx, "get", server.get)
    monkeypatch.setattr(auth, "_jwks_cache", auth._JwksCache())
    return server


@pytest.fixture
def jwks(jwks_server: _JwksServer) -> dict[str, Any]:
    return jwks_server.keys


def test_rejects_hs256_token_signed_with_legacy_secret(
    monkeypatch: pytest.MonkeyPatch, jwks: dict[str, Any]
) -> None:
    legacy_secret = b"legacy-supabase-hs256-secret-0123456789"
    # Guards against bringing back the HS256 secret branch: the app no longer reads this
    # injected setting. The algorithm allowlist itself is guarded by the RS256 test.
    monkeypatch.setitem(
        vars(settings), "supabase_jwt_secret", base64.b64encode(legacy_secret).decode()
    )
    token = jwt.encode(_claims(), legacy_secret, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_hs256_token_signed_with_empty_key(
    monkeypatch: pytest.MonkeyPatch, jwks: dict[str, Any]
) -> None:
    # Guards against bringing back the HS256 secret branch with an empty secret. The app no
    # longer reads this injected setting; the RS256 test guards the algorithm allowlist.
    monkeypatch.setitem(vars(settings), "supabase_jwt_secret", "")
    token = jwt.encode(_claims(), b"", algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_rs256_token_even_with_a_published_rsa_key(jwks: dict[str, Any]) -> None:
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks["keys"].append(_rsa_public_jwk(rsa_key, "test-rs256-key"))
    token = jwt.encode(
        _claims(),
        _private_pem(rsa_key),
        algorithm="RS256",
        headers={"kid": "test-rs256-key"},
    )

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_unsigned_token_with_alg_none(jwks: dict[str, Any]) -> None:
    token = _unsigned_token({"alg": "none", "typ": "JWT", "kid": KID}, _claims())

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(
    "encoding, public_format",
    [
        (serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
        (serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo),
    ],
    ids=["der", "pem"],
)
def test_rejects_hs256_token_signed_with_the_jwks_public_key(
    jwks: dict[str, Any],
    signing_key: ec.EllipticCurvePrivateKey,
    encoding: serialization.Encoding,
    public_format: serialization.PublicFormat,
) -> None:
    """Algorithm confusion: an attacker uses the published public key as the HMAC secret.

    der: regression for CVE-2026-85394, GHSA-3qf3-8w2g-rqmx (DER keys without PEM armor).
    pem: regression for CVE-2024-33663. Redundant with der while we use python-jose,
    which already refuses PEM keys as HMAC secrets; kept to check the switch to PyJWT.
    """
    public_key = signing_key.public_key().public_bytes(encoding, public_format)
    token = _hmac_token(_claims(), public_key, kid=KID)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_that_is_not_a_jwt(jwks: dict[str, Any]) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _authenticate("abc")

    assert exc_info.value.status_code == 401


def test_accepts_valid_es256_token(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    user_id = uuid.uuid4()
    token = _es256_token(_claims(sub=str(user_id)), signing_key)

    assert _authenticate(token) == user_id


def test_rejects_expired_token(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    token = _es256_token(_claims(exp=int(time.time()) - 3600), signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_for_another_audience(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    token = _es256_token(_claims(aud="another-audience"), signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_from_another_issuer(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    token = _es256_token(_claims(iss="https://another.supabase.co/auth/v1"), signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize("claim", ["exp", "aud", "iss"])
def test_rejects_token_missing_a_required_claim(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey, claim: str
) -> None:
    claims = _claims()
    del claims[claim]
    token = _es256_token(claims, signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_without_sub(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    claims = _claims()
    del claims["sub"]
    token = _es256_token(claims, signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_whose_sub_is_not_a_uuid(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    token = _es256_token(_claims(sub="admin"), signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_whose_sub_is_not_a_string(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    token = _es256_token(_claims(sub=123), signing_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize("kid", ["unknown-kid", None], ids=["unknown", "missing"])
def test_rejects_token_whose_kid_is_not_in_the_jwks(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey, kid: str | None
) -> None:
    token = _es256_token(_claims(), signing_key, kid=kid)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(
    "kid", [[KID], {"kid": KID}], ids=["list", "object"]
)
def test_rejects_token_whose_kid_is_not_a_string(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey, kid: Any
) -> None:
    # The kid comes from the unverified header: a malformed one is a bad token, not a 500.
    token = jwt.encode(
        _claims(), _private_pem(signing_key), algorithm="ES256", headers={"kid": kid}
    )

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_token_signed_by_another_key_with_a_known_kid(jwks: dict[str, Any]) -> None:
    attacker_key = ec.generate_private_key(ec.SECP256R1())
    token = _es256_token(_claims(), attacker_key)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_jwks_download_failure_is_not_reported_as_401(
    monkeypatch: pytest.MonkeyPatch,
    jwks: dict[str, Any],
    signing_key: ec.EllipticCurvePrivateKey,
) -> None:
    # A Supabase outage is a server error, not an invalid client token.
    def unavailable(*args: Any, **kwargs: Any) -> None:
        raise httpx.ConnectError("Supabase unavailable")

    monkeypatch.setattr(auth.httpx, "get", unavailable)
    token = _es256_token(_claims(), signing_key)

    with pytest.raises(httpx.HTTPError):
        _authenticate(token)


def test_rejects_es256_token_whose_kid_names_a_non_ec_key(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    # The client chooses the kid: pointing it at an RSA key is a bad token, not a server error.
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks["keys"].append(_rsa_public_jwk(rsa_key, "test-rs256-key"))
    token = _es256_token(_claims(), signing_key, kid="test-rs256-key")

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_jwks_that_is_not_json_is_not_reported_as_401(
    monkeypatch: pytest.MonkeyPatch,
    jwks: dict[str, Any],
    signing_key: ec.EllipticCurvePrivateKey,
) -> None:
    # A broken JWKS response is Supabase's fault: it must surface as a server error.
    json_calls: list[None] = []

    class _HtmlResponse(_FakeResponse):
        def json(self) -> dict[str, Any]:
            json_calls.append(None)
            raise json.JSONDecodeError("Expecting value", "<html>", 0)

    monkeypatch.setattr(auth.httpx, "get", lambda *args, **kwargs: _HtmlResponse({}))
    token = _es256_token(_claims(), signing_key)

    with pytest.raises(Exception) as exc_info:
        _authenticate(token)

    error = exc_info.value
    assert not (isinstance(error, HTTPException) and error.status_code == 401)
    # The failure must come from parsing the JWKS, not from an unrelated error.
    assert len(json_calls) == 1


def test_fetches_jwks_from_the_supabase_auth_url(
    monkeypatch: pytest.MonkeyPatch, jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey
) -> None:
    urls: list[str] = []

    def fake_get(url: str, *args: Any, **kwargs: Any) -> _FakeResponse:
        urls.append(url)
        return _FakeResponse(jwks)

    monkeypatch.setattr(auth.httpx, "get", fake_get)
    _authenticate(_es256_token(_claims(), signing_key))

    assert urls == [f"{ISSUER}/.well-known/jwks.json"]


def test_accepts_token_signed_with_a_key_published_after_the_first_download(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    new_key = ec.generate_private_key(ec.SECP256R1())
    jwks_server.keys["keys"].append(_ec_public_jwk(new_key, "rotated-key"))
    clock.now += COOLDOWN_SECONDS + 1
    user_id = uuid.uuid4()

    token = _es256_token(_claims(sub=str(user_id)), new_key, kid="rotated-key")

    assert _authenticate(token) == user_id
    assert jwks_server.downloads == 2


def test_unknown_kids_within_the_cooldown_do_not_download_the_jwks_again(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    clock.now += COOLDOWN_SECONDS - 1

    for i in range(5):
        with pytest.raises(HTTPException) as exc_info:
            _authenticate(_es256_token(_claims(), signing_key, kid=f"invented-{i}"))
        assert exc_info.value.status_code == 401

    assert jwks_server.downloads == 1


def test_unknown_kid_after_the_cooldown_downloads_the_jwks_again(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    clock.now += COOLDOWN_SECONDS + 1

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(_es256_token(_claims(), signing_key, kid="invented"))

    assert exc_info.value.status_code == 401
    assert jwks_server.downloads == 2


def test_jwks_refresh_failure_on_unknown_kid_is_not_reported_as_401(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    jwks_server.error = httpx.ConnectError("Supabase unavailable")
    clock.now += COOLDOWN_SECONDS + 1

    with pytest.raises(httpx.HTTPError):
        _authenticate(_es256_token(_claims(), signing_key, kid="rotated-key"))

    assert jwks_server.downloads == 2


def test_failed_download_counts_for_the_cooldown_and_is_not_reported_as_401(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    jwks_server.error = httpx.ConnectError("Supabase unavailable")
    token = _es256_token(_claims(), signing_key)
    with pytest.raises(httpx.HTTPError):
        _authenticate(token)
    clock.now += COOLDOWN_SECONDS - 1

    with pytest.raises(auth.JwksUnavailableError) as exc_info:
        _authenticate(token)

    assert exc_info.value.__cause__ is jwks_server.error
    assert jwks_server.downloads == 1


def test_concurrent_requests_with_a_new_kid_download_the_jwks_once(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    new_key = ec.generate_private_key(ec.SECP256R1())
    jwks_server.keys["keys"].append(_ec_public_jwk(new_key, "rotated-key"))
    clock.now += COOLDOWN_SECONDS + 1
    token = _es256_token(_claims(), new_key, kid="rotated-key")
    jwks_server.gate = threading.Event()
    jwks_server.entered.clear()
    results: list[object] = []

    def authenticate() -> None:
        try:
            results.append(_authenticate(token))
        except Exception as error:
            results.append(error)

    threads = [threading.Thread(target=authenticate) for _ in range(8)]
    for thread in threads:
        thread.start()
    # Hold the refresh open so the other threads pile up behind it.
    jwks_server.entered.wait(timeout=5)
    threading.Event().wait(0.1)
    jwks_server.gate.set()
    for thread in threads:
        thread.join(timeout=5)

    assert all(isinstance(result, uuid.UUID) for result in results), results
    assert len(results) == 8
    assert jwks_server.downloads == 2


def test_key_removed_from_the_jwks_is_rejected_after_the_max_age(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    token = _es256_token(_claims(), signing_key)
    _authenticate(token)
    jwks_server.keys["keys"] = []
    clock.now += MAX_AGE_SECONDS + 1

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401
    assert jwks_server.downloads == 2


def test_cached_key_is_used_with_a_warning_when_the_refresh_after_the_max_age_fails(
    jwks_server: _JwksServer,
    signing_key: ec.EllipticCurvePrivateKey,
    clock: _Clock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    user_id = uuid.uuid4()
    token = _es256_token(_claims(sub=str(user_id)), signing_key)
    _authenticate(token)
    jwks_server.error = httpx.ConnectError("Supabase unavailable")
    clock.now += MAX_AGE_SECONDS + 1
    capsys.readouterr()

    # The request that attempts the refresh, then one inside the cooldown that follows it.
    assert _authenticate(token) == user_id
    assert _authenticate(token) == user_id

    assert jwks_server.downloads == 2
    # One line per failed refresh, not per request: an outage must not flood the logs.
    assert capsys.readouterr().out.count(STALE_KEYS_WARNING) == 1


def test_unknown_kid_when_the_refresh_after_the_max_age_fails_is_not_reported_as_401(
    jwks_server: _JwksServer, signing_key: ec.EllipticCurvePrivateKey, clock: _Clock
) -> None:
    _authenticate(_es256_token(_claims(), signing_key))
    jwks_server.error = httpx.ConnectError("Supabase unavailable")
    clock.now += MAX_AGE_SECONDS + 1

    with pytest.raises(httpx.HTTPError):
        _authenticate(_es256_token(_claims(), signing_key, kid="rotated-key"))

    assert jwks_server.downloads == 2
