# Graphics-Text Survey — *Benkei Gaiden: Suna no Shou*

**Status:** **verified** across all `282` compressed `$1F:8000` entries, the uncompressed `$0B:9095` UI tile block, `$0A:E111` / `$0A:E20A` / `$0A:E20D` loader callers, and live MesenCE PPU/VRAM captures (`explore1`, `explore_menus`, `explore_world_battle`, `battle_ppu`).

## Summary Verdict

All in-game dialogue, menus, Battle HUD/commands, enemy names, location banners, chapter cards, prologue/ending crawls, and credits are **dynamically rendered** by the unified `$00:E760/$EA2A` 1bpp font engine and require **no bitmap redraws** once scripts and the VWF font are patched.

Only **title/splash logos, 3 town/shop tilesets, 1 battle effect numeral sheet, and 2 uncompressed 8×8 UI mini-glyphs** contain static tile-drawn Japanese graphics requiring Phase 8 edits or verification.

---

## Static Tile-Drawn Japanese & Splash Graphics (Phase 8 Scope)

| Asset ID / Address | Destination | Comp / Raw Size | Format | Callers / Screen | Visible Japanese / Text | Phase 8 Action |
|---|---|---:|---|---|---|---|
| `$1F:8000` **#113** | `dst=$004000` | `2,560 B` raw (`80` tiles) | 4bpp | Title Screen main logo (with tilemaps **#117** `$000000` 2048 B / **#118** `$000800` 2048 B) (**verified** via `map117_113.png` & `explore1`) | **弁慶外伝** (large calligraphy title logo) | **Redraw** into stylized `BENKEI GAIDEN` logo tiles and update tilemap **#117**/**#118** |
| `$1F:8000` **#281** | `dst=$006000` | `1,186 B` / `3,072 B` (`96` tiles) | 4bpp | `$09:C3EF`, `$09:CB02` — Title Screen subtitle & copyright (with **#107**/**#108** `$000800`) (**verified**) | **沙の章 © 1992 SUNSOFT** | **Redraw** `沙の章` into English subtitle (*Chapter of Sand* or final approved subtitle) preserving `© 1992 SUNSOFT` |
| `$1F:8000` **#115** | `dst=$004000` | `512 B` raw (`16` tiles) | 4bpp | `$09:816A` (`JSL $0A:E111`) (**candidate** companion to #113/#114) | Brush/splash accent strokes (**candidate**) | **Inspect/Retouch** if tied to `弁慶外伝` title layout (**candidate**) |
| `$1F:8000` **#114** | `dst=$001000` | `2,848 B` raw (`89` tiles) | 4bpp | `$09:8163` (`JSL $0A:E111`) — Sunsoft splash (**verified**) | `SUNSOFT` outlined logo + borders | Already English (`SUNSOFT`); leave intact unless branding/layout changes |
| `$1F:8000` **#116** | `dst=$006000` | `3,776 B` raw (`118` tiles) | 4bpp | `$09:8171` (`JSL $0A:E111`) — Textured Sunsoft splash (**verified**) | `SUNSOFT` stone/textured logo | Already English (`SUNSOFT`); leave intact |
| `$1F:8000` **#001** | `dst=$001000` | `8,655 B` / `15,360 B` (`480` tiles) | 4bpp | Town / overworld map tileset loader (`$00:9525` family, **verified** via `town_tiles_full.png`) | Town building shop signs (`宿`, `防`, `道`, etc.) | **Redraw** building plaque tiles into English shop/inn signs (`INN`, `ARM`, `ITEM`, etc.) |
| `$1F:8000` **#011** | `dst=$001000` | `9,859 B` / `15,360 B` (`480` tiles) | 4bpp | Town shop tileset (`$00:9525` family, **verified** via `town_tiles_full.png`) | Shop plaques (`武`, `道`, `防`, `飯`, etc.) | **Redraw** shop plaques into concise English/icon signage (`ARMS`, `ITEM`, `ARM`, `INN`, etc.) |
| `$1F:8000` **#013** | `dst=$003000` | `4,813 B` / `7,872 B` (`246` tiles) | 4bpp | Town tileset (`$00:9525` family, **verified** via `town_tiles_full.png`) | Tavern sign (`酒`) | **Redraw** `酒` plaque as English/icon tavern sign (e.g. `SAKE`/`PUB` or flask) |
| `$1F:8000` **#227** | `dst=$004000` | `3,249 B` / `5,120 B` (`160` tiles) | 4bpp | Battle VRAM (`$0C:DD4C..`, confirmed in `battle_vram_2bpp.png`) | Battle FX + kanji numerals `〇一二三四五六七八九` | **Verify usage in battle QA** (`candidate` spell/skill count vs decorative seal); redraw `0–9` only if UI-functional |
| **`$0B:9095–$0B:9184`** | `$7E:AC10–$ACFF` -> VRAM `$4000` | `240 B` raw (`15` tiles) | 2bpp (uncompressed) | `$00:F437` window/UI static init (**verified** live in `battle_msg` & `uncomp_0B9095.png`) | Tiles `9–10`: 8×8 mini-kanji **`動`** (active battle tab) & **`文`** (text/page indicator); tiles `0–8` borders/cursor | **Replace** 8×8 `動`/`文` glyphs (e.g., concise icon/tag) in raw 2bpp data |

