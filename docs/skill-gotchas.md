# Skill Gotchas

- `references/setup.md` / `scripts/fetch_emu.py`: On macOS ARM64, `fetch_emu.py mesen` downloads `Mesen_2.2.1_macOS_ARM64_AppleSilicon.zip`, whose outer zip only contains `Mesen.app.zip`; it must be unpacked a second time with `ditto -xk` and `xattr -dr com.apple.quarantine`.
- `scripts/emu.py`: `EXE["snes"]` hardcodes `Mesen.exe`, so `find_emu()` does not find `tools/mesen/Mesen.app/Contents/MacOS/Mesen` on macOS without passing `--emu` (wrapped via `tools/run_emu.py`).
- `references/setup.md` / `tools/mesen/`: MesenCE 2.2.1 on macOS supports portable mode when `settings.json` sits beside the executable at `Mesen.app/Contents/MacOS/settings.json`; `AllowIoOsAccess: true` and `Snes.Port1.Type: "SnesController"` work in `--testRunner` headless mode.
- `assets/skill.py`: Default `SKILL` path only checks `~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game`; on agents installed under `~/.agents/skills/translate-retro-game`, `tools/skill.py` needs that fallback candidate.
- `scripts/hooks/pre-commit`: Calls `python -X utf8` on line 18 for the NUL-byte check; macOS only has `python3`, so update line 18 to `python3 -X utf8`.
