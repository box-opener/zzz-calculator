# Damage entry coverage (non-authoritative)

This is a presentation-coverage record for the 15 characters currently supported by this repository. It does not define game semantics. A selectable standalone entry is added only when the source gives a usable damage basis; damage that belongs to a selected move remains visible as an event under that move instead of being counted twice.

| Character | Independently selectable damage | Damage kept under its source move or remaining source requirement |
| --- | --- | --- |
| 雅 Miyabi | 霜灼·破 (`move-entry:character:1091:frostburn-break`). | C6霜月前序斩击仍随霜月条目结算，沿用该招式的来源身份与蓄力段数。 |
| 仪玄 Yixuan | 额外能力落雷和C1落雷，都是玄墨贯穿伤害；不添加MoveId、SkillGroup或DamageTag。额外能力项要求当前满足资格并选择极限支援换下场状态。 | 霄云劲第五段、阵法震击、强化特殊追加符箓等保留在各自源招式的结果里；源事件的独立实例仍按每个命中计算。 |
| 卢西娅 Lucia | 梦境追加攻击（合唱），保留FOLLOW_UP_ATTACK标签但没有MoveId或SkillGroup。 | 合唱的HP末段组件、终结技启动与一次冲撞依各自已确认的父条目结算。 |
| 耀嘉音 Astra | 终曲追加震音、音簇；保留源中明确的Tremolo/Cluster标签和震音技能组，但不造MoveId。音簇保留三次重复。 | 额外能力、入场、影画产生的同类震音/音簇及C4入场伤害，仍在其实际终曲/入场来源事件中派生。 |
| 猫又 Nekomata | 潜能达到1级时可独立选择超凶爪印；以猫又当前攻击力30%结算，不添加MoveId或标签。 | 潜能失衡重复攻击作为各自源普通攻击的额外事件；随机分支不实现。 |
| 爱丽丝 Alice | C6决胜状态额外攻击可选择并按当前层数/次数结算。核心周期伤害也有选择项，但请求目前缺少原文要求的已结算前序伤害ID，故准确返回partial。 | C6额外攻击仍可由决胜状态内的直接攻击命中派生。周期伤害比例读取指定历史事件的最终伤害，不能以当前攻击力、异常强度或本次新攻击代替。 |
| 薇薇安 Vivian | 异放（薇薇安当前面板）独立结算；每个当前队伍来源角色/元素单独显示，不相加进同一战斗总伤。预言单跳可按用户显式次数独立结算。 | 羽毛追击落羽生花仍由实际合法异常触发来源产生；属性混合的未审分支保持局部诊断。 |
| 叶瞬光 Ye Shunguang | 无新增独立入口。 | 归尘、斩妄开天末击额外组件依源招式命中显示；它们沿用同一末击来源，不伪造独立招式。 |
| 柚叶 Yuzuha | 无新增独立入口。 | 强力炮弹、彩糖花火在其合法触发命中下派生，保留各自子事件。 |
| 扳机 Trigger | 无新增独立入口。 | 断离和破甲凶弹作为对应触发命中的派生伤害，保留在源事件结果中。 |
| 照 Zhao | 无新增独立入口。 | 三个蓄力最大生命值追加段是指定技能终结命中的伤害组件，随普通攻击、连携或支援突击对应末段展示。 |
| 青衣 Qingyi | 现有所有已支持直接伤害条目可选；无额外独立伤害模板。 | 本次没有已知自闭合派生伤害需要新增独立入口。 |
| 琉音 Dialyn | 无新增独立入口。 | C6余音伤害由真实唯一持有人当前Direct/Penetration命中派生；无法从当前队伍操作顺序推定持有人。 |
| 妮可 Nicole | 现有直接伤害、强击、紊乱条目可选；无额外独立伤害模板。 | 能量场总倍率按已确认静态组件相加；不由持续时间推断跳数。 |
| 安比 Anby | 现有普通攻击、闪避反击、特殊/强化特殊、连携、终结和支援伤害可选；无独立派生伤害模板。 | C6的当前充能消耗一次增伤属于已选招式的倍率修正，不作为重复子事件。 |

The Alice periodic selection is intentionally not reported as a complete damage calculation. The typed base source requires `event:alice:1401:periodic-source`, while the one-selected-move request contains no such settled result. A future request contract may supply that result; until then the entry shows the missing source diagnostic and preserves the known main calculation paths.
