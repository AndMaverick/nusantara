"""Regression sets written alongside the code, run end to end. These are not independent benchmarks: the cases were written by the author of the
parsers, so a pass means "does what the author meant", and the misses listed at the bottom are the ones known and pinned.

    python examples/evaluate.py          # prints a table, exits 1 on any unexpected result
"""
from __future__ import annotations

import sys
from datetime import date, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nusantara import (  # noqa: E402
    find_amounts,
    format_rupiah,
    normalize_phone,
    normalize_slang,
    parse_date,
    parse_nik,
    parse_phone,
    parse_rupiah,
    parse_terbilang,
    parse_time,
    terbilang,
)

MONEY = [
    ("Rp 1.500.000", 1500000), ("Rp1.500.000,-", 1500000), ("1,5 juta", 1500000), ("1.5 juta", 1500000), ("500 rb", 500000), ("500 ribu", 500000),
    ("12 jt", 12000000), ("2 miliar", 2000000000), ("1 triliun", 10**12), ("Rp 250.000", 250000), ("IDR 3.000.000", 3000000),
    ("seratus ribu rupiah", 100000), ("setengah juta", 500000), ("Rp 1,25 juta", 1250000), ("75 ribu", 75000), ("Rp 10.000.000.000", 10**10),
    ("2 juta 500 ribu", 2500000), ("Rp 999", 999), ("1,5jt", 1500000),
]
DATES = [
    ("17 Agustus 2026", date(2026, 8, 17)), ("17 Agu 2026", date(2026, 8, 17)), ("17/08/2026", date(2026, 8, 17)), ("17-08-26", date(2026, 8, 17)),
    ("2026-08-17", date(2026, 8, 17)), ("1 Pebruari 2025", date(2025, 2, 1)), ("5 Nopember 2024", date(2024, 11, 5)), ("29 Februari 2024", date(2024, 2, 29)),
    ("Senin, 17 Agustus 2026", date(2026, 8, 17)), ("31 Des 2025", date(2025, 12, 31)),
]
TIMES = [
    ("jam 8 malam", time(20)), ("jam 12 malam", time(0)), ("jam 12 siang", time(12)), ("setengah tiga sore", time(14, 30)), ("pukul 09.30", time(9, 30)),
    ("jam 5 sore", time(17)), ("jam 1 dini hari", time(1)), ("pkl 7 pagi", time(7)), ("jam dua belas siang", time(12)), ("setengah 12 malam", time(23, 30)),
]
PHONES = [
    ("0812-3456-7890", "+6281234567890"), ("+62 812 3456 7890", "+6281234567890"), ("62812345678", "+62812345678"), ("(021) 555 1234", "+62215551234"),
    ("0895 3456 7890", "+6289534567890"), ("+62-21-5551234", "+62215551234"), ("0856-1234-5678", "+6285612345678"), ("081234567890", "+6281234567890"),
]
SLANG = [
    ("gak bisa", "tidak bisa"), ("udh sampe", "sudah sampai"), ("yg penting", "yang penting"), ("bgt", "sangat"), ("bagus2", "bagus-bagus"),
    ("kmrn dtg", "kemarin datang"), ("nggak mau", "tidak mau"), ("sy blm tau", "saya belum tahu"), ("Budi dtg", "Budi datang"), ("kucing lucu", "kucing lucu"),
]


def check(name: str, cases: list, fn) -> list[str]:
    misses = []
    for text, expected in cases:
        try:
            got = fn(text)
        except ValueError as exc:
            got = f"ValueError({exc})"
        if got != expected:
            misses.append(f"{text!r}: expected {expected!r}, got {got!r}")
    print(f"{name:<26}{len(cases) - len(misses):>3}/{len(cases)}")
    return misses


def money(text: str):
    try:
        return parse_rupiah(text)
    except ValueError as exc:
        return f"ValueError({exc})"


def main() -> int:
    all_misses = {
        "money": check("rupiah amounts", MONEY, money),
        "dates": check("dates", DATES, parse_date),
        "times": check("clock times", TIMES, parse_time),
        "phones": check("phone numbers", PHONES, normalize_phone),
        "slang": check("slang (word by word)", SLANG, normalize_slang),
    }
    # structural properties over many values rather than a hand-written list
    words_range, fmt_range = range(0, 200_000, 7), range(0, 5_000_000, 997)
    bad_words = [n for n in words_range if parse_terbilang(terbilang(n)) != n]
    print(f"{'terbilang round trip':<26}{len(words_range) - len(bad_words)}/{len(words_range)} (every 7th integer below 200,000)")
    bad_fmt = [n for n in fmt_range if parse_rupiah(format_rupiah(n)) != n]
    print(f"{'rupiah format round trip':<26}{len(fmt_range) - len(bad_fmt)}/{len(fmt_range)} (every 997th integer below 5,000,000)")
    ok_nik = parse_nik("3174011508900001")
    assert ok_nik.valid and parse_phone("0812-3456-7890").operator == "Telkomsel" and find_amounts("tidak ada") == []
    failed = any(all_misses.values()) or bad_words or bad_fmt
    for group, misses in all_misses.items():
        for miss in misses:
            print(f"MISS [{group}] {miss}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
