import { useCallback, useEffect, useRef, useState } from "react";
import MiyousheQrLogin from "./MiyousheQrLogin";
import MiyousheVerification from "./MiyousheVerification";
import { parseRecordVerification, type RecordVerification } from "../state/miyousheVerification";
import type { QrAuthentication } from "../state/miyousheQr";
import type { CharacterConfig, EquipmentValidationCatalog } from "../state/equipmentConfig";
import { sortCharactersById } from "../state/characterLibrary";
import {
  MIYOUSHE_STORAGE_KEY, readMiyousheProfiles, saveMiyousheProfile, validateMiyousheProfile,
  type MiyousheProfile, type MiyousheCharacter,
} from "../state/miyousheProfiles";

type Props = {
  catalog: EquipmentValidationCatalog;
  ready: boolean;
  supportedCharacterIds: string[];
  onLoad: (configuration: CharacterConfig, character: MiyousheCharacter) => void;
};

export default function MiyoushePanel({ catalog, ready, supportedCharacterIds, onLoad }: Props) {
  const [uid, setUid] = useState("");
  const [cookie, setCookie] = useState("");
  const [loginMode, setLoginMode] = useState<"qr" | "cookie">("qr");
  const [qrAuthentication, setQrAuthentication] = useState<QrAuthentication | null>(null);
  const [profiles, setProfiles] = useState<MiyousheProfile[]>([]);
  const [activeUid, setActiveUid] = useState("");
  const [fetchBusy, setBusy] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verification, setVerification] = useState<RecordVerification | null>(null);
  const busy = fetchBusy || verifying;
  const [message, setMessage] = useState("");
  const [failed, setFailed] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const hydrated = useRef(false);
  useEffect(() => {
    if (!ready || hydrated.current) return;
    hydrated.current = true;
    try {
      const saved = readMiyousheProfiles(window.localStorage, catalog);
      setProfiles(saved);
      setActiveUid(saved[0]?.uid ?? "");
      setUid(saved[0]?.uid ?? "");
    } catch {
      setFailed(true);
      setMessage("本地角色资料无法读取；可以清除资料后重新获取。");
    }
  }, [ready, catalog]);
  useEffect(() => () => controller.current?.abort(), []);
  const active = profiles.find((p) => p.uid === activeUid);
  const authenticated = useCallback((auth: QrAuthentication | null) => {
    setQrAuthentication(auth);
    if (!auth) setVerification(null);
    if (auth?.accounts.length) setUid((current) => auth.accounts.some((a) => a.uid === current) ? current : auth.accounts[0].uid);
  }, []);

  const saveProfile = (data: unknown) => {
    const incoming = validateMiyousheProfile(data, catalog);
    const next = saveMiyousheProfile(profiles, incoming);
    setProfiles(next); setActiveUid(incoming.uid);
    setVerification(null); setFailed(false);
    try {
      window.localStorage.setItem(MIYOUSHE_STORAGE_KEY, JSON.stringify(next));
      setMessage(`已获取并保存 ${incoming.characters.length} 个角色，可选择加载。`);
    } catch {
      setFailed(true); setMessage("角色已获取，但浏览器无法保存本地资料；本次仍可加载。");
    }
  };

  const fetchCharacters = async () => {
    if (!/^[1-9]\d{5,8}$/.test(uid.trim()) || (loginMode === "cookie" ? !cookie.trim() : !qrAuthentication)) {
      setFailed(true);
      setMessage(loginMode === "cookie" ? "请输入国服绝区零游戏 UID 和米游社登录 Cookie。" : "请先完成扫码登录并填写国服游戏 UID。");
      return;
    }
    const authentication = loginMode === "qr" ? { qr_session: qrAuthentication!.session_id } : { cookie };
    setCookie("");
    const abort = new AbortController();
    controller.current?.abort();
    controller.current = abort;
    setBusy(true); setFailed(false); setMessage("正在获取角色及装备，请稍候…");
    try {
      const response = await fetch("/api/v1/miyoushe/characters", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid: uid.trim(), ...authentication }), signal: abort.signal,
      });
      const data = await response.json();
      if (controller.current !== abort || abort.signal.aborted) return;
      if (!response.ok) {
        if (response.status === 428 && data.verification) {
          setVerification(parseRecordVerification(data.verification));
          setFailed(true); setMessage(loginMode === "qr" ? "角色战绩需要安全验证，请点击下方按钮继续；无需重新扫码。" : "角色战绩需要安全验证，请点击下方按钮继续；无需重新填写 Cookie。");
          return;
        }
        throw new Error(data.diagnostics?.[0]?.message ?? "米游社角色获取失败。");
      }
      saveProfile(data);
    } catch (error) {
      if (controller.current !== abort || abort.signal.aborted || (error as Error).name === "AbortError") return;
      setFailed(true); setMessage((error as Error).message || "网络连接失败，请重试。");
    } finally {
      if (controller.current === abort) { setBusy(false); controller.current = null; }
    }
  };

  const clearSaved = () => {
    try {
      window.localStorage.removeItem(MIYOUSHE_STORAGE_KEY);
      setProfiles([]); setActiveUid(""); setFailed(false); setMessage("已清除本地米游社角色资料。");
    } catch { setFailed(true); setMessage("浏览器无法清除本地资料。"); }
  };

  return <details className="miyoushe-panel">
    <summary>从米游社加载我的角色</summary>
    <p className="roster-hint">可使用米游社 App 扫码或手动 Cookie 获取国服角色。角色资料保存在当前浏览器，登录凭据不保存到本地。</p>
    <form onSubmit={(e) => { e.preventDefault(); void fetchCharacters(); }} className="miyoushe-form">
      <div className="miyoushe-actions" role="tablist" aria-label="米游社登录方式">
        {(["qr", "cookie"] as const).map((mode) => <button key={mode} type="button" role="tab" aria-selected={loginMode === mode}
          className={loginMode === mode ? "primary-button" : "secondary-button"} disabled={busy} onClick={() => {
            if (loginMode === mode) return;
            setLoginMode(mode); setQrAuthentication(null); setCookie(""); setVerification(null); setMessage(""); setFailed(false);
          }}>{mode === "qr" ? "扫码登录" : "手动 Cookie"}</button>)}
      </div>
      {loginMode === "qr" && <MiyousheQrLogin busy={busy} onAuthenticated={authenticated} />}
      {loginMode === "qr" && qrAuthentication && qrAuthentication.accounts.length > 1 && <label className="select-field"><span>扫码账号的国服角色</span>
        <select value={uid} disabled={busy} onChange={(e) => setUid(e.target.value)}>
          {qrAuthentication.accounts.map((a) => <option key={a.uid} value={a.uid}>{a.nickname} · {a.uid}</option>)}
        </select></label>}
      <label className="select-field"><span>绝区零游戏 UID</span>
        <input aria-label="米游社游戏 UID" value={uid} inputMode="numeric" maxLength={9} disabled={busy} onChange={(e) => setUid(e.target.value)} placeholder="国服游戏 UID" />
      </label>
      <label className="select-field miyoushe-manual-cookie" hidden={loginMode !== "cookie"}><span>米游社 Cookie</span>
        <input aria-label="米游社 Cookie" type="password" autoComplete="off" spellCheck={false} maxLength={16384} value={cookie} disabled={busy} onChange={(e) => setCookie(e.target.value)} placeholder="登录米游社后复制战绩请求的 Cookie" />
      </label>
      <div className="miyoushe-actions">
        <button className="primary-button" type="submit" disabled={!ready || busy || verification !== null || (loginMode === "qr" && !qrAuthentication)}>{fetchBusy ? "获取中…" : "获取并保存角色"}</button>
        {fetchBusy && <button className="secondary-button" type="button" onClick={() => { controller.current?.abort(); setBusy(false); setFailed(false); setMessage("已取消获取。"); }}>取消</button>}
        <button className="secondary-button" type="button" disabled={busy} onClick={clearSaved}>清除本地资料</button>
      </div>
    </form>
    {message && <p className={`miyoushe-message ${failed ? "error" : ""}`} role={failed ? "alert" : "status"}>{message}</p>}
    {verification && <MiyousheVerification key={verification.verification_id} verification={verification} onBusyChange={setVerifying}
      onSuccess={(data) => { try { saveProfile(data); } catch { setFailed(true); setMessage("获取结果无法加载，请重新获取角色。"); setVerification(null); } }}
      onCancel={(text) => { setVerification(null); setVerifying(false); setFailed(false); setMessage(text); }} />}
    {profiles.length > 0 && <>
      <label className="select-field"><span>已保存账号（离线可加载）</span><select disabled={busy} value={activeUid} onChange={(e) => { setActiveUid(e.target.value); setUid(e.target.value); }}>
        {profiles.map((p) => <option key={p.uid} value={p.uid}>{p.uid} · {p.characters.length} 个角色</option>)}
      </select></label>
      {active && <>
        <p className="roster-hint">获取时间：{new Date(active.fetched_at).toLocaleString("zh-CN")}</p>
        {active.characters.length === 0 && <p className="muted">此账号未返回角色，请检查 UID 与战绩设置。</p>}
        <div className="miyoushe-characters">
          {sortCharactersById(active.characters).map((c) => <article key={c.character_id}>
            <div><strong>{c.display_name}</strong><small>{c.level ?? "?"}级 · {c.cinema ?? "?"}影</small>
              {c.issues.map((issue, i) => <p key={i} className="roster-hint">{issue}</p>)}
              {!supportedCharacterIds.includes(c.character_id) && <p className="roster-hint">此版本尚未支持该角色。</p>}
            </div>
            <button className="secondary-button" type="button" disabled={!ready || busy || !c.configuration || !supportedCharacterIds.includes(c.character_id)} onClick={() => {
              if (c.configuration) { onLoad(c.configuration, c); setFailed(false); setMessage(`已加载 ${c.display_name} 的真实配置。`); }
            }}>加载到当前槽位</button>
          </article>)}
        </div>
      </>}
    </>}
  </details>;
}
