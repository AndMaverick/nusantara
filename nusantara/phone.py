"""Indonesian phone numbers: normalize any written form to +62, classify mobile, landline or toll-free, hint the operator from the prefix,
and print in the national or international style."""
from __future__ import annotations

import re
from dataclasses import dataclass

# Mobile prefixes by operator (the 3-digit block after the leading 0). A prefix says who was allocated the block, not who serves the
# number today: with number portability the real operator can differ.
_OPERATORS: dict[str, tuple[str, ...]] = {
    "Telkomsel": ("811", "812", "813", "821", "822", "823", "851", "852", "853"),
    "Indosat": ("814", "815", "816", "855", "856", "857", "858"),
    "XL": ("817", "818", "819", "859", "877", "878"),
    "Axis": ("831", "832", "833", "838"),
    "Tri": ("895", "896", "897", "898", "899"),
    "Smartfren": ("881", "882", "883", "884", "885", "886", "887", "888", "889"),
}
OPERATOR_BY_PREFIX = {prefix: name for name, prefixes in _OPERATORS.items() for prefix in prefixes}

# Landline area codes without the leading 0 (the larger cities; a landline has a 1 to 3 digit code after the 0).
AREA_CODES = {
    "21": "Jakarta", "22": "Bandung", "24": "Semarang", "31": "Surabaya", "61": "Medan", "274": "Yogyakarta", "361": "Denpasar",
    "411": "Makassar", "251": "Bogor", "711": "Palembang", "751": "Padang", "561": "Pontianak", "541": "Samarinda", "542": "Balikpapan",
    "341": "Malang", "271": "Surakarta",
}


@dataclass(frozen=True)
class PhoneNumber:
    e164: str            # +6281234567890
    kind: str            # "mobile", "landline", "toll-free" or "other"
    national: str        # digits after +62, no leading 0
    operator: str | None  # mobile only, by prefix allocation
    area: str | None      # landline only, when the area code is in the table

    def format(self, style: str = "international") -> str:
        """``international``: +62 812-3456-7890. ``national``: 0812-3456-7890. ``e164``: +6281234567890."""
        if style == "e164":
            return self.e164
        if style not in ("international", "national"):
            raise ValueError(f"style must be international, national or e164, not {style!r}")
        digits = self.national
        if self.kind in ("mobile", "toll-free"):
            groups = [digits[:3], digits[3:7], digits[7:]]
        elif self.kind == "landline":
            code = next((c for c in sorted(AREA_CODES, key=len, reverse=True) if digits.startswith(c)), digits[:2])
            rest = digits[len(code):]
            groups = [code, rest[:len(rest) // 2 + len(rest) % 2], rest[len(rest) // 2 + len(rest) % 2:]]
        else:
            groups = [digits]
        body = "-".join(g for g in groups if g)
        return f"+62 {body}" if style == "international" else f"0{body}"


def parse_phone(raw: str) -> PhoneNumber:
    """Read an Indonesian number written any common way: 0812-3456-7890, +62 812 3456 7890, 6281234567890, 062812..., +62 (0)812...,
    (021) 555 1234. Raises ValueError for foreign numbers, wrong lengths, or anything that is not a number."""
    text = re.sub(r"(?i)\s*(?:ext\.?|extension|x)\s*\d+\s*$", "", raw.strip())  # an extension is not part of the number
    digits = re.sub(r"\D", "", text)
    if not digits or re.search(r"[A-Za-z]", text):
        raise ValueError(f"not a phone number: {raw!r}")
    if text.startswith("+") and not digits.startswith("62"):
        raise ValueError(f"not an Indonesian number: {raw!r}")
    if digits.startswith("0062"):
        digits = digits[4:]
    elif digits.startswith("062"):
        digits = digits[3:]
    elif digits.startswith("62"):
        digits = digits[2:]
    elif digits.startswith("0"):
        digits = digits[1:]
    else:
        raise ValueError(f"not an Indonesian number: {raw!r}")
    if digits.startswith("0"):  # +62 0812: a trunk zero kept after the country code
        digits = digits[1:]
    if digits.startswith(("800", "804")):
        kind = "toll-free"
        if not 8 <= len(digits) <= 12:
            raise ValueError(f"unexpected length for an Indonesian toll-free number: {raw!r}")
    elif digits.startswith("8"):
        kind = "mobile"
        if not 9 <= len(digits) <= 12:
            raise ValueError(f"unexpected length for an Indonesian mobile number: {raw!r}")
    elif digits[:1] in "123456789" and 8 <= len(digits) <= 11:
        kind = "landline"
    else:
        raise ValueError(f"unexpected length or prefix for an Indonesian number: {raw!r}")
    operator = OPERATOR_BY_PREFIX.get(digits[:3]) if kind == "mobile" else None
    area = None
    if kind == "landline":
        area = next((AREA_CODES[c] for c in sorted(AREA_CODES, key=len, reverse=True) if digits.startswith(c)), None)
    return PhoneNumber("+62" + digits, kind, digits, operator, area)


def normalize_phone(raw: str) -> str:
    """Canonical +62 form for Indonesian numbers."""
    return parse_phone(raw).e164
