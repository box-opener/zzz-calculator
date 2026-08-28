# 计算器计算实现规范

本计算器是基于用户指定场景的静态伤害分析器，不是战斗模拟器。

程序只计算用户当前配置下某个招式、异常或派生伤害事件的结算结果，不负责验证该场景如何通过实际操作、资源循环、技能衔接或者时间轴达成。

静态计算场景不根据 State 的持续时间判断 Effect 是否仍然有效。只要对应计算规则项处于启用状态，其 Effect 在本次计算中视为有效。持续时间仍按领域模型归属于 State，但当前版本计算管线不消费该字段。用户可以通过规则项开关主动使该 Effect 退出计算管线。

对于仅影响事件能否发生、何时发生、经过何种操作发生，而不改变该事件最终倍率、伤害属性、伤害标签、伤害类型、参与乘区、有效 Modifier、历史记录内容或事件数量的机制，默认在这个版本不实现，不会加入计算管线，也不会显示在当前版本的前端页面上。

若某项机制仅决定多个合法计算分支中的哪一个成立，则应当将其转换为用户可选的场景条件，而不是实现战斗状态机。

Effect 条件首先尝试由当前角色、小队、装备、影画和敌人配置自动求值。

若当前配置能够唯一确定条件真假，则自动启用或禁用，不要求用户选择。

只有无法由静态配置唯一确定、但不同取值会改变正式计算结果的条件，才转换为用户可选场景条件。

## 技能归属与伤害标签

【闪避】是独立的 SkillGroup。【冲刺攻击】与【闪避反击】共同归属于【闪避】技能分类。

二者使用彼此独立的伤害标签：

- 冲刺攻击：`SkillGroup.DODGE` + `DamageTag.DASH_ATTACK`；
- 闪避反击：`SkillGroup.DODGE` + `DamageTag.DODGE_COUNTER`。

“闪避类招式造成的伤害提高”通过 `SkillGroupFilter(DODGE)` 同时匹配冲刺攻击与闪避反击。

“冲刺攻击伤害提高”只通过 `DamageTagFilter(DASH_ATTACK)` 匹配冲刺攻击；“闪避反击伤害提高”只通过 `DamageTagFilter(DODGE_COUNTER)` 匹配闪避反击。

冲刺攻击与闪避反击不会仅因使用普通攻击键发动而获得 `DamageTag.BASIC_ATTACK`，普通攻击伤害提高默认不作用于二者。

文本仅规定某招式“视为发动闪避”时，只保留对应的招式发动身份，不得自动将该招式的 SkillGroup 改为 `DODGE`，也不得自动添加 `DASH_ATTACK` 或 `DODGE_COUNTER` 标签。

## 前端与配置

计算器的视觉风格应当参考项目本地已有的前端实现风格，不得自创风格。

用户可以输入自己角色的 UID，然后程序会从米游社网页中获取用户的角色信息。该信息应当被正确保存在本地，以便随时调用。用户可以选择加载自己的角色或从零开始配置角色。

小队至多存在3名角色，用户可以主动配置当前操作角色。

用户从零开始配置角色的最小配置项为：

- 角色：等级、核心技等级、各技能等级、影画；
- 音擎：等级、精炼等级；
- 驱动盘：套装、主词条、副词条。

计算器应当为用户自动配置提供帮助，在用户选择一个角色时生成默认角色配置。

默认配置不携带驱动盘。若为S级代理人，则默认为0画；若为A级代理人，则默认为6画。全技能为满级，也就是全技能为12级（S）、16级（A）。3画代理人全技能+2，因此默认技能等级为14级。

代理人装备的武器默认为该角色专武，A级代理人携带精5武器，S级代理人携带精1武器。角色与专武使用显式的 `character_id → signature_weapon_id` 映射，不得根据展示名称或代号包含关系推断专武。

用户还可以配置：

- 敌人等级；
- 当前是否失衡；
- 各属性抗性、弱点；
- 与角色专属 Effect 有关的敌人状态。

未配置时使用目标怪物默认值，默认目标为“卫士II”。

当前操作角色为本次主计算对象。

队友 Effect 中：

- `target=self`：只作用于 Effect.owner，自身不是当前操作角色时不得应用；
- `target=team`：可以作用于当前操作角色；
- `target=enemy`：若对应敌人状态被启用，可以影响当前操作角色的计算；
- 动态身份按术语规范独立判断，不得因为 Effect 来源于队友而默认作用于当前操作角色。

