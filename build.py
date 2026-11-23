"""Master ROM builder for Benkei Gaiden: Suna no Shou (SNES)."""
from __future__ import annotations

import argparse
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import check_rom  # noqa: E402
import compress  # noqa: E402
import extract  # noqa: E402
import make_font  # noqa: E402
import make_gfx  # noqa: E402
import romdiff  # noqa: E402
import tbl  # noqa: E402

DEFAULT_ROM = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
DEFAULT_SCRIPT_DIR = ROOT / "script"
ASAR_BIN = ROOT / "tools" / "asar" / "asar"
ENGINE_ASM = ROOT / "asm" / "engine.asm"
EXPANDED_ROM_SIZE = 0x200000  # 2 MiB LoROM

MARKER_PARTY_NAMES = ("Fudo", "Mikage", "Tokoyo", "Byakuren", "Meisa")

CTRL_TOKEN_RE = re.compile(r"\{([^}]+)\}")

BANK31_SITES: tuple[tuple[int, int], ...] = (
    (0x00, 0xAF77), (0x00, 0xAF7D), (0x00, 0xAF87),
    (0x00, 0xB440), (0x00, 0xB47A), (0x00, 0xBEDC),
    (0x00, 0xBEE2), (0x00, 0xBEEC), (0x00, 0xD01E),
    (0x0B, 0x8F6F), (0x0B, 0x8F76),
    (0x0C, 0xA3F5), (0x0C, 0xA3FC), (0x0C, 0xA4A5), (0x0C, 0xA4AC),
    (0x0C, 0xA6FC), (0x0C, 0xA6FF), (0x0C, 0xA702),
    (0x0C, 0xB89E), (0x0C, 0xBB49), (0x0C, 0xBB84), (0x0C, 0xBF14),
    (0x0C, 0xC82F), (0x0C, 0xC835), (0x0C, 0xC83B),
    (0x0C, 0xC841), (0x0C, 0xCA46), (0x0C, 0xF7FA), (0x0C, 0xF81C),
)
BANK32_SITES: tuple[tuple[int, int], ...] = (
    (0x00, 0xB49D), (0x00, 0xB4D2), (0x0C, 0xBDCA),
)

SENTINEL_BANK_ASSIGN: dict[str, int] = {
    "tbl_equip.json": 0x31,
    "tbl_items.json": 0x31,
    "tbl_jutsu.json": 0x31,
    "tbl_ougi.json": 0x31,
    "tbl_enemies.json": 0x31,
    "tbl_locations.json": 0x31,
    "tbl_equip_desc.json": 0x32,
    "tbl_items_desc.json": 0x32,
    "tbl_jutsu_desc.json": 0x32,
}

PROLOGUE_TORTURE: dict[str, str] = {
    "1D_8000": "Sphinx of black quartz, judge!{end}",
    "1D_801A": "ABCDEFGHIJKLMNOPQRSTUVWXYZ 012345{end}",
    "1D_8036": "abcdefghijklmnopqrstuvwxyz 6789!?{end}",
    "1D_8051": ".,:;()-+/&%#=$@*[]<>'\" |\\^_`~{end}",
    "1A_8000": (
        "Sphinx of black quartz, judge!{nl}"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ 01234{nl}"
        "abcdefghijklmnopqrstuvwxyz 56789"
        "{page}{name0}: !?\"'.,:;()-+/&%#=$@*[]{page}"
        "Pg2: {name1} {name2} test.{page}"
        "Pg3: Saizo says move out.{page}"
        "Pg4: Aye.{page}"
        "Pg5: Lead {name0} cleanly.{page}"
        "Pg6: Tell His Majesty.{page}"
        "Pg7: Enemy agents close in.{page}"
        "Pg8: Stay sharp!{end}"
    ),
}


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


