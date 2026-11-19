"""Verification tests for Phase 3 script extraction and byte-identical identity build."""
import json
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
import romdiff  # noqa: E402

ROM_PATH = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
SCRIPT_DIR = ROOT / "script"


class TestIdentityAndExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = ROM_PATH.read_bytes()
        cls.tables = extract.load_tables(ROOT / "tbl")

    def test_identity_build_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            out_rom = tmp_dir / "id.sfc"
            writes_path = tmp_dir / "writes.txt"
            built, writes, _ = build.build_identity(
                rom_path=ROM_PATH,
                script_dir=SCRIPT_DIR,
                out_path=out_rom,
                writes_path=writes_path,
                verify_sha1=False,
            )
            self.assertEqual(built, self.orig)
            self.assertEqual(len(writes), len(extract.REGIONS))
            self.assertEqual(
                romdiff.check(self.orig, built, set(), romdiff.load_writes(writes_path)),
                ([], 0),
            )

    def test_script_100pct_rom_coverage_and_roundtrip(self):
        expected_files = {spec["name"] for spec in extract.REGIONS}
        actual_files = {p.name for p in SCRIPT_DIR.glob("*.json")}
        self.assertEqual(actual_files, expected_files)

        seen_ids: set[str] = set()
        covered_1a_1d: set[int] = set()
        by_name = {spec["name"]: spec for spec in extract.REGIONS}

        for spec in extract.REGIONS:
            doc = json.loads((SCRIPT_DIR / spec["name"]).read_text(encoding="utf-8"))
            table = self.tables[doc["table"]]
            bank = spec["bank"]
            start_pc = extract.lorom_to_pc(bank, spec["start"])
            end_pc = extract.lorom_to_pc(bank, spec["end"])

            if bank in (0x1A, 0x1B, 0x1C, 0x1D):
                span = set(range(start_pc, end_pc))
                self.assertFalse(covered_1a_1d & span, f"Overlapping coverage in {spec['name']}")
                covered_1a_1d.update(span)

            for entry in doc["entries"]:
                eid = entry["id"]
                self.assertNotIn(eid, seen_ids, f"Duplicate id {eid}")
                seen_ids.add(eid)
                self.assertNotRegex(entry["jp"], extract.HEX_ESCAPE_RE, f"Hex escape in {eid}")
                if entry["status"] == "data":
                    raw = bytes.fromhex(entry["raw_hex"])
                elif entry["status"] == "empty" and doc["kind"] == "sentinel_table":
                    raw = b""
                else:
                    raw = table.encode(entry["jp"])
                self.assertEqual(len(raw), entry["size"], f"Size mismatch for {eid}")
                addr = int(entry["addr"], 16)
                pc = extract.lorom_to_pc(bank, addr)
                self.assertEqual(raw, self.orig[pc : pc + entry["size"]], f"ROM mismatch for {eid}")

            self.assertEqual(
                extract.repack_region(doc, self.tables, field="jp"),
                self.orig[start_pc:end_pc],
                f"Region repack mismatch for {spec['name']}",
            )

        # Verify 100% of banks $1A-$1D (0x0D0000..0x0F0000): every uncovered byte must be 0xFF
        b1a_start = extract.lorom_to_pc(0x1A, 0x8000)
        b1d_end = extract.lorom_to_pc(0x1D, 0xFFFF) + 1
        uncovered_non_ff = [
            hex(off)
            for off in range(b1a_start, b1d_end)
            if off not in covered_1a_1d and self.orig[off] != 0xFF
        ]
        self.assertEqual(uncovered_non_ff, [], f"Uncovered non-0xFF bytes in $1A-$1D: {uncovered_non_ff[:10]}")

        # Verify $00:F534-$F551 party names preserve leading/trailing spaces verbatim
        party_doc = json.loads((SCRIPT_DIR / "party_names.json").read_text(encoding="utf-8"))
        self.assertEqual(len(party_doc["entries"]), 5)
        for p in party_doc["entries"]:
            self.assertEqual(p["size"], 6)
            self.assertTrue(p["jp"].startswith(" ") and p["jp"].endswith(" "), f"Stripped spaces in {p['id']}")

        # Verify explicit 2-byte non-text padding before $1C:88FE
        act2_1c = json.loads((SCRIPT_DIR / "act2_bank1c.json").read_text(encoding="utf-8"))
        idx_88fc = next(i for i, e in enumerate(act2_1c["entries"]) if e["id"] == "1C_88FC")
        self.assertEqual(act2_1c["entries"][idx_88fc]["status"], "data")
        self.assertEqual(act2_1c["entries"][idx_88fc]["raw_hex"], "00fe")
        self.assertEqual(act2_1c["entries"][idx_88fc + 1]["id"], "1C_88FE")
        self.assertEqual(act2_1c["entries"][idx_88fc + 1]["addr"], "0x88FE")
        self.assertIn("party_names.json", by_name)

    def test_extract_does_not_clobber_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            first = extract.extract_all(ROM_PATH, tmp_dir, force=False)
            self.assertEqual(len(first["written"]), len(extract.REGIONS))

            party_path = tmp_dir / "party_names.json"
            doc = json.loads(party_path.read_text(encoding="utf-8"))
            doc["entries"][0]["en"] = "Benkei"
            with open(party_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")

            second = extract.extract_all(ROM_PATH, tmp_dir, force=False)
            self.assertEqual(len(second["written"]), 0)
            self.assertEqual(len(second["skipped"]), len(extract.REGIONS))

            doc_after = json.loads(party_path.read_text(encoding="utf-8"))
            self.assertEqual(doc_after["entries"][0]["en"], "Benkei")


if __name__ == "__main__":
    unittest.main()
