import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { NanokaClient } from "../src/importers/nanoka/client.js";
import {
  diffNanokaSnapshots,
  type NanokaDiffReport,
} from "../src/importers/nanoka/diff.js";

const baselineVersion = process.argv[2] ?? "3.0.3+15825894";
const client = new NanokaClient();
const latestVersion = await client.discoverLatestVersion();
console.log(`Nanoka 当前版本：${latestVersion}`);
console.log(`项目基准版本：${baselineVersion}`);

const [before, after] = await Promise.all([
  client.fetchSnapshot(baselineVersion, { legacyManifestDir: "archive" }),
  client.fetchSnapshot(latestVersion),
]);
const report = diffNanokaSnapshots(before, after);
const reportDir = path.resolve("reports/nanoka");
await mkdir(reportDir, { recursive: true });
const stem = `${baselineVersion}--${latestVersion}`;
const jsonPath = path.join(reportDir, `${stem}.json`);
const markdownPath = path.join(reportDir, `${stem}.md`);
await writeFile(jsonPath, JSON.stringify(report, null, 2));
await writeFile(markdownPath, renderMarkdown(report, after.manifests));

console.log(`差异报告：${markdownPath}`);
for (const [name, diff] of Object.entries(report.manifests)) {
  console.log(
    `${name}: ${diff.beforeCount} → ${diff.afterCount}, ` +
      `新增 ${diff.added.length}, 删除 ${diff.removed.length}, 变更 ${diff.changed.length}`,
  );
}

function renderMarkdown(
  report: NanokaDiffReport,
  manifests: typeof after.manifests,
): string {
  const lines = [
    "# Nanoka 绝区零数据差异",
    "",
    `- 来源：https://zzz.nanoka.cc/`,
    `- 旧版本：\`${report.fromVersion}\``,
    `- 新版本：\`${report.toVersion}\``,
    `- 生成时间：${report.generatedAt}`,
    "",
  ];
  for (const [name, diff] of Object.entries(report.manifests)) {
    lines.push(
      `## ${name}`,
      "",
      `数量：${diff.beforeCount} → ${diff.afterCount}`,
      "",
      `新增（${diff.added.length}）：${formatItems(diff.added, manifests[name as keyof typeof manifests])}`,
      "",
      `删除（${diff.removed.length}）：${diff.removed.join(", ") || "无"}`,
      "",
      `变更（${diff.changed.length}）：${formatItems(diff.changed, manifests[name as keyof typeof manifests])}`,
      "",
    );
  }
  return `${lines.join("\n")}\n`;
}

function formatItems(ids: string[], manifest: Record<string, unknown>): string {
  if (ids.length === 0) return "无";
  return ids
    .map((id) => {
      const item = manifest[id] as Record<string, unknown> | undefined;
      const localized = item?.zh as Record<string, unknown> | string | undefined;
      const english = item?.en as Record<string, unknown> | string | undefined;
      const name =
        (localized && typeof localized === "object" ? localized.name : localized) ??
        item?.name ??
        (english && typeof english === "object" ? english.name : english);
      return name ? `${id} ${String(name)}` : id;
    })
    .join("、");
}
