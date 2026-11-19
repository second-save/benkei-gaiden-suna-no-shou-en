# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 3 (Identity Build & Extraction) COMPLETE -> Phase 4 (Font/VWF Engine & Marker Build) next.
- **Done:** Phase 1 RE (`[main 0774b7d]`); Phase 2 Cold-Boot Debug Warp Tool (`[main 6ba5513]`, 13/13 scenes + `GOD`/`NOENC`/`FAST`); Phase 3 Extraction & Identity Build (`tools/extract.py`, `script/*.json` — 17 files / 3,197 entries covering 100% of `$1A–$1D` + `$00:F534` with zero `[XX]` unknowns and explicit `00fe` `data` span at `$1C:88FC`, `build.py --mode identity` byte-identical `build/id.sfc` verified by `romdiff.py` & MesenCE smoke, `tests/test_identity.py`).
- **Next:** Phase 4 LoROM 2 MiB expansion, `$00:EC06` / `$1D` relocation hooks, VWF 8×16 font engine + English glyph table, and marker build + pixel width gate.
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