用户可以导入、导出当前小队或当前操作角色配置的 JSON 文件。

## 计算规则项

前端统一将所有可能影响本次计算的规则来源展示为“计算规则项”。

计算规则项可以来源于：

- 核心被动；
- 额外能力；
- 影画；
- 音擎；
- 驱动盘；
- 招式自身规则；
- 队友提供的 Effect。

用户可以启用或禁用可选规则项。计算规则项应当显示名称和详细文本，名称即为其来源，详细文本为导出该规则项的游戏文本。

对于存在叠层效果的计算规则项，默认满层，但用户可以修改层数。

计算规则项的开关只允许用户将一个本来合法生效的规则主动排除出本次计算，用于静态场景选择和收益比较；不得通过开关使当前角色、小队、装备、影画、属性、职业、target 或动态身份判定下本来不合法的规则强制生效。

计算规则项本身只保存规则定义、合法性和 Effect 结果。某次计算是否启用的唯一来源是 `CalculationScenario.enabled_rule_item_ids`；不得同时读取规则项自身的 enabled 字段作为第二个启用状态。

`CalculationRuleItem.condition_ids` 控制整个规则项的场景成立条件；`EffectRule.condition` 只控制规则项内部的单个 Effect。二者不得互相替代。

`EffectRule.trigger` 匹配的是 `CalculationScenario` 中按 `effect_id` 保存的 `ScenarioTriggerFact`，表示此前触发该 Effect 的事件；它不得与当前正在结算的 DamageEvent 直接比较。当前 DamageEvent 的属性、技能归属、伤害标签和伤害类型只由 `EffectRule.filters` 匹配。

若规则需要限定某个独立派生事件的创建来源，可以使用显式的
`CreatedByEffectFilter`。该 Filter 只读取 Application 层从
`InstantiatedDamageEvent.created_by_effect_id` 传入的来源身份，不得通过伪造 `MoveId` 或由
调用方另传任意 provenance 字典替代。

Effect 存在 trigger 但场景没有对应 trigger fact 时，匹配结果为 BLOCKED；存在 trigger fact 但事件类型或招式不匹配时，匹配结果为 NOT_MATCHED。不能把缺少 trigger fact 当作 False。

Effect 的 target 与 filters 是独立判断轴。`target=enemy` 只表示 Effect 作用于敌人，不会禁止 Character、CharacterRole、FieldPosition 或 OperationState Filter 检查当前计算角色。

Effect 匹配采用 MATCHED / NOT_MATCHED / BLOCKED 三值逻辑。当 AND 已由 NOT_MATCHED 决定，或 OR 已由 MATCHED 决定时，其他不确定分支不得继续产生 blocking diagnostic。UnresolvedEffect 也必须先经过已知 target、trigger、condition 和 filters；若已知规则已使其与当前计算无关，则不阻塞本次计算。

能由静态配置唯一确定的结构性条件不可由用户覆盖；无法由静态配置确定的场景条件由用户输入决定。

用户关闭规则项只影响本次计算，不改变原始角色配置。

每一个计算规则项至少能够追溯：

- 稳定 ID；
- owner；
- source / source_type；
- 展示名称；
- 原始游戏文本；
- 当前是否合法；
- 当前是否启用（由 `CalculationScenario.enabled_rule_item_ids` 决定）；
- 若可叠层：当前层数及合法上下限；
- 其产生的 Effect / Modifier / EventCreation。

禁用某计算规则项时，由该规则项产生的所有 Effect、Modifier 和 EventCreation 均退出本次计算管线；不得只关闭其中一部分派生结果，除非原始规则本身包含可以独立选择的多个效果。

DamageEvent 本身不是 Buff 开关。EventCreation 类规则启用后可以改变本次计算所包含的 DamageEvent 数量。

主页面始终只展示当前操作角色的面板、招式和主计算结果。切换当前操作角色后重新计算。

当前操作角色的唯一真值来源为 `CalculationScenario.current_operator`。EffectMatchContext 等下游上下文不得再保存另一份可独立变化的 current_operator。

为构造异常历史记录、比较 disorder_trigger、wind_anomaly_trigger 等派生场景时，计算器可以建立临时 CalculationContext，并在该临时上下文中将指定角色视为操作角色。

