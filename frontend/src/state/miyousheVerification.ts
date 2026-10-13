export type RecordVerification = { verification_id: string; expires_at: string };
export type GeetestProof = { geetest_challenge: string; geetest_validate: string; geetest_seccode: string };
export type GeetestChallenge = { gt: string; challenge: string; new_captcha: boolean; success: 1 };

export function parseRecordVerification(raw: unknown): RecordVerification {
  if (!raw || typeof raw !== "object") throw new Error("验证会话格式无效，请重新获取角色。");
  const value = raw as Record<string, unknown>;
  if (typeof value.verification_id !== "string" || !/^[A-Za-z0-9_-]{43}$/.test(value.verification_id)
      || typeof value.expires_at !== "string" || !Number.isFinite(Date.parse(value.expires_at))) throw new Error("验证会话格式无效，请重新获取角色。");
  return { verification_id: value.verification_id, expires_at: value.expires_at };
}

export function parseGeetestChallenge(raw: unknown): GeetestChallenge {
  if (!raw || typeof raw !== "object") throw new Error("验证参数格式无效，请重新开始验证。");
  const value = raw as Record<string, unknown>;
  if (value.schema_version !== "zzz-miyoushe-verification-v1" || value.success !== 1
      || typeof value.gt !== "string" || value.gt.length < 1 || value.gt.length > 128
      || typeof value.challenge !== "string" || value.challenge.length < 1 || value.challenge.length > 128) throw new Error("验证暂不可用，请重新开始验证。");
  return { gt: value.gt, challenge: value.challenge, new_captcha: value.new_captcha === true, success: 1 };
}

export function cancelRecordVerification(verification_id: string) {
  void fetch("/api/v1/miyoushe/verification/cancel", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ verification_id }), keepalive: true,
  }).catch(() => undefined);
}

export type GeetestWidget = {
  onReady: (callback: () => void) => void;
  onSuccess: (callback: () => void) => void;
  onClose: (callback: () => void) => void;
  onError: (callback: () => void) => void;
  verify: () => void;
  getValidate: () => GeetestProof | false;
  destroy: () => void;
};
type InitGeetest = (options: Record<string, unknown>, ready: (widget: GeetestWidget) => void) => void;
declare global { interface Window { initGeetest?: InitGeetest } }
let loading: Promise<InitGeetest> | null = null;

export function loadGeetest(): Promise<InitGeetest> {
  if (window.initGeetest) return Promise.resolve(window.initGeetest);
  if (loading) return loading;
  loading = new Promise<InitGeetest>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://static.geetest.com/static/js/gt.0.5.2.js";
    script.async = true; script.referrerPolicy = "no-referrer";
    const timeout = setTimeout(() => { script.remove(); reject(new Error("安全验证组件加载超时，请检查网络后重试。")); }, 15000);
    script.onload = () => { clearTimeout(timeout); if (window.initGeetest) resolve(window.initGeetest); else reject(new Error("安全验证组件不可用。")); };
    script.onerror = () => { clearTimeout(timeout); script.remove(); reject(new Error("安全验证组件加载失败，请检查网络后重试。")); };
    document.head.appendChild(script);
  }).catch((error) => { loading = null; throw error; });
  return loading;
}
