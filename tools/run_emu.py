"""Repo wrapper for $SKILL/scripts/emu.py that locates this project's MesenCE binary on macOS/Linux/Windows."""
import glob
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402


def find_mesen() -> str:
    patterns = [
        str(ROOT / "tools" / "mesen" / "**" / "Mesen"),
        str(ROOT / "tools" / "mesen" / "**" / "Mesen.exe"),
    ]
    for pat in patterns:
        hits = sorted(p for p in glob.glob(pat, recursive=True) if os.path.isfile(p) and os.access(p, os.X_OK))
        if hits:
            return os.path.abspath(hits[0])
    sys.exit("Mesen executable not found under tools/mesen/: run fetch_emu.py mesen")


def main() -> int:
    argv = sys.argv[1:]
    if "--emu" not in argv:
        argv = [*argv, "--emu", find_mesen()]
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), *argv]
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    sys.exit(main())
