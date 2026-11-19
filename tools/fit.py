"""Pixel-accurate English line wrapper & width inspector for Benkei Gaiden: Suna no Shou."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import lint  # noqa: E402


def wrap_page(text: str, width_px: int, widths: bytes, fixed_char_px: int | None = None) -> list[str]:
    """Word-wrap a single paragraph cleanly without exceeding `width_px`."""
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    cur = words[0]
    for w in words[1:]:
        cand = cur + " " + w
        if lint.measure_line_px(cand, widths, fixed_char_px=fixed_char_px) <= width_px:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def format_box(text: str, box: str = "dialogue") -> str:
    """Wrap `text` into `{nl}` / `{page}` chunks matching docs/windows.json box limits."""
    windows = lint.load_windows()
    if box not in windows:
        raise ValueError(f"Unknown box {box!r}")
    spec = windows[box]
    width_px = spec["width_px"]
    max_lines = spec["max_lines"]
    fixed_px = spec.get("fixed_char_px")
    widths = lint.load_widths()

    has_end = text.endswith("{end}")
    body = text[:-5] if has_end else text
    raw_pages = body.split("{page}")
    out_pages: list[str] = []
    for raw_p in raw_pages:
        wrapped: list[str] = []
        for manual_line in raw_p.split("{nl}"):
            wrapped.extend(wrap_page(manual_line, width_px, widths, fixed_char_px=fixed_px))
        for i in range(0, len(wrapped), max_lines):
            out_pages.append("{nl}".join(wrapped[i : i + max_lines]))
    return "{page}".join(out_pages) + ("{end}" if has_end else "")


def check_tsv(path: Path) -> int:
    """Check an out.tsv file against box widths and print per-line diagnostics."""
    import batches

    entries = batches.index()
    widths = lint.load_widths()
    windows = lint.load_windows()
    bad = 0
    for row in batches.read_tsv(path):
        eid = row[0]
        en = "\t".join(row[1:])
        e = entries.get(eid)
        if not e:
            print(f"{eid}: unknown id")
            bad += 1
            continue
        eff_box, spec = lint.box_spec_for(e, windows=windows)
        for p_idx, page in enumerate(en.split("{page}"), 1):
            lines = page.split("{nl}")
            if len(lines) > spec["max_lines"]:
                print(f"{eid} [{eff_box}] p{p_idx}: {len(lines)} lines > {spec['max_lines']}")
                bad += 1
            for l_idx, line in enumerate(lines, 1):
                px = lint.measure_line_px(line, widths, fixed_char_px=spec.get("fixed_char_px"))
                if px > spec["width_px"]:
                    print(f"{eid} [{eff_box}] p{p_idx}:L{l_idx}: {px}px > {spec['width_px']}px | {line}")
                    bad += 1
    if bad == 0:
        print(f"{path}: all lines fit pixel budgets")
    return 1 if bad else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--box", default="dialogue", help="Window box key from docs/windows.json")
    ap.add_argument("--tsv", type=Path, help="Check pixel widths for a batch .out.tsv")
    ap.add_argument("text", nargs="?", help="English string to wrap & measure")
    args = ap.parse_args(argv)

    if args.tsv:
        return check_tsv(args.tsv)
    if args.text is None:
        ap.error("provide either --tsv <path> or text to wrap")
    wrapped = format_box(args.text, box=args.box)
    widths = lint.load_widths()
    spec = lint.load_windows()[args.box]
    print(wrapped)
    for p_idx, page in enumerate(wrapped.split("{page}"), 1):
        for l_idx, line in enumerate(page.split("{nl}"), 1):
            px = lint.measure_line_px(line, widths, fixed_char_px=spec.get("fixed_char_px"))
            print(f"  p{p_idx} L{l_idx}: {px:3d}/{spec['width_px']}px | {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
