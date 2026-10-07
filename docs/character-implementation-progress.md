# Character implementation progress (non-authoritative)

This is an implementation queue, not a game-semantics source. Unless the user gives a different priority order, the catalog order is ascending numeric character ID from the live Nanoka 3.2 character index at `https://static.nanoka.cc/zzz/3.2/character.json`, cached at `/private/tmp/nanoka-character-index-3.2.json`. The index has 60 IDs; with Lycaon registered, 32 are not yet implemented. Rank and type columns retain the source index numeric values without redefining their semantics.

New live records should retain the complete source JSON and the verified live-3.2 source URL/version. Existing character raw records remain unchanged. Rows marked “已实现” or “部分实现” are present in the calculator registry. Rows still marked “待实现” will be addressed in ascending ID order.

| Character ID | Nanoka code | Chinese catalog name | Rank value | Type value | Status |
|---:|---|---|---:|---:|---|
| `1011` | Anby | 安比 | 3 | 2 | 部分实现（live raw + level-60 panel + 13 direct damage moves + electric anomaly/disorder + C2/C6; Daze/Energy results remain outside current calculator contract） |
| `1021` | Nekomata | 猫又 | 4 | 1 | 部分实现（live raw + potential 0–6 selector, reviewed Direct moves, static Physical Anomaly/Disorder, deterministic stunned-target potential repeats and C1 back-hit interaction; baseline random repeat and Energy/Daze outputs remain outside scope） |
| `1031` | Nicole | 妮可 | 3 | 4 | 部分实现（live raw + normal/enhanced direct curves, static Ether Corrosion/Disorder, confirmed Core/Cinema and R5 signature build; unknown Energy Field/charge branches and resource/Daze outputs remain local source/result limits） |
| `1041` | Soldier 11 | 「11号」 | 4 | 1 | 部分实现（live 3.2 raw + level-60 panel + 17 baseline/20 potential Direct entries + static Burn/Disorder + reviewed Core/Cinema/Potential rules; resource and Daze outputs remain outside the current result contract） |
| `1051` | Yidhari | 伊德海莉 | 4 | 6 | 部分实现（live 3.2 raw + level-60 panel + Ice Penetration damage entries + Ice Anomaly/Disorder + Core/Cinema; low-HP intermediate damage curve and Ice-tentacle child identity remain local diagnostics） |
| `1061` | Corin | 可琳 | 3 | 1 | 部分实现（live 3.2 raw + level-60 panel + A-rank skill defaults + reviewed Physical Direct entries including complete maximum continuous-saw totals + Physical Assault/Disorder + Core/Cinema current-state rules; Daze and Energy resource results remain outside the current result contract） |
| `1071` | Caesar | 凯撒 | 4 | 5 | 部分实现（live 3.2 raw + level-60 Defense panel + reviewed Physical Direct entries + static Physical Assault/Disorder + current-operator shield ATK, enemy debuff and Cinema rules; shield capacity, Daze, Energy/Support Point, and incoming-damage results remain outside the current contract） |
| `1081` | Billy | 比利 | 3 | 1 | 部分实现（live 3.2 raw + level-60 panel + reviewed Physical Direct entries + static Physical Assault/Disorder + Core/Cinema current-state rules; Daze and Energy resource results remain outside the current result contract） |
| `1091` | Miyabi | 雅 | 4 | 3 | 已实现（已有registry/compiler） |
| `1101` | Koleda | 珂蕾妲 | 4 | 2 | 部分实现（live 3.2 raw + level-60 panel + potential 0–6 + Physical/Fire Direct entries + Fire Burn/Disorder + Ben team-coordination curves + Core/Cinema current states; Vanguard 锐暴, Daze and Energy results remain outside the registered calculation contract） |
| 1111 | Anton | 安东 | 3 | 1 | 部分实现（live 3.2 raw + level-60 panel + Physical/Electric Direct entries + Electric Shock/Disorder + source-scoped Core and current Cinema states; the mixed Drill/Pile Assist Strike bonus allocation and triggered extra-Shock source attribution remain local limits; Energy, shield/incoming and Daze results remain outside the current contract） |
| `1121` | Ben | 本 | 3 | 5 | 部分实现（live 3.2 raw + level-60 Defense panel + Physical/Fire Direct entries + static Burn/Disorder + shield-state team Crit and Cinema counter state; Core Initial DEF-to-ATK layer and Cinema 2 counter-child identity remain localized pending clarification; shield, incoming damage, Energy, Support Points, and Daze are outside the result contract） |
| `1131` | Soukaku | 苍角 | 3 | 4 | 部分实现（live 3.2 raw + level-60 Support panel + reviewed Physical/Ice Direct entries + static Physical Assault/Ice Shatter/Disorder + Core self-buff, Ice Additional Ability, Cinema 4/6 states; transferred Core buff recipient and EX multi-click total remain source-limited; Daze/Energy/time/resource outputs remain outside current contract） |
| `1141` | Lycaon | 莱卡恩 | 4 | 2 | 部分实现（live 3.2 raw + level-60 Stun panel + Potential 0–6 selector + Physical/Ice Direct entries, Potential Ice Dance and selectable Hunt sequences + static Ice Anomaly/Disorder; Physical source hits have no anomaly buildup and do not create a Physical record; Core/Additional Ability/Cinema current states; Daze, shield, Energy and timing results remain outside the current contract） |
| `1151` | Lucy | 露西 | 3 | 4 | 待实现 |
| `1161` | Lighter | 莱特 | 4 | 2 | 待实现 |
| `1171` | Burnice | 柏妮思 | 4 | 3 | 待实现 |
| `1181` | Grace | 格莉丝 | 4 | 3 | 待实现 |
| `1191` | Ellen | 艾莲 | 4 | 1 | 待实现 |
| `1201` | Harumasa | 悠真 | 4 | 1 | 待实现 |
| `1211` | Rina | 丽娜 | 4 | 4 | 待实现 |
| `1221` | Yanagi | 柳 | 4 | 3 | 部分实现（live 3.2 raw + level-60 panel + reviewed Direct moves + static Shock/Disorder + selected-record Polar Disorder with current-AP additive component; Daze, buildup, energy and timing outputs remain outside the current result contract） |
| `1241` | Zhu Yuan | 朱鸢 | 4 | 1 | 待实现 |
| `1251` | QingYi | 青衣 | 4 | 2 | 已实现（已有registry/compiler） |
| `1261` | Jane | 简 | 4 | 3 | 待实现 |
| `1271` | Seth | 赛斯 | 3 | 5 | 待实现 |
| `1281` | Piper | 派派 | 3 | 3 | 待实现 |
| `1291` | Hugo | 雨果 | 4 | 1 | 待实现 |
| `1301` | Orphie & Magus | 奥菲丝&「鬼火」 | 4 | 1 | 待实现 |
| `1311` | Astra | 耀嘉音 | 4 | 4 | 已实现（已有registry/compiler） |
| `1321` | Evelyn | 伊芙琳 | 4 | 1 | 待实现 |
| `1331` | Vivian | 薇薇安 | 4 | 3 | 已实现（已有registry/compiler；B5在当前上场角色面板下分组显示各自异放结果，不计入所选招式总计） |
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
| `1561` | Velina | 维琳娜 | 4 | 3 | 部分实现（live 3.2 raw + level-60 panel + reviewed Direct/cyclone curves + static Weathering + Wind-triggered Turbulence/Discharge; Daze, buildup, resource and timing outputs remain outside the result contract） |
| `1571` | Norma | 诺姆 | 4 | 2 | 待实现 |
| `1581` | Remielle | 蕾米埃尔 | 4 | 3 | 部分实现（live 3.2 raw + level-60 panel + 17 Luminance Direct entries + stable formation Flow + selectable ordinary/special virtual-void source slots + typed Flare/penetration snapshots + switchable AP/C4/C6 rules; Daze/resource results remain outside the current calculation output） |
| `1591` | Sigrid | 希格莉德 | 4 | 1 | 待实现 |
| `1611` | Claret | 克拉蕾 | 4 | 7 | 待实现 |
| `1621` | Roxy | 洛克茜 | 4 | 2 | 待实现 |

