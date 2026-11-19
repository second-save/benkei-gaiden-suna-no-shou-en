"""Where the translate-retro-game skill lives. Repo scripts do `from skill import SKILL`; `python tools/skill.py` prints it.

Copied into a game repo's tools/ at setup. Env TRANSLATE_SKILL overrides the default (a non-plugin install).
"""
import os, sys

_CANDIDATES = [
    os.environ.get("TRANSLATE_SKILL"),
    os.path.expanduser("~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game"),
    os.path.expanduser("~/.agents/skills/translate-retro-game"),
]
SKILL = next((p for p in _CANDIDATES if p and os.path.isfile(os.path.join(p, "SKILL.md"))), None)
if not SKILL:
    sys.exit("translate-retro-game skill not found: install the plugin, or set TRANSLATE_SKILL to its folder")
SCRIPTS = os.path.join(SKILL, "scripts")

if __name__ == "__main__":
    print(SKILL.replace("\\", "/"))
