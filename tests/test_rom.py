"""Verify base ROM presence and SHA-1 digest."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_rom  # noqa: E402


class TestRomIntegrity(unittest.TestCase):
    def test_rom_sha1(self):
        check_rom.check()


if __name__ == "__main__":
    unittest.main()
