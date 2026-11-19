# Benkei Gaiden: Suna no Shou (SNES) English translation

Skill: translate-retro-game (`/Users/antoineclerc-renaud/.agents/skills/translate-retro-game/SKILL.md`; `python3 -X utf8 tools/skill.py`). Read it before ROM, text or QA work.
Hooks setup on fresh clone: `git config core.hooksPath tools/hooks`.

## Commands (run from repo root)
- Build:    `python3 -X utf8 build.py` (TBD in Phase 3+; checks `rom.sha1` first)
- Check:    `python3 -X utf8 tools/check.py` (pre-commit hook runs this)
- Smoke:    `python3 -X utf8 tools/run_emu.py build/benkei_suna_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python3 -X utf8 tools/run_emu.py build/benkei_suna_en.sfc --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet`
- Release:  `python3 -X utf8 tools/release.py` (never publish without user approval)

## Paths
- Original ROM: `rom/Benkei Gaiden - Suna no Shou (Japan).sfc` (gitignored; SHA-1 `05a71b38a66f285564ec8447ff4877db74387860` in `rom.sha1`).
- Emulator: `tools/mesen/Mesen.app/Contents/MacOS/Mesen` (MesenCE 2.2.1 macOS ARM64; settings in `tools/emu-config/`). Assembler: `tools/asar/asar` (Asar 1.91).
- Text: `script/` (JSON). Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts: `docs/fonts.md`. Savestates: `work/states/`.

## Rulings
- Edit source files (`.py .lua .asm .tbl .json`) only with the file-edit tool; never shell heredocs, `sed -i`, or `.replace()` scripts.
- User rulings live in `docs/decisions.md` (pre-approved, drop honorifics, standard Hepburn, translate all graphics & credits, Mesen playtest).
- Mesen macOS ARM64 notes: `fetch_emu.py mesen` drops `Mesen.app.zip` (must unpack with `ditto -xk`); `emu.py` looks for `Mesen.exe`, so always use `tools/run_emu.py`.
- Use `python3.14` or `python3.12` when Pillow/numpy/capstone are needed; default `python3` (3.15) is stdlib-only.

## Status
`docs/status.md`: done, next, open bugs. Update at the end of every phase/session.