## Current queue

Current item: Lycaon 1141 follows the reviewed and pushed Soukaku 1131. After Lycaon is reviewed and pushed, continue with Lucy 1151.

## Corin (`character:1061`)

The preserved live Nanoka 3.2 source is `core/data/characters/corin.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1061.json`. Corin is an A-rank Attack agent with Physical as her base element. Her level-60 panel includes +75 base ATK and +28.8% Crit Damage from extra-level property `21101`; the catalog uses the matching `IconRole09` portrait. The reviewed signature mapping is `wengine:13106` 家政员 (`Weapon_A_1061`); it remains an explicit selection rather than an automatic equipment default. Its level-60 build adds 624 white ATK and 25% ATK. At R5, the engine adds 0.72 flat Energy Regeneration only while Corin is actually off-field; its EX-hit Physical bonus uses an explicit 0–15 current-stack input, defaulting to 15. Stack expiry is not simulated.

Direct entries use their own source curve IDs. Dodge Counter and Quick Assist sum the two raw components. Special and EX each expose the start, explosion, continuous-saw maximum segment, and a complete maximum total that adds the source components once. The “continuous-saw maximum damage” source value is treated as a complete segment total once; no hit count or duration is inferred. A-rank skill defaults are level 16, Core 7 and Cinema 0; C3/C5 skill-level increases are capped at 16.

