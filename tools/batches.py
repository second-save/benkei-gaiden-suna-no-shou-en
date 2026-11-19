"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500] [--files f1.json ...]
    python -X utf8 tools/batches.py check [bNNN ...]
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]

Adapted from translate-retro-game assets/batches.py for Benkei Gaiden: Suna no Shou.
Batch TSV: id, speaker, box, limit, jp. Output: work/tl/bNNN.out.tsv (id<TAB>en).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import lint  # noqa: E402
import tbl  # noqa: E402

TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

NARRATION_GROUPS = lint.NARRATION_GROUPS


def docs(only_files: set[str] | None = None):
    """Yield (path, doc, entries) per script file."""
    for path in sorted(SCRIPT.rglob("*.json")):
        if only_files and path.name not in only_files:
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc["entries"] if isinstance(doc, dict) else doc


def needs_english(entry: dict) -> bool:
    """True for active translatable entries with empty `en` (excludes empty/data/kanji-picker)."""
    if entry.get("status") in ("empty", "data"):
        return False
    if lint.is_kanji_picker_row(entry):
        return False
    return bool(entry.get("jp")) and not entry.get("en")


def group_of(entry: dict, doc_name: str = "") -> str:
    """Entries with the same key stay together in one batch."""
    if entry.get("dup"):
        return entry["dup"]
    eid = entry["id"]
    if eid.startswith("1D_") and entry.get("addr"):
        addr = int(entry["addr"], 16)
        for key, lo, hi in NARRATION_GROUPS:
            if lo <= addr <= hi:
                return f"grp_{key}"
    # Keep sys_bank1d_a8 fragments together in small coherent chunks by address range
    if doc_name == "sys_bank1d_a8.json" and entry.get("addr"):
        addr = int(entry["addr"], 16)
        if 0xA970 <= addr <= 0xAB7E:
            return "grp_sys_fragments"
    return eid


def speaker_of(entry: dict) -> str:
    if entry.get("speaker"):
        return entry["speaker"]
    m = re.match(r"^(?:\{page\}|\{nl\}|\s)*([^\s「」『』\{]{1,12})「", entry.get("jp", ""))
    return m.group(1) if m else ""


def limit_label(entry: dict, doc_box: str | None = None, windows: dict | None = None) -> str:
    eff, spec = lint.box_spec_for(entry, doc_box=doc_box, windows=windows)
    if spec.get("fixed_char_px"):
        chars = spec["width_px"] // spec["fixed_char_px"]
        return f"{chars}ch"
    if spec["max_lines"] == 1:
        return f"{spec['width_px']}px"
    return f"{spec['width_px']}px x{spec['max_lines']}"


def glossary(path: Path = GLOSSARY):
    return lint.parse_glossary(path)


def problems(
    entry: dict,
    en: str,
    terms,
    widths: bytes | None = None,
    en_table: tbl.Table | None = None,
    windows: dict | None = None,
) -> list[str]:
    return lint.lint_entry(
        entry,
        en,
        terms=terms,
        widths=widths,
        en_table=en_table,
        windows=windows,
    )


def index() -> dict[str, dict]:
    return {e["id"]: e for _, _, entries in docs() for e in entries}


