# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 4 (Font, VWF Engine & Marker Build) COMPLETE -> Phase 5 (Glossary, Text Linter & Translation Setup) next.
- **Done:** Phase 1 RE (`[main 0774b7d]`); Phase 2 Cold-Boot Debug Warp Tool (`[main 6ba5513]`, 13/13 scenes + `GOD`/`NOENC`/`FAST`); Phase 3 Extraction & Identity Build (`[main e8b7c85]`); Phase 4 Font/VWF Engine & Marker Build (`tbl/en.tbl`, `tools/make_font.py` + `asm/font_en_{1bpp,widths}.bin`, 2 MiB LoROM expansion + `asm/engine.asm` with `LookupRedirect`, 320-slot 8x16 VWF tile cache, `$FB` pre-cache separator, `Hook_EC06/CFDF/D043/01A4DB/F573/F4D9/E9A3/ED80/CD11/CB0A/CF25`, `build.py --mode marker|translate`, 13/13 cold-boot + interactive dialogue/battle/menu/status/location MesenCE QA in `work/qa/marker/`, measured pixel gate `docs/windows.json`, and `tests/test_font_and_marker.py`).
- **Next:** Phase 5 complete `glossary.md` and `tools/lint.py`, followed by Phase 6 full script translation (`script/*.json`).
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
