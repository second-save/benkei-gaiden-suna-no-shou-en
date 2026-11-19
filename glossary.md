# Glossary - Benkei Gaiden: Suna no Shou

Binding for every translator and reviewer. Agents propose additions in reports; only the controller edits this file.

## Rulings (see docs/decisions.md)
- Honorifics: Dropped; adapt naturally into English feudal titles (e.g., Lord, Lady, Master). Name order: natural English / historical convention.
- Romanization: Standard Hepburn / established English historical spellings for real figures (e.g., Benkei, Yoshitsune).
- Credits: Translate into English (see Staff section below).
- Register / flavor: Feudal Japanese dark-fantasy RPG tone; match character speech registers naturally. Sound effects: `*Slam!*` etc.
- Abbreviations: None by default — full names and terms everywhere, using engine work (VWF, relocation, extra pages) rather than truncation.

## Style rules
- Punctuation map: 「」 -> `"..."`, 『』 -> `'...'`, ・・・ / ．．． -> `...`, ！？ -> `!?`, ！！ -> `!!`, `—` / `ー` -> `--`, fullwidth `　` -> preserve leading `{pad}` only where cursor alignment requires it; use `Speaker: "..."` format for named spoken dialogue (`Hayate: "Master Saizo..."`).
- Drop inline furigana glosses meant for Japanese children (e.g., `邵元（しょうげん）` -> `Shogen`, `崑崙（コンロン）` -> `Kunlun`, `{name3}（びゃくれん）` -> `{name3}`).
- Never glue ordinal suffixes onto runtime number variables (use `No. 1`, `#1`, etc.) and never put `a`/`an` immediately before `{name0}`..`{name4}`.
- Avoid literal `{word}` or `[XX]` (two hex digits in brackets) in English prose — `tbl.Table` parses those as control codes/hex bytes.

## Context-sensitive terms (handled by translators/reviewers by context, not blind string match)
- `沙`: **Suna** for the bloodline/clan (`"those of the Suna bloodline"`, `"Suna's legacy"`), or **the Sands** / **Sand** when used symbolically in karma/ending lines (`"the karma of the Sands"`). Chapter subtitle `沙の章` = *Chapter of the Sands* / *Suna no Shou*.
- `忍`: **Shinobu** when naming the Kasumi kunoichi; otherwise normal verb *endure* or *stealth/shinobi*.
- `元`: **the Yuan** / **Yuan Dynasty** when referring to Kublai Khan's empire; otherwise normal meaning (*origin*, *former*, etc.).
- `銭`: **Sen** (Act 1 Japanese bronze currency; `16 px` status unit).
- `銀` / `両`: **Ryo** (Act 2 Chinese silver currency; 1 silver Ryo = 20 Sen; `16 px` status unit).

