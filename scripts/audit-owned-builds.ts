import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { REVIEWED_CHARACTER_BUFF_RULES } from "../data/rules/reviewed-buff-registry.js";
import type { CharacterBuild, ImportedShowcase } from "../src/domain/model/character-build.js";
import type {
  CharacterRuleAuditCharacter,
  CharacterRuleAuditIssue,
  CharacterRuleAuditReport,
} from "../src/domain/audit/character-rule-audit.js";

const uidArgument = process.argv.find((argument) => argument.startsWith("--uid="));
const uid = uidArgument?.slice("--uid=".length) ?? "16241824";
const version = "3.2.1+17934514";
const accountPath = path.resolve(".cache", "uid", "normalized", `${uid}.json`);
const auditPath = path.resolve("reports", "audit", `character-rules-${version}.json`);
const reportPath = path.resolve("reports", "audit", `owned-builds-${uid}.md`);

const account = JSON.parse(await readFile(accountPath, "utf8")) as ImportedShowcase;
const audit = JSON.parse(await readFile(auditPath, "utf8")) as CharacterRuleAuditReport;
const auditByCharacter = new Map(audit.characters.map((character) => [character.id, character]));
const rulesById = new Map(REVIEWED_CHARACTER_BUFF_RULES.map((rule) => [rule.id, rule]));

interface BuildReadiness {
  build: CharacterBuild;
  character: CharacterRuleAuditCharacter;
  globalIssues: CharacterRuleAuditIssue[];
  skillIssues: CharacterRuleAuditIssue[];
  specializedIssues: CharacterRuleAuditIssue[];
  dazeIssues: CharacterRuleAuditIssue[];
  inactiveIssues: CharacterRuleAuditIssue[];
  status: "ready" | "scoped" | "blocked";
}

const readiness = account.builds.flatMap((build): BuildReadiness[] => {
  const character = auditByCharacter.get(build.character.id);
  if (character === undefined) return [];
  const globalIssues: CharacterRuleAuditIssue[] = [];
  const skillIssues: CharacterRuleAuditIssue[] = [];
  const specializedIssues: CharacterRuleAuditIssue[] = [];
  const dazeIssues: CharacterRuleAuditIssue[] = [];
  const inactiveIssues: CharacterRuleAuditIssue[] = [];

  for (const issue of character.issues.filter((item) => item.severity !== "info")) {
    if (!issueAppliesToBuild(issue, build)) {
      inactiveIssues.push(issue);
      continue;
    }
    if (issue.code === "unconsumed-effect") {
      if (issue.effectKind === "daze-bonus") dazeIssues.push(issue);
      else specializedIssues.push(issue);
    } else if (issue.sourceKey?.includes(":skill:") === true) {
      skillIssues.push(issue);
    } else {
      globalIssues.push(issue);
    }
  }

  const status = globalIssues.length > 0 ? "blocked" :
    skillIssues.length > 0 || specializedIssues.length > 0 || dazeIssues.length > 0
      ? "scoped"
      : "ready";
  return [{
    build,
    character,
    globalIssues,
    skillIssues,
    specializedIssues,
    dazeIssues,
    inactiveIssues,
    status,
  }];
});

const order = { ready: 0, scoped: 1, blocked: 2 } as const;
readiness.sort((left, right) => order[left.status] - order[right.status] ||
  Number(left.character.id) - Number(right.character.id));

const lines = [
  "# UID 构筑级角色规则审计",
  "",
  `- UID：${uid}`,
  `- 数据版本：${version}`,
  `- 构筑数：${readiness.length}`,
  `- 可整体验证：${readiness.filter((item) => item.status === "ready").length}`,
  `- 可限定场景验证：${readiness.filter((item) => item.status === "scoped").length}`,
  `- 先补全局规则：${readiness.filter((item) => item.status === "blocked").length}`,
  "",
  "> 该报告按账号实际影画和核心等级过滤；未生效的高命规则不再阻塞当前构筑。",
  "> 招式文本、附加伤害实例和失衡值分别列出，因此不会把某一个局部缺口误报成整名角色不可测试。",
  "",
  "| ID | 角色 | 构筑 | 结论 | 全局缺口 | 招式缺口 | 附加伤害 | 失衡值 | 已过滤未激活 |",
  "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
  ...readiness.map((item) =>
    `| ${item.character.id} | ${item.character.name} | C${item.build.character.cinema} / 核心${item.build.character.coreLevel} | ${statusLabel(item.status)} | ${item.globalIssues.length} | ${item.skillIssues.length} | ${item.specializedIssues.length} | ${item.dazeIssues.length} | ${item.inactiveIssues.length} |`
  ),
  "",
  "## 当前可整体验证",
  "",
  ...listOrEmpty(readiness.filter((item) => item.status === "ready").map((item) =>
    `- ${item.character.name}（C${item.build.character.cinema}，核心${item.build.character.coreLevel}）`
  )),
  "",
  "## 可限定场景验证",
  "",
  ...readiness.filter((item) => item.status === "scoped").flatMap((item) => [
    `### ${item.character.name}（C${item.build.character.cinema}）`,
    "",
    ...renderIssues("不要把以下招式文本当作已覆盖", item.skillIssues),
    ...renderIssues("以下附加伤害事件尚未接入", item.specializedIssues),
    ...renderIssues("失衡值尚未接入最终伤害链", item.dazeIssues),
    "",
  ]),
  "## 仍有当前构筑全局缺口",
  "",
  ...readiness.filter((item) => item.status === "blocked").flatMap((item) => [
    `### ${item.character.name}（C${item.build.character.cinema}）`,
    "",
    ...item.globalIssues.map((issue) => `- ${issue.sourceKey ?? issue.ruleId ?? issue.code}：${issue.message}`),
    "",
  ]),
];

await mkdir(path.dirname(reportPath), { recursive: true });
await writeFile(reportPath, `${lines.join("\n")}\n`);
console.log(`账号构筑审计：${reportPath}`);
console.log(`可整体验证：${readiness.filter((item) => item.status === "ready").map((item) => item.character.name).join("、") || "无"}`);

function issueAppliesToBuild(issue: CharacterRuleAuditIssue, build: CharacterBuild): boolean {
  const talent = issue.sourceKey?.match(/:talent:(\d+)/);
  if (talent != null && Number(talent[1]) > build.character.cinema) return false;
  if (issue.ruleId !== undefined) {
    const rule = rulesById.get(issue.ruleId);
    if (rule?.cinemaAtLeast !== undefined && rule.cinemaAtLeast > build.character.cinema) return false;
    if (rule?.coreLevel !== undefined && rule.coreLevel !== build.character.coreLevel) return false;
  }
  return true;
}

function statusLabel(status: BuildReadiness["status"]): string {
  if (status === "ready") return "可整体验证";
  if (status === "scoped") return "可限定场景验证";
  return "先补全局规则";
}

function renderIssues(label: string, issues: readonly CharacterRuleAuditIssue[]): string[] {
  if (issues.length === 0) return [];
  return [
    `- ${label}：`,
    ...issues.map((issue) => `  - ${issue.sourceKey ?? issue.ruleId ?? issue.code}`),
  ];
}

function listOrEmpty(items: readonly string[]): string[] {
  return items.length === 0 ? ["- 无"] : [...items];
}
