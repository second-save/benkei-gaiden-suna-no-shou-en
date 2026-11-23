# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 7 (Visual QA & Bugfix Closure) COMPLETE -> Phase 8 (Tile-Drawn Graphics Translation) next.
- **Done:** Phase 1 RE (`[main 0774b7d]`); Phase 2 Cold-Boot Debug Warp Tool (`[main 6ba5513]`); Phase 3 Extraction & Identity Build (`[main e8b7c85]`); Phase 4 Font/VWF Engine & Marker Build (`[main 5504e62]`); Phase 5 Engine/Font Polish (`[main 5f55c61]`); Phase 6 Full Script Translation & Dual Review (`3197` entries, 0 untranslated, Wave 1a/1b `[main 981e116]`, Act 1 `[main 023f354]`, Act 2 in `script/act2_bank1c.json` & `script/act2_bank1d.json`); Phase 7 Visual QA & Engine Fixes (`asm/engine.asm`: `$0199CA/$0199D2` Settings X-coords, `$0CBB5D` Jutsu pad loop `BEQ->BCS`, `Hook_C131` Item Bag/Battle items unclipped copy & right-aligned qty, `$0CBFA9/$0CD517/$0CD522` JP byte replacements; `docs/polish.md` cleared 0 open `[ ]` items; MesenCE QA verified Settings, Sound Test, Male/Female, Status, Jutsu+Desc, Equip+Desc, Items+Desc, Save Shrine, Town/Inn dialogue, Battle Text/Active modes, Ending Credits).
- **Next:** Phase 8 tile-drawn graphics translation (`#113`+`#117/#118`, `#281`+`#107/#108`, `#001`, `#011`, `#013`, `#227`, `$0B:9095` `動`/`文` -> `A`/`T`), then Phase 9 `.bps` + `README.md` release zip & smoke test.
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
