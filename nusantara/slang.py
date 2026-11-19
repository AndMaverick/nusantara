"""Chat Indonesian to standard Indonesian. The dictionary is small, reviewable and conservative: only words that mean one thing in chat.
Words with a second meaning (kaya is also "rich", kek is also "cake", gua is also "cave", cm is also "centimetre") are deliberately left out."""
from __future__ import annotations

import re
from collections.abc import Mapping

SLANG: dict[str, str] = {
    # negation and aspect
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "ngga": "tidak", "enggak": "tidak", "engga": "tidak", "gk": "tidak", "tdk": "tidak",
    "kagak": "tidak", "nggk": "tidak", "udah": "sudah", "udh": "sudah", "sdh": "sudah", "dah": "sudah", "belom": "belum", "blm": "belum",
    "blom": "belum", "lg": "lagi", "msh": "masih", "masi": "masih", "gpp": "tidak apa-apa", "gapapa": "tidak apa-apa", "gpapa": "tidak apa-apa",
    # degree and limit
    "bgt": "sangat", "banget": "sangat", "bngt": "sangat", "bgd": "sangat", "aja": "saja", "aj": "saja", "doang": "saja", "doank": "saja",
    "cuma": "hanya", "cuman": "hanya", "dikit": "sedikit", "sdikit": "sedikit", "bnyk": "banyak", "lbh": "lebih", "krg": "kurang",
    # question words
    "gimana": "bagaimana", "gmn": "bagaimana", "gmna": "bagaimana", "bgmn": "bagaimana", "gmana": "bagaimana", "knp": "kenapa", "napa": "kenapa",
    "kpn": "kapan", "dmn": "di mana", "brp": "berapa", "brapa": "berapa",
    # function words
    "yg": "yang", "yng": "yang", "dgn": "dengan", "dg": "dengan", "dngn": "dengan", "utk": "untuk", "untk": "untuk", "krn": "karena",
    "karna": "karena", "krna": "karena", "jg": "juga", "jga": "juga", "jgn": "jangan", "dlm": "dalam", "pd": "pada", "kpd": "kepada",
    "tp": "tetapi", "tapi": "tetapi", "ttg": "tentang", "tntg": "tentang", "spy": "supaya", "sblm": "sebelum", "stlh": "setelah",
    "emang": "memang", "emg": "memang", "emank": "memang", "kalo": "kalau", "klo": "kalau", "kalok": "kalau", "bkn": "bukan", "bukn": "bukan",
    "dll": "dan lain-lain", "dsb": "dan sebagainya", "dst": "dan seterusnya", "nih": "ini", "tuh": "itu", "gini": "begini", "gitu": "begitu",
    "gtu": "begitu", "gni": "begini", "kayak": "seperti", "kyk": "seperti",
    # pronouns
    "sy": "saya", "sya": "saya", "gue": "saya", "gw": "saya", "lu": "kamu", "loe": "kamu", "elu": "kamu", "km": "kamu", "kmu": "kamu",
    # time
    "kmrn": "kemarin", "bsk": "besok", "skrg": "sekarang", "skg": "sekarang", "skrng": "sekarang", "ntar": "nanti", "entar": "nanti",
    "ntr": "nanti", "tdi": "tadi", "trs": "terus", "trus": "terus", "thn": "tahun", "bln": "bulan", "tgl": "tanggal", "mlm": "malam",
    # verbs and everyday words
    "bikin": "membuat", "pake": "pakai", "pakek": "pakai", "tau": "tahu", "tw": "tahu", "bener": "benar", "bnr": "benar", "males": "malas",
    "mls": "malas", "capek": "lelah", "gede": "besar", "pengen": "ingin", "pingin": "ingin", "pengin": "ingin", "dapet": "dapat",
    "dpt": "dapat", "bs": "bisa", "bsa": "bisa", "hrs": "harus", "hrus": "harus", "abis": "habis", "org": "orang", "orng": "orang",
    "temen": "teman", "tmn": "teman", "duit": "uang", "bokap": "ayah", "nyokap": "ibu", "hrg": "harga", "hrga": "harga",
    "sbnrnya": "sebenarnya", "sebenernya": "sebenarnya", "dtg": "datang", "dtng": "datang", "sampe": "sampai", "smpe": "sampai",
    # thanks and requests
    "makasih": "terima kasih", "mksh": "terima kasih", "thx": "terima kasih", "thanks": "terima kasih", "trims": "terima kasih",
    "tengkyu": "terima kasih", "tks": "terima kasih", "plis": "tolong", "pls": "tolong", "tlg": "tolong",
}
# Particles that carry tone and have no standard equivalent. Listed so they are never mistaken for unknown slang.
PARTICLES = frozenset({"sih", "deh", "dong", "kok", "lah", "kan", "yah", "lho", "loh", "nah", "ya", "yuk", "lo"})
_LAUGHTER = re.compile(r"(?i)^(?:w?k(?:w?k)+w?|(?:ha){2,}h?|(?:he){2,}h?|(?:hi){2,}h?|(?:xi){2,}x?|(?:awok){2,}|(?:wk){2,})$")
_WORD = re.compile(r"[A-Za-z]+")
_REDUP = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]{2,})2(?![A-Za-z0-9])")


def is_laughter(token: str) -> bool:
    """wkwk, wkwkwk, haha, hehe, hihi, xixi, kwkwk, awokawok."""
    return bool(_LAUGHTER.match(token))


def _lookup(word: str, table: Mapping[str, str], squeeze: bool) -> str | None:
    low = word.lower()
    if low in table:
        return table[low]
    if squeeze:
        for pattern in (r"(.)\1{2,}", r"(.)\1+"):  # bangeeet, then bangeet
            short = re.sub(pattern, r"\1", low)
            if short != low and short in table:
                return table[short]
    return None


def normalize_slang(text: str, *, squeeze: bool = True, reduplication: bool = True, extra: Mapping[str, str] | None = None,
                    preserve_case: bool = False) -> str:
    """Replace chat abbreviations with standard Indonesian. Words not in the dictionary, including names, are left as they are.

    squeeze         stretched spellings (bangeeet, gaaak) are read as their dictionary word. Only when the squeezed form is in the dictionary.
    reduplication   orang2 becomes orang-orang, buku2 becomes buku-buku.
    extra           your own entries, which win over the built-in ones.
    preserve_case   keep an initial capital on the replacement (Gak becomes Tidak). The 0.1 behaviour lowercases it.

    Replacement is word by word. It does not reorder: "bagus banget" becomes "bagus sangat", where standard Indonesian says "sangat bagus"."""
    table: Mapping[str, str] = {**SLANG, **{k.lower(): v for k, v in (extra or {}).items()}}
    if reduplication:
        text = _REDUP.sub(lambda m: f"{m.group(1)}-{m.group(1)}", text)

    def swap(m: re.Match[str]) -> str:
        word = m.group(0)
        if is_laughter(word):
            return word
        new = _lookup(word, table, squeeze)
        if new is None:
            return word
        return new[:1].upper() + new[1:] if preserve_case and word[:1].isupper() else new

    return _WORD.sub(swap, text)


def slang_density(text: str) -> float:
    """Share of words (two letters or more, laughter and particles excluded) that are chat slang: a quick formal-versus-informal signal for routing."""
    words = [w for w in _WORD.findall(text) if len(w) >= 2 and not is_laughter(w) and w.lower() not in PARTICLES]
    if not words:
        return 0.0
    return sum(_lookup(w, SLANG, True) is not None for w in words) / len(words)
