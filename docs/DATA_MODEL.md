# 数据模型约定

## CharacterBuild

`CharacterBuild` 只描述玩家拥有和装备了什么，不保存敌人状态或战斗 Buff。

主要内容：

- 数据来源、UID、导入时间和数据版本。
- 角色 ID、等级、突破、影画、核心技、技能等级。
- 音擎 ID、等级、突破和精炼。
- 六个驱动盘及其真实主副词条。

## 单位

- 固定生命、攻击、防御、穿透和异常精通使用实际显示数值。
- 百分比统一使用“百分点”：`30` 表示 `30%`，不表示 `0.3`。
- 能量自动回复使用游戏面板值，例如 `1.2`。
- 所有外部原始值必须在 importer 中转换单位，计算引擎不猜测单位。

## 支持状态

```text
raw-only  基础数据可见，战斗规则未迁移
partial   部分规则可计算，并附缺失警告
verified  主要公式和规则均通过用户确认与回归测试
```

## 状态分离

角色配置与场景状态分开：

```text
CharacterBuild  玩家角色装备
ScenarioState   Buff 开关、层数、敌人状态
AttackContext   本次攻击类型、属性和技能
StaticData      角色/音擎/驱动盘基础数据库
```

伤害类别至少包括：

```text
direct       直接伤害
anomaly      基础属性异常
assault      强击
disorder     紊乱
yifang       异放
yaobian      耀变
turbulence   乱流
penetration  贯穿伤害
```

异放、耀变、乱流和紊乱不是普通伤害加成的别名，而是独立伤害标签。由原异常伤害派生的效果使用 `derived-damage`，同时记录来源伤害类别和额外倍率，不能使用“攻击力百分比”的 `damage-instance` 代替。

异放的 `derived-damage` 还必须记录倍率语义：

- `multiply-original-anomaly`：额外结算一次原属性异常，使用“原属性异常倍率 × 异放倍率”。
- `replace-anomaly`：直接结算自身给出的属性异常倍率，不再乘原属性异常倍率，但伤害标签仍为 `yifang`。

两者的最终独立乘区和抗性区都按异放标签处理，区别只发生在基础值的倍率组成。

防御和抗性效果都必须保留效果类型和作用域：`def-shred`/`resistance-shred` 表示作用于敌人的减防/减抗 Debuff，默认对所有伤害生效；`def-ignore`/`resistance-ignore` 表示按当前角色、技能或伤害标签筛选的攻击侧无视。不能在汇总时把两者合并成一个没有来源和作用域的百分比。

紊乱计算还必须保留以下来源关系，不能只保存一个合并后的攻击角色：

- `sourceAnomalyEffectStrength`：被结算异常来源者的异常效果强度。
- `disorderDamageBonusFromSourcePercent`：来源者的“被结算的紊乱伤害提升”。
- `disorderDamageBonusFromTriggererPercent`：触发者的“造成的紊乱伤害提升”。
- `remainingSeconds`：异常状态当前剩余时间；未提供时按基础最大持续时间计算。
- `fixedDisorderMultiplierPercent`：直接进入紊乱基础倍率区的固定附加倍率。

极性紊乱的原紊乱比例与异常精通附加伤害也要分字段保存，最终显示时再合并。

乱流还必须保存：

- `windAnomalyPresent`：场上是否存在风化，这是乱流触发条件。
- `sourceAnomaly`：被结算的非风异常类型。
- `sourceAnomalyEffectStrength`：非风异常来源者的异常效果强度。
- `additionalTurbulenceMultiplierPercent`：直接进入乱流倍率区的特殊附加倍率。
- `turbulenceDamageBonusPercent` 与 `turbulenceCritMultiplier`：乱流增伤区和乱流暴击区。

风化施加者的角色身份属于战斗事件来源，不等于 `sourceAnomalyEffectStrength` 的来源者。
