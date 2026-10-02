# Character implementation progress (non-authoritative)

This is an implementation queue, not a game-semantics source. The catalog order for this queue is ascending numeric character ID from the live Nanoka 3.2 character index at `https://static.nanoka.cc/zzz/3.2/character.json`, cached at `/private/tmp/nanoka-character-index-3.2.json`. The index has 60 IDs; 13 are now present in the calculator registry, leaving 47 to implement. Rank and type columns retain the source index numeric values without redefining their semantics.

New live records should retain the complete source JSON and the verified live-3.2 source URL/version. Existing character raw records remain unchanged. Rows marked “已实现” or “部分实现” are present in the calculator registry. Rows still marked “待实现” will be addressed in ascending ID order.

| Character ID | Nanoka code | Chinese catalog name | Rank value | Type value | Status |
|---:|---|---|---:|---:|---|
| `1011` | Anby | 安比 | 3 | 2 | 部分实现（live raw + level-60 panel + 13 direct damage moves + electric anomaly/disorder + C2/C6; Daze/Energy results remain outside current calculator contract） |
| `1021` | Nekomata | 猫又 | 4 | 1 | 待实现 |
| `1031` | Nicole | 妮可 | 3 | 4 | 待实现 |
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

Next unsupported ID: `1021` (猫又 / Nekomata). The queue proceeds by ascending numeric ID, skipping the 13 entries already marked supported above. Source acquisition, raw preservation, reviewed mapping, compiler integration, validation, and a per-character commit remain the required closure for each new character.

## Anby (`character:1011`)

The complete Nanoka raw payload is stored from `https://static.nanoka.cc/zzz/3.2/zh/character/1011.json`, with source version `3.2`. The reviewed direct mapping preserves separate source skill IDs: Basic Voltaic Assault stages 1–3 are Physical and stage 4 is Electric; Falling Thunder is Electric; Arc Slash is Physical; the remaining damage entries follow their explicit Electric source text. The raw Daze curves remain intact; core and Cinema Daze bonuses use the Daze modifier node, while no Daze result is emitted. Energy Gain Efficiency and one-shot Energy restoration stay in non-blocking source diagnostics and are not converted to Energy Regeneration.

Cinema 6 uses an explicit current 0–8 charge selection. A selected positive count enables one +45% ordinary damage bonus on the current Basic or Dash hit; remaining charges do not multiply that bonus and charge creation/consumption timing is not replayed. The A-rank UI defaults are Cinema 6 and skill level 16, including Ultimate. The reviewed signature mapping is Anby → `wengine:13101` (the Nanoka catalog identifies the Demara Battery Mark II icon as `Weapon_A_1011` and says the model is often used by Anby); its default selection is Refinement 5. Nanoka's `IconRole01` portrait asset is not included locally, so the catalog uses a neutral placeholder without borrowing another character's image.
