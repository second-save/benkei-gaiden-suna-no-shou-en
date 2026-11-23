# Translator Brief - *Benkei Gaiden: Suna no Shou* (SNES, 1992)

You are translating a slice of the Japanese RPG *Benkei Gaiden: Suna no Shou* (*Chapter of the Sands*) into natural, evocative English for a historical/archival fan translation. Dark-fantasy feudal Japan and Silk Road China RPG following the orphan mystic Fudo and the awakened warrior-monk Benkei against Kublai Khan's occult sects.
Work ONLY on the batches assigned in your dispatch, one at a time in the order given, checking each to a clean pass before starting the next. Do all translation yourself; do not invoke subagents.

## Read First
1. `docs/style-reference.md` — voice table, speaker formatting, and approved JP/EN pilot pairs. Match this register.
2. `build/terms_<batch>.txt` — binding glossary entries matched in your batch (full table lives in `glossary.md`).
3. `docs/synopsis.md` — full story arc and spoiler guardrails. Do NOT spoil late reveals early.

## Input Format: `work/tl/<batch>.tsv`
Columns: `id<TAB>speaker<TAB>box<TAB>limit<TAB>jp`
- Entries appear in story order within each file — read neighboring lines for speaker and scene context!
- `box` tells you where the text displays and which pixel/line budget applies:
  - `dialogue`, `system`, `battle_msg`, `equip_desc`, `jutsu_desc`: **192 px** wide × **3 lines** per `{page}` (`tools/lint.py` enforces every line).
  - `item_desc`: **192 px** wide × **2 lines** per `{page}`.
  - `prologue_crawl`, `ending_crawl`: **208 px** wide × **1 line** (`{nl}` and `{page}` forbidden).
  - `equip_name`, `item_name`, `jutsu_name`, `ougi_name`: **96 px** wide × **1 line** (2-column list).
  - `enemy_name`: **120 px** wide × **1 line** (drop the Japanese `（ふりがな）` furigana completely!).
  - `location_banner`: **224 px** safe (**28 chars** max at fixed 8 px/char, max **256 px / 32 chars**).
  - Narrow UI slots (`title_menu` `48px`, `battle_cmd` `40px`, `party_name` `48px`, `status_lv` `24px`, `status_slash` `8px`, `status_currency` `16px`, `credits_overlay_top` `12ch`, `credits_overlay_bottom` `20ch`) are pre-flagged in `limit`.

## Output Format: `work/tl/<batch>.out.tsv`
Write with your file-write tool (`write_file`), NEVER shell heredocs or `python -c`:
- Format: `id<TAB>English`, every input `id` **once**, in the **exact same order**.
- **ASCII only:** straight quotes `'..."`, hyphens `--` or `-`, three periods `...` (no curly quotes, em-dashes, fullwidth Japanese chars, `\t`, or `\uXXXX`).
- **Speaker & Dialogue format:** When Japanese begins with `名前「...` (note JP omits closing `」`!), render as `Name: "..."` (e.g., `Hayate: "Master Saizo, it has been too long."`). When an unnamed speaker has no `Name「` prefix in JP, do NOT invent a speaker name — write plain spoken dialogue in quotes `"..."` (or plain narration if it's narrator/system prose). Multi-speaker dialogue in one entry: use `{page}` between speakers or explicit `{nl}` if short and dramatic as in JP.
- **Line breaks (`{nl}` / `{page}`):** Pre-wrap every multi-line box explicitly with `{nl}` and `{page}` so NO line exceeds `192 px` and NO `{page}` exceeds `max_lines` (the hardware auto-wrap breaks mid-word!). Use `python3 -X utf8 tools/fit.py --box dialogue "text"` if unsure of pixel widths! Wait: remember each `{name0..4}` reserves **48 px** worst-case width.

## Validate
From the repository root:
```
python3 -X utf8 tools/batches.py check <batch>
```
Fix every reported line until it prints `OK`.

## Style & Rulings
- **Faithful, not stiff:** Preserve all facts and emotional beats; adapt idioms naturally without padding or omitting. Keep punchy comic/battle beats sharp.
- **Keep voices audible:** Match `docs/style-reference.md`:
  - Elders (`じゃ/のう/わし`) sound aged and weathered (`"eh?"`, `"mind you"`, `"old bones"`).
  - Tokoyo (`ぜ/ねえ/おれ`) sounds fiery and brash (`"ain't"`, `"dammit"`, `"c'mon"`).
  - Benkei (`おれさま/ワッハッハッ`) sounds booming, fearless, warm (`"Hah! Leave it to me!"`, `"Bwahaha!"`).
  - Hayate / Mikage / Shogen / Himiko / Kublai Khan retain their distinct formal/courtly/stately cadences.
  - Villains (`呪魂`, `雀皇`, `宗玉`) sound imperious, sneering, or eerie — never bland NPC prose.
- **Honorifics (D2):** Drop Japanese suffixes (`-san`, `-sama`, `-dono`, `-kun`, `-chan`); render titles naturally (*Lord*, *Lady*, *Master*, *Elder*) when social rank calls for it.
- **No Abbreviations (D5):** Write full words (`Spirit Crystal Ring`, `Yamataikoku`, `Storm-Calling Rite`).
- **Placeholders:** Copy `{end}`, `{name0}`..`{name4}`, `{pal0}`, `{pal1}`, `{wait:XX}`, `{nop:XX}` identically to JP. Never write ordinal suffixes (`1st/2nd`) right onto `{nameN}`, never put `a`/`an` directly before `{nameN}`, and never write literal `[XX]` or `{word}` in English prose.

## Consistency
Never edit `glossary.md`. Report new recurring names/terms in your final message.

## Report (reply concisely)
1. File written and exact entry count (`N/N OK via batches.py check <batch>`).
2. Any lines flagged:
   - `NEW TERM: <jp> -> <en>`
   - `UNSURE: <id> - <note>`
   - `LONG: <id> - <note>` (only if unable to fit cleanly without splitting/relocating)
