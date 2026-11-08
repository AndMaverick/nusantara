"""nusantara: Indonesian text and number utilities for AI pipelines. Rupiah, slang, dates, phone numbers."""

from __future__ import annotations

import re
from datetime import date

__version__ = "0.1.0"

UNITS = {"triliun": 1e12, "miliar": 1e9, "milyar": 1e9, "juta": 1e6, "jt": 1e6, "ribu": 1e3, "rb": 1e3, "k": 1e3}
AMOUNT = re.compile(r"(?i)(?:rp\.?\s*)?(\d[\d.,]*)\s*(triliun|miliar|milyar|juta|jt|ribu|rb|k)?(?![A-Za-z0-9])")

MONTHS = ["januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus",
          "september", "oktober", "november", "desember"]
MONTH_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6, "jul": 7, "agu": 8, "agt": 8,
              "sep": 9, "okt": 10, "nov": 11, "des": 12}
DATE = re.compile(r"(?i)\b(\d{1,2})\s+([a-z]+)\s+(\d{4})\b")

SLANG = {
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "enggak": "tidak", "tdk": "tidak",
    "udah": "sudah", "udh": "sudah", "sdh": "sudah", "bgt": "sangat", "banget": "sangat",
    "aja": "saja", "gimana": "bagaimana", "yg": "yang", "dgn": "dengan", "utk": "untuk",
    "krn": "karena", "jg": "juga", "sy": "saya", "emang": "memang", "kalo": "kalau",
}
WORD = re.compile(r"[A-Za-z]+")


def _number(raw: str) -> float:
    raw = raw.strip(".,")
    if "," in raw:
        return float(raw.replace(".", "").replace(",", "."))
    if raw.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
        return float(raw.replace(".", ""))
    return float(raw)


def parse_rupiah(text: str):
    """First amount in the text, as a number of rupiah. Handles Rp 1.500.000, 1,5 juta, 500 rb, 2 miliar."""
    for match in AMOUNT.finditer(text):
        number, unit = match.group(1), match.group(2)
        if not unit and not re.search(r"(?i)rp", match.group(0)) and not re.fullmatch(r"\d{1,3}(\.\d{3})+", number):
            continue
        value = _number(number) * (UNITS[unit.lower()] if unit else 1)
        return int(value) if value == int(value) else value
    raise ValueError(f"no rupiah amount found in: {text!r}")


def format_rupiah(amount: float) -> str:
    sign = "-" if amount < 0 else ""
    return f"{sign}Rp {abs(round(amount)):,}".replace(",", ".")


def normalize_slang(text: str) -> str:
    """Replace common chat abbreviations with standard Indonesian. Case-insensitive, other text untouched."""
    return WORD.sub(lambda m: SLANG.get(m.group(0).lower(), m.group(0)), text)


def parse_date(text: str) -> date:
    """Find a date like '17 Agustus 2026' or '17 Agu 2026'."""
    for match in DATE.finditer(text):
        day, name, year = int(match.group(1)), match.group(2).lower(), int(match.group(3))
        month = MONTH_ABBR.get(name[:3]) if name[:3] in MONTH_ABBR and (name in MONTHS or len(name) == 3) else None
        if name in MONTHS:
            month = MONTHS.index(name) + 1
        if month:
            return date(year, month, day)
    raise ValueError(f"no Indonesian date found in: {text!r}")


def format_date(value: date) -> str:
    return f"{value.day} {MONTHS[value.month - 1].capitalize()} {value.year}"


def normalize_phone(raw: str) -> str:
    """Canonical +62 form for Indonesian numbers."""
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("62"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    else:
        raise ValueError(f"not an Indonesian number: {raw!r}")
    if not 8 <= len(digits) <= 12:
        raise ValueError(f"unexpected length for an Indonesian number: {raw!r}")
    return "+62" + digits
