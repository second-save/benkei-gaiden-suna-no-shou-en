# Text Engine Architecture (`$00:E760–$00:F630` & Related Paths)

**Status:** **verified** (full 65816 disassembly of `$00:E75D–$F5A0`, `$0B:8F00–$9095`, `$0C:CD11–$CD48`, `$03:E438–$EB25`, `$09:CDB2–$CE05`, plus live MesenCE PPU inspection of title/menu/dialogue/location-banner frames in `work/re/explore1..4`).

## 1. Unified Text Rendering Pipeline

All normal text — field dialogue, Main Menu, Status screen, Shop/Item/Jutsu lists, Name Entry grid, Battle UI/messages (`$09:CDB2–$CE05`), Prologue crawl (`$09:9C4E`), Ending crawl (`$03:E660..`), and Ending Credits (`$03:E438..`) — passes through a single engine in bank `$00`:

1. **String setup (`$00:EC35`):** Saves `$A2 -> $A3`, calls `JSL $00:EC06` to resolve the 24-bit ROM address in `[$A0]` (`$A0:$A1:$A2`), sets `DB = $7E`, selects window slot `$00..$03` (`$00:EC58,X` -> `$AA` points to `$7E:D280`, `$D480`, `$D680`, or `$D880`), and resets `$CD = 0`.
2. **Pass 1 — Glyph resolution & allocation (`$00:E99D` -> `$00:EA23/$EA2A` -> `$00:EA31`):**
   - Loops through bytes of `[$A0],Y`:
     - `< $F0`: single-byte glyph ID (`8x16`, 1 tile column wide).
     - `$F0–$F7`: 2-byte kanji ID: `((b0 << 8 | b1) & $07FF) << 1` (left half) followed by `+ 1` (right half, 2 columns wide total).
     - `$F8–$FB`: `$00:EE9C` `RTS` (ignored control slots; **0 occurrences** in ROM text).
     - `$FC <sub ...>`: converted to `16`-bit command words `$FF02..$FF05` in `$1A80`/`$1B80`.
     - `$FD` / `$FE` / `$FF`: newline / page break / end (`$FF00`, `$FF01`, `$FFFF`).
   - Direct immediate-print callers (`$00:E99D`) fill `$1A80,X`; paged dialogue callers (`$00:ED8A` -> `$00:EED3`) fill `$1B80,X`, track columns in `$B0` against max columns `$D5` (`$00:EDFC` / `$00:EE0C`), track lines in `$B2` against max lines `$D7`, and inject automatic line/page breaks via `$00:EE7C` (note: **Japanese word-wrapping wraps arbitrarily by column `$D5`; English will require word-boundary wrap logic or pre-wrapped lines**).