临时上下文只用于该派生结果，不改变用户实际选择的当前操作角色，也不得污染其他计算结果。

## 数值展示

前端展示百分比增幅时，默认展示“相对于该计算节点默认值的增量”，而不是该节点最终乘区值。

例如：

```text
异常增伤 +20%
→ 计算节点值为 1.2
→ 前端显示 +20%

易伤 +30%
→ 对应加成显示 +30%
→ 不显示 1.3 或 130%
```

外部数据缺失不得默认按0处理。若缺失字段会改变正式计算结果，则对应结果标记为“数据不足，无法计算”，不得输出虚假数值。

已明确属于当前版本实现范围之外的机制直接忽略，不创建 Unresolved。

原始数据明显错误时忽略错误字段并记录数据问题，不围绕错误数据建立领域模型。

只有语义存在多种解释、且不同解释会改变当前版本正式计算结果时，才创建阻塞性 Unresolved 或要求人工确认。

语义存在歧义但当前版本下所有解释数值等价时，只保留非阻塞提示。

角色的局外面板和计算规则项生效后的局内面板分别展示。左侧展示局外面板，右侧展示局内面板。局内面板由局外面板和附加在局外面板上的绿色加号展示。鼠标移动到绿色加号时，应显示其来源计算规则项。

只有按本规范归入面板区域的真实局内面板属性变化，以及音擎或驱动盘来源的普通增伤，会显示在角色的局内面板加成上。角色技能、核心被动、影画和招式自身提供的事件级普通增伤显示为蓝色加成。

对于不显示在局内面板上的普通增伤，例如所有“造成的伤害提升”和对应招式增伤，应当以蓝色加号附加在局内面板的绿色加号上。鼠标移动到蓝色加号时，同样应显示其来源计算规则项。

对于独立伤害增幅，例如贯穿增伤、特殊独立区、异常增伤、异放增伤等，只有当前角色计算规则项存在对应增伤时才显示。这些增幅不归属局内或局外面板，应当在面板下单开一行显示百分比，并允许查看来源计算规则项。

总结：

- 绿色加成：面板区域中展示的局内加成，包括真实局内面板属性变化，以及按本规范归入面板区域展示的音擎、驱动盘来源普通增伤；
- 蓝色加成：不归入面板区域基础值，但进入普通增伤区的事件级修正；
- 独立行：进入其他独立计算节点的伤害修正。

显示命破角色面板时，局内和局外面板都需要增加贯穿力，展示逻辑与其他面板数据一致。

## 招式与 DamageEvent

同一个招式的同一主伤害只创建一个主 DamageEvent，不因多段 Hit 或三种暴击展示模式重复创建。

“不暴击伤害 / 期望伤害 / 全暴击伤害”是对同一 DamageEvent 使用三种展示用暴击结算模式得到的三个结果，不得为了展示三种暴击结果复制或改变 DamageEvent 的领域语义。

三种模式：

- 不暴击：暴击区按1结算；
- 期望：使用正式暴击期望公式；
- 全暴击：暴击区按 `1 + 暴击伤害` 结算。

该规则仅适用于具备普通暴击能力的伤害类型。

对所有招式伤害，第一版计算器默认使用数据库提供的完整招式倍率。即使技能文本描述该招式包含多段攻击，也不按 Hit 拆分，整个招式视为一个主伤害事件。只有规范明确要求创建独立 DamageEvent 的额外伤害才额外创建 DamageEvent。

主 DamageEvent 的倍率唯一来自 `MoveCalculationEntry.multiplier_variants`。主事件模板不得重复保存倍率；由 EventCreation 创建的派生 DamageEvent 可以在其独立模板中保存自己的倍率。

第一版计算器默认属性异常由单一指定角色独立完成100%的异常积蓄。

因此：

- 该异常记录的 contributors 只有该角色；
- anomaly_triggerer 为该角色；
- weighted_anomaly_effect_strength 等于该角色在当前场景下的异常效果强度；
- weighted_impact_strength 同理；
- 不需要技能级异常积蓄值；
- 不模拟异常条积蓄过程和溢出。

对于除了南宫羽以外的非异常角色，不显示其造成的异常伤害。

对于南宫羽和所有非流明属性异常角色，在显示所有招式伤害之外，还需要计算并显示：