def _check_prepatch_rom(orig: bytes) -> None:
    """Assert expected clean JP ROM bytes before applying bank/hook patches."""
    if len(orig) != 0x180000:
        raise ValueError(f"Expected 1.5 MiB clean ROM (0x180000 B), got {len(orig):#x}")
    if orig[extract.lorom_to_pc(0x00, 0xFFD7)] != 0x0B:
        raise ValueError("Unexpected $00:FFD7 ROM size byte in clean ROM")
    for bank, addr in BANK31_SITES + BANK32_SITES:
        pc = extract.lorom_to_pc(bank, addr)
        if orig[pc] != 0x1D:
            raise ValueError(f"Expected bank byte 0x1D at ${bank:02X}:{addr:04X}, got {orig[pc]:#04x}")
    checks = (
        (0x00, 0x8090, "2027f10c0c0806"),
        (0x00, 0x87DC, "a91685a0a91485a1a90785a2a90685a3"),
        (0x02, 0xBD3F, "226be7009dad040c"),
        (0x02, 0xBD77, "226be700b5ad0a0c"),
        (0x0B, 0x8F7B, "2206ec00"),
        (0x0B, 0x8F90, "38a910e5b0"),
        (0x0B, 0x8FB3, "20bb8f"),
        (0x0B, 0x901C, "08c2200a"),
        (0x01, 0xA2A2, "a20000e220"),
        (0x01, 0x99C4, "226be700d1c20604226be700ecc61604"),
        (0x01, 0xA34E, "f0a2f0cff0bbff"),
        (0x01, 0xA4DB, "a91d008502"),
        (0x0C, 0xC24F, "ad5218eba20c0a2014c2a90da2120a"),
        (0x0C, 0xC29A, "a217c4a90eeb"),
        (0x0C, 0xC6FF, "eba911a00d0820f5baa20900"),
        (0x0C, 0xC726, "a9118d5e19"),
        (0x0C, 0xCB0A, "e220bba0"),
        (0x0C, 0xCD11, "c22029ff"),
        (0x0C, 0xCF25, "a6aba000"),
        (0x0C, 0xA5E4, "a9462092aa"),
        (0x0C, 0xA617, "a9392092aa"),
        (0x0C, 0xA621, "a9382092aa"),
        (0x0C, 0xA8B7, "a939eba93920a6a9"),
        (0x0C, 0xA913, "a9572092aa"),
        (0x0C, 0xA97C, "a939eba93920a6a9"),
        (0x0C, 0xA98A, "a939eba93520a6a9"),
        (0x0C, 0xA998, "a939eba93920a6a9"),
        (0x0C, 0xA9C4, "a9392092aa"),
        (0x0C, 0xBB54, "a00a0084a8a910e4a8f0069d801e"),
        (0x0C, 0xC130, "48a2fab58600a91d8502"),
        (0x0C, 0xBFA8, "a2f4548e821e"),
        (0x0C, 0xD516, "a2f321"),
        (0x0C, 0xD521, "a28e8a8e801e"),
        (0x0B, 0x9095, "ff00ff00ff00ff00ff00ff00ff00ff00"),
        (0x0B, 0x9135, "ff74ffc47fffdfbfbfd5fff5bb45caf5ff18ffffbf449f64db3cff18ff6cbbc7"),
        (
            0x09,
            0xDA78,
            "0000000000000000000000000000000000000000000000000000000000000000"
            "000000000000000000005700580059005a005b00000000000000000000000000",
        ),
        (0x09, 0xCBA8, "08c220a918808d800ca90800"),
        (0x0E, 0x8EB2, "00c8002000a004208100082081200c2080"),
    )
    for bank, addr, hex_exp in checks:
        pc = extract.lorom_to_pc(bank, addr)
        exp = bytes.fromhex(hex_exp)
        got = orig[pc : pc + len(exp)]
        if got != exp:
            raise ValueError(f"Unexpected bytes at ${bank:02X}:{addr:04X}: got {got.hex()}, expected {hex_exp}")


def _preserved_tokens(jp_text: str) -> list[str]:
    """Return engine-significant tokens excluding {end} and ben_097 {sF0xx} aliases."""
    out = []
    for tok in CTRL_TOKEN_RE.findall(jp_text):
        if tok == "end" or tok.startswith("sF"):
            continue
        out.append("{" + tok + "}")
    return out


