# Text Tables & Bank Accounting — *Benkei Gaiden: Suna no Shou*

**Status:** **verified** (100% byte-accounting audit of `$1A–$1D`, code scan of `$00–$1E` for pointer tables and inline calls, and disassembly of `$00:BA63`, `$00:B430`, `$0B:8F58`, `$0C:CD11`, `$09:9C50`, `$03:D490–$EB25`).

## 1. Global Scan Summary (`$00–$2F`)

- **All game text resides exclusively in banks `$1A–$1D`** plus the 30-byte default party-name table at **`$00:F534`**. Exhaustive scans of banks `$00–$19` and `$1E` found no other text tables or encoded text blocks.
- **Total used text & pointer data across `$1A–$1D`:** **`103,519` bytes** (`$FF` padding excluded).

## 2. Text Banks `$1A–$1D` Breakdown

| Bank | Address Range | Used Bytes | Trailing/Gap `$FF` | Chunks / Entries | Dispatch & Contents |
|---|---|---:|---:|---|---|
| `$1A` | `$8000–$A52E` | `9,519` | `23,249` B (`$A52F–$FFFF`) | `179` `$FF`-strings | Act 1 (Japan, `$0D00 bit 7 == 0`) dialogue (`ptr = $8000–$A7FF`) |
| `$1B` | `$8000–$FF47` | `32,584` | `184` B (`$FF48–$FFFF`) | `616` `$FF`-strings | Act 1 (Japan, `$0D00 bit 7 == 0`) dialogue (`encoded ptr = $0000–$7FFF`) |
| `$1C` | `$8000–$FA76` | `31,351` | `1,417` B (`$FA77–$FFFF`) | `596` `$FF`-strings | Act 2 (China, `$0D00 bit 7 != 0`, set by `$09:9C7C`) dialogue (`encoded ptr = $0000–$7FFF`) |
| `$1D` (low) | `$8000–$A578` | `9,593` | `647` B gap (`$A579–$A7FF`) | `218` non-empty chunks (`219` total) | Prologue crawl (`$8000–$817A`, `$09:9DA0`), ending crawl (`$A200–$A578`, `$03:EA22..$EB25`), Act 2/UI (`$817B–$A1FF`) |
| `$1D` (high) | `$A800–$F7F7` | `20,472` | `2,056` B (`$F7F8–$FFFF`) | See sub-tables below | Shared system/UI strings, item/spell/enemy/location tables, descriptions, credits overlay |

## 3. Bank `$1D` Sub-Region & Sentinel-Chained Pointer Tables

Every pointer table from `$B0AC` through `$ECCE` stores 16-bit pointers little-endian (`$1D:xxxx`), followed immediately by its strings; each table ends with an extra sentinel pointer equal to the start of the next section so callers (`$00:B430`, `$0B:8F58`) compute string length via `ptr[i+1] - ptr[i]`.

