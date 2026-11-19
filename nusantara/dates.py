"""Indonesian dates and clock times: 17 Agustus 2026, 17/08/2026, besok, 3 hari lagi, jam 8 malam, setengah tiga sore, WIB, WITA, WIT.

Two traps this module exists for: numeric dates are day first (03/04/2026 is 3 April), and "setengah tiga" is half *before* three,
2:30, not 3:30."""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone

MONTHS = ["januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus", "september", "oktober", "november", "desember"]
_MONTH_LOOKUP = {name: i + 1 for i, name in enumerate(MONTHS)} | {
    "pebruari": 2, "nopember": 11, "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "agu": 8, "agt": 8, "ags": 8,
    "sep": 9, "sept": 9, "okt": 10, "nov": 11, "des": 12,
}
MONTH_ABBR = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "mei": 5, "jun": 6, "jul": 7, "agu": 8, "agt": 8, "sep": 9, "okt": 10, "nov": 11, "des": 12}
WEEKDAYS = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu"]  # Monday is 0, as in datetime.date.weekday()
_WEEKDAY_LOOKUP = {name: i for i, name in enumerate(WEEKDAYS)} | {"jum'at": 4, "jumát": 4, "ahad": 6}

WIB = timezone(timedelta(hours=7), "WIB")
WITA = timezone(timedelta(hours=8), "WITA")
WIT = timezone(timedelta(hours=9), "WIT")
ZONES = {"WIB": WIB, "WITA": WITA, "WIT": WIT}

FIXED_HOLIDAYS = {
    (1, 1): "Tahun Baru Masehi", (5, 1): "Hari Buruh Internasional", (6, 1): "Hari Lahir Pancasila",
    (8, 17): "Hari Kemerdekaan Republik Indonesia", (12, 25): "Hari Raya Natal",
}

_MONTH_WORD = "|".join(sorted(_MONTH_LOOKUP, key=len, reverse=True))
_WEEKDAY_WORD = "|".join(sorted(_WEEKDAY_LOOKUP, key=len, reverse=True))
_TEXT_DATE = re.compile(rf"(?i)(?<![A-Za-z0-9])(\d{{1,2}})\s+({_MONTH_WORD}|mei)\.?\s+(\d{{4}})(?!\d)")
_NUMERIC_DATE = re.compile(r"(?<![\d.\-/])(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4}|\d{2})(?![\d.\-/])")
_ISO_DATE = re.compile(r"(?<![\d\-])(\d{4})-(\d{2})-(\d{2})(?![\d\-])")
_WEEKDAY_BEFORE = re.compile(rf"(?i)(?<![A-Za-z])({_WEEKDAY_WORD})\s*,?\s*$")


@dataclass(frozen=True)
class ParsedDate:
    value: date
    text: str
    start: int
    end: int
    weekday_mismatch: bool  # a weekday was written before the date and it is not that date's weekday


def weekday_name(value: date) -> str:
    return WEEKDAYS[value.weekday()].capitalize()


def month_name(month: int) -> str:
    return MONTHS[month - 1].capitalize()


def format_date(value: date, *, weekday: bool = False, abbreviated: bool = False) -> str:
    """17 Agustus 2026, Senin, 17 Agustus 2026 with ``weekday=True``, or 17 Agu 2026 with ``abbreviated=True``."""
    month = month_name(value.month)[:3] if abbreviated else month_name(value.month)
    if abbreviated and value.month == 8:
        month = "Agu"
    text = f"{value.day} {month} {value.year}"
    return f"{weekday_name(value)}, {text}" if weekday else text