- 该角色100%积蓄一管当前怪物异常条造成的属性异常伤害；持续跳字只显示单次跳字伤害，无持续跳字则显示触发时的单次伤害；
- 该异常按照最大持续时间被结算的紊乱伤害。

对于同一被结算异常记录，分别假设队伍中的每名角色为 disorder_trigger，重新判断所有“造成的紊乱伤害提升”和触发者专属减抗等动态效果，并分别计算紊乱伤害。主界面默认显示其中最高值并标注 disorder_trigger，其余候选结果允许展开查看。

当小队中存在可以触发异放的角色时，应当对小队中所有非流明属性异常角色和南宫羽计算对应异放伤害。存在多个异放触发来源时，应全部显示并标注异放来源。

当队伍中存在风属性角色时，计算器默认采用“由风属性角色触发对应非风异常后的乱流”作为该异常的派生结算场景，因此主界面的常规紊乱结果替换为乱流结果。

若存在多个合法 wind_anomaly_trigger，应分别计算乱流。主界面默认显示最高结果并标注触发者，其余结果允许展开查看。

当小队中存在流明属性角色时，流明属性没有异常积蓄和异常伤害，只有耀变。每名非流明属性队友均假定独立完成一管自身属性异常，并生成一个 Synthetic AnomalyRecord。是否属于异常职业不影响该规则。流明属性队友不生成普通异常历史记录。

记录规则如下：

```text
队友 A 作为操作角色时的面板
→ 假定 A 独立完成一管其属性异常
→ Synthetic AnomalyRecord A

队友 B 作为操作角色时的面板
→ 假定 B 独立完成一管其属性异常
→ Synthetic AnomalyRecord B

流明角色某招式
→ LuminanceDamageEvent(record=A)
→ LuminanceDamageEvent(record=B)
```

敌人的易伤区和抗性区也应当和角色面板一样，用蓝色数值标注受到角色计算规则项影响的部分，并允许查看来源。针对特定招式生效的减抗、增抗、增减易伤不应显示在通用敌人面板中。

敌人的防御区显示针对当前操作者的当前有效防御力，以及针对当前操作角色的实际防御区乘数。通用防御降低和无视防御用蓝色标明来源。只针对特定招式的防御区影响不在通用面板显示，只显示在对应招式计算详情中。

若招式创建了伤害事件，例如极性紊乱、决算等，即使底层引擎尚未定义、验证或完成，也应将这些伤害事件单独列出，查看规则与常规伤害事件保持一致。

一个招式可以包含一个主 DamageEvent 和零个或多个由 EventCreation 创建的独立 DamageEvent。

## 角色定义编译契约

角色数据进入计算管线前，必须由受审的角色编译器输出
`CharacterCalculationDefinition`。该对象是“角色原始数据 + Build 配置 + 已确认的
静态语义场景”的场景化编译结果，不是可跨不同配置或敌人场景复用的永久角色对象。
通用 Definition 本身不得保存任何具体角色的 CompileConfig；具体编译器只应将配置影响后的
结果写入通用字段，并由调用方保留原始编译输入。
以下任一输入改变时，旧 Definition 失效并应重新编译：技能等级、核心技等级、影画、会改变
事件语义的静态场景条件。敌人的失衡易伤数值和是否失衡属于本次 Calculation Request 的
结算环境，不得复制进角色 CompileConfig；帷幕上限属于角色编译语义，敌人的失衡易伤仍由
请求环境唯一提供。

原始角色记录与 reviewed semantic mapping 必须分层保存。原始记录只提供稳定的角色、招式、
参数和文本字段；SkillGroup、DamageTag、倍率关系、变种属性和场景条件等解释后的语义，必须
来自显式的人工审阅映射。第一版不得以正则或自然语言猜测替代该映射。
角色编译器必须同时接收 raw record 与 reviewed mapping；不得仅凭 reviewed mapping 中的
重复常量生成倍率或来源文本。

`CalculationRuleItem` 只保存规则定义、资格和 Effect；本次计算是否启用的唯一来源仍是
`CalculationScenario.enabled_rule_item_ids`。编译器可以为前端生成默认启用的 Scenario，
但不得把 `enabled` 字段重新放回 RuleItem。