## Characters
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 不動 | Fudo | 48px | Protagonist (party_0, male or female) | Fudou |
| 巳陰 / 巳影 | Mikage | 48px | Calm Renbukan jutsu adept (party_1) | |
| 常由 | Tokoyo | 48px | Renbukan swordsman (party_2; canon reading とこよ) | Tsuneyoshi / Joyu |
| 白蓮 | Byakuren | 48px | Changsha boy who joins in Act 2 (party_3) | |
| 鳴沙 | Meisa | 48px | Amnesiac Kunlun envoy (party_4; canon reading めいさ) | Meisha |
| 武蔵坊弁慶 | Musashibo Benkei | | Awakened War Demon hero | |
| 弁慶 | Benkei | | Short reference after introduction | |
| 源義経 | Minamoto no Yoshitsune | | Historical warrior & legend | |
| 義経 | Yoshitsune | | Short reference | |
| 北条時宗 | Hojo Tokimune | | Kamakura shogunal regent | |
| 時宗 | Tokimune | | Short reference | |
| フビライ・カン | Kublai Khan | | Grand Khan / Yuan Emperor | Khubilai / Hubilai |
| ジンギス・カン | Genghis Khan | | Grandfather of Kublai Khan | Genghiz / Chinggis |
| 卑弥呼 | Himiko | | Ancient Queen of Yamataikoku | |
| 才蔵 | Saizo | | Fudo's adoptive master at Shumon Fort | Saizou |
| ハヤテ | Hayate | | Warrior of the Tendo Clan | |
| 邵元 | Shogen | | Sado monk & mystic scholar | Shougen |
| 玄三 | Genzo | | Head of the Kasumi Clan | Genzou |
| 飛影 | Hiei | | Kasumi deputy commander | |
| 影丸 | Kagemaru | | Kasumi deputy commander | |
| 緒方義之 | Yoshiyuki Ogata | | Lord of Tanabe | |
| 義之 | Yoshiyuki | | Short reference | |
| 宮緒 | Miyao | | Dewa Sanzan Elder | |
| 孫ベエ | Magobee | | Blacksmith / artisan | |
| 二海堂春次 | Harutsugu Nikaido | | Act 1 antagonist | |
| 春次 | Harutsugu | | Short reference | |
| 麗花 | Reika | | Meisa's true Dunhuang name (do NOT spoil early) | |
| 恒沙 | Gosha | | Queen Mother of the West at Kunlun | Kousha |
| チザム | Chizam | | Dadu/Dunhuang ally (impersonated by Jako late) | Chizamu |
| バヤン | Bayan | | Mongol commander | |
| 円上 | Enjo | | Act 1 antagonist/monk | |
| 兵馬 | Hyoma | | Allied fighter | |
| 宗忠 | Munetada | | Allied lord / retainer | |
| マヤコ | Mayako | | NPC character | |
| 四界皇帝 | Emperor of the Four Realms | | Final overlord sealed beneath Magic Palace | Four Worlds Emperor |
| 四界将 | Four Realm Generals / Four Realm General | | Four commanders of the Curse Realm Sect | Four Worlds Generals |
| 呪魂 | Jugon | | General of the Curse Realm (canon reading ジュゴン) | Jukon |
| 武克 | Bukoku | | General of the Demon-Beast Realm | |
| 雀皇 | Jako | | General of the Illusion Realm | Jakou |
| 宗玉 | Sogyoku | | General of the Ryukoku Realm | Sougyoku |
| 羅観 | Rakan | | Early Suna antagonist at Happo Outer Array | |
| 羅覚 | Rakaku | | Enigmatic Suna figure allied with the enemy | |
| 覚樹 | Kakuju | | Antagonist boss | |
| 士牙羅鬼 | Shigaraki | | Antagonist boss | |
| 青鳳 | Seiho | | Antagonist boss | Seihou |
| 狂舞 | Kyobu | | Antagonist boss | Kyoubu |
| 死狂舞 | Shikyobu | | Undead Kyobu | Shikyoubu |
| 守慶法師 | Master Jukei / Jukei | | Fallen master / boss | |
| 李 大観 | Li Daiguan | | Continental boss | |
| 西蘭 | Seiran | | Continental boss | |
| 仙明 | Senmei | | Continental boss | |

## Staff Credits (8x32 chapter cards: top role <= 12 chars, bottom name <= 20 chars)
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 制作 | PRODUCER | 12ch | Credits top card | |
| 演出 | DIRECTOR | 12ch | Credits top card | |
| 美術 | ART | 12ch | Credits top card | |
| 作曲 | COMPOSER | 12ch | Credits top card | |
| 題字 | CALLIGRAPHY | 12ch | Credits top card | |
| 協力 | SPECIAL | 12ch | Paired on credits flow (`SPECIAL` / `THANKS` or `THANKS`) | |
| 脚本 | SCENARIO | 12ch | Credits top card | |
| 進行 | COORDINATOR | 12ch | Credits top card | |
| 酒{sF079} 敦史 | Atsushi Sakai | 20ch | Producer | |
| 籏野  篤 | Atsushi Hatano | 20ch | Producer | |
| 東  祐{sF0BA} | Yusuke Azuma | 20ch | Director | |
| 佐藤 秀{sF0FA} | Hideki Sato | 20ch | Director | |
| 村田  肇 | Hajime Murata | 20ch | Director | |
| 石川  巧 | Takumi Ishikawa | 20ch | Art | |
| 小島 裕{sF0BA} | Yusuke Kojima | 20ch | Art | |
| 打道 良二 | Ryoji Uchimichi | 20ch | Art | |
| {sF08D}山 {sF0B8}司 | Masashi Kageyama | 20ch | Composer | |
| 塚本  浩 | Hiroshi Tsukamoto | 20ch | Music / Sound | |
| 浅田 明弘 | Akihiro Asada | 20ch | Music / Sound | |
| {sF088}田 則昭 | Noriaki Urata | 20ch | Special Thanks | |
| 鈴木 和子 | Kazuko Suzuki | 20ch | Special Thanks | |
| 寺田 白{sF08B} | Hakuun Terada | 20ch | Calligraphy | |
| 東谷 浩明 | Hiroaki Higashitani | 20ch | Coordinator | |
| 江口 弘泰 | Hiroyasu Eguchi | 20ch | Coordinator | |
| 山本 {sF08F}夫 | Hideo Yamamoto | 20ch | Coordinator | |
| 吉田 {sF0EE}春 | Yoshiharu Yoshida | 20ch | Supervisor (`{sF0DE}修` = SUPERVISOR) | |
| 中村 {sF07C}朗 | Ichiro Nakamura | 20ch | Scenario | |
| 柳  草{sF07C}郎 | Soichiro Yanagi | 20ch | Scenario | |
| 山形 厚史 | Atsushi Yamagata | 20ch | Scenario | |
| 酒{sF079} 豊澄 | Toyozumi Sakai | 20ch | Production Progress | |
| 池下 友香子 | Yukako Ikeshita | 20ch | Production Progress | |

