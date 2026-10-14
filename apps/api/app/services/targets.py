"""Which column the predictions (and the insights' summaries) are about."""

from typing import Any


def measures(profile: dict[str, Any]) -> list[str]:
    """The numeric columns that are not identifiers, in file order."""
    return [
        c["name"] for c in profile.get("columns", [])
        if c["type"] == "numeric" and not c.get("is_identifier")
    ]


def forecast_target(profile: dict[str, Any]) -> str | None:
    """The first numeric column that is not an identifier."""
    return next(iter(measures(profile)), None)


def regression_target(profile: dict[str, Any]) -> str | None:
    """The last numeric column that is not an identifier, when another one can be a feature."""
    numeric = measures(profile)
    return numeric[-1] if len(numeric) >= 2 else None