The Physical Assault and Disorder choices use the calculator's static full-gauge and NoCrit model. Disorder uses `450% + floor(t) × 7.5%` with an explicit 0–10-second current remaining-time input. Core chainsaw damage, Cinema 1 target damage, Cinema 2 Physical resistance stacks, and the Additional Ability's actual enemy-stunned requirement keep separate scopes. Cinema 6's 0–40 current charge input is a resource state, not a time or stack-history simulation; each selected qualifying explosion adds one `3% × current charges` attack ratio to that event. Support Parry Daze and Cinema 4 Energy restoration remain source-only because the current result contract has no Daze or Energy output.

## Caesar (`character:1071`)

The preserved live Nanoka 3.2 record is `core/data/characters/caesar.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1071.json`. Caesar is an S-rank Defense agent with a Physical base element; this role is not Vanguard. The level-60 panel uses the source's +75 base ATK and +18 Impact extra-level value. Her signature is `wengine:14107` 奔袭獠牙 (`Weapon_S_1071`), verified by the local raw description rather than by list position.

The reviewed Direct curves retain Nanoka's parameter-curve IDs separately from the `skill_list` action IDs. Basic Attack stages, shield throw, Dash/Counter, Special/EX sequences, Chain, Ultimate, Quick Assist, and Support Strike are independently selectable. The third Basic-stage derived coefficient remains a separate entry pending clarification; no third-stage combined total is inferred. Static Physical Assault and Disorder use NoCrit. Core shield-holder attack is a current-operator panel effect; its current buff state can remain active for the source's post-shield interval without simulating a timer. Cinema 2 adds its 50% increase to the Core attack value only while the shield is active. Cinema 1 and the Additional Ability are current enemy debuff states. The Additional Ability's team eligibility is derived from another active Parry Support-capable agent or the same source faction. Cinema 6 applies its guaranteed Crit and damage bonuses only to its named Super Strong Shield Bash and Support Strike entries; its self Crit Rate/Crit Damage increase is a separate current-state panel effect.

Shield capacity and absorption, damage taken, interrupt resistance, Daze, Energy and Support Point changes, and cooldown/duration replay remain outside the current result contract. The source-only inputs are not converted to fabricated damage or resource totals.

## Billy (`character:1081`)

The preserved live Nanoka 3.2 record is `core/data/characters/billy.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1081.json`. Billy is an A-rank Attack agent with a Physical base element. The source icon `IconRole10` is not present in the local portrait assets, so the catalog uses the neutral placeholder. The local 13108 engine raw record is `Weapon_A_1081` and describes Billy's modified engine; it remains a selectable signature rather than being auto-equipped.

The reviewed move list keeps standing/crouching Basic fire and single-bullet ratios separate, along with the distinct roll/finisher, spread/focused Dash, three Special stages, EX, Chain, Ultimate, Quick Assist, and Assist Strike. The raw curve IDs are kept separate from skill-list action IDs. Crouch damage, post-Chain Ultimate stacks, and Cinema 6 damage stacks are current user-selected states; shot cadence, hit history, Energy, and Daze are not simulated. The Cinema 4 EX Crit Rate input defaults to the source maximum of 32% for the close-range maximum scenario; it can be lowered to 0–32% and is scoped only to that EX event. No distance-to-Crit curve is inferred. Billy's additional ability requires another same-element or same-faction agent; `AidTypeEvade` does not count as Parry Support.

## Koleda (`character:1101`)

The preserved live Nanoka 3.2 record is `core/data/characters/koleda.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1101.json`. Koleda is an S-rank Stun agent with a Fire base element; her level-60 panel adds +75 base ATK and +18 Impact from the source's level-6 extra properties. The local engine `wengine:14110` is `Weapon_S_1101`; its raw detail identifies Koleda. The source portrait icon `IconRole14` is not present in the local portrait assets, so the catalog uses the neutral placeholder.

The reviewed list keeps Physical Basic stages and Dash separate from her Fire Enhanced Basic stages, Counter, Special/EX hit and explosion parts, Chain, Ultimate, and both Assist damage actions. Ben cooperation uses source curve 1101007 for the Enhanced Basic second stage at Potential 0 when Ben is in the actual team; from Potential 1 onward it is a separate selected second-stage entry gated by the current “did not switch during the first Enhanced Basic stage” state. Special/EX cooperation uses its own source explosion curve and the current quick-follow-up state. Ultimate uses the coordinated curve when Ben is in the team. None of these checks uses the current operator as a substitute for team membership.

Potential 0–6 is user-selectable. Potential 1 exposes the source-described team +35% damage state and the 0–2 consumed Furnace layers for the Enhanced Basic second-stage +10%-per-layer effect. Potential 2–6 applies the source's non-Vanguard team Crit Damage values (11/17/23/29/35%). The separate `[锋御]` 锐暴 branch is retained in source-only diagnostics because that role is not registered. Potential 1's `ability_list` ID 11101401 has an empty description, and its stronger first-stage chase effect has no separate numeric curve; neither is given invented damage.

Cinema 4 uses a 0–2 current Furnace charge input to increase Chain/Ultimate damage by 18% per layer. Cinema 6 creates one 360%-current-ATK child event on the EX explosion, Chain, or Ultimate explosion, inheriting the parent's Fire element, StandardCrit, and matching skill group/tags; the child does not match its own creation filter. Daze and Energy/resource results remain outside the current result contract where no result value is defined.

## Remielle (`character:1581`): confirmed Flow, mutation, and Flare model

The complete live-3.2 raw record is retained at `core/data/characters/remielle.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1581.json`. This section records implementation decisions confirmed directly by the user; it does not amend game source text or authoritative calculation documentation.

Remielle's nominal Luminance identity stays unchanged. The active damage element follows the stable formation's next character (1→2→3→1; two members point to each other; solo remains Luminance). Flow affects her Direct event element bonus and special Flare element/resistance calculation, but does not create ordinary Luminance Anomaly or Disorder records.

The Core's mutation coefficient is captured once into team anomaly-effect-strength records as `1 + current Rem AP × 0.0002 + 0.10` when three Anomaly agents are active `+ 0.20` when Cinema 2 is enabled. Existing explicit history is not recalculated. Ordinary virtual-void source choices use the active teammate's reviewed Attribute Anomaly template elements (for example Miyabi's LIESHUANG and Yixuan's XUANMO), falling back to one base-element static source only where that character has no reviewed Attribute Anomaly entry. Each source snapshot retains the selected element and that source actor's penetration. A special virtual-void source has its own typed snapshot based on Remielle's current anomaly effect strength, Flow element and penetration; it is not represented as an ordinary AnomalyRecord. Up to three user-selected source slots may mix and repeat these source kinds, and an empty slot adds no event or blocking diagnostic.

Flare multipliers use the raw `AvatarSkillLevel` formulas directly (skill level 12 is not shifted by one), then add the active Core AP contribution. Cinema 4 multiplies that sum by 1.12 through a separately switchable rule. Cinema 6's extra second trigger is a separately switchable rule for Vertical Rainbow and Surprise. A C6 Basic 4 special source uses 25% of the entry special source factor; entry/refill special sources use the normal special factor `2.5 × Rem level/60`. Ordinary source Flare has no special factor. The source actor's anomaly damage bonus is not inherited; current Remielle Luminance Flare bonus, current target defense reduction, and current event defense-ignore apply at settlement.

Flare remains a Luminance anomaly-damage event with no invented MoveId, skill group or damage tag. Its parent Direct entry is calculated once and each selected source slot contributes its own NoCrit child event. The old virtual-light availability checkbox is ignored as a legacy input: configured source slots alone express source availability for the static model. Resource creation/consumption, source ordering, durations, cooldowns, and combat timing are not simulated.

