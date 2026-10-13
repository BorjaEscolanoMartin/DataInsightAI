"""Which column the predictions (and the insights' summaries) are about."""

from typing import Any


def _numeric(profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [c for c in profile.get("columns", []) if c["type"] == "numeric"]


def forecast_target(profile: dict[str, Any]) -> str | None:
    """The first numeric column that is not an identifier."""
    return next((c["name"] for c in _numeric(profile) if not c.get("is_identifier")), None)


def regression_target(profile: dict[str, Any]) -> str | None:
    """The last numeric column, when there is another one to use as a feature."""
    numeric = _numeric(profile)
    return numeric[-1]["name"] if len(numeric) >= 2 else None
