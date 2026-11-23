"""Phase 8 tile-drawn graphics dumper and English pixel-art generator."""
from __future__ import annotations

import argparse
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import compress  # noqa: E402


def write_png(path: Path, width: int, height: int, rgb: bytes) -> None:
    """Write an 8-bit RGB PNG using pure stdlib zlib/struct."""
    path.parent.mkdir(parents=True, exist_ok=True)
    stride = width * 3
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(rgb[y * stride : (y + 1) * stride])

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return len(data).to_bytes(4, "big") + tag + data + crc.to_bytes(4, "big")

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw), 6)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png)


def cgram_to_rgb(pal_bin: bytes) -> list[tuple[int, int, int]]:
    """Convert 512-byte SNES CGRAM to 256 (R,G,B) tuples."""
    colors = []
    for i in range(0, min(len(pal_bin), 512), 2):
        c = int.from_bytes(pal_bin[i : i + 2], "little")
        r = (c & 0x1F) * 255 // 31
        g = ((c >> 5) & 0x1F) * 255 // 31
        b = ((c >> 10) & 0x1F) * 255 // 31
        colors.append((r, g, b))
    while len(colors) < 256:
        colors.append((0, 0, 0))
    return colors


def decode_4bpp_tile(tile: bytes) -> list[int]:
    """Decode a 32-byte SNES 4bpp 8x8 tile to 64 palette indices (0..15)."""
    out = [0] * 64
    for y in range(8):
        p0 = tile[y * 2]
        p1 = tile[y * 2 + 1]
        p2 = tile[16 + y * 2]
        p3 = tile[16 + y * 2 + 1]
        for x in range(8):
            sh = 7 - x
            v = ((p0 >> sh) & 1) | (((p1 >> sh) & 1) << 1) | (((p2 >> sh) & 1) << 2) | (((p3 >> sh) & 1) << 3)
            out[y * 8 + x] = v
    return out


def encode_4bpp_tile(pixels: list[int]) -> bytes:
    """Encode 64 palette indices (0..15) into a 32-byte SNES 4bpp 8x8 tile."""
    out = bytearray(32)
    for y in range(8):
        p0 = p1 = p2 = p3 = 0
        for x in range(8):
            v = pixels[y * 8 + x] & 0x0F
            sh = 7 - x
            p0 |= (v & 1) << sh
            p1 |= ((v >> 1) & 1) << sh
            p2 |= ((v >> 2) & 1) << sh
            p3 |= ((v >> 3) & 1) << sh
        out[y * 2] = p0
        out[y * 2 + 1] = p1
        out[16 + y * 2] = p2
        out[16 + y * 2 + 1] = p3
    return bytes(out)


def decode_2bpp_tile(tile: bytes) -> list[int]:
    """Decode a 16-byte SNES 2bpp 8x8 tile to 64 palette indices (0..3)."""
    out = [0] * 64
    for y in range(8):
        p0, p1 = tile[y * 2], tile[y * 2 + 1]
        for x in range(8):
            sh = 7 - x
            out[y * 8 + x] = ((p0 >> sh) & 1) | (((p1 >> sh) & 1) << 1)
    return out


def encode_2bpp_tile(pixels: list[int]) -> bytes:
    """Encode 64 palette indices (0..3) into a 16-byte SNES 2bpp 8x8 tile."""
    out = bytearray(16)
    for y in range(8):
        p0 = p1 = 0
        for x in range(8):
            v = pixels[y * 8 + x] & 3
            sh = 7 - x
            p0 |= (v & 1) << sh
            p1 |= ((v >> 1) & 1) << sh
        out[y * 2] = p0
        out[y * 2 + 1] = p1
    return bytes(out)


