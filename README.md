# nusantara

Most AI infrastructure assumes American defaults. In Indonesian text, money is written Rp 1.500.000 or 1,5 juta or 500 rb, chat is full of abbreviations like gak and bgt, dates use Agustus and Des, and phone numbers appear as 0812, +62 812, or 62812. nusantara normalizes these into clean values before they reach a model, a database, or a report. Standard library only.

It is a companion to [lisan](https://github.com/AndMaverick/lisan), which does the same job for Arabic. If you are building for regional markets and want a second opinion on architecture, you can [start a conversation](https://calendly.com/andmaverick/30min?utm_source=github&utm_medium=repo&utm_campaign=nusantara).

## Use

```python
from nusantara import format_rupiah, normalize_phone, normalize_slang, parse_date, parse_rupiah

parse_rupiah("sekitar 1,5 juta")            # 1500000
parse_rupiah("gajinya 12 jt per bulan")     # 12000000
format_rupiah(1500000)                      # 'Rp 1.500.000'
normalize_slang("Gak udah deh, Budi bgt")   # 'tidak sudah deh, Budi sangat'
parse_date("Lahir 17 Agustus 2026")         # datetime.date(2026, 8, 17)
normalize_phone("0812-3456-7890")           # '+6281234567890'
```

## Design

- **Units and separators.** Dots as thousands separators, commas as decimals, and the units ribu, juta, miliar, triliun with their short forms.
- **Slang is conservative.** A small, reviewable dictionary. Words not in it are left untouched, including proper names.
- **Phone numbers converge.** Local, international, and bare forms all become +62 form. Foreign and implausibly short numbers raise errors.
- **A starting point.** Colloquial Indonesian is large and regional. The slang table is intentionally small and meant to be extended with your own data.

## Tests

```
python -m unittest discover -s tests -t . -v
```

MIT licensed. Built by [AndMaverick LLC](https://www.andmaverick.com).

---

**Related reading:** [The Language They Did Not Build For](https://blog.andmaverick.com/the-language-they-did-not-build-for?utm_source=github&utm_medium=repo&utm_campaign=nusantara)

**If this is your problem.** If your data, language, or jurisdiction sits outside the assumptions of American AI infrastructure, that is work I do. Let us talk. [Begin a conversation](https://calendly.com/andmaverick?utm_source=github&utm_medium=repo&utm_campaign=nusantara).
