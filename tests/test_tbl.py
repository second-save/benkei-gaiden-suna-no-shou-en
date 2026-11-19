"""Verification tests for tbl/jp.tbl and tbl/credits_jp.tbl against base ROM."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import tbl  # noqa: E402

ROM_PATH = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"


def lorom(bank: int, addr: int) -> int:
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def u16(rom: bytes, bank: int, addr: int) -> int:
    p = lorom(bank, addr)
    return int.from_bytes(rom[p : p + 2], "little")


def parse_ptr_table(rom: bytes, tbl_addr: int) -> list[tuple[int, int]]:
    first = u16(rom, 0x1D, tbl_addr)
    count = (first - tbl_addr) // 2 - 1  # final word is sentinel end address
    ptrs = [u16(rom, 0x1D, tbl_addr + i * 2) for i in range(count + 1)]
    return [(ptrs[i], ptrs[i + 1]) for i in range(count)]


class TestTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.jp = tbl.Table.load(ROOT / "tbl" / "jp.tbl")
        cls.cred = tbl.Table.load(ROOT / "tbl" / "credits_jp.tbl")

    def test_no_duplicate_values_in_tbl_files(self):
        for name in ("jp.tbl", "credits_jp.tbl"):
            seen = {}
            for lineno, raw in enumerate((ROOT / "tbl" / name).read_text("utf-8-sig").splitlines(), 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                k, _, v = line.partition("=")
                self.assertNotIn(v, seen, f"{name}:{lineno} duplicate value {v!r} for {k} (prev {seen.get(v)})")
                seen[v] = k

    def test_standard_text_roundtrip_zero_unknowns(self):
        ranges = [
            (0x1A, 0x8000, 0xA52F),
            (0x1B, 0x8000, 0xFF48),
            (0x1C, 0x8000, 0xFA77),
            (0x1D, 0x8000, 0xA579),
            (0x1D, 0xA800, 0xB0AC),
            (0x1D, 0xB254, 0xB5FA),
            (0x1D, 0xB660, 0xB796),
            (0x1D, 0xB7F0, 0xB8E9),
            (0x1D, 0xB8F9, 0xB93D),
            (0x1D, 0xBA8F, 0xC2D1),
            (0x1D, 0xC2D1, 0xD834),
            (0x1D, 0xD91C, 0xDC3E),
            (0x1D, 0xDDE6, 0xE828),
            (0x1D, 0xE88A, 0xECCE),
            (0x1D, 0xED5E, 0xF59F),
            (0x00, 0xF534, 0xF552),  # 5 default party names
        ]
        for bank, s, e in ranges:
            chunk = self.rom[lorom(bank, s) : lorom(bank, e)]
            text, used = self.jp.decode(chunk, 0, length=len(chunk))
            self.assertEqual(used, len(chunk))
            self.assertNotRegex(text, r"\[[0-9A-F]{2}\]", f"Unknown byte in ${bank:02X}:{s:04X}..${e:04X}")
            self.assertEqual(self.jp.encode(text), chunk, f"Roundtrip mismatch in ${bank:02X}:{s:04X}")

    def test_pointer_tables_and_known_strings(self):
        for tbl_addr, expected_count in [
            (0xB0AC, 211),
            (0xB5FA, 50),
            (0xB796, 44),
            (0xB8E9, 7),
            (0xB93D, 168),
            (0xD834, 115),
            (0xDC3E, 211),
            (0xE828, 48),
            (0xECCE, 71),
        ]:
            entries = parse_ptr_table(self.rom, tbl_addr)
            self.assertEqual(len(entries), expected_count)
            for p0, p1 in entries:
                if p1 <= p0:
                    continue
                seg = self.rom[lorom(0x1D, p0) : lorom(0x1D, p1)]
                text, _ = self.jp.decode(seg, 0, length=len(seg))
                self.assertNotRegex(text, r"\[[0-9A-F]{2}\]")
                self.assertEqual(self.jp.encode(text), seg)

        # Spot-check known strings
        locs = parse_ptr_table(self.rom, 0xD834)
        p0, p1 = locs[41]
        loc41, _ = self.jp.decode(self.rom[lorom(0x1D, p0) : lorom(0x1D, p1)], 0, length=p1 - p0)
        self.assertEqual(loc41, "才蔵の部屋")

    def test_credits_overlay_roundtrip_zero_unknowns(self):
        chunk = self.rom[lorom(0x1D, 0xF59F) : lorom(0x1D, 0xF7F8)]
        text, used = self.cred.decode(chunk, 0, length=len(chunk))
        self.assertEqual(used, len(chunk))
        self.assertNotRegex(text, r"\[[0-9A-F]{2}\]")
        self.assertEqual(self.cred.encode(text), chunk)
        self.assertIn("制作{end}", text)
        self.assertIn("村田  肇{end}", text)
        self.assertIn("{sF088}田 則昭{end}", text)


if __name__ == "__main__":
    unittest.main()