## Places
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 修門砦 | Shumon Fort | 28ch | Opening stronghold in Shikoku | Shuumon |
| 八方外法陣 | Happo Outer Array | 28ch | Barrier surrounding Shumon Fort | |
| 土佐の村 | Tosa Village | 28ch | First village in Shikoku | |
| 黒羽のほこら | Kuroba Shrine | 28ch | Shrine in Shikoku | |
| 出羽三山 | Dewa Sanzan | 28ch | Sacred mountains in northern Japan | |
| 恐山 | Mt. Osore | 28ch | Spirit mountain | |
| 殺生宮 | Sessho Shrine | 28ch | Shrine | |
| 京都御所 | Kyoto Imperial Palace | 28ch | Seat of the Emperor | |
| 京都 / 京の都 | Kyoto / the capital | 28ch | Imperial Capital (Kyoto) | |
| 練武館 | Renbukan | | Mikage and Tokoyo's fallen school in Nagato | |
| 黄泉の道 | Path of Yomi | 28ch | Road of the Dead | |
| 守光楼閣 | Shuko Pavilion | 28ch | Barrier tower anchoring the Storm-Calling Rite | |
| かすみ砦 | Kasumi Fort | 28ch | Stronghold of the Kasumi Clan | |
| 退魔陵 | Exorcism Mausoleum | 28ch | Mausoleum | |
| 吉野ヶ里 | Yoshinogari | 28ch | Kyushu settlement & ruins | |
| 鬼界城 | Kikai Castle | 28ch | Jugon's fortress in Kyushu | |
| カムイ遺跡 | Kamui Ruins | 28ch | Ancient ruins in Ezo | |
| 剣山 | Mt. Tsurugi | 28ch | Mountain in Shikoku hiding the War Demon's Coffin | |
| 長沙の村 | Changsha Village / Changsha | 28ch | First continental village (Byakuren's home) | |
| 少林寺 | Shaolin Temple | 28ch | Martial monastery | |
| 達磨洞 | Bodhidharma Cave | 28ch | Sacred cave near Shaolin | |
| 洛陽 | Luoyang | 28ch | Ancient Chinese capital | |
| 西安 | Xi'an | 28ch | Silk Road gateway city | |
| 幻陽楼 | Genyo Tower | 28ch | Illusion tower in Xi'an | |
| アグニの迷道 | Agni's Labyrinth | 28ch | Fiery maze | |
| 大同 | Datong | 28ch | Northern Shanxi city | |
| 臨安 | Lin'an | 28ch | Southern Song capital | |
| 大都 | Dadu | 28ch | Yuan capital (Beijing) | |
| 雲崗石窟 | Yungang Grottoes | 28ch | Stone grottoes near Datong | |
| 蘭州 | Lanzhou | 28ch | Gansu Yellow River city | |
| 敦煌 | Dunhuang | 28ch | Oasis town / Meisa's true home | |
| 莫高窟 | Mogao Caves | 28ch | Thousand-Buddha Grottoes | |
| 火焔山 | Flaming Mountains | 28ch | Desert barrier west of Dunhuang | |
| 邪馬台国 | Yamataikoku | | Ancient realm ruled by Himiko | |
| ウルムチ | Urumqi | 28ch | Oasis city north of Taklamakan | |
| ホータン | Hotan | 28ch | Jade oasis south of Taklamakan | |
| 崑崙 | Kunlun | 28ch | Sacred hidden paradise | Konron |
| 魔導宮 | Magic Palace | 28ch | Dark twin of Kunlun | Madogu / Madoukyu |
| 鬼獣界 | Demon-Beast Realm | 28ch | Realm ruled by Bukoku | |
| 幻応界 | Illusion Realm | 28ch | Realm ruled by Jako | |
| 流酷界 | Ryukoku Realm / Ryukoku | 28ch | Central realm ruled by Sogyoku | |
| 呪界 | Curse Realm | 28ch | Realm ruled by Jugon | Jukai |
| 対馬 | Tsushima | 28ch | Island between Kyushu and Korea | |
| 平泉 | Hiraizumi | | Historical site of Yoshitsune's supposed death | |
| 開京 | Kaesong | 28ch | Goryeo capital on port map | |
| 蝦夷 | Ezo | | Northern island (Hokkaido) | |

## Items / skills / terms
| JP | EN | max | notes | Avoid |
|---|---|---|---|---|
| 天道一族 | Tendo Clan | | Hayate's clan | |
| かすみ一族 | Kasumi Clan | | Genzo and Shinobu's shinobi clan | |
| 呪界衆 | Curse Realm Sect | | Kublai Khan's mystic cult | |
| 法力者 | Mystic / Mystics | | Practitioner of spiritual arts | |
| 法術 | Jutsu / mystic arts | | Battle menu uses `Jutsu` (`40px`) | |
| 招嵐の法 | Storm-Calling Rite | | Ancient gale rite protecting Japan | |
| 神獣鏡 | Divine Beast Mirror | | Sacred mirror hidden by Himiko | |
| 霊晶輪 | Spirit Crystal Ring / Spirit Crystal Rings | 96px | Five elemental crystal rings | |
| 赤晶輪 | Red Crystal Ring | 96px | Fire Spirit Crystal Ring | |
| 緑晶輪 | Green Crystal Ring | 96px | Wood Spirit Crystal Ring | |
| 青晶輪 | Blue Crystal Ring | 96px | Water Spirit Crystal Ring | |
| 紫晶輪 | Purple Crystal Ring | 96px | Metal Spirit Crystal Ring | |
| 黄晶輪 | Yellow Crystal Ring | 96px | Earth Spirit Crystal Ring | |
| 至崩輪 | Ring of Ruin | 96px | Kunlun heirloom that shatters barriers | |
| 戦鬼の棺 | War Demon's Coffin | | Coffin sealing Benkei on Mt. Tsurugi | |
| 戦鬼 | War Demon | | Benkei's fearsome moniker | |
| 海龍の骨 | Sea Dragon Bone | 96px | Talisman parting the sea to Kikai Castle | |
| 皇帝の闇 | Emperor's Darkness | 96px | Key item tied to Kublai Khan | |
| 飛跳印 | Soaring Seal | 96px | Opens path along Twin Sal Trees | |
| 夢操印 | Dream-Weaving Seal | 96px | Dream realm seal | |
| 三日月の笛 | Crescent Flute | 96px | Calls the twin crescent toward Kunlun | |
| 破封の鍵 | Sealbreaker Key | 96px | Key item | |
| 月光灯 | Moonlight Lantern | 96px | Key item | |
| 月影の馬 | Moonshadow Steed | 96px | Key item | |
| 式符 | Talisman / Talismans | 96px | Consumable paper ward | Shikifu |
| 沙羅双樹 | Twin Sal Trees | | Bridge linking the two otherworlds | |
| 文永の役 | Bun'ei Campaign | | 1274 first Mongol invasion of Japan | |
| 蒙古軍 | Mongol army / Mongol forces / Mongols | | Invading Yuan army | |
| 麒鱗 | Kirin | | Mythic sacred beast summoned by Himiko | |

## Decisions from earlier batches
- (Updated 2026-11-20: initial glossary seeded from verified ROM extraction and pilot survey.)
