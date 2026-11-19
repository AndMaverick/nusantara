import unittest
from datetime import date

from nusantara import (
    expand_address,
    find_province,
    format_npwp,
    is_laughter,
    mask_nik,
    normalize_phone,
    normalize_slang,
    parse_address,
    parse_nik,
    parse_npwp,
    parse_phone,
    slang_density,
)


class PhoneTests(unittest.TestCase):
    def test_every_written_form_gives_the_same_number(self):
        for raw in ["0812-3456-7890", "+62 812 3456 7890", "081234567890", "(0812) 3456 7890", "+62-812-3456-7890", "0812 3456 7890"]:
            self.assertEqual(parse_phone(raw).e164, "+6281234567890", raw)
            self.assertEqual(normalize_phone(raw), "+6281234567890", raw)

    def test_operator_comes_from_the_prefix(self):
        for raw, operator in [("0812 3456 7890", "Telkomsel"), ("0851 1234 5678", "Telkomsel"), ("0895 3456 7890", "Tri"), ("0881 2345 6789", "Smartfren")]:
            p = parse_phone(raw)
            self.assertEqual((p.kind, p.operator), ("mobile", operator), raw)

    def test_landline_has_area_and_no_operator(self):
        p = parse_phone("(021) 555 1234 ext 12")
        self.assertEqual((p.kind, p.area, p.operator, p.e164), ("landline", "Jakarta", None, "+62215551234"))

    def test_toll_free(self):
        self.assertEqual(parse_phone("0800-1-234-567").kind, "toll-free")

    def test_formats(self):
        p = parse_phone("081234567890")
        self.assertEqual(p.format("international"), "+62 812-3456-7890")
        self.assertEqual(p.format("national"), "0812-3456-7890")
        with self.assertRaises(ValueError):
            p.format("local")
        self.assertEqual(p.format("e164"), "+6281234567890")

    def test_rejections_say_why(self):
        for raw in ["08123", "12345", "+1 415 555 2671", "", "abc"]:
            with self.assertRaises(ValueError, msg=raw):
                parse_phone(raw)


class SlangTests(unittest.TestCase):
    def test_common_forms(self):
        self.assertEqual(normalize_slang("gak bisa bgt, yg penting udh sampe nih"), "tidak bisa sangat, yang penting sudah sampai ini")

    def test_reduplication(self):
        self.assertEqual(normalize_slang("bagus2 banget"), "bagus-bagus sangat")
        self.assertEqual(normalize_slang("bagus2 banget", reduplication=False), "bagus2 sangat")

    def test_unknown_words_are_left_alone(self):
        self.assertEqual(normalize_slang("Gaaak bisaaa"), "tidak bisaaa")  # only words in the table change, nothing is guessed
        self.assertEqual(normalize_slang("kucing lucu"), "kucing lucu")

    def test_extra_entries_and_case(self):
        self.assertEqual(normalize_slang("lol gk", extra={"lol": "tertawa"}), "tertawa tidak")
        self.assertEqual(normalize_slang("Gak Bisa", preserve_case=True), "Tidak Bisa")

    def test_density_and_laughter(self):
        self.assertEqual(slang_density("saya tidak bisa"), 0.0)
        self.assertGreater(slang_density("gak bisa bgt yg penting"), 0.5)
        self.assertTrue(is_laughter("wkwkwk"))
        self.assertFalse(is_laughter("halo"))

    def test_is_idempotent_on_its_own_output(self):
        once = normalize_slang("gak bisa bgt yg penting udh sampe")
        self.assertEqual(normalize_slang(once), once)


class AddressTests(unittest.TestCase):
    FULL = "Jl. Sudirman No. 5 RT 03/RW 04, Kel. Menteng, Kec. Menteng, Jakarta Pusat 10310"

    def test_expansion(self):
        self.assertEqual(expand_address(self.FULL), "Jalan Sudirman Nomor 5 RT 03/RW 04, Kelurahan Menteng, Kecamatan Menteng, Jakarta Pusat 10310")

    def test_parse_full_address(self):
        a = parse_address(self.FULL)
        self.assertEqual((a.street, a.number, a.rt, a.rw), ("Jalan Sudirman", "5", 3, 4))
        self.assertEqual((a.kelurahan, a.kecamatan, a.province, a.postal_code), ("Menteng", "Menteng", "DKI Jakarta", "10310"))
        self.assertIsNone(a.city)  # an unmarked Jakarta city gives no city: honest limit

    def test_marked_regency_and_province(self):
        a = parse_address("Perum Griya Asri Blok C3 No 7, Kab. Sleman, DI Yogyakarta 55281")
        self.assertEqual((a.city, a.province, a.postal_code, a.number), ("Kabupaten Sleman", "DI Yogyakarta", "55281", "7"))

    def test_pieces_that_are_absent_stay_none(self):
        a = parse_address("jln merdeka no 10 bandung")
        self.assertEqual((a.street, a.number, a.postal_code, a.province), ("Jalan Merdeka", "10", None, None))

    def test_provinces(self):
        self.assertEqual(find_province("tinggal di Jawa Barat"), "Jawa Barat")
        self.assertIsNone(find_province("tinggal di Mars"))


class IdTests(unittest.TestCase):
    def test_structure_of_a_male_nik(self):
        n = parse_nik("3174011508900001")
        self.assertTrue(n.valid)
        self.assertEqual((n.province, n.gender, n.birth_date, n.serial), ("DKI Jakarta", "male", date(1990, 8, 15), "0001"))
        self.assertEqual((n.province_code, n.regency_code, n.district_code), ("31", "74", "01"))

    def test_female_days_have_forty_added(self):
        n = parse_nik("3174015508900001")
        self.assertEqual((n.gender, n.birth_date), ("female", date(1990, 8, 15)))

    def test_bad_niks_say_why(self):
        bad_day = parse_nik("3174019908900001")
        self.assertFalse(bad_day.valid)
        self.assertIn("not a real date", bad_day.issues[0])
        short = parse_nik("317401150890000")
        self.assertFalse(short.valid)
        self.assertIn("16 digits", short.issues[0])
        self.assertFalse(parse_nik("abcdefghijklmnop").valid)

    def test_unnamed_papua_codes_are_accepted_but_not_named(self):
        n = parse_nik("9271011508900001")
        self.assertTrue(n.valid)
        self.assertEqual((n.province_code, n.province), ("92", None))

    def test_mask(self):
        self.assertEqual(mask_nik("3174011508900001"), "317401******0001")

    def test_npwp(self):
        self.assertEqual(format_npwp("123456789012345"), "12.345.678.9-012.345")
        self.assertEqual(parse_npwp("12.345.678.9-012.345"), "123456789012345")
        with self.assertRaises(ValueError):
            format_npwp("12345")


if __name__ == "__main__":
    unittest.main()