编译期能够确定的角色语义条件必须输出为 `STATIC` `ScenarioCondition`，Scenario 不得覆盖；
改变这类条件必须重新编译。需要用户在本次计算中选择的条件输出为 `USER_SELECTED`。
单位倍率的次数只能引用 `ScenarioIntegerParameter`，不得引用布尔条件。

已结构化支持但当前影画等级未解锁的 RuleItem 必须保留，并标记为
`RuleEligibility.INELIGIBLE`；启用集合不得绕过该资格检查。改变帷幕易伤上限的影画属于
编译规则变化，不额外伪造一个独立的伤害 Effect。

`MoveId` 是可复用的招式语义身份，同一招式拆成多个阶段时可以由多个 MoveEntry 共用；
`MoveEntryId`、`RuleItemId`、`EffectId`、`ScenarioConditionId`、`ScenarioParameterId`、
`EventTemplateId` 和 `DamageEventSemanticId` 等稳定身份在其规定作用域内必须唯一。
`MoveIdFilter` 属于普通 AtomicFilter，可与其他 Filter 通过 AND、OR、NOT 组合。

主 DamageEvent 的倍率唯一来自其 `MoveCalculationEntry.multiplier_variants`；主事件模板不得
重复保存倍率。派生 DamageEvent 的倍率唯一来自对应的
`DerivedDamageEventTemplateRef`。EventCreation 产生的独立额外事件不得自动继承来源招式的
`move_id`、SkillGroup 或伤害标签，除非规范明确要求继承；因此其模板可以使用
`move_id=None`、空标签集合来避免被来源招式的规则再次匹配。

如果原始文本明确说明独立事件本身属于某个已确认的招式语义，reviewed compiler 可以显式
赋予对应的 `move_id`、SkillGroup 或标签；这必须是人工确认的事件身份，不得由 EventCreation
来源自动推断。

编译器对基础属性与变种属性的范围匹配必须显式展开。例如物理伤害增幅作用于物理和凛刃时，
输出 `AnyFilter(ElementFilter(PHYSICAL), ElementFilter(LINREN))`；Matcher 不得把精确的
`ElementFilter` 偷换成隐式的原属性匹配。

每个 DamageEvent 单独显示计算结果和乘区详情。若这些事件均属于同一次用户选择的招式结算，则同时显示“招式总伤害”，其值为该组中所有能够得到正式数值的 DamageEvent 结果之和。

不同 DamageEvent 分别使用各自适用的暴击、增伤、抗性、防御等规则，不得先合并倍率再计算。

若其中任一必要事件无法计算，是否仍展示“已知部分合计”需要明确标记，不得把部分结果冒充完整总伤害。

若解析结果明确要求创建一种 DamageEvent，但当前核心计算层尚未实现对应 Calculator，该事件仍应显示，并保留名称、来源文本、事件类型和已知参数；计算结果显示为“当前版本暂不支持计算”，不得忽略该事件、按0计算或将其并入其他 DamageEvent。该情况属于实现能力缺失，不等同于原始数据缺失。

“不暴击 / 期望 / 全暴击”三值展示仅用于 StandardCritRule。NoCritRule 的伤害只显示一个正式结果。具备独立异常暴击能力或历史继承异常暴击能力的事件，应按照该事件自身 CritRule 计算正式结果；第一版前端不强制为其生成普通攻击式的三值展示。

不得使用角色面板普通暴击率或暴击伤害替代异常事件自己的暴击规则。

## 应用执行层

`CharacterCalculationDefinition`、`CalculationScenario` 和基础快照进入计算器前，必须经过
应用执行层。执行层负责选择 Move、解析倍率、匹配 Effect、形成结算快照、创建派生事件，
然后才构造 `CalculationContext` 调用具体 Calculator。Calculator 不得自行读取 Definition、
Scenario、Character、Enemy 或 Buff 数据。

一次应用请求可以包含一个主 `CharacterCalculationDefinition` 和零个或多个
`supporting_definitions`。主 Definition 是当前 `MoveEntry` 的唯一来源；支援 Definition
只提供本次场景可用的 RuleItem、Effect 和派生事件模板。请求内的 RuleItem、Effect、事件模板
和 DamageEvent 语义身份必须在所有 Definition 合并后的作用域内唯一。

