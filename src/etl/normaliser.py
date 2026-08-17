from __future__ import annotations

import re

_MONTH_ABBREVS = {
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
}

_TICKER_SUFFIXES = [".NS", ".BO", ".BSE", ".NSE", " BSE", " NSE"]

def normalize_year(raw: str | float | None) -> int | None:

    if raw is None:
        return None

    if isinstance(raw, (int, float)):
        year = int(raw)
        if 1900 <= year <= 2100:
            return year
        return None

    if not isinstance(raw, str):
        return None

    text = raw.strip()
    if not text:
        return None

    if text.upper() in ("TTM", "YEAR", "N/A", "-", "NA"):
        return None

    fy_match = re.match(r"^FY\s*(\d{2,4})$", text, re.IGNORECASE)
    if fy_match:
        return _expand_year(fy_match.group(1))

    range_match = re.match(r"^(\d{4})\s*[-–]\s*(\d{2,4})$", text)
    if range_match:
        return _expand_year(range_match.group(2))

    mon_year = re.match(r"^([A-Za-z]{3})\s*[-/]?\s*(\d{2,4})\b", text)
    if mon_year:
        month_str = mon_year.group(1).lower()
        if month_str in _MONTH_ABBREVS:
            return _expand_year(mon_year.group(2))

    plain = re.match(r"^(\d{4})$", text)
    if plain:
        year = int(plain.group(1))
        if 1900 <= year <= 2100:
            return year

    plain2 = re.match(r"^(\d{2})$", text)
    if plain2:
        return _expand_year(plain2.group(1))

    four_digit = re.search(r"(\d{4})", text)
    if four_digit:
        year = int(four_digit.group(1))
        if 1900 <= year <= 2100:
            return year

    return None

def _expand_year(year_str: str) -> int:

    year = int(year_str)
    if year < 100:
        return year + 2000 if year < 50 else year + 1900
    return year

def normalize_ticker(raw: str | float | None) -> str | None:

    if raw is None:
        return None

    if isinstance(raw, (int, float)):
        raw = str(int(raw)) if isinstance(raw, float) and raw == int(raw) else str(raw)

    if not isinstance(raw, str):
        return None

    text = raw.strip()
    if not text:
        return None

    text = text.upper()

    for suffix in _TICKER_SUFFIXES:
        suffix_upper = suffix.upper()
        if text.endswith(suffix_upper):
            text = text[: -len(suffix_upper)].strip()

    text = re.sub(r"\s+", " ", text).strip()

    return text if text else None