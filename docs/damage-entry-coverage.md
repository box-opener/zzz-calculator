# Damage entry coverage (non-authoritative)

This is a presentation-coverage record for the supported reviewed characters. It does not define game semantics. A selectable standalone entry is added only when the source gives a usable damage basis; damage that belongs to a selected move remains visible as an event under that move instead of being counted twice.

| Character | Independently selectable damage | Damage kept under its source move or remaining source requirement |
| --- | --- | --- |
| 雅 Miyabi | 霜灼·破 (`move-entry:character:1091:frostburn-break`). | C6霜月前序斩击仍随霜月条目结算，沿用该招式的来源身份与蓄力段数。 |
| 仪玄 Yixuan | 额外能力落雷和C1落雷，都是玄墨贯穿伤害；不添加MoveId、SkillGroup或DamageTag。额外能力项要求当前满足资格并选择极限支援换下场状态。 | 霄云劲第五段、阵法震击、强化特殊追加符箓等保留在各自源招式的结果里；源事件的独立实例仍按每个命中计算。 |
| 卢西娅 Lucia | 梦境追加攻击（合唱），保留FOLLOW_UP_ATTACK标签但没有MoveId或SkillGroup。 | 合唱的HP末段组件、终结技启动与一次冲撞依各自已确认的父条目结算。 |
| 耀嘉音 Astra | 终曲追加震音、音簇；保留源中明确的Tremolo/Cluster标签和震音技能组，但不造MoveId。音簇保留三次重复。 | 额外能力、入场、影画产生的同类震音/音簇及C4入场伤害，仍在其实际终曲/入场来源事件中派生。 |
| 猫又 Nekomata | 潜能达到1级时可独立选择超凶爪印；以猫又当前攻击力30%结算，不添加MoveId或标签。 | 潜能失衡重复攻击作为各自源普通攻击的额外事件；随机分支不实现。 |
| 爱丽丝 Alice | C6决胜状态额外攻击可选择并按当前层数/次数结算。核心周期伤害也有选择项，但请求目前缺少原文要求的已结算前序伤害ID，故准确返回partial。 | C6额外攻击仍可由决胜状态内的直接攻击命中派生。周期伤害比例读取指定历史事件的最终伤害，不能以当前攻击力、异常强度或本次新攻击代替。 |
| 薇薇安 Vivian | 异放（薇薇安当前面板）独立结算；每个当前队伍来源角色/元素单独显示，不相加进同一战斗总伤。预言单跳按显式次数结算；新选择项缺省为1跳，用户显式0或其他次数不覆盖。 | 羽毛追击落羽生花仍由实际合法异常触发来源产生；属性混合的未审分支保持局部诊断。 |
| 叶瞬光 Ye Shunguang | 无新增独立入口。 | 归尘、斩妄开天末击额外组件依源招式命中显示；它们沿用同一末击来源，不伪造独立招式。 |
| 柚叶 Yuzuha | 6影强力炮弹（300% ATK/枚）与甜蜜惊吓追加彩糖花火·极分别可选；二者保留源中的物理属性、无MoveId/SkillGroup/DamageTag和同一显式当前枚数输入。 | 从「硬糖射击」触发的原派生仍由该父条目结算，独立选择不再重触发它们。 |
| 扳机 Trigger | 4影断离（200% ATK）与6影破甲凶弹（1200% ATK）分别可选。破甲凶弹仍受当前狙击架势和只作用于该精确弹体的50%普通增伤。 | 从协奏曲或普攻触发的原派生仍由父命中结算，独立选择不会递归创建自身。 |
| 照 Zhao | 无新增独立入口。 | 三个蓄力最大生命值追加段是指定技能终结命中的伤害组件，随普通攻击、连携或支援突击对应末段展示。 |
| 青衣 Qingyi | 现有所有已支持直接伤害条目可选；无额外独立伤害模板。 | 本次没有已知自闭合派生伤害需要新增独立入口。 |
| 琉音 Dialyn | 无新增独立入口。 | C6余音伤害由真实唯一持有人当前Direct/Penetration命中派生；无法从当前队伍操作顺序推定持有人。 |
| 妮可 Nicole | 现有直接伤害、强击、紊乱条目可选；无额外独立伤害模板。 | 能量场总倍率按已确认静态组件相加；不由持续时间推断跳数。 |
| 安比 Anby | 现有普通攻击、闪避反击、特殊/强化特殊、连携、终结和支援伤害可选；无独立派生伤害模板。 | C6的当前充能消耗一次增伤属于已选招式的倍率修正，不作为重复子事件。 |
| 潘引壶 Yinhu | 无独立派生伤害入口；15项Physical Direct招式均可单独选择。 | Core贯穿力加成由每位队友自己的当前持有状态显式控制，且仅用于该队友的Penetration事件；C6按完整Core系数与总cap替换基础分支。气绝状态的20%普通增伤和C1额外10%作用于敌方；不创建Anomaly或Disorder伤害。 |
| 真斗 Manato | 19项source-backed Physical/Fire招式条目可选择；普通攻击的烬风作为显式互斥的整次Fire伤害倍率。 | 连打最大支援突击保留1441024起手与1441025连续斩击总倍率两个事件；中间连打次数与比例未提供，不推导。C1历史损失HP作用于Basic Fire与Support Follow-up；消耗HP暴伤只作用于炽风·胧切及连续斩击事件。资源、时间、Energy、Daze及C4致命伤害恢复不生成静态伤害事件。 |
| 「席德」 Seed | Reviewed Basic 1–4、Heavy Strike、Falling Crash 1–2、Dash、Counter、Special/EX、Chain、Ultimate、Quick Assist与Assist Strike各自可选择；不展示Anomaly/Disorder。 | Core partner按其他Attack角色的unique highest Initial ATK选取；多候选需已组装初始面板，缺失或并列时不猜测。仅当对应recipient规则与当前状态条件同时生效时，候选dealer自身的相关结果才局部partial；Seed自身及不匹配的dealer仍可计算。Core/围杀的off-field持有人以当前状态输入；+25%普通增伤使用精确dealer身份。C6已知3×165% ATK激光保留在重戮source诊断下，但独立事件分类未知，不合成Direct事件。 |
| 千夏 Sunna | 14项reviewed Physical Direct招式可选择；不展示Anomaly/Disorder。坏猫自动攻击使用千夏Initial ATK。 | Core猫的凝视作为Direct派生事件，采用实际触发强攻/异常队友的ATK、暴击属性和原生属性，不继承父招式的MoveId、SkillGroup或DamageTag；Cinema 2只修改这些派生事件的倍率，Cinema 6额外伤害也只作用于猫的凝视。印记、协律、帷幕与影画状态均为当前场景输入；不模拟触发次数、持续时间或资源时间轴。 |
| 南宫羽 Nangong Yu | 15项reviewed Ether Direct招式、Ether Anomaly、Ether Disorder与Core异放可选择；Polar Disorder仅由当前有效的Direct触发入口派生。 | Core异放仅在所选Core entry满足当前触发条件且指定了真实队友的已编译普通异常记录时生成；保留记录的实际元素变体和异常强度。普通/C6异放倍率模式互斥，C2只加成普通模式。C2连携极性紊乱按本次连携重击的当前proc条件结算；普通异常记录查询不会自动生成极性紊乱。不模拟资源、Daze或时间轴。 |
| 般岳 BanYue | 24项source-backed Fire/Penetration entries可选择，按当前贯穿力结算；不展示自身Anomaly/Disorder。 | 摧岳派生倾山使用其自身1471009 Basic身份。C6 600%贯穿力火伤是独立Fire事件，但没有MoveId、SkillGroup或DamageTag，不继承摧岳身份；Core宽范围火属性贯穿增益仍适用，C1/C4只作用于明示招式。C6-only Mingwang的已知+8%可计算，Extra Ability基础+5%资格歧义仅局部partial。 |
| 爱芮 Aria | 19项Ether Direct招式、Ether Corrosion与Ether Disorder可选；记录仅在source-backed Ether/Xuanmo当前异常时长内计算。 | Core异放只由第三段蓄力普攻命中条件创建，倍率读取所选原异常记录并按初始异常掌控；C1独立暴击区只用于该异放。选择真实队友与已审异常模板，不自动合成没有模板的来源记录。Extra开启时以太侵蚀记录延长至13秒，关闭时为10秒；不模拟资源与时间轴。 |
| 希希芙 Cissia | 13项source-backed Electric Direct entries可选择；不展示自身Anomaly/Disorder。 | Basic 蛇吻下的基础蚀骨与Core额外攻击倍率共用1521019曲线；C4额外蚀骨按当前0–3层作为独立事件。C6只由当前标记状态下的主Direct/Penetration命中触发一次，排除中性派生段和所有蚀骨事件，且不继承触发招式身份。毒素、能量、触发间隔和资源时间轴不回放。 |
| 星徽·比利 Starlight - Billy | 17项reviewed Physical Penetration entries可选择；不展示自身Anomaly/Disorder。 | 四段普通攻击分别保留源曲线；最高马力独立可选。Core当前最大生命值贯穿力和各影画/额外能力仅作用于源明示面板、招式与状态。C6消耗星辉按当前0–2层给最高马力/终结技的整次贯穿倍率各加100%贯穿力倍率/层，同时其+18%贯穿伤害区独立结算，不创建重复子事件。三项招架支援只有失衡值，不建立伤害入口。 |
| 普罗米娅 Promeia | 17项reviewed Ice Direct招式、披风每秒曲线、重霜飞镖曲线、Ice Anomaly与Disorder可选择。 | Core异放只由当前绝裁末击创建；读取已选择真实普通异常来源，但保持固定type-2倍率，不乘来源tick profile。额外能力使普通Ice/Lieshuang霜寒记录分别从10/20秒延长到13/23秒，紊乱默认剩余时间随当前记录调整。资源消耗和30秒有罪推定刷新不回放。 |

The Alice periodic selection is intentionally not reported as a complete damage calculation. The typed base source requires `event:alice:1401:periodic-source`, while the one-selected-move request contains no such settled result. A future request contract may supply that result; until then the entry shows the missing source diagnostic and preserves the known main calculation paths.
