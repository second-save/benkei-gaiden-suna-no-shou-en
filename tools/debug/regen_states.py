"""Regenerates cold-boot debug savestates and QA sheets from tools/debug/scenes.lua."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROM = ROOT / "rom" / "Benkei Gaiden - Suna no Shou (Japan).sfc"
SCENES_LUA = ROOT / "tools" / "debug" / "scenes.lua"
WARP_LUA = ROOT / "tools" / "debug" / "warp.lua"


def parse_scenes(path: Path = SCENES_LUA) -> list[dict]:
    """Parses SCENE_ORDER and SCENES metadata blocks from scenes.lua without Lua runtime."""
    text = path.read_text(encoding="utf-8")
    order_m = re.search(r"SCENE_ORDER\s*=\s*\{(.*?)\}", text, re.DOTALL)
    if not order_m:
        raise ValueError("SCENE_ORDER not found in scenes.lua")
    order = re.findall(r'"([a-z0-9_]+)"', order_m.group(1))

    scenes_idx = text.find("SCENES = {")
    if scenes_idx == -1:
        raise ValueError("SCENES table not found in scenes.lua")
    body = text[scenes_idx:]

    parsed = []
    for name in order:
        pat = re.compile(rf"^\s*{re.escape(name)}\s*=\s*\{{(.*?)^\s*\}},", re.MULTILINE | re.DOTALL)
        m = pat.search(body)
        if not m:
            raise ValueError(f"Scene {name!r} listed in SCENE_ORDER missing from SCENES")
        blk = m.group(1)

        def get_str(key: str, default: str | None = None) -> str | None:
            km = re.search(rf'\b{key}\s*=\s*"([^"]*)"', blk)
            return km.group(1) if km else default

        def get_int(key: str, default: int | None = None) -> int | None:
            km = re.search(rf"\b{key}\s*=\s*(0x[0-9A-Fa-f]+|\d+)", blk)
            return int(km.group(1), 0) if km else default

        parsed.append({
            "name": name,
            "desc": get_str("desc", ""),
            "mode": get_str("mode"),
            "frames": get_int("frames", 360),
            "shot_every": get_int("shot_every", 80),
            "route": get_str("route"),
        })
    return parsed


def run_scene(scene: dict, rom: Path, timeout: int, dry_run: bool = False) -> bool:
    name = scene["name"]
    state_out = ROOT / "work" / "states" / f"{name}.mss"
    qa_dir = ROOT / "work" / "qa" / "debug_warp" / name
    cmd = [
        sys.executable,
        "-X",
        "utf8",
        str(ROOT / "tools" / "run_emu.py"),
        str(rom),
        "--out",
        str(qa_dir),
        "--script",
        str(WARP_LUA),
        "--var",
        f"SCENE={name!r}",
        "--frames",
        str(scene["frames"]),
        "--shot-every",
        str(scene["shot_every"]),
        "--sheet",
        "--smoke",
        "--state-out",
        str(state_out),
        "--timeout",
        str(timeout),
    ]
    if scene["route"]:
        cmd.extend(["--route-str", scene["route"]])
    if dry_run:
        print("DRY-RUN:", " ".join(cmd))
        return True

    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"FAIL {name}: run_emu exited {r.returncode}", file=sys.stderr)
        return False
    log_path = qa_dir / "log.txt"
    log_text = log_path.read_text(encoding="utf-8") if log_path.is_file() else ""
    if f"WARP_OK {name}" not in log_text:
        print(f"FAIL {name}: missing 'WARP_OK {name}' in {log_path}", file=sys.stderr)
        return False
    if not state_out.is_file():
        print(f"FAIL {name}: savestate not written: {state_out}", file=sys.stderr)
        return False
    print(f"OK {name}: state={state_out.relative_to(ROOT)} sheet={(qa_dir / 'sheet.png').relative_to(ROOT)}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, default=DEFAULT_ROM, help="Target SFC ROM path")
    ap.add_argument("--scenes", nargs="*", help="Optional subset of scene names")
    ap.add_argument("--list", action="store_true", help="List available scenes and exit")
    ap.add_argument("--dry-run", action="store_true", help="Print emulator commands without executing")
    ap.add_argument("--timeout", type=int, default=120, help="Per-scene emulator timeout in seconds")
    args = ap.parse_args(argv)

    all_scenes = parse_scenes()
    if args.list:
        for s in all_scenes:
            print(f"{s['name']:18s} [{s['mode']:10s} {s['frames']:3d}f] {s['desc']}")
        return 0

    by_name = {s["name"]: s for s in all_scenes}
    if args.scenes:
        missing = [n for n in args.scenes if n not in by_name]
        if missing:
            print(f"Unknown scenes: {', '.join(missing)}", file=sys.stderr)
            return 2
        selected = [by_name[n] for n in args.scenes]
    else:
        selected = all_scenes

    if not args.dry_run and not args.rom.is_file():
        print(f"ROM not found: {args.rom}", file=sys.stderr)
        return 1

    ok = True
    for s in selected:
        if not run_scene(s, args.rom, args.timeout, args.dry_run):
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
