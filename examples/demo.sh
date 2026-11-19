#!/usr/bin/env sh
# Every subcommand once. Run from the repository root: sh examples/demo.sh
set -e
python -m nusantara money "bayar Rp 1,5 juta atau 500 rb"
python -m nusantara say 1234567
python -m nusantara say 5000 --rupiah
python -m nusantara slang "gak bisa bgt, yg penting udh sampe"
python -m nusantara date "Senin, 17 Agustus 2026 pukul 09.30 WITA"
python -m nusantara date "besok jam 8 malam" --today 2026-03-31
python -m nusantara phone "0812-3456-7890"
python -m nusantara nik 3174011508900001
python -m nusantara address "Jl. Sudirman No. 5 RT 03/RW 04, Kel. Menteng, Kec. Menteng, Jakarta Pusat 10310"
