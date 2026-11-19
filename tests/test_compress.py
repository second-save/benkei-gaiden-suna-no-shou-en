"""Tests for tools/compress.py against Benkei Gaiden: Suna no Shou ROM and reference dumps."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compress  # noqa: E402

ROM_PATH = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
REF_FONT_DIR = ROOT.parent / "Benkei" / "Font"


class TestCompression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()

    def test_font_entries_match_reference(self):
        expected_sizes = {92: 8192, 93: 8192, 94: 8192, 95: 8192, 96: 2816, 97: 4928}
        for idx, want_size in expected_sizes.items():
            dst, src, clen, raw = compress.decompress_entry(self.rom, idx)
            self.assertEqual(dst, 0x4000)
            self.assertEqual(len(raw), want_size)
            ref_path = REF_FONT_DIR / f"ben_{idx:03d}.raw"
            if ref_path.is_file():
                self.assertEqual(raw, ref_path.read_bytes(), f"Mismatch on ben_{idx:03d}.raw")

    def test_all_282_entries_roundtrip(self):
        for idx in range(compress.ENTRY_COUNT):
            _, _, _, raw = compress.decompress_entry(self.rom, idx)
            self.assertEqual(len(raw) % 32, 0, f"Entry {idx} not 32-byte aligned")
            recomp = compress.compress(raw)
            dec, dlen = compress.decompress_at(recomp, 0x008000)
            self.assertEqual(dlen, len(recomp), f"Entry {idx} trailing bytes")
            self.assertEqual(dec, raw, f"Entry {idx} roundtrip mismatch")


if __name__ == "__main__":
    unittest.main()
