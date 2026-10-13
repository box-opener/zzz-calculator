import { useEffect, useRef, useState } from "react";
import { cancelQrSession, parseQrSnapshot, type QrAuthentication, type QrSnapshot } from "../state/miyousheQr";

type Phase = "idle" | "starting" | "error" | QrSnapshot["status"];
type Props = { busy: boolean; onAuthenticated: (authentication: QrAuthentication | null) => void };

export default function MiyousheQrLogin({ busy, onAuthenticated }: Props) {
  const [phase, setPhase] = useState<Phase>("idle");
  const [snapshot, setSnapshot] = useState<QrSnapshot | null>(null);
  const [message, setMessage] = useState("使用米游社 App 扫码，并在手机上确认登录。");
  const session = useRef<string | null>(null);
  const generation = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const request = useRef<AbortController | null>(null);

  const clearWork = () => {
    generation.current += 1;
    if (timer.current !== null) clearTimeout(timer.current);
    timer.current = null;
    request.current?.abort(); request.current = null;
    if (session.current) cancelQrSession(session.current);
    session.current = null;
  };
  useEffect(() => {
    const leaving = () => clearWork();
    window.addEventListener("pagehide", leaving);
    return () => { window.removeEventListener("pagehide", leaving); clearWork(); onAuthenticated(null); };
  }, [onAuthenticated]);

  const finish = (next: Phase, text: string) => {
    clearWork(); onAuthenticated(null);
    setSnapshot(null); setPhase(next); setMessage(text);
  };

  const poll = async (id: string, attempt: number, previous: QrSnapshot, failures = 0) => {
    if (generation.current !== attempt) return;
    if (Date.now() >= Date.parse(previous.expires_at)) {
      finish("expired", "二维码已过期，请重新生成。"); return;
    }
    const abort = new AbortController(); request.current = abort;
    try {
      const response = await fetch("/api/v1/miyoushe/qr/status", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: id }), signal: abort.signal,
      });
      const data = await response.json();
      if (generation.current !== attempt || abort.signal.aborted) return;
      if (!response.ok) {
        if ((response.status >= 500 || response.status === 429) && failures < 3) {
          setMessage("连接暂时中断，正在重试扫码状态…");
          timer.current = setTimeout(() => { void poll(id, attempt, previous, failures + 1); }, 3000);
          return;
        }
        finish("error", data.diagnostics?.[0]?.message ?? "扫码状态查询失败，请重试。");
        return;
      }
      const next = parseQrSnapshot(data);
      if (next.status === "expired" || next.status === "cancelled") {
        finish(next.status, next.status === "expired" ? "二维码已过期，请重新生成。" : "扫码登录已取消，可以重新生成二维码。"); return;
      }
      setPhase(next.status);
      if (next.status === "confirmed") {
        setSnapshot(next); // Discard the QR image and ticket as soon as confirmation arrives.
        onAuthenticated({ session_id: id, expires_at: next.expires_at, accounts: next.accounts });
        setMessage(next.account_warning ? "扫码登录成功；未能自动读取 UID，请手动输入游戏 UID。"
          : next.accounts.length > 0 ? "扫码登录成功，已读取国服游戏 UID。" : "扫码登录成功；请填写国服绝区零游戏 UID。");
        timer.current = setTimeout(() => {
          if (generation.current === attempt) finish("expired", "本次登录已到期，请重新扫码或使用手动 Cookie。");
        }, Math.max(0, Date.parse(next.expires_at) - Date.now()));
        return;
      }
      setSnapshot({ ...next, qr_image: previous.qr_image });
      setMessage(next.status === "scanned" ? "已扫描，请在米游社 App 确认登录。" : "请使用米游社 App 扫描二维码。");
      timer.current = setTimeout(() => { void poll(id, attempt, { ...next, qr_image: previous.qr_image }); }, next.poll_after_ms);
    } catch (error) {
      if (generation.current !== attempt || abort.signal.aborted) return;
      if (failures < 3) {
        setMessage("连接暂时中断，正在重试扫码状态…");
        timer.current = setTimeout(() => { void poll(id, attempt, previous, failures + 1); }, 3000);
      } else { finish("error", (error as Error).message || "扫码登录失败，请重新生成。"); }
    } finally { if (request.current === abort) request.current = null; }
  };

  const start = async () => {
    clearWork(); onAuthenticated(null); setSnapshot(null); setPhase("starting"); setMessage("正在生成二维码…");
    const attempt = generation.current;
    const abort = new AbortController(); request.current = abort;
    try {
      const response = await fetch("/api/v1/miyoushe/qr/start", { method: "POST", signal: abort.signal });
      const data = await response.json();
      if (generation.current !== attempt || abort.signal.aborted) {
        if (typeof data.session_id === "string") cancelQrSession(data.session_id);
        return;
      }
      if (!response.ok) throw new Error(data.diagnostics?.[0]?.message ?? "二维码生成失败。");
      const created = parseQrSnapshot(data, true);
      session.current = created.session_id!; setSnapshot(created); setPhase("created");
      setMessage("请使用米游社 App 扫描二维码。");
      timer.current = setTimeout(() => { void poll(created.session_id!, attempt, created); }, created.poll_after_ms);
    } catch (error) {
      if (generation.current !== attempt || abort.signal.aborted) return;
      finish("error", (error as Error).message || "二维码生成失败，请重试。");
    } finally { if (request.current === abort) request.current = null; }
  };

  return <div className="miyoushe-qr">
    {snapshot?.qr_image && <img className="miyoushe-qr-image" src={snapshot.qr_image} alt="米游社登录二维码" />}
    <p className={`miyoushe-message ${phase === "error" ? "error" : ""}`} role={phase === "error" ? "alert" : "status"}>{message}</p>
    {snapshot && <p className="roster-hint">{phase === "confirmed" ? "本次登录" : "二维码"}有效至 {new Date(snapshot.expires_at).toLocaleTimeString("zh-CN")}</p>}
    <div className="miyoushe-actions">
      <button className="secondary-button" type="button" disabled={busy || phase === "starting"} onClick={() => { void start(); }}>
        {phase === "starting" ? "生成中…" : phase === "idle" ? "生成登录二维码" : phase === "confirmed" ? "切换扫码账号" : "重新生成二维码"}
      </button>
      {["starting", "created", "scanned", "confirmed"].includes(phase) && <button className="secondary-button" type="button" disabled={busy} onClick={() => {
        finish("cancelled", phase === "confirmed" ? "已退出本次扫码登录。" : "已取消扫码登录。");
      }}>{phase === "confirmed" ? "退出登录" : "取消扫码"}</button>}
    </div>
  </div>;
}
