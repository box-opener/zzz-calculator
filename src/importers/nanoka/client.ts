import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const SITE_URL = "https://zzz.nanoka.cc/character";
const CDN_ROOT = "https://static.nanoka.cc/zzz";
const MANIFESTS = [
  "character",
  "weapon",
  "equipment",
  "monster",
  "boss",
] as const;

export const DETAIL_KINDS = ["character", "weapon", "equipment"] as const;
export type NanokaDetailKind = (typeof DETAIL_KINDS)[number];
export type NanokaLocale = "zh" | "en";

export type NanokaManifestName = (typeof MANIFESTS)[number];
export type NanokaManifest = Record<string, unknown>;

export interface NanokaSnapshot {
  source: "nanoka.cc";
  version: string;
  fetchedAt: string;
  manifests: Record<NanokaManifestName, NanokaManifest>;
}

export interface NanokaClientOptions {
  cacheDir?: string;
  userAgent?: string;
}

export interface FetchNanokaSnapshotOptions {
  legacyManifestDir?: string;
}

export interface NanokaDetailFetchOptions {
  locale?: NanokaLocale;
  ids?: Partial<Record<NanokaDetailKind, readonly string[]>>;
  concurrency?: number;
  force?: boolean;
}

export interface NanokaDetailSnapshot {
  source: "nanoka.cc";
  version: string;
  locale: NanokaLocale;
  fetchedAt: string;
  details: Record<NanokaDetailKind, Record<string, NanokaManifest>>;
}

export class NanokaClient {
  private readonly cacheDir: string;
  private readonly userAgent: string;

  constructor(options: NanokaClientOptions = {}) {
    this.cacheDir = options.cacheDir ?? ".cache/nanoka";
    this.userAgent = options.userAgent ?? "zzz-calculator-next/0.1";
  }

  async discoverLatestVersion(): Promise<string> {
    const html = await this.fetchText(SITE_URL);
    return parseNanokaVersion(html);
  }

  async fetchSnapshot(
    version: string,
    options: FetchNanokaSnapshotOptions = {},
  ): Promise<NanokaSnapshot> {
    assertNanokaVersion(version);
    const manifests = {} as Record<NanokaManifestName, NanokaManifest>;
    for (const name of MANIFESTS) {
      manifests[name] = await this.fetchManifest(
        version,
        name,
        options.legacyManifestDir,
      );
    }
    return {
      source: "nanoka.cc",
      version,
      fetchedAt: new Date().toISOString(),
      manifests,
    };
  }

  /**
   * 下载角色、音擎和驱动盘的官方详情 JSON。
   *
   * 详情接口只允许走 Nanoka CDN，不接受旧 archive 回退。旧 manifest
   * 可以用于版本差异计算，但不能冒充技能/Buff 原文。
   */
  async fetchDetail(
    version: string,
    kind: NanokaDetailKind,
    id: string,
    options: Pick<NanokaDetailFetchOptions, "locale" | "force"> = {},
  ): Promise<NanokaManifest> {
    assertNanokaVersion(version);
    assertNanokaDetailId(id);
    const locale = options.locale ?? "zh";
    const cachePath = this.detailCachePath(version, locale, kind, id);
    if (!options.force) {
      try {
        return parseObject(await readFile(cachePath, "utf8"), cachePath);
      } catch {
        // 未缓存时继续请求 Nanoka；详情数据不允许从旧本地文件回退。
      }
    }

    const url = buildNanokaDetailUrl(version, locale, kind, id);
    const payload = parseObject(await this.fetchText(url), url);
    await mkdir(path.dirname(cachePath), { recursive: true });
    await writeFile(cachePath, JSON.stringify(payload, null, 2));
    return payload;
  }

  async fetchDetailSnapshot(
    version: string,
    manifests: Pick<NanokaSnapshot["manifests"], NanokaDetailKind>,
    options: NanokaDetailFetchOptions = {},
  ): Promise<NanokaDetailSnapshot> {
    assertNanokaVersion(version);
    const locale = options.locale ?? "zh";
    const concurrency = normalizeConcurrency(options.concurrency ?? 6);
    const result = {} as NanokaDetailSnapshot["details"];

    for (const kind of DETAIL_KINDS) {
      const ids = [
        ...new Set(options.ids?.[kind] ?? Object.keys(manifests[kind])),
      ].sort(compareIds);
      const entries = await mapWithConcurrency(ids, concurrency, async (id) => [
        id,
        await this.fetchDetail(
          version,
          kind,
          id,
          options.force === undefined
            ? { locale }
            : { locale, force: options.force },
        ),
      ] as const);
      result[kind] = Object.fromEntries(entries);
    }

    return {
      source: "nanoka.cc",
      version,
      locale,
      fetchedAt: new Date().toISOString(),
      details: result,
    };
  }

