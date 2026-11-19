# Style Reference - *Benkei Gaiden: Suna no Shou*

Tone, formatting, voice rules, and approved JP/EN pairs for every translator and reviewer.

## Core Tone & Formatting
- **World:** 1270s feudal Japan & Silk Road Yuan China dark-fantasy RPG. Earthy, mythic, urgent — neither dry museum prose nor modern slang.
- **Spoken Lines vs Narration:**
  - When JP prefixes a speaker (`ハヤテ「...` — note JP drops the closing `」`), render as `Hayate: "..."` with full closing quotation marks.
  - When an unnamed speaker speaks (`"..."` without `「` in JP, e.g., villagers/soldiers), render plain `"..."` — do NOT invent fake speaker prefixes like `Soldier:`.
  - When narration/signposts/system prompts occur, write clean prose without quotes.
- **Line Wrapping:** Explicitly wrap every line inside 192 px (`dialogue`, `system`, `battle_msg`, `equip_desc`, `jutsu_desc`) or 192 px × 2 (`item_desc`) using `{nl}` and `{page}` (`<= 3` lines per `{page}`). Remember each `{name0..4}` token reserves **48 px** worst-case width.
- **No Dropped Register:** Match character voices below on every line. Never flatten old men (`じゃ/のう/わし`), fiery youth (`ぜ/ねえ`), knights (`ござる/仕った`), Kyoto townsfolk (`どすえ`), Tosa villagers (`ちや`), or Benkei (`おれさま/ワッハッハッ`) into generic neutral text.

## Character Voice Table
| Character / Archetype | JP Cues | English Voice |
|---|---|---|
| **Saizo** (才蔵) | わし、おおせか、ウム、いたせ、おまえ | Stern, paternal veteran warrior. Dignified, measured imperatives: *"Prepare yourself for the road."*, *"Leave the fort in their hands."* |
| **Hayate** (ハヤテ) | ござる、参上仕った、御意に、おぬし | Disciplined shinobi retainer; shifts to gritty plain speech in crisis (`おれ`). Formal to elders (*"My lord Saizo"*, *"At His Majesty's command"*); stoic and warm to the young fighters (*"Foul beast..."*, *"Go on ahead!"*). |
| **Mikage** (`{name1}`) | です・ます、ござる（対目上）、落ち着いた敬語 | Polite, level-headed, observant. Clear sentences, courteous address without stiffness (*"We owe you our thanks."*, *"Wait -- what does that mean?"*). |
| **Tokoyo** (`{name2}`) | おれ、ぜ、ねえ、バカをいえ、あんた | Brash, big-hearted swordsman. Natural contractions and grit (*"Dammit!"*, *"Don't talk crazy!"*, *"Look, we're sticking with you!"*). |
| **Benkei** (弁慶) | おれさま、じゃねえか、ワッハッハッ | Booming, larger-than-life warrior-monk. Fearless, warm-hearted, unapologetically loud (*"Bwahaha!"*, *"Wait a damn second!"*, *"I won't die -- not even Hell could hold me!"*). |
| **Byakuren** (`{name3}`) | ぼく、かあさん、・・・ | Earnest, brave young boy. Simple, heartfelt cadence (*"Thank goodness!"*, *"Mother's waiting, I know, but..."*). |
| **Meisa** (`{name4}`) | わたし、・・・ね、〜の、ごきげんよう | Soft-spoken, gentle, slightly otherworldly. Graceful, tender phrasing (*"My memories are starting to return..."*, *"Fare you well, Sister."*). |
| **Village Elders & Monks** | わし、じゃ、のう、じゃろう | Weathered rural elders (*"Eh?"*, *"Long ago, mind you..."*, *"Aye, no mistaking it."*). |
| **Tosa / Kyoto Folk** | ちや（土佐）、どすえ・〜や（京・上方） | Regional warmth without unreadable eye-dialect (*"Folk have set out from here for years..."*, *"Why, the Khan leads the Great Yuan across the sea."*). |
| **Kublai Khan & Himiko** | われ、わし、御霊、ゆえに | Imperial, commanding, archaic solemnity (*"In the name of Himiko, I call upon the Divine Beast Mirror..."*). |
| **Four Realm Generals** | きさま、おろか者、フフッ、グフッ | Theatrical menace — sneering arrogance (`Jako`, `Sogyoku`) or brute fury (`Jugon`, `Bukoku`). |

## Approved JP / EN Pilot Pairs
Visually verified on `build/pilot.sfc` in MesenCE (`work/qa/pilot/`):

| ID | Japanese | English |
|---|---|---|
| `1A_8000` (p1) | ハヤテ「才蔵どの、おひさしゅうござる。帝の命により、参上仕った | `Hayate: "Master Saizo, it has{nl}been too long. I come at{nl}the Emperor's command."` |
| `1A_8000` (p2) | 才蔵「天道のハヤテか。して、帝は何と？ | `Saizo: "Hayate of the Tendo,{nl}is it? Well then, what word{nl}from the Emperor?"` |
| `1A_8000` (p4) | 才蔵「・・・この才蔵にも、「動け」とのおおせか・・・ | `Saizo: "...So His Majesty bids{nl}even old Saizo step forth{nl}at last..."` |
| `1A_8000` (p6) | 才蔵「ウム。この砦のことを配下のものにたくした後、{name0}を連れて早急に帝のもとにまいろう | `Saizo: "Hmm. Once I leave{nl}this fort to my men, I shall{nl}bring {name0} swiftly"` ... |
| `1A_812E` | ハヤテ「おぬしが、{name0}どのか・・・{page}つらい修行に、長い間よく耐えてきたな。{name0}どのには、語らねばならぬことが多くある。 | `Hayate: "So you are{nl}{name0}..."{page}"You endured long years of{nl}grueling training. I have much{nl}to tell you, {name0}."` ... |
| `1A_8207` | こらこら。これは、「戦鬼の碑」じゃ。遊び場ではないぜよ | `"Hey now! This here's the{nl}War Demon Stele -- not a{nl}playground, mind you!"` |
| `1A_8228` | ここからは、大勢のものたちが旅だっていったちや。「天道一族」のハヤテも、才蔵さまの弟子の一人だった・・・ | `"Plenty of folk have set out{nl}from here over the years.{nl}Hayate of the Tendo Clan{page}was one of Lord Saizo's{nl}very own pupils too..."` |
| `1A_839F` | この砦をおおうのは、我が呪法「八方外法陣」。私を倒さねば、この結界は消えぬ{page}才蔵「何奴！ | `"This barrier sealing your{nl}fort is my curse: the{nl}Happo Outer Array.{page}Unless you defeat me, the{nl}seal will never lift."{page}Saizo: "Who goes there?!"` |
| `1A_8457` | 才蔵「よし。全てをおまえにたくそう。おまえが無事に帰った時、わしの知る全てを語ろう。では、ゆけ！ | `Saizo: "Very well. I entrust{nl}everything to you. When you{nl}return safely, I will tell{page}you all that I know.{nl}Now go!"` |
| `1D_8000..8087` | 「守光楼閣」崩壊とともに、日本は／「招嵐の法」を失った。... | `With Shuko Pavilion's fall, Japan` / `lost the Storm-Calling Rite. Upon` / `learning of this, Kublai Khan urged` ... |
