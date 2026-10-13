import { useEffect, useId, useRef, useState } from "react";
import { cancelRecordVerification, loadGeetest, parseGeetestChallenge, type GeetestWidget, type RecordVerification } from "../state/miyousheVerification";
import { hostGeetestPopups } from "../state/geetestPopupHost";

type Props = {
  verification: RecordVerification;
  onSuccess: (profile: unknown) => void;
  onCancel: (message: string) => void;
  onBusyChange: (busy: boolean) => void;
};

export default function MiyousheVerification({ verification, onSuccess, onCancel, onBusyChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("本次获取信息已保留。请完成安全验证后继续获取角色。");
  const callbacks = useRef({ onSuccess, onCancel, onBusyChange });
  callbacks.current = { onSuccess, onCancel, onBusyChange };
  const generation = useRef(0);
  const request = useRef<AbortController | null>(null);
  const widget = useRef<GeetestWidget | null>(null);
  const submitting = useRef(false);
  // Bind-mode challenges must live inside the native dialog's top layer.
  // GeeTest v3 supports `area` for bind challenges; appendTo is invalid in bind.
  // https://docs.geetest.com/captcha/apirefer/api/web#product
  const challengeAreaId = `miyoushe-verification-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const challengeArea = useRef<HTMLDivElement>(null);
  const startButton = useRef<HTMLButtonElement>(null);
  const releasePopupHost = useRef<(()=>void)|null>(null);
  const readyTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clearReadyTimer = () => { if (readyTimer.current !== null) clearTimeout(readyTimer.current); readyTimer.current = null; };
  const clearWork = () => {
    generation.current += 1; request.current?.abort(); request.current = null;
    clearReadyTimer();
    widget.current?.destroy(); widget.current = null; submitting.current = false;
    releasePopupHost.current?.(); releasePopupHost.current = null;
  };
  const changeBusy = (value: boolean) => { setBusy(value); callbacks.current.onBusyChange(value); };
  const closeChallenge = () => {
    clearWork(); changeBusy(false); setMessage("已关闭验证，可以重新开始。");
    requestAnimationFrame(() => startButton.current?.focus());
  };
  useEffect(() => {
    const expire = () => { clearWork(); callbacks.current.onCancel("安全验证已过期，请重新获取角色。"); };
    const timer = setTimeout(expire, Math.max(0, Date.parse(verification.expires_at) - Date.now()));
    const leaving = () => { clearWork(); cancelRecordVerification(verification.verification_id); };
    const dialog = challengeArea.current?.closest('dialog');
    const escapeChallenge = (event:KeyboardEvent) => {
      const popup = challengeArea.current?.querySelector('.geetest_panel');
      if (event.key !== 'Escape' || submitting.current || !widget.current || !popup || getComputedStyle(popup).display === 'none') return;
      // Close only the challenge, retaining the import dialog and its login.
      event.preventDefault(); event.stopPropagation(); closeChallenge();
    };
    dialog?.addEventListener('keydown', escapeChallenge, true);
    window.addEventListener("pagehide", leaving);
    return () => { clearTimeout(timer); dialog?.removeEventListener('keydown', escapeChallenge, true); window.removeEventListener("pagehide", leaving); clearWork(); cancelRecordVerification(verification.verification_id); callbacks.current.onBusyChange(false); };
  }, [verification.verification_id, verification.expires_at]);

  const api = async (action: string, body: Record<string, unknown>, abort: AbortController) => {
    const response = await fetch(`/api/v1/miyoushe/verification/${action}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, signal: abort.signal,
      body: JSON.stringify({ verification_id: verification.verification_id, ...body }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.diagnostics?.[0]?.message ?? "安全验证失败，请重试。");
    return data;
  };

  const start = async () => {
    clearWork(); const attempt = generation.current;
    const abort = new AbortController(); request.current = abort;
    changeBusy(true); setMessage("正在打开安全验证，请在弹窗中完成操作…");
    try {
      const challenge = parseGeetestChallenge(await api("start", {}, abort));
      const init = await loadGeetest();
      if (generation.current !== attempt || abort.signal.aborted) return;
      if (!challengeArea.current) throw new Error("安全验证窗口未就绪，请重新打开验证。");
      releasePopupHost.current = hostGeetestPopups(challengeArea.current);
      readyTimer.current = setTimeout(() => {
        if (generation.current !== attempt || abort.signal.aborted) return;
        clearWork(); changeBusy(false); setMessage("安全验证窗口加载超时，请重新打开验证；无需重新登录。");
      }, 20000);
      init({ ...challenge, offline: false, product: "bind", area: `#${challengeAreaId}`, protocol: "https://", api_server: "api.geetest.com", lang: "zh-cn" }, (captcha) => {
        if (generation.current !== attempt) { captcha.destroy(); return; }
        widget.current = captcha;
        captcha.onReady(() => {
          if (generation.current !== attempt) return;
          clearReadyTimer();
          setMessage("请在安全验证窗口中完成操作；关闭后可以重新打开。");
          try { captcha.verify(); }
          catch { clearWork(); changeBusy(false); setMessage("无法打开安全验证窗口，请重新开始验证。"); }
        });
        captcha.onClose(() => {
          if (generation.current !== attempt || submitting.current) return;
          closeChallenge();
        });
        captcha.onError(() => {
          if (generation.current !== attempt || submitting.current) return;
          clearWork(); changeBusy(false); setMessage("安全验证组件连接失败，请检查网络后重试。");
        });
        captcha.onSuccess(() => {
          if (generation.current !== attempt || submitting.current) return;
          const proof = captcha.getValidate();
          if (!proof) { changeBusy(false); setMessage("请先完成安全验证。"); return; }
          submitting.current = true;
          setMessage("正在校验并继续获取角色…");
          void api("complete", { proof }, abort).then((profile) => {
            if (generation.current !== attempt || abort.signal.aborted) return;
            clearWork(); changeBusy(false); callbacks.current.onSuccess(profile);
          }).catch((error) => {
            if (generation.current !== attempt || abort.signal.aborted) return;
            clearWork(); changeBusy(false); setMessage((error as Error).message || "验证失败，请重试。");
          });
        });
      });
    } catch (error) {
      if (generation.current !== attempt || abort.signal.aborted) return;
      clearWork(); changeBusy(false); setMessage((error as Error).message || "无法打开安全验证，请重试。");
    }
  };

  return <section className="miyoushe-qr" aria-label="米游社角色安全验证">
    <div ref={challengeArea} id={challengeAreaId} className="miyoushe-verification-area" />
    <p className="miyoushe-message" role="status">{message}</p>
    <div className="miyoushe-actions">
      <button ref={startButton} className="primary-button" type="button" disabled={busy} onClick={() => { void start(); }}>{busy ? "验证中…" : "完成安全验证并继续获取"}</button>
      <button className="secondary-button" type="button" onClick={() => { clearWork(); callbacks.current.onCancel("已取消安全验证，已有角色资料仍可加载。"); }}>取消验证</button>
    </div>
  </section>;
}
