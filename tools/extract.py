"""Extract and repack all Benkei Gaiden: Suna no Shou (SNES) script and table regions."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import tbl  # noqa: E402

DEFAULT_ROM = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
DEFAULT_OUT_DIR = ROOT / "script"
HEX_ESCAPE_RE = re.compile(r"\[[0-9A-F]{2}\]")

# Non-text bytes inside text blocks verified against pointer tables ($0D:B7CD -> $1C:88FE).
EXPLICIT_DATA_SPANS: dict[tuple[int, int], tuple[int, str]] = {
    (0x1C, 0x88FC): (2, "2-byte non-text padding before $1C:88FE ($0D:B7CD target)"),
}

REGIONS: tuple[dict, ...] = (
    {"name": "act1_bank1a.json", "bank": 0x1A, "start": 0x8000, "end": 0xA530, "kind": "ff_strings", "table": "jp.tbl", "box": "dialogue"},
    {"name": "act1_bank1b.json", "bank": 0x1B, "start": 0x8000, "end": 0xFF49, "kind": "ff_strings", "table": "jp.tbl", "box": "dialogue"},
    {"name": "act2_bank1c.json", "bank": 0x1C, "start": 0x8000, "end": 0xFA78, "kind": "ff_strings", "table": "jp.tbl", "box": "dialogue"},
    {"name": "act2_bank1d.json", "bank": 0x1D, "start": 0x8000, "end": 0xA57A, "kind": "ff_strings", "table": "jp.tbl", "box": "dialogue"},
    {"name": "sys_bank1d_a8.json", "bank": 0x1D, "start": 0xA800, "end": 0xB0AC, "kind": "ff_strings", "table": "jp.tbl", "box": "system"},
    {"name": "tbl_equip.json", "bank": 0x1D, "start": 0xB0AC, "end": 0xB5FA, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "equip_name"},
    {"name": "tbl_items.json", "bank": 0x1D, "start": 0xB5FA, "end": 0xB796, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "item_name"},
    {"name": "tbl_jutsu.json", "bank": 0x1D, "start": 0xB796, "end": 0xB8E9, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "jutsu_name"},
    {"name": "tbl_ougi.json", "bank": 0x1D, "start": 0xB8E9, "end": 0xB93D, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "ougi_name"},
    {"name": "tbl_enemies.json", "bank": 0x1D, "start": 0xB93D, "end": 0xC2D1, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "enemy_name", "notes": "furigana stripped at $1E by $0C:CD11"},
    {"name": "ui_bank1d_c2.json", "bank": 0x1D, "start": 0xC2D1, "end": 0xD834, "kind": "ff_strings", "table": "jp.tbl", "box": "ui"},
    {"name": "tbl_locations.json", "bank": 0x1D, "start": 0xD834, "end": 0xDC3E, "kind": "sentinel_table", "has_ff": False, "table": "jp.tbl", "box": "location_banner", "max_chars": 16},
    {"name": "tbl_equip_desc.json", "bank": 0x1D, "start": 0xDC3E, "end": 0xE828, "kind": "sentinel_table", "has_ff": True, "table": "jp.tbl", "box": "equip_desc"},
    {"name": "tbl_items_desc.json", "bank": 0x1D, "start": 0xE828, "end": 0xECCE, "kind": "sentinel_table", "has_ff": True, "table": "jp.tbl", "box": "item_desc"},
    {"name": "tbl_jutsu_desc.json", "bank": 0x1D, "start": 0xECCE, "end": 0xF59F, "kind": "sentinel_table", "has_ff": True, "table": "jp.tbl", "box": "jutsu_desc"},
    {"name": "credits_overlay.json", "bank": 0x1D, "start": 0xF59F, "end": 0xF7F9, "kind": "ff_strings", "table": "credits_jp.tbl", "box": "credits_overlay"},
    {"name": "party_names.json", "bank": 0x00, "start": 0xF534, "end": 0xF552, "kind": "fixed_records", "record_size": 6, "table": "jp.tbl", "box": "party_name"},
)


def lorom_to_pc(bank: int, addr: int) -> int:
    """Convert LoROM bank:addr ($8000-$FFFF) to PC file offset."""
    return (bank & 0x7F) * 0x8000 + (addr - 0x8000)


def _u16(rom: bytes, bank: int, addr: int) -> int:
    p = lorom_to_pc(bank, addr)
    return int.from_bytes(rom[p : p + 2], "little")


def load_tables(tbl_dir: Path = ROOT / "tbl") -> dict[str, tbl.Table]:
    """Load the project Japanese text and credits overlay tables."""
    return {
        "jp.tbl": tbl.Table.load(tbl_dir / "jp.tbl"),
        "credits_jp.tbl": tbl.Table.load(tbl_dir / "credits_jp.tbl"),
    }


def _decode_checked(table: tbl.Table, chunk: bytes, offset: int, length: int | None, ctx: str) -> tuple[str, int]:
    text, used = table.decode(chunk, offset, length=length)
    raw = chunk[offset : offset + used]
    m = HEX_ESCAPE_RE.search(text)
    if m:
        raise ValueError(f"{ctx}: unknown hex escape {m.group(0)} in {text!r}")
    if table.encode(text) != raw:
        raise ValueError(f"{ctx}: roundtrip mismatch for {text!r}")
    return text, used


def _box_for_ff_string(bank: int, region_start: int, addr: int, default_box: str) -> str:
    if bank == 0x1D and region_start == 0x8000:
        if 0x8000 <= addr <= 0x817A:
            return "prologue_crawl"
        if 0xA200 <= addr < 0xA57A:
            return "ending_crawl"
    return default_box


def _extract_ff_strings(rom: bytes, spec: dict, table: tbl.Table) -> list[dict]:
    bank, start, end = spec["bank"], spec["start"], spec["end"]
    off0, off1 = lorom_to_pc(bank, start), lorom_to_pc(bank, end)
    pos, entries = off0, []
    while pos < off1:
        cur_addr = start + (pos - off0)
        span = EXPLICIT_DATA_SPANS.get((bank, cur_addr))
        if span is not None:
            size, note = span
            raw = rom[pos : pos + size]
            entries.append({
                "id": f"{bank:02X}_{cur_addr:04X}",
                "addr": f"0x{cur_addr:04X}",
                "size": size,
                "jp": "",
                "en": "",
                "raw_hex": raw.hex(),
                "box": "data",
                "status": "data",
                "notes": note,
            })
            pos += size
            continue
        text, used = _decode_checked(table, rom, pos, None, f"${bank:02X}:{cur_addr:04X}")
        is_empty = text == "{end}"
        entries.append({
            "id": f"{bank:02X}_{cur_addr:04X}",
            "addr": f"0x{cur_addr:04X}",
            "size": used,
            "jp": text,
            "en": "{end}" if is_empty else "",
            "box": _box_for_ff_string(bank, start, cur_addr, spec["box"]),
            "status": "empty" if is_empty else "todo",
            "notes": "",
        })
        pos += used
    if pos != off1:
        raise ValueError(f"{spec['name']}: decoded end 0x{start + (pos - off0):04X} != 0x{end:04X}")
    return entries


def _extract_sentinel_table(rom: bytes, spec: dict, table: tbl.Table) -> tuple[int, list[dict]]:
    bank, start, end = spec["bank"], spec["start"], spec["end"]
    prefix = spec["name"][:-5]
    first = _u16(rom, bank, start)
    count = (first - start) // 2 - 1
    ptrs = [_u16(rom, bank, start + i * 2) for i in range(count + 1)]
    if ptrs[-1] != end:
        raise ValueError(f"{spec['name']}: sentinel 0x{ptrs[-1]:04X} != expected end 0x{end:04X}")
    entries = []
    default_note = spec.get("notes", "")
    for i in range(count):
        p0, p1 = ptrs[i], ptrs[i + 1]
        if p1 < p0:
            raise ValueError(f"{spec['name']}[{i}]: non-monotonic ptr 0x{p0:04X} > 0x{p1:04X}")
        size = p1 - p0
        entry = {
            "id": f"{prefix}_{i:03d}",
            "index": i,
            "addr": f"0x{p0:04X}",
            "size": size,
            "jp": "",
            "en": "",
            "box": spec["box"],
            "status": "empty" if size == 0 else "todo",
            "notes": default_note,
        }
        if "max_chars" in spec:
            entry["max_chars"] = spec["max_chars"]
        if size > 0:
            seg = rom[lorom_to_pc(bank, p0) : lorom_to_pc(bank, p1)]
            text, _ = _decode_checked(table, seg, 0, size, f"{spec['name']}[{i}] @ ${bank:02X}:{p0:04X}")
            if spec["has_ff"] and seg[-1] != 0xFF:
                raise ValueError(f"{spec['name']}[{i}] missing trailing $FF")
            entry["jp"] = text
        entries.append(entry)
    return first, entries


def _extract_fixed_records(rom: bytes, spec: dict, table: tbl.Table) -> list[dict]:
    bank, start, end, rsize = spec["bank"], spec["start"], spec["end"], spec["record_size"]
    if (end - start) % rsize != 0:
        raise ValueError(f"{spec['name']}: span not divisible by record_size {rsize}")
    count = (end - start) // rsize
    entries = []
    for i in range(count):
        addr = start + i * rsize
        seg = rom[lorom_to_pc(bank, addr) : lorom_to_pc(bank, addr + rsize)]
        text, _ = _decode_checked(table, seg, 0, rsize, f"party[{i}] @ ${bank:02X}:{addr:04X}")
        entries.append({
            "id": f"party_{i}",
            "index": i,
            "addr": f"0x{addr:04X}",
            "size": rsize,
            "max_bytes": rsize,
            "jp": text,
            "en": "",
            "box": spec["box"],
            "status": "todo",
            "notes": "",
        })
    return entries


def extract_region(rom: bytes, spec: dict, tables: dict[str, tbl.Table]) -> dict:
    """Extract and validate one region specification from ROM bytes."""
    table = tables[spec["table"]]
    doc: dict = {
        "file": spec["name"],
        "bank": f"0x{spec['bank']:02X}",
        "start": f"0x{spec['start']:04X}",
        "end": f"0x{spec['end']:04X}",
        "kind": spec["kind"],
        "table": spec["table"],
        "box": spec["box"],
    }
    if spec["kind"] == "ff_strings":
        doc["entries"] = _extract_ff_strings(rom, spec, table)
    elif spec["kind"] == "sentinel_table":
        data_start, entries = _extract_sentinel_table(rom, spec, table)
        doc["data_start"] = f"0x{data_start:04X}"
        doc["has_ff"] = spec["has_ff"]
        doc["entries"] = entries
    elif spec["kind"] == "fixed_records":
        doc["record_size"] = spec["record_size"]
        doc["entries"] = _extract_fixed_records(rom, spec, table)
    else:
        raise ValueError(f"Unknown region kind {spec['kind']!r}")
    return doc


def repack_region(doc: dict, tables: dict[str, tbl.Table], field: str = "jp") -> bytes:
    """Encode an extracted JSON document back into its raw ROM region bytes."""
    table = tables[doc["table"]]
    kind = doc["kind"]
    entries = doc["entries"]

    def encode_entry(entry: dict) -> bytes:
        if entry["status"] == "data":
            return bytes.fromhex(entry["raw_hex"])
        if entry["status"] == "empty" and kind == "sentinel_table":
            return b""
        return table.encode(entry[field])

    if kind == "ff_strings":
        return b"".join(encode_entry(e) for e in entries)

    if kind == "sentinel_table":
        cur = int(doc["data_start"], 16)
        ptrs: list[int] = []
        data_parts: list[bytes] = []
        for entry in entries:
            ptrs.append(cur)
            raw = encode_entry(entry)
            data_parts.append(raw)
            cur += len(raw)
        ptrs.append(cur)
        ptr_bytes = b"".join(p.to_bytes(2, "little") for p in ptrs)
        expected_table_len = int(doc["data_start"], 16) - int(doc["start"], 16)
        if len(ptr_bytes) != expected_table_len:
            raise ValueError(f"{doc['file']}: ptr table length {len(ptr_bytes)} != {expected_table_len}")
        return ptr_bytes + b"".join(data_parts)

    if kind == "fixed_records":
        rsize = doc["record_size"]
        out = bytearray()
        for entry in entries:
            raw = encode_entry(entry)
            if len(raw) != rsize:
                raise ValueError(f"{entry['id']}: encoded length {len(raw)} != {rsize}")
            out.extend(raw)
        return bytes(out)

    raise ValueError(f"Unknown region kind {kind!r}")


def extract_all(
    rom_path: Path = DEFAULT_ROM,
    out_dir: Path = DEFAULT_OUT_DIR,
    force: bool = False,
    check_only: bool = False,
) -> dict:
    """Extract all 17 script/table regions; never overwrites existing JSON unless force=True."""
    rom = rom_path.read_bytes()
    tables = load_tables()
    if not check_only:
        out_dir.mkdir(parents=True, exist_ok=True)
    written, skipped, total_entries, total_bytes = [], [], 0, 0
    for spec in REGIONS:
        doc = extract_region(rom, spec, tables)
        repacked = repack_region(doc, tables, field="jp")
        start_pc = lorom_to_pc(spec["bank"], spec["start"])
        end_pc = lorom_to_pc(spec["bank"], spec["end"])
        if repacked != rom[start_pc:end_pc]:
            raise ValueError(f"{spec['name']}: repacked bytes differ from ROM slice")
        total_entries += len(doc["entries"])
        total_bytes += len(repacked)
        out_path = out_dir / spec["name"]
        if check_only:
            continue
        if out_path.exists() and not force:
            skipped.append(spec["name"])
            continue
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=1, ensure_ascii=False))
            f.write("\n")
        written.append(spec["name"])
    return {
        "written": written,
        "skipped": skipped,
        "regions": len(REGIONS),
        "entries": total_entries,
        "bytes": total_bytes,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=DEFAULT_ROM, help="Source clean JP ROM path")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for JSON files")
    ap.add_argument("--force", action="store_true", help="Overwrite existing JSON files")
    ap.add_argument("--check-only", action="store_true", help="Validate extraction/repack without writing files")
    args = ap.parse_args(argv)
    res = extract_all(args.rom, args.out_dir, force=args.force, check_only=args.check_only)
    print(
        f"extract ok: {res['regions']} regions, {res['entries']} entries, {res['bytes']} bytes "
        f"(written={len(res['written'])}, skipped={len(res['skipped'])})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
