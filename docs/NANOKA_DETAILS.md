# Nanoka 详情数据与 Buff 审查流程

## 数据来源边界

Nanoka 是角色、音擎、驱动盘、技能和倍率的唯一静态原文来源。旧版
`app.js`、`dict/`、`archive` 以及历史审查单不能作为 Buff 原文或解析输入。
`archive` 只允许在版本 manifest 差异计算中使用，不允许回退到详情文本。

当前详情 URL 形式为：

```text
https://static.nanoka.cc/zzz/{version}/{locale}/{kind}/{id}.json
```

其中 `kind` 为 `character`、`weapon` 或 `equipment`，中文使用 `zh`。

## 当前下载结果

执行：

```bash
npm run sync:nanoka:details
```

当前版本 `3.2.1+17934514` 已下载：

- 60 名角色详情；
- 100 个音擎详情；
- 30 套驱动盘详情；
- 2687 条待审查原文候选。

详情按版本、语言和对象类型缓存到 `.cache/nanoka/{version}/details/`，已有文件
不会重复请求。`--force` 可强制重新下载：

```bash
npm run sync:nanoka:details -- --force
```

## 原文提取范围

- 角色：`passive.level`、`talent`，以及技能描述中包含数值/状态变化关键词的文本；
- 音擎：`talents` 的 1~5 阶文本；
- 驱动盘：`desc2` 和 `desc4`。

提取器只保存原文、显示标记清洗后的阅读文本、详情 URL 和稳定 `key`。解析器会把
无语义警告的简单确定性效果自动接收，并由
`data/rules/nanoka-compiled-auto.ts` 自动接入统一注册表；动态换算、动作顺序、叠层
边界和复合效果仍保持 `partial`，不会进入当前计算。已有人工审查语义组优先覆盖
自动候选，避免同一 Buff 被重复激活。

角色详情同时提供队伍触发所需的稳定标签：`weapon_type` 映射为职业，
`element_type` 映射为元素，`camp` 映射为阵营。额外能力条件现在使用条件树表达，
不再使用旧版 `hasSameElementOrFaction` 模糊布尔字段；旧版已存在的同职业判断以及
爱丽丝、凯撒特殊职业触发均集中在通用条件构造器中。

当前已增加保守解析命令：

```bash
npm run parse:nanoka:buffs
```

它会生成 `data/compiled/nanoka-buffs-{version}.json`。其中简单且无语义警告的候选会
标记为 `verified`，能量/资源/技能等级/纯护盾流程等当前范围外条目标记为 `ignored`；
解析器发现条件冲突、复合事件、动作顺序、倍率改写或模型缺口时，标记为
`needs-review` 并保留 `partial` 候选。

审查文件：

- `reports/buffs/nanoka-official-review-all.md`：全量候选；
- `reports/buffs/nanoka-official-review-batch-001.md`：去重后的首批 20 条。
- `reports/buffs/nanoka-buff-parse-issues-all.md`：全量解析问题；
- `reports/buffs/nanoka-buff-parse-review-batch-001.md`：首批 20 条结构化解析问题。
- `reports/buffs/nanoka-buff-review-queue-001.md`：真正面向人工的首批 10 条审查队列。

本批已确认的 20 条规则位于 `data/rules/nanoka-reviewed-batch-001.ts`。它们保留
Nanoka 版本、详情 URL、条目 key 和原始描述；凯撒核心护盾等尚未确认的规则仍留在
审查报告，不会进入计算。

## 历史文件处理

`reports/buffs/review-batch-001.md`、`review-batch-002.md` 和
`data/rules/character-buffs-review-001.ts` 保留作迁移记录，但它们来自旧本地字典，
原文可信度不足，已经从当前 Buff 审查流程和测试入口隔离。即使历史结论看起来
合理，也必须重新对照 Nanoka 详情 URL 确认后才能迁移。
