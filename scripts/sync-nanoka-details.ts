import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import {
  NanokaClient,
  assertNanokaVersion,
  type NanokaLocale,
} from "../src/importers/nanoka/client.js";
import {
  extractNanokaBuffReviewEntries,
  renderNanokaBuffReview,
  selectNanokaReviewBatch,
} from "../src/importers/nanoka/detail-review.js";

const args = new Set(process.argv.slice(2));
const versionArgument = process.argv.find((arg) => arg.startsWith("--version="));
const localeArgument = process.argv.find((arg) => arg.startsWith("--locale="));
const version = versionArgument?.slice("--version=".length);
const locale = (localeArgument?.slice("--locale=".length) ?? "zh") as NanokaLocale;
const force = args.has("--force");

if (locale !== "zh" && locale !== "en") {
  throw new Error(`Nanoka 详情语言只支持 zh/en：${locale}`);
}
if (version) assertNanokaVersion(version);

const client = new NanokaClient();
const targetVersion = version ?? (await client.discoverLatestVersion());
console.log(`Nanoka 详情版本：${targetVersion}`);
console.log(`详情语言：${locale}${force ? "（强制刷新）" : ""}`);

const snapshot = await client.fetchSnapshot(targetVersion);
const details = await client.fetchDetailSnapshot(targetVersion, snapshot.manifests, {
  locale,
  concurrency: 6,
  force,
});

const detailDir = path.resolve(
  ".cache",
  "nanoka",
  targetVersion,
  "details",
  locale,
);
await mkdir(detailDir, { recursive: true });
const entries = extractNanokaBuffReviewEntries(details);
const index = {
  source: details.source,
  version: details.version,
  locale: details.locale,
  fetchedAt: details.fetchedAt,
  detailCounts: Object.fromEntries(
    Object.entries(details.details).map(([kind, values]) => [kind, Object.keys(values).length]),
  ),
  reviewEntryCount: entries.length,
  detailUrlPattern: `https://static.nanoka.cc/zzz/${targetVersion}/${locale}/{kind}/{id}.json`,
};
await writeFile(path.join(detailDir, "index.json"), JSON.stringify(index, null, 2));

const reportDir = path.resolve("reports", "buffs");
await mkdir(reportDir, { recursive: true });
const reportPath = path.join(reportDir, "nanoka-official-review-all.md");
await writeFile(reportPath, renderNanokaBuffReview(details, entries));

const batchSize = 20;
const batchPath = path.join(reportDir, "nanoka-official-review-batch-001.md");
await writeFile(
  batchPath,
  renderNanokaBuffReview(details, selectNanokaReviewBatch(entries, batchSize)),
);

console.log(`角色详情：${index.detailCounts.character}`);
console.log(`音擎详情：${index.detailCounts.weapon}`);
console.log(`驱动盘详情：${index.detailCounts.equipment}`);
console.log(`官方原文候选：${entries.length}`);
console.log(`全量审查清单：${reportPath}`);
console.log(`首批 20 条：${batchPath}`);
