# W-Engine implementation progress (non-authoritative)

This is a resumable queue, not a game-semantics source. Ordering is the insertion order of the live Nanoka 3.2 W-Engine catalog object fetched from
`https://static.nanoka.cc/zzz/3.2/weapon.json` on 2026-10-02. The engine detail records use the already verified live-3.2 route
`https://static.nanoka.cc/zzz/3.2/zh/weapon/{id}.json`.

The index contains 100 entries. The current loader and reviewed mapping cover all 100 matching IDs, with no raw-only or reviewed-mapping-only IDs. The original 15 fixtures remain unchanged and retain their legacy source metadata. The other 85 engines keep complete live detail payloads and separate source-index URLs. The adapter closes the reviewed W-Engine slice at level 60 and includes Refinement 1–5 values. Non-60 build levels remain an explicit missing-data diagnostic, not a range silently approximated from level-60 values.

The rows marked “已实现” have a raw fixture, reviewed mapping, and compiler branch. Refinement values are selected from their own raw refinement text. Rows marked “部分实现” preserve known Build/Rule behavior and identify capability-ineligible branches, unmodeled timing/history, or result types outside the current damage-request contract.

| Nanoka order | ID | Chinese catalog name | Rank | Specialty | Current state |
|---:|---:|---|:---:|---|---|
| 001 | `12001` | 「月相」-望 | B | 强攻 | 已实现（live raw + reviewed + level-60 Build/Rule + R1–R5 + payload） |
| 002 | `12002` | 「月相」-晦 | B | 强攻 | 已实现（raw + reviewed + conditional wearer damage bonus + R1–R5 + payload） |
| 003 | `12003` | 「月相」-朔 | B | 强攻 | 部分实现（raw + Build + R1–R5；一次性能量回复有资源结果缺口诊断） |
| 004 | `12004` | 「残响」-Ⅰ型 | B | 支援 | 已实现（raw + reviewed + TEAM冲击力panel + R1–R5 + non-stack处理） |
| 005 | `12005` | 「残响」-Ⅱ型 | B | 支援 | 已实现（raw + reviewed + TEAM掌控/精通panel + R1–R5 + non-stack处理） |
| 006 | `12006` | 「残响」-Ⅲ型 | B | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 007 | `12007` | 「湍流」-铳型 | B | 击破 | 部分实现（raw + Build/EX失衡modifier + R1–R5；Daze结果有非阻断诊断） |
| 008 | `12008` | 「湍流」-矢型 | B | 击破 | 部分实现（raw + Build/主要目标失衡modifier + R1–R5；Daze结果有非阻断诊断） |
| 009 | `12009` | 「湍流」-斧型 | B | 击破 | 已实现（raw + SELF冲击panel active状态 + R1–R5） |
| 010 | `12010` | 「电磁暴」-壹式 | B | 异常 | 已实现（raw + SELF异常掌控panel active状态 + R1–R5） |
| 011 | `12011` | 「电磁暴」-贰式 | B | 异常 | 已实现（raw + max-star成长AP白值60 + SELF异常精通panel active状态 + R1–R5） |
| 012 | `12012` | 「电磁暴」-叁式 | B | 异常 | 部分实现（raw + 穿透率Build；能量回复结果缺口诊断） |
| 013 | `12013` | 「恒等式」-本格 | B | 防护 | 已实现（raw + DEF%Build + 受击后SELF防御panel + R1–R5） |
| 014 | `12014` | 「恒等式」-变格 | B | 防护 | 部分实现（raw + DEF%Build；敌人对玩家伤害结果缺口诊断） |
| 015 | `12015` | 「灰烬」-钴蓝 | B | 命破 | 已实现（raw + HP%Build + 接战后SELF攻击panel + R1–R5） |
| 016 | `12016` | 「月相」-弦 | B | 锋御 | 部分实现（raw + 白DEF/DEF%Build + 普攻条件增伤编译；无已注册Vanguard角色） |
| 017 | `13001` | 街头巨星 | A | 强攻 | 已实现（raw + ATK%Build + ULT当前充能0–3增伤 + R1–R5） |
| 018 | `13002` | 时光切片 | A | 支援 | 部分实现（raw + 穿透率Build；喧响/能量资源结果缺口诊断） |
| 019 | `13003` | 雨林饕客 | A | 异常 | 已实现（raw + AP白值成长 + 当前攻击层数0–10 panel + R1–R5） |
| 020 | `13004` | 星徽引擎 | A | 强攻 | 已实现（raw + ATK%Build + 当前触发状态panel + R1–R5） |
| 021 | `13005` | 人为刀俎 | A | 击破 | 已实现（raw + 能量自动回复Build + 当前能量层数0–8冲击panel + R1–R5） |
| 022 | `13006` | 贵重骨核 | A | 击破 | 部分实现（raw + 成长后Impact Build + 目标血量分支Daze规则 + R1–R5；Daze结果非阻断诊断） |
| 023 | `13007` | 正版变身器 | A | 防护 | 已实现（raw + HP% Build + 常驻HP/受击后Impact状态 + R1–R5） |
| 024 | `13008` | 双生泣星 | A | 异常 | 部分实现（raw + ATK% Build + 当前异常精通层数0–4 + R1–R5；层数时间轴非阻断诊断） |
| 025 | `13009` | 触电唇彩 | A | 异常 | 部分实现（raw + AP75 Build + 场上异常攻击力/目标异常增伤；跨目标范围分支局部诊断） |
| 026 | `13010` | 兔能环 | A | 防护 | 已实现（raw + HP/DEF Build + HP/护盾下攻击力 + R1–R5） |
| 027 | `13011` | 春日融融 | A | 防护 | 部分实现（raw + ATK% Build + 结果类型源Rule；受伤/能量效率无结果诊断） |
| 028 | `13012` | 幻变魔方 | A | 命破 | 已实现（raw + ATK% Build + EX后暴伤状态/低血目标EX增伤 + R1–R5） |
| 029 | `13013` | 鎏金花信 | A | 强攻 | 已实现（raw + ATK% Build + 强化特殊技增伤 + R1–R5） |
| 030 | `13014` | 电波漫步 | A | 命破 | 已实现（raw + HP% Build + 贯穿力当前层数0–3 + R1–R5） |
| 031 | `13015` | 强音热望 | A | 强攻 | 已实现（raw + 暴击率Build + EX/连携攻击增益与异常目标额外当前状态 + R1–R5） |
| 032 | `13016` | 光影刻刀 | A | 防护 | 部分实现（raw + Impact Build + 结果类型源Rule；受伤/秽息无结果诊断） |
| 033 | `13017` | 喵运当头 | A | 锋御 | 部分实现（raw + 白DEF/DEF%Build + EX后当前防御增益；无已注册Vanguard角色） |
| 034 | `13018` | 咚哒回声 | A | 异常 | 部分实现（raw + AP75 Build + 异常目标伤害；乱流后能量结果诊断） |
| 035 | `13019` | 青漪灵鼎 | A | 命破 | 部分实现（raw + HP%Build + 当前叠层伤害/满层暴击率；层数时间轴非阻断诊断） |
| 036 | `13020` | 炎炙沸釜 | A | 击破 | 部分实现（raw + Impact Build + 支援突击状态Daze/普通增伤；Daze结果非阻断诊断） |
| 037 | `13021` | 血髓秘匣 | A | 锋御 | 部分实现（raw + 白DEF/暴击率Build + 当前暴击率超100%增伤；无已注册Vanguard角色） |
| 038 | `13101` | 德玛拉电池Ⅱ型 | A | 击破 | 部分实现（raw + Impact Build + 电伤 + 能量效率当前态源Rule；资源结果诊断） |
| 039 | `13103` | 聚宝箱 | A | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 040 | `13106` | 家政员 | A | 强攻 | 已实现（raw + ATK%Build + 非当前操作角色的后场能量自动回复/当前物理层0–15 + R1–R5） |
| 041 | `13108` | 仿制星徽引擎 | A | 强攻 | 已实现（raw + ATK%Build + 远距触发当前物理增益，后续同持有人物理招式适用 + R1–R5） |
| 042 | `13111` | 旋钻机-赤轴 | A | 强攻 | 部分实现（raw + 能量回复Build + Basic/Dash电伤分支；登记强攻角色不含电属性） |
| 043 | `13112` | 比格气缸 | A | 防护 | 部分实现（raw + DEF%Build + incoming结果源Rule + 受击追击触发的防御额外伤害局部身份诊断） |
| 044 | `13113` | 含羞恶面 | A | 支援 | 部分实现（raw + ATK%Build + Ice bonus capability-gated + 全队当前攻击层数0–4/non-stack） |
| 045 | `13115` | 好斗的阿炮 | A | 支援 | 部分实现（raw + 能量自动回复Build + 全队当前攻击层0–4/non-stack；资源结果无输出） |
| 046 | `13127` | 维序者-特化型 | A | 防护 | 已实现（raw + ATK%Build + 护盾下flat能量自动回复 + EX/支援突击积蓄效率） |
| 047 | `13128` | 轰鸣座驾 | A | 异常 | 已实现（raw + ATK%Build + 三类独立随机结果current-state：攻击、AP、积蓄） |
| 048 | `13135` | 裁纸刀 | A | 击破 | 部分实现（raw + Impact Build + 追击触发后的Physical/Daze增益；Daze结果非阻断诊断） |
| 049 | `13142` | 震元奇枢 | A | 防护 | 部分实现（raw + ATK%Build + EX/ULT伤害标签范围；能量回复结果诊断） |
| 050 | `13144` | 燔火胧夜 | A | 命破 | 部分实现（raw + HP%Build + Fire伤害能力门控 + HP下降后暴击状态；当前登记命破角色无Fire） |
| 051 | `14001` | 加农转子 | A | 强攻 | 部分实现（raw + CritRate Build + ATK%面板；暴击触发额外伤害的必要子事件局部身份诊断） |
| 052 | `14002` | 逍遥游球 | A | 支援 | 已实现（raw + EnergyRegen Build + 属性克制后目标暴击率event-stat/non-stack） |
| 053 | `14003` | 左轮转子 | A | 击破 | 部分实现（live raw + Impact Build + EX当前充能失衡修正；Daze结果缺口非阻断） |
| 054 | `14102` | 钢铁肉垫 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 055 | `14104` | 硫磺石 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 056 | `14105` | 海妖摇篮 | S | 命破 | 已实现（Ice贯穿独立区能力门控 + 半血Crit面板 + HP Build + R1–R5） |
| 057 | `14107` | 奔袭獠牙 | S | 防护 | 部分实现（Impact Build + 全队当前伤害/失衡状态；护盾与Daze结果缺口非阻断） |
| 058 | `14109` | 霰落星殿 | S | 异常 | 部分实现（CritDamage面板 + 当前冰伤层能力门控 + CritRate Build + R1–R5） |
| 059 | `14110` | 燃狱齿轮 | S | 击破 | 已实现（后场自动回复结构门控 + EX当前Impact层 + Impact Build + R1–R5） |
| 060 | `14114` | 拘缚者 | S | 击破 | 部分实现（Basic普通增伤/失衡当前层 + Impact Build；Daze结果缺口非阻断） |
| 061 | `14116` | 焰心桂冠 | S | 击破 | 已实现（快速/极限支援Impact状态 + 目标当前萎靡层事件暴伤 + R1–R5） |
| 062 | `14117` | 灼心摇壶 | S | 异常 | 已实现（后场结构门控 + 当前伤害层 + 独立AP增益有效状态 + ATK Build + R1–R5） |
| 063 | `14118` | 嵌合编译器 | S | 异常 | 已实现（ATK面板 + 当前AP层 + 穿透率Build + R1–R5） |
| 064 | `14119` | 深海访客 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 065 | `14120` | 残心青囊 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 066 | `14121` | 啜泣摇篮 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 067 | `14122` | 时流贤者 | S | 异常 | 部分实现（Electric积蓄能力门控 + 命中异常目标AP面板状态 + 当前AP门槛紊乱增伤 + ATK Build + R1–R5） |
| 068 | `14124` | 防暴者Ⅵ型 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 069 | `14125` | 玉壶青冰 | S | 击破 | 已实现（Impact当前0–30层 + 独立15层触发的全队伤害状态 + R1–R5） |
| 070 | `14126` | 淬锋钳刺 | S | 异常 | 已实现（异常精通Build + Physical当前层 + 满层积蓄效率 + R1–R5） |
| 071 | `14129` | 千面日陨 | S | 强攻 | 部分实现（CritDamage面板 + 冰伤触发无视防御状态；当前强攻角色无冰伤能力） |
| 072 | `14130` | 嚣枪喧焰 | S | 强攻 | 部分实现（CritRate面板 + 追击火伤后的无视防御层；当前强攻角色无火伤能力） |
| 073 | `14131` | 玲珑妆匣 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 074 | `14132` | 心弦夜响 | S | 强攻 | 部分实现（CritDamage面板 + Chain/Ultimate火伤抗性无视层；当前强攻角色无火伤能力） |
| 075 | `14133` | 飞鸟星梦 | S | 异常 | 已实现（Anomaly Buildup Efficiency + 以太触发AP当前层 + AP Build + R1–R5） |
| 076 | `14134` | 半糖雪兔 | S | 防护 | 已实现（HP%Build + 单独Energy flat + TEAM ATK/HP + Zhao帷幕CritDamage状态） |
| 077 | `14136` | 索魂影眸 | S | 击破 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 078 | `14137` | 青溟笼舍 | S | 命破 | 已实现（CritRate + Ether普通伤/EX或ULT贯穿独立层 + HP%Build + R1–R5） |
| 079 | `14138` | 牺牲洁纯 | S | 强攻 | 部分实现（CritDamage Build/当前层 + 满层Electric伤；当前强攻角色无电伤能力） |
| 080 | `14139` | 福虓炉炉 | S | 击破 | 部分实现（EX/Chain/ULT Daze + TEAM伤害当前层；Daze非阻断、当前击破角色无火伤能力） |
| 081 | `14140` | 十方锻星 | S | 异常 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 082 | `14141` | 狸法七变化 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 083 | `14143` | 云霓孤光 | S | 强攻 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 084 | `14145` | 铸梦炉歌 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 085 | `14146` | 机巧心种 | S | 强攻 | 已实现（live raw + Build + 暴击率 + 当前层电伤/满层Basic与终结技无视防御 + R1–R5） |
| 086 | `14147` | 怒目金刚 | S | 命破 | 部分实现（raw + 暴击率 + 当前火贯穿伤害层；当前命破角色不具火伤能力） |
| 087 | `14148` | 昨夜来电 | S | 击破 | 部分实现（raw + 后场回复结构门控 + 当前物理强化特殊层/满层暴伤；Daze结果无输出） |
| 088 | `14149` | 思络成歌 | S | 支援 | 已实现（raw + reviewed + level-60 Build/Rule） |
| 089 | `14150` | 壳中之灵 | S | 异常 | 已实现（raw + 异常精通Build + 前场状态下异常目标/属性异常/紊乱各自伤害区） |
| 090 | `14151` | 霓虹妄想 | S | 击破 | 部分实现（raw + 常驻异常精通 + Ether Basic/EX触发层与满层精通；当前击破角色不具Ether能力） |
| 091 | `14152` | 鳞齿寻踪 | S | 强攻 | 部分实现（raw + Energy回复Build + Crit Rate面板 + 当前电伤无视防御；Energy触发历史不回放） |
| 092 | `14153` | 辉骑面铠 | S | 命破 | 部分实现（raw + 暴击率 + 当前物理贯穿伤害层；当前命破角色无物理伤能力） |
| 093 | `14154` | 朔月裁霜 | S | 异常 | 部分实现（raw + Ice伤害当前层 + 满层Discharge独立区；触发和计时以当前状态表示） |
| 094 | `14155` | 日冕遗蜕 | S | 强攻 | 部分实现（raw + 常驻暴击率 + Pellois专属以太抗性无视未映射到其他角色） |
| 095 | `14156` | 琳琅鎏心 | S | 异常 | 部分实现（raw + 常驻异常精通 + 当前风化/乱流层与满层TEAM精通；当前异常角色无风伤能力） |
| 096 | `14157` | 首席跟班 | S | 击破 | 部分实现（raw + 冲击力/暴击率/抗性与后场回复 + Fire EX触发TEAM层；Daze结果无输出） |
| 097 | `14158` | 空羽复归之诗 | S | 异常 | 部分实现（raw + 常驻异常精通 + 异化反应当前态下TEAM伤害和自身属性异常伤害；不增加紊乱伤害） |
| 098 | `14159` | 骁骑礼赞 | S | 强攻 | 已实现（raw + 暴伤当前层 + 满层冰抗性无视 + R1–R5） |
| 099 | `14161` | 猩红渴望 | S | 锋御 | 部分实现（typed DEF白值/DEF%Build + Crit Rate/电伤；Vanguard无角色注册，Sharp结果无结算节点） |
| 100 | `14162` | 绯月银棺 | S | 击破 | 部分实现（raw + 暴击率/风抗性无视 + TEAM_OTHER当前增益；Daze结果无输出且当前击破角色无风EX） |

