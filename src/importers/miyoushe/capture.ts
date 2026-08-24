import type { Response } from "playwright-core";

export const MIYOUSHE_BASIC_ENDPOINT = "/user/avatar_basic_list";
export const MIYOUSHE_DETAIL_ENDPOINT = "/user/batch_avatar_detail_v2";

export type CapturedEndpoint = "avatar-basic-list" | "avatar-detail";

export interface CapturedMiyousheResponse {
  endpoint: CapturedEndpoint;
  url: string;
  capturedAt: string;
  payload: unknown;
}

export function classifyMiyousheUrl(url: string): CapturedEndpoint | null {
  if (url.includes(MIYOUSHE_BASIC_ENDPOINT)) return "avatar-basic-list";
  if (url.includes(MIYOUSHE_DETAIL_ENDPOINT)) return "avatar-detail";
  return null;
}

export function responseMatchesUid(url: string, uid: string): boolean {
  try {
    const parsed = new URL(url);
    const responseUid = parsed.searchParams.get("uid");
    return responseUid === null || responseUid === uid;
  } catch {
    return false;
  }
}

export async function captureMiyousheResponse(
  response: Response,
  uid: string,
): Promise<CapturedMiyousheResponse | null> {
  const endpoint = classifyMiyousheUrl(response.url());
  if (!endpoint || !responseMatchesUid(response.url(), uid) || !response.ok()) {
    return null;
  }

  const payload: unknown = await response.json();
  if (!isSuccessfulPayload(payload)) return null;

  return {
    endpoint,
    url: redactUrl(response.url()),
    capturedAt: new Date().toISOString(),
    payload,
  };
}

export function isSuccessfulPayload(payload: unknown): boolean {
  if (!payload || typeof payload !== "object") return false;
  const value = payload as { retcode?: unknown; data?: unknown };
  return value.retcode === 0 && value.data !== undefined;
}

function redactUrl(url: string): string {
  const parsed = new URL(url);
  for (const key of [...parsed.searchParams.keys()]) {
    if (!new Set(["uid", "region", "lang"]).has(key)) {
      parsed.searchParams.delete(key);
    }
  }
  return parsed.toString();
}
