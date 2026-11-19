# WRAM & System Interface Map — *Benkei Gaiden: Suna no Shou*

**Status:** Mixed **verified** (disassembly + live MesenCE RAM diffs across `ram_saizo`, `ram_courtyard`, `explore_guard*`, `explore_world_battle`, `explore_battle*`) and **candidate** (battle subfields beyond initialized IDs/HP).

---

## 1. Zero-Page & Core Engine (`$00:0000–$00FF`)

| Address | Size | Role | State | Notes |
|---|---:|---|---|---|
| `$0048` | 2 B | Frame / NMI / DMA queue write index | **verified** | Used across `$09:C47E`, `$0C:85D5`, `$0A:8114` to enqueue OAM/DMA requests into `$0B20` |
| `$004A` | 2 B | Global frame counter (low bytes tick every NMI) | **verified** | Masked in `$04:A2BC` (day/night/step checks), `$0B:959B`, etc. |
| `$0052` | 1 B | Pending / saved Map ID low byte (`submap`) | **verified** | Input to `$00:9344` (`LoadMap`); saved/restored by `$00:84A2` (`EnterBattle`) and `$03:F91E` (`WarpMap`) |
| `$0053` | 1 B | Pending / saved Map ID high byte (`area`) | **verified** | Input to `$00:9344` (`LoadMap`); `court=$11`, `battle_saved=$00` (from map `$0021`) |
| `$0054` | 1 B | Pending / saved player tile `X` | **verified** | Loaded by `$03:F91E`; saved from `$0D89` on battle entry (`$00:84B4`) |
| `$0055` | 1 B | Pending / saved player tile `Y` | **verified** | Loaded by `$03:F91E`; saved from `$0D8B` on battle entry (`$00:84B9`) |
| `$006C` | 1 B | Pending player facing / warp direction (`$FF` keep/default) | **verified** | Loaded by `$03:F91E` (`WarpMap`) |
| `$006D` | 1 B | Warp transition / BGM control byte (e.g. `$BC`, `$BE`, `$4D`) | **verified** | Read by `$03:F91E` / `$00:9344` |
| `$006E` | 1 B | Current map/screen mode (`$01` town, `$FF` battle, etc.) | **verified** | Checked by `$01:8436` for random encounter eligibility |
| `$0076–$0077` | 2 B | Master brightness / fade targets (`$0F` full on, `$80` blanked) | **verified** | Written before screen transitions (`$00:84EB`, `$00:852A`, `$03:8A01`) |
| `$00A0–$00E7` | 72 B | Unified text engine zero-page state (`$D5` box width `$18`, `$D7` lines `$03`, `$DC` bank/ptr cursor) | **verified** | See `docs/re/text_engine.md` |

---

## 2. Field Input, Control & Actor Table (`$0200–$05FF`)

| Address | Size | Role | State | Notes |
|---|---:|---|---|---|
| `$02FC–$02FD` | 2 B | Encounter / battle formation or RNG seed word | **verified** | `$00:84F5` pushes/restores `$02FC` across `JSL $0C:8002` (`$FCF7` in live battle RAM) |
| `$04FC–$04FD` | 2 B | Controller 1 newly-pressed joypad buttons (`$8000` B, `$4000` Y, `$2000` Sel, `$1000` Start, `$0800` Up, `$0400` Down, `$0200` Left, `$0100` Right, `$0080` A, `$0040` X) | **verified** | Dispatched by `$02:800D` against table `$02:8031` |
| `$04FE` | 2 B | Active field cursor / nearby NPC interaction ID | **verified** | Tested by `$02:E1E1` (`A` button talk vs menu open) |
| `$0500–$057F` | 128 B | Active map NPC/event object table (`16` × `8`-byte slots; `+$06..07 = $FFFF` terminator) | **verified** | Observed live in `ram_courtyard` (`$0530` gate guard `X=$11, Y=$1A`); layout `+$01=X, +$03=Y, +$04..07=ID/flags/sprite` |
| `$0B20–$0BFF` | — | NMI VRAM/DMA transfer queue entries (8 bytes per slot, indexed by `$0048`) | **verified** | Populated by `$0A:8111`, `$09:CC43`, `$0C:85D5` |