The first seven W-Engine batches cover the pending catalog entries through `14139`; the final 15 rows were completed together. Previously supported IDs such as `12006`, `13103`, `14102`, `14104`, `14119`–`14121`, `14124`, `14131`, and `14136` remain included in the 100-entry catalog but were not rebuilt. The typed Vanguard entries `12016`, `13017`, `13021`, and `14161` have no registered character path.

The sixth batch uses the exact remaining Nanoka index entries `14003`, `14105`, `14107`, `14109`, `14110`, `14114`, `14116`, `14117`, `14118`, and `14122`; index rows 054–055 and 064–066 were already implemented and were skipped. All ten raw fixtures retain the full live-3.2 detail record and separate index URL. Their fixed level-60 advanced stats and R1–R5 values use each refinement's own source text.

`14003` exposes the current 0–6 charge count only on EX Special Daze. The request carries the modifier and a non-blocking Daze-result diagnostic; charge timing is not replayed. `14105` keeps its Ice Penetration bonus in the Penetration Damage lane and its half-HP Crit Rate as a separate SELF panel state. The currently registered Rupture agent has no Ice damage capability, so only that Ice branch is ineligible for that owner. `14107` applies the current team damage buff, and keeps shield-strength and Daze values typed with a non-blocking result limitation.

`14109` applies permanent Crit Damage and a current 0–2 Ice-damage stack state, capability-gated for Ice. `14110` derives backline eligibility from the owner's actual current-operator relationship, and accepts the 0–2 active EX Special Impact stacks. `14114` applies its current 0–5 stacks to Basic-tagged damage and preserves the Daze modifier; its same-move trigger cap and expiry are not replayed.

`14116` keeps the owner's support-triggered Impact state separate from the target's current Depression stack count. The latter is an enemy-target event Crit Damage modifier for standard-crit Ice/Fire Direct and Penetration damage, so it does not change formal panels or No-Crit results. `14117` likewise derives backline energy from current-operator structure. Its current damage stack count and the six-second AP-buff active condition are independent inputs: the source grants AP when gaining damage stacks at five or more, so later falling below five does not silently clear a still-active AP buff. Stack generation, the doubled backline rate, cooldown, and timers are not replayed. `14118` applies its Attack panel bonus and current 0–3 AP stacks.

`14122` gates Electric anomaly accumulation by owner capability, exposes the AP after a Special hit on an anomalous target as a current state, and checks the Disorder modifier against the owner's formal current AP, including active panel buffs. The registered Anomaly owner has no Electric damage capability; no Electric character is synthesized. The pure Disorder threshold reads the actual Disorder triggerer, not the record's historical contributors or the current operator. Its current-AP threshold is inclusive at 375.

The seventh batch follows rows 069–080 and skips already implemented `14131` and
`14136`; its ten IDs are `14125`, `14126`, `14129`, `14130`, `14132`, `14133`,
`14134`, `14137`, `14138`, and `14139`. Each raw fixture contains the complete
live-3.2 detail and source-index URL, and R1–R5 numeric values are stored from each
refinement's own source text.

`14125` applies the current 0–30 Tea Power stacks to the wearer's Impact panel. Its
team damage buff is a separate active state because it is triggered when a new
stack is acquired at 15 or more and can persist after the stack count falls. The
same-name team effect uses one stable group across holders and blocks mixed active
refinement values rather than choosing a copy. `14126` applies the current 0–3
Hunter's Intent stacks to Physical damage and applies Anomaly Buildup Efficiency
only at three selected stacks; it does not retest the current action as the
triggering Dash hit.

`14129` keeps its permanent Crit Damage panel from the three-second zero-degree
state that ignores Defense on subsequent owner hits. Its activation requires an
Ice-capable Attack owner, which the current Attack registry does not provide. `14130`
keeps its permanent Crit Rate panel separate from active Defense-ignore stacks after
a Fire Follow-up Attack; the current Attack roster has no Fire-capable owner. `14132`
limits active Fire resistance-ignore stacks to the owner's Chain/Ultimate Fire
damage; its Crit Damage panel is independent. `14133` adds its permanent Anomaly
Buildup Efficiency to owner buildup events and expresses Ether-triggered Anomaly
Proficiency as a current 0–6 panel stack. AP-stack eligibility requires Ether damage
capability.

`14134`'s level-60 advanced source property is HP% (`hp_percent`, +30% at max star),
not Energy Regeneration. Its R1–R5 Energy effect remains separate flat points per
second (+0.46 to +0.74). The team Attack/HP passive is a unique current panel group;
the 60-second team Crit Damage state is separately gated by the registered Zhao
Ether Curtain mechanism. `14137` uses separate ordinary Ether and EX/Ultimate Ether
Penetration lanes under the current 0–2 stack count. `14138` applies its current
0–3 stack Crit Damage to the panel; the additional Electric damage effect requires
an Electric-capable Attack owner, absent from the current registry. `14139` keeps
EX Special/Chain/Ultimate Daze in the Daze node, and its team damage stack applies
to current team damage after an eligible Fire Chain/Ultimate trigger. Daze has no
result lane, and no current Stun owner can produce that Fire trigger.

## W-Engine live 3.2 final batch (non-authoritative implementation notes)

The final source-order batch is `14146`, `14147`, `14148`, `14150`–`14159`, `14161`, and `14162`. All 15 fixtures retain the full live-3.2 detail payload and each Refinement 1–5 source description. The loader and reviewed mappings now cover all 100 index entries. The build adapter remains level-60 only; other levels return the existing missing-data diagnostic.

`14148` requires a physical EX Special for its physical-layer trigger. Owner capability eligibility is based on element/skill-group/tag combinations from the same reviewed move, so Qingyi's physical Dash and Electric EX do not combine into a fictional Physical EX. Dialyn's registered Physical EX capability remains eligible. For `14151`, the source says Ether EX Special **or** Basic Attack; those are evaluated as two alternative scopes, not as one event carrying both tags. The registered Stun owners currently have no Ether damage capability. `14157`'s Fire EX team effect likewise remains ineligible for Stun owners with no Fire EX.

`14150`'s current buff input represents the Ether owner's entry/Special trigger state; actual event bonuses require the owner to be the current operator because the source removes the buff after returning to the backline. Its anomalous-target normal damage, Attribute Anomaly, and Disorder effects retain separate conditions and lanes. `14158` is worded as an **异化** reaction, distinct from the separately named 异放 mechanic: its current buff state controls the owner Attribute Anomaly bonus and TEAM damage bonus. The owner also receives the unconditional AP passive. This source does not grant a Disorder bonus. Trigger and 30-second refresh history are not replayed.

`14151` includes the exact sentence `拥有2层效果时，装备者的异常精通额外提升96点，该效果全队唯一`. The compiler represents the currently known single-holder TEAM stack and full-stack owner AP. Whether the uniqueness phrase scopes only to the AP effect or to the composite stack effect cannot be established for multiple holders; that multi-holder interpretation remains unreviewed.

`14161` is retained as white Defense plus Defense-percent Build data, not Attack. It has no registered Vanguard owner. Its Electric Sharp damage bonus remains a typed source rule with a non-blocking limitation because the current request has no Sharp result lane; no Anomaly or Direct event is fabricated. `14162` retains the current TEAM_OTHER damage buff and excludes the holder. Its Daze modifier is typed with a non-blocking result limitation, and the currently registered Stun owners cannot produce Wind EX Special.
