# Translation & Visual QA Polish Log — Benkei Gaiden: Suna no Shou (SNES)

Track non-blocking minor items, cross-file proper-noun checks during Wave 2 dialogue, and live in-game MesenCE checks for Phase 7. Clear every `[ ]` item to `[x]` before Phase 9 release.

## Wave 1a / Engine & Battle Checks
- [ ] Verify Sound Test (`MUSIC` password on Name Entry) box width, track centering (`1D_C7EF..1D_CA9E`), and `"Ka -- Heart of the Land"` (`1D_C8DF`) right-border fit in MesenCE.
- [ ] Verify Settings menu column spacing (`1D_C705..1D_C72A`: `Ultra`/`Fast`/`Mid`/`Slow`/`Crawl`, `Active`/`Text`, `Stereo`/`Mono`, `Backdrop`) in MesenCE; widen or rename `Mid` -> `Normal` if spacing allows.
- [ ] Verify Status screen column alignment (`1D_C3E0` `Lv HP MP` header vs numeric HP/MP columns; `1D_C417..1D_C423` `Weapon:`/`Armor:`/`Helm:`/`Shield:` spacing against equipped item names).
- [ ] Verify live Battle messages after Bank `$0C` `$20` particle patch: damage dealt/taken (`1D_AC33`/`1D_AC3A`/`1D_AC3F`), HP & MP recovery items/jutsu (`1D_AC95` check if MP items also call `$0C:AA58`), battle item use (`1D_AD0B` via `$0C:A635`), status effects (`1D_ACA3`/`1D_ACBF`), parry (`1D_AC86`), jutsu reflect (`1D_AD34`), and `tbl_jutsu_031` (`Call Ally`).
- [ ] Cross-check event callers of `1D_ACC8` (`08:BC4A`, `1E:CA68`, `2E:AF5E`) during Wave 2 dialogue translation to confirm transitive vs passive phrasing (`defeated <target>` vs ` was defeated!`).
- [ ] Cross-check `tbl_locations_016` (`近江守護` `Omi Guardpost` vs `Omi Governor's Estate`) against Act 1 dialogue mentions in `act1_bank1b.json`. (`tbl_locations_044` `虚虫洞` verified canon `こちゅうどう` in `1B_82A9` -> `Kochudo Cavern`.)
- [ ] Cross-check `tbl_locations_100, 104, 105, 106` (`Magic Palace/... Realm`) banner fit in Phase 7 QA.
- [ ] Check debug `1D_C770` (` 0 1 2 3 4 5 6 7`) / `1D_C7C5` (`Male`/`Female`) UI alignment if triggered.

## Wave 1b Checks (Descriptions)
- [ ] Check 4th equipment slot label `防：` (`1D_C423` / `1D_D830`): currently `Shield:`, whereas all `tbl_equip_192..210` items in that slot are gauntlets, bangles, bracers, charms, or wards (`Guard:` / `Ward:` / `Accessory:` may fit better once Status/Equip screens are visually inspected).
- [ ] Verify `MP: <N>` column alignment (`144..147px`) inside the Jutsu description box in MesenCE, and verify in-game slot usage for `tbl_jutsu_desc_033` (`こざん` `Mirage`), `043` (`かほそく` `Fleetfoot`), `044` (`くとけ` `Detox`) vs `tbl_jutsu_033` (`Fleetfoot`).
- [ ] Verify Equip description window rendering for `tbl_equip_desc_037` (unawakened `Vajra Blade Kiryu` 2-line prose without stat line) and `tbl_equip_desc_043..049` (single-line `War Demon ...` entries).
