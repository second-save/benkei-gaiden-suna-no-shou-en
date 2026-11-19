# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 2 (Debug Warp Tool) COMPLETE -> Phase 3 (Identity Build & Extraction) + Phase 4 (Font/VWF & Marker Build) next.
- **Done:** Phase 1 RE (`docs/re/*`, `tools/compress.py` 282/282, `tbl/{jp,credits_jp}.tbl`, `[main 0774b7d]`); Phase 2 Cold-Boot Debug Warp Tool (`tools/debug/{scenes.lua,warp.lua,regen_states.py}`): all 13/13 cold-boot warp scenes (`title`, `name_entry` kana grid, `shumon_saizo`, `shumon_courtyard`, `happo_dungeon`, `tosa_village`, `act1_world`, `battle_normal`, `battle_rakan`, `act2_prologue` sea/crawl, `act2_town`, `chapter_card` `ben_097` overlay, `ending_credits`) + opt-in `GOD=1`/`NOENC=1`/`FAST=1` mods + `tests/test_debug_scenes.py` verified via MesenCE & `tools/check.py`.
- **Next:** Phase 3 identity build (`build/id.sfc`) + script/graphics extraction, followed by Phase 4 VWF font engine + marker build (`tools/build.py`).
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
