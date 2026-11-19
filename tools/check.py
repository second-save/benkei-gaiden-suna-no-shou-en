"""One-command repository check: verifies base ROM hash and runs unit tests."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_rom  # noqa: E402


def main() -> int:
    check_rom.check()
    print("rom ok")

    tests_dir = ROOT / "tests"
    if tests_dir.is_dir() and any(tests_dir.glob("test_*.py")):
        r = subprocess.run(
            [sys.executable, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
            cwd=ROOT,
        )
        if r.returncode != 0:
            return r.returncode
    return 0


if __name__ == "__main__":
    sys.exit(main())
