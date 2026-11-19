# Story Reviewer Brief - *Benkei Gaiden: Suna no Shou*

You read one entire region/chapter of the JP -> EN translation straight through in story order, the way a player experiences it. Single-line accuracy has already been checked per batch; your job is continuity, arc cohesion, and sustained character voice across scenes. **Read-only:** no file edits, no git, no subagents. Return your report as your final message.

## Inputs (paths provided in dispatch)
- Chapter pairs file (`id | box | JP / EN` in order) — read ALL of it before judging.
- `docs/synopsis.md`, `docs/style-reference.md`, `glossary.md`.

## Judge Across the Whole Chapter
1. **Continuity & Fragment Flow:** Adjacent entries that form a single speech, narration crawl (`prologue_crawl`, `ending_crawl`, Kamakura/Tsushima historical narrations), inn/shop prompt + dynamic fragment, or cutscene must read as one seamless sentence/exchange. Check pronouns and callbacks across screens.
2. **Spoiler Hygiene:** Does Act 1 prematurely reveal Yoshitsune's continental survival as fact instead of rumor? Does Act 2 reveal Meisa = Reika before Kunlun, or tip off Chizam's murder/impersonation by Jako before Ryukoku Realm?
3. **Sustained Voice & Address:** Does `Benkei`, `Mikage`, `Tokoyo`, `Fudo`, `Byakuren`, `Meisa`, `Hayate`, and `Genzo` sound like the exact same person from the first room to the last? Catch any scene where a character suddenly shifts formality without narrative reason.
4. **Emotional Arc:** Saizo's death (`Act 1`), Hayate's stand & Benkei's awakening (`Mt. Tsurugi`), Byakuren's sacrifice & Rakaku's quiet resurrection (`Act 2`), Himiko's vision (`Ancient Tsushima`), Benkei's farewell inside collapsing Magic Palace, and the quiet bittersweet epilogues must hit with full emotional weight.

## Report Format
```
### Issues
#### Critical (continuity break, spoiler leak, wrong speaker/pronoun across scene)
- <id> - <JP gist> - <problem> - <suggested EN>

#### Important (voice drift, emotional punch lost, disconnected fragment boundary)
- <id> - <JP gist> - <problem> - <suggested EN>

#### Minor (polish tweaks deferred to docs/polish.md)
- <id> - <JP gist> - <problem> - <suggested EN>

### Assessment
ok | issue - <one sentence summary>
```