def render_4bpp_sheet(
    data: bytes,
    cols: int = 16,
    palette: list[tuple[int, int, int]] | None = None,
    pal_bank: int = 0,
    scale: int = 2,
) -> tuple[int, int, bytes]:
    """Render raw 4bpp tile bytes into an RGB buffer."""
    if palette is None:
        palette = [(i * 17, i * 17, i * 17) for i in range(16)] + [(0, 0, 0)] * 240
    n_tiles = len(data) // 32
    rows = max(1, (n_tiles + cols - 1) // cols)
    w = cols * 8 * scale
    h = rows * 8 * scale
    buf = bytearray([20, 12, 24] * (w * h))
    base_c = pal_bank * 16
    for idx in range(n_tiles):
        tx, ty = idx % cols, idx // cols
        pxs = decode_4bpp_tile(data[idx * 32 : (idx + 1) * 32])
        for py in range(8):
            for px in range(8):
                ci = pxs[py * 8 + px]
                c = palette[base_c + ci] if ci > 0 else (30, 20, 40)
                for sy in range(scale):
                    oy = (ty * 8 + py) * scale + sy
                    row_off = oy * w * 3
                    for sx in range(scale):
                        ox = (tx * 8 + px) * scale + sx
                        p = row_off + ox * 3
                        buf[p : p + 3] = bytes(c)
    return w, h, bytes(buf)


def render_tilemap(
    tilemap: bytes,
    vram_chr: bytes,
    palette: list[tuple[int, int, int]],
    cols: int = 32,
    rows: int = 32,
    tile_base: int = 0,
) -> tuple[int, int, bytes]:
    """Render a 32x32 16-bit SNES BG tilemap against a VRAM 4bpp chr region."""
    w, h = cols * 8, rows * 8
    buf = bytearray([0] * (w * h * 3))
    for ty in range(rows):
        for tx in range(cols):
            i = ty * 32 + tx
            if i * 2 + 2 > len(tilemap):
                continue
            word = int.from_bytes(tilemap[i * 2 : i * 2 + 2], "little")
            tid = (word & 0x3FF) + tile_base
            pal = (word >> 10) & 7
            hflip = bool(word & 0x4000)
            vflip = bool(word & 0x8000)
            off = tid * 32
            if off + 32 > len(vram_chr):
                continue
            pxs = decode_4bpp_tile(vram_chr[off : off + 32])
            for py in range(8):
                sy = 7 - py if vflip else py
                for px in range(8):
                    sx = 7 - px if hflip else px
                    ci = pxs[sy * 8 + sx]
                    if ci == 0:
                        continue
                    c = palette[pal * 16 + ci]
                    p = ((ty * 8 + py) * w + (tx * 8 + px)) * 3
                    buf[p : p + 3] = bytes(c)
    return w, h, bytes(buf)


def render_vram_region(
    vram_bin: bytes,
    pal_bin: bytes,
    word_base: int,
    tile_count: int,
    pal_bank: int = 0,
    cols: int = 16,
    scale: int = 2,
) -> tuple[int, int, bytes]:
    byte_off = word_base * 2
    chunk = vram_bin[byte_off : byte_off + tile_count * 32]
    return render_4bpp_sheet(chunk, cols=cols, palette=cgram_to_rgb(pal_bin), pal_bank=pal_bank, scale=scale)


def dump_recon(rom_path: Path, recon_dir: Path) -> None:
    rom = rom_path.read_bytes()
    title_vram = (recon_dir / "title_full" / "title.vram.bin").read_bytes()
    title_pal = (recon_dir / "title_full" / "title.pal.bin").read_bytes()
    title_rgb = cgram_to_rgb(title_pal)

    title2_vram = (recon_dir / "title_long" / "title2.vram.bin").read_bytes()
    title2_pal = (recon_dir / "title_long" / "title2.pal.bin").read_bytes()
    title2_rgb = cgram_to_rgb(title2_pal)

    tosa_vram = (recon_dir / "tosa" / "tosa.vram.bin").read_bytes()
    tosa_pal = (recon_dir / "tosa" / "tosa.pal.bin").read_bytes()
    chang_vram = (recon_dir / "changsha" / "changsha.vram.bin").read_bytes()
    chang_pal = (recon_dir / "changsha" / "changsha.pal.bin").read_bytes()
    bat_vram = (recon_dir / "battle" / "battle.vram.bin").read_bytes()
    bat_pal = (recon_dir / "battle" / "battle.pal.bin").read_bytes()

    # Dump raw decompressed sheets of interest
    sheets = [
        (101, title2_rgb, 2, "entry_101_pal2"),
        (102, title2_rgb, 2, "entry_102_pal2"),
        (113, title2_rgb, 4, "entry_113_pal4"),
        (114, title_rgb, 4, "entry_114_pal4"),
        (115, title_rgb, 4, "entry_115_pal4"),
        (116, title_rgb, 4, "entry_116_pal4"),
        (281, title2_rgb, 2, "entry_281_pal2"),
        (1, cgram_to_rgb(tosa_pal), 3, "entry_001_tosa"),
        (11, cgram_to_rgb(chang_pal), 3, "entry_011_changsha"),
        (13, cgram_to_rgb(tosa_pal), 3, "entry_013_tosa"),
        (227, cgram_to_rgb(bat_pal), 8, "entry_227_oam0"),
    ]
    out = recon_dir / "sheets"
    for idx, rgb, pbank, name in sheets:
        dst, src, clen, raw = compress.decompress_entry(rom, idx)
        w, h, img = render_4bpp_sheet(raw, cols=16, palette=rgb, pal_bank=pbank, scale=2)
        write_png(out / f"{name}.png", w, h, img)

    # Render title BG1/BG2 tilemaps from title2 VRAM ($0000 and $0800 word offsets -> $0000 and $1000 byte offsets)
    # Title CHR base is word $1000 -> byte $2000; in #107 tile ids are >=256 (which is $2000 word offset -> VRAM $3000?)
    for label, vram, rgb in [("title1_f480", title_vram, title_rgb), ("title2_f1250", title2_vram, title2_rgb)]:
        w, h, bg1 = render_tilemap(vram[0x0000:0x0800], vram[0x2000:], rgb)
        write_png(out / f"{label}_bg1.png", w, h, bg1)
        w, h, bg2 = render_tilemap(vram[0x1000:0x1800], vram[0x2000:], rgb)
        write_png(out / f"{label}_bg2.png", w, h, bg2)
        # Render Mode7 / whole $0000..$7FFF chr at $6000 too
        w, h, chr6 = render_4bpp_sheet(vram[0xC000:0xE000], cols=16, palette=rgb, pal_bank=2, scale=2)
        write_png(out / f"{label}_vram6000.png", w, h, chr6)

    # Render $0B:9095 2bpp tiles 0..14 zoomed 6x using Battle BG3 pal 1..3 colors
    pc9095 = compress.lorom_to_pc(0x0B9095)
    raw2 = rom[pc9095 : pc9095 + 15 * 16]
    cols2 = 15
    sc = 6
    bw, bh = cols2 * 8 * sc, 8 * sc
    bbuf = bytearray([0] * (bw * bh * 3))
    c2bpp = [(0, 0, 0), (20, 26, 12), (110, 120, 100), (245, 245, 230)]
    for t in range(15):
        pxs = decode_2bpp_tile(raw2[t * 16 : (t + 1) * 16])
        for y in range(8):
            for x in range(8):
                c = c2bpp[pxs[y * 8 + x]]
                for sy in range(sc):
                    oy = y * sc + sy
                    for sx in range(sc):
                        ox = (t * 8 + x) * sc + sx
                        p = (oy * bw + ox) * 3
                        bbuf[p : p + 3] = bytes(c)
    write_png(out / "bank0b_9095_2bpp.png", bw, bh, bytes(bbuf))
    print(f"Wrote recon sheets to {out}")


# ---------------------------------------------------------------------------
# Phase 8: Clean-ROM addresses, pre-patch expectations, and pixel-art builders
# ---------------------------------------------------------------------------

TITLE_LOGO_ENTRY = 101
TITLE_LOGO_TILE_COUNT = 235  # Hardcoded `LDA #$00EB` at $09:C440 for Mode 7 upload
TITLE_TILEMAP_LOROM = 0x09DA78
TITLE_SUBTITLE_ENTRY = 281
TITLE_SUBTITLE_POS_LOROM = 0x09CBAC  # operand of `LDA #$8018` at $09:CBAB (x=24, y=128)
TITLE_SUBTITLE_META_LOROM = 0x0E8EB2  # 4x4=16B OAM metasprite #8 entries before $80
TOWN_JP_PLAQUES_ENTRY = 1
TOWN_CN_PLAQUES_ENTRY = 11
BATTLE_DIGITS_ENTRY = 227
BATTLE_BADGE_ACTIVE_LOROM = 0x0B9135  # Tile 10 of $0B:9095 (動 -> A)
BATTLE_BADGE_TEXT_LOROM = 0x0B9145    # Tile 11 of $0B:9095 (文 -> T)

# Centered horizontal 128x32 OAM ribbon at (x=64, y=154), below New Game/Continue (y=96..144)
TITLE_SUBTITLE_POS_BYTES = bytes([64, 154])
TITLE_SUBTITLE_META_BYTES = bytes.fromhex("00000020200004204000082060000c20")


def _fill_poly(canvas: list[list[int]], pts: list[tuple[float, float]], val: int = 1) -> None:
    """Scanline-fill a closed polygon (2D coordinates in pixel space) with integer `val`."""
    h = len(canvas)
    w = len(canvas[0])
    min_y = max(0, int(min(p[1] for p in pts)) - 1)
    max_y = min(h - 1, int(max(p[1] for p in pts)) + 1)
    n = len(pts)
    for py in range(min_y, max_y + 1):
        y = py + 0.5
        xs: list[float] = []
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            x_start = max(0, int(xs[k] + 0.5))
            x_end = min(w, int(xs[k + 1] + 0.5))
            row = canvas[py]
            for px in range(x_start, x_end):
                row[px] = val


def _stroke_seg(
    canvas: list[list[int]], x0: float, y0: float, x1: float, y1: float, r0: float, r1: float | None = None, val: int = 1
) -> None:
    """Fill a tapered thick segment (chiseled/brush capsule) from (x0,y0) to (x1,y1)."""
    if r1 is None:
        r1 = r0
    h = len(canvas)
    w = len(canvas[0])
    rmax = max(r0, r1) + 1.0
    dx, dy = x1 - x0, y1 - y0
    len2 = dx * dx + dy * dy
    y_lo = max(0, int(min(y0, y1) - rmax))
    y_hi = min(h - 1, int(max(y0, y1) + rmax))
    x_lo = max(0, int(min(x0, x1) - rmax))
    x_hi = min(w - 1, int(max(x0, x1) + rmax))
    for py in range(y_lo, y_hi + 1):
        cy = py + 0.5
        row = canvas[py]
        for px in range(x_lo, x_hi + 1):
            cx = px + 0.5
            if len2 <= 1e-6:
                t = 0.0
            else:
                t = max(0.0, min(1.0, ((cx - x0) * dx + (cy - y0) * dy) / len2))
            nx = x0 + t * dx
            ny = y0 + t * dy
            rr = r0 + t * (r1 - r0)
            if (cx - nx) ** 2 + (cy - ny) ** 2 <= rr * rr:
                row[px] = val


def _draw_logo_glyph(mask: list[list[int]], ch: str, x: float, y: float, w: float, h: float) -> None:
    """Draw an angular calligraphic/chiseled serif display letter into binary mask."""
    st = w * 0.135  # half-width of main vertical stems (~3.2-3.5 px -> 6-7 px total)
    hbar = h * 0.085  # half-thickness of horizontal bars

    def rect(x0: float, y0: float, x1: float, y1: float, v: int = 1) -> None:
        _fill_poly(mask, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], v)

    def poly(pts: list[tuple[float, float]], v: int = 1) -> None:
        _fill_poly(mask, [(x + px * w, y + py * h) for px, py in pts], v)

    def seg(ax: float, ay: float, bx: float, by: float, ra: float, rb: float | None = None, v: int = 1) -> None:
        _stroke_seg(mask, x + ax * w, y + ay * h, x + bx * w, y + by * h, ra, rb, v)

    if ch == "B":
        # Flared top/bottom serif + chiseled stem + dual angular bowls
        poly([(0.02, 0.00), (0.28, 0.00), (0.28, 1.00), (0.02, 1.00)])
        poly([(0.00, 0.00), (0.68, 0.00), (0.86, 0.10), (0.88, 0.34), (0.72, 0.46),
              (0.89, 0.56), (0.91, 0.86), (0.70, 1.00), (0.00, 1.00),
              (0.00, 0.85), (0.62, 0.85), (0.70, 0.77), (0.70, 0.61), (0.58, 0.54),
              (0.18, 0.54), (0.18, 0.40), (0.58, 0.40), (0.68, 0.33), (0.68, 0.17), (0.58, 0.13), (0.00, 0.13)])
        # Clean inner counters
        poly([(0.26, 0.14), (0.58, 0.14), (0.66, 0.20), (0.66, 0.33), (0.56, 0.40), (0.26, 0.40)], 0)
        poly([(0.26, 0.54), (0.60, 0.54), (0.69, 0.61), (0.69, 0.78), (0.60, 0.85), (0.26, 0.85)], 0)
        # Re-assert spine and serif spurs
        poly([(0.00, 0.00), (0.12, 0.06), (0.12, 0.94), (0.00, 1.00)], 1)
    elif ch == "E":
        poly([(0.00, 0.00), (0.94, 0.00), (0.98, 0.15), (0.82, 0.13), (0.27, 0.13),
              (0.27, 0.41), (0.74, 0.41), (0.78, 0.54), (0.27, 0.54), (0.27, 0.86),
              (0.84, 0.86), (0.98, 0.84), (0.94, 1.00), (0.00, 1.00),
              (0.08, 0.90), (0.08, 0.10)])
    elif ch == "N":
        poly([(0.00, 0.00), (0.26, 0.00), (0.76, 0.72), (0.76, 0.00), (0.96, 0.00),
              (0.96, 1.00), (0.70, 1.00), (0.22, 0.30), (0.22, 1.00), (0.02, 1.00),
              (0.08, 0.88), (0.08, 0.10)])
        # Top/bottom serif accents
        poly([(0.70, 0.00), (1.00, 0.00), (0.94, 0.12), (0.76, 0.12)])
    elif ch == "K":
        poly([(0.00, 0.00), (0.28, 0.00), (0.28, 1.00), (0.00, 1.00), (0.08, 0.88), (0.08, 0.10)])
        # Upper diagonal slash + flared tip
        poly([(0.24, 0.46), (0.72, 0.00), (0.98, 0.00), (0.88, 0.12), (0.44, 0.52),
              (0.96, 1.00), (0.68, 1.00), (0.24, 0.56)])
    elif ch == "I":
        poly([(0.04, 0.00), (0.96, 0.00), (0.90, 0.14), (0.65, 0.14), (0.65, 0.86),
              (0.90, 0.86), (0.96, 1.00), (0.04, 1.00), (0.10, 0.86), (0.35, 0.86),
              (0.35, 0.14), (0.10, 0.14)])
    elif ch == "G":
        poly([(0.24, 0.00), (0.86, 0.00), (0.96, 0.18), (0.72, 0.18), (0.68, 0.14),
              (0.32, 0.14), (0.25, 0.24), (0.25, 0.78), (0.33, 0.86), (0.68, 0.86),
              (0.68, 0.62), (0.50, 0.62), (0.54, 0.48), (0.94, 0.48), (0.94, 0.90),
              (0.76, 1.00), (0.22, 1.00), (0.04, 0.84), (0.04, 0.16)])
    elif ch == "A":
        poly([(0.36, 0.00), (0.64, 0.00), (1.00, 1.00), (0.74, 1.00), (0.65, 0.74),
              (0.35, 0.74), (0.26, 1.00), (0.00, 1.00)])
        poly([(0.50, 0.22), (0.61, 0.60), (0.39, 0.60)], 0)
    elif ch == "D":
        poly([(0.00, 0.00), (0.70, 0.00), (0.95, 0.18), (0.95, 0.82), (0.70, 1.00),
              (0.00, 1.00), (0.08, 0.88), (0.08, 0.10)])
        poly([(0.28, 0.15), (0.62, 0.15), (0.71, 0.25), (0.71, 0.75), (0.62, 0.85), (0.28, 0.85)], 0)
    else:
        raise ValueError(f"Unsupported title glyph: {ch!r}")