def _make(day: int, month: int, year: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def find_dates(text: str, *, default_year: int | None = None) -> list[ParsedDate]:
    """Every explicit date: 17 Agustus 2026, 17 Agu 2026, 17/08/2026 (day first), 17-08-26, 2026-08-17. Impossible dates (31 Februari) are skipped.
    Two-digit years follow the POSIX rule: 69 and below are 20xx, 70 and above are 19xx. A weekday written just before the date is checked against it."""
    found: list[ParsedDate] = []
    for m in _TEXT_DATE.finditer(text):
        month = _MONTH_LOOKUP.get(m.group(2).lower().rstrip("."))
        parsed = _make(int(m.group(1)), month, int(m.group(3))) if month else None
        if parsed:
            found.append(_with_weekday(text, parsed, m))
    for m in _ISO_DATE.finditer(text):
        parsed = _make(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        if parsed:
            found.append(_with_weekday(text, parsed, m))
    for m in _NUMERIC_DATE.finditer(text):
        year = int(m.group(3))
        if len(m.group(3)) == 2:
            year += 2000 if year <= 68 else 1900
        parsed = _make(int(m.group(1)), int(m.group(2)), year)
        if parsed:
            found.append(_with_weekday(text, parsed, m))
    if default_year is not None:
        for m in re.finditer(rf"(?i)(?<![A-Za-z0-9])(\d{{1,2}})\s+({_MONTH_WORD})(?![A-Za-z0-9])(?!\s+\d{{4}})", text):
            parsed = _make(int(m.group(1)), _MONTH_LOOKUP[m.group(2).lower()], default_year)
            if parsed:
                found.append(_with_weekday(text, parsed, m))
    found.sort(key=lambda d: d.start)
    return found


def _with_weekday(text: str, value: date, m: re.Match[str]) -> ParsedDate:
    before = _WEEKDAY_BEFORE.search(text[:m.start()])
    start = before.start() if before else m.start()
    mismatch = before is not None and _WEEKDAY_LOOKUP[before.group(1).lower()] != value.weekday()
    return ParsedDate(value, text[start:m.end()], start, m.end(), mismatch)


def _add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(value.day, calendar.monthrange(year, month + 1)[1]))


_SMALL = {"satu": 1, "dua": 2, "tiga": 3, "empat": 4, "lima": 5, "enam": 6, "tujuh": 7, "delapan": 8, "sembilan": 9, "sepuluh": 10}
_UNIT_DAYS = {"hari": ("d", 1), "minggu": ("d", 7), "bulan": ("m", 1), "tahun": ("m", 12)}


def parse_relative(text: str, today: date) -> date | None:
    """Relative expressions measured from ``today``: hari ini, kemarin, kemarin lusa, besok, lusa, 3 hari lagi, 2 minggu lalu, minggu depan,
    bulan lalu, tahun depan, seminggu lagi. Returns None when there is none. Month and year steps keep the day, clamped to the month's length."""
    t = text.lower()
    for phrase, shift in (("kemarin lusa", -2), ("hari ini", 0), ("kemarin", -1), ("besok", 1), ("lusa", 2)):
        if re.search(rf"(?<![a-z]){phrase}(?![a-z])", t):
            return today + timedelta(days=shift)
    small = "|".join(_SMALL)
    m = re.search(rf"(?<![a-z0-9])(?:(\d+|{small})\s+|se)(hari|minggu|bulan|tahun)\s+(?:yang\s+)?(lalu|lagi|depan|kemarin)(?![a-z])", t)
    if m:
        count = 1 if m.group(1) is None else int(m.group(1)) if m.group(1).isdigit() else _SMALL[m.group(1)]
        kind, size = _UNIT_DAYS[m.group(2)]
        sign = -1 if m.group(3) in ("lalu", "kemarin") else 1
        return today + timedelta(days=sign * count * size) if kind == "d" else _add_months(today, sign * count * size)
    m = re.search(r"(?<![a-z])(minggu|bulan|tahun)\s+(depan|lalu|kemarin)(?![a-z])", t)
    if m:
        kind, size = _UNIT_DAYS[m.group(1)]
        sign = 1 if m.group(2) == "depan" else -1
        return today + timedelta(days=sign * size) if kind == "d" else _add_months(today, sign * size)
    return None


def parse_date(text: str, *, today: date | None = None, default_year: int | None = None) -> date:
    """The first date in the text. Explicit dates win; with ``today`` given, relative expressions (besok, 3 hari lagi) are understood too."""
    dates = find_dates(text, default_year=default_year)
    if dates:
        return dates[0].value
    if today is not None:
        relative = parse_relative(text, today)
        if relative is not None:
            return relative
    raise ValueError(f"no Indonesian date found in: {text!r}")


def fixed_holiday(value: date) -> str | None:
    """The name of a fixed-date national holiday, or None. Holidays that move (Idul Fitri, Idul Adha, Nyepi, Waisak, Imlek and the rest)
    are set by government decree each year and are not computed here."""
    return FIXED_HOLIDAYS.get((value.month, value.day))


_HOUR_WORDS = {**_SMALL, "sebelas": 11, "dua belas": 12}
_HOUR_WORD = "|".join(sorted(_HOUR_WORDS, key=len, reverse=True))
_KEYWORD = r"(?:pukul|pkl|jam)\.?"
_PERIOD = r"(?:\s*(pagi|siang|sore|malam|dini\s+hari))?"
_CLOCK = re.compile(rf"(?i)(?:(?<![A-Za-z0-9]){_KEYWORD}\s*(setengah\s+)?(\d{{1,2}}|{_HOUR_WORD})(?:\s*[.:]\s*(\d{{2}}))?{_PERIOD}(?![A-Za-z0-9])"
                    rf"|(?<![A-Za-z0-9.])(setengah\s+)(\d{{1,2}}|{_HOUR_WORD}){_PERIOD}(?![A-Za-z0-9])"
                    rf"|(?<![\d.:])(\d{{1,2}}):(\d{{2}})(?!\d))")


def _hour24(hour: int, period: str | None) -> int:
    if period is None or hour > 12 or hour == 0:
        return hour
    period = period.replace(" ", "")
    if period == "pagi":
        if hour == 12:
            raise ValueError("'12 pagi' is ambiguous: say 12 malam (midnight) or 12 siang (noon)")
        return hour
    if period == "siang":
        return hour if hour >= 10 else hour + 12 if hour <= 4 else _bad(hour, period)
    if period == "sore":
        return hour + 12 if 3 <= hour <= 6 else _bad(hour, period)
    if period == "dinihari":
        return 0 if hour == 12 else hour if hour <= 5 else _bad(hour, period)
    if period == "malam":
        return 0 if hour == 12 else hour + 12 if hour >= 6 else hour if hour <= 4 else _bad(hour, period)
    return hour


def _bad(hour: int, period: str) -> int:
    raise ValueError(f"'{hour} {period}' is not a time people write")


def _scan_times(text: str) -> tuple[list[tuple[time, int, int]], list[str]]:
    out: list[tuple[time, int, int]] = []
    errors: list[str] = []
    for m in _CLOCK.finditer(text):
        try:
            if m.group(8) is not None:
                hour, minute, period, half = int(m.group(8)), int(m.group(9)), None, False
            elif m.group(5):
                raw, period, half, minute = m.group(6).lower(), m.group(7), True, 0
                hour = int(raw) if raw.isdigit() else _HOUR_WORDS[raw]
            else:
                raw, period, half = m.group(2).lower(), m.group(4), bool(m.group(1))
                hour = int(raw) if raw.isdigit() else _HOUR_WORDS[raw]
                minute = int(m.group(3) or 0)
            hour = _hour24(hour, period.lower() if period else None)
            if half:
                moment = (datetime(2000, 1, 1) + timedelta(hours=hour % 24 if hour != 24 else 0)) - timedelta(minutes=30)
                hour, minute = moment.hour, 30
            if hour == 24:
                hour = 0
            out.append((time(hour, minute), m.start(), m.end()))
        except ValueError as exc:
            errors.append(str(exc))
    return out, errors


def find_times(text: str) -> list[tuple[time, int, int]]:
    """Clock times with positions. Reads jam 9 pagi, pukul 14.30, 14:30, jam delapan malam, setengah tiga sore (14:30). A bare 14.30 with a dot is
    taken as a time only after jam, pukul or pkl, because it is also how decimals are written. Ambiguous or impossible ones are skipped."""
    return _scan_times(text)[0]


def parse_time(text: str) -> time:
    """The first clock time in the text. Raises ValueError with the reason when a time was written but cannot be read ('12 pagi', 'jam 25')."""
    found, errors = _scan_times(text)
    if found:
        return found[0][0]
    raise ValueError(errors[0] if errors else f"no clock time found in: {text!r}")


def parse_datetime(text: str, *, today: date | None = None, tz: timezone = WIB) -> datetime:
    """A timezone-aware datetime from text such as "Senin, 17 Agustus 2026 pukul 09.30 WITA" or "besok jam 8 malam".
    The zone is the WIB, WITA or WIT written in the text, else ``tz`` (WIB by default). Needs a date (or ``today`` for relative ones) and a time."""
    day = parse_date(text, today=today)
    zone = next((ZONES[z] for z in re.findall(r"\b(WITA|WIB|WIT)\b", text)), tz)
    return datetime.combine(day, parse_time(text), tzinfo=zone)


def to_zone(value: datetime, zone: str | timezone) -> datetime:
    """The same instant in WIB, WITA or WIT."""
    target = ZONES[zone] if isinstance(zone, str) else zone
    return value.astimezone(target)
