# Status

Updated at the end of every session/phase. Keep it to what the next session needs; history is in git.

- **Phase:** 5 (Glossary, Style Reference, Linter, Batch Pipeline & Pilot Visual QA) COMPLETE -> Phase 6 (Full Script Translation & Review) next.
- **Done:** Phase 1 RE (`[main 0774b7d]`); Phase 2 Cold-Boot Debug Warp Tool (`[main 6ba5513]`); Phase 3 Extraction & Identity Build (`[main e8b7c85]`); Phase 4 Font/VWF Engine & Marker Build (`[main 5504e62]`); Phase 5 Engine/Font Polish (tightened 4px lowercase glyphs in `tools/make_font.py` fitting `Sen`/`Ryo` in 16px and `New Game` in 47px; `$0B:8F90/$8FB3/$901C` 8x32 banner/credits scaler doubling capacity to 12ch top / 20ch bottom / 30ch banner; tile-aligned `{pad}` flush; `$00:8095` title window +1 tile; `JslStockEA31` `pea $EC62` RTL fix for untranslated kanji), Translation Docs (`glossary.md`, `docs/synopsis.md`, `docs/style-reference.md`, `docs/translator-brief.md`, `docs/reviewer-brief.md`, `docs/story-reviewer-brief.md`), Deterministic Tooling (`tools/lint.py`, `tools/fit.py`, `tools/batches.py`, `tests/test_lint_and_batches.py`, wired into `tools/check.py`), and Visually Verified Pilot Slice (`party_names`, core `ui_bank1d_c2` UI/battle/status/title/party, 4 `credits_overlay` cards, 4 `tbl_locations` banners, `1A_8000..1A_84A2` opening cutscene, and `1D_8000..1D_816C` Act 2 crawl verified in MesenCE at `work/qa/pilot/`).
- **Next:** Phase 6 batch translation & dual review (tables first -> dialogue waves -> Name Entry English grid) via `tools/batches.py`, then Phase 7 full visual QA and Phase 8 graphics/UI tile redraws.
- **Open bugs:** None.
- **Waiting on the user:** Nothing (pre-approved per D7).