def generate_title_logo() -> tuple[bytes, bytes]:
    """Generate `#101` 4bpp tiles (EXACTLY 235 tiles = 7520 B) and `$09:DA78` tilemap (2048 B) for `BENKEI GAIDEN`."""
    w, h = 256, 224
    mask = [[0] * w for _ in range(h)]

    # Top word: BENKEI in y=11..45 (rows 1..5), x=14..242 (228 px wide)
    benkei_layout = [
        ("B", 16, 11, 34, 34),
        ("E", 55, 11, 31, 34),
        ("N", 92, 11, 34, 34),
        ("K", 132, 11, 34, 34),
        ("E", 171, 11, 31, 34),
        ("I", 208, 12, 24, 33),
    ]
    for ch, gx, gy, gw, gh in benkei_layout:
        _draw_logo_glyph(mask, ch, gx, gy, gw, gh)

    # Bottom word: GAIDEN in y=51..83 (rows 6..10), x=28..228 (200 px wide)
    gaiden_layout = [
        ("G", 28, 51, 31, 31),
        ("A", 63, 51, 31, 31),
        ("I", 98, 51, 21, 31),
        ("D", 124, 51, 30, 31),
        ("E", 160, 51, 28, 31),
        ("N", 193, 51, 31, 31),
    ]
    for ch, gx, gy, gw, gh in gaiden_layout:
        _draw_logo_glyph(mask, ch, gx, gy, gw, gh)

    # Shade strictly with BG pal 1 indices 1..6:
    # 1 = vivid purple body, 2 = lower-stroke bevel, 3/4 = inner/edge transition, 5/6 = crisp outline + drop shadow
    canvas = [[0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            if mask[py][px]:
                # Subtle inner bottom-right edge bevel inside strokes
                has_up = py > 0 and mask[py - 1][px]
                has_down = py + 1 < h and mask[py + 1][px]
                has_right = px + 1 < w and mask[py][px + 1]
                if not has_down and has_up:
                    canvas[py][px] = 2
                elif not has_right:
                    canvas[py][px] = 2
                else:
                    canvas[py][px] = 1

    # Add 1px outline (4/5) + (+1,+1)/(+2,+2) drop shadow (6) in empty pixels around the letters
    for py in range(h):
        for px in range(w):
            if mask[py][px]:
                continue
            if (py > 0 and mask[py - 1][px]) or (px > 0 and mask[py][px - 1]) or (py > 0 and px > 0 and mask[py - 1][px - 1]):
                canvas[py][px] = 5
            elif (py + 1 < h and mask[py + 1][px]) or (px + 1 < w and mask[py][px + 1]):
                canvas[py][px] = 4
            elif py >= 2 and px >= 2 and mask[py - 2][px - 2]:
                canvas[py][px] = 6
            elif (py >= 2 and mask[py - 2][px]) or (px >= 2 and mask[py][px - 2]):
                canvas[py][px] = 6

    # Deduplicate 8x8 tiles (tile 0 reserved all-zero transparent)
    tiles: list[bytes] = [bytes(32)]
    tile_ids: dict[bytes, int] = {tiles[0]: 0}
    tilemap = bytearray(32 * 32 * 2)

    for ty in range(28):
        for tx in range(32):
            pxs = []
            for y in range(8):
                py = ty * 8 + y
                row = canvas[py]
                for x in range(8):
                    pxs.append(row[tx * 8 + x])
            raw_tile = encode_4bpp_tile(pxs)
            tid = tile_ids.get(raw_tile)
            if tid is None:
                tid = len(tiles)
                tile_ids[raw_tile] = tid
                tiles.append(raw_tile)
            off = (ty * 32 + tx) * 2
            tilemap[off : off + 2] = tid.to_bytes(2, "little")

    if len(tiles) > TITLE_LOGO_TILE_COUNT:
        raise ValueError(
            f"Title logo #101 requires {len(tiles)} unique tiles, exceeding Mode 7 limit {TITLE_LOGO_TILE_COUNT}"
        )

    while len(tiles) < TITLE_LOGO_TILE_COUNT:
        tiles.append(bytes(32))

    raw_101 = b"".join(tiles)
    if len(raw_101) != TITLE_LOGO_TILE_COUNT * 32:
        raise AssertionError(f"Expected {TITLE_LOGO_TILE_COUNT * 32} B, got {len(raw_101)}")
    return raw_101, bytes(tilemap)


# ---------------------------------------------------------------------------
# Compact crisp pixel fonts for subtitle (#281), plaques (#001/#011), digits (#227)
# ---------------------------------------------------------------------------

# 9px-tall bold serif-flavored display glyphs (varied widths 4..7 px) for 128x32 subtitle
_SUBTITLE_FONT: dict[str, list[str]] = {
    "C": [
        ".#####.",
        "##...##",
        "##.....",
        "##.....",
        "##.....",
        "##.....",
        "##.....",
        "##...##",
        ".#####.",
    ],
    "H": [
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "#######",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
    ],
    "A": [
        "..###..",
        ".##.##.",
        "##...##",
        "##...##",
        "#######",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
    ],
    "P": [
        "######.",
        "##...##",
        "##...##",
        "##...##",
        "######.",
        "##.....",
        "##.....",
        "##.....",
        "##.....",
    ],
    "T": [
        "#######",
        "#######",
        "...##..",
        "...##..",
        "...##..",
        "...##..",
        "...##..",
        "...##..",
        "..####.",
    ],
    "E": [
        "#######",
        "##.....",
        "##.....",
        "##.....",
        "#####..",
        "##.....",
        "##.....",
        "##.....",
        "#######",
    ],
    "R": [
        "######.",
        "##...##",
        "##...##",
        "##...##",
        "######.",
        "##..##.",
        "##...##",
        "##...##",
        "##...##",
    ],
    "O": [
        ".#####.",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        ".#####.",
    ],
    "F": [
        "#######",
        "##.....",
        "##.....",
        "##.....",
        "#####..",
        "##.....",
        "##.....",
        "##.....",
        "##.....",
    ],
    "S": [
        ".#####.",
        "##...##",
        "##.....",
        ".###...",
        "..###..",
        "....##.",
        ".....##",
        "##...##",
        ".#####.",
    ],
    "N": [
        "##...##",
        "###..##",
        "####.##",
        "##.####",
        "##..###",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
    ],
    "D": [
        "######.",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "##...##",
        "######.",
    ],
    " ": [
        "....",
    ] * 9,
}


def generate_title_subtitle(orig_raw_281: bytes) -> bytes:
    """Replace tiles 0..63 of `#281` with golden `CHAPTER OF / THE SANDS` while keeping 64..95 (`© 1992 SUNSOFT`) intact."""
    if len(orig_raw_281) != 96 * 32:
        raise ValueError(f"Expected 3072 B for #281, got {len(orig_raw_281)}")

    w, h = 128, 32
    fg = [[0] * w for _ in range(h)]

    def text_width(s: str, gap: int = 2) -> int:
        return sum(len(_SUBTITLE_FONT[c][0]) for c in s) + gap * max(0, len(s) - 1)

    def blit_line(s: str, y0: int, gap: int = 2) -> None:
        tw = text_width(s, gap=gap)
        cx = (w - tw) // 2
        for ch in s:
            rows = _SUBTITLE_FONT[ch]
            gw = len(rows[0])
            for ry, row in enumerate(rows):
                for rx, pix in enumerate(row):
                    if pix == "#":
                        fg[y0 + ry][cx + rx] = 1
            cx += gw + gap

    blit_line("CHAPTER OF", y0=3, gap=2)
    blit_line("THE SANDS", y0=18, gap=3)

    # Color with OAM pal 4 (CGRAM 12): 1=bright gold, 2=lower gold shading, 5/6=dark bronze outline/shadow
    canvas = [[0] * w for _ in range(h)]
    for py in range(h):
        for px in range(w):
            if fg[py][px]:
                # Subtle lower-half depth using palette index 2 on bottom row of a stroke
                if py + 1 < h and not fg[py + 1][px]:
                    canvas[py][px] = 2
                else:
                    canvas[py][px] = 1
                continue
            # 1px crisp dark-bronze outline + (+1,+1) drop shadow
            adj4 = (
                (py > 0 and fg[py - 1][px])
                or (py + 1 < h and fg[py + 1][px])
                or (px > 0 and fg[py][px - 1])
                or (px + 1 < w and fg[py][px + 1])
            )
            diag_br = py > 0 and px > 0 and fg[py - 1][px - 1]
            if diag_br:
                canvas[py][px] = 6
            elif adj4:
                canvas[py][px] = 5

    out = bytearray(orig_raw_281)
    # 4 contiguous 32x32 OAM sprites in 16-col VRAM (tiles 0..63 = rows 0..3)
    for k in range(4):
        x_base = k * 32
        for ty in range(4):
            for tx in range(4):
                pxs = []
                for y in range(8):
                    row = canvas[ty * 8 + y]
                    for x in range(8):
                        pxs.append(row[x_base + tx * 8 + x])
                tile_idx = ty * 16 + k * 4 + tx
                out[tile_idx * 32 : (tile_idx + 1) * 32] = encode_4bpp_tile(pxs)
    return bytes(out)


# 6px-tall crisp uppercase glyphs for 16x16 town plaques (13x11 inner box)
_PLAQUE_FONT: dict[str, list[str]] = {
    "I": ["###", ".#.", ".#.", ".#.", ".#.", "###"],
    "N": ["#..#", "##.#", "#.##", "#.##", "#..#", "#..#"],
    "W": ["#...#", "#...#", "#.#.#", "#.#.#", "##.##", ".#.#."],
    "E": ["###", "#..", "##.", "#..", "#..", "###"],
    "P": ["##.", "#.#", "##.", "#..", "#..", "#.."],
    "A": [".#.", "#.#", "###", "#.#", "#.#", "#.#"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#", "#.#"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#"],
    "T": ["###", ".#.", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "#.#", "###"],
    "B": ["##.", "#.#", "##.", "#.#", "#.#", "##."],
}


def _patch_16x16_plaque(
    raw: bytearray,
    tile_quad: tuple[int, int, int, int],
    label: str,
    fill_rows: list[int],
    ink_val: int,
    canonical_border_grid: list[list[int]] | None = None,
) -> None:
    """Refill inner rows 3..13, cols 2..14 of a 16x16 plaque preserving outer border, and draw `label`."""
    tl, tr, bl, br = tile_quad
    coords = [(0, 0, tl), (0, 8, tr), (8, 0, bl), (8, 8, br)]
    if canonical_border_grid is not None:
        grid = [row[:] for row in canonical_border_grid]
    else:
        grid = [[0] * 16 for _ in range(16)]
        for dy, dx, t in coords:
            px = decode_4bpp_tile(raw[t * 32 : (t + 1) * 32])
            for y in range(8):
                for x in range(8):
                    grid[dy + y][dx + x] = px[y * 8 + x]

    # Refill inner panel ONLY (rows 3..13, cols 2..14), preserving outer frame (rows 0..2, 14..15; cols 0..1, 15)
    for ry in range(3, 14):
        bg = fill_rows[ry - 3]
        for rx in range(2, 15):
            grid[ry][rx] = bg

    total_w = sum(len(_PLAQUE_FONT[c][0]) for c in label) + max(0, len(label) - 1)
    start_x = 2 + (13 - total_w) // 2
    start_y = 5  # centered in rows 3..13: 2px above (rows 3..4), 6px glyph (rows 5..10), 3px below (rows 11..13)
    cx = start_x
    for ch in label:
        glyph = _PLAQUE_FONT[ch]
        for gy, grow in enumerate(glyph):
            for gx, chp in enumerate(grow):
                if chp == "#":
                    grid[start_y + gy][cx + gx] = ink_val
        cx += len(glyph[0]) + 1

    for dy, dx, t in coords:
        pxs = []
        for y in range(8):
            for x in range(8):
                pxs.append(grid[dy + y][dx + x])
        raw[t * 32 : (t + 1) * 32] = encode_4bpp_tile(pxs)


def generate_shop_plaques_001(orig_raw_001: bytes) -> bytes:
    """Replace ONLY the 5 Japan wooden shop plaques in `#001` (480 tiles = 15360 B)."""
    if len(orig_raw_001) != 480 * 32:
        raise ValueError(f"Expected 15360 B for #001, got {len(orig_raw_001)}")
    out = bytearray(orig_raw_001)
    # Canonical spotless wooden frame (preserving exact rows 0..1, row 15, cols 0..1, col 15)
    canon = [[0] * 16 for _ in range(16)]
    for ry in (0, 1):
        canon[ry] = [0xE, 2] + [1] * 13 + [2]
    canon[2] = [0xE] + [4] * 14 + [3]
    for ry in range(3, 14):
        canon[ry][0] = 0xE
        canon[ry][1] = 4
        canon[ry][15] = 3
    canon[14] = [0xE] + [4] * 14 + [3]
    canon[15] = [0xE] * 16

    # Tosa wood palette BG pal 1: 3=(164,131,98) light tan, 4=(139,106,74) wood, E=(0,0,0) ink
    fill = [4, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4]
    specs = [
        ((288, 289, 304, 305), "INN"),
        ((290, 291, 306, 307), "WEP"),
        ((292, 293, 308, 309), "ARM"),
        ((294, 295, 310, 311), "ITM"),
        ((296, 297, 312, 313), "PUB"),
    ]
    for quad, lbl in specs:
        _patch_16x16_plaque(out, quad, lbl, fill, ink_val=0xE, canonical_border_grid=canon)
    return bytes(out)


def generate_shop_plaques_011(orig_raw_011: bytes) -> bytes:
    """Replace ONLY the 4 China stone shop plaques in `#011` (480 tiles = 15360 B)."""
    if len(orig_raw_011) != 480 * 32:
        raise ValueError(f"Expected 15360 B for #011, got {len(orig_raw_011)}")
    out = bytearray(orig_raw_011)
    # Extract spotless stone outer frame (rows 0..2, 14..15; cols 0..1, 15) from clean #011 WEP (202,203,218,219)
    canon = [[0] * 16 for _ in range(16)]
    for dy, dx, t in ((0, 0, 202), (0, 8, 203), (8, 0, 218), (8, 8, 219)):
        px = decode_4bpp_tile(orig_raw_011[t * 32 : (t + 1) * 32])
        for y in range(8):
            for x in range(8):
                canon[dy + y][dx + x] = px[y * 8 + x]

    # Changsha stone palette BG pal 1: C=(164,139,115), D=(148,115,98), E=(106,74,57), 1=(0,0,0) crisp black ink
    fill = [0xC, 0xC, 0xD, 0xD, 0xD, 0xD, 0xD, 0xD, 0xD, 0xD, 0xE]
    specs = [
        ((202, 203, 218, 219), "WEP"),
        ((204, 205, 220, 221), "ITM"),
        ((234, 235, 250, 251), "ARM"),
        ((236, 237, 252, 253), "INN"),
    ]
    for quad, lbl in specs:
        _patch_16x16_plaque(out, quad, lbl, fill, ink_val=0x1, canonical_border_grid=canon)
    return bytes(out)


# 6x6 bold digits 0..9 rendered at x=1..6, y=1..6 inside 8x8 with 0x1 drop shadow
_BATTLE_DIGITS: dict[int, list[str]] = {
    0: [".FFFF.", "FF..FF", "FF..FF", "FF..FF", "FF..FF", ".FFFF."],
    1: ["..FF..", ".FFF..", "..FF..", "..FF..", "..FF..", ".FFFF."],
    2: [".FFFF.", "FF..FF", "...FF.", "..FF..", ".FF...", "FFFFFF"],
    3: [".FFFF.", "FF..FF", "..FFF.", "....FF", "FF..FF", ".FFFF."],
    4: ["...FF.", "..FFF.", ".FF.FF", "FF..FF", "FFFFFF", "....FF"],
    5: ["FFFFFF", "FF....", "FFFFF.", "....FF", "FF..FF", ".FFFF."],
    6: [".FFFF.", "FF....", "FFFFF.", "FF..FF", "FF..FF", ".FFFF."],
    7: ["FFFFFF", "....FF", "...FF.", "..FF..", ".FF...", ".FF..."],
    8: [".FFFF.", "FF..FF", ".FFFF.", "FF..FF", "FF..FF", ".FFFF."],
    9: [".FFFF.", "FF..FF", ".FFFFF", "....FF", "....FF", ".FFFF."],
}


def generate_battle_digits_227(orig_raw_227: bytes) -> bytes:
    """Replace ONLY tiles 16..25 (`〇..九`) in `#227` with outlined Arabic `0..9` (`0xF` fg, `0x1` shadow)."""
    if len(orig_raw_227) != 160 * 32:
        raise ValueError(f"Expected 5120 B for #227, got {len(orig_raw_227)}")
    out = bytearray(orig_raw_227)
    for d in range(10):
        grid = [[0] * 8 for _ in range(8)]
        rows = _BATTLE_DIGITS[d]
        for ry in range(6):
            for rx in range(6):
                if rows[ry][rx] == "F":
                    grid[1 + ry][1 + rx] = 0xF
        # Down-left shadow matching original #227 kanji style
        for py in range(8):
            for px in range(8):
                if grid[py][px] != 0:
                    continue
                if (py > 0 and grid[py - 1][px] == 0xF) or (px < 7 and grid[py][px + 1] == 0xF) or (py > 0 and px < 7 and grid[py - 1][px + 1] == 0xF):
                    grid[py][px] = 0x1
        pxs = [grid[y][x] for y in range(8) for x in range(8)]
        tid = 16 + d
        out[tid * 32 : (tid + 1) * 32] = encode_4bpp_tile(pxs)
    return bytes(out)


# 8x8 2bpp battle mode badges (`1`=dark olive bg, `2`=shadow/AA, `3`=bright cream fg; never `0`)
_BADGE_A = [
    "11333111",
    "13313311",
    "33111332",
    "33333332",
    "33111332",
    "33111332",
    "33111332",
    "22111222",
]
_BADGE_T = [
    "33333331",
    "33333332",
    "22233222",
    "11133211",
    "11133211",
    "11133211",
    "11133211",
    "11122211",
]


def generate_battle_mode_badges() -> tuple[bytes, bytes]:
    """Return 16-byte 2bpp tiles for Tile 10 (`A` Active) and Tile 11 (`T` Text) at `$0B:9135` / `$0B:9145`."""
    tiles = []
    for art in (_BADGE_A, _BADGE_T):
        pxs = [int(ch) for row in art for ch in row]
        tiles.append(encode_2bpp_tile(pxs))
    return tiles[0], tiles[1]


def build_patches(orig_rom: bytes) -> dict:
    """Build all Phase 8 compressed tilesets and direct ROM byte patches from clean JP ROM."""
    raw_101, tilemap_09da78 = generate_title_logo()
    _, _, _, orig_281 = compress.decompress_entry(orig_rom, TITLE_SUBTITLE_ENTRY)
    _, _, _, orig_001 = compress.decompress_entry(orig_rom, TOWN_JP_PLAQUES_ENTRY)
    _, _, _, orig_011 = compress.decompress_entry(orig_rom, TOWN_CN_PLAQUES_ENTRY)
    _, _, _, orig_227 = compress.decompress_entry(orig_rom, BATTLE_DIGITS_ENTRY)

    raw_281 = generate_title_subtitle(orig_281)
    raw_001 = generate_shop_plaques_001(orig_001)
    raw_011 = generate_shop_plaques_011(orig_011)
    raw_227 = generate_battle_digits_227(orig_227)
    badge_a, badge_t = generate_battle_mode_badges()

    return {
        "compressed_entries": {
            TITLE_LOGO_ENTRY: raw_101,
            TITLE_SUBTITLE_ENTRY: raw_281,
            TOWN_JP_PLAQUES_ENTRY: raw_001,
            TOWN_CN_PLAQUES_ENTRY: raw_011,
            BATTLE_DIGITS_ENTRY: raw_227,
        },
        "direct_writes": [
            (TITLE_TILEMAP_LOROM, tilemap_09da78, "gfx:title_tilemap_09da78"),
            (TITLE_SUBTITLE_POS_LOROM, TITLE_SUBTITLE_POS_BYTES, "gfx:title_subtitle_pos"),
            (TITLE_SUBTITLE_META_LOROM, TITLE_SUBTITLE_META_BYTES, "gfx:title_subtitle_meta"),
            (BATTLE_BADGE_ACTIVE_LOROM, badge_a, "gfx:battle_badge_active"),
            (BATTLE_BADGE_TEXT_LOROM, badge_t, "gfx:battle_badge_text"),
        ],
    }


def _blit_4bpp_tile_to_rgb(
    buf: bytearray, w: int, h: int, px0: int, py0: int, tile32: bytes, palette: list[tuple[int, int, int]], pal_bank: int
) -> None:
    pxs = decode_4bpp_tile(tile32)
    base = pal_bank * 16
    for y in range(8):
        dy = py0 + y
        if not (0 <= dy < h):
            continue
        for x in range(8):
            dx = px0 + x
            if not (0 <= dx < w):
                continue
            ci = pxs[y * 8 + x]
            if ci == 0:
                continue
            off = (dy * w + dx) * 3
            buf[off : off + 3] = bytes(palette[base + ci])


def _upscale_rgb(w: int, h: int, rgb: bytes | bytearray, scale: int) -> tuple[int, int, bytes]:
    if scale == 1:
        return w, h, bytes(rgb)
    nw, nh = w * scale, h * scale
    out = bytearray(nw * nh * 3)
    for y in range(h):
        for x in range(w):
            c = rgb[(y * w + x) * 3 : (y * w + x) * 3 + 3]
            for sy in range(scale):
                row_off = (y * scale + sy) * nw * 3
                for sx in range(scale):
                    p = row_off + (x * scale + sx) * 3
                    out[p : p + 3] = c
    return nw, nh, bytes(out)


def _render_plaque_pair_sheet(
    orig_raw: bytes,
    new_raw: bytes,
    quads: list[tuple[int, int, int, int]],
    palette: list[tuple[int, int, int]],
    pal_bank: int,
    scale: int = 6,
) -> tuple[int, int, bytes]:
    n = len(quads)
    w, h = n * 18, 36
    buf = bytearray([24, 18, 32] * (w * h))
    for i, (tl, tr, bl, br) in enumerate(quads):
        x0 = i * 18 + 1
        for src_raw, y0 in ((orig_raw, 1), (new_raw, 19)):
            for dy, dx, tid in ((0, 0, tl), (0, 8, tr), (8, 0, bl), (8, 8, br)):
                _blit_4bpp_tile_to_rgb(buf, w, h, x0 + dx, y0 + dy, src_raw[tid * 32 : (tid + 1) * 32], palette, pal_bank)
    return _upscale_rgb(w, h, buf, scale)


def generate_previews(rom_path: Path, recon_dir: Path, preview_dir: Path) -> None:
    """Render before/after zoomed PNG previews of all Phase 8 translated graphics."""
    rom = rom_path.read_bytes()
    patches = build_patches(rom)
    entries = patches["compressed_entries"]
    raw_101 = entries[TITLE_LOGO_ENTRY]
    raw_281 = entries[TITLE_SUBTITLE_ENTRY]
    raw_001 = entries[TOWN_JP_PLAQUES_ENTRY]
    raw_011 = entries[TOWN_CN_PLAQUES_ENTRY]
    raw_227 = entries[BATTLE_DIGITS_ENTRY]
    tilemap_09da78 = patches["direct_writes"][0][1]
    badge_a, badge_t = patches["direct_writes"][3][1], patches["direct_writes"][4][1]

    preview_dir.mkdir(parents=True, exist_ok=True)

    # Palettes from live recon if available, else realistic fallbacks
    title_pal_p = recon_dir / "title_long" / "title2.pal.bin"
    title_vram_p = recon_dir / "title_long" / "title2.vram.bin"
    if title_pal_p.is_file():
        title_rgb = cgram_to_rgb(title_pal_p.read_bytes())
    else:
        title_rgb = [(0, 0, 0)] * 256
        title_rgb[16:23] = [(0, 0, 0), (131, 0, 189), (106, 0, 164), (82, 0, 139), (57, 0, 106), (24, 0, 65), (8, 0, 41)]
        title_rgb[192:199] = [(0, 0, 0), (156, 156, 0), (139, 139, 0), (115, 115, 0), (82, 82, 0), (49, 49, 0), (32, 32, 0)]

    # 1. Title composite at 2x (BG2 desert sunset + BG1 #101 + OAM #281 + menu guide box)
    if title_vram_p.is_file():
        tvram = title_vram_p.read_bytes()
        _, _, bg2 = render_tilemap(tvram[0x1000:0x1800], tvram[0x2000:], title_rgb, cols=32, rows=28)
        comp = bytearray(bg2)
    else:
        comp = bytearray([30, 12, 16] * (256 * 224))
    tm_pal1 = b"".join(
        ((int.from_bytes(tilemap_09da78[i : i + 2], "little") | 0x0400) if int.from_bytes(tilemap_09da78[i : i + 2], "little") else 0).to_bytes(2, "little")
        for i in range(0, len(tilemap_09da78), 2)
    )
    w_bg1, h_bg1, bg1 = render_tilemap(tm_pal1, raw_101, title_rgb, cols=32, rows=28)
    for py in range(224):
        for px in range(256):
            off = (py * 256 + px) * 3
            c = bg1[off : off + 3]
            if c != b"\x00\x00\x00":
                comp[off : off + 3] = c
    # Render 4 OAM subtitle sprites at (64, 154) with OAM pal 4 (CGRAM bank 12)
    for k in range(4):
        sx = 64 + k * 32
        sy = 154
        for ty in range(4):
            for tx in range(4):
                tid = ty * 16 + k * 4 + tx
                _blit_4bpp_tile_to_rgb(comp, 256, 224, sx + tx * 8, sy + ty * 8, raw_281[tid * 32 : (tid + 1) * 32], title_rgb, 12)
    # Draw New Game / Continue overlap check box (x=96..166, y=96..144) in thin cyan dashed outline
    for x in range(96, 167, 2):
        for y in (96, 144):
            p = (y * 256 + x) * 3
            comp[p : p + 3] = b"\x40\xd0\xd0"
    for y in range(96, 145, 2):
        for x in (96, 166):
            p = (y * 256 + x) * 3
            comp[p : p + 3] = b"\x40\xd0\xd0"
    w, h, up = _upscale_rgb(256, 224, comp, 2)
    write_png(preview_dir / "title_composite.png", w, h, up)

    # 2. Title #101 tilesheet
    w, h, img = render_4bpp_sheet(raw_101, cols=16, palette=title_rgb, pal_bank=1, scale=2)
    write_png(preview_dir / "title_logo_tiles.png", w, h, img)

    # 3. Title #281 before/after with CGRAM 12
    _, _, _, orig_281 = compress.decompress_entry(rom, TITLE_SUBTITLE_ENTRY)
    _, _, img_before = render_4bpp_sheet(orig_281, cols=16, palette=title_rgb, pal_bank=12, scale=2)
    w, h, img_after = render_4bpp_sheet(raw_281, cols=16, palette=title_rgb, pal_bank=12, scale=2)
    write_png(preview_dir / "title_subtitle_281.png", w, h * 2, img_before + img_after)

    # 4. #001 Tosa wooden plaques before/after
    tosa_pal_p = recon_dir / "tosa" / "tosa.pal.bin"
    tosa_rgb = cgram_to_rgb(tosa_pal_p.read_bytes()) if tosa_pal_p.is_file() else title_rgb
    _, _, _, orig_001 = compress.decompress_entry(rom, TOWN_JP_PLAQUES_ENTRY)
    w, h, p1 = _render_plaque_pair_sheet(
        orig_001, raw_001,
        [(288, 289, 304, 305), (290, 291, 306, 307), (292, 293, 308, 309), (294, 295, 310, 311), (296, 297, 312, 313)],
        tosa_rgb, pal_bank=1, scale=6,
    )
    write_png(preview_dir / "plaques_001.png", w, h, p1)

    # 5. #011 Changsha stone plaques before/after
    ch_pal_p = recon_dir / "changsha" / "changsha.pal.bin"
    ch_rgb = cgram_to_rgb(ch_pal_p.read_bytes()) if ch_pal_p.is_file() else title_rgb
    _, _, _, orig_011 = compress.decompress_entry(rom, TOWN_CN_PLAQUES_ENTRY)
    w, h, p11 = _render_plaque_pair_sheet(
        orig_011, raw_011,
        [(202, 203, 218, 219), (204, 205, 220, 221), (234, 235, 250, 251), (236, 237, 252, 253)],
        ch_rgb, pal_bank=1, scale=6,
    )
    write_png(preview_dir / "plaques_011.png", w, h, p11)

    # 6. #227 battle digits before/after
    bat_pal_p = recon_dir / "battle" / "battle.pal.bin"
    bat_rgb = cgram_to_rgb(bat_pal_p.read_bytes()) if bat_pal_p.is_file() else title_rgb
    _, _, _, orig_227 = compress.decompress_entry(rom, BATTLE_DIGITS_ENTRY)
    dw, dh = 80, 18
    dbuf = bytearray([24, 18, 32] * (dw * dh))
    for i in range(10):
        tid = 16 + i
        _blit_4bpp_tile_to_rgb(dbuf, dw, dh, i * 8, 0, orig_227[tid * 32 : (tid + 1) * 32], bat_rgb, 8)
        _blit_4bpp_tile_to_rgb(dbuf, dw, dh, i * 8, 9, raw_227[tid * 32 : (tid + 1) * 32], bat_rgb, 8)
    w, h, dup = _upscale_rgb(dw, dh, dbuf, 6)
    write_png(preview_dir / "battle_digits_227.png", w, h, dup)

    # 7. $0B:9135/$0B:9145 2bpp battle mode badges before/after
    pc9135 = compress.lorom_to_pc(BATTLE_BADGE_ACTIVE_LOROM)
    orig_a, orig_t = rom[pc9135 : pc9135 + 16], rom[pc9135 + 16 : pc9135 + 32]
    c2bpp = [(0, 0, 0), (20, 26, 12), (110, 120, 100), (245, 245, 230)]
    bw, bh = 18, 18
    bbuf = bytearray([0] * (bw * bh * 3))
    for row_i, pair in enumerate(((orig_a, orig_t), (badge_a, badge_t))):
        for col_i, tbytes in enumerate(pair):
            pxs = decode_2bpp_tile(tbytes)
            for y in range(8):
                for x in range(8):
                    p = ((row_i * 9 + y) * bw + (col_i * 9 + x)) * 3
                    bbuf[p : p + 3] = bytes(c2bpp[pxs[y * 8 + x]])
    w, h, bup = _upscale_rgb(bw, bh, bbuf, 8)
    write_png(preview_dir / "battle_badges_0b.png", w, h, bup)
    print(f"Wrote Phase 8 previews to {preview_dir}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc")
    ap.add_argument("--dump", action="store_true", help="Render recon PNG sheets to work/gfx_recon/sheets/")
    ap.add_argument("--preview", action="store_true", help="Render Phase 8 before/after previews to work/gfx_preview/")
    args = ap.parse_args(argv)
    if args.dump:
        dump_recon(args.rom, ROOT / "work" / "gfx_recon")
    if args.preview:
        generate_previews(args.rom, ROOT / "work" / "gfx_recon", ROOT / "work" / "gfx_preview")
    return 0


if __name__ == "__main__":
    sys.exit(main())