## Anby (`character:1011`)

The complete Nanoka raw payload is stored from `https://static.nanoka.cc/zzz/3.2/zh/character/1011.json`, with source version `3.2`. The reviewed direct mapping preserves separate source skill IDs: Basic Voltaic Assault stages 1–3 are Physical and stage 4 is Electric; Falling Thunder is Electric; Arc Slash is Physical; the remaining damage entries follow their explicit Electric source text. The raw Daze curves remain intact; core and Cinema Daze bonuses use the Daze modifier node, while no Daze result is emitted. Energy Gain Efficiency and one-shot Energy restoration stay in non-blocking source diagnostics and are not converted to Energy Regeneration.

Cinema 6 uses an explicit current 0–8 charge selection. A selected positive count enables one +45% ordinary damage bonus on the current Basic or Dash hit; remaining charges do not multiply that bonus and charge creation/consumption timing is not replayed. The A-rank UI defaults are Cinema 6 and skill level 16, including Ultimate. The reviewed signature mapping is Anby → `wengine:13101` (the Nanoka catalog identifies the Demara Battery Mark II icon as `Weapon_A_1011` and says the model is often used by Anby); its default selection is Refinement 5. Nanoka's `IconRole01` portrait asset is not included locally, so the catalog uses a neutral placeholder without borrowing another character's image.

## Nekomata (`character:1021`)

The full live-3.2 detail is retained at `core/data/characters/nekomata.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1021.json`. The calculator's Potential slider selects the `[0]` baseline at 0 or the source variant with IDs `102100`–`102105` at levels 1–6; full source JSON and all six potential details remain preserved. Potential 1 adds the named Fluffy Claw Dodge Counter and the alternate stunned-target repeat descriptions. Potential 2–6 add the corresponding current Pounce Crit Damage bonus of 20%, 30%, 40%, 50%, and 60%.

All baseline direct entries use the raw physical damage curves and source skill IDs, including the five separate Cat Claw stages and the Red Blade attack. The baseline 33.33% random repeat is not simulated. For Potential 1–6, Cat Claw 5 and Red Blade repeat twice more when the selected hit targets an actually stunned enemy; each repeat uses the corresponding listed main-hit multiplier once. Static Physical Assault and Disorder use the standard single-character 100% buildup assumption and NoCrit. Potential's Super Furry Mark is a separate Physical Direct event at 30% of Nekomata's current ATK for each selected Nekomata Direct hit while the current Pounce state is active; the calculator does not replay its one-second cooldown or a timeline.

Core damage and Cinema stack effects use explicit current-state inputs. Cinema 1 applies to Nekomata's Direct Physical attack events: it reads the actual enemy-stunned state and otherwise requires the current event's back-hit condition, so the two routes cannot double the 16% Physical resistance ignore. The same unlocked Cinema 1 + actual stunned state also satisfies Steel Cushion's back-hit condition; the manual back-hit checkbox does not stack or override that fact. Cinema 2's Energy Gain Efficiency and Support Parry Daze curves remain source notes because the request has no Energy or Daze result. The catalog uses a neutral placeholder because the source `IconRole11` image is not packaged locally.

The existing Nanoka `14102` Steel Cushion record has catalog icon `Weapon_S_1021` and is exposed as Nekomata's signature selection; the S-rank default is R1. The real equipment-build path applies its level-60 white ATK/CR substat and separates the physical-damage bonus from the current back-hit damage bonus.

## Nicole (`character:1031`)

The complete live-3.2 source is retained at `core/data/characters/nicole.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1031.json`; this record declares no Potential variants. The level-60 panel includes +75 base ATK and +0.36 flat Energy Regeneration (`30501`, 36/100) from the raw extra-level record. The source signature mapping is the A-rank Treasure Chest `13103` (`Weapon_A_1031`), which defaults to R5; its level-60 build contributes 624 white ATK, +50% out-of-combat Energy Regeneration, and a separate current +0.8 flat panel effect while its Ether-trigger state is active.

The reviewed list keeps the exact Physical normal/enhanced Basic and Dash curves separate. The raw maximum of eight enhanced-ammo uses does not map to each multi-hit curve component, so an explicit current “enhanced ammo active” condition selects the exact enhanced curve without simulating a charge counter. Ether Dodge Counter, Special, EX cannon, Chain cannon, Ultimate cannon, Quick Assist, and Support Follow-up remain distinct from the Physical Basic/Dash entries. The explicit `A + {B/3}*3`, `/4*4`, and `/20*20` formulas are resolved as sums of the two raw curves once each, without multiplying the repeated component again.

Core Defense Down and its same-target Ether extra ability use an explicit current target state. Cinema 6 is an event-stat target Crit Rate modifier for Standard-Crit Direct/Penetration events; it does not alter formal character panels or NoCrit anomaly results. Per the user's A23 decision, EX tap totals include both cannon curves plus the full Energy Field total, and charged EX is a separate selectable total that adds its charge coefficient once. Chain and Ultimate likewise add their cannon and full field totals once; no duration, tick, range, or hit count is modeled. At skill level 12 these totals are 12.048% (tap EX), 16.354% (charged EX), 9.876% (Chain), and 30.402% (Ultimate). At level 16 they are 14.24%, 19.33%, 11.676%, and 35.930%. A24 retains one normal/enhanced ammo state across Basic and Dash and does not simulate the 0–8 reload count. C2/Ultimate Energy and Support Parry Daze remain source notes because the current request has no Energy/Daze result. The catalog uses a neutral placeholder because `IconRole12` is not packaged locally.

## Soldier 11 (`character:1041`)

The complete live-3.2 source is retained at `core/data/characters/soldier11.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1041.json`. The source identifies 「11号」 as an Attack character with Fire as her base element; source rarity value 4 is represented as S rank in the project catalog. The level-60 panel is normalized from its growth and extra-level records; +75 base ATK and +14.4% Crit Rate are included in the level-60 baseline. `Weapon_S_1041` identifies `wengine:14104` 硫磺石 as the reviewed signature and it follows the S-rank R1 default.

The reviewed baseline maps four Physical Warmup Basic stages, four Fire Fire-Suppression Basic stages, Physical and Fire Dash attacks, Fire Dodge Counter, Special, EX Special, Chain, Ultimate, Quick Assist, and Support Follow-up from their own raw parameter IDs. Potential 1–6 exposes the source's fifth Basic stage, enhanced fifth stage, and Fireburst move; the enhanced fifth-stage multiplier is its source base curve plus the selected current Potential Fire-Suppression use count times its extra curve. Core damage, Extra Ability Fire damage, the actual enemy-stunned bonus, Cinema 2 current damage stacks, Cinema 6 current charges, and Potential crit-damage effects use their respective event or panel scopes. Fire Anomaly and Disorder use the calculator's static 100%-buildup and NoCrit model. The catalog uses the neutral placeholder because `IconRole05` is not packaged locally.

## Yidhari (`character:1051`)

The complete live-3.2 source is retained at `core/data/characters/yidhari.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1051.json`. Yidhari is registered as an S-rank Rupture agent with Ice as her base element. Her reviewed Ice skill curves use the Penetration calculator, so their base uses current Force and their breakdown does not include enemy Defense. Core adds 0.1 current-Max-HP Force on top of the generic 0.25 current ATK + 0.1 current Max HP formula. The R1 Kraken's Cradle (`14105`, `Weapon_S_1051`) is the reviewed signature and its level-60 build path is covered.

The source review maps the three Shattered Strike stages and derived first-stage curve, four selectable Frost-Covering charge curves, Dash/Counter, Special/EX/Pursuit/Polar Crush, Chain with/without Veil, Ultimate, Quick Assist, and Support Follow-up. Static Ice Anomaly and Disorder use NoCrit. Cinema 1 Ice resistance ignore, Cinema 2 Crit Damage, Cinema 4 Veil max-HP, Cinema 6 Insight Penetration bonus, and the additional-ability eligibility/current low-HP conditions retain separate rules.

## Velina (`character:1561`)

The complete Nanoka live-3.2 detail is retained at `core/data/characters/velina.json` from `https://static.nanoka.cc/zzz/3.2/zh/character/1561.json`; the source declares no Potential details. Nanoka rarity value 4 is represented as S rank in the project catalog. Level-60 base stats include the source +75 base ATK and +54 anomaly proficiency ascension value. Her reviewed signature is W-Engine `14156` (`Weapon_S_1561`, 无懈之礼).