def _marker_string(doc_name: str, entry: dict, idx: int, en_table: tbl.Table) -> bytes:
    """Generate deterministic printable-ASCII marker payload preserving engine contracts."""
    if entry.get("status") == "data":
        return bytes.fromhex(entry["raw_hex"])
    if entry.get("status") == "empty":
        return b"" if doc_name.startswith("tbl_") else b"\xff"

    eid = entry["id"]
    jp = entry["jp"]
    if eid in PROLOGUE_TORTURE:
        return en_table.encode(PROLOGUE_TORTURE[eid])

    if doc_name == "tbl_locations.json":
        return en_table.encode(f"Loc {idx:03d}")
    if doc_name == "tbl_enemies.json":
        return en_table.encode(f"Enemy {idx:03d}")
    if doc_name == "tbl_equip.json":
        return en_table.encode(f"Eq {idx:03d}")
    if doc_name == "tbl_items.json":
        return en_table.encode(f"Itm {idx:02d}")
    if doc_name == "tbl_jutsu.json":
        return en_table.encode(f"Jut {idx:02d}")
    if doc_name == "tbl_ougi.json":
        return en_table.encode(f"Oug {idx}")
    if doc_name.endswith("_desc.json"):
        toks = _preserved_tokens(jp)
        tag = doc_name.split("_")[1][:2].capitalize()
        body = f"[{tag}{idx:03d}]" + ("".join(t for t in toks if t.startswith("{name")))
        if "{nl}" in toks:
            body += "{nl}L1"
        return en_table.encode(body + "{end}")
    if doc_name == "credits_overlay.json":
        addr_hex = eid.split("_")[1]
        toks = _preserved_tokens(jp)
        body = f"C:{addr_hex}"
        if "{nl}" in toks:
            body += "{nl}C2"
        return en_table.encode(body + "{end}")

    addr_val = int(entry["addr"], 16)
    if doc_name == "ui_bank1d_c2.json" and 0xCAA8 <= addr_val <= 0xD7C6:
        return en_table.encode("ABCDEFGHIJKLMNO{end}")

    # Preserve pure party-name placeholder slots (e.g. "{name0}{end}") directly for menu checks
    stripped = jp
    for m in range(5):
        if stripped == f"{{name{m}}}{{end}}":
            return en_table.encode(stripped)

    toks = _preserved_tokens(jp)
    names = [t for t in toks if t.startswith("{name")]
    flow = [t for t in toks if t in ("{nl}", "{page}")]
    if doc_name == "ui_bank1d_c2.json" and entry.get("size", 99) <= 10 and not names and not flow:
        return en_table.encode(f"U:{eid.split('_')[1]}{{end}}")

    prefix = f"[{eid}]"
    if names and not flow:
        prefix += " " + " ".join(names)
    elif flow:
        # Interleave flow breaks cleanly with short text so every page/line draws ink
        parts = [prefix + (" " + names[0] if names else "")]
        for k, fl in enumerate(flow, 1):
            parts.append(f"{fl}L{k}")
        return en_table.encode("".join(parts) + "{end}")
    return en_table.encode(prefix + "{end}")


def _encode_entry(
    doc: dict,
    entry: dict,
    idx: int,
    mode: str,
    en_table: tbl.Table,
    jp_tables: dict[str, tbl.Table],
) -> bytes:
    if entry.get("status") == "data":
        return bytes.fromhex(entry["raw_hex"])
    if entry.get("status") == "empty":
        return b"" if doc["kind"] == "sentinel_table" else b"\xff"
    if mode == "marker":
        return _marker_string(doc["file"], entry, idx, en_table)
    en_text = entry.get("en", "")
    if en_text:
        return en_table.encode(en_text)
    return jp_tables[doc["table"]].encode(entry["jp"])


def _pack_sentinel_bank(
    rom: bytearray,
    writes: list[str],
    orig: bytes,
    bank: int,
    tables_data: list[tuple[dict, list[bytes]]],
) -> None:
    """Pack sentinel pointer tables (pinned at orig addresses) and contiguous data in a ROM bank."""
    pinned: list[tuple[int, int, str]] = []
    for doc, chunks in tables_data:
        ptr_start = int(doc["start"], 16)
        ptr_end = ptr_start + (len(chunks) + 1) * 2
        if ptr_start < 0x8000 or ptr_end > 0x10000:
            raise ValueError(f"Bank ${bank:02X} ptr table {doc['file']} out of $8000..$FFFF bounds")
        pinned.append((ptr_start, ptr_end, doc["file"]))
    pinned.sort()
    for (a0, e0, n0), (a1, _, n1) in zip(pinned, pinned[1:]):
        if e0 > a1:
            raise ValueError(f"Bank ${bank:02X}: ptr table {n0} (${e0:04X}) overlaps {n1} (${a1:04X})")

    # Build largest-contiguous free spans around pinned pointer tables
    spans: list[list[int]] = []
    cur = 0x8000
    for p_start, p_end, _ in pinned:
        if cur < p_start:
            spans.append([cur, p_start])
        cur = max(cur, p_end)
    if cur < 0x10000:
        spans.append([cur, 0x10000])

    # Place larger contiguous tables first so small gaps fill cleanly last
    ordered = sorted(tables_data, key=lambda item: sum(len(c) for c in item[1]), reverse=True)
    for doc, chunks in ordered:
        payload = b"".join(chunks)
        need = len(payload)
        chosen: list[int] | None = None
        for sp in spans:
            if sp[1] - sp[0] >= need:
                chosen = sp
                break
        if chosen is None:
            avail = [sp[1] - sp[0] for sp in spans]
            raise ValueError(
                f"Bank ${bank:02X}: {doc['file']} payload ({need} B) exceeds largest free span (spans={avail})"
            )
        base_addr = chosen[0]
        chosen[0] += need

        ptrs = []
        pos = base_addr
        for c in chunks:
            ptrs.append(pos)
            pos += len(c)
        ptrs.append(pos)
        ptr_bytes = b"".join(p.to_bytes(2, "little") for p in ptrs)

        ptr_start = int(doc["start"], 16)
        put(rom, extract.lorom_to_pc(bank, ptr_start), ptr_bytes, f"ptrs:{doc['file']}", orig, writes)
        if payload:
            put(rom, extract.lorom_to_pc(bank, base_addr), payload, f"data:{doc['file']}", orig, writes)


