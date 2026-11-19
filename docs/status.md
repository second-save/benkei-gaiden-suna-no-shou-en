# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 1 (Research & Recon) COMPLETE -> Phase 2 (Debug Warp Tool) next.
- **Done:** Isolated git repo initialized under `second-save`, MesenCE 2.2.1 & Asar 1.91 wired, full 48-bank LoROM map (`docs/re/rom_map.md`), `$1F:8000` `282/282` roundtrip compressor/decompressor (`tools/compress.py`), complete text engine + 100% `$1A–$1D` (`103,519` B) & `$0D:8002` pointer trace (`docs/re/text_engine.md`, `docs/re/text_tables.md`), verified kanji tables (`tbl/jp.tbl` 998 kanji, `tbl/credits_jp.tbl` 154 overlay kanji, `tools/check.py` 7/7 passing), live battle verification & PPU/VRAM confirmation (`work/re/explore_battle*`), `$1F:8000` + `$0B:9095` graphics-text survey (`docs/re/graphics_text.md`), and WRAM + Phase 2 warp/battle API map (`docs/re/ram_map.md`).
- **Next:** Phase 2 Debug Warp Tool (`build/warp.sfc`, title/select-menu debug warp into Acts 1 & 2, battles, and key locations) followed by Phase 3 identity build (`build/id.sfc`).
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
