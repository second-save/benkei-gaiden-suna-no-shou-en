# Character Encoding & Font Tables (`tbl/jp.tbl` & `tbl/credits_jp.tbl`)

**Status:** **verified** (visual verification of `ben_092..097` glyphs in `work/re/font_single.png`, `font_kanji_used_0..3.png`, and `font_credits_97.png`, furigana verification across all 168 enemies in `$1D:B93D`, zero duplicate values, and 100% byte-exact roundtrip in `tests/test_tbl.py`).

## 1. Glyph Addressing (`$00:E99D`, `$00:EA31`)

All glyphs in WRAM (`$7E:2000–$7E:AAFF`, 35,584 B from compressed `$1F:8000` entries `92..96`) are **1bpp 8×16 tiles** (`16` bytes/tile):

- **Single-byte (`$00–$BF`):** `glyph_id = byte` (`1` tile column wide).
  - `$00–$0F`: Digits `0–9`, uppercase hex `A–F`.
  - `$10–$1F`: Space (`$10`) and punctuation (`”`, `！`, `？`, `：`, `ー`, `＼`, `／`, `。`, `、`, `「`, `」`, `・`, `’`, `（`, `）`).
  - `$20–$6F`: Precomposed hiragana (80 glyphs, including dakuten/handakuten and small kana; `$48=る`, `$49=れ`, `$4A=ろ`, `$4B=わ`, `$4C=を`, `$4D=ん`).
  - `$70–$BF`: Precomposed katakana (80 glyphs).
  - **`$00–$1F` static VRAM optimization (`$00:F442`, `$00:EA40`):** Preloaded permanently into VRAM tiles `$0010–$004E` without consuming slots in the 320-tile dynamic cache (`$7E:D000`).
  - `$C0–$EF`: Never referenced in any text bank (and would collide into `$F060+` kanji halves!).
- **2-byte Kanji (`$F0–$F7`):** `glyph_id = ((b0 << 8 | b1) & $07FF) << 1` (left half) and `glyph_id + 1` (right half, `2` tile columns wide).
  - Valid used standard range: **`$F060–$F457`** (`998` unique used kanji, sorted in gojūon / on'yomi dictionary order; **zero identical bitmaps** across all `00..BF` and all `998` used kanji).
  - Note: Only **`998` of `~1,024` kanji slots** up to `$F457` are actually referenced in ROM text; unused slots are mostly skipped near `$F439..$F457`.

## 2. Dynamic Party Name Placeholders (`$F440–$F44E`)

`$00:F4D9` copies 5 default names (`30` bytes at `$00:F534`, 6 half-width tiles each) into `$7E:A800–$A9DF`, mapping directly to the `$F440–$F44E` kanji IDs. An exhaustive scan of `$1A–$1D` proved that all `1,497` `$F44x` bytes occur exclusively as consecutive 3-tile (`6`-byte) sequences:

| Hex Sequence | Placeholder | Default Value (`$00:F534`) | Role |
|---|---|---|---|
| `F440F441F442` | `{name0}` | ` 不動 ` | Protagonist (Fudo) |
| `F443F444F445` | `{name1}` | ` 巳陰 ` | Party Member 1 (Mikage) |
| `F446F447F448` | `{name2}` | ` 常由 ` | Party Member 2 (Tsuneyoshi) |
| `F449F44AF44B` | `{name3}` | ` 白蓮 ` | Party Member 3 (Byakuren) |
| `F44CF44DF44E` | `{name4}` | ` 鳴沙 ` | Party Member 4 (Meisha) |

## 3. Control Codes (`$F8–$FF`)

- **`$FD` (`{nl}`):** Newline; scrolls box when at line limit `$D7`.
- **`$FE` (`{page}`):** Wait for button press + clear dialogue box.
- **`$FF` (`{end}`):** End of string (`TERMINATORS` in `tools/tbl.py`).
- **`$FC $00` (`{pal0}`):** Set BG3 tilemap attribute palette 0 (`$E3 = $2000`).
- **`$FC $01` (`{pal1}`):** Set BG3 tilemap attribute palette 1 (`$E3 = $2400`).
- **`$FC $02 <arg>` (`{wait:1}`):** 3-byte frame delay via `$0B:9395`.
- **`$FC $03 <arg>` (`{nop:1}`):** 3-byte no-op.
- **`$F8–$FB` (`{noopF8}`–`{noopFB}`):** 1-byte `RTS` no-ops; `0` occurrences in static ROM text (`$FC` also has `0` occurrences in static ROM text).

## 4. Credits / Chapter Overlay (`tbl/credits_jp.tbl`)

When displaying Chapter Cards (`$03:D4B2`, `$03:D5D2`) or Ending Credits (`$03:E0D0..`, `$03:E43E`), `$00:F552` decompresses entry `97` (`4,928` B = `154` kanji) over `$7E:4000–$533F` (`$F100–$F199`). Because strings in `$1D:F59F–$F7F7` also reference 20 `$F0xx` codes outside `$F100–$F199` whose glyphs duplicate kanji inside `ben_097` (e.g., `$F079` vs `$F103` = `井`), `tbl/credits_jp.tbl` maps those 20 base-bank `$F0xx` codes to zero-arg tokens `{sF0xx}` so roundtrip encoding remains 100% bijective without collisions in `tools/tbl.py`.