def _pack_ff_banks(
    rom: bytearray,
    writes: list[str],
    orig: bytes,
    ff_docs: list[tuple[dict, list[bytes]]],
) -> dict[int, list[tuple[int, int, int]]]:
    """Pack relocated $FF-terminated string regions into banks $33..$3D without crossing bank seams."""
    cur_bank = 0x33
    cur_addr = 0x8000
    bank_buf = bytearray()
    redirects: dict[int, list[tuple[int, int, int]]] = {0x1A: [], 0x1B: [], 0x1C: [], 0x1D: []}

    def flush() -> None:
        if bank_buf:
            put(rom, extract.lorom_to_pc(cur_bank, 0x8000), bytes(bank_buf), f"strings:${cur_bank:02X}", orig, writes)

    for doc, chunks in ff_docs:
        orig_bank = int(doc["bank"], 16)
        for entry, raw in zip(doc["entries"], chunks):
            if entry.get("status") == "data":
                continue
            if len(raw) > 0x8000:
                raise ValueError(f"{entry['id']}: encoded size {len(raw)} exceeds 32 KiB bank")
            if cur_addr + len(raw) > 0x10000:
                flush()
                cur_bank += 1
                if cur_bank > 0x3D:
                    raise ValueError(f"Relocated $FF strings overflow past bank $3D at {entry['id']}")
                cur_addr = 0x8000
                bank_buf.clear()
            orig_addr = int(entry["addr"], 16)
            redirects[orig_bank].append((orig_addr, cur_addr, cur_bank))
            bank_buf.extend(raw)
            cur_addr += len(raw)

    flush()
    return redirects


def _build_redirect_tables(redirects: dict[int, list[tuple[int, int, int]]]) -> bytes:
    """Pack sorted 6-byte binary-search tables with 16-byte header for $30:B000."""
    bases: list[int] = []
    counts: list[int] = []
    body = bytearray()
    for bank_id in (0x1A, 0x1B, 0x1C, 0x1D):
        recs = sorted(redirects[bank_id], key=lambda item: item[0])
        seen: set[int] = set()
        bases.append(16 + len(body))
        counts.append(len(recs))
        for orig_addr, new_addr, new_bank in recs:
            if orig_addr in seen:
                raise ValueError(f"Duplicate redirect orig_addr ${bank_id:02X}:{orig_addr:04X}")
            seen.add(orig_addr)
            body.extend(struct.pack("<HHH", orig_addr, new_addr, new_bank))
    blob = struct.pack("<8H", *bases, *counts) + bytes(body)
    if len(blob) > 0x5000:
        raise ValueError(f"redirect_tables.bin ({len(blob)} B) exceeds $30:B000..$FFFF (20,480 B)")
    return blob


def _ensure_font_bins() -> tuple[Path, Path]:
    """Ensure generated 1bpp font and advance-width binaries exist (gitignored *.bin)."""
    font_path = ROOT / "asm" / "font_en_1bpp.bin"
    widths_path = ROOT / "asm" / "font_en_widths.bin"
    if not font_path.is_file() or not widths_path.is_file():
        font_bytes, width_bytes = make_font.build_font_binaries()
        font_path.parent.mkdir(parents=True, exist_ok=True)
        font_path.write_bytes(font_bytes)
        widths_path.write_bytes(width_bytes)
    return font_path, widths_path


