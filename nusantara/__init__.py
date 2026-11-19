"""nusantara: Indonesian text and data infrastructure. Rupiah and number words, dates and clock times, phone numbers, chat slang, addresses and
identity-number structure. Dependency-free."""
from __future__ import annotations

from .address import PROVINCES, Address, expand_address, find_province, parse_address
from .dates import (
    MONTH_ABBR,
    MONTHS,
    WEEKDAYS,
    WIB,
    WIT,
    WITA,
    ZONES,
    ParsedDate,
    find_dates,
    find_times,
    fixed_holiday,
    format_date,
    month_name,
    parse_date,
    parse_datetime,
    parse_relative,
    parse_time,
    to_zone,
    weekday_name,
)
from .ids import NIK, format_npwp, mask_nik, parse_nik, parse_npwp
from .money import UNITS, Amount, find_amounts, format_rupiah, parse_rupiah
from .phone import PhoneNumber, normalize_phone, parse_phone
from .slang import SLANG, is_laughter, normalize_slang, slang_density
from .words import parse_terbilang, terbilang, terbilang_rupiah

__version__ = "0.2.0"

__all__ = [
    "MONTHS", "MONTH_ABBR", "NIK", "PROVINCES", "SLANG", "UNITS", "WEEKDAYS", "WIB", "WIT", "WITA", "ZONES", "Address", "Amount", "ParsedDate",
    "PhoneNumber", "expand_address", "find_amounts", "find_dates", "find_province", "find_times", "fixed_holiday", "format_date", "format_npwp",
    "format_rupiah", "is_laughter", "mask_nik", "month_name", "normalize_phone", "normalize_slang", "parse_address", "parse_date", "parse_datetime",
    "parse_nik", "parse_npwp", "parse_phone", "parse_relative", "parse_rupiah", "parse_terbilang", "parse_time", "slang_density", "terbilang",
    "terbilang_rupiah", "to_zone", "weekday_name",
]
