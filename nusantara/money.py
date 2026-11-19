"""Rupiah amounts: find them in text, read them as numbers, write them back. Handles Rp 1.500.000, 1,5 juta, 500rb, 1 juta 500 ribu,
IDR 1,500,000, "lima ratus ribu rupiah" and "setengah juta"."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .words import NUMBER_WORDS, parse_terbilang

UNITS = {"triliun": 10**12, "miliar": 10**9, "milyar": 10**9, "juta": 10**6, "jt": 10**6, "ribu": 10**3, "rb": 10**3, "k": 10**3}
SHORTHAND = {"t": 10**12, "m": 10**9}  # finance chat: 2M is 2 miliar, 1,5T is 1,5 triliun. Off by default because M is also "juta" in some circles.
_NUM = r"\d(?:[\d.,]*\d)?"
_UNIT_NAMES = "triliun|miliar|milyar|juta|jt|ribu|rb|k"
_GROUPED_DOT = re.compile(r"^\d{1,3}(\.\d{3})+$")
_GROUPED_COMMA = re.compile(r"^\d{1,3}(,\d{3})+$")


@dataclass(frozen=True)
class Amount:
    value: int | float
    text: str
    start: int
    end: int
    kind: str          # "digits" or "words"
    currency: bool     # an Rp, IDR or "rupiah" marker sits with the amount
    ambiguous: bool    # a separator could be read two ways (1,500 or 1.500 with a unit); the Indonesian reading was used


def _tidy(value: float) -> int | float:
    return int(value) if value == int(value) else value


def _read_number(raw: str, has_unit: bool) -> tuple[float, bool]:
    """Indonesian reading: dot groups thousands and comma is the decimal point. English-style groups (1,500,000) and a lone
    1,500 with no unit are read as thousands. Returns ``(value, ambiguous)``."""
    has_dot, has_comma = "." in raw, "," in raw
    if has_dot and has_comma:
        decimal = "." if raw.rfind(".") > raw.rfind(",") else ","
        group = "," if decimal == "." else "."
        return float(raw.replace(group, "").replace(decimal, ".")), False
    if has_dot:
        if _GROUPED_DOT.match(raw):
            return float(raw.replace(".", "")), has_unit and raw.count(".") == 1
        return float(raw), False
    if has_comma:
        if _GROUPED_COMMA.match(raw) and raw.count(",") > 1:
            return float(raw.replace(",", "")), False
        after = raw.split(",")[1] if raw.count(",") == 1 else ""
        if len(after) == 3 and not has_unit and len(raw.split(",")[0]) <= 3:
            return float(raw.replace(",", "")), True
        return float(raw.replace(",", ".")), len(after) == 3
    return float(raw), False


def _digit_pattern(shorthand: bool) -> re.Pattern[str]:
    units = _UNIT_NAMES + ("|t|m" if shorthand else "")
    pair = rf"(?:{_NUM})\s*(?:{units})"
    return re.compile(
        rf"(?<![A-Za-z0-9])(?P<cur>(?:rp\.?|idr)\s*)?(?P<n>{_NUM})(?:\s*(?P<u>{units})(?![A-Za-z0-9])(?P<rest>(?:\s+{pair}(?![A-Za-z0-9]))*))?(?P<tail>\s*rupiah\b)?",
        re.IGNORECASE,
    )


def find_amounts(text: str, *, require_currency: bool = False, shorthand: bool = False) -> list[Amount]:
    """Every amount in ``text``, with value, position and whether it carried a currency marker.

    A bare number counts only with Rp, IDR or "rupiah", with a unit (juta, rb, k...), or written with thousands dots (1.500.000).
    Number words count with a unit from ribu up or with "rupiah". ``require_currency=True`` keeps only amounts with a currency marker, which is
    what to use when "lima juta orang" must not become money. ``shorthand=True`` also reads 2M as 2 miliar and 1,5T as 1,5 triliun."""
    found: list[Amount] = []
    units = {**UNITS, **(SHORTHAND if shorthand else {})}
    for m in _digit_pattern(shorthand).finditer(text):
        unit, cur, tail = m.group("u"), m.group("cur"), m.group("tail")
        has_marker = bool(cur or tail)
        if not (has_marker or unit or _GROUPED_DOT.match(m.group("n"))):
            continue
        try:
            number, ambiguous = _read_number(m.group("n"), bool(unit))
        except ValueError:
            continue
        value = number * (units[unit.lower()] if unit else 1)
        last = units[unit.lower()] if unit else 0
        for pair in re.finditer(rf"({_NUM})\s*([A-Za-z]+)", m.group("rest") or ""):
            size = units[pair.group(2).lower()]
            if size >= last:
                break
            value += _read_number(pair.group(1), True)[0] * size
            last = size
        found.append(Amount(_tidy(value), m.group().rstrip(), m.start(), m.start() + len(m.group().rstrip()), "digits", has_marker, ambiguous))
    found += _word_amounts(text)
    found.sort(key=lambda a: a.start)
    kept: list[Amount] = []
    for a in found:  # a word run can sit inside a digit match's span: keep the earlier, longer one
        if kept and a.start < kept[-1].end:
            continue
        kept.append(a)
    return [a for a in kept if a.currency or not require_currency]


def _word_amounts(text: str) -> list[Amount]:
    words = list(re.finditer(r"[A-Za-z]+", text))
    out: list[Amount] = []
    i = 0
    while i < len(words):
        if words[i].group().lower() not in NUMBER_WORDS or words[i].group().lower() in ("koma", "belas", "puluh", "ratus"):
            i += 1
            continue
        j = i
        while j + 1 < len(words) and words[j + 1].group().lower() in NUMBER_WORDS and text[words[j].end():words[j + 1].start()].strip() == "":
            j += 1
        run = [w.group().lower() for w in words[i:j + 1]]
        end = words[j].end()
        tail = j + 1 < len(words) and words[j + 1].group().lower() == "rupiah" and text[end:words[j + 1].start()].strip() == ""
        marker = tail
        if tail:
            end = words[j + 1].end()
        while run:
            try:
                value = parse_terbilang(" ".join(run))
                break
            except ValueError:
                run.pop()  # drop trailing words that do not belong ("lima ratus ribu satu juta")
                tail = False
                end = words[i + len(run) - 1].end() if run else end
        else:
            i = j + 1
            continue
        has_magnitude = any(w in ("ribu", "juta", "miliar", "milyar", "triliun", "seribu", "sejuta", "semiliar", "setriliun") for w in run)
        if has_magnitude or marker and tail:
            out.append(Amount(_tidy(value), text[words[i].start():end], words[i].start(), end, "words", bool(marker and tail), False))
        i = j + 1
    return out


def parse_rupiah(text: str, *, require_currency: bool = False) -> int | float:
    """The first amount in the text, as rupiah. Handles Rp 1.500.000, 1,5 juta, 500 rb, 2 miliar, 1 juta 500 ribu and amounts in words."""
    amounts = find_amounts(text, require_currency=require_currency)
    if not amounts:
        raise ValueError(f"no rupiah amount found in: {text!r}")
    return amounts[0].value


def _group(n: int, sep: str) -> str:
    return f"{n:,}".replace(",", sep)


def format_rupiah(amount: float, *, decimals: int = 0, style: str = "full") -> str:
    """Write an amount. ``style="full"`` gives Rp 1.500.000, ``"compact"`` gives Rp 1,5 juta, ``"idr"`` gives IDR 1,500,000 (English separators).
    Rounds half up, which is how money is rounded (Python's round() rounds halves to even). ``decimals`` keeps that many decimal places."""
    if style not in ("full", "compact", "idr"):
        raise ValueError(f"style must be full, compact or idr, not {style!r}")
    value = Decimal(str(amount))
    sign = "-" if value < 0 else ""
    value = abs(value)
    if style == "compact":
        names = [("triliun", 10**12), ("miliar", 10**9), ("juta", 10**6), ("ribu", 10**3)]
        for i, (name, size) in enumerate(names):
            if value >= size:
                q = (value / size).quantize(Decimal("0.01"), ROUND_HALF_UP)
                if q >= 1000 and i > 0:
                    name, size = names[i - 1]
                    q = (value / size).quantize(Decimal("0.01"), ROUND_HALF_UP)
                text = f"{q:f}".rstrip("0").rstrip(".").replace(".", ",")
                return f"{sign}Rp {text} {name}"
    quant = Decimal(1).scaleb(-decimals)
    rounded = value.quantize(quant, ROUND_HALF_UP)
    whole, _, frac = f"{rounded:f}".partition(".")
    grouped_sep, decimal_sep = ("," , ".") if style == "idr" else (".", ",")
    body = _group(int(whole), grouped_sep) + (decimal_sep + frac if decimals else "")
    return f"{sign}{'IDR' if style == 'idr' else 'Rp'} {body}"
