"""Indonesian number words (terbilang), both directions. Used on invoices, contracts and cheques, where the amount is written out in words."""
from __future__ import annotations

ONES = ["nol", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan"]
DIGIT = {w: i for i, w in enumerate(ONES)}
MAGNITUDES = [("triliun", 10**12), ("miliar", 10**9), ("juta", 10**6), ("ribu", 10**3)]
MAGNITUDE = dict(MAGNITUDES) | {"milyar": 10**9}
MAX_TERBILANG = 10**15 - 1  # below one kuadriliun


def _below_thousand(n: int) -> list[str]:
    words: list[str] = []
    hundreds, rest = divmod(n, 100)
    if hundreds == 1:
        words.append("seratus")
    elif hundreds:
        words += [ONES[hundreds], "ratus"]
    if rest == 10:
        words.append("sepuluh")
    elif rest == 11:
        words.append("sebelas")
    elif 12 <= rest <= 19:
        words += [ONES[rest - 10], "belas"]
    elif rest >= 20:
        tens, unit = divmod(rest, 10)
        words += [ONES[tens], "puluh"]
        if unit:
            words.append(ONES[unit])
    elif rest:
        words.append(ONES[rest])
    return words


def terbilang(value: int | float, *, title: bool = False) -> str:
    """A number in Indonesian words. 1500000 is "satu juta lima ratus ribu", 1100 is "seribu seratus", 11 is "sebelas".

    Floats are read out digit by digit after "koma": 1.5 is "satu koma lima". Negative numbers start with "minus". Integers up to 10**15 - 1.
    With ``title=True`` every word is capitalised, as it is on an invoice."""
    if isinstance(value, bool):
        raise TypeError("terbilang takes a number, not a bool")
    negative = value < 0
    value = abs(value)
    whole = int(value)
    if whole > MAX_TERBILANG:
        raise ValueError(f"terbilang handles numbers below 10**15, got {value}")
    fraction = ""
    if isinstance(value, float) and value != whole:
        digits = f"{value:.10f}".split(".")[1].rstrip("0")
        fraction = " koma " + " ".join(ONES[int(d)] for d in digits)
    if whole == 0:
        words = ["nol"]
    else:
        words = []
        rest = whole
        for name, size in MAGNITUDES:
            group, rest = divmod(rest, size)
            if not group:
                continue
            if name == "ribu" and group == 1:
                words.append("seribu")
            else:
                words += _below_thousand(group) + [name]
        words += _below_thousand(rest)
    text = " ".join(words) + fraction
    if negative and (whole or fraction):
        text = "minus " + text
    return text.title() if title else text


def terbilang_rupiah(value: int, *, title: bool = True) -> str:
    """The amount as written on an invoice: ``terbilang_rupiah(1500000)`` is "Satu Juta Lima Ratus Ribu Rupiah"."""
    return terbilang(value, title=title) + (" Rupiah" if title else " rupiah")


_SE_WORDS = {"seratus": 100, "sepuluh": 10, "sebelas": 11}
_SE_MAGNITUDE = {"seribu": 10**3, "sejuta": 10**6, "semiliar": 10**9, "semilyar": 10**9, "setriliun": 10**12}
NUMBER_WORDS = (set(DIGIT) | set(MAGNITUDE) | set(_SE_WORDS) | set(_SE_MAGNITUDE) | {"belas", "puluh", "ratus", "koma", "setengah"})


def parse_terbilang(text: str) -> int | float:
    """Read an Indonesian number written in words. Inverse of ``terbilang``: ``parse_terbilang("dua ratus lima puluh ribu")`` is 250000.

    Accepts the fused forms seratus, seribu, sejuta, semiliar, sepuluh, sebelas, "setengah juta" (half a million), "koma" decimals and
    "minus". Raises ValueError on anything that is not a well-formed number, such as "dua puluh ratus" or "ribu" on its own."""
    tokens = text.lower().replace("-", " ").split()
    if not tokens:
        raise ValueError("empty number")
    negative = tokens[0] in ("minus", "negatif")
    if negative:
        tokens = tokens[1:]
    total = 0
    cur = 0
    pend: int | None = None
    last_mag = 10**15
    decimals: list[int] | None = None
    seen = False
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        i += 1
        if decimals is not None:
            if tok not in DIGIT:
                raise ValueError(f"after 'koma' only digits can follow, got {tok!r}")
            decimals.append(DIGIT[tok])
            continue
        seen = True
        if tok == "koma":
            if pend is not None:
                cur += pend
                pend = None
            decimals = []
        elif tok == "setengah":
            if i >= len(tokens) or tokens[i] not in MAGNITUDE or total or cur or pend is not None:
                raise ValueError("'setengah' must be followed by ribu, juta, miliar or triliun")
            mag = MAGNITUDE[tokens[i]]
            i += 1
            total += mag // 2
            last_mag = mag
        elif tok in DIGIT:
            if pend is not None:
                raise ValueError(f"two digits in a row at {tok!r}")
            pend = DIGIT[tok]
        elif tok in _SE_WORDS:
            if pend is not None:
                raise ValueError(f"unexpected {tok!r}")
            cur += _SE_WORDS[tok]
        elif tok in ("belas", "puluh", "ratus"):
            if pend is None or pend == 0:
                raise ValueError(f"{tok!r} needs a digit before it")
            if tok == "belas":
                cur += 10 + pend
            else:
                cur += pend * (10 if tok == "puluh" else 100)
            pend = None
        elif tok in MAGNITUDE or tok in _SE_MAGNITUDE:
            mag = _SE_MAGNITUDE.get(tok) or MAGNITUDE[tok]
            if tok in _SE_MAGNITUDE:
                if pend is not None or cur:
                    raise ValueError(f"unexpected {tok!r}")
                group = 1
            else:
                group = cur + (pend or 0)
                pend = None
                if group == 0:
                    raise ValueError(f"{tok!r} needs a number before it")
            if mag >= last_mag:
                raise ValueError(f"{tok!r} is out of order")
            total += group * mag
            cur = 0
            last_mag = mag
        else:
            raise ValueError(f"not a number word: {tok!r}")
    if not seen:
        raise ValueError("no number")
    cur += pend or 0
    value: int | float = total + cur
    if decimals is not None:
        if not decimals:
            raise ValueError("'koma' needs digits after it")
        value = float(f"{value}." + "".join(str(d) for d in decimals))
    return -value if negative else value