  detailCachePath(
    version: string,
    locale: NanokaLocale,
    kind: NanokaDetailKind,
    id: string,
  ): string {
    return path.join(this.cacheDir, version, "details", locale, kind, `${id}.json`);
  }

  private async fetchManifest(
    version: string,
    name: NanokaManifestName,
    legacyManifestDir?: string,
  ): Promise<NanokaManifest> {
    const cachePath = path.join(this.cacheDir, version, `${name}.json`);
    try {
      return JSON.parse(await readFile(cachePath, "utf8")) as NanokaManifest;
    } catch {
      const url = `${CDN_ROOT}/${version}/${name}.json`;
      let payload: unknown;
      try {
        payload = JSON.parse(await this.fetchText(url)) as unknown;
      } catch (networkError) {
        if (!legacyManifestDir) throw networkError;
        payload = await this.readLegacyManifest(legacyManifestDir, name);
      }
      if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        throw new Error(`Nanoka ${name}.json 不是对象结构。`);
      }
      await mkdir(path.dirname(cachePath), { recursive: true });
      await writeFile(cachePath, JSON.stringify(payload, null, 2));
      return payload as NanokaManifest;
    }
  }

  private async readLegacyManifest(
    directory: string,
    name: NanokaManifestName,
  ): Promise<unknown> {
    const filename =
      name === "boss" ? "sample_detail_boss.json" : `full_${name}.json`;
    try {
      return JSON.parse(
        await readFile(path.join(directory, filename), "utf8"),
      ) as unknown;
    } catch (error) {
      throw new Error(`缺少旧版 Nanoka 本地快照：${filename} (${String(error)})`);
    }
  }

  private async fetchText(url: string): Promise<string> {
    const response = await fetch(url, {
      headers: { "User-Agent": this.userAgent },
    });
    if (!response.ok) {
      throw new Error(`Nanoka 请求失败：HTTP ${response.status} (${url})`);
    }
    return response.text();
  }
}

export function buildNanokaDetailUrl(
  version: string,
  locale: NanokaLocale,
  kind: NanokaDetailKind,
  id: string,
): string {
  assertNanokaVersion(version);
  assertNanokaDetailId(id);
  return `${CDN_ROOT}/${version}/${locale}/${kind}/${id}.json`;
}

export function assertNanokaDetailId(id: string): void {
  if (!/^\d+$/.test(id)) {
    throw new Error(`Nanoka 详情 ID 无效：${id}`);
  }
}

export function parseNanokaVersion(html: string): string {
  const match = html.match(
    /static\.nanoka\.cc\/zzz\/([^/"']+)\/character\.json/,
  );
  if (!match?.[1]) throw new Error("无法从 Nanoka 角色页识别数据版本。");
  assertNanokaVersion(match[1]);
  return match[1];
}

export function assertNanokaVersion(version: string): void {
  if (!/^\d+\.\d+\.\d+\+\d+$/.test(version)) {
    throw new Error(`Nanoka 数据版本格式无效：${version}`);
  }
}

function parseObject(text: string, source: string): NanokaManifest {
  let payload: unknown;
  try {
    payload = JSON.parse(text) as unknown;
  } catch (error) {
    throw new Error(`Nanoka JSON 解析失败：${source} (${String(error)})`);
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new Error(`Nanoka JSON 不是对象结构：${source}`);
  }
  return payload as NanokaManifest;
}

function normalizeConcurrency(value: number): number {
  if (!Number.isInteger(value) || value < 1 || value > 32) {
    throw new Error(`Nanoka 并发数应为 1 到 32：${value}`);
  }
  return value;
}

async function mapWithConcurrency<T, R>(
  values: readonly T[],
  concurrency: number,
  worker: (value: T) => Promise<R>,
): Promise<R[]> {
  const results = new Array<R>(values.length);
  let nextIndex = 0;
  async function consume(): Promise<void> {
    while (true) {
      const index = nextIndex++;
      if (index >= values.length) return;
      results[index] = await worker(values[index] as T);
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, values.length) }, () => consume()),
  );
  return results;
}

function compareIds(left: string, right: string): number {
  return Number(left) - Number(right) || left.localeCompare(right);
}
