import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { BuffRule } from "../src/domain/model/buff.js";
import { validateBuffRule } from "../src/domain/engine/validate-buff-rule.js";

interface CompiledEntry {
  key: string;
  disposition: string;
  rule?: BuffRule;
  rules?: readonly BuffRule[];
}

interface CompiledDatabase {
  version: string;
  entries: readonly CompiledEntry[];
}

const versionArgument = process.argv.find((arg) => arg.startsWith("--version="));
const version = versionArgument?.slice("--version=".length) ?? "3.2.1+17934514";
const inputPath = path.resolve("data", "compiled", `nanoka-buffs-${version}.json`);
const outputPath = path.resolve("data", "rules", "nanoka-equipment-reviewed-001.ts");

// 这些装备已有用户确认过的手写规则，保留其更精确的 lookup、作用域和满层语义，
// 避免同一装备同时从 Nanoka 单档文本和手写规则重复生效。
const manuallyReviewedKeys = new Set<string>([
  "weapon:14140:talent:1",
  "weapon:14140:talent:2",
  "weapon:14140:talent:3",
  "weapon:14140:talent:4",
  "weapon:14140:talent:5",
  "weapon:14121:talent:1",
  "weapon:14121:talent:2",
  "weapon:14121:talent:3",
  "weapon:14121:talent:4",
  "weapon:14121:talent:5",
  "equipment:31800:desc2",
  "equipment:32600:desc2",
  "equipment:32600:desc4",
  "equipment:33400:desc4",
]);

const database = JSON.parse(await readFile(inputPath, "utf8")) as CompiledDatabase;
const byId = new Map<string, BuffRule>();
for (const entry of database.entries) {
  if (entry.disposition === "ignored" || manuallyReviewedKeys.has(entry.key)) continue;
  if (!entry.key.startsWith("weapon:") && !entry.key.startsWith("equipment:")) continue;
  const rules = entry.rules ?? (entry.rule ? [entry.rule] : []);
  for (const rule of rules) {
    const notes = [
      rule.notes,
      "用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。",
    ].filter((value): value is string => Boolean(value));
    const verifiedRule: BuffRule = {
      ...rule,
      status: "verified",
      ...(notes.length > 0 ? { notes: notes.join("；") } : {}),
    };
    const validation = validateBuffRule(verifiedRule);
    if (!validation.valid) {
      throw new Error(`${verifiedRule.id}: ${JSON.stringify(validation.issues)}`);
    }
    const previous = byId.get(verifiedRule.id);
    if (previous !== undefined) {
      throw new Error(`重复的 Nanoka 装备规则：${verifiedRule.id}`);
    }
    byId.set(verifiedRule.id, verifiedRule);
  }
}

const rules = [...byId.values()].sort((left, right) => left.id.localeCompare(right.id));
const output = [
  'import type { BuffRule } from "../../src/domain/model/buff.js";',
  "",
  "/**",
  ` * Nanoka ${version} 音擎与驱动盘已确认规则。`,
  " *",
  " * 音擎规则带 weaponRefinement，只激活当前精炼档位；驱动盘规则带",
  " * equippedCountAtLeast，只在满足 2/4 件套时激活。范围外条目不在此文件中。",
  " */",
  `export const NANOKA_EQUIPMENT_REVIEWED_RULES: readonly BuffRule[] = ${JSON.stringify(rules, null, 2)};`,
  "",
  "export const NANOKA_EQUIPMENT_REVIEWED_RULES_BY_ID: Readonly<Record<string, BuffRule>> =",
  "  Object.fromEntries(NANOKA_EQUIPMENT_REVIEWED_RULES.map((rule) => [rule.id, rule]));",
  "",
].join("\n");
await writeFile(outputPath, output);

console.log(`生成音擎与驱动盘规则：${outputPath}`);
console.log(`规则数量：${rules.length}`);
console.log(`音擎：${rules.filter((rule) => rule.source.type === "weapon").length}`);
console.log(`驱动盘：${rules.filter((rule) => rule.source.type === "drive-disc-set").length}`);