3. **Dynamic 1bpp Tile Cache (`$00:EA31..$00:EB9D`):**
   - **Preloaded `$00–$1F`:** Lookup table at `$00:EA40` maps glyph IDs `$00–$1F` straight to fixed BG3 VRAM tile indices `$0010, $0012, ..., $004E` (two vertical 8×8 tiles per glyph; uploaded once at init by `$00:F442` to VRAM `$0400` / tile `$0010`, with bitplane 1 OR'd to `$FF`).
   - **Dynamic `>= $20`:** Calls `$00:EA80` to track glyph ID in the active window's 256-entry list (`$7E:D280..$D9FF`), then `$00:EAE4` searches/allocates in the **320-slot** (`$0140`) global tile cache (`$7E:D000..$D27F` IDs -> `$7E:AC00..$BFFF` 1bpp buffer, 16 bytes per 8×16 glyph).
   - Cache slot `k` (`0..319`) maps to BG3 VRAM tile index `k + $0080` (`$0080..$01BF`; each 8×16 char uses `k + $80` top and `k + $81` bottom? Note `k` increments by `2` in `EA82/EAE6` steps -> actually `$AC00 + k*8`? Verify byte-stride: `$EB45`: `LDA $AE; ASL x4` = `glyph * 16` from `$7E:2000`; `TYA; ASL x3` = byte_offset_Y `* 8`, since `Y` advances by 2 bytes per slot in `$D000`, so `Y * 8 == slot_index * 16` bytes!).
   - **`$00:EC6A` DMA upload:** Transfers `$7E:AC00` (`$0A00` B -> VRAM word `$4400`, tiles `$0080..$011F`) and `$7E:B600` (`$0A00` B -> VRAM word `$4E00`, tiles `$0120..$01BF`) via DMA cmd `$08` (`$2115 = $00`, bitplane 0 low bytes only!). Init routine `$00:F47F` pre-filled bitplane 1 (`$2115 = $80` / cmd `$09`) across both `$4400` and `$4E00` from the same pattern so bitplane 0 controls ink color vs background/shadow cleanly (**critical Phase 5 insight**: 8×16 half-width and VWF shifts only manipulate 1bpp rows in `$7E:2000` / `$7E:AC00`!).
4. **Tilemap Writer (`$00:EB9E..$00:EC04`):**
   - Computes `$7E:C000` BG3 tilemap offset from `(X, Y)` packed in `$A3`: `(y & $3F) * $40 + (x & $1F) * 2 + $C000`.
   - Loops through `$1A80,X`: writes `tile + $E3` (top row `$A8`) and `tile + 1 + $E3` (bottom row `$AB` = row + 1).
   - Palette selector `$E3`: `$2000` (palette 0, default) or `$2400` (palette 1).

## 2. Bank Resolution (`$00:EC06`, **verified**)

Uses `$0D00` bit 7 (`$80`) and 16-bit pointer `ptr` (`$A0:$A1`):

| `$0D00 & $80` | `ptr` Range | Resolved ROM Address | Formula / Action |
|---|---|---|---|
| `== 0` | `$0000–$7FFF` | **`$1B:$8000–$FFFF`** | Forces bit 15 to 1 (`ASL $A1; SEC; ROR $A1`), `bank = $1B` |
| `== 0` | `$8000–$A7FF` | **`$1A:$8000–$A7FF`** | `bank = $1A` |
| `== 0` | `$A800–$FFFF` | **`$1D:$A800–$FFFF`** | `bank = $1D` |
| `!= 0` | `$0000–$7FFF` | **`$1C:$8000–$FFFF`** | Forces bit 15 to 1 (`ASL $A1; SEC; ROR $A1`), `bank = $1C` |
| `!= 0` | `$8000–$FFFF` | **`$1D:$8000–$FFFF`** | `bank = $1D` |

## 3. Caller Entry Points (`$00:E75D–$E99C` & `$00:ECBE–$ED55`, **verified**)

- **`$00:E762 / $E765 / $E768` (`JSR`) and `$00:E76B / $E770 / $E775` (`JSL`)**: read 4 inline bytes after the call (`dw ptr16; db x, y`), write to `$1A80`, upload DMA (`$00:E890`), and draw onto BG3. Window ID (`$A8 = 0..3`) selects which window slot in `$7E:D280..` is used.
- **`$00:E7CA / $E7D3 / $E7D8 / $E7DD`**: read 2 inline bytes (`db x, y`) and draw NUL/FF-terminated RAM buffer **`$7E:1E80`**.
- **`$00:E80C..$E826`**: pointer in `$A0`, coordinates in **`$195E` (`x`) / `$1960` (`y`)** (used by Battle and Credits!).
- **`$00:E85C..$E870`**: pointer in `$A0`, inline coordinates or preloaded `A` = window slot.
- **`$00:E97B`**: renders string `[$A0]` into `$1A80` without writing tilemap (`JSL $00:E815` / `$00:E88C` commits it).
- **`$00:ECBE..$ED55`**: paged dialogue printer (clears box via `$00:F0B8`/`$F0D5`, processes `$FD` newline & `$FE` blinking cursor wait at `$00:EFFA`).

## 4. Box Dimensions & Control Codes (**verified**)

- **Default dialogue box (`$00:F3DE`):** Box origin `(x=4, y=20)`, **`$D5 = $18` (24 half-width columns = 12 kanji)**, **`$D7 = 3` lines** (6 BG3 tile rows high).
- **Menu/Window clearing (`$00:F2E2`):** Takes 4 inline bytes (`x, y, w, h`), clears BG3 tilemap and garbage-collects unreferenced tiles in `$7E:D000`. Battle callers use full-screen `(0,0,32,64)` (`$09:BD47`), top/bottom split windows, etc.
- **Control codes (`$00:E9A7`, `$00:EB9E`, `$00:ED91`, `$00:EE9D`, `$00:EF11`):**
  - `$FD` -> `$FF00` (newline; scrolls window via `$00:EFD1` if on last line `$D7`)
  - `$FE` -> `$FF01` (page wait for A/B/joypad input at `$00:EFFA`, clears box via `$00:F0B8`)
  - `$FF` -> `$FFFF` (end of string)
  - `$F8–$FB` -> `$00:EE9C` (`RTS`, unused; 0 occurrences in ROM text)
  - `$FC $00` (`$FF02`) -> set `$E3 = $2000` (palette 0); `$FC $01` (`$FF03`) -> set `$E3 = $2400` (palette 1); `$FC $02 <arg>` (`$FF04 <arg>`) -> wait frames via `JSL $0B:9395`; `$FC $03 <arg>` (`$FF05 <arg>`) -> no-op. Scan of `$1A–$1D` confirmed **0 occurrences** of `$FC` in static ROM text.

## 5. Font Loaders & Special Renderers (**verified**)

- **Main Font (`$00:F573`):** Decompresses compressed entries **`92, 93, 94, 95, 96`** (`$5C..$60`, `8192+8192+8192+8192+2816 = 35,584` B) via `$0A:E20A` into `$7E:2000..$7E:AAFF` (1bpp 8×16 glyphs, 16 bytes/glyph).
- **Dynamic Party Names (`$00:F4D9`, `$00:F534`):** Copies 5 default 30-byte / 6-tile character names into `$7E:A800..$A9DF`, mapped to kanji codes **`$F440–$F442`** (Member 0, default `不動` padded with `$10`), **`$F443–$F445`**, **`$F446–$F448`**, **`$F449–$F44B`**, **`$F44C–$F44E`**. Editable by player on the Name Entry screen (`文字/作字`).
- **Credits / Chapter Font Overlay (`$00:F552` / `$00:F56B`):** `$00:F552` decompresses entry **`97`** (`4,928` B = 154 glyphs `$F100..$F199`) into `$7E:4000..$533F`, temporarily overwriting entry `93` (`$7E:4000..$5FFF`) for Chapter Cards (`$03:D4B2`, `$03:D5D2`) and Ending Credits (`$03:E0D0..`, `$03:E43E`). `$00:F56B` restores entry `93` afterwards (`$03:E5CF`).
- **Location Banner `2x` Software Scaler (`$0B:8F06`, `$0B:8F4A`, `$0B:8F58`, `$0B:8FE9`, `$0B:901C`):**
  - `$0B:8F58` / `$0B:8F4A` look up location ID in `$1D:D834` (length `ptr[i+1] - ptr[i]`, no `$FF`), read 8×16 1bpp glyphs from `$7E:2000`, double each pixel horizontally and vertically in software to `16x32` tiles (`4` vertical × `2` horizontal tiles per half-width char) at VRAM `$5C00` (or `$0400` + `$7E:C000`), and center within `16` half-width columns via `SEC; LDA #$10; SBC $B0` (`$0B:8F90`).
  - **Constraint:** Location names and `$0B:8EE3/$8F06` banner calls MUST stay **`<= 16` half-width glyphs** (`8` full-width kanji) or subtraction at `$0B:8F90` underflows (`$FF`, etc.).
- **Enemy Furigana Stripper (`$0C:CD11..$CD48`):** Copies enemy name from `$1D:B93D,X` into `$7E:1E80` and halts (`STA #$FF`) upon encountering `$1E` (`(`), stripping the developer-embedded `(<furigana>)` reading in-game.
- **Battle Text Wrappers (`$09:CDB2–$CE05`):** Set `$195E/$1960` cursor coordinates and invoke `$00:E97B`, `$00:E815`, `$00:E8C4` using the exact same engine.
