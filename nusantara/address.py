"""Indonesian addresses: expand the abbreviations (Jl., Gg., Kel., Kec., Kab.), read RT/RW, house number, postal code, kelurahan, kecamatan,
kabupaten or kota, and recognise the 38 provinces by name or common abbreviation. Pattern based, so it reads addresses that carry their
markers (Kel., Kec., Kota) and says nothing about those that do not."""
from __future__ import annotations

import re
from dataclasses import dataclass

PROVINCES: dict[str, tuple[str, ...]] = {
    "Aceh": ("nad", "nanggroe aceh darussalam"), "Sumatera Utara": ("sumut", "sumatra utara"), "Sumatera Barat": ("sumbar", "sumatra barat"),
    "Riau": (), "Kepulauan Riau": ("kepri",), "Jambi": (), "Sumatera Selatan": ("sumsel", "sumatra selatan"), "Kepulauan Bangka Belitung": ("babel", "bangka belitung"),
    "Bengkulu": (), "Lampung": (), "DKI Jakarta": ("dki", "jakarta", "daerah khusus ibukota jakarta"), "Jawa Barat": ("jabar",),
    "Banten": (), "Jawa Tengah": ("jateng",), "DI Yogyakarta": ("diy", "yogyakarta", "daerah istimewa yogyakarta"), "Jawa Timur": ("jatim",),
    "Bali": (), "Nusa Tenggara Barat": ("ntb",), "Nusa Tenggara Timur": ("ntt",), "Kalimantan Barat": ("kalbar",),
    "Kalimantan Tengah": ("kalteng",), "Kalimantan Selatan": ("kalsel",), "Kalimantan Timur": ("kaltim",), "Kalimantan Utara": ("kaltara",),
    "Sulawesi Utara": ("sulut",), "Gorontalo": (), "Sulawesi Tengah": ("sulteng",), "Sulawesi Barat": ("sulbar",), "Sulawesi Selatan": ("sulsel",),
    "Sulawesi Tenggara": ("sultra",), "Maluku": (), "Maluku Utara": ("malut",), "Papua Barat": (), "Papua Barat Daya": (), "Papua Selatan": (),
    "Papua": (), "Papua Tengah": (), "Papua Pegunungan": (),
}
_ALIAS = {alias: name for name, aliases in PROVINCES.items() for alias in aliases} | {name.lower(): name for name in PROVINCES}

_ABBREVIATIONS = [
    (r"jl|jln", "Jalan"), (r"gg", "Gang"), (r"kel", "Kelurahan"), (r"kec", "Kecamatan"), (r"kab", "Kabupaten"), (r"prov", "Provinsi"),
    (r"ds", "Desa"), (r"dsn", "Dusun"), (r"kp|kmp", "Kampung"), (r"perum", "Perumahan"), (r"komp|kmpl", "Kompleks"), (r"kav", "Kavling"),
    (r"lt", "Lantai"), (r"psr", "Pasar"),
]


def expand_address(text: str) -> str:
    """Spell out address abbreviations: "Jl. Merdeka No. 5, Kel. Baru, Kec. Lama" becomes "Jalan Merdeka Nomor 5, Kelurahan Baru, Kecamatan Lama".
    "No" is expanded only before a number. RT and RW are left as they are."""
    out = re.sub(r"(?i)(?<![A-Za-z])no\.?\s*(?=\d)", "Nomor ", text)
    for pattern, full in _ABBREVIATIONS:
        out = re.sub(rf"(?i)(?<![A-Za-z])(?:{pattern})\.?(?=\s|$)", full, out)
    return re.sub(r"\s+", " ", out).strip()


@dataclass(frozen=True)
class Address:
    street: str | None
    number: str | None
    rt: int | None
    rw: int | None
    kelurahan: str | None
    kecamatan: str | None
    city: str | None        # the part after Kota or Kabupaten, with the marker kept ("Kota Bandung")
    province: str | None    # canonical name
    postal_code: str | None


_STOP = r"(?=\s*(?:,|;|\bno\b|\bnomor\b|\brt\b|\brw\b|\bkel\b|\bkelurahan\b|\bdesa\b|\bkec\b|\bkecamatan\b|\bkab\b|\bkabupaten\b|\bkota\b|\bprov\b|\bprovinsi\b|\d{5}\b|$))"


def _before_province(value: str) -> str:
    """Cut a captured name where a province name starts ("Bogor Jawa Barat" is the city Bogor in the province Jawa Barat)."""
    low = value.lower()
    cut = len(value)
    for alias in _ALIAS:
        m = re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low)
        if m and m.start() > 0:
            cut = min(cut, m.start())
    return value[:cut].strip()


def _field(text: str, marker: str) -> str | None:
    m = re.search(rf"(?i)(?<![A-Za-z]){marker}\.?\s+([A-Za-z][A-Za-z' ]*?){_STOP}", text)
    return _before_province(m.group(1).strip()).title() if m else None


def parse_address(text: str) -> Address:
    """Pull the parts out of one address. Fields without a marker in the text are None."""
    t = expand_address(text)
    street = None
    m = re.search(rf"(?i)(?<![A-Za-z])(jalan|gang)\s+([^,;]+?){_STOP}", t)
    if m:
        street = f"{m.group(1).title()} {m.group(2).strip().title()}"
    number = None
    m = re.search(r"(?i)\bnomor\s+(\d+[A-Za-z]?(?:\s*[-/]\s*\d+[A-Za-z]?)?)", t)
    if m:
        number = m.group(1).replace(" ", "").upper()
    rt = rw = None
    m = re.search(r"(?i)\bRT\.?\s*0*(\d{1,3})\s*(?:[/,]\s*(?:RW\.?\s*)?|\s+RW\.?\s*)0*(\d{1,3})", t)
    if m:
        rt, rw = int(m.group(1)), int(m.group(2))
    else:
        a, b = re.search(r"(?i)\bRT\.?\s*0*(\d{1,3})", t), re.search(r"(?i)\bRW\.?\s*0*(\d{1,3})", t)
        rt, rw = int(a.group(1)) if a else None, int(b.group(1)) if b else None
    postal = re.findall(r"(?<!\d)(\d{5})(?!\d)", t)
    kota = _field(t, "kota")
    kab = _field(t, "kabupaten")
    city = f"Kota {kota}" if kota else f"Kabupaten {kab}" if kab else None
    return Address(street, number, rt, rw, _field(t, "kelurahan") or _field(t, "desa"), _field(t, "kecamatan"), city, find_province(t), postal[-1] if postal else None)


def find_province(text: str) -> str | None:
    """The province named in the text, by full name or common abbreviation (Jabar, Kaltim, NTT, DIY). The longest name wins, so
    "Kalimantan Timur" is not read as "Timur" and "Papua Barat Daya" is not read as "Papua Barat"."""
    low = text.lower()
    for alias in sorted(_ALIAS, key=len, reverse=True):
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?![a-z])", low):
            return _ALIAS[alias]
    return None
