# ROM Map — *Benkei Gaiden: Suna no Shou*

**Status:** **verified** (header inspection, 48-bank trailing-`$FF` audit, and 24-bit pointer/call scan against `rom.sha1`).

## Cartridge Header (`$00:FFB0–$00:FFFF`, PC `0x007FB0–0x007FFF`)

| Field | Value | Notes |
|---|---|---|
| Title (`$00:FFC0`) | `BENKEI -SUNA-        ` | 21 bytes ASCII + spaces |
| Map Mode (`$00:FFD5`) | `$20` | LoROM, SlowROM |
| ROM Type (`$00:FFD6`) | `$02` | ROM + RAM + Battery |
| ROM Size (`$00:FFD7`) | `$0B` | `1,572,864` bytes (1.5 MiB / 48 LoROM banks `$00–$2F`) |
| SRAM Size (`$00:FFD8`) | `$03` | `8 KiB` |
| Country (`$00:FFD9`) | `$00` | Japan (NTSC) |
| Checksum / Complement | `$BEC1` / `$413E` | Sum `$FFFF`, **verified** by `tools/check_rom.py` |
| Reset Vector (`$00:FFFC`) | `$8000` (Emulation) | Code executes starting bank `$00` |

## LoROM Addressing

Each bank `$00–$2F` maps CPU `$8000–$FFFF` (`32,768` bytes) to PC file offset `bank * 0x8000 + (addr - 0x8000)`. No copier header (`file size == 1,572,864 B`).

## Bank-by-Bank Map (`$00–$2F`)

Trailing `$FF` counts were measured over contiguous trailing `$FF` bytes at the end of each 32 KiB bank.

| Banks | PC Range | Used Bytes | Trailing `$FF` | Role & Contents |
|---|---|---:|---:|---|
| `$00` | `0x000000–0x007FFF` | `32,767` | `1` | Core engine: boot, NMI/IRQ, event dispatcher (`$00:BA63`), unified text engine (`$00:E760–$F630`), vectors (**verified**) |
| `$01` | `0x008000–0x00FFFF` | `31,192` | `1,576` | Overworld movement/collision (`$01:82E0`), SRAM save/load (`$01:93xx–$97xx`), field UI (**verified**) |
| `$02` | `0x010000–0x017FFF` | `31,118` | `1,650` | Field logic, transitions (`$02:9019 -> $09:9C4A`), palette/mode helpers (**verified**) |
| `$03` | `0x018000–0x01FFFF` | `31,362` | `1,406` | Chapter cards (`$03:D4B2..`), name entry UI (`$03:CE90`), ending/credits/crawl (`$03:E0D0..$EB25`) (**verified**) |
| `$04` | `0x020000–0x027FFF` | `12,156` | `20,612` | Helper routines, party/sprite utilities; large trailing `$FF` free block (`$AF7C–$FFFF`) (**verified**) |
| `$05–$08` | `0x028000–0x047FFF` | `123,760` | `7,312` | Map tilemaps and overworld/town map data (**verified** via `$80` RLE/map headers) |
| `$09` | `0x048000–0x04FFFF` | `30,173` | `2,595` | Battle text wrappers (`$09:CDB2–$CE05`), prologue crawl (`$09:9C4E`, `$09:9DA0`), battle/spell tables (`$09:EB90..`) (**verified**) |
| `$0A` | `0x050000–0x057FFF` | `27,099` | `5,669` | Tile decompressor (`$0A:E120`, `$0A:E20A`/`$E20D`), graphics/animation tables (**verified**) |
| `$0B` | `0x058000–0x05FFFF` | `30,647` | `2,121` | Location banner `2x` scaler (`$0B:8F06`, `$0B:8F4A`, `$0B:8F58`, `$0B:8FE9`), frame wait (`$0B:9395`), border tiles (`$0B:9095`) (**verified**) |
| `$0C` | `0x060000–0x067FFF` | `31,895` | `873` | Menu/shop/inventory/battle-UI string copy & formatting (`$0C:838C`, `$0C:BDE2`, `$0C:CD11` enemy furigana stripper) (**verified**) |
| `$0D` | `0x068000–0x06FFFF` | `31,015` | `1,753` | Event/dialogue pointer tables (`$0D:8002` Groups `0–7`), shop/item/enemy stat tables (`$0D:BB36..$F926`) (**verified**) |
| `$0E` | `0x070000–0x077FFF` | `20,261` | `12,507` | Mixed battle/map helpers and data; `12,507` B trailing `$FF` (`$CF25–$FFFF`) (**verified**) |
| `$0F` | `0x078000–0x07FFFF` | `28,307` | `4,461` | Map/sprite/HUD helpers (`$0F:ED34`) (**verified**) |
| `$10–$19` | `0x080000–0x0CFFFF` | `297,521` | `30,159` | SPC700 audio driver, BRR samples, sequences, battle/map data (`$19` has `16,259` B free) (**candidate**; zero text tables found) |
| `$1A` | `0x0D0000–0x0D7FFF` | `9,519` | `23,249` | Dialogue text block A (`$8000–$A52E`), accessed when `($0D00 & $80) == 0` and ptr `$8000–$A7FF` (**verified**) |
| `$1B` | `0x0D8000–0x0DFFFF` | `32,584` | `184` | Dialogue text block B (`$8000–$FF47`), accessed when `($0D00 & $80) == 0` and encoded ptr `< $8000` (**verified**) |
| `$1C` | `0x0E0000–0x0E7FFF` | `31,351` | `1,417` | Dialogue text block C (`$8000–$FA76`), accessed when `($0D00 & $80) != 0` and encoded ptr `< $8000` (**verified**) |
| `$1D` | `0x0E8000–0x0EFFFF` | `30,065` | `2,056` | Dialogue block D (`$8000–$A578`, `$647` B `$FF` gap `$A579–$A7FF`), system/UI strings (`$A800–$B0AB`), 10-table chain (`$B0AC–$F59E`), credits/chapter overlay strings (`$F59F–$F7F7`) (**verified**) |
| `$1E` | `0x0F0000–0x0F7FFF` | `32,044` | `724` | Game/map/battle code & tables (**verified**; no text tables) |
| `$1F` | `0x0F8000–0x0FFFFF` | `32,758` | `10` | Compressed graphics index table (`$1F:8000–$1F:8581`, 282 × 5 B) + start of compressed blob (`$1F:8582..`) (**verified**) |
| `$20–$2F` | `0x100000–0x17FFFF` | `507,484` | `16,804` | Packed compressed graphics/font/tilemap streams (`$1F:8582–$2F:BE74`); `$2F:BE75–$FFFF` has `16,779` B `$FF` (**verified**) |

## Expansion Notes (for Phases 3–8)

- **Existing free space inside 1.5 MiB:** `$04` (`20,612` B), `$0E` (`12,507` B), `$19` (`16,259` B), `$1A` (`23,249` B), `$2F` (`16,779` B) are contiguous trailing `$FF` blocks. Note that `$1A` text pointers cannot reach above `$A7FF` through unmodified `$00:EC06`, whereas bank `$04` has `> 20 KiB` contiguous room for ASM hooks (`Phase 2/3/5`).
- **Clean LoROM expansion:** Expanding `$0B` -> `$0C` (2 MiB, banks `$30–$3F`) or 4 MiB (banks `$30–$7D`, updating header byte `$FFD7 = $0C` and recalculating `$FFDC/$FFDE`) provides `512 KiB`–`2.5 MiB` of guaranteed contiguous free space for relocated English dialogue, expanded descriptions, VWF font tables, and recompressed graphics.
