import random
import unittest

from nusantara import find_amounts, format_rupiah, parse_rupiah, parse_terbilang, terbilang, terbilang_rupiah

KNOWN_WORDS = [
    (0, "nol"), (1, "satu"), (10, "sepuluh"), (11, "sebelas"), (12, "dua belas"), (19, "sembilan belas"), (20, "dua puluh"),
    (21, "dua puluh satu"), (99, "sembilan puluh sembilan"), (100, "seratus"), (101, "seratus satu"), (110, "seratus sepuluh"),
    (111, "seratus sebelas"), (200, "dua ratus"), (999, "sembilan ratus sembilan puluh sembilan"), (1000, "seribu"), (1001, "seribu satu"),
    (1100, "seribu seratus"), (2000, "dua ribu"), (10_000, "sepuluh ribu"), (11_000, "sebelas ribu"), (100_000, "seratus ribu"),
    (101_000, "seratus satu ribu"), (1_000_000, "satu juta"), (1_500_000, "satu juta lima ratus ribu"), (1_001_000, "satu juta seribu"),
    (2_000_000_000, "dua miliar"), (10**12, "satu triliun"), (12_345_678, "dua belas juta tiga ratus empat puluh lima ribu enam ratus tujuh puluh delapan"),
]


class TerbilangTests(unittest.TestCase):
    def test_known_values_both_ways(self):
        for number, words in KNOWN_WORDS:
            self.assertEqual(terbilang(number), words)
            self.assertEqual(parse_terbilang(words), number)

    def test_round_trip_on_random_numbers_of_every_size(self):
        rng = random.Random(2026)
        for digits in range(1, 16):
            for _ in range(150):
                n = rng.randrange(10 ** (digits - 1) if digits > 1 else 0, 10**digits)
                self.assertEqual(parse_terbilang(terbilang(n)), n, n)

    def test_decimals_negatives_and_title(self):
        self.assertEqual(terbilang(1.5), "satu koma lima")
        self.assertEqual(terbilang(-3), "minus tiga")
        self.assertEqual(parse_terbilang("minus tiga"), -3)
        self.assertEqual(parse_terbilang("tiga koma empat dua"), 3.42)
        self.assertEqual(terbilang(1500, title=True), "Seribu Lima Ratus")

    def test_rupiah_wording(self):
        self.assertEqual(terbilang_rupiah(1_500_000), "Satu Juta Lima Ratus Ribu Rupiah")
        self.assertEqual(terbilang_rupiah(250, title=False), "dua ratus lima puluh rupiah")

    def test_fused_forms_and_half(self):
        self.assertEqual(parse_terbilang("sejuta lima ratus ribu"), 1_500_000)
        self.assertEqual(parse_terbilang("seratus ribu"), 100_000)
        self.assertEqual(parse_terbilang("setengah juta"), 500_000)
        self.assertEqual(parse_terbilang("Dua Ratus Lima Puluh Ribu"), 250_000)
        self.assertEqual(parse_terbilang("dua puluh-satu"), 21)

    def test_malformed_numbers_are_refused(self):
        for bad in ["", "dua puluh ratus", "ribu", "dua dua", "juta ribu", "kucing", "satu juta satu juta", "belas", "tiga koma", "setengah"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_terbilang(bad)

    def test_too_large(self):
        with self.assertRaises(ValueError):
            terbilang(10**15)
        with self.assertRaises(TypeError):
            terbilang(True)


class ParseRupiahTests(unittest.TestCase):
    CASES = [
        ("Harganya Rp 1.500.000 saja", 1_500_000), ("Rp500", 500), ("sekitar 1,5 juta", 1_500_000), ("500 ribu", 500_000), ("Rp 2 miliar", 2_000_000_000),
        ("gajinya 12 jt per bulan", 12_000_000), ("250rb", 250_000), ("5k", 5000), ("1 juta 500 ribu", 1_500_000), ("2 juta 250 rb", 2_250_000),
        ("IDR 1,500,000", 1_500_000), ("Rp1.500.000,00", 1_500_000), ("Rp 500.000,-", 500_000), ("Rp. 75.000", 75_000), ("1.5 juta", 1_500_000),
        ("lima ratus ribu rupiah", 500_000), ("dua juta lima ratus ribu", 2_500_000), ("setengah juta", 500_000), ("sejuta", 1_000_000),
        ("seribu rupiah", 1000), ("Rp 12.500.000 (dua belas juta lima ratus ribu rupiah)", 12_500_000), ("3,25 miliar", 3_250_000_000),
        ("1 triliun", 10**12), ("Rp 1.234.567,89", 1_234_567.89), ("500 RIBU", 500_000), ("Rp 1,500", 1500),
    ]

    def test_cases(self):
        for text, value in self.CASES:
            self.assertEqual(parse_rupiah(text), value, text)

    def test_no_amount(self):
        for text in ["tidak ada angka di sini", "telp 0812-3456-7890", "5 kg beras", "dua puluh orang", ""]:
            with self.assertRaises(ValueError, msg=text):
                parse_rupiah(text)

    def test_require_currency_skips_quantities(self):
        self.assertEqual(parse_rupiah("lima juta orang, Rp 2 juta", require_currency=True), 2_000_000)
        with self.assertRaises(ValueError):
            parse_rupiah("3 juta orang", require_currency=True)

    def test_shorthand_is_opt_in(self):
        self.assertEqual(find_amounts("2M dan 1,5T"), [])
        self.assertEqual([a.value for a in find_amounts("2M dan 1,5T", shorthand=True)], [2_000_000_000, 1_500_000_000_000])


class FindAmountsTests(unittest.TestCase):
    def test_positions_kinds_and_currency(self):
        text = "Total Rp 12.500.000 (dua belas juta lima ratus ribu rupiah), cicilan 3 jt"
        found = find_amounts(text)
        self.assertEqual([(a.value, a.kind, a.currency) for a in found],
                         [(12_500_000, "digits", True), (12_500_000, "words", True), (3_000_000, "digits", False)])
        for a in found:
            self.assertEqual(text[a.start:a.end], a.text)

    def test_ambiguous_separators_are_flagged_and_read_the_indonesian_way(self):
        a = find_amounts("1,500 juta")[0]
        self.assertTrue(a.ambiguous)
        self.assertEqual(a.value, 1_500_000)
        b = find_amounts("Rp 1,500")[0]
        self.assertTrue(b.ambiguous)
        self.assertEqual(b.value, 1500)
        self.assertFalse(find_amounts("Rp 1.500.000")[0].ambiguous)
        self.assertFalse(find_amounts("1,5 juta")[0].ambiguous)

    def test_a_unit_letter_must_end_the_word(self):
        self.assertEqual(find_amounts("5 kg"), [])
        self.assertEqual(find_amounts("5 kilo"), [])
        self.assertEqual(len(find_amounts("5k, 6rb")), 2)

    def test_units_must_descend_in_compound_amounts(self):
        self.assertEqual(find_amounts("1 juta 2 miliar")[0].value, 1_000_000)


class FormatRupiahTests(unittest.TestCase):
    def test_styles(self):
        self.assertEqual(format_rupiah(1_500_000), "Rp 1.500.000")
        self.assertEqual(format_rupiah(-2500), "-Rp 2.500")
        self.assertEqual(format_rupiah(1_500_000, decimals=2), "Rp 1.500.000,00")
        self.assertEqual(format_rupiah(1_500_000, style="idr"), "IDR 1,500,000")
        self.assertEqual(format_rupiah(1_500_000, style="compact"), "Rp 1,5 juta")
        self.assertEqual(format_rupiah(2_500_000_000, style="compact"), "Rp 2,5 miliar")
        self.assertEqual(format_rupiah(12_000_000, style="compact"), "Rp 12 juta")
        self.assertEqual(format_rupiah(999_999, style="compact"), "Rp 1 juta")

    def test_rounds_half_up_not_half_to_even(self):
        self.assertEqual(format_rupiah(2.5), "Rp 3")
        self.assertEqual(format_rupiah(0.5), "Rp 1")
        self.assertEqual(format_rupiah(1234567.5), "Rp 1.234.568")

    def test_bad_style(self):
        with self.assertRaises(ValueError):
            format_rupiah(1, style="usd")

    def test_round_trips(self):
        rng = random.Random(7)
        for _ in range(500):
            n = rng.randrange(1, 10**12)
            self.assertEqual(parse_rupiah(format_rupiah(n)), n)
            self.assertEqual(parse_rupiah(format_rupiah(n, style="idr")), n)
            self.assertEqual(parse_rupiah(terbilang_rupiah(n)), n)


if __name__ == "__main__":
    unittest.main()