装备编译器产生的 `CalculationRuleItem` 和用户可选的装备场景条件，可以通过应用请求的
附加规则/条件集合进入同一匹配管线。它们不应伪装成一个重复的角色 Definition；装备规则
的 owner 仍然是装备角色，source 必须保留具体音擎或其他装备身份。

派生伤害模板有两种合法归属：招式自身的
`MoveCalculationEntry.derived_damage_events`，以及 Definition 级的
`independent_derived_damage_events`。后者用于由支援入场、队伍条件或其他不属于某个本角色
MoveEntry 的 RuleItem 创建的独立事件。两种归属中的模板和倍率均只能注册一次；不得为了满足
MoveEntry 结构伪造不存在的来源招式。

角色初始面板与结算面板是不同的数据层。需要从初始面板派生 Effect 数值时，应用请求必须
提供独立的初始角色快照，不得从已经包含 Panel Effect 的 settlement snapshot 反推。第一版
只支持受限的 `PanelStatDerivedValue`：读取指定角色的
`CHARACTER_INITIAL_ATTACK`，乘固定系数后应用可选上限。无法提供初始快照时必须产生
`MISSING_DATA`，不得回退到 settlement attack。

请求中的 `base_calculation_modifiers` 表示调用方已经确定的基础结算环境，不属于任何
`CalculationRuleItem`。例如敌人基础失衡易伤 `+150%` 应以
`ENEMY_STUN_VULNERABILITY + ADD 1.50` 传入。基础 Modifier 必须已经使用 `ADD`，且不得
包含角色面板节点。

应用层负责解释 Modifier operation。没有 `OVERRIDE` 时，同一节点的基础 ADD 与规则 ADD
共同汇总；存在唯一 `OVERRIDE` 时，该值替代同一节点的基础值，并以规范化 ADD 传给
Calculator。多个 OVERRIDE，或 OVERRIDE 与任何其他规则 operation 的先后关系未被规范明确
时，必须阻塞，不得根据数组顺序猜测。

Application 层的事件身份和来源信息不得写入领域 `DamageEventMetadata`。应使用薄的
`InstantiatedDamageEvent` wrapper 保存 `template_id`、`semantic_id`、展示名称、来源规则项、
创建 Effect 和 `repeat_count`，Calculator 只读取 wrapper 中的领域事件。

`UNIT_REPEAT` 的 Calculator 结果始终是一个等价单位的结果，`breakdown` 也只解释该单位。
重复次数保留在 Application 输出的 `repeat_count`，事件的展示值为
`result.value × repeat_count`；不得把次数伪装成原始技能倍率或篡改单位 breakdown。

派生事件必须放入 Application 事件队列，并在创建后重新经过 EffectMatcher。循环检测只检查
当前 EventCreation ancestry 中是否再次进入同一模板或语义边；不得用全局 semantic ID 集合
静默去重。不同分支再次创建同一 semantic event 时，应产生阻塞性契约诊断。

Panel Modifier 的执行顺序固定为：基础角色快照 → 正式、事件无关的 Panel Effect →
settlement snapshot。该正式快照应保存在 Application 输出中。非暴击、期望暴击、全暴击
只允许在调用 Calculator 前对暴击率建立临时快照，不得重新匹配 Effect，也不得把展示快照
当作正式局内面板。

基础 Panel Effect 只有在 `trigger is None`、`condition` 为空或为 `AlwaysCondition`、且
`filters` 为空时才视为全局、事件无关的 Panel Effect。

应用层在当前 DamageEvent 匹配前执行一次全局 Panel pre-pass。事件无关的 `target=SELF`
Panel Effect 写入其 `Effect.owner` 的角色快照，即使该角色不是当前操作角色；它仍必须通过
RuleItem 的启用、资格、场景条件和叠层校验。这样支援角色的自身面板变化可以影响其随后创建的
派生事件，同时不会把自身事件增伤误当成全局面板。

应用层可以额外识别一种明确的 recipient Panel Effect：`target=TEAM`，触发事实为
`SUPPORT_ENTRY`，并且 Filter 仅用于匹配 `SUPPORT_ENTRY_CHARACTER`。该 Effect 只写入
当前场景声明的入场角色；不得因为 `target=TEAM` 让其他队友获得该面板效果。其他带有
招式、属性、伤害类型或伤害标签 Filter 的 Panel Effect 不得伪装成全局 settlement panel。

