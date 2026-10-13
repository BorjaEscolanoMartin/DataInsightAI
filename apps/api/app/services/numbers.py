"""Spanish number and date format: one rule to write them for the LLM and to read them back."""

import re
from typing import NamedTuple

# Thousands with points, decimals with a comma: 8.734,60, 0,92, -1.234.567,9.
_SPANISH_NUMBER = re.compile(r"-?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?")
# Any run of digits, points and commas, also when glued to letters (12h, Q3), so no figure
# escapes the check. A sign counts only when it does not follow a word or a number: the
# hyphen in 163-239 or 2024-2025 is not a minus.
_NUMBER_TOKEN = re.compile(r"(?:(?<!\w)[-+])?\d(?:[\d.,]*\d)?")


class ParsedNumber(NamedTuple):
    text: str
    # None when the text is a number in another format (0.92, 1,234.56).
    value: float | None
    decimals: int
    # "+" or "-" when the text writes the sign, "" otherwise.
    sign: str = ""


def format_es(value: float, decimals: int = 0) -> str:
    text = f"{value:,.{decimals}f}"
    if text.startswith("-") and not text.strip("-0.,"):
        text = text[1:]  # -0,00
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def parse_es(text: str) -> float:
    if not _SPANISH_NUMBER.fullmatch(text):
        raise ValueError(f"Not a number in Spanish format: {text!r}")
    return float(text.replace(".", "").replace(",", "."))


def find_numbers(text: str) -> list[ParsedNumber]:
    found = []
    for token in _NUMBER_TOKEN.findall(text):
        sign = token[0] if token[0] in "+-" else ""
        try:
            value: float | None = parse_es(token.removeprefix("+"))
        except ValueError:
            value = None
        decimals = len(token.split(",")[1]) if value is not None and "," in token else 0
        found.append(ParsedNumber(token, value, decimals, sign))
    return found


MONTHS_ES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
# What format_day_es and format_period_es write: 28 nov 2025, oct 2024, T1 2024.
SPANISH_DATE = re.compile(rf"(?:\d{{1,2}} )?(?:{'|'.join(MONTHS_ES)}) \d{{4}}|T[1-4] \d{{4}}")


def format_day_es(iso_date: str) -> str:
    year, month, day = iso_date.split("-")
    return f"{int(day)} {MONTHS_ES[int(month) - 1]} {year}"


def format_period_es(label: str) -> str:
    """A pandas period label: 2024-10 (month), 2024Q1 (quarter) or 2024 (year)."""
    if "Q" in label:
        year, quarter = label.split("Q")
        return f"T{quarter} {year}"
    if "-" in label:
        year, month = label.split("-")
        return f"{MONTHS_ES[int(month) - 1]} {year}"
    return label
