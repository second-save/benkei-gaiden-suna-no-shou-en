"""Unit tests for tools/lint.py, tools/fit.py, and tools/batches.py."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import batches  # noqa: E402
import fit  # noqa: E402
import lint  # noqa: E402


class TestLintAndBatches(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.widths = lint.load_widths()
        cls.windows = lint.load_windows()
        cls.en_table = lint.load_en_table()
        cls.terms = lint.parse_glossary()

    def test_measure_line_px_rules(self):
        self.assertEqual(lint.measure_line_px("Sen", self.widths), 16)
        self.assertEqual(lint.measure_line_px("Ryo", self.widths), 16)
        self.assertEqual(lint.measure_line_px("New Game", self.widths), 47)
        # {name0} always reserves 48px
        self.assertEqual(lint.measure_line_px("{name0}: Hi", self.widths), 48 + self.widths[ord(":")] + self.widths[ord(" ")] + self.widths[ord("H")] + self.widths[ord("i")])
        # {pad} flushes partial tile to next multiple of 8, then adds 8px
        self.assertEqual(lint.measure_line_px("{pad}", self.widths), 8)
        self.assertEqual(lint.measure_line_px("A{pad}B", self.widths), 8 + 8 + self.widths[ord("B")])
        # 8x32 fixed-grid credits/locations
        self.assertEqual(lint.measure_line_px("Ichiro Nakamura", self.widths, fixed_char_px=8), 15 * 8)

    def test_narrow_box_overrides(self):
        self.assertEqual(lint.box_spec_for({"id": "1D_C7A3", "box": "ui"}, windows=self.windows)[0], "title_menu")
        self.assertEqual(lint.box_spec_for({"id": "1D_C427", "box": "ui"}, windows=self.windows)[0], "battle_cmd")
        self.assertEqual(lint.box_spec_for({"id": "1D_C395", "box": "ui"}, windows=self.windows)[0], "status_lv")
        self.assertEqual(lint.box_spec_for({"id": "1D_C3F3", "box": "ui"}, windows=self.windows)[0], "status_slash")
        self.assertEqual(lint.box_spec_for({"id": "1D_C411", "box": "ui"}, windows=self.windows)[0], "status_currency")
        self.assertEqual(lint.box_spec_for({"id": "1D_8178", "box": "prologue_crawl"}, windows=self.windows)[0], "dialogue")
        self.assertEqual(lint.box_spec_for({"id": "1D_F7B9", "box": "credits_overlay"}, windows=self.windows)[0], "credits_overlay_top")
        self.assertEqual(lint.box_spec_for({"id": "1D_F7BE", "box": "credits_overlay"}, windows=self.windows)[0], "credits_overlay_bottom")

    def test_lint_checks(self):
        dlg_entry = {"id": "1A_TEST", "jp": "才蔵「{name0}、行くぞ{end}", "box": "dialogue", "addr": "0x8000"}
        # Clean pass
        ok = lint.lint_entry(
            dlg_entry,
            'Saizo: "{name0}, let\'s move!{end}',
            terms=self.terms,
            widths=self.widths,
            en_table=self.en_table,
            windows=self.windows,
        )
        self.assertEqual(ok, [])

        # Missing glossary term & missing {end}
        bad1 = lint.lint_entry(dlg_entry, "Old man: Go, {name0}!", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows)
        self.assertTrue(any("glossary" in p for p in bad1))
        self.assertTrue(any("{end}" in p for p in bad1))

        # Staff Credits words (e.g. 協力) must not false-positive in normal dialogue
        self.assertEqual(
            lint.lint_entry(
                {"id": "1A_STAFF_FP", "jp": "みなで協力しよう{end}", "box": "dialogue", "addr": "0x8020"},
                "Let's all work together!{end}",
                terms=self.terms,
                widths=self.widths,
                en_table=self.en_table,
                windows=self.windows,
            ),
            [],
        )

        # Avoid term + honorific + glued ordinal + a {name0}
        bad2 = lint.lint_entry(
            dlg_entry,
            "Saizo-dono: Saizou is a {name0} and {name0}th!{end}",
            terms=self.terms,
            widths=self.widths,
            en_table=self.en_table,
            windows=self.windows,
        )
        self.assertTrue(any("Avoid" in p for p in bad2))
        self.assertTrue(any("honorific" in p for p in bad2))
        self.assertTrue(any("ordinal" in p for p in bad2))
        self.assertTrue(any("a/an" in p for p in bad2))

        # Unencodable Japanese / curly quotes
        bad3 = lint.lint_entry(dlg_entry, "Saizo: “Go, {name0}!”{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows)
        self.assertTrue(any("non-ASCII" in p for p in bad3))

        # Narrow box overflow (battle_cmd <= 40px, status_currency <= 16px, credits top <= 12ch)
        self.assertNotEqual(
            lint.lint_entry({"id": "1D_C427", "jp": "攻撃{end}", "box": "ui", "addr": "0xC427"}, "Obliterate{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )
        self.assertEqual(
            lint.lint_entry({"id": "1D_C411", "jp": "銭{end}", "box": "ui", "addr": "0xC411"}, "Sen{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )
        self.assertEqual(
            lint.lint_entry({"id": "1D_F7B9", "jp": "脚本{end}", "box": "credits_overlay", "addr": "0xF7B9"}, "SCENARIO{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )
        self.assertNotEqual(
            lint.lint_entry({"id": "1D_F7B9", "jp": "脚本{end}", "box": "credits_overlay", "addr": "0xF7B9"}, "SCENARIO_LONG{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )

        # Name entry grid 16-byte enforcement
        grid_e = {"id": "1D_C451", "jp": "{pad}あ{pad}{pad}い{pad}{pad}う{pad}{pad}え{pad}{pad}お{pad}{end}", "box": "ui", "addr": "0xC451"}
        self.assertEqual(
            lint.lint_entry(grid_e, "{pad}A{pad}{pad}B{pad}{pad}C{pad}{pad}D{pad}{pad}E{pad}{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )
        self.assertNotEqual(
            lint.lint_entry(grid_e, "{pad}A{pad}B{pad}C{pad}D{pad}E{pad}{end}", terms=self.terms, widths=self.widths, en_table=self.en_table, windows=self.windows),
            [],
        )

        # Stub last word check
        stub = lint.lint_entry(
            {"id": "1A_STUB", "jp": "こんにちは{end}", "box": "dialogue", "addr": "0x8010"},
            "Welcome to Shumon Fort{nl}now{end}",
            terms=self.terms,
            widths=self.widths,
            en_table=self.en_table,
            windows=self.windows,
        )
        self.assertTrue(any("stub" in p for p in stub), stub)

        # Single-line $00:E762/$00:E76B parser strings must reject {nl}
        for bad_single in (
            {"id": "1D_AE39", "jp": "旅の記録が壊れています！！{end}", "box": "system", "addr": "0xAE39"},
            {"id": "1D_AD9D", "jp": "文永の役（1274年）より2年後ー{end}", "box": "fullscreen_card", "addr": "0xAD9D"},
        ):
            res = lint.lint_entry(
                bad_single,
                "Bad{nl}line{end}",
                terms=self.terms,
                widths=self.widths,
                en_table=self.en_table,
                windows=self.windows,
            )
            self.assertTrue(any("single-line" in p for p in res), res)

    def test_fit_wrap(self):
        sample = 'Hayate: "My lord Saizo, it has been too long. I come bearing urgent word from the Emperor himself!"{end}'
        wrapped = fit.format_box(sample, box="dialogue")
        for p in wrapped.split("{page}"):
            lines = p.split("{nl}")
            self.assertLessEqual(len(lines), 3)
            for l in lines:
                self.assertLessEqual(lint.measure_line_px(l, self.widths), 192, l)

    def test_batches_selftest(self):
        batches._selftest()


if __name__ == "__main__":
    unittest.main()
