import unittest
from datetime import date

from nusantara import format_date, format_rupiah, normalize_phone, normalize_slang, parse_date, parse_rupiah


class RupiahTests(unittest.TestCase):
    def test_parse_plain_and_dotted(self):
        self.assertEqual(parse_rupiah("Harganya Rp 1.500.000 saja"), 1500000)
        self.assertEqual(parse_rupiah("Rp500"), 500)

    def test_parse_units(self):
        self.assertEqual(parse_rupiah("sekitar 1,5 juta"), 1500000)
        self.assertEqual(parse_rupiah("500 ribu"), 500000)
        self.assertEqual(parse_rupiah("Rp 2 miliar"), 2000000000)
        self.assertEqual(parse_rupiah("gajinya 12 jt per bulan"), 12000000)
        self.assertEqual(parse_rupiah("250rb"), 250000)

    def test_format(self):
        self.assertEqual(format_rupiah(1500000), "Rp 1.500.000")
        self.assertEqual(format_rupiah(-2500), "-Rp 2.500")

    def test_round_trip(self):
        self.assertEqual(parse_rupiah(format_rupiah(7250000)), 7250000)

    def test_no_amount(self):
        with self.assertRaises(ValueError):
            parse_rupiah("tidak ada angka di sini")


class SlangTests(unittest.TestCase):
    def test_normalizes_and_keeps_case_of_unknown_words(self):
        self.assertEqual(normalize_slang("Gak udah deh, Budi bgt"), "tidak sudah deh, Budi sangat")

    def test_leaves_standard_text_alone(self):
        text = "Rapat dimulai pukul sembilan."
        self.assertEqual(normalize_slang(text), text)


class DateTests(unittest.TestCase):
    def test_parse_full_and_abbreviated(self):
        self.assertEqual(parse_date("Lahir 17 Agustus 2026"), date(2026, 8, 17))
        self.assertEqual(parse_date("5 des 2025"), date(2025, 12, 5))
        self.assertEqual(parse_date("1 Mei 2024"), date(2024, 5, 1))

    def test_format(self):
        self.assertEqual(format_date(date(2026, 8, 17)), "17 Agustus 2026")

    def test_missing_date(self):
        with self.assertRaises(ValueError):
            parse_date("besok pagi")


class PhoneTests(unittest.TestCase):
    def test_forms_converge(self):
        for raw in ("0812-3456-7890", "+62 812 3456 7890", "6281234567890", "(0812) 3456 7890"):
            self.assertEqual(normalize_phone(raw), "+6281234567890")

    def test_rejects_foreign_or_short(self):
        with self.assertRaises(ValueError):
            normalize_phone("+1 415 555 0100")
        with self.assertRaises(ValueError):
            normalize_phone("0812")


if __name__ == "__main__":
    unittest.main()
