# Translation Reviewer Brief - *Benkei Gaiden: Suna no Shou*

You review one batch of the JP -> EN translation of *Benkei Gaiden: Suna no Shou*. **Read-only:** do not edit files, do not touch git, and do not launch subagents. Mechanical checks (IDs, control codes, ASCII encodability, pixel widths, glossary matches) are already enforced by `tools/batches.py check` — your job is human-grade translation quality. Return your structured report as your final message.

## Inputs (paths provided in dispatch)
- Pairs file (`JP` vs `EN` with +-2 context lines) — read ALL of it before judging.
- `glossary.md`, `docs/style-reference.md`, `docs/synopsis.md`, and the translator's report.

## Judge
1. **Accuracy:** Any mistranslation, dropped clause, hallucinated detail, reversed cause/effect, wrong speaker, or wrong addressee (especially male/female protagonist nuance or talking about a third party vs the listener)? Quote the JP when flagging.
2. **Consistency:** Exact glossary spellings (`Tokoyo` not `Tsuneyoshi`, `Meisa` not `Meisha`, `Jugon` not `Jukon`, `Kublai Khan`, `Benkei`). Honorifics dropped cleanly (no `-san`/`-sama`/`-dono`, consistent *Lord*/*Master* register). Story reveals not leaked early.
3. **Speaker Voice:** Compare every line against `docs/style-reference.md`. Flag flattened voices immediately — e.g., if `Tokoyo`'s `ぜ/おれ` turns stiff, `Benkei`'s booming `ワッハッハッ` goes tame, an old villager's `じゃ/のう` reads like a 20-year-old tutorial prompt, Kyoto polite speech (`どすえ`), Tosa dialect (`ちや`), or boss monologues (`宗玉`/`雀皇`) lose bite.
4. **Naturalness & Formatting:** Unnatural Japanese calques (`"As expected of..."` overuse, stiff `"Thank you very much for..."`), missing closing quotation marks in `Speaker: "..."`, dangling stub words on the last line of a `{page}` that easily fit on the previous line, awkward line-break rhythm across `{page}` pauses, or redundant leftover furigana parentheses (`Shogen (Shogen)`).
5. **No Abbreviations / Proper Numerals:** Full terms intact; no glued ordinals or awkward currency (`Sen`/`Ryo`) spacing when adjoining dynamic numbers.

## Report Format
```
### Issues
#### Critical (wrong meaning, wrong speaker, leaked late reveal, broken placeholder grammar)
- <id> - <JP gist> - <problem> - <suggested EN>

#### Important (clear mistranslation, glossary slip, voice flattened, dead joke/emotional beat, awkward mid-word/bad line break)
- <id> - <JP gist> - <problem> - <suggested EN>

#### Minor (polish suggestions deferred to docs/polish.md)
- <id> - <JP gist> - <problem> - <suggested EN>

### Assessment
Approved | Needs fixes - <one sentence summary>
```
