# ZZZ Calculator Next 架构

## 目标

新版本采用“纯计算核心 + 声明式规则数据 + 输入适配器 + 薄 UI”。旧版 `index.html`、`app.js` 和 `dict/` 暂时保留，只作为行为参考和迁移来源。

核心约束：

1. 计算引擎不读取 DOM，也不生成 HTML。
2. UID、手动配置和旧配置必须转换成统一的 `CharacterBuild`。
3. Buff 是带条件、对象、阶段和效果的规则，不是若干数字字段。
4. 每次计算返回数值和来源追踪。
5. 未审核机制必须显示警告，不得静默按满层生效。
6. 原始数据、审核规则和浏览器产物分开保存。

## 分层

```text
外部数据/UID
    ↓ importer
CharacterBuild + StaticData
    ↓ application
CalculationInput
    ↓ domain engine
CalculationResult + Trace + Warnings
    ↓ UI
页面展示与用户确认
```

目录职责：

```text
src/domain/model/       统一数据类型
src/domain/engine/      纯属性、Buff 和伤害计算
src/importers/          Enka、旧 JSON 等输入适配器
src/application/        组织一次计算用例
scripts/                数据更新、UID 导入和审计命令
tests/fixtures/         用户确认过的真实配置与结果
data/raw/               不修改的上游原始数据
data/rules/             人工审核的战斗规则
data/compiled/          自动生成的前端数据包
```

## 第一条竖向链路

第一阶段只完成：

```text
UID/参考截图 → CharacterBuild → 战前基础面板 → 差异与追踪
```

不在这一阶段处理战斗 Buff、4 件套条件效果、队友增益和最终伤害。

