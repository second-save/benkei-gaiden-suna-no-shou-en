# Compression (`$1F:8000` Table & `$0A:E120`/`$0A:E20A`)

**Status:** **verified** (disassembly of `$0A:E120..$0A:E9DF`, exact match against `../Benkei/Font/ben_092..097.raw`, and `decompress(compress(raw)) == raw` across all 282/282 entries in `tests/test_compress.py`).

## Index Table (`$1F:8000`, PC `0x0F8000`)

- **282 entries** (`0..281`), 5 bytes each (`$1F:8000..$1F:8581`), immediately followed by entry `0`'s compressed stream at `$1F:8582`.
- Entry format (little-endian):
  - `+0..1` (`uint16`): `dst` — target VRAM word address (for `$0A:E120`) or `$7F:0000` byte offset (for `$0A:E20A`/`$0A:E20D`).
  - `+2..4` (`uint24`): `src` — 24-bit LoROM source pointer (`bank:addr`).

## Routine Entry Points

- **`JSL $0A:E120`** (`A` = entry index, 8/16-bit): sets `$2116 = dst` and DMAs each decompressed 32-byte tile (`$0280..$029F`) straight to `$2118/$2119`.
- **`JSL $0A:E20A` / `JSL $0A:E20D`** (`A` = entry index): writes decompressed 32-byte tiles sequentially to `$7F:0000 + dst + offset`. (Note: `$0A:E20D` masks `A` with `$00FF`; `$0A:E20A` uses full 16-bit `A`.)

## Bitstream Format (`tools/compress.py`)

Data decompresses in 32-byte SNES 4bpp tile units (bitplanes 0, 1 at even/odd bytes `0..15`; bitplanes 2, 3 at even/odd bytes `16..31`):

1. Read 1-byte group header `hdr` (processes up to 8 tiles, MSB first).
2. For each bit `b` of `hdr`:
   - **`b == 0`**: all 4 planes (`p0`, `p1`, `p2`, `p3`) are decoded via `SubE3B1`.
   - **`b == 1`**: read 1 control byte `ctl` (`$32`):
     - If `ctl == 0xC6`: **end of stream** (return immediately without emitting a tile).
     - `ctl & 0x80`: `0` = `SubE3B1(p0)`, `1` = zero-fill `p0`.
     - `ctl & 0x60`: `0x00` = `SubE3B1(p1)`, `0x20` = copy `p0 -> p1`, `0x40/0x60` = zero-fill `p1`.
     - `ctl & 0x18`: `0x00` = `SubE3B1(p2)`, `0x08` = copy `p0 -> p2`, `0x10` = copy `p1 -> p2`, `0x18` = zero-fill `p2`.
     - `ctl & 0x07`: `0x00` = `SubE3B1(p3)`, `0x01` = copy `p0 -> p3`, `0x02` = copy `p1 -> p3`, `0x03` = copy `p2 -> p3`, `0x04..0x07` = zero-fill `p3`.
     - **Encoder edge case:** never emit `ctl == 0xC6` (`p0=0, p1=0, p2=SubE3B1, p3=0`); use `0xC4` (or `0xE6`), which performs the identical plane clears.
3. **`SubE3B1` per-plane encoding (8 bytes):**
   - Byte `mask`: bit 7 = `1` raw rows / `0` 8×8 bit-matrix transposed rows; bits `6..0` correspond to rows `1..7` (`1` = read next literal byte, `0` = repeat previous row byte). Row `0` is always read literally after `mask`.
