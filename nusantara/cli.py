"""Command line for Indonesian text. Arguments or stdin (``-``), JSON out where there is structure.

Exit codes: 0 success, 1 a check failed (no amount found with --require, an invalid phone number or NIK, a weekday that does not match its date
with --strict-weekday), 2 error."""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Sequence
from datetime import date
from typing import Any

from . import (
    expand_address,
    find_amounts,
    find_dates,
    find_times,
    mask_nik,
    normalize_slang,
    parse_address,
    parse_datetime,
    parse_nik,
    parse_phone,
    parse_terbilang,
    terbilang,
    terbilang_rupiah,
)


def _text(value: str) -> str:
    return sys.stdin.read() if value == "-" else value


def _dump(obj: Any) -> None:
    def default(o: Any) -> Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        return str(o)
    print(json.dumps(obj, ensure_ascii=False, default=default))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nusantara", description="Indonesian text and data infrastructure.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("money", help="rupiah amounts in text")
    p.add_argument("text")
    p.add_argument("--require", action="store_true", help="exit 1 when no amount is found")
    p.add_argument("--require-currency", action="store_true", help="only amounts with Rp, IDR or 'rupiah'")
    p.add_argument("--shorthand", action="store_true", help="read 2M as 2 miliar and 1,5T as 1,5 triliun")
    p = sub.add_parser("say", help="a number in Indonesian words (terbilang)")
    p.add_argument("number", type=int)
    p.add_argument("--rupiah", action="store_true")
    p = sub.add_parser("unsay", help="Indonesian number words to a number")
    p.add_argument("words")
    p = sub.add_parser("slang", help="normalize chat Indonesian")
    p.add_argument("text")
    p = sub.add_parser("date", help="dates and clock times in text")
    p.add_argument("text")
    p.add_argument("--today", help="YYYY-MM-DD, for relative words such as besok")
    p.add_argument("--strict-weekday", action="store_true", help="exit 1 when a written weekday does not match its date")
    p = sub.add_parser("phone", help="normalize and classify a phone number; exit 1 if invalid")
    p.add_argument("number")
    p = sub.add_parser("nik", help="check the structure of a NIK; exit 1 if invalid")
    p.add_argument("number")
    p.add_argument("--mask", action="store_true", help="print only the masked number")
    p = sub.add_parser("address", help="parse an address")
    p.add_argument("text")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _run(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _run(a: argparse.Namespace) -> int:
    c = a.command
    if c == "money":
        found = find_amounts(_text(a.text), require_currency=a.require_currency, shorthand=a.shorthand)
        _dump([dataclasses.asdict(x) for x in found])
        return 1 if a.require and not found else 0
    if c == "say":
        print(terbilang_rupiah(a.number) if a.rupiah else terbilang(a.number))
    elif c == "unsay":
        print(parse_terbilang(a.words))
    elif c == "slang":
        print(normalize_slang(_text(a.text)))
    elif c == "date":
        text = _text(a.text)
        today = date.fromisoformat(a.today) if a.today else None
        dates = find_dates(text)
        times = find_times(text)
        out: dict[str, Any] = {"dates": [{"date": d.value.isoformat(), "text": d.text, "weekday_mismatch": d.weekday_mismatch} for d in dates],
                               "times": [t.isoformat() for t, _, _ in times]}
        if today and not dates:
            from .dates import parse_relative
            rel = parse_relative(text, today)
            if rel:
                out["dates"] = [{"date": rel.isoformat(), "text": "relative", "weekday_mismatch": False}]
        if out["dates"] and times:
            out["datetime"] = parse_datetime(text, today=today).isoformat()
        _dump(out)
        return 1 if a.strict_weekday and any(d.weekday_mismatch for d in dates) else 0
    elif c == "phone":
        try:
            _dump(dataclasses.asdict(parse_phone(a.number)) | {"international": parse_phone(a.number).format(), "national": parse_phone(a.number).format("national")})
        except ValueError as exc:
            print(f"invalid: {exc}", file=sys.stderr)
            return 1
    elif c == "nik":
        nik = parse_nik(a.number)
        if a.mask:
            print(mask_nik(a.number))
        else:
            _dump(dataclasses.asdict(nik) | {"number": mask_nik(a.number) if len(nik.number) == 16 else nik.number})
        return 0 if nik.valid else 1
    else:
        _dump(dataclasses.asdict(parse_address(a.text)) | {"expanded": expand_address(a.text)})
    return 0


if __name__ == "__main__":
    sys.exit(main())