---

## 3. Persistent Save-Backed WRAM (`$01:80D0–$01:8170`)

`SaveGameToSRAM` (`$01:80D0`) copies four contiguous blocks plus the custom-name pixel cache into `8 KiB` SRAM (`$70:0000+`):

### 3a. World / Progress Block (`$0D00–$0DFF`, `256` B)

| Address | Size | Role | State | Notes |
|---|---:|---|---|---|
| **`$0D00–$0D0F`** | 16 B | **Event Flag Bitfield (`128` bits: flags `$00–$7F`)** | **verified** | Accessed by `$01:9302` (`Test`), `$01:9329` (`Set`), `$01:9349` (`Clear`). Byte `= flag >> 3`, bitmask `$00:A2F4[flag & 7]` = **MSB-first** (`$80, $40, $20, $10, $08, $04, $02, $01`). **Crucial:** **`$0D00` bit 7 (`$0080`, flag `$00`? Note `$0D00 & $0080` via 16-bit load = MSB of `$0D00` = Flag `$00`!) switches Act 1 (`$1A/$1B`) vs Act 2 (`$1C/$1D`) text banks in `$00:EC06`**! |
| **`$0D28–$0D29`** | 2 B | **Current Map ID (`u16` little-endian: low=`$0D28` submap/type, high=`$0D29` area)** | **verified** | Live values: `$1013` (Saizo's room), `$1110` (Shumon Fort Courtyard), `$3D00` / `$0000` (World Map exterior at `$50,$D2`), `$0021` (Happo Geho barrier dungeon), `$FFxx` during `$00:8500` battle |
| **`$0D2A–$0D2C`** | 3 B | **Party Gold (`ryo`, 24-bit unsigned little-endian)** | **verified** | Checked/subtracted as 24-bit integer in `$00:C6E5–$C6FD` |
| **`$0D2E–$0D2F`** | 2 B | Step / Day-Night encounter timer (`$01:846C`) | **verified** | Incremented by field step handler `$01:8428`; sets/clears Flag `$01` at `$01C0/$11D0/$0AC8`; `0x0001 -> 0x0002` observed exiting Fort |
| **`$0D88–$0DB7`** | 48 B | Party train buffer (up to `6` × `8`-byte follower/trail structs; `FF FF` terminated) | **verified** | Observed live in `ram_saizo2` (`$0D80–$0DB7`) |
| **`$0D89`** | 1 B | Leader (`Benkei`) current tile `X` coordinate | **verified** | Live verified: Saizo `$EE/$F0`, Courtyard `$10..$12`, World `$50`, Barrier dungeon `$0C..$15` |
| **`$0D8B`** | 1 B | Leader (`Benkei`) current tile `Y` coordinate | **verified** | Live verified: Saizo `$EF`, Courtyard `$13..$1D`, World `$D2`, Barrier dungeon `$07..$0A` |
| **`$0D8F`** | 1 B | Leader facing / movement state byte | **verified** | Observed `$0C/$0D/$0F` in Saizo's room, `$00..$06` during Courtyard movement |

### 3b. Inventories & Party Stats (`$1000–$113F`, `320` B)

| Address | Size | Role | State | Notes |
|---|---:|---|---|---|
| `$1000–$103F` | 64 B | Party Item Bag (`32` × `2` B slots; `$FF $00` = empty) | **verified** | Saved by `$01:811E` |
| `$1040–$107F` | 64 B | Party Equipment / Storage Bag (`32` × `2` B slots; `$FF $00` = empty) | **verified** | Saved by `$01:810A` |
| `$1080–$113F` | 192 B | **Active Party Character Blocks (`6` × `32`-byte structs, stride `$20`)** | **verified** | Saved by `$01:80F6`; copied into battle RAM at `$0C:8028`. Slot 0 (`$1080`) = `Benkei`; unused slots have `+$00 = $FFFF` |

#### Per-Character `32`-Byte Struct (`$1080 + slot * $20`)

Confirmed against `ram_courtyard` (`$1080..$109F`), Status Screen screenshot (`explore_npc` panel 5: `HP 40/40, MP 0/0, LV 1, 力 2, 素早さ 1, 運 4, 攻撃力 3, 守備力 2, EXP 0`), and Battle HUD (`40/0 -> 37/0` in `explore_battle_atk`):

| Offset | Size | Field | Observed Value (Lv 1 Benkei) | State |
|---|---:|---|---:|---|
| `+$00` | 2 B | Character ID (`$0000` = Benkei, `$FFFF` = empty) | `$0000` | **verified** |
| `+$02` | 2 B | Current HP | `40` (`$0028` -> `37` after hit) | **verified** |
| `+$04` | 2 B | Current MP / Spell Points | `0` (`$0000`) | **verified** |
| `+$06–$09` | 4 B | Status / ailment & temp battle flags | `$0000 $0000` | **candidate** |
| `+$0A` | 1 B | Level | `1` (`$01`) | **verified** |
| `+$0B–$0E` | 4 B | Equipped Weapon / Armor / Shield / Helm item IDs (`$FF` = none) | `$FF $FF $FF $FF` | **verified** |
| `+$0F` | 1 B | Accessory / 5th equip slot (`$FF` = none) | `$FF` | **candidate** |
| `+$10` | 2 B | Attack Power (`攻撃力`, or Attack mod) | `3` | **verified** |
| `+$12` | 2 B | Strength (`力`) | `2` | **verified** |
| `+$14` | 2 B | Agility (`素早さ`) | `1` | **verified** |
| `+$16` | 2 B | Vitality / Defense base (`守備力` = `2` on Status screen; `6` here includes growth/base table) | `6` | **candidate** |
| `+$18` | 2 B | Luck (`運`) | `4` | **verified** |
| `+$1A–$1F` | 6 B | Experience (`EXP`) / spell / growth fields (copied `+$1A` at `$0C:8033`) | `0` | **candidate** |

### 3c. Custom Party Name Bitmaps (`$7E:A800–$A9DF`, `480` B)

- Copied to/from SRAM by `$01:8132` (`480 B` = `5` party slots × `96 B` raw 1bpp glyph data for `{name0}..{name4}`). **verified**

---

## 4. Battle Engine WRAM (`$1180–$1A0F`)

Verified via `$0C:8002` initialization, `$0C:C9DF`, `$0C:8548`, `$03:8B33`, and live `explore_battle_atk` WRAM diffs (`式魂`):

| Address | Role | State |
|---|---|---|
| `$1180–$11FF` | Battle item usage / selection mirror (`+$00` item ID, `+$01` status scanned at `$0C:C9DF`) | **verified** |
| `$1380` | Active battle state (`$00` field / `$FF` in battle) | **verified** (`$00 -> $FF` in live battle) |
| `$1381–$13FF` | Battle party working copy (copied from `$1080` at `$0C:802D`, `$1386`/`$138C` read by HUD `$0C:8599`) | **verified** |
| `$1580–$16FF` | Battle enemy instance structs (`$1586` enemy HP/data, `$1590–$159F`, `$1680–$16FF`; live HP/damage changes observed in `explore_battle_atk`) | **verified** (range) / **candidate** (per-byte layout) |
| `$1780–$17FF` | Battle turn order / backdrop (`$1780=01`, `$1782=$31` terrain/backdrop, `$179E` turn index at `$0C:8084`) | **verified** |
| `$1800–$180F` | Battle target / command cursor slots (`$1801..$180A` cleared to `$FF` by `$0C:C9E0`) | **verified** |
| `$1A01` | Battle loop / menu input state flags (`$00` intro -> `$90` active turn) | **verified** |
| `$1A02` | Active battle phase/turn substate (`$09` menu -> `$01` anim/action -> `$00`) | **verified** |
| `$1A03` | Boss / special battle flag (`$80` set by `$03:8B33` before Rakan fight; `$09` in `explore_battle_atk`) | **verified** |

---

## 5. Text & UI Buffer WRAM (`$1950–$1EFF` & `$7E:*`)

Fully documented in `docs/re/text_engine.md` (**verified**):
- `$1950–$1962`: Box coordinates / cursor (`$195E` col, `$1960` row, `$1962` palette).
- `$1A80`, `$1B80`, `$1E80`: Dynamic text string formatting / enemy name stripped buffer (`$0C:CD11`).
- `$7E:2000–$AAFF`: Loaded map collision/tilemap work buffers.
- `$7E:AC00–$BFFF`: Window tilemap / static `$00–$1F` tile buffer (`$7E:AC10` loaded from `$0B:9095`).
- `$7E:C000`: 1bpp font decompression scratch buffer (`$00:F573`/`$F552`/`$F56B`).
- `$7E:D000–$D9FF`: Dynamic 320-slot 1bpp glyph cache (`$00:EA2A`), DMA'd to VRAM `$4400`/`$4E00` bitplane 0 (bitplane 1 pre-filled `$FF`).

---

## 6. Phase 2 Debug Warp Tool Interface

To warp directly to any map, Act, event state, or enemy encounter during Phases 2–9 QA without manual playthrough:

1. **Map Warp (`LoadMap`) — `JSL $00:9344` (via `$03:F91E` inline convention or direct RAM setup):**
   - Set `$0052` (Map sub-ID lo), `$0053` (Map area hi), `$0054` (`X`), `$0055` (`Y`), `$006C` (facing direction; `$FF` default), `$006D` (transition/BGM flags; e.g. `$BC`/`$BE`), then `JSL $00:9344` (16/8-bit caller must save/restore `P` cleanly — see `$03:F91E`).
   - Also update Event Flags `$0D00–$0D0F` via `LDA #flag; JSL $01:9329` (`SetFlag`) / `JSL $01:9349` (`ClearFlag`) so map scripts/exits match the target chapter.
2. **Act 1 / Act 2 Bank Switch (`$0D00` bit 7):**
   - **Act 1 (Japan, `$1A/$1B`)**: `$0D00` bit 7 (`$0D00 & $80`) == `0` (clear Flag `$00` via `$01:9349`).
   - **Act 2 (China, `$1C/$1D`)**: `$0D00` bit 7 (`$0D00 & $80`) == `1` (set Flag `$00` via `$01:9329`, matching `$09:9C7C`).
   - **Always toggle `$0D00` bit 7 alongside warping to Act 2 maps**, or dialogue pointers in `$1C/$1D` will read the wrong bank.
3. **Direct Battle Entry (`EnterBattle`) — `JSL $00:84A2`:**
   - Set `X` = enemy group / formation ID (e.g., `$000C` for Rakan boss, `$01B7`/`$00D8` normal groups checked at `$00:84BD`), `Y` = battle backdrop/script ID (e.g., `$0031`), and optionally `$1A03 = $80` for boss lock, then `JSL $00:84A2`. Returns Carry clear on win / set on flee or loss.
4. **Party / Stats / Gold Quick-Set:**
   - Set `$0D2A–$0D2C` for Gold; set `$1080 + slot*$20` `+$00` Char ID, `+$02` HP, `+$04` MP, `+$0A` Lv, `+$0B–$0E` Equip; set `$1000..$107F` for inventory/items as needed for late-game warp presets.
