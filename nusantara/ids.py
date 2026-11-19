"""Indonesian identity numbers, checked for structure only: NIK (16 digits) and NPWP (15 or 16 digits).

Nothing here consults a register. A structurally valid number can still be unissued, and these checks cannot say whose it is."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

# Province codes in the first two digits of a NIK. The 34 long-standing ones are named. 92, 93, 95 and 96 (the provinces created from Papua in
# 2022) are accepted as assigned but left unnamed: verify them against the Kemendagri table before relying on a name.
NIK_PROVINCES = {
    "11": "Aceh", "12": "Sumatera Utara", "13": "Sumatera Barat", "14": "Riau", "15": "Jambi", "16": "Sumatera Selatan", "17": "Bengkulu",
    "18": "Lampung", "19": "Kepulauan Bangka Belitung", "21": "Kepulauan Riau", "31": "DKI Jakarta", "32": "Jawa Barat", "33": "Jawa Tengah",
    "34": "DI Yogyakarta", "35": "Jawa Timur", "36": "Banten", "51": "Bali", "52": "Nusa Tenggara Barat", "53": "Nusa Tenggara Timur",
    "61": "Kalimantan Barat", "62": "Kalimantan Tengah", "63": "Kalimantan Selatan", "64": "Kalimantan Timur", "65": "Kalimantan Utara",
    "71": "Sulawesi Utara", "72": "Sulawesi Tengah", "73": "Sulawesi Selatan", "74": "Sulawesi Tenggara", "75": "Gorontalo", "76": "Sulawesi Barat",
    "81": "Maluku", "82": "Maluku Utara", "91": "Papua Barat", "94": "Papua",
}
_UNNAMED_PROVINCES = {"92", "93", "95", "96"}


@dataclass(frozen=True)
class NIK:
    number: str
    valid: bool
    issues: list[str] = field(default_factory=list)
    province_code: str | None = None
    province: str | None = None
    regency_code: str | None = None
    district_code: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    serial: str | None = None


def parse_nik(raw: str, *, today: date | None = None) -> NIK:
    """Read the structure of a NIK: PPRRDD (province, regency or city, district) then DDMMYY (birth date, with 40 added to the day for women)
    then a four-digit serial. Spaces, dots and dashes are ignored. Never raises: ``valid`` and ``issues`` say what is wrong.

    The two-digit birth year has no century. Years up to the current two-digit year read as 20xx and later ones as 19xx, so a person born
    in 1925 is indistinguishable from one born in 2025: the number alone cannot say."""
    number = re.sub(r"[\s.\-]", "", raw)
    issues: list[str] = []
    if not number.isdigit():
        return NIK(number, False, ["contains characters other than digits"])
    if len(number) != 16:
        return NIK(number, False, [f"must be 16 digits, has {len(number)}"])
    today = today or date.today()
    province_code = number[:2]
    if province_code not in NIK_PROVINCES and province_code not in _UNNAMED_PROVINCES:
        issues.append(f"province code {province_code} is not assigned")
    if number[2:4] == "00" or number[4:6] == "00":
        issues.append("regency or district code is 00")
    day, month, year2 = int(number[6:8]), int(number[8:10]), int(number[10:12])
    gender = "female" if day > 40 else "male"
    day = day - 40 if day > 40 else day
    year = 2000 + year2 if year2 <= today.year % 100 else 1900 + year2
    birth: date | None = None
    try:
        birth = date(year, month, day)
        if birth > today:
            issues.append("birth date is in the future")
            birth = None
    except ValueError:
        issues.append(f"birth date {number[6:12]} is not a real date")
    if number[12:] == "0000":
        issues.append("serial is 0000")
    return NIK(number, not issues, issues, province_code, NIK_PROVINCES.get(province_code), number[2:4], number[4:6], birth,
               gender if birth else None, number[12:])


def mask_nik(raw: str) -> str:
    """Show the first six and last four digits and hide the rest: 317401******0001. For logs and screens, where the full number should not appear."""
    number = re.sub(r"[\s.\-]", "", raw)
    if len(number) != 16 or not number.isdigit():
        raise ValueError("a NIK has 16 digits")
    return number[:6] + "*" * 6 + number[12:]


def parse_npwp(raw: str) -> str:
    """Digits of an NPWP tax number: 15 (the long-standing format) or 16 (the format used since 2024, which for individuals is the NIK).
    Raises ValueError for any other length."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) not in (15, 16):
        raise ValueError(f"an NPWP has 15 or 16 digits, got {len(digits)}")
    return digits


def format_npwp(raw: str) -> str:
    """15 digits as 12.345.678.9-012.345; 16 digits are returned as plain digits."""
    d = parse_npwp(raw)
    if len(d) == 16:
        return d
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}.{d[8]}-{d[9:12]}.{d[12:]}"
