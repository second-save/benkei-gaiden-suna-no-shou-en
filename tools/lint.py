"""Deterministic English translation linter for Benkei Gaiden: Suna no Shou."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import make_font  # noqa: E402
import tbl  # noqa: E402

SCRIPT_DIR = ROOT / "script"
GLOSSARY_PATH = ROOT / "glossary.md"
WINDOWS_PATH = ROOT / "docs" / "windows.json"
WIDTHS_PATH = ROOT / "asm" / "font_en_widths.bin"
EN_TBL_PATH = ROOT / "tbl" / "en.tbl"

FREE_TOKENS = {"{nl}", "{page}"}
ONE_LINE_BOXES = {
    "equip_name",
    "item_name",
    "jutsu_name",
    "ougi_name",
    "enemy_name",
    "location_banner",
    "party_name",
    "credits_overlay_top",
    "credits_overlay_bottom",
    "prologue_crawl",
    "ending_crawl",
    "battle_cmd",
    "title_menu",
    "status_lv",
    "status_slash",
    "status_currency",
}
MULTI_WRAP_BOXES = {"dialogue", "system", "battle_msg", "equip_desc", "item_desc", "jutsu_desc"}

NARROW_ID_BOX: dict[str, str] = {
    "1D_C7A3": "title_menu",
    "1D_C7A9": "title_menu",
    "1D_C395": "status_lv",
    "1D_C3F3": "status_slash",
    "1D_D7F4": "status_slash",
    "1D_C411": "status_currency",
    "1D_C414": "status_currency",
    "1D_8178": "dialogue",
}
BATTLE_CMD_IDS = {
    "1D_C32C", "1D_C331", "1D_C336", "1D_C33B", "1D_C340",
    "1D_C427", "1D_C42C", "1D_C431", "1D_C436", "1D_C43B",
    "1D_C440", "1D_C44C", "1D_D7C7", "1D_D7CC", "1D_D7D1",
    "1D_D7D6", "1D_D7DB", "1D_D7E0", "1D_D7E5", "1D_D7EA", "1D_D7EF",
}
CREDITS_TOP_IDS = {
    "1D_F59F", "1D_F5B7", "1D_F5D9", "1D_F5FB", "1D_F60A",
    "1D_F62C", "1D_F63B", "1D_F65E", "1D_F7B9", "1D_F7DE",
}
NARRATION_GROUPS = (
    ("act2_prologue", 0x8000, 0x816C),
    ("hist_prologue", 0xAE60, 0xB07A),
    ("koan_storm", 0x9F52, 0x9FAA),
    ("epilogue_crawl", 0xA200, 0xA55D),
)


def narration_group_of(entry: dict) -> str | None:
    """Return group name for split bank $1D narration/crawl sequences."""
    eid = entry.get("id", "")
    if not eid.startswith("1D_") or not entry.get("addr"):
        return None
    addr = int(entry["addr"], 16)
    for name, lo, hi in NARRATION_GROUPS:
        if lo <= addr <= hi:
            return name
    return None

HONORIFIC_SUFFIX_RE = re.compile(r"\b[A-Za-z]{2,}-(?:san|sama|dono|kun|chan|sensei)\b", re.IGNORECASE)
ORDINAL_VAR_RE = re.compile(r"\{name[0-4]\}(?:st|nd|rd|th)\b", re.IGNORECASE)
ARTICLE_VAR_RE = re.compile(r"\b(?:a|an)\s+\{name[0-4]\}", re.IGNORECASE)


def load_widths(path: Path = WIDTHS_PATH) -> bytes:
    """Load 128-byte VWF advance widths, generating from make_font if missing."""
    if path.is_file():
        return path.read_bytes()
    _, widths = make_font.build_font_binaries()
    return widths


def load_windows(path: Path = WINDOWS_PATH) -> dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_en_table(path: Path = EN_TBL_PATH) -> tbl.Table:
    return tbl.Table.load(path)


def is_name_grid_row(entry: dict) -> bool:
    """True for the 5-column fixed-stride Name Entry picker rows in ui_bank1d_c2.json."""
    eid = entry.get("id", "")
    if not eid.startswith("1D_") or entry.get("box") not in (None, "ui"):
        return False
    addr = int(entry.get("addr", "0x0"), 16)
    return (0xC451 <= addr <= 0xC6B1) or (0xCAA8 <= addr <= 0xD7B7)


def is_kanji_picker_row(entry: dict) -> bool:
    """True for unused/secondary 210 kanji rows ($1D:CAA8..$D7B7)."""
    addr_s = entry.get("addr", "")
    if not addr_s:
        return False
    addr = int(addr_s, 16)
    return entry.get("id", "").startswith("1D_") and 0xCAA8 <= addr <= 0xD7B7


def box_spec_for(entry: dict, doc_box: str | None = None, windows: dict[str, dict] | None = None) -> tuple[str, dict]:
    """Return (effective_box_name, window_spec) for a script entry."""
    if windows is None:
        windows = load_windows()
    eid = entry["id"]
    base_box = entry.get("box") or doc_box or "dialogue"

    if eid in NARROW_ID_BOX:
        eff = NARROW_ID_BOX[eid]
    elif eid in BATTLE_CMD_IDS:
        eff = "battle_cmd"
    elif base_box == "credits_overlay":
        eff = "credits_overlay_top" if eid in CREDITS_TOP_IDS else "credits_overlay_bottom"
    else:
        eff = base_box

    spec = dict(windows[eff])
    if eff == "title_menu":
        spec["max_lines"] = 1  # each entry renders on one line of the 2-option box
    if eff in ("credits_overlay_top", "credits_overlay_bottom", "location_banner", "party_name", "battle_cmd"):
        spec["max_lines"] = 1
    return eff, spec


def _char_kind(ch: str) -> str:
    if "\u3040" <= ch <= "\u309f":
        return "hiragana"
    if "\u30a0" <= ch <= "\u30ff":
        return "katakana"
    if "\u4e00" <= ch <= "\u9fff" or ch == "々":
        return "kanji"
    return "other"


def has_term(jp: str, term: str) -> bool:
    """True when `term` appears bounded across kana/kanji script-type transitions."""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        left_ok = a == 0 or _char_kind(jp[a - 1]) != _char_kind(term[0])
        right_ok = b == len(jp) or _char_kind(jp[b]) != _char_kind(term[-1])
        if left_ok and right_ok:
            return True
    return False


def parse_glossary(path: Path = GLOSSARY_PATH) -> list[tuple[list[str], list[str], list[str]]]:
    """Parse `| JP | EN | max | notes | Avoid |` rows from glossary.md (skipping Staff Credits)."""
    rows: list[tuple[list[str], list[str], list[str]]] = []
    if not path.is_file():
        return rows
    section = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if "Staff Credits" in section or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("JP", "") or set(cells[0]) <= set("-: "):
            continue
        jps = [x.strip() for x in cells[0].split("/") if x.strip()]
        ens = [x.strip() for x in cells[1].split("/") if x.strip()]
        avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
        if jps and ens:
            rows.append((jps, ens, avoid))
    return rows


def measure_line_px(line: str, widths: bytes, fixed_char_px: int | None = None) -> int:
    """Compute exact rendered pixel width for one single line (without {nl}/{page})."""
    px = 0
    i = 0
    while i < len(line):
        m = tbl.TOKEN.match(line, i)
        if m:
            tok_name = m.group(1)
            hex_byte = m.group(3)
            if hex_byte is not None:
                val = int(hex_byte, 16)
                px += fixed_char_px if fixed_char_px else (widths[val] if val < 0x80 else 8)
            elif tok_name == "pad":
                if fixed_char_px:
                    px += fixed_char_px
                else:
                    px = ((px + 7) // 8) * 8 + 8
            elif tok_name in ("name0", "name1", "name2", "name3", "name4"):
                px += 48
            elif tok_name in ("pal0", "pal1", "wait", "nop", "end"):
                pass
            elif tok_name in ("nl", "page"):
                pass
            else:
                px += fixed_char_px if fixed_char_px else 8
            i = m.end()
            continue
        ch = line[i]
        code = ord(ch)
        if fixed_char_px:
            px += fixed_char_px
        elif 0x20 <= code <= 0x7E:
            px += widths[code]
        else:
            px += 8
        i += 1
    return px


def _tokens_for_parity(text: str, allow_pad: bool = False) -> Counter[str]:
    counts: Counter[str] = Counter()
    for m in tbl.TOKEN.finditer(text):
        full = m.group(0)
        name = m.group(1)
        if name in ("nl", "page") or (name and name.startswith("sF")):
            continue
        if allow_pad and name == "pad":
            continue
        counts[full] += 1
    return counts


def _strip_tokens_for_prose(text: str) -> str:
    return tbl.TOKEN.sub("", text)


def _check_stub_last_lines(page: str, box_name: str, width_px: int, widths: bytes) -> list[str]:
    if box_name not in MULTI_WRAP_BOXES:
        return []
    lines = page.split("{nl}")
    if len(lines) < 2:
        return []
    problems: list[str] = []
    for prev_l, cur_l in zip(lines, lines[1:]):
        prev_s = prev_l.replace("{end}", "").strip()
        cur_s = cur_l.replace("{end}", "").strip()
        if not prev_s or not cur_s or " " in cur_s:
            continue
        if len(_strip_tokens_for_prose(prev_s).split()) < 3:
            continue
        if prev_s.endswith((":", '"', ".", "!", "?", "--", "...")) or cur_s.startswith(('"', "'")):
            continue
        if ":" in cur_s:
            continue
        cur_px = measure_line_px(cur_s, widths)
        if cur_px <= 24:
            combined_px = measure_line_px(prev_s + " " + cur_s, widths)
            if combined_px <= width_px:
                problems.append(
                    f"stub last word {cur_s!r} ({cur_px}px) fits on previous line ({combined_px}<={width_px}px)"
                )
    return problems


def lint_entry(
    entry: dict,
    en: str,
    terms: list[tuple[list[str], list[str], list[str]]] | None = None,
    widths: bytes | None = None,
    en_table: tbl.Table | None = None,
    windows: dict[str, dict] | None = None,
    doc_box: str | None = None,
) -> list[str]:
    """Validate one translated entry against all mechanical, width, token, and glossary rules."""
    if not en or not en.strip():
        return ["empty English"]
    if "\t" in en or "\r" in en or "\n" in en or re.search(r"\\u[0-9a-fA-F]{4}", en):
        return ["raw tab/newline or \\uXXXX escape in English (use {nl}/{page})"]

    if widths is None:
        widths = load_widths()
    if en_table is None:
        en_table = load_en_table()
    if windows is None:
        windows = load_windows()
    if terms is None:
        terms = parse_glossary()

    out: list[str] = []
    # Reject accidental fullwidth or curly quotes before encoding
    for m in tbl.TOKEN.finditer(en):
        if m.group(3):
            out.append(f"raw hex byte {m.group(0)} in English")
    plain_no_tok = tbl.TOKEN.sub("", en)
    non_ascii = sorted({ch for ch in plain_no_tok if not (" " <= ch <= "~")})
    if non_ascii:
        out.append(f"non-ASCII characters {non_ascii}")

    encoded = b""
    try:
        encoded = en_table.encode(en)
    except ValueError as exc:
        out.append(str(exc))

    jp = entry["jp"]
    eff_box, spec = box_spec_for(entry, doc_box=doc_box, windows=windows)
    grid_row = is_name_grid_row(entry)

    # {end} parity + control-token parity (excluding credits {sF0xx} aliases)
    want_end = jp.count("{end}")
    have_end = en.count("{end}")
    if want_end != have_end:
        out.append(f"{{end}} mismatch: JP has {want_end}, EN has {have_end}")

    if not grid_row:
        allow_pad = eff_box == "battle_cmd"
        want_toks = _tokens_for_parity(jp, allow_pad=allow_pad)
        have_toks = _tokens_for_parity(en, allow_pad=allow_pad)
        if want_toks != have_toks:
            out.append(f"control codes differ: JP {dict(want_toks)} EN {dict(have_toks)}")

    if eff_box in ONE_LINE_BOXES and ("{nl}" in en or "{page}" in en):
        out.append(f"{{nl}}/{{page}} forbidden in single-line box {eff_box}")

    if ORDINAL_VAR_RE.search(en):
        out.append('ordinal suffix glued onto {nameN} variable (write "No. ..." instead)')
    if ARTICLE_VAR_RE.search(en):
        out.append("indefinite article a/an before {nameN}")
    if m_hon := HONORIFIC_SUFFIX_RE.search(en):
        out.append(f"Japanese honorific suffix retained ({m_hon.group(0)!r}); drop per D2")

    # Pixel width & line-count checks per {page}
    fixed_px = spec.get("fixed_char_px")
    width_px = spec["width_px"]
    max_lines = spec["max_lines"]
    pages = en.split("{page}")
    for p_idx, page in enumerate(pages, 1):
        lines = page.split("{nl}")
        if len(lines) > max_lines:
            out.append(f"page {p_idx}: {len(lines)} lines > max {max_lines} ({eff_box})")
        for l_idx, line in enumerate(lines, 1):
            px = measure_line_px(line, widths, fixed_char_px=fixed_px)
            if px > width_px:
                out.append(f"page {p_idx} line {l_idx}: {px}px > {width_px}px ({eff_box})")
        if not grid_row:
            out.extend(_check_stub_last_lines(page, eff_box, width_px, widths))

    # Name-entry grid rows must preserve exact 16-byte record length (15 + $FF)
    if grid_row and encoded and len(encoded) != 16:
        out.append(f"name entry row must encode to 16 bytes (got {len(encoded)})")

    # Glossary & Avoid checks (split narration sequences validate positive glossary terms across their whole group)
    grp_name = narration_group_of(entry)
    if not grid_row and not entry["id"].startswith("1D_F5") and not entry["id"].startswith("1D_F6") and not entry["id"].startswith("1D_F7"):
        jp_plain = tbl.TOKEN.sub("", jp)
        for jps, ens, avoid in terms:
            if any("{" in j for j in jps):
                continue
            if grp_name is None and any(has_term(jp_plain, j) for j in jps) and not any(e.lower() in en.lower() for e in ens):
                out.append(f"glossary: {jps[0]} -> {ens[0]}")
            for a in avoid:
                if re.search(rf"\b{re.escape(a)}\b", en):
                    out.append(f"glossary Avoid: {a}")

    return out


def check_narration_groups(
    items: list[tuple[dict, str]],
    terms: list[tuple[list[str], list[str], list[str]]] | None = None,
) -> list[str]:
    """Validate glossary terms across concatenated split narration/crawl sequences."""
    if terms is None:
        terms = parse_glossary()
    grouped: dict[str, list[tuple[dict, str]]] = {}
    for entry, en in items:
        g = narration_group_of(entry)
        if g and en:
            grouped.setdefault(g, []).append((entry, en))
    errs: list[str] = []
    for g, pairs in grouped.items():
        jp_cat = "".join(tbl.TOKEN.sub("", e["jp"]) for e, _ in pairs)
        en_cat = " ".join(tbl.TOKEN.sub(" ", en) for _, en in pairs)
        for jps, ens, _ in terms:
            if any("{" in j for j in jps):
                continue
            if any(has_term(jp_cat, j) for j in jps) and not any(e.lower() in en_cat.lower() for e in ens):
                errs.append(f"group[{g}]: glossary {jps[0]} -> {ens[0]}")
    return errs


def lint_all(script_dir: Path = SCRIPT_DIR) -> list[str]:
    """Validate all non-empty `en` entries across script/*.json."""
    widths = load_widths()
    en_table = load_en_table()
    windows = load_windows()
    terms = parse_glossary()
    errors: list[str] = []
    seen_items: list[tuple[dict, str]] = []
    for p in sorted(script_dir.glob("*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        doc_box = doc.get("box")
        for e in doc["entries"]:
            en = e.get("en", "")
            if not en:
                continue
            seen_items.append((e, en))
            probs = lint_entry(
                e,
                en,
                terms=terms,
                widths=widths,
                en_table=en_table,
                windows=windows,
                doc_box=doc_box,
            )
            for prob in probs:
                errors.append(f"{e['id']}: {prob}: {en!r}")
    errors.extend(check_narration_groups(seen_items, terms=terms))
    return errors


def main(argv: list[str] | None = None) -> int:
    errs = lint_all()
    if errs:
        for line in errs[:200]:
            print(line)
        print(f"lint failed: {len(errs)} problems")
        return 1
    print("lint ok: 0 problems")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
