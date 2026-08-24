import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { assertNanokaVersion, type NanokaDetailKind, type NanokaDetailSnapshot } from "../src/importers/nanoka/client.js";
import {
  extractNanokaBuffReviewEntries,
  selectNanokaReviewBatch,
  type NanokaBuffReviewEntry,
} from "../src/importers/nanoka/detail-review.js";
import {
  parseNanokaBuffEntries,
  renderNanokaEquipmentReviewQueue,
  renderNanokaEquipmentRemainingReviewQueue,
  renderNanokaActionableReviewQueue,
  renderNanokaBuffParseReview,
  selectNanokaEquipmentReviewEntries,
  selectNanokaActionableReviewBatch,
  type NanokaParsedBuff,
} from "../src/importers/nanoka/parse-buff.js";
import { applyNanokaReviewDecisions } from "../src/importers/nanoka/review-decisions.js";
import {
  NANOKA_REVIEW_DECISIONS_BATCH_001,
  NANOKA_REVIEW_DECISIONS_BATCH_002,
  NANOKA_REVIEW_DECISIONS_BATCH_003,
} from "../data/rules/nanoka-review-decisions.js";
import { NANOKA_EQUIPMENT_REVIEWED_BATCH_002 } from "../data/rules/nanoka-equipment-reviewed-002.js";

const versionArgument = process.argv.find((arg) => arg.startsWith("--version="));
const localeArgument = process.argv.find((arg) => arg.startsWith("--locale="));
const version = versionArgument?.slice("--version=".length) ?? await findLatestCachedVersion();
const locale = localeArgument?.slice("--locale=".length) ?? "zh";
assertNanokaVersion(version);
if (locale !== "zh" && locale !== "en") throw new Error(`语言只支持 zh/en：${locale}`);

const snapshot = await loadDetailSnapshot(version, locale);
const entries = extractNanokaBuffReviewEntries(snapshot);
const parsed = applyNanokaReviewDecisions(
  parseNanokaBuffEntries(entries),
  {
    ...NANOKA_REVIEW_DECISIONS_BATCH_001,
    ...NANOKA_REVIEW_DECISIONS_BATCH_002,
    ...NANOKA_REVIEW_DECISIONS_BATCH_003,
  },
);
const actionableGroups = selectNanokaActionableReviewBatch(parsed, parsed.length);
const reportDir = path.resolve("reports", "buffs");
const compiledDir = path.resolve("data", "compiled");
await mkdir(reportDir, { recursive: true });
await mkdir(compiledDir, { recursive: true });

const database = {
  source: "nanoka.cc",
  version,
  locale,
  generatedAt: new Date().toISOString(),
  policy: "deterministic-no-warning-auto-accepted; manual-review-required-for-needs-review",
  counts: {
    candidates: parsed.length,
    withRule: parsed.filter((item) => item.rule !== null).length,
    rules: parsed.reduce(
      (total, item) => total + (item.rules?.length ?? (item.rule ? 1 : 0)),
      0,
    ),
    ignored: parsed.filter((item) => item.disposition === "ignored").length,
    autoAccepted: parsed.filter((item) => item.disposition === "auto-accepted").length,
    needsReview: parsed.filter((item) => item.disposition === "needs-review").length,
    needsReviewGroups: actionableGroups.length,
  },
  entries: parsed,
};
const databasePath = path.join(compiledDir, `nanoka-buffs-${version}.json`);
await writeFile(databasePath, JSON.stringify(database, null, 2));

const issues = parsed.filter((item) => item.issues.length > 0);
const allIssuesPath = path.join(reportDir, "nanoka-buff-parse-issues-all.md");
await writeFile(allIssuesPath, renderNanokaBuffParseReview(version, issues));

