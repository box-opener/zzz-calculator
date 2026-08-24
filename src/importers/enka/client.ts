import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import type { EnkaResponse } from "./types.js";

interface CacheEnvelope {
  fetchedAt: string;
  expiresAt: string;
  payload: EnkaResponse;
}

export interface EnkaFetchResult {
  data: EnkaResponse;
  fromCache: boolean;
  stale: boolean;
  warning?: string;
}

export class EnkaUidError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "EnkaUidError";
  }
}

export interface EnkaUidClientOptions {
  endpoint?: string;
  userAgent?: string;
  cacheDir?: string;
  timeoutMs?: number;
}

export class EnkaUidClient {
  private readonly endpoint: string;
  private readonly userAgent: string;
  private readonly cacheDir: string;
  private readonly timeoutMs: number;

  constructor(options: EnkaUidClientOptions = {}) {
    this.endpoint = options.endpoint ?? "https://enka.network/api/zzz/uid";
    this.userAgent = options.userAgent ?? "zzz-calculator-next/0.1";
    this.cacheDir = options.cacheDir ?? ".cache/uid/enka";
    this.timeoutMs = options.timeoutMs ?? 15_000;
  }

  async fetch(uid: string): Promise<EnkaFetchResult> {
    if (!/^\d{8,10}$/.test(uid)) {
      throw new EnkaUidError("绝区零 UID 应为 8 到 10 位数字。", 400);
    }

    const cache = await this.readCache(uid);
    if (cache && Date.parse(cache.expiresAt) > Date.now()) {
      return { data: cache.payload, fromCache: true, stale: false };
    }

    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      let response: Response;
      try {
        response = await fetch(`${this.endpoint}/${uid}`, {
          headers: { "User-Agent": this.userAgent },
          signal: controller.signal,
        });
      } finally {
        clearTimeout(timer);
      }

      const payload = (await response.json()) as EnkaResponse & {
        message?: string;
      };
      if (!response.ok) {
        throw new EnkaUidError(
          payload.message ?? `Enka 请求失败：HTTP ${response.status}`,
          response.status,
        );
      }

      await this.writeCache(uid, payload);
      return { data: payload, fromCache: false, stale: false };
    } catch (error) {
      if (cache) {
        return {
          data: cache.payload,
          fromCache: true,
          stale: true,
          warning: `UID 服务暂时不可用，已使用过期缓存：${String(error)}`,
        };
      }
      if (error instanceof EnkaUidError) throw error;
      throw new EnkaUidError(`无法访问 UID 服务：${String(error)}`);
    }
  }

  private cachePath(uid: string): string {
    return path.join(this.cacheDir, `${uid}.json`);
  }

  private async readCache(uid: string): Promise<CacheEnvelope | null> {
    try {
      return JSON.parse(
        await readFile(this.cachePath(uid), "utf8"),
      ) as CacheEnvelope;
    } catch {
      return null;
    }
  }

  private async writeCache(uid: string, payload: EnkaResponse): Promise<void> {
    const ttlSeconds = Math.max(payload.ttl ?? 300, 1);
    const envelope: CacheEnvelope = {
      fetchedAt: new Date().toISOString(),
      expiresAt: new Date(Date.now() + ttlSeconds * 1000).toISOString(),
      payload,
    };
    await mkdir(this.cacheDir, { recursive: true });
    await writeFile(this.cachePath(uid), JSON.stringify(envelope, null, 2));
  }
}