事件专属面板属性必须进入独立的 event-stat lane，不得污染正式 settlement snapshot。第一版
只支持 `CHARACTER_CURRENT_CRIT_RATE + ADD`，其 recipient 从当前 DamageEvent 的
`StandardCritRule.stat_owner` 得到。事件倍率修正进入独立的 event-multiplier lane；第一版
只支持 `DAMAGE_SKILL_MULTIPLIER + MULTIPLY`，在调用 Calculator 前作用于事件副本。
这两个 lane 都必须写入对应的 DamageEvent execution trace。

叠层规则的默认层数保存在 RuleItem，场景可以通过 `ScenarioRuleStack` 覆盖合法层数。
第一版只定义 `ADD Modifier × stack_count`；叠层的非 `ADD` Modifier，以及层数不为1的
EventCreation、StateChange 或其他非 Modifier Effect，必须阻塞，不得静默执行一次。

每个 DamageEvent 都必须拥有独立的执行 trace，至少记录该事件的 RuleItem 匹配结果和应用
到该事件的 Modifier。不得把主事件与派生事件的匹配结果摊平成没有事件归属的列表。

输出状态必须区分：Calculator 返回 `MISSING_DATA` 为 `DATA_INSUFFICIENT`；场景或应用语义
阻塞为 `BLOCKED`；没有对应 Calculator 为 `UNSUPPORTED_CALCULATOR`。至少一个事件成功时，
`known_total` 为所有成功事件展示值之和；没有任何成功事件时为 `None`，不得返回假零。

当一个招式包含多个 DamageEvent 时，“不暴击 / 期望 / 全暴击”的招式总伤害分别对所有 StandardCritRule 事件应用对应展示模式后求和。NoCritRule 以及其他不采用普通暴击模式的事件，在三个总伤害场景中均使用其自身正式结算结果。不得为了生成总伤害而修改这些事件自身的 CritRule。

## Build Assembly

装备面板必须先由独立的 Build Assembly 层构造，再进入角色 Definition 和应用执行层。
Calculator 不读取音擎、驱动盘或其他装备对象，也不负责聚合装备属性。

Build Assembly 支持两种输入模式：

- `MANUAL_PANEL`：调用方直接提供已经确定的局外面板；
- `EQUIPMENT_BUILD`：使用角色基础属性和已验证的装备属性贡献构造局外面板。

装备模式的属性贡献必须明确区分：

- 白值贡献：加入对应属性白值；
- 局外百分比贡献：以对应白值为基准；
- 局外固定值贡献：在百分比计算后相加；
- 直接比例贡献：用于暴击率、暴击伤害、穿透率和属性伤害加成等比例属性。

第一版装备白值贡献只将音擎攻击力加入攻击力白值；角色其他白值由角色基础属性输入
提供。驱动盘主词条、副词条和套装静态属性不得因为“白值”字段名称而自动变成百分比
计算基准。

攻击力的构造顺序为：

```text
攻击力白值 = 角色基础攻击力 + 音擎攻击力加成
初始攻击力 = 攻击力白值 × (1 + 局外攻击力百分比加成)
             + 局外固定攻击力加成
```

其他具有白值的属性使用同样的“白值 → 百分比 → 固定值”顺序；穿透率不存在白值，
其贡献直接线性相加。Build Assembly 不提前舍入中间结果。

构建输出必须包含最终局外面板、初始角色快照、每项贡献的来源追踪、规则项容器和
结构化诊断。主词条、副词条和2件套静态属性属于面板贡献；4件套及其他条件性效果
必须编译为 `CalculationRuleItem` / `Effect`，不得在 Build Assembly 中直接执行战斗规则。

空装备槽位不产生任何属性，副词条属于具体装备对象，不使用全局副词条次数池。
属性伤害加成必须保存具体基础属性身份，不能退化为无属性范围的通用字段。

手工面板模式与装备模式最终必须输出相同类型的角色初始快照，后续应用执行层和
Calculator 不得区分面板来源。缺失或无法解析的构建数据必须保留为未决状态并产生
结构化诊断，不得按零或其他默认值静默计算。

