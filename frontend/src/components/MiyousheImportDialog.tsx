import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import type { DriveDiscConfig } from "../state/driveDiscState";

type MiyousheRole = {
  uid: string;
  nickname: string;
  level: number | null;
  region: string;
  game_biz: string;
};

type LoginStartResponse = {
  session_id: string;
  qr_url: string;
};

type LoginPollResponse = {
  status: "Created" | "Scanned" | "Confirmed";
  qr_url?: string;
  roles?: MiyousheRole[];
};

type MiyousheImportDialogProps = {
  characterId: string;
  onClose: () => void;
  onApply: (preview: MiyousheImportPreview) => void;
};

export type MiyousheImportPreview = {
  character_id: string;
  display_name: string;
  character_level: number | null;
  compile_config: {
    cinema_level?: number;
    core_level?: number;
    skill_levels?: Record<string, number>;
  };
  wengine: { id: string; level: number; refinement?: number; source_base_value?: number; source_advanced_stat_value?: number } | null;
  wengine_present: boolean;
  wengine_explicit_null: boolean;
  drive_discs: DriveDiscConfig[];
  drive_discs_present: boolean;
  drive_discs_explicit_null: boolean;
  diagnostics: { code: string; message: string; blocking: boolean }[];
  can_apply: boolean;
};

async function jsonRequest<T>(
  path: string,
  body?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
    signal,
  });
  const result = await response.json() as T & { message?: string };
  if (!response.ok) throw new Error(result.message ?? "米游社请求失败，请稍后重试。");
  return result;
}