def _build_party_names_bin(doc: dict, mode: str, en_table: tbl.Table) -> bytes:
    """Encode 5 ASCII party names <= 48px wide with $FF terminators for $30:A900."""
    _, widths_path = _ensure_font_bins()
    widths = widths_path.read_bytes()
    entries = doc["entries"]
    if len(entries) != 5:
        raise ValueError(f"party_names.json must have 5 entries, found {len(entries)}")

    raw_names: list[bytes] = []
    for i, entry in enumerate(entries):
        name = MARKER_PARTY_NAMES[i] if mode == "marker" else (entry.get("en", "").strip() or MARKER_PARTY_NAMES[i])
        encoded = en_table.encode(name)
        if any(b >= 0x80 for b in encoded):
            raise ValueError(f"party_names[{i}] {name!r} must be ASCII < $80 for Hook_F4D9")
        px_width = sum(widths[b] for b in encoded)
        if px_width > 48:
            raise ValueError(f"party_names[{i}] {name!r} measures {px_width}px > 48px slot limit")
        raw_names.append(encoded + b"\xff")

    offs = []
    cur = 10
    for r in raw_names:
        offs.append(cur)
        cur += len(r)
    blob = struct.pack("<5H", *offs) + b"".join(raw_names)
    if len(blob) > 0x0700:
        raise ValueError(f"party_names_en.bin ({len(blob)} B) exceeds $30:A900..$AFFF (1,792 B)")
    return blob


def _vacate_original_banks(
    rom: bytearray, writes: list[str], orig: bytes, script_dir: Path
) -> None:
    """Fill vacated $1A-$1D regions with $FF, preserving explicit non-text data spans."""
    for spec in extract.REGIONS:
        bank = spec["bank"]
        if bank not in (0x1A, 0x1B, 0x1C, 0x1D):
            continue
        start, end = spec["start"], spec["end"]
        vac = bytearray(b"\xff" * (end - start))
        doc = json.loads((script_dir / spec["name"]).read_text(encoding="utf-8"))
        for entry in doc["entries"]:
            if entry.get("status") == "data":
                off = int(entry["addr"], 16) - start
                raw = bytes.fromhex(entry["raw_hex"])
                vac[off : off + len(raw)] = raw
        put(rom, extract.lorom_to_pc(bank, start), bytes(vac), f"vacate:{spec['name']}", orig, writes)


def _apply_graphics_patches(rom: bytearray, writes: list[str], orig: bytes) -> None:
    """Apply Phase 8 translated graphics, tilemap/metasprite hooks, and relocate compressed tilesets to $3E-$3F."""
    patches = make_gfx.build_patches(orig)
    for lorom_addr, data, label in patches["direct_writes"]:
        put(rom, extract.lorom_to_pc(lorom_addr >> 16, lorom_addr & 0xFFFF), data, label, orig, writes)

    cur_bank = 0x3E
    cur_addr = 0x8000
    for idx, raw in patches["compressed_entries"].items():
        comp = compress.compress(raw)
        dec, dlen = compress.decompress_at(comp, 0x008000)
        if dec != raw or dlen != len(comp):
            raise ValueError(f"Compression roundtrip failed for graphics entry #{idx:03d}")
        if cur_addr + len(comp) > 0x10000:
            cur_bank += 1
            cur_addr = 0x8000
        if cur_bank > 0x3F:
            raise ValueError(f"Graphics entry #{idx:03d} ({len(comp)} B) overflowed Banks $3E-$3F")

        src_lorom = (cur_bank << 16) | cur_addr
        put(rom, extract.lorom_to_pc(cur_bank, cur_addr), comp, f"gfx:entry_{idx:03d}", orig, writes)
        put(
            rom,
            compress.lorom_to_pc(compress.TABLE_LOROM + idx * 5 + 2),
            src_lorom.to_bytes(3, "little"),
            f"gfx:ptr_{idx:03d}",
            orig,
            writes,
        )
        cur_addr += len(comp)


