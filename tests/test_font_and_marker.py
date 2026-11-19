"""Verification tests for Phase 4 English VWF engine, font, marker ROM, and window widths."""
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import build  # noqa: E402
import extract  # noqa: E402
import make_font  # noqa: E402
import tbl  # noqa: E402

ROM_PATH = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
SCRIPT_DIR = ROOT / "script"


class TestFontAndMarker(unittest.TestCase):
    def test_en_tbl_roundtrip(self):
        t = tbl.Table.load(ROOT / "tbl" / "en.tbl")
        ascii_sample = "".join(chr(c) for c in range(0x20, 0x7F))
        enc_ascii = t.encode(ascii_sample)
        self.assertEqual(enc_ascii, bytes(range(0x20, 0x7F)))
        dec_ascii, used = t.decode(enc_ascii, 0, length=len(enc_ascii))
        self.assertEqual(used, len(enc_ascii))
        self.assertEqual(dec_ascii, ascii_sample)

        ctrl_sample = (
            "{d0}{d9}{dA}{dF}{pad}{p11}{p1D}{furi_open}{furi_close}"
            "{name0}{name1}{name2}{name3}{name4}"
            "{pal0}{pal1}{wait:05}{nop:01}{nl}{page}Hello!{end}"
        )
        raw = t.encode(ctrl_sample)
        dec_ctrl, used_ctrl = t.decode(raw)
        self.assertEqual(used_ctrl, len(raw))
        self.assertEqual(dec_ctrl, ctrl_sample)

    def test_font_bins_invariants(self):
        font, widths = make_font.build_font_binaries()
        self.assertEqual(len(font), 2048)
        self.assertEqual(len(widths), 128)
        font_file = ROOT / "asm" / "font_en_1bpp.bin"
        widths_file = ROOT / "asm" / "font_en_widths.bin"
        if font_file.is_file() and widths_file.is_file():
            self.assertEqual(font_file.read_bytes(), font)
            self.assertEqual(widths_file.read_bytes(), widths)

        for code in range(128):
            adv = widths[code]
            self.assertGreaterEqual(adv, 3, f"width[{code:#04x}] < 3")
            self.assertLessEqual(adv, 8, f"width[{code:#04x}] > 8")
            if code <= 0x10:
                self.assertEqual(adv, 8, f"fixed token {code:#04x} must have width 8")
        self.assertEqual(widths[0x20], 4, "space width must be 4px")

        for code in range(0x21, 0x7F):
            adv = widths[code]
            rows = font[code * 16 : (code + 1) * 16]
            self.assertTrue(any(rows), f"glyph {code:#04x} ({chr(code)}) is blank")
            rightmost = -1
            for r in rows:
                for col in range(8):
                    if r & (0x80 >> col):
                        rightmost = max(rightmost, col)
            self.assertGreaterEqual(rightmost, 0)
            self.assertLessEqual(
                rightmost,
                adv - 2,
                f"glyph {chr(code)!r} rightmost col {rightmost} overlaps advance-1 ({adv})",
            )

    def test_marker_build_in_tempdir(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            out_rom = tmp_dir / "marker.sfc"
            writes_path = tmp_dir / "writes.txt"
            built, _, total_entries = build.build_expanded(
                mode="marker",
                lang="en",
                rom_path=ROM_PATH,
                script_dir=SCRIPT_DIR,
                out_path=out_rom,
                writes_path=writes_path,
                verify_sha1=False,
            )
            self.assertEqual(len(built), 0x200000)
            self.assertEqual(total_entries, 3197)
            self.assertEqual(built[extract.lorom_to_pc(0x00, 0xFFD7)], 0x0C)

            # Bank byte patches
            for bank, addr in build.BANK31_SITES:
                self.assertEqual(built[extract.lorom_to_pc(bank, addr)], 0x31, f"${bank:02X}:{addr:04X}")
            for bank, addr in build.BANK32_SITES:
                self.assertEqual(built[extract.lorom_to_pc(bank, addr)], 0x32, f"${bank:02X}:{addr:04X}")

            # Hook opcodes targeting bank $30
            jml_hooks = (
                (0x00, 0xEC06),
                (0x00, 0xCFDF),
                (0x00, 0xD043),
                (0x00, 0xE9A3),
                (0x00, 0xED80),
                (0x00, 0xF4D9),
                (0x00, 0xF573),
                (0x0C, 0xCB0A),
                (0x0C, 0xCD11),
                (0x0C, 0xCF25),
            )
            for bank, addr in jml_hooks:
                pc = extract.lorom_to_pc(bank, addr)
                self.assertEqual(built[pc], 0x5C, f"Missing JML at ${bank:02X}:{addr:04X}")
                self.assertEqual(built[pc + 3], 0x30, f"JML target bank != $30 at ${bank:02X}:{addr:04X}")

            pc_01a4db = extract.lorom_to_pc(0x01, 0xA4DB)
            self.assertEqual(built[pc_01a4db], 0x22)
            self.assertEqual(built[pc_01a4db + 3], 0x30)
            self.assertEqual(built[pc_01a4db + 4], 0xEA)

            pc_0b8f7b = extract.lorom_to_pc(0x0B, 0x8F7B)
            self.assertEqual(built[pc_0b8f7b], 0x22)
            self.assertEqual(built[pc_0b8f7b + 3], 0x30)

            # Verify redirect_tables.bin structure & sorting
            redir = (tmp_dir / "redirect_tables.bin").read_bytes()
            self.assertEqual(
                redir,
                built[extract.lorom_to_pc(0x30, 0xB000) : extract.lorom_to_pc(0x30, 0xB000) + len(redir)],
            )
            bases = struct.unpack_from("<4H", redir, 0)
            counts = struct.unpack_from("<4H", redir, 8)
            for i in range(4):
                self.assertGreater(counts[i], 0, f"Zero redirect count for bank ${0x1A + i:02X}")
                prev_addr = -1
                for j in range(counts[i]):
                    oa, na, nb = struct.unpack_from("<HHH", redir, bases[i] + j * 6)
                    self.assertGreater(oa, prev_addr, f"Unsorted orig_addr in bank ${0x1A + i:02X}")
                    prev_addr = oa
                    self.assertGreaterEqual(nb, 0x33)
                    self.assertLessEqual(nb, 0x3D)
                    self.assertGreaterEqual(na, 0x8000)

            # Verify party_names_en.bin and <= 48px limit
            pnames = (tmp_dir / "party_names_en.bin").read_bytes()
            widths = (ROOT / "asm" / "font_en_widths.bin").read_bytes()
            offs = struct.unpack_from("<5H", pnames, 0)
            for i, off in enumerate(offs):
                end = pnames.index(0xFF, off)
                raw = pnames[off:end]
                self.assertTrue(len(raw) > 0 and all(b < 0x80 for b in raw))
                self.assertLessEqual(sum(widths[b] for b in raw), 48)

            # Verify explicit $1C:88FC 00FE data span preserved while vacated text is 0xFF
            pc_88fc = extract.lorom_to_pc(0x1C, 0x88FC)
            self.assertEqual(built[pc_88fc : pc_88fc + 2], b"\x00\xfe")
            pc_1a8000 = extract.lorom_to_pc(0x1A, 0x8000)
            self.assertEqual(built[pc_1a8000 : pc_1a8000 + 8], b"\xff" * 8)

    def test_windows_json_covers_all_script_boxes(self):
        windows = json.loads((ROOT / "docs" / "windows.json").read_text(encoding="utf-8"))
        script_boxes: set[str] = set()
        for p in sorted(SCRIPT_DIR.glob("*.json")):
            doc = json.loads(p.read_text(encoding="utf-8"))
            for e in doc["entries"]:
                box = e.get("box", doc["box"])
                if box != "data":
                    script_boxes.add(box)

        missing = sorted(script_boxes - set(windows))
        self.assertEqual(missing, [], f"Missing boxes in docs/windows.json: {missing}")

        for name, spec in windows.items():
            self.assertIsInstance(spec["width_px"], int, name)
            self.assertGreater(spec["width_px"], 0, name)
            self.assertIsInstance(spec["max_lines"], int, name)
            self.assertGreater(spec["max_lines"], 0, name)
            self.assertEqual(spec["status"], "measured", name)
            self.assertTrue((ROOT / spec["shot"]).is_file(), f"Missing QA shot for {name}: {spec['shot']}")


if __name__ == "__main__":
    unittest.main()
