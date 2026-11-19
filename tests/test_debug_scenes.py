"""Verification tests for Phase 2 cold-boot debug warp scenes and CLI."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.debug.regen_states import parse_scenes  # noqa: E402

EXPECTED_SCENES = [
    "title",
    "name_entry",
    "shumon_saizo",
    "shumon_courtyard",
    "happo_dungeon",
    "tosa_village",
    "act1_world",
    "battle_normal",
    "battle_rakan",
    "act2_prologue",
    "act2_town",
    "chapter_card",
    "ending_credits",
]
VALID_MODES = {"title", "name_entry", "map", "battle", "jump"}


class TestDebugScenes(unittest.TestCase):
    def test_debug_files_exist(self):
        for rel in (
            "tools/debug/scenes.lua",
            "tools/debug/warp.lua",
            "tools/debug/regen_states.py",
        ):
            self.assertTrue((ROOT / rel).is_file(), f"Missing {rel}")

    def test_parse_scenes_schema(self):
        scenes = parse_scenes()
        self.assertEqual([s["name"] for s in scenes], EXPECTED_SCENES)
        for s in scenes:
            self.assertIn(s["mode"], VALID_MODES, f"{s['name']} invalid mode {s['mode']!r}")
            self.assertTrue(s["desc"], f"{s['name']} missing desc")
            self.assertIsInstance(s["frames"], int)
            self.assertGreater(s["frames"], 0, f"{s['name']} frames must be > 0")
            self.assertIsInstance(s["shot_every"], int)
            self.assertGreater(s["shot_every"], 0, f"{s['name']} shot_every must be > 0")

    def test_regen_states_list_cli(self):
        r = subprocess.run(
            [sys.executable, "-X", "utf8", "tools/debug/regen_states.py", "--list"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in EXPECTED_SCENES:
            self.assertIn(name, r.stdout)


if __name__ == "__main__":
    unittest.main()
