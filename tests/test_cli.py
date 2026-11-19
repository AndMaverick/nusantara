import contextlib
import io
import json
import subprocess
import sys
import unittest

from nusantara.cli import main


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_money(self):
        code, out, _ = run("money", "bayar Rp 1,5 juta dan 2 miliar")
        self.assertEqual(code, 0)
        self.assertEqual([x["value"] for x in json.loads(out)], [1500000, 2000000000])

    def test_money_require_gate(self):
        self.assertEqual(run("money", "tidak ada uang di sini", "--require")[0], 1)
        self.assertEqual(run("money", "tidak ada uang di sini")[0], 0)

    def test_say_and_unsay_round_trip(self):
        code, out, _ = run("say", "1234567")
        self.assertEqual(code, 0)
        self.assertEqual(run("unsay", out.strip())[1].strip(), "1234567")
        self.assertIn("rupiah", run("say", "5000", "--rupiah")[1].lower())

    def test_slang(self):
        self.assertEqual(run("slang", "gak bisa bgt")[1].strip(), "tidak bisa sangat")

    def test_date_and_weekday_gate(self):
        code, out, _ = run("date", "Senin, 17 Agustus 2026 pukul 09.30 WITA")
        data = json.loads(out)
        self.assertEqual((code, data["dates"][0]["date"], data["times"]), (0, "2026-08-17", ["09:30:00"]))
        self.assertTrue(data["datetime"].endswith("+08:00"))
        self.assertEqual(run("date", "Selasa, 17 Agustus 2026", "--strict-weekday")[0], 1)
        self.assertEqual(run("date", "Selasa, 17 Agustus 2026")[0], 0)

    def test_relative_date_needs_today(self):
        data = json.loads(run("date", "besok", "--today", "2026-03-31")[1])
        self.assertEqual(data["dates"][0]["date"], "2026-04-01")
        self.assertEqual(json.loads(run("date", "besok")[1])["dates"], [])
        data = json.loads(run("date", "besok jam 8 malam", "--today", "2026-03-31")[1])
        self.assertEqual(data["datetime"], "2026-04-01T20:00:00+07:00")

    def test_phone_exit_codes(self):
        code, out, _ = run("phone", "0812-3456-7890")
        self.assertEqual((code, json.loads(out)["e164"]), (0, "+6281234567890"))
        code, _, err = run("phone", "12345")
        self.assertEqual(code, 1)
        self.assertIn("invalid", err)

    def test_nik_exit_codes_and_masking(self):
        code, out, _ = run("nik", "3174011508900001")
        data = json.loads(out)
        self.assertEqual((code, data["province"], data["number"]), (0, "DKI Jakarta", "317401******0001"))
        self.assertEqual(run("nik", "3174011508900001", "--mask")[1].strip(), "317401******0001")
        self.assertEqual(run("nik", "3174019908900001")[0], 1)

    def test_address(self):
        data = json.loads(run("address", "Jl. Sudirman No. 5, Jakarta Pusat 10310")[1])
        self.assertEqual((data["street"], data["postal_code"]), ("Jalan Sudirman", "10310"))
        self.assertTrue(data["expanded"].startswith("Jalan Sudirman Nomor 5"))

    def test_bad_input_is_exit_2(self):
        code, _, err = run("say", str(10**21))
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("error:"))
        self.assertEqual(run("date", "x", "--today", "not-a-date")[0], 2)
        self.assertEqual(run("say", "-5")[1].strip(), "minus lima")

    def test_module_entry_point(self):
        proc = subprocess.run([sys.executable, "-m", "nusantara", "say", "21"], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "dua puluh satu"))


if __name__ == "__main__":
    unittest.main()
