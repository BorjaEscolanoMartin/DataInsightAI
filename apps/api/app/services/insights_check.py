"""Keep only the insights whose figures appear in the data the model received."""

import logging
import re
from typing import Any, NamedTuple

from app.services.numbers import ParsedNumber, find_numbers

logger = logging.getLogger(__name__)

# Small integers are counts written as words ("3 días") and are not checked.
MAX_UNCHECKED_INTEGER = 10
# Dates (2025-11-28) and period labels (2024-10, 2024Q1) are matched whole, not as numbers.
_DATE_OR_PERIOD = re.compile(r"\d{4}(?:-\d{2}(?:-\d{2})?|Q[1-4])")


class Dropped(NamedTuple):
    category: str
    title: str
    missing: list[str]


def _found(number: ParsedNumber, data: list[float]) -> bool:
    if number.value is None:
        return False
    if number.decimals == 0 and abs(number.value) <= MAX_UNCHECKED_INTEGER:
        return True
    # Rounded to the precision the insight uses. Without a sign it may be either ("un 1,9 %
    # menos" for -1,9 %); a written sign must be the data's.
    if number.sign:
        return any(abs(round(d, number.decimals) - number.value) < 1e-9 for d in data)
    return any(abs(round(abs(d), number.decimals) - abs(number.value)) < 1e-9 for d in data)


def check_insights(
    insights: dict[str, Any], data_block: str
) -> tuple[dict[str, Any], list[Dropped]]:
    """The insights without those that quote a figure missing from the data, and what was
    dropped. Dates and periods are not figures, in the data or in the insights."""
    known_dates = set(_DATE_OR_PERIOD.findall(data_block))
    figures = _DATE_OR_PERIOD.sub(" ", data_block)
    data = [n.value for n in find_numbers(figures) if n.value is not None]

    def missing(text: str) -> list[str]:
        text = _DATE_OR_PERIOD.sub(lambda m: " " if m.group() in known_dates else m.group(), text)
        return [n.text for n in find_numbers(text) if not _found(n, data)]

    checked: dict[str, Any] = {}
    dropped: list[Dropped] = []
    for category, items in insights.items():
        checked[category] = []
        for item in items:
            not_found = missing(f"{item['title']}\n{item['description']}")
            if not_found:
                dropped.append(Dropped(category, item["title"], not_found))
                logger.warning(
                    "Insight dropped (%s, %r): figures not in the data: %s",
                    category, item["title"], ", ".join(not_found),
                )
            else:
                checked[category].append(item)
    return checked, dropped
