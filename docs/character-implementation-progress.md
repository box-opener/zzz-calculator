# Character implementation progress (non-authoritative)

This is an implementation queue, not a game-semantics source. The catalog order for this queue is ascending numeric character ID from the live Nanoka 3.2 character index at `https://static.nanoka.cc/zzz/3.2/character.json`, cached at `/private/tmp/nanoka-character-index-3.2.json`. The index has 60 IDs; 15 are now present in the calculator registry, leaving 45 to implement. Rank and type columns retain the source index numeric values without redefining their semantics.

New live records should retain the complete source JSON and the verified live-3.2 source URL/version. Existing character raw records remain unchanged. Rows marked “已实现” or “部分实现” are present in the calculator registry. Rows still marked “待实现” will be addressed in ascending ID order.

| Character ID | Nanoka code | Chinese catalog name | Rank value | Type value | Status |
|---:|---|---|---:|---:|---|
| `1011` | Anby | 安比 | 3 | 2 | 部分实现（live raw + level-60 panel + 13 direct damage moves + electric anomaly/disorder + C2/C6; Daze/Energy results remain outside current calculator contract） |
| `1021` | Nekomata | 猫又 | 4 | 1 | 部分实现（live raw + potential-0 baseline, all mapped Direct moves, static Physical Anomaly/Disorder and confirmed core/cinema rules; Potential variants and random repeat hit multiplier remain local source limitations） |
| `1031` | Nicole | 妮可 | 3 | 4 | 部分实现（live raw + normal/enhanced direct curves, static Ether Corrosion/Disorder, confirmed Core/Cinema and R5 signature build; unknown Energy Field/charge branches and resource/Daze outputs remain local source/result limits） |
| `1041` | Soldier 11 | 「11号」 | 4 | 1 | 待实现 |
| `1051` | Yidhari | 伊德海莉 | 4 | 6 | 待实现 |
| `1061` | Corin | 可琳 | 3 | 1 | 待实现 |
| `1071` | Caesar | 凯撒 | 4 | 5 | 待实现 |
| `1081` | Billy | 比利 | 3 | 1 | 待实现 |
| `1091` | Miyabi | 雅 | 4 | 3 | 已实现（已有registry/compiler） |
| `1101` | Koleda | 珂蕾妲 | 4 | 2 | 待实现 |
| `1111` | Anton | 安东 | 3 | 1 | 待实现 |
| `1121` | Ben | 本 | 3 | 5 | 待实现 |
| `1131` | Soukaku | 苍角 | 3 | 4 | 待实现 |
| `1141` | Lycaon | 莱卡恩 | 4 | 2 | 待实现 |
| `1151` | Lucy | 露西 | 3 | 4 | 待实现 |
| `1161` | Lighter | 莱特 | 4 | 2 | 待实现 |
| `1171` | Burnice | 柏妮思 | 4 | 3 | 待实现 |
| `1181` | Grace | 格莉丝 | 4 | 3 | 待实现 |
| `1191` | Ellen | 艾莲 | 4 | 1 | 待实现 |
| `1201` | Harumasa | 悠真 | 4 | 1 | 待实现 |
| `1211` | Rina | 丽娜 | 4 | 4 | 待实现 |
| `1221` | Yanagi | 柳 | 4 | 3 | 待实现 |
| `1241` | Zhu Yuan | 朱鸢 | 4 | 1 | 待实现 |
| `1251` | QingYi | 青衣 | 4 | 2 | 已实现（已有registry/compiler） |
| `1261` | Jane | 简 | 4 | 3 | 待实现 |
| `1271` | Seth | 赛斯 | 3 | 5 | 待实现 |
| `1281` | Piper | 派派 | 3 | 3 | 待实现 |
| `1291` | Hugo | 雨果 | 4 | 1 | 待实现 |
| `1301` | Orphie & Magus | 奥菲丝&「鬼火」 | 4 | 1 | 待实现 |
| `1311` | Astra | 耀嘉音 | 4 | 4 | 已实现（已有registry/compiler） |
| `1321` | Evelyn | 伊芙琳 | 4 | 1 | 待实现 |
| `1331` | Vivian | 薇薇安 | 4 | 3 | 已实现（已有registry/compiler） |
| `1341` | Zhao | 照 | 4 | 5 | 已实现（已有registry/compiler） |
| `1351` | Pulchra | 波可娜 | 3 | 2 | 待实现 |
| `1361` | Trigger | 「扳机」 | 4 | 2 | 已实现（已有registry/compiler） |
| `1371` | YiXuan | 仪玄 | 4 | 6 | 已实现（已有registry/compiler） |
| `1381` | Soldier 0 - Anby | 零号·安比 | 4 | 1 | 待实现 |
| `1391` | Ju Fufu | 橘福福 | 4 | 2 | 待实现 |
| `1401` | Alice | 爱丽丝 | 4 | 3 | 已实现（已有registry/compiler） |
| `1411` | Yuzuha | 柚叶 | 4 | 4 | 已实现（已有registry/compiler） |
| `1421` | Yinhu | 潘引壶 | 3 | 5 | 待实现 |
| `1431` | Ye Shunguang | 叶瞬光 | 4 | 1 | 已实现（已有registry/compiler） |
| `1441` | Manato | 真斗 | 3 | 6 | 待实现 |
| `1451` | Lucia | 卢西娅 | 4 | 4 | 已实现（已有registry/compiler） |
| `1461` | Seed | 「席德」 | 4 | 1 | 待实现 |
| `1471` | Banyue | 般岳 | 4 | 6 | 待实现 |
| `1481` | Dialyn | 琉音 | 4 | 2 | 已实现（已有registry/compiler） |
| `1491` | Sunna | 千夏 | 4 | 4 | 待实现 |
| `1501` | Aria | 爱芮 | 4 | 3 | 待实现 |
| `1511` | NangongYu | 南宫羽 | 4 | 2 | 待实现 |
| `1521` | Cissia | 希希芙 | 4 | 1 | 待实现 |
| `1531` | Starlight - Billy | 星徽·比利 | 4 | 6 | 待实现 |
| `1541` | Promeia | 普罗米娅 | 4 | 3 | 待实现 |
| `1551` | Pyrois | 佩洛伊斯 | 4 | 1 | 待实现 |
| `1561` | Velina | 维琳娜 | 4 | 3 | 待实现 |
| `1571` | Norma | 诺姆 | 4 | 2 | 待实现 |
| `1581` | Remielle | 蕾米埃尔 | 4 | 3 | 待实现 |
| `1591` | Sigrid | 希格莉德 | 4 | 1 | 待实现 |
| `1611` | Claret | 克拉蕾 | 4 | 7 | 待实现 |
| `1621` | Roxy | 洛克茜 | 4 | 2 | 待实现 |