const issueEntries = entries.filter((entry) => issues.some((item) => item.key === entry.key));
const batchEntries = selectNanokaReviewBatch(issueEntries, 20);
const batchKeys = new Set(batchEntries.map((entry) => entry.key));
const batch = parsed.filter((item) => batchKeys.has(item.key));
const batchPath = path.join(reportDir, "nanoka-buff-parse-review-batch-001.md");
await writeFile(batchPath, renderNanokaBuffParseReview(version, batch));

const actionableBatch = selectNanokaActionableReviewBatch(parsed, 10);
const actionableBatchPath = path.join(reportDir, "nanoka-buff-review-queue-001.md");
await writeFile(
  actionableBatchPath,
  renderNanokaActionableReviewQueue(version, parsed, actionableBatch),
);

const equipmentReviewEntries = selectNanokaEquipmentReviewEntries(parsed);
const equipmentReviewPath = path.join(reportDir, "nanoka-equipment-review-queue-001.md");
await writeFile(
  equipmentReviewPath,
  renderNanokaEquipmentReviewQueue(version, parsed, equipmentReviewEntries),
);

const remainingEquipmentEntries = parsed.filter((item) =>
  (item.key.startsWith("weapon:") || item.key.startsWith("equipment:")) &&
  item.disposition !== "ignored" &&
  item.rule === null &&
  (item.rules === undefined || item.rules.length === 0) &&
  !NANOKA_EQUIPMENT_REVIEWED_BATCH_002.some((rule) => rule.source.key === item.key),
);
const remainingEquipmentBatch = selectNanokaEquipmentReviewEntries(remainingEquipmentEntries);
const remainingEquipmentReviewPath = path.join(reportDir, "nanoka-equipment-review-remaining-001.md");
await writeFile(
  remainingEquipmentReviewPath,
  renderNanokaEquipmentRemainingReviewQueue(version, remainingEquipmentEntries, remainingEquipmentBatch),
);

console.log(`Nanoka 版本：${version}`);
console.log(`Buff 候选：${parsed.length}`);
console.log(`生成结构化候选：${database.counts.withRule}`);
console.log(`需要人工审查：${database.counts.needsReview}`);
console.log(`版本化静态数据库：${databasePath}`);
console.log(`全部问题：${allIssuesPath}`);
console.log(`首批问题：${batchPath}`);
console.log(`真正需要人工确认原始条目：${parsed.filter((item) => item.disposition === "needs-review").length}`);
console.log(`真正需要人工确认语义组：${actionableGroups.length}`);
console.log(`首批人工队列：${actionableBatchPath}`);
console.log(`音擎与驱动盘审查队列：${equipmentReviewPath}`);
console.log(`装备剩余待确认：${remainingEquipmentReviewPath}`);

async function findLatestCachedVersion(): Promise<string> {
  const versions = (await readdir(path.resolve(".cache", "nanoka")))
    .filter((value) => /^\d+\.\d+\.\d+\+\d+$/.test(value))
    .sort();
  const latest = versions.at(-1);
  if (!latest) throw new Error("没有找到 Nanoka 详情缓存，请先运行 npm run sync:nanoka:details。");
  return latest;
}

async function loadDetailSnapshot(versionValue: string, localeValue: string): Promise<NanokaDetailSnapshot> {
  const root = path.resolve(".cache", "nanoka", versionValue, "details", localeValue);
  const details = {} as NanokaDetailSnapshot["details"];
  for (const kind of ["character", "weapon", "equipment"] as const) {
    const values: Record<string, Record<string, unknown>> = {};
    for (const filename of await readdir(path.join(root, kind))) {
      if (!filename.endsWith(".json") || filename === "index.json") continue;
      const id = filename.slice(0, -5);
      values[id] = JSON.parse(await readFile(path.join(root, kind, filename), "utf8")) as Record<string, unknown>;
    }
    details[kind] = values;
  }
  return {
    source: "nanoka.cc",
    version: versionValue,
    locale: localeValue as "zh" | "en",
    fetchedAt: new Date().toISOString(),
    details,
  };
}
