"""Master ROM builder for Benkei Gaiden: Suna no Shou (SNES)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import check_rom  # noqa: E402
import extract  # noqa: E402
import romdiff  # noqa: E402

DEFAULT_ROM = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
DEFAULT_SCRIPT_DIR = ROOT / "script"


def put(rom: bytearray, off: int, data: bytes, by: str, orig: bytes, writes: list[str]) -> None:
    """Write `data` at PC offset `off` and record original vs new hex for romdiff verification."""
    orig_slice = orig[off : off + len(data)]
    if len(orig_slice) < len(data):
        orig_slice = orig_slice + b"\xff" * (len(data) - len(orig_slice))
    writes.append(f"{off:X} {orig_slice.hex()} {data.hex()} {by}")
    rom[off : off + len(data)] = data


def build_identity(
    rom_path: Path = DEFAULT_ROM,
    script_dir: Path = DEFAULT_SCRIPT_DIR,
    out_path: Path = ROOT / "build" / "id.sfc",
    writes_path: Path | None = None,
    verify_sha1: bool = True,
) -> tuple[bytes, list[str], int]:
    """Repack all 17 script/table JSON files into a byte-identical SFC ROM."""
    if verify_sha1 and rom_path.resolve() == DEFAULT_ROM.resolve():
        check_rom.check()

    orig = rom_path.read_bytes()
    rom = bytearray(orig)
    tables = extract.load_tables(ROOT / "tbl")
    writes: list[str] = []
    total_entries = 0

    for spec in extract.REGIONS:
        json_path = script_dir / spec["name"]
        if not json_path.is_file():
            raise FileNotFoundError(f"Missing extracted script file: {json_path}")
        doc = json.loads(json_path.read_text(encoding="utf-8"))
        total_entries += len(doc["entries"])
        repacked = extract.repack_region(doc, tables, field="jp")
        start_pc = extract.lorom_to_pc(spec["bank"], spec["start"])
        end_pc = extract.lorom_to_pc(spec["bank"], spec["end"])
        if len(repacked) != end_pc - start_pc:
            raise ValueError(
                f"{spec['name']}: repacked size {len(repacked)} != expected {end_pc - start_pc}"
            )
        put(rom, start_pc, repacked, f"script:{spec['name']}", orig, writes)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    built = bytes(rom)
    out_path.write_bytes(built)

    wpath = writes_path if writes_path is not None else out_path.parent / "writes.txt"
    wpath.parent.mkdir(parents=True, exist_ok=True)
    with open(wpath, "w", encoding="utf-8", newline="\n") as f:
        for line in writes:
            f.write(line + "\n")

    errs, _ = romdiff.check(orig, built, set(), romdiff.load_writes(wpath))
    if errs:
        raise ValueError("romdiff failed:\n" + "\n".join(errs))
    if built != orig:
        raise ValueError("Identity build differs from source ROM")
    return built, writes, total_entries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("identity",), default="identity", help="Build mode")
    ap.add_argument("--lang", default="en", help="Target language code (e.g. en)")
    ap.add_argument("--rom", type=Path, default=DEFAULT_ROM, help="Clean base JP SFC ROM")
    ap.add_argument("--script-dir", type=Path, default=DEFAULT_SCRIPT_DIR, help="Script JSON directory")
    ap.add_argument("--out", type=Path, default=None, help="Output SFC ROM path")
    ap.add_argument("--writes", type=Path, default=None, help="Output write-log path for romdiff.py")
    args = ap.parse_args(argv)

    lang = args.lang.strip()
    if not lang:
        ap.error("--lang must be non-empty")

    out_path = args.out
    if out_path is None:
        out_path = ROOT / "build" / ("id.sfc" if args.mode == "identity" else f"benkei_suna_{lang}.sfc")

    built, _, total_entries = build_identity(
        rom_path=args.rom,
        script_dir=args.script_dir,
        out_path=out_path,
        writes_path=args.writes,
    )
    rel_out = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
    print(f"identity build ok: {len(built)} bytes, 0 diffs, {len(extract.REGIONS)} regions, {total_entries} entries -> {rel_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