def build_expanded(
    mode: str,
    lang: str = "en",
    rom_path: Path = DEFAULT_ROM,
    script_dir: Path = DEFAULT_SCRIPT_DIR,
    out_path: Path = ROOT / "build" / "marker.sfc",
    writes_path: Path | None = None,
    verify_sha1: bool = True,
) -> tuple[bytes, list[str], int]:
    """Build 2 MiB expanded SNES ROM in 'marker' or 'translate' mode with Asar VWF/redirect hooks."""
    orig = rom_path.read_bytes()
    _check_prepatch_rom(orig)
    if verify_sha1 and rom_path.resolve() == DEFAULT_ROM.resolve():
        check_rom.check()

    en_table = tbl.Table.load(ROOT / "tbl" / "en.tbl")
    jp_tables = extract.load_tables(ROOT / "tbl")
    rom = bytearray(orig) + bytearray([0xFF] * (EXPANDED_ROM_SIZE - len(orig)))
    writes: list[str] = []

    sentinel_banks: dict[int, list[tuple[dict, list[bytes]]]] = {0x31: [], 0x32: []}
    ff_docs: list[tuple[dict, list[bytes]]] = []
    party_doc: dict | None = None
    total_entries = 0

    for spec in extract.REGIONS:
        json_path = script_dir / spec["name"]
        if not json_path.is_file():
            raise FileNotFoundError(f"Missing extracted script file: {json_path}")
        doc = json.loads(json_path.read_text(encoding="utf-8"))
        entries = doc["entries"]
        total_entries += len(entries)

        if doc["kind"] == "fixed_records":
            party_doc = doc
            continue

        encoded_chunks = [_encode_entry(doc, e, i, mode, en_table, jp_tables) for i, e in enumerate(entries)]
        if doc["kind"] == "sentinel_table":
            target_bank = SENTINEL_BANK_ASSIGN[spec["name"]]
            sentinel_banks[target_bank].append((doc, encoded_chunks))
        elif doc["kind"] == "ff_strings":
            ff_docs.append((doc, encoded_chunks))
        else:
            raise ValueError(f"Unsupported region kind: {doc['kind']}")

    for sbank, tdata in sentinel_banks.items():
        _pack_sentinel_bank(rom, writes, orig, sbank, tdata)

    redirects = _pack_ff_banks(rom, writes, orig, ff_docs)
    redir_blob = _build_redirect_tables(redirects)
    party_blob = _build_party_names_bin(party_doc, mode, en_table)

    put(rom, extract.lorom_to_pc(0x30, 0xB000), redir_blob, "bin:redirect_tables.bin", orig, writes)
    put(rom, extract.lorom_to_pc(0x30, 0xA900), party_blob, "bin:party_names_en.bin", orig, writes)
    _vacate_original_banks(rom, writes, orig, script_dir)
    if mode == "translate":
        _apply_graphics_patches(rom, writes, orig)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    (out_path.parent / "redirect_tables.bin").write_bytes(redir_blob)
    (out_path.parent / "party_names_en.bin").write_bytes(party_blob)
    if out_path.exists():
        out_path.unlink()
    out_path.write_bytes(bytes(rom))

    res = subprocess.run(
        [str(ASAR_BIN), "--fix-checksum=off", str(ENGINE_ASM.resolve()), str(out_path.resolve())],
        cwd=ROOT / "asm",
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Asar assembly failed ({res.returncode}):\n{res.stdout}\n{res.stderr}")

    built = out_path.read_bytes()
    if len(built) != EXPANDED_ROM_SIZE:
        raise ValueError(f"Expected {EXPANDED_ROM_SIZE} B expanded ROM after Asar, got {len(built)} B")

    wpath = writes_path if writes_path is not None else out_path.parent / "writes.txt"
    wpath.parent.mkdir(parents=True, exist_ok=True)
    with open(wpath, "w", encoding="utf-8", newline="\n") as f:
        for line in writes:
            f.write(line + "\n")

    return built, writes, total_entries


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("identity", "marker", "translate"), default="identity", help="Build mode")
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
        if args.mode == "identity":
            out_path = ROOT / "build" / "id.sfc"
        elif args.mode == "marker":
            out_path = ROOT / "build" / "marker.sfc"
        else:
            out_path = ROOT / "build" / f"benkei_suna_{lang}.sfc"

    if args.mode == "identity":
        built, _, total_entries = build_identity(
            rom_path=args.rom,
            script_dir=args.script_dir,
            out_path=out_path,
            writes_path=args.writes,
        )
        rel_out = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
        print(f"identity build ok: {len(built)} bytes, 0 diffs, {len(extract.REGIONS)} regions, {total_entries} entries -> {rel_out}")
    else:
        built, _, total_entries = build_expanded(
            mode=args.mode,
            lang=lang,
            rom_path=args.rom,
            script_dir=args.script_dir,
            out_path=out_path,
            writes_path=args.writes,
        )
        rel_out = out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path
        print(f"{args.mode} build ok: {len(built)} bytes, {len(extract.REGIONS)} regions, {total_entries} entries -> {rel_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