The reviewed Direct list uses each basic, dodge, special, chain, ultimate, and assist source skill curve. The Broad Cyclone's source-defined Wind or infused tick is represented by one selected element and 10 repeated source ticks; Wind and the infused value are alternatives, not additive. The micro/broad EX body damage and their separate Discharge-on-dissipation effects are kept as different typed events. A non-Wind Disorder on a currently Weathered target can generate Velina's Wind-triggered Turbulence using the actual non-Wind history record; that result replaces the ordinary Disorder result, and competing Turbulence candidates are not summed.

The Core's initial Energy Regeneration effect uses whole 0.01 steps above 1.2, capped independently at +35% damage and +84 Anomaly Mastery. It reads the initial panel, including equipment advanced stats; 2.16 yields 96 steps. Core Turbulence bonus and micro/broad Discharge rates use the compiled Core level. Extra Ability/Cinema damage scopes, C1 resistance ignore, C4 attack buff state, and C6 current Weathering remaining-time bonus have separate rules and owner/event filters. Winded-state +10% Wind Direct/Penetration damage uses the special-independent region; it does not enter the normal damage bonus region.

The calculator retains Daze, buildup, resource gains, cooldowns, and durations as source data without replaying them. The source says an infused Cyclone deals the corresponding infused attribute, but does not enumerate whether Luminance or attribute variants can be infused; the current choice field exposes the five ordinary non-Wind attributes only. No ordinary Wind Disorder entry is created because the calculation specification says Wind Weathering does not enter ordinary Disorder.

## Anton (character:1111)

The preserved live Nanoka 3.2 record is core/data/characters/anton.json with source URL https://static.nanoka.cc/zzz/3.2/zh/character/1111.json. Anton is an A-rank Attack agent with Electric as his base element and Belobog Heavy Industries as his source faction. The level-60 panel is normalized from the source, including +75 base ATK and +14.4% Crit Rate. The local 13111 record is Weapon_A_1111 旋钻机-赤轴; its description identifies Anton's modification. At level 60 it contributes 624 base ATK and 50% Energy Regeneration; its R5 80% Electric Basic/Dash bonus is a selectable current state and does not replay its cooldown. IconRole15 has no local portrait asset, so the catalog uses the neutral placeholder.

Direct entries retain source curve IDs separately from action IDs and preserve the Physical normal Basic/Dash/counter and Electric burst/skill/assist variants. The Core bonus is applied only to source-identified Pile Driver and Drill entries. The Assist Strike has one total curve for a Drill component followed by a Pile Driver finisher, without per-component ratios, so the two Core bonuses are not guessed for that aggregate. Cinema 4 Crit Rate and Cinema 6 burst Basic/burst Dodge Counter stacks are explicit current states; the 0–6 damage stacks default to their maximum when the rule is enabled. Electric Shock is modeled as a 125% per-second, 10-second static anomaly; Disorder uses 450% + floor(t) × 125% with a current 0–10-second remaining-time input.

The Additional Ability's known extra Shock coefficient is 45% of one 125% Shock tick. Its triggering state is selected explicitly without replaying the four-Crit history or 0.5-second interval. Source-record attribution and subsequent settlement ownership are still unresolved and block only that optional child event. Cinema 1 Energy recovery, Cinema 2 shield/incoming behavior, and Daze remain outside the current result contract.

## Ben (character:1121)

The preserved live Nanoka 3.2 record is core/data/characters/ben.json with source URL https://static.nanoka.cc/zzz/3.2/zh/character/1121.json. Ben is an A-rank Defense agent with Fire as his base element and Belobog Heavy Industries as his faction. His level-60 panel is normalized from the source: ATK 653.0866, DEF 724.0351, HP 8577.5504, Impact 95, and Energy Regeneration 1.56. The local 13112 record is Weapon_A_1121 比格气缸, whose description identifies Ben; its R5 advanced DEF and proc remain bound to real defense-role capabilities. IconRole16 is absent from local portrait assets, so the catalog uses the neutral placeholder.