| `$1D` Range | Table Ptrs Range | Data Range | Entry Count | `$FF`-Term? | Caller / Notes |
|---|---|---|---:|---|---|
| `$8000–$817A` | at `$09:9DA0` | `$8000–$817A` | `19` (`16` non-empty) | Yes | Prologue crawl (`$09:9C4E`), sets `$0D00 \|= $0080` (**verified**) |
| `$9F52–$9FC3` | inline | `$9F52–$9FC3` | `5` | Yes | `$03:CE90` (`$03:CEA8..CEFF`) (**verified**) |
| `$A200–$A578` | `$03:EA6A..$EB25` + inline | `$A200–$A578` | `5` crawl groups + `2` | Yes | Ending crawl screens (`$03:E660..$EA30`) (**verified**) |
| `$A800–$B0AB` | inline / `$0D` | `$A800–$B0AB` | `141` non-empty (`142` chunks) | Yes | Shared system, shop, battle, and name-entry messages (**verified**) |
| `$B0AC–$B5F9` | `$B0AC–$B253` | `$B254–$B5F9` | `211` (+ sentinel `$B5FA`) | No (length by diff) | Weapons, Armor & Equipment names (`$00:B446`, `$0C:A4AE`, `$0C:C82D`) (**verified**) |
| `$B5FA–$B795` | `$B5FA–$B65F` | `$B660–$B795` | `50` (+ sentinel `$B796`) | No (length by diff) | Consumables & Key Items (`$00:B480`, `$0C:A4A7`, `$0C:BF0F`, etc.) (**verified**) |
| `$B796–$B8E8` | `$B796–$B7EF` | `$B7F0–$B8E8` | `44` (+ sentinel `$B8E9`) | No (length by diff) | Jutsu / Spell names (`$09:93CE`, `$0C:A3F7`, `$0C:B899`, etc.) (**verified**) |
| `$B8E9–$B93C` | `$B8E9–$B8F8` | `$B8F9–$B93C` | `7` (+ sentinel `$B93D`) | No (length by diff) | Ougi / Special Combo Techniques (`$00:B8BD`, `$0C:A3FE`, `$0C:BB7F`, etc.) (**verified**) |
| `$B93D–$C2D0` | `$B93D–$BA8E` | `$BA8F–$C2D0` | `168` (+ sentinel `$C2D1`) | Yes | Enemy names with `$1E <furigana> $1F` (`$0C:CA4A`, `$0C:CD19`) (**verified**) |
| `$C2D1–$D833` | inline / code | `$C2D1–$D833` | `449` chunks | Yes | Menu/status/battle/shop/name-entry/settings UI strings (**verified**) |
| `$D834–$DC3D` | `$D834–$D91B` | `$D91C–$DC3D` | `115` (+ sentinel `$DC3E`) | No (length by diff) | Location names (`$0B:8F58` 2x banner scaler; **`<= 16` half-width chars**) (**verified**) |
| `$DC3E–$E827` | `$DC3E–$DDE5` | `$DDE6–$E827` | `211` (+ sentinel `$E828`) | Yes | Equipment descriptions (`$00:B4A3`, `$0C:BDE4`) (**verified**) |
| `$E828–$ECCD` | `$E828–$E889` | `$E88A–$ECCD` | `48` (+ sentinel `$ECCE`) | Yes | Consumable & Key item descriptions (`$00:B4D8`, `$01:CE04`, `$0C:BDE2`, etc.) (**verified**) |
| `$ECCE–$F59E` | `$ECCE–$ED5D` | `$ED5E–$F59E` | `71` (+ sentinel `$F59F`) | Yes | Jutsu / Special Tech descriptions & info (`$01:EBA9`, `$0C:BDE6/$BDE8`) (**verified**) |
| `$F59F–$F7F7` | `$03:D4B2/$D5D2/$E0F6/$E199/$E5D6` | `$F59F–$F7F7` | `~55` strings | Yes | Chapter cards (`$03:D4B2..`), ending banners (`$0B:8EE3`), staff credits (`$03:E5D6`); uses **`ben_097`** overlay (`$F100–$F199`) (**verified**) |

## 4. Event Dialogue Dispatch Table (`$0D:8000–$0D:BB2C`)

- Read by `$00:BA78` / `$01:8306` (`LDA $0D:8002,X`):
  - **8 groups (`0–7`):** `$801E`, `$8182`, `$9B34`, `$8012`, `$A1FF`, `$A377`, `$B6A6`, `$BB28`.
  - Contains **`1,389` unique event records** spanning `$0D:8016–$0D:BB2C`.
  - Record layout: 5-byte header + N 3-byte condition clauses (`(byte & $7F) != $7F`) + `$7F` terminator + `uint16 ptr16` (resolved by `$00:EC06`).

## 5. Inline Callers & Fixed Code Tables

- **Direct inline string callers (`138` 4-byte `ptr16, x, y` calls across code banks):** `125` point to `$1D:$A800–$FFFE`, `7` point to `$8000–$A7FF`, and `6` point to `< $8000`. Note `$00:ED40/$ED4E` / `$00:E7CA..E7DD` are 2-byte `(x, y)` RAM-buffer (`$7E:1E80`) calls.
- **`$00:F534` (30 bytes):** 5 default 6-byte party member names (`5 x 6` bytes) copied into `$7E:A800..$A9DF` by `$00:F4D9`.
