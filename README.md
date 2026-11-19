# nusantara

Most AI infrastructure assumes American defaults. In Indonesian text, money is written Rp 1.500.000 or 1,5 juta or 500 rb, chat is full of abbreviations like gak and bgt, dates use Agustus and Des, "setengah tiga" means half past two, and phone numbers appear as 0812, +62 812, or 62812. nusantara reads all of that into clean values before it reaches a model, a database, or a report, and writes values back out the way Indonesians write them. Standard library only, Python 3.10 to 3.13, typed.

It is a companion to [lisan](https://github.com/AndMaverick/lisan), which does the same job for Arabic. If you are building for regional markets and want a second opinion on architecture, you can [start a conversation](https://calendly.com/andmaverick?utm_source=github&utm_medium=repo&utm_campaign=nusantara).

## What it does

| Module | Reads | Writes |
|---|---|---|
| `money` | `Rp 1.500.000`, `1,5 juta`, `500 rb`, `12 jt`, `IDR 3.000.000`, "seratus ribu rupiah", "setengah juta"; every amount in a text, with positions | `format_rupiah` in full, compact or IDR style, half-up rounding |
| `words` | "seribu dua ratus tiga puluh empat" back to 1234 | `terbilang`, `terbilang_rupiah` (cheque and invoice wording), up to 10^15 - 1 |
| `dates` | `17 Agustus 2026`, `17 Agu`, `17/08/26`, `2026-08-17`, old spellings (Pebruari, Nopember), weekdays, relative words (besok, lusa, kemarin lusa, 2 minggu lalu), clock times (jam 8 malam, setengah tiga sore), WIB/WITA/WIT | `format_date`, zone conversion, fixed national holidays |
| `phone` | `0812-3456-7890`, `+62 812 3456 7890`, `62812...`, landlines with area, toll-free, extensions | E.164, national and international formats; operator and area from the prefix |
| `slang` | chat Indonesian: gak, bgt, udh, yg, bagus2 | normalized text, slang density, laughter detection |
| `address` | `Jl. Sudirman No. 5 RT 03/RW 04, Kel. Menteng, ...` | expanded abbreviations; street, number, RT, RW, kelurahan, kecamatan, city, province (38), postal code |
| `ids` | NIK (16 digits) and NPWP (15 digits) | structure of a NIK (region, birth date, gender), masking, NPWP formatting |

## Use

```python
from nusantara import (
    find_amounts, format_rupiah, normalize_phone, normalize_slang, parse_date, parse_datetime,
    parse_nik, parse_rupiah, parse_time, terbilang_rupiah,
)
from datetime import date

parse_rupiah("sekitar 1,5 juta")                 # 1500000
parse_rupiah("gajinya 12 jt per bulan")          # 12000000
[a.value for a in find_amounts("DP Rp 5.000.000 dan cicilan 750 rb")]   # [5000000, 750000]
format_rupiah(1500000)                           # 'Rp 1.500.000'
terbilang_rupiah(1250000)                        # 'Satu Juta Dua Ratus Lima Puluh Ribu Rupiah'

normalize_slang("gak udah deh, Budi bgt")        # 'tidak sudah deh, Budi sangat'
parse_date("Lahir 17 Agustus 2026")              # datetime.date(2026, 8, 17)
parse_date("besok", today=date(2026, 3, 31))     # datetime.date(2026, 4, 1)
parse_time("setengah tiga sore")                 # datetime.time(14, 30)
parse_datetime("Senin, 17 Agustus 2026 pukul 09.30 WITA")   # 2026-08-17 09:30 at UTC+8

normalize_phone("0812-3456-7890")                # '+6281234567890'
parse_nik("3174011508900001").birth_date         # datetime.date(1990, 8, 15)
```

Command line, with exit codes you can gate on (0 ok, 1 check failed, 2 error):

```
python -m nusantara money "bayar Rp 1,5 juta atau 500 rb" --require
python -m nusantara date "Selasa, 17 Agustus 2026" --strict-weekday    # exit 1: 17 Agustus 2026 is a Senin
python -m nusantara phone 12345                                         # exit 1
python -m nusantara nik 3174011508900001 --mask
```

`sh examples/demo.sh` runs every subcommand once.

## Design

- **Round trips are tested.** `terbilang` and `parse_terbilang` agree on every 7th integer below 200,000 and on random integers up to 10^15. `format_rupiah` and `parse_rupiah` agree on every 997th integer below 5,000,000.
- **Ambiguity is reported, not guessed.** "jam 12 pagi" raises with the reason. A separator that could be read two ways (`1.500 juta`, `1,500 juta`) is read the Indonesian way and flagged `ambiguous` on the amount. A written weekday that does not match its date sets `weekday_mismatch`. Impossible dates such as 31 Februari are skipped, never rolled over.
- **Indonesian conventions.** Dots are thousands separators and commas are decimals. Numeric dates are day first. "setengah tiga" is 2:30, half an hour before three. Two digit years use the POSIX pivot (68 and below is 20xx). "jam 12 malam" is midnight, "jam 12 siang" is noon.
- **Slang is conservative.** A reviewable table of about 160 entries, applied word by word. Words not in it are left untouched, including proper names. Extend it with `extra=` or case-preserving `preserve_case=True`.
- **Phone numbers converge.** Local, international and bare forms all become +62. Foreign and implausible numbers raise errors with the reason.
- **Personal data is masked on output.** The CLI never echoes a full NIK: the structure it prints carries the masked number (`317401******0001`), and `--mask` prints only that. The library has `mask_nik` for your own logs.
- **Old API kept.** Everything from 0.1 still works, and its tests still pass.

## Measured

`python examples/evaluate.py` runs regression sets and prints the counts. This is the output of that script at this commit:

```
rupiah amounts            19/19
dates                     10/10
clock times               10/10
phone numbers              8/8
slang (word by word)      10/10
terbilang round trip      28572/28572 (every 7th integer below 200,000)
rupiah format round trip  5016/5016 (every 997th integer below 5,000,000)
```

The case lists were written by the author of the parsers alongside the code, so they are regression sets that show the code does what was intended. They are not an independent benchmark, and 100 percent on them says nothing about text the author did not think of. Bring your own sample and run it through the CLI before you rely on any of this.

## Honest limits

- **Slang** is a small word-by-word table with no reordering, no context and no regional variants beyond what is listed. A word in the table is always replaced, even where the chat writer meant something else.
- **Addresses** are pattern based and need their markers (`Jl.`, `Kel.`, `Kec.`, `Kab.`, a postal code). An unmarked city such as "Jakarta Pusat" gives a province but no city. Free-form addresses with no markers return mostly empty fields.
- **NIK** checks structure only: length, a real birth date, the province code and the female day offset of 40. It does not verify that a person or a number exists. Province codes 92, 93, 95 and 96 are accepted but not named. The century of a two digit birth year is ambiguous and is documented in the code.
- **Phone operator** comes from the number prefix, which is the original allocation. Number portability means the current carrier can differ.
- **Holidays**: only fixed national dates are known. Movable holidays (Idul Fitri, Nyepi, Waisak and so on) are not computed.
- **Numbers with dots** such as "tahun 2.024" are read as amounts with a thousands separator, because that is what a dot usually is in Indonesian.
- **Shorthand** such as `2M` or `1,5T` is off by default because it is ambiguous; turn it on with `shorthand=True`.

## Tests

```
python -m unittest discover -s tests -t . -v
```

94 tests, run on Python 3.10 to 3.13 in CI with ruff and mypy in strict mode.

MIT licensed. Built by [AndMaverick LLC](https://www.andmaverick.com).

---

**Related reading:** [The Language They Did Not Build For](https://blog.andmaverick.com/the-language-they-did-not-build-for?utm_source=github&utm_medium=repo&utm_campaign=nusantara)

**If this is your problem.** If your data, language, or jurisdiction sits outside the assumptions of American AI infrastructure, that is work I do. Let us talk. [Begin a conversation](https://calendly.com/andmaverick?utm_source=github&utm_medium=repo&utm_campaign=nusantara).
