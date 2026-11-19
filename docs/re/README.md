# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [rom_map.md](rom_map.md) | 48-bank LoROM layout (`$00–$2F`), header, free `$FF` space, 2–4 MiB expansion notes | **verified** |
| [compression.md](compression.md) | `$1F:8000` 282-entry table, `$0A:E111`/`$E120`/`$E20A`/`$E20D` decompressor & encoder | **verified** |
| [text_engine.md](text_engine.md) | Unified `$00:E75D–$F630` engine, `$00:EC06` bank mapper, 320-slot 1bpp cache, `2x` banners, furigana stripper | **verified** |
| [text_tables.md](text_tables.md) | Full `$1A–$1D` (`103,519` B) audit, 10 sentinel tables, `$0D:8002` Groups `0–7`, credits/crawls | **verified** |
| [encoding.md](encoding.md) | `tbl/jp.tbl` (998 standard kanji + `{name0..4}`) & `tbl/credits_jp.tbl` (154 `ben_097` overlay kanji) | **verified** |
| [graphics_text.md](graphics_text.md) | Survey of all `282` compressed assets + `$0B:9095` UI tiles + live Title/Battle PPU captures | **verified** |
| [ram_map.md](ram_map.md) | Persistent SRAM-backed WRAM, actor/party/battle state, Phase 2 warp/flag/battle call interface | mixed **verified** / **candidate** |