def read_tsv(path: Path) -> list[list[str]]:
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing() -> list[Path]:
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def split(size: int, only_files: set[str] | None = None) -> None:
    """Number from the last batch and skip IDs already in existing bNNN.tsv files."""
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    windows = lint.load_windows()
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    groups: dict[str, list[tuple[dict, str | None]]] = {}
    for path, doc, entries in docs(only_files):
        doc_box = doc.get("box") if isinstance(doc, dict) else None
        for e in entries:
            if needs_english(e) and e["id"] not in taken:
                groups.setdefault(group_of(e, path.name), []).append((e, doc_box))

    batches: list[list[tuple[dict, str | None]]] = []
    cur: list[tuple[dict, str | None]] = []
    chars = 0
    for group in groups.values():
        c = sum(len(tbl.TOKEN.sub("", e["jp"])) for e, _ in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
            batches.append(cur)
            cur, chars = [], 0
        cur.extend(group)
        chars += c
    if cur:
        batches.append(cur)

    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = []
        for e, doc_box in batch:
            eff_box, _ = lint.box_spec_for(e, doc_box=doc_box, windows=windows)
            rows.append(
                f"{e['id']}\t{speaker_of(e)}\t{eff_box}\t{limit_label(e, doc_box, windows)}\t{e['jp']}"
            )
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(tbl.TOKEN.sub("", e["jp"]) for e, _ in batch)
        used = [(j, ens[0]) for jpl, ens, _ in terms for j in jpl if "{" not in j and lint.has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text(
            "".join(f"{j}\t{e}\n" for j, e in used) or "(no glossary terms in this batch)\n",
            encoding="utf-8",
            newline="\n",
        )
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch: str, entries: dict[str, dict], terms) -> tuple[list[str], dict[str, str]]:
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    out_path = TL / f"{batch}.out.tsv"
    if not out_path.is_file():
        return [f"missing output file {out_path}"], {}
    rows = [(r[0], "\t".join(r[1:])) for r in read_tsv(out_path)]
    bad: list[str] = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(
            f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
            f"duplicate {dup[:8]} (order must match too)"
        )
    widths = lint.load_widths()
    en_table = lint.load_en_table()
    windows = lint.load_windows()
    for eid, en in rows:
        if eid in entries:
            bad.extend(
                f"{eid}: {p}: {en!r}"
                for p in problems(entries[eid], en, terms, widths=widths, en_table=en_table, windows=windows)
            )
    bad.extend(lint.check_narration_groups([(entries[eid], en) for eid, en in rows if eid in entries], terms=terms))
    return bad, dict(rows)


def merge(new: dict[str, str], overwrite: bool) -> None:
    """Refuse to replace existing different English unless `--overwrite` is passed."""
    if not overwrite:
        for _, _, entries in docs():
            for e in entries:
                if e["id"] in new and e.get("en") and e["en"] != new[e["id"]]:
                    sys.exit(f"{e['id']} would lose {e['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for path, doc, entries in docs():
        touched = False
        for e in entries:
            if e["id"] in new and e.get("en") != new[e["id"]]:
                e["en"], e["status"] = new[e["id"]], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def main(argv: list[str]) -> int:
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        size = int(args[args.index("--size") + 1]) if "--size" in args else 3500
        only: set[str] | None = None
        if "--files" in args:
            fi = args.index("--files") + 1
            only = set()
            for a in args[fi:]:
                if a.startswith("--"):
                    break
                only.add(Path(a).name)
        split(size, only_files=only)
        return 0
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        widths = lint.load_widths()
        en_table = lint.load_en_table()
        windows = lint.load_windows()
        bad = [
            f"{i}: {p}: {e['en']!r}"
            for i, e in entries.items()
            if e.get("en")
            for p in problems(e, e["en"], terms, widths=widths, en_table=en_table, windows=windows)
        ]
        bad.extend(
            lint.check_narration_groups(
                [(e, e["en"]) for e in entries.values() if e.get("en")],
                terms=terms,
            )
        )
        print(f"{len(entries)} entries, {len(bad)} problems")
        if bad:
            print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    new, failed = {}, 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        new.update(rows)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
    if failed:
        return 1
    if cmd == "merge":
        merge(new, overwrite)
    return 0


def _selftest() -> None:
    import tempfile

    global ROOT, TL, SCRIPT, GLOSSARY
    saved = (ROOT, TL, SCRIPT, GLOSSARY)
    try:
        with tempfile.TemporaryDirectory() as d:
            ROOT = Path(d)
            TL, SCRIPT, GLOSSARY = ROOT / "work/tl", ROOT / "script", ROOT / "glossary.md"
            SCRIPT.mkdir()
            GLOSSARY.write_text(
                "| JP | EN | max | notes | Avoid |\n|---|---|---|---|---|\n| 才蔵 | Saizo | | | Saizou |\n",
                encoding="utf-8",
            )
            doc = {
                "file": "test.json",
                "box": "dialogue",
                "entries": [
                    {"id": "a", "jp": "才蔵が来た{end}", "en": "", "box": "dialogue", "status": "todo"},
                    {"id": "b", "jp": "待機{end}", "en": "", "box": "dialogue", "status": "todo"},
                    {"id": "c", "jp": "", "en": "", "box": "dialogue", "status": "empty"},
                    {"id": "d", "jp": "{name0}の番{end}", "en": "", "box": "dialogue", "status": "todo"},
                ],
            }
            (SCRIPT / "s.json").write_text(json.dumps(doc), encoding="utf-8")
            assert main(["split"]) == 0
            assert [r[0] for r in read_tsv(TL / "b001.tsv")] == ["a", "b", "d"]
            assert "才蔵\tSaizo" in (ROOT / "build/terms_b001.txt").read_text(encoding="utf-8")
            split(3500)
            assert len(existing()) == 1

            out = TL / "b001.out.tsv"
            out.write_text("a\tHe came{end}\nb\tWait{end}\n", encoding="utf-8")
            assert main(["check", "b001"]) == 1  # missing d, missing Saizo
            out.write_text("a\tSaizo came{end}\nb\tWait{end}\nd\t{name0}th turn{end}\n", encoding="utf-8")
            assert main(["merge", "b001"]) == 1  # ordinal glued onto {name0}
            assert index()["a"]["en"] == ""
            out.write_text("a\tSaizou and Saizo{end}\nb\tWait{end}\nd\tTurn No. 1 for {name0}{end}\n", encoding="utf-8")
            assert main(["check", "b001"]) == 1  # Avoid spelling
            out.write_text("a\tSaizo arrived.{end}\nb\tStand by.{end}\nd\tNow it is {name0} up next.{end}\n", encoding="utf-8")
            assert main(["merge", "b001"]) == 0 and index()["b"]["en"] == "Stand by.{end}"
            assert main(["check"]) == 0
            out.write_text("a\tSaizo showed up.{end}\nb\tStand by.{end}\nd\tNow it is {name0} up next.{end}\n", encoding="utf-8")
            try:
                main(["merge", "b001"])
                raise AssertionError("merge replaced English without --overwrite")
            except SystemExit:
                pass
            assert main(["merge", "b001", "--overwrite"]) == 0 and index()["a"]["en"] == "Saizo showed up.{end}"
    finally:
        ROOT, TL, SCRIPT, GLOSSARY = saved
    print("selftest ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        _selftest()
    else:
        sys.exit(main(sys.argv[1:]))