## Current queue

Next unsupported ID: `1041`（「11号」/ Soldier 11). The queue proceeds by ascending numeric ID, skipping the 15 entries already marked supported above. Source acquisition, raw preservation, reviewed mapping, compiler integration, validation, and a per-character commit remain the required closure for each new character.

## Anby (`character:1011`)

The complete Nanoka raw payload is stored from `https://static.nanoka.cc/zzz/3.2/zh/character/1011.json`, with source version `3.2`. The reviewed direct mapping preserves separate source skill IDs: Basic Voltaic Assault stages 1–3 are Physical and stage 4 is Electric; Falling Thunder is Electric; Arc Slash is Physical; the remaining damage entries follow their explicit Electric source text. The raw Daze curves remain intact; core and Cinema Daze bonuses use the Daze modifier node, while no Daze result is emitted. Energy Gain Efficiency and one-shot Energy restoration stay in non-blocking source diagnostics and are not converted to Energy Regeneration.

Cinema 6 uses an explicit current 0–8 charge selection. A selected positive count enables one +45% ordinary damage bonus on the current Basic or Dash hit; remaining charges do not multiply that bonus and charge creation/consumption timing is not replayed. The A-rank UI defaults are Cinema 6 and skill level 16, including Ultimate. The reviewed signature mapping is Anby → `wengine:13101` (the Nanoka catalog identifies the Demara Battery Mark II icon as `Weapon_A_1011` and says the model is often used by Anby); its default selection is Refinement 5. Nanoka's `IconRole01` portrait asset is not included locally, so the catalog uses a neutral placeholder without borrowing another character's image.

