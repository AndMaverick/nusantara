import unittest
from datetime import date, datetime, time, timedelta

from nusantara import (
    WIB,
    WIT,
    WITA,
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

TODAY = date(2026, 3, 31)  # a Tuesday


class ExplicitDateTests(unittest.TestCase):
    def test_every_written_form(self):
        d = date(2026, 8, 17)
        for text in ["17 Agustus 2026", "17 agustus 2026", "17 Agu 2026", "17 Agt 2026", "17 Ags 2026", "17/08/2026", "17-08-2026", "17.08.2026",
                     "17-08-26", "2026-08-17", "Lahir 17 Agustus 2026 di Jakarta"]:
            self.assertEqual(parse_date(text), d, text)

    def test_numeric_dates_are_day_first(self):
        self.assertEqual(parse_date("03/04/2026"), date(2026, 4, 3))
        self.assertEqual(parse_date("12/11/2025"), date(2025, 11, 12))

    def test_months_including_old_spellings(self):
        for name, month in [("Januari", 1), ("Februari", 2), ("Pebruari", 2), ("Maret", 3), ("Mei", 5), ("Juni", 6), ("Juli", 7), ("Agustus", 8),
                            ("September", 9), ("Sept", 9), ("Oktober", 10), ("Okt", 10), ("November", 11), ("Nopember", 11), ("Desember", 12), ("Des", 12)]:
            self.assertEqual(parse_date(f"5 {name} 2025").month, month, name)

    def test_two_digit_years_follow_the_posix_pivot(self):
        self.assertEqual(parse_date("01/01/68").year, 2068)
        self.assertEqual(parse_date("01/01/69").year, 1969)

    def test_impossible_dates_are_skipped_not_guessed(self):
        self.assertEqual(find_dates("31 Februari 2026"), [])
        self.assertEqual(find_dates("29 Februari 2025"), [])
        self.assertEqual(parse_date("29 Februari 2024"), date(2024, 2, 29))
        self.assertEqual(parse_date("31 Februari 2026 atau 1 Maret 2026"), date(2026, 3, 1))

    def test_default_year_for_dates_without_one(self):
        self.assertEqual(parse_date("rapat 17 Agustus", default_year=2026), date(2026, 8, 17))
        with self.assertRaises(ValueError):
            parse_date("rapat 17 Agustus")

    def test_positions(self):
        text = "Lahir 17 Agustus 2026 di Jakarta"
        found = find_dates(text)[0]
        self.assertEqual(text[found.start:found.end], "17 Agustus 2026")

    def test_no_date(self):
        for text in ["besok pagi", "", "bulan Agustus", "1 juta"]:
            with self.assertRaises(ValueError, msg=text):
                parse_date(text)


class WeekdayTests(unittest.TestCase):
    def test_17_august_2026_is_a_monday(self):
        self.assertEqual(date(2026, 8, 17).weekday(), 0)
        self.assertEqual(weekday_name(date(2026, 8, 17)), "Senin")

    def test_weekday_check(self):
        ok = find_dates("Senin, 17 Agustus 2026")[0]
        self.assertFalse(ok.weekday_mismatch)
        self.assertEqual(ok.text, "Senin, 17 Agustus 2026")
        self.assertTrue(find_dates("Selasa, 17 Agustus 2026")[0].weekday_mismatch)
        self.assertFalse(find_dates("17 Agustus 2026")[0].weekday_mismatch)

    def test_all_weekday_names(self):
        for i, name in enumerate(["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]):
            self.assertEqual(weekday_name(date(2026, 8, 17) + timedelta(days=i)), name)

    def test_format(self):
        d = date(2026, 8, 17)
        self.assertEqual(format_date(d), "17 Agustus 2026")
        self.assertEqual(format_date(d, weekday=True), "Senin, 17 Agustus 2026")
        self.assertEqual(format_date(d, abbreviated=True), "17 Agu 2026")
        self.assertEqual(format_date(date(2026, 12, 5), abbreviated=True), "5 Des 2026")
        self.assertEqual(month_name(5), "Mei")

    def test_fixed_holidays(self):
        self.assertEqual(fixed_holiday(date(2026, 8, 17)), "Hari Kemerdekaan Republik Indonesia")
        self.assertEqual(fixed_holiday(date(2026, 12, 25)), "Hari Raya Natal")
        self.assertIsNone(fixed_holiday(date(2026, 8, 18)))


class RelativeTests(unittest.TestCase):
    def test_days(self):
        for text, expected in [("hari ini", TODAY), ("besok pagi", date(2026, 4, 1)), ("lusa", date(2026, 4, 2)), ("kemarin", date(2026, 3, 30)),
                               ("kemarin lusa", date(2026, 3, 29)), ("3 hari lagi", date(2026, 4, 3)), ("5 hari yang lalu", date(2026, 3, 26)),
                               ("tiga hari lagi", date(2026, 4, 3)), ("sehari lagi", date(2026, 4, 1))]:
            self.assertEqual(parse_relative(text, TODAY), expected, text)

    def test_weeks_months_years(self):
        for text, expected in [("minggu depan", date(2026, 4, 7)), ("minggu lalu", date(2026, 3, 24)), ("2 minggu lalu", date(2026, 3, 17)),
                               ("seminggu lagi", date(2026, 4, 7)), ("bulan lalu", date(2026, 2, 28)), ("bulan depan", date(2026, 4, 30)),
                               ("2 bulan lagi", date(2026, 5, 31)), ("tahun depan", date(2027, 3, 31)), ("1 tahun lalu", date(2025, 3, 31))]:
            self.assertEqual(parse_relative(text, TODAY), expected, text)

    def test_month_end_is_clamped(self):
        self.assertEqual(parse_relative("sebulan lagi", date(2026, 1, 31)), date(2026, 2, 28))
        self.assertEqual(parse_relative("setahun lagi", date(2024, 2, 29)), date(2025, 2, 28))

    def test_needs_today_and_a_relative_word(self):
        self.assertIsNone(parse_relative("tidak ada", TODAY))
        self.assertEqual(parse_date("besok", today=TODAY), date(2026, 4, 1))
        with self.assertRaises(ValueError):
            parse_date("besok")

    def test_explicit_date_wins_over_relative(self):
        self.assertEqual(parse_date("besok, yaitu 5 Mei 2026", today=TODAY), date(2026, 5, 5))


class TimeTests(unittest.TestCase):
    CASES = [
        ("jam 9 pagi", time(9)), ("jam 10 pagi", time(10)), ("jam 12 siang", time(12)), ("jam 1 siang", time(13)), ("jam 3 sore", time(15)),
        ("jam 5 sore", time(17)), ("jam 6 malam", time(18)), ("jam 8 malam", time(20)), ("jam 11 malam", time(23)), ("jam 12 malam", time(0)),
        ("jam 2 malam", time(2)), ("jam 1 dini hari", time(1)), ("pukul 14.30", time(14, 30)), ("pukul 09.00 WIB", time(9)), ("14:30", time(14, 30)),
        ("jam 9.15 pagi", time(9, 15)), ("jam dua belas siang", time(12)), ("pukul delapan malam", time(20)), ("pkl 7 pagi", time(7)),
        # setengah N is half an hour BEFORE N
        ("setengah tiga sore", time(14, 30)), ("setengah 12 malam", time(23, 30)), ("jam setengah satu siang", time(12, 30)), ("setengah delapan", time(7, 30)),
        ("jam setengah 8 malam", time(19, 30)),
    ]

    def test_cases(self):
        for text, expected in self.CASES:
            self.assertEqual(parse_time(text), expected, text)

    def test_ambiguous_or_impossible_times_say_why(self):
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            parse_time("jam 12 pagi")
        with self.assertRaises(ValueError):
            parse_time("jam 25")
        self.assertEqual(parse_time("jam 9 malam lewat"), time(21))  # trailing words do not break a valid time
        self.assertEqual(parse_time("pukul 24.00"), time(0))  # 24.00 is read as midnight
        for bad in ["3.5 juta", "tidak ada", ""]:
            with self.assertRaises(ValueError, msg=bad):
                parse_time(bad)

    def test_a_dotted_number_is_not_a_time_without_a_keyword(self):
        self.assertEqual(find_times("harga 14.30 dolar"), [])
        self.assertEqual(find_times("harga 3.5 juta"), [])

    def test_positions(self):
        text = "rapat pukul 09.30 di kantor"
        t, start, end = find_times(text)[0]
        self.assertEqual((t, text[start:end]), (time(9, 30), "pukul 09.30"))


class DatetimeAndZoneTests(unittest.TestCase):
    def test_zone_offsets(self):
        self.assertEqual([z.utcoffset(None) for z in (WIB, WITA, WIT)], [timedelta(hours=7), timedelta(hours=8), timedelta(hours=9)])

    def test_parse_datetime_reads_the_zone_in_the_text(self):
        dt = parse_datetime("Senin, 17 Agustus 2026 pukul 09.30 WITA")
        self.assertEqual(dt, datetime(2026, 8, 17, 9, 30, tzinfo=WITA))
        self.assertEqual(dt.utcoffset(), timedelta(hours=8))

    def test_default_zone_is_wib_and_can_be_changed(self):
        self.assertEqual(parse_datetime("17 Agustus 2026 jam 9 pagi").utcoffset(), timedelta(hours=7))
        self.assertEqual(parse_datetime("17 Agustus 2026 jam 9 pagi", tz=WIT).utcoffset(), timedelta(hours=9))

    def test_relative_datetime(self):
        self.assertEqual(parse_datetime("besok jam 8 malam", today=TODAY), datetime(2026, 4, 1, 20, tzinfo=WIB))

    def test_conversion_keeps_the_instant(self):
        wib = parse_datetime("17 Agustus 2026 jam 9 pagi WIB")
        wit = to_zone(wib, "WIT")
        self.assertEqual((wit.hour, wit.tzname()), (11, "WIT"))
        self.assertEqual(wit, wib)
        self.assertEqual(to_zone(wib, "WITA").hour, 10)

    def test_lowercase_wit_is_not_a_zone(self):
        self.assertEqual(parse_datetime("17 Agustus 2026 jam 9 pagi with wit").utcoffset(), timedelta(hours=7))

    def test_needs_both_parts(self):
        with self.assertRaises(ValueError):
            parse_datetime("17 Agustus 2026")
        with self.assertRaises(ValueError):
            parse_datetime("jam 9 pagi")


if __name__ == "__main__":
    unittest.main()