### Surveyed Non-Text Compressed Blocks (Confirmed Zero Redraw Needed)

- **`#092–#097`**: 1bpp planar fonts (`ben_092..097`) handled in Phase 4 VWF/font build (**verified**).
- **`#035` / `#036` (`$004000`, `8192 B`)**: World Maps (Japan & China/Mongolia) — geographic coastlines and skull/citadel icons only; **zero** baked text (**verified**).
- **`#027–#031`, `#083–#090`**: Party portraits (`4bpp`), zero text (**verified**).
- **`#091` (`$00D800`, `768 B`, caller `$00:A843`)**: Box fill/cursor gradients, zero text (**verified**).
- **`#105` (`512 B`), `#119` (`4096 B`)**: Title star/twinkle particles & UI sprites (**verified**; `#119` sparse cursor sparkles, zero readable kanji).
- **`#109` (`20768 B`), `#110` (`19104 B`)** + tilemaps **`#111`/`#112`**: Ending cutscene landscape artwork (`$03:E4DB..`), zero text (**verified**).
- **`#000, #002–#010, #012, #014–#017, #018–#026, #032–#034, #037–#082, #098–#104, #120–#280`**: Dungeon/field tilesets, NPC sprites, enemy sprites, spell/attack FX, battle backgrounds (`#246–#249` verified as battle sprite fragments loaded at `$0C:DD5B–DD7A`). **Zero** baked Japanese text (**verified** visually on contact sheets `s4bpp_0..11.png` & `s2bpp_0..10.png`).

---

## Dynamic Font-Rendered Displays (No Bitmap Redraw Required)

All of the following were verified live or via disassembly to render through `$00:E760/$EA2A` and `$1D`/`$1A–$1C` string tables:

1. **Title Screen Options (`最初から / 続きから`)** and **Name Entry Screen (`なまえを いれてください？`, `男・女`, `名前を入力しますか？`, `文字作字`, kana grid)** (**verified** in `explore1/sheet.png` & `title_vram_2bpp.png`). Note: Name Entry grid behavior (`$03:CE90`) will be updated alongside English character support in Phase 4/5.
2. **2× Location Banners** (e.g. `八方外法陣` in `explore_world_battle/sheet.png` panel 4): dynamically scaled from `$1D:D834` (`115` strings) by `$0B:8F06/$8F58` (**verified**; hard `<= 16` half-width char buffer in stock routine).
3. **Chapter Cards & End Credits / Crawls (`$03:D4B2..$EB25`, `$09:9DA0`)**: dynamically drawn using `ben_097` + `$1D:F59F–$F7F7` (**verified** in `text_tables.md`).
4. **Battle Top HUD (`不動 / 40 / 0`), Command Box (`攻撃 遁走 / 法術 道具`), Enemy Name Box (`式魂`, furigana stripped by `$0C:CD11`), Encounter Banner (`式魂(...)`), and Combat Messages (`$09:CDB2–$CE05`)** (**verified** in `explore_battle/sheet.png` and `battle_ppu/ppu_000090.vram.bin` showing 1bpp glyphs in bitplane 0 at VRAM `$4400` with bitplane 1 pre-filled `$FF`).