## Nekomata (`character:1021`)

The full live-3.2 detail is retained at `core/data/characters/nekomata.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1021.json`. The reviewed compile view selects the seven core levels whose raw potential is `[0]`; all raw potential records remain preserved. The `potential_detail` records identify IDs `102100`–`102105` as 猫的报恩 I–VI / 潜能觉醒, a separate Potential progression for which the calculator has no selector. Its modified skill descriptions, extra evade move, and extra dodge counter are therefore not treated as Cinema or merged into the baseline.

All 14 baseline direct entries use the raw physical damage curves and source skill IDs, including the five separate Cat Claw stages and the Red Blade attack. The source's 33.33% repeat text applies to the fifth Cat Claw hit and Red Blade, but Nanoka exposes no separate repeat multiplier or event identity. The main hit stays calculated; when the current repeated-hit result is explicitly selected for one of those exact event templates, a blocking ambiguity diagnostic preserves the known main hit and leaves only the repeated damage unresolved. Other Cat Claw stages are unaffected. Static Physical Assault and Disorder use the standard single-character 100% buildup assumption and NoCrit.

Core damage and Cinema stack effects use explicit current-state inputs. Cinema 1 applies to Nekomata's Direct Physical attack events: it reads the actual enemy-stunned state and otherwise requires the current event's back-hit condition, so the two routes cannot double the 16% Physical resistance ignore. Cinema 2's Energy Gain Efficiency and Support Parry Daze curves remain source notes because the request has no Energy or Daze result. The catalog uses a neutral placeholder because the source `IconRole11` image is not packaged locally.

The existing Nanoka `14102` Steel Cushion record has catalog icon `Weapon_S_1021` and is exposed as Nekomata's signature selection; the S-rank default is R1. The real equipment-build path applies its level-60 white ATK/CR substat and separates the physical-damage bonus from the current back-hit damage bonus.

## Nicole (`character:1031`)

The complete live-3.2 source is retained at `core/data/characters/nicole.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1031.json`; this record declares no Potential variants. The level-60 panel includes +75 base ATK and +0.36 flat Energy Regeneration (`30501`, 36/100) from the raw extra-level record. The source signature mapping is the A-rank Treasure Chest `13103` (`Weapon_A_1031`), which defaults to R5; its level-60 build contributes 624 white ATK, +50% out-of-combat Energy Regeneration, and a separate current +0.8 flat panel effect while its Ether-trigger state is active.

The reviewed list keeps the exact Physical normal/enhanced Basic and Dash curves separate. The raw maximum of eight enhanced-ammo uses does not map to each multi-hit curve component, so an explicit current “enhanced ammo active” condition selects the exact enhanced curve without simulating a charge counter. Ether Dodge Counter, Special, EX cannon, Chain cannon, Ultimate cannon, Quick Assist, and Support Follow-up remain distinct from the Physical Basic/Dash entries. The explicit `A + {B/3}*3`, `/4*4`, and `/20*20` formulas are resolved as sums of the two raw curves once each, without multiplying the repeated component again.

Core Defense Down and its same-target Ether extra ability use an explicit current target state. Cinema 6 is an event-stat target Crit Rate modifier for Standard-Crit Direct/Penetration events; it does not alter formal character panels or NoCrit anomaly results. EX-charge and energy-field branches preserve their separate source curves; when a current branch is selected, a local ambiguity diagnostic keeps the known cannon hit because the raw text does not specify whether the charge/field coefficient is per event or the full total and does not give the hit count. C2/Ultimate Energy and Support Parry Daze remain source notes because the current request has no Energy/Daze result. The catalog uses a neutral placeholder because `IconRole12` is not packaged locally.
