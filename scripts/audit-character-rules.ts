import { mkdir, readFile, readdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  auditCharacterRules,
  renderCharacterRuleAuditMarkdown,
} from "../src/domain/audit/character-rule-audit.js";
import { mapNanokaCharacterProfiles } from "../src/importers/nanoka/profile.js";
import type { NanokaParsedBuff } from "../src/importers/nanoka/parse-buff.js";
import {
  REVIEWED_BUFF_REGISTRY_VERSION,
  REVIEWED_CHARACTER_BUFF_RULES,
} from "../data/rules/reviewed-buff-registry.js";

const versionArgument = process.argv.find((argument) => argument.startsWith("--version="));
const version = versionArgument?.slice("--version=".length) ?? REVIEWED_BUFF_REGISTRY_VERSION;
const strict = process.argv.includes("--strict");
const compiledPath = path.resolve("data", "compiled", `nanoka-buffs-${version}.json`);
const detailRoot = path.resolve(".cache", "nanoka", version, "details", "zh", "character");
const reportRoot = path.resolve("reports", "audit");

const database = JSON.parse(await readFile(compiledPath, "utf8")) as {
  version: string;
  entries: NanokaParsedBuff[];
};
const details: Record<string, Record<string, unknown>> = {};
for (const filename of await readdir(detailRoot)) {
  if (!filename.endsWith(".json") || filename === "index.json") continue;
  const id = filename.slice(0, -5);
  details[id] = JSON.parse(
    await readFile(path.join(detailRoot, filename), "utf8"),
  ) as Record<string, unknown>;
}

const report = auditCharacterRules({
  sourceVersion: database.version,
  profiles: mapNanokaCharacterProfiles(details),
  entries: database.entries,
  rules: REVIEWED_CHARACTER_BUFF_RULES,
});

await mkdir(reportRoot, { recursive: true });
const jsonPath = path.join(reportRoot, `character-rules-${version}.json`);
const markdownPath = path.join(reportRoot, `character-rules-${version}.md`);
await writeFile(jsonPath, `${JSON.stringify(report, null, 2)}\n`);
await writeFile(markdownPath, renderCharacterRuleAuditMarkdown(report));

console.log(`角色规则审计版本：${version}`);
console.log(`角色：${report.summary.characters}`);
console.log(`已登记规则：${report.summary.reviewedRules}`);
console.log(`正向场景成功激活：${report.summary.activatedRules}`);
console.log(`阻断错误：${report.summary.errors}`);
console.log(`待审语义组：${report.summary.pendingReviewGroups}`);
console.log(`已剔除非伤害机制：${report.summary.deferredOutOfScopeGroups}`);
console.log(`主链未消费效果：${report.summary.integrationGaps}`);
console.log(`Markdown：${markdownPath}`);
console.log(`JSON：${jsonPath}`);

if (report.summary.errors > 0 || (strict && (
  report.summary.pendingReviewGroups > 0 || report.summary.integrationGaps > 0
))) {
  process.exitCode = 1;
}
