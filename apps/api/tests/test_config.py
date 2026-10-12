import pytest
from pydantic import ValidationError

from app.config import Settings


def _settings() -> Settings:
    return Settings(_env_file=None)


def test_requires_supabase_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        _settings()


@pytest.mark.parametrize(
    "url",
    ["", "http://example.supabase.co", "https:///"],
    ids=["empty", "http", "only-slashes"],
)
def test_rejects_supabase_url_that_is_not_https(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv("SUPABASE_URL", url)

    with pytest.raises(ValidationError):
        _settings()


def test_accepts_https_supabase_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://abcdefgh.supabase.co")

    assert _settings().supabase_url == "https://abcdefgh.supabase.co"


@pytest.mark.parametrize(
    "url",
    ["https://abcdefgh.supabase.co/", "https://abcdefgh.supabase.co///"],
    ids=["one-slash", "several-slashes"],
)
def test_strips_trailing_slashes_from_supabase_url(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setenv("SUPABASE_URL", url)

    assert _settings().supabase_url == "https://abcdefgh.supabase.co"