Stage18-2 的音擎 vertical slice 只开放已审核的叶瞬光与耀嘉音专武，并以满级60级
静态值作为当前数据切片；非60级输入必须产生明确诊断，不能回退到满级值。音擎的
基础攻击和高级属性进入 Build Assembly，音擎特效则通过附加的 RuleItem/Scenario
Condition 集合进入现有 Matcher 与 Execution。专武映射必须使用显式的角色 ID 映射。
音擎目录只保存型号、名称、图标和职业等模型元数据；装备到具体角色后，必须由实例级
编辑器输出 owner-qualified 的 RuleItem/Effect 身份，不能在目录中预先保存一套全局规则
ID。音擎规则与角色规则共同进入同一个场景规则编辑器和
`CalculationScenario.enabled_rule_item_ids`，前端不得因为装备存在而强制启用其效果。
同一型号音擎装备到不同角色时，其实例级场景条件也必须保持独立，不能共享另一名装备者
的触发状态。
音擎来源的规则匹配/Modifier 追踪必须保留 `source_type=weapon`，以便与角色事件级
加成和正式局内面板来源区分。

## 多倍率参数处理

数据库中同一技能条目可能包含多个伤害倍率参数。多个倍率之间不得仅根据其在数据库中的排列顺序推断先后、包含、互斥或相加关系。

### 明确编号的连续招式阶段

当参数明确表示“一段、二段、三段……”等连续招式阶段时，每个阶段作为独立的 `MoveCalculationEntry` 或招式变体展示并分别计算。

前端可以额外提供“完整连段合计”，其值为这些阶段计算结果的和，但该合计属于展示层汇总，不创建新的 DamageEvent，也不得将各阶段倍率预先相加后作为一个 DamageEvent 重新计算。

### 明确互斥的招式版本

当文本能够明确确认多个倍率对应同一招式在不同状态、输入方式或场景下的互斥版本时，应建立多个 `multiplier_variant`。

每个 variant 对应一个合法场景条件；同一次计算只能选择其中一个，不得将倍率相加。

本次计算选中的互斥 variant 唯一由其场景条件决定；Definition 和 RuleItem 不保存另一份
选中状态。若对应条件无法唯一确定，保留未决状态，不得把多个 variant 同时送入计算器。

若无法由静态配置唯一决定具体 variant，则由用户选择。

### 明确的单位倍率与次数

当文本明确说明倍率是“每次”“每道”“每枚”“每段”等单位伤害，而总次数又会改变正式伤害结果时，保留单位倍率，并将次数作为 `ScenarioIntegerParameter` 场景输入。`UNIT_REPEAT` 只能引用数值型场景参数，不得引用布尔 `ScenarioCondition`。

总伤害必须通过多个等价结算单位的数学汇总得到；第一版仍不需要恢复真实 Hit 时间轴。

若次数可以由静态配置唯一确定，则自动确定；否则允许用户输入合法次数。

### 已提供完整招式倍率

若数据库明确给出完整招式总倍率，则直接使用完整倍率。即使文本描述招式包含多次攻击，也不得再次按照 Hit 拆分或乘次数。

### 关系无法确定

若多个倍率之间的关系无法由术语规范、计算规范、实现规范或明确游戏文本唯一确定，并且不同解释会改变正式计算结果，则不得依据参数名称、数据排列顺序或游戏常识猜测，应产生阻塞性诊断并要求人工确认。

若外部数据库存在明显重复或错误参数，则按照数据质量问题处理，不为了兼容错误数据创造新的战斗语义。

## 方案比较

计算器应允许用户将当前配置保存为基准方案，并修改角色影画、音擎、驱动盘词条、小队成员或计算规则项形成比较方案。

比较必须分别完整执行两次计算管线，不得通过对最终伤害直接乘一个估算比例得到。

对同一输出项展示绝对差值与相对提升率：

```text
提升率 = 比较方案结果 / 基准方案结果 - 1
```

若两方案改变了事件集合，应明确展示新增、消失或发生类型变化的 DamageEvent，而不是只给一个总百分比。

当基准方案对应结果为0时，相对提升率无定义，前端只显示绝对变化，不显示无穷大或人为定义的百分比。

两个方案之间的 DamageEvent 应按其稳定语义身份进行对应，不得按照列表位置对应。同一来源招式中相同事件类型和事件身份视为同一比较项；仅存在于一侧的事件分别标记为“新增”或“消失”。

## 配置持久化

配置 JSON 必须包含 `schema_version`。

角色、音擎、驱动盘等实体使用稳定 ID 保存，不使用展示名称作为唯一标识。
