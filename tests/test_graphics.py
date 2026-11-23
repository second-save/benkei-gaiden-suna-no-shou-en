"""Unit tests for Phase 8 tile-drawn English graphics generation and ROM budget checks."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import compress  # noqa: E402
import make_gfx  # noqa: E402

ROM_PATH = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"


def _extract_16x16_grid(raw: bytes, quad: tuple[int, int, int, int]) -> list[list[int]]:
    tl, tr, bl, br = quad
    grid = [[0] * 16 for _ in range(16)]
    for dy, dx, tid in ((0, 0, tl), (0, 8, tr), (8, 0, bl), (8, 8, br)):
        px = make_gfx.decode_4bpp_tile(raw[tid * 32 : (tid + 1) * 32])
        for y in range(8):
            for x in range(8):
                grid[dy + y][dx + x] = px[y * 8 + x]
    return grid


class TestGraphicsGenerators(unittest.TestCase):
    def test_title_logo_bounds_and_palette(self):
        raw_101, tilemap = make_gfx.generate_title_logo()
        self.assertEqual(len(raw_101), 235 * 32)
        self.assertEqual(raw_101[:32], bytes(32))  # tile 0 must be transparent

        for tid in range(235):
            pxs = make_gfx.decode_4bpp_tile(raw_101[tid * 32 : (tid + 1) * 32])
            self.assertTrue(all(0 <= p <= 6 for p in pxs), f"Tile {tid} used palette index outside 0..6")

        self.assertEqual(len(tilemap), 2048)
        words = [int.from_bytes(tilemap[i : i + 2], "little") for i in range(0, 2048, 2)]
        self.assertTrue(all(0 <= w < 235 for w in words))

        # New Game / Continue menu box zone (rows 12..17) must stay completely empty
        for ty in range(12, 18):
            for tx in range(32):
                self.assertEqual(words[ty * 32 + tx], 0, f"Non-empty tile at menu row {ty}, col {tx}")

    def test_battle_mode_badges_2bpp_no_transparent_pixels(self):
        badge_a, badge_t = make_gfx.generate_battle_mode_badges()
        self.assertEqual(len(badge_a), 16)
        self.assertEqual(len(badge_t), 16)
        for label, raw in (("A", badge_a), ("T", badge_t)):
            pxs = make_gfx.decode_2bpp_tile(raw)
            self.assertTrue(all(p in (1, 2, 3) for p in pxs), f"Badge {label} contains transparent index 0")


@unittest.skipUnless(ROM_PATH.is_file(), "Clean JP ROM required for graphics ROM patch checks")
class TestGraphicsPatchesAgainstRom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.patches = make_gfx.build_patches(cls.rom)

    def test_title_subtitle_preserves_sunsoft_copyright(self):
        _, _, _, orig_281 = compress.decompress_entry(self.rom, make_gfx.TITLE_SUBTITLE_ENTRY)
        new_281 = self.patches["compressed_entries"][make_gfx.TITLE_SUBTITLE_ENTRY]
        self.assertEqual(len(new_281), 3072)
        self.assertEqual(new_281[64 * 32 :], orig_281[64 * 32 :])

    def test_shop_plaques_001_preserves_unpatched_tiles_and_top_bottom_frame(self):
        _, _, _, orig_001 = compress.decompress_entry(self.rom, make_gfx.TOWN_JP_PLAQUES_ENTRY)
        new_001 = self.patches["compressed_entries"][make_gfx.TOWN_JP_PLAQUES_ENTRY]
        self.assertEqual(len(new_001), 15360)

        quads = [
            (288, 289, 304, 305),
            (290, 291, 306, 307),
            (292, 293, 308, 309),
            (294, 295, 310, 311),
            (296, 297, 312, 313),
        ]
        patched_tids = {t for q in quads for t in q}
        self.assertEqual(len(patched_tids), 20)

        for tid in range(480):
            if tid not in patched_tids:
                self.assertEqual(
                    new_001[tid * 32 : (tid + 1) * 32],
                    orig_001[tid * 32 : (tid + 1) * 32],
                    f"#001 tile {tid} unexpectedly modified",
                )

        for quad in quads:
            og = _extract_16x16_grid(orig_001, quad)
            ng = _extract_16x16_grid(new_001, quad)
            for ry in (0, 1, 15):
                self.assertEqual(ng[ry], og[ry], f"#001 quad {quad} row {ry} frame changed")

    def test_shop_plaques_011_preserves_unpatched_tiles_and_stone_frame(self):
        _, _, _, orig_011 = compress.decompress_entry(self.rom, make_gfx.TOWN_CN_PLAQUES_ENTRY)
        new_011 = self.patches["compressed_entries"][make_gfx.TOWN_CN_PLAQUES_ENTRY]
        self.assertEqual(len(new_011), 15360)

        quads = [
            (202, 203, 218, 219),
            (204, 205, 220, 221),
            (234, 235, 250, 251),
            (236, 237, 252, 253),
        ]
        patched_tids = {t for q in quads for t in q}
        self.assertEqual(len(patched_tids), 16)

        for tid in range(480):
            if tid not in patched_tids:
                self.assertEqual(
                    new_011[tid * 32 : (tid + 1) * 32],
                    orig_011[tid * 32 : (tid + 1) * 32],
                    f"#011 tile {tid} unexpectedly modified",
                )

        wep_frame = _extract_16x16_grid(orig_011, (202, 203, 218, 219))
        for quad in quads:
            ng = _extract_16x16_grid(new_011, quad)
            for ry in (0, 1, 2, 14, 15):
                self.assertEqual(ng[ry], wep_frame[ry], f"#011 quad {quad} row {ry} frame mismatch")
            for ry in range(16):
                for rx in (0, 1, 15):
                    self.assertEqual(ng[ry][rx], wep_frame[ry][rx], f"#011 quad {quad} ({rx},{ry}) frame mismatch")

    def test_battle_digits_227_preserves_surrounding_tiles(self):
        _, _, _, orig_227 = compress.decompress_entry(self.rom, make_gfx.BATTLE_DIGITS_ENTRY)
        new_227 = self.patches["compressed_entries"][make_gfx.BATTLE_DIGITS_ENTRY]
        self.assertEqual(len(new_227), 5120)
        self.assertEqual(new_227[: 16 * 32], orig_227[: 16 * 32])
        self.assertEqual(new_227[26 * 32 :], orig_227[26 * 32 :])

    def test_compressed_entries_roundtrip_and_fit_banks_3e_3f(self):
        cur_bank = 0x3E
        cur_addr = 0x8000
        for idx, raw in self.patches["compressed_entries"].items():
            comp = compress.compress(raw)
            dec, dlen = compress.decompress_at(comp, 0x008000)
            self.assertEqual(dlen, len(comp), f"Entry #{idx:03d} stream length mismatch")
            self.assertEqual(dec, raw, f"Entry #{idx:03d} roundtrip mismatch")
            if cur_addr + len(comp) > 0x10000:
                cur_bank += 1
                cur_addr = 0x8000
            self.assertLessEqual(cur_bank, 0x3F, f"Entry #{idx:03d} overflowed Banks $3E-$3F")
            cur_addr += len(comp)


if __name__ == "__main__":
    unittest.main()
