import base64
import copy
import hashlib
import hmac
import json
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

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


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unsigned_token(header: dict[str, Any], claims: dict[str, Any]) -> str:
    def segment(data: dict[str, Any]) -> str:
        return _b64url(json.dumps(data).encode())

    return f"{segment(header)}.{segment(claims)}."


# Tokens are signed by hand, not with the JWT library under test: the tests then check it
# independently, and they can build tokens a library refuses to sign (an empty HMAC key, a
# kid that is not a string, a PEM public key as HMAC secret).
def _signed_token(
    alg: str,
    claims: dict[str, Any],
    sign: Callable[[bytes], bytes],
    kid: Any = None,
    **extra_headers: Any,
) -> str:
    header: dict[str, Any] = {"alg": alg, "typ": "JWT"}
    if kid is not None:
        header["kid"] = kid
    header.update(extra_headers)
    signing_input = _unsigned_token(header, claims)[:-1]
    return f"{signing_input}.{_b64url(sign(signing_input.encode()))}"


def _hmac_token(claims: dict[str, Any], secret: bytes, kid: str | None = None) -> str:
    def sign(data: bytes) -> bytes:
        return hmac.new(secret, data, hashlib.sha256).digest()

    return _signed_token("HS256", claims, sign, kid=kid)


def _rs256_token(claims: dict[str, Any], key: rsa.RSAPrivateKey, kid: str) -> str:
    def sign(data: bytes) -> bytes:
        return key.sign(data, padding.PKCS1v15(), hashes.SHA256())

    return _signed_token("RS256", claims, sign, kid=kid)


def _es256_token(
    claims: dict[str, Any],
    key: ec.EllipticCurvePrivateKey,
    kid: Any = KID,
    **extra_headers: Any,
) -> str:
    def sign(data: bytes) -> bytes:
        # JWS ES256 signatures are the raw 32-byte r and s, not the DER cryptography returns.
        r, s = decode_dss_signature(key.sign(data, ec.ECDSA(hashes.SHA256())))
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")

    return _signed_token("ES256", claims, sign, kid=kid, **extra_headers)


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
    token = _hmac_token(_claims(), legacy_secret)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_hs256_token_signed_with_empty_key(
    monkeypatch: pytest.MonkeyPatch, jwks: dict[str, Any]
) -> None:
    # Guards against bringing back the HS256 secret branch with an empty secret. The app no
    # longer reads this injected setting; the RS256 test guards the algorithm allowlist.
    monkeypatch.setitem(vars(settings), "supabase_jwt_secret", "")
    token = _hmac_token(_claims(), b"")

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


def test_rejects_rs256_token_even_with_a_published_rsa_key(jwks: dict[str, Any]) -> None:
    rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks["keys"].append(_rsa_public_jwk(rsa_key, "test-rs256-key"))
    token = _rs256_token(_claims(), rsa_key, kid="test-rs256-key")

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
    pem: regression for CVE-2024-33663 (PEM public keys accepted as HMAC secrets).
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
    token = _es256_token(_claims(), signing_key, kid=kid)

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


@pytest.mark.parametrize(
    "crit, extension",
    [(["exp"], {}), (["urn:example:must-understand"], {"urn:example:must-understand": True})],
    ids=["registered-claim", "unknown-extension"],
)
def test_rejects_token_with_a_crit_header(
    jwks: dict[str, Any],
    signing_key: ec.EllipticCurvePrivateKey,
    crit: list[str],
    extension: dict[str, Any],
) -> None:
    # RFC 7515 4.1.11: a token whose crit names an extension we do not process must be rejected.
    token = _es256_token(_claims(), signing_key, crit=crit, **extension)

    with pytest.raises(HTTPException) as exc_info:
        _authenticate(token)

    assert exc_info.value.status_code == 401


@pytest.mark.parametrize(
    "breakage",
    [
        {"x": _b64url_uint(0, 32), "y": _b64url_uint(0, 32)},  # (0, 0) is not on P-256
        {"x": None},
        {"kty": None},
    ],
    ids=["point-off-the-curve", "missing-x", "missing-kty"],
)
def test_broken_jwks_key_is_a_server_error_and_good_keys_still_work(
    jwks: dict[str, Any], signing_key: ec.EllipticCurvePrivateKey, breakage: dict[str, Any]
) -> None:
    # A key Supabase publishes broken is a server fault, not an invalid client token.
    broken_key: dict[str, Any] = _ec_public_jwk(
        ec.generate_private_key(ec.SECP256R1()), "broken-key"
    )
    for field, value in breakage.items():
        if value is None:
            del broken_key[field]
        else:
            broken_key[field] = value
    jwks["keys"].append(broken_key)

    with pytest.raises(Exception) as exc_info:
        _authenticate(_es256_token(_claims(), signing_key, kid="broken-key"))
    assert not isinstance(exc_info.value, HTTPException)

    user_id = uuid.uuid4()
    assert _authenticate(_es256_token(_claims(sub=str(user_id)), signing_key)) == user_id
