import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  renderNanokaAnomalyReviewQueue,
  reviewedNanokaRuleGroup,
  selectNanokaAnomalyReviewQueue,
} from "../src/importers/nanoka/anomaly-review.js";
import { nanokaReviewGroupKey, type NanokaParsedBuff } from "../src/importers/nanoka/parse-buff.js";
import {
  NANOKA_REVIEW_DECISIONS_BATCH_001,
  NANOKA_REVIEW_DECISIONS_BATCH_002,
  NANOKA_REVIEW_DECISIONS_BATCH_003,
} from "../data/rules/nanoka-review-decisions.js";
import { REVIEWED_CHARACTER_BUFF_RULES } from "../data/rules/reviewed-buff-registry.js";

const versionArgument = process.argv.find((arg) => arg.startsWith("--version="));
const version = versionArgument?.slice("--version=".length) ?? "3.2.1+17934514";
const databasePath = path.resolve("data", "compiled", `nanoka-buffs-${version}.json`);
const reportPath = path.resolve("reports", "buffs", "nanoka-anomaly-review-queue-001.md");

const database = JSON.parse(await readFile(databasePath, "utf8")) as {
  version: string;
  entries: NanokaParsedBuff[];
};
const reviewedGroups = collectReviewedGroups(database.entries);
const selection = selectNanokaAnomalyReviewQueue(database.entries, reviewedGroups, 20);
await writeFile(reportPath, renderNanokaAnomalyReviewQueue(database.version, database.entries, selection));

console.log(`Nanoka 异常伤害复筛版本：${database.version}`);
console.log(`异常相关候选：${selection.candidates.length}`);
console.log(`已确认/已处理剔除：${selection.excludedReviewed}`);
console.log(`剩余待审原始条目：${selection.remaining.length}`);
console.log(`剩余待审语义组：${selection.remainingGroups}`);
console.log(`首批复审队列：${reportPath}`);

function collectReviewedGroups(entries: readonly NanokaParsedBuff[]): Set<string> {
  const groups = new Set<string>();
  for (const rule of REVIEWED_CHARACTER_BUFF_RULES) {
    const group = reviewedNanokaRuleGroup(rule);
    if (group) groups.add(group);
  }

  const decisions = {
    ...NANOKA_REVIEW_DECISIONS_BATCH_001,
    ...NANOKA_REVIEW_DECISIONS_BATCH_002,
    ...NANOKA_REVIEW_DECISIONS_BATCH_003,
  };
  for (const key of Object.keys(decisions)) {
    const item = entries.find((candidate) => candidate.key === key);
    if (item) {
      groups.add(nanokaReviewGroupKey(item));
    }
  }
  return groups;
}