export default function MiyousheImportDialog({ characterId, onClose, onApply }: MiyousheImportDialogProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const previewAbortRef = useRef<AbortController | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<LoginPollResponse["status"]>("Created");
  const [roles, setRoles] = useState<MiyousheRole[]>([]);
  const [selectedUid, setSelectedUid] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(true);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [preview, setPreview] = useState<MiyousheImportPreview | null>(null);

  useEffect(() => {
    let disposed = false;
    let polling = false;
    let done = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let activeSessionId: string | null = null;
    const abortController = new AbortController();

    const start = async () => {
      try {
        const result = await jsonRequest<LoginStartResponse>(
          "/api/v1/miyoushe/login/start",
          undefined,
          abortController.signal,
        );
        if (disposed) {
          void jsonRequest("/api/v1/miyoushe/logout", { session_id: result.session_id }).catch(() => undefined);
          return;
        }
        activeSessionId = result.session_id;
        setSessionId(result.session_id);
        setQrUrl(result.qr_url);
        setStarting(false);
        timer = setTimeout(() => void poll(), 1200);
      } catch (requestError) {
        if (!disposed) {
          setError((requestError as Error).message);
          setStarting(false);
        }
      }
    };

    const poll = async () => {
      if (disposed || polling || done || !activeSessionId) return;
      polling = true;
      try {
        const result = await jsonRequest<LoginPollResponse>("/api/v1/miyoushe/login/poll", {
          session_id: activeSessionId,
        }, abortController.signal);
        if (disposed) return;
        setStatus(result.status);
        if (result.qr_url) setQrUrl(result.qr_url);
        if (result.roles) {
          done = true;
          setRoles(result.roles);
          setSelectedUid(result.roles[0]?.uid ?? "");
        }
      } catch (requestError) {
        if (!disposed) {
          done = true;
          setError((requestError as Error).message);
        }
      } finally {
        polling = false;
        if (!disposed && !done) timer = setTimeout(() => void poll(), 1200);
      }
    };

    void start();

    return () => {
      disposed = true;
      abortController.abort();
      previewAbortRef.current?.abort();
      if (timer) clearTimeout(timer);
    };
  }, []);

  useEffect(() => {
    if (!qrUrl || !canvasRef.current) return;
    void QRCode.toCanvas(canvasRef.current, qrUrl, {
      width: 224,
      margin: 1,
      errorCorrectionLevel: "L",
    }).catch(() => setError("二维码生成失败，请关闭后重试。"));
  }, [qrUrl]);

  const close = () => {
    previewAbortRef.current?.abort();
    if (sessionId) {
      void jsonRequest("/api/v1/miyoushe/logout", { session_id: sessionId }).catch(() => undefined);
    }
    onClose();
  };

  const readSelectedCharacter = async () => {
    if (!sessionId || !selectedUid) return;
    previewAbortRef.current?.abort();
    const abortController = new AbortController();
    previewAbortRef.current = abortController;
    setLoadingPreview(true);
    setError(null);
    try {
      const result = await jsonRequest<MiyousheImportPreview>(
        "/api/v1/miyoushe/import/preview",
        {
          session_id: sessionId,
          role_uid: selectedUid,
          character_id: characterId,
        },
        abortController.signal,
      );
      setPreview(result);
    } catch (requestError) {
      if (!abortController.signal.aborted) setError((requestError as Error).message);
    } finally {
      if (!abortController.signal.aborted) setLoadingPreview(false);
    }
  };

  return (
    <div className="miyoushe-modal-overlay" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) close();
    }}>
      <section className="miyoushe-import-dialog" role="dialog" aria-modal="true" aria-labelledby="miyoushe-import-title">
        <header className="miyoushe-dialog-header">
          <div>
            <span className="eyebrow">MIYOUSHE · CN</span>
            <h2 id="miyoushe-import-title">米游社角色导入</h2>
          </div>
          <button className="icon-button" type="button" aria-label="关闭米游社导入" onClick={close}>×</button>
        </header>
        {starting ? (
          <p className="miyoushe-dialog-status">正在连接米游社官方登录服务…</p>
        ) : error && !sessionId ? (
          <div className="miyoushe-dialog-error" role="alert">
            <p>{error}</p>
            <button className="secondary-button" type="button" onClick={close}>关闭</button>
          </div>
        ) : status !== "Confirmed" ? (
          <div className="miyoushe-login-step">
            <canvas ref={canvasRef} className="miyoushe-login-qr" aria-label="米游社官方扫码登录二维码" />
            {error && <p className="miyoushe-dialog-inline-error" role="alert">{error}</p>}
            <p className="miyoushe-dialog-status">
              {status === "Scanned" ? "已扫码，请在米游社 App 中确认登录。" : "请使用米游社 App 扫描二维码并确认授权。"}
            </p>
            <small>授权只用于读取当前绝区零账号的养成数据。</small>
            <button className="secondary-button" type="button" onClick={close}>取消</button>
          </div>
        ) : preview ? (
          <div className="miyoushe-preview-step">
            <p className="miyoushe-dialog-status">
              {preview.display_name} · 等级 {preview.character_level ?? "未导入（本地白值数据不足）"}
            </p>
            <div className="miyoushe-preview-summary">
              <span>影画：{typeof preview.compile_config.cinema_level === "number" ? `M${preview.compile_config.cinema_level}` : "未提供，保留当前值"}</span>
              <span>技能等级：{preview.compile_config.skill_levels ? "已读取" : "未确认，保留当前值"}</span>
              <span>音擎：{preview.wengine ? preview.wengine.id : preview.wengine_explicit_null ? "未装备" : "无完整可映射数据"}</span>
              <span>驱动盘：{preview.drive_discs.length} 个槽位有可映射数据</span>
            </div>
            {preview.diagnostics.length > 0 && <ul className="miyoushe-preview-warnings">
              {preview.diagnostics.map((item, index) => <li key={`${item.code}-${index}`}>{item.message}</li>)}
            </ul>}
            <p className="miyoushe-preview-note">仅点击应用后才会更新此角色的已确认字段；缺失或未确认的数据会保留，并在诊断中说明。</p>
            <div className="miyoushe-dialog-actions">
              <button className="secondary-button" type="button" onClick={() => setPreview(null)}>返回角色选择</button>
              <button className="primary-button" type="button" disabled={!preview.can_apply} onClick={() => {
                onApply(preview);
                close();
              }}>应用到当前角色</button>
            </div>
          </div>
        ) : (
          <div className="miyoushe-role-step">
            <p className="miyoushe-dialog-status">已连接米游社，请选择绝区零国服角色。</p>
            {error && <p className="miyoushe-dialog-inline-error" role="alert">{error}</p>}
            <label className="miyoushe-role-field">
              <span>游戏角色 / UID</span>
              <select value={selectedUid} onChange={(event) => setSelectedUid(event.target.value)}>
                {roles.map((role) => (
                  <option key={`${role.game_biz}-${role.uid}-${role.region}`} value={role.uid}>
                    {role.nickname || "绝区零角色"} · {role.uid} · {role.region}{role.level === null ? "" : ` · 绳网等级 ${role.level}`}
                  </option>
                ))}
              </select>
            </label>
            <div className="miyoushe-dialog-actions">
              <button className="secondary-button" type="button" onClick={close}>取消</button>
              <button className="primary-button" type="button" disabled={!sessionId || !selectedUid || loadingPreview} onClick={() => void readSelectedCharacter()}>
                {loadingPreview ? "读取中…" : "读取角色数据"}
              </button>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
