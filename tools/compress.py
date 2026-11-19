"""Compression/decompression codec for Benkei Gaiden: Suna no Shou ($1F:8000 graphics table).

Decompressor entry points in ROM:
  - $0A:E120: decompresses entry A from $1F:8000 table directly to VRAM word addr `dst`.
  - $0A:E20A / $0A:E20D: decompresses entry A into WRAM $7F:0000 + dst.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

TABLE_LOROM = 0x1F8000
ENTRY_COUNT = 282  # indices 0..281 ($1F:8000..$1F:8581; entry 0 data starts at $1F:8582)


def lorom_to_pc(addr: int) -> int:
    return ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)


def read_table(rom: bytes) -> list[tuple[int, int, int]]:
    """Return list of (index, dst, src_lorom) for all 282 entries in $1F:8000."""
    base = lorom_to_pc(TABLE_LOROM)
    entries = []
    for i in range(ENTRY_COUNT):
        ent = rom[base + i * 5 : base + i * 5 + 5]
        dst = int.from_bytes(ent[:2], "little")
        src = int.from_bytes(ent[2:5], "little")
        entries.append((i, dst, src))
    return entries


def _transpose_8x8(plane: list[int] | bytes) -> list[int]:
    out = [0] * 8
    for i in range(8):
        z = 0
        shift = 7 - i
        for c in range(8):
            z = (z << 1) | ((plane[c] >> shift) & 1)
        out[i] = z
    return out


def decompress_at(rom: bytes, src_lorom: int) -> tuple[bytes, int]:
    """Decompress stream starting at `src_lorom`. Returns (raw_bytes, compressed_len)."""
    start = lorom_to_pc(src_lorom)
    pos = start
    out = bytearray()
    ram = bytearray(0x20)

    def sub_e3b1(off: int) -> None:
        nonlocal pos
        mask = rom[pos]
        pos += 1
        carry = mask & 0x80
        mask = (mask << 1) & 0xFF
        val = rom[pos]
        pos += 1
        ram[off] = val
        for x in range(1, 8):
            if mask & 0x80:
                val = rom[pos]
                pos += 1
            ram[off + (x << 1)] = val
            mask = (mask << 1) & 0xFF
        if not carry:
            tmp = [ram[off + (i << 1)] for i in range(8)]
            t = _transpose_8x8(tmp)
            for i in range(8):
                ram[off + (i << 1)] = t[i]

    def copy_plane(src_off: int, dst_off: int) -> None:
        for i in range(8):
            ram[dst_off + (i << 1)] = ram[src_off + (i << 1)]

    def clear_plane(off: int) -> None:
        for i in range(8):
            ram[off + (i << 1)] = 0

    while len(out) < 0x10000:
        hdr = rom[pos]
        pos += 1
        for _ in range(8):
            if not (hdr & 0x80):
                sub_e3b1(0x00)
                sub_e3b1(0x01)
                sub_e3b1(0x10)
                sub_e3b1(0x11)
            else:
                b32 = rom[pos]
                if b32 & 0x80:
                    if b32 == 0xC6:
                        pos += 1
                        return bytes(out), pos - start
                    pos += 1
                    clear_plane(0x00)
                else:
                    pos += 1
                    sub_e3b1(0x00)

                m60 = b32 & 0x60
                if m60 == 0x00:
                    sub_e3b1(0x01)
                elif m60 == 0x20:
                    copy_plane(0x00, 0x01)
                else:
                    clear_plane(0x01)

                m18 = b32 & 0x18
                if m18 == 0x00:
                    sub_e3b1(0x10)
                elif m18 == 0x08:
                    copy_plane(0x00, 0x10)
                elif m18 == 0x10:
                    copy_plane(0x01, 0x10)
                else:
                    clear_plane(0x10)

                m07 = b32 & 0x07
                if m07 == 0x00:
                    sub_e3b1(0x11)
                elif m07 == 0x01:
                    copy_plane(0x00, 0x11)
                elif m07 == 0x02:
                    copy_plane(0x01, 0x11)
                elif m07 == 0x03:
                    copy_plane(0x10, 0x11)
                else:
                    clear_plane(0x11)

            hdr = (hdr << 1) & 0xFF
            out.extend(ram)

    raise ValueError(f"Decompression at ${src_lorom:06X} exceeded 64 KiB without 0xC6 terminator")


def decompress_entry(rom: bytes, idx: int) -> tuple[int, int, int, bytes]:
    """Decompress entry `idx` from $1F:8000. Returns (dst, src_lorom, comp_len, raw_bytes)."""
    if not (0 <= idx < ENTRY_COUNT):
        raise IndexError(f"Entry index {idx} out of range 0..{ENTRY_COUNT - 1}")
    base = lorom_to_pc(TABLE_LOROM + idx * 5)
    dst = int.from_bytes(rom[base : base + 2], "little")
    src = int.from_bytes(rom[base + 2 : base + 5], "little")
    raw, clen = decompress_at(rom, src)
    return dst, src, clen, raw


def _encode_plane_rle(rows: list[int], raw_mode: bool) -> bytes:
    mask = 0x80 if raw_mode else 0x00
    payload = bytearray([rows[0]])
    prev = rows[0]
    for i in range(1, 8):
        if rows[i] != prev:
            mask |= 1 << (7 - i)
            payload.append(rows[i])
            prev = rows[i]
    return bytes([mask]) + bytes(payload)


def _encode_plane(plane: list[int]) -> bytes:
    raw_enc = _encode_plane_rle(plane, True)
    tr_enc = _encode_plane_rle(_transpose_8x8(plane), False)
    return raw_enc if len(raw_enc) <= len(tr_enc) else tr_enc


def _encode_tile(tile32: bytes) -> tuple[bool, bytes]:
    """Encode one 32-byte 4bpp tile. Returns (needs_flag_bit, chunk_bytes)."""
    p0 = [tile32[i * 2] for i in range(8)]
    p1 = [tile32[i * 2 + 1] for i in range(8)]
    p2 = [tile32[16 + i * 2] for i in range(8)]
    p3 = [tile32[16 + i * 2 + 1] for i in range(8)]
    zeros = [0] * 8

    lit0 = _encode_plane(p0)
    lit1 = _encode_plane(p1)
    lit2 = _encode_plane(p2)
    lit3 = _encode_plane(p3)

    if p0 == zeros:
        b0, d0 = 0x80, b""
    else:
        b0, d0 = 0x00, lit0

    if p1 == zeros:
        b1, d1 = 0x40, b""
    elif p1 == p0:
        b1, d1 = 0x20, b""
    else:
        b1, d1 = 0x00, lit1

    if p2 == zeros:
        b2, d2 = 0x18, b""
    elif p2 == p0:
        b2, d2 = 0x08, b""
    elif p2 == p1:
        b2, d2 = 0x10, b""
    else:
        b2, d2 = 0x00, lit2

    if p3 == zeros:
        b3, d3 = 0x04, b""
    elif p3 == p0:
        b3, d3 = 0x01, b""
    elif p3 == p1:
        b3, d3 = 0x02, b""
    elif p3 == p2:
        b3, d3 = 0x03, b""
    else:
        b3, d3 = 0x00, lit3

    b32 = b0 | b1 | b2 | b3
    if b32 == 0xC6:
        b32 = 0xC4  # 0xC6 is end-of-stream; 0xC4 has identical plane-clear bits

    flagged = bytes([b32]) + d0 + d1 + d2 + d3
    unflagged = lit0 + lit1 + lit2 + lit3
    if len(flagged) < len(unflagged):
        return True, flagged
    return False, unflagged


def compress(raw: bytes) -> bytes:
    """Compress raw tile bytes (multiple of 32 bytes) into Benkei Suna compressed format."""
    if len(raw) % 32 != 0:
        raise ValueError(f"raw length {len(raw)} is not a multiple of 32 bytes")

    tiles = [_encode_tile(raw[i : i + 32]) for i in range(0, len(raw), 32)]
    out = bytearray()

    for g in range(0, len(tiles), 8):
        group = tiles[g : g + 8]
        hdr = 0
        body = bytearray()
        for bit_idx, (flagged, chunk) in enumerate(group):
            if flagged:
                hdr |= 1 << (7 - bit_idx)
            body.extend(chunk)
        if len(group) < 8:
            # Put terminator bit right after the last real tile in this partial group
            hdr |= 1 << (7 - len(group))
            body.append(0xC6)
            out.append(hdr)
            out.extend(body)
            return bytes(out)
        out.append(hdr)
        out.extend(body)

    # Exact multiple of 8 tiles: emit final group with bit 7 = 1 and 0xC6 terminator
    out.append(0x80)
    out.append(0xC6)
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rom", type=Path)
    ap.add_argument("--verify", action="store_true", help="roundtrip compress(decompress) across all 282 entries")
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    if args.verify:
        le_count = 0
        total_orig = 0
        total_recomp = 0
        for i in range(ENTRY_COUNT):
            dst, src, clen, raw = decompress_entry(rom, i)
            comp = compress(raw)
            dec, dlen = decompress_at(comp, 0x008000)
            if dec != raw or dlen != len(comp):
                print(f"FAIL entry {i}: dec_match={dec == raw} dlen={dlen}/{len(comp)}")
                return 1
            total_orig += clen
            total_recomp += len(comp)
            if len(comp) <= clen:
                le_count += 1
        print(
            f"OK {ENTRY_COUNT}/{ENTRY_COUNT} roundtrip exact; "
            f"{le_count}/{ENTRY_COUNT} <= orig size "
            f"(orig={total_orig} B, recomp={total_recomp} B)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