The reviewed Direct set separates Basic stages, physical Dash, Fire Dodge Counter, Special active/counter alternatives, the four EX components, Chain, Ultimate, Quick Assist, and Assist Strike. The optional EX main-plus-follow-up and guard-counter-plus-follow-up totals add only their explicitly named source curves once; the regular Special active hit and successful guard-counter are alternative branches, not a summed sequence. Static Fire Burn uses 50% of anomaly effect strength per 0.5-second tick for 20 ticks; Fire Disorder uses 450% + floor(t/0.5)×50% with current remaining time as an input. No shield value, incoming damage, Energy, Support Point, or Daze result is fabricated. Cinema 4 counter bonus and the Additional Ability's shield-conditioned team Crit are explicit current states.

Koleda cooperation is selected from actual team membership: at Potential 0 Koleda's Enhanced Basic stage 2 uses the coordinated curve, while Potential 1 separates the standard stage 2 from the Ben-coordinated branch that requires the first-stage no-switch state. Her Special/EX quick-cooperation state remains separate, and her Ultimate uses its team-coordinated source curve when Ben is in the team.

Two local calculation limits remain pending user clarification. Ben's Core states that Initial ATK gains 80% of Initial DEF, but the user is deciding whether the conversion belongs in the out-of-combat panel or a combat layer. Cinema 2 states a known 300% current-DEF counter extra hit, but its child element/Crit/tag inheritance and EX follow-up occurrence are not explicit; the affected child stays unresolved while parent counter damage remains available. Core shield capacity and incoming effects, Cinema 1 Energy, and Cinema 6 Daze remain outside the current output contract.

## Soukaku (`character:1131`)

The live Nanoka 3.2 record is retained at `core/data/characters/soukaku.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1131.json`. Soukaku is an A-rank Support agent with Ice as her base element and no Potential variants. The catalog uses the neutral portrait placeholder because `IconRole17` is not packaged locally. The local A-rank engine `13113` (`Weapon_A_1131`, 含羞恶面) is mapped as her signature and remains unequipped by default.

The reviewed damage entries retain Physical normal Basic/Dash separately from Ice Frost Banner Basic/Dash, then map Counter, Special/flag components, EX windfield/continuous source components, Chain, Ultimate, Quick Assist, and the explicit Assist Strike curve sum. The normal Special's windfield and finisher each appear once in its complete entry. The EX continuous parameter is divided by 2 as the raw description requires; its multi-click total is not inferred. Static Physical Assault, Ice Shatter, and Ice Disorder use the shared static-anomaly source model.

The Core's self attack buff uses Initial ATK × the level-specific coefficient, capped at 500; consuming Vortex adds one matching capped increment to model the source's doubling to 1000. The text also transfers this buff to the corresponding entrant through Flag-triggered Quick Assist/Chain, but does not define persistence or simultaneous holders. Cinema 4 is an Ice/Lieshuang target resistance-reduction state, while Cinema 6's +45% applies only to the Frost Banner enhanced Basic/Dash templates. Cinema 1 duration, Cinema 2 random Vortex/Energy behavior, and Defense Assist Daze are source-only; none is converted to a damage or time simulation.

## Lycaon (`character:1141`)

The live Nanoka 3.2 record is retained at `core/data/characters/lycaon.json` with source URL `https://static.nanoka.cc/zzz/3.2/zh/character/1141.json`. Lycaon is an S-rank Stun agent with Ice as his base element and Victoria Housekeeping as his faction. `IconRole18` is not packaged locally, so the catalog uses the neutral placeholder. The local engine `14114` is `Weapon_S_1141` 拘缚者 and remains unequipped by default.

Normal Basic stages and Dash use the source Physical curves; all mapped Physical hits have zero attribute-infliction, so no Physical anomaly record is generated. Charged Basic tiers, Dodge Counter, Special/EX, Chain, Ultimate, and Assist entries use their source Ice curves. Special and EX source descriptions explicitly sum their components. Potential 1 exposes Ice Dance and selectable Hunt Basic/Counter follow-up sequences; the static calculator does not generate them from another teammate's move history. Potential 2–6 applies the source 5/7.5/10/12.5/15% Impact bonus only when the user selects the current Hunt off-field state.

Core Ice RES reduction is represented as a current target state and applies to all Ice/Lieshuang damage once active. The Potential Core's +30% other-element enemy vulnerability excludes Ice/Lieshuang. The Additional Ability uses the actual stunned-enemy state and adds 35% Stun vulnerability when its team eligibility is met. Cinema 6 exposes a current 0–5 damage-bonus stack; the calculator does not replay stack-building, timers, Energy, shield, incoming damage, or Daze.
