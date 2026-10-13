export type QrAccount = { uid: string; nickname: string };
export type QrStatus = "created" | "scanned" | "confirmed" | "expired" | "cancelled";
export type QrSnapshot = {
  status: QrStatus;
  expires_at: string;
  poll_after_ms: number;
  accounts: QrAccount[];
  account_warning: boolean;
  session_id?: string;
  qr_image?: string;
};
export type QrAuthentication = { session_id: string; expires_at: string; accounts: QrAccount[] };

export function parseQrSnapshot(raw: unknown, creating = false): QrSnapshot {
  if (!raw || typeof raw !== "object") throw new Error("扫码登录返回格式无效，请重试。");
  const r = raw as Record<string, unknown>;
  if (r.schema_version !== "zzz-miyoushe-qr-v1" || !["created", "scanned", "confirmed", "expired", "cancelled"].includes(String(r.status))
      || typeof r.expires_at !== "string" || !Number.isFinite(Date.parse(r.expires_at))
      || typeof r.poll_after_ms !== "number" || r.poll_after_ms < 1000 || r.poll_after_ms > 10000
      || !Array.isArray(r.accounts) || r.accounts.length > 100) throw new Error("扫码登录返回格式无效，请重试。");
  const accounts = r.accounts.map((row: unknown): QrAccount => {
    if (!row || typeof row !== "object") throw new Error("游戏账号资料格式无效。");
    const a = row as Record<string, unknown>;
    if (typeof a.uid !== "string" || !/^[1-9]\d{5,8}$/.test(a.uid) || typeof a.nickname !== "string") throw new Error("游戏账号资料格式无效。");
    return { uid: a.uid, nickname: a.nickname.slice(0, 80) };
  });
  if (creating && (typeof r.session_id !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(r.session_id)
      || r.status !== "created" || typeof r.qr_image !== "string" || r.qr_image.length > 500000
      || !/^data:image\/svg\+xml;base64,[A-Za-z0-9+/=]+$/.test(r.qr_image))) throw new Error("二维码资料无效，请重新生成。");
  return { status: r.status as QrStatus, expires_at: r.expires_at, poll_after_ms: r.poll_after_ms,
    accounts, account_warning: r.account_warning === true,
    ...(creating ? { session_id: r.session_id as string, qr_image: r.qr_image as string } : {}) };
}

// A session handle stays in component memory; only role snapshots enter localStorage.
export function cancelQrSession(session_id: string) {
  void fetch("/api/v1/miyoushe/qr/cancel", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id }), keepalive: true,
  }).catch(() => undefined);
}
