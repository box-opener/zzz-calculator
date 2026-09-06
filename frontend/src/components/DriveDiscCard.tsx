import { useMemo, useState } from "react";
import {
  isDriveDiscComplete,
  type DriveDiscConfig,
  type DriveDiscSlotSchema,
  type DriveDiscStatOption,
  type DriveDiscSubstat,
} from "../state/driveDiscState";

export type DriveDiscSetInfo = {
  set_id: string;
  display_name: string;
  icon_path: string;
  two_piece_text: string;
  four_piece_text: string;
};

export type DriveDiscPreview = {
  slot: number;
  set_id: string;
  set_name: string;
  main_stat: DriveDiscStatPreview | null;
  substats: DriveDiscStatPreview[];
  total_rolls: number;
  complete: boolean;
};

export type DriveDiscStatPreview = {
  stat_key: string;
  label: string;
  value_per_roll: number;
  display_value_per_roll: string;
  roll_count: number;
  total_value: number;
  display_total_value: string;
};

export type DriveDiscCardProps = {
  schema: DriveDiscSlotSchema;
  disc: DriveDiscConfig | undefined;
  preview: DriveDiscPreview | undefined;
  driveDiscSets: readonly DriveDiscSetInfo[];
  substatOptions: readonly DriveDiscStatOption[];
  diagnostics: readonly { diagnostic_id: string; message: string; blocking: boolean }[];
  onSelectSet: (setId: string) => void;
  onUpdateMain: (mainStat: string) => void;
  onUpdateSubstat: (index: number, next: DriveDiscSubstat) => void;
  onUpdateRoll: (index: number, delta: number) => void;
  onRemoveSubstat: (index: number) => void;
  onAddSubstat: (stat: string) => void;
  formatValue: (stat: string, value: number) => string;
};

export function DriveDiscCard({
  schema,
  disc,
  preview,
  driveDiscSets,
  substatOptions,
  diagnostics,
  onSelectSet,
  onUpdateMain,
  onUpdateSubstat,
  onUpdateRoll,
  onRemoveSubstat,
  onAddSubstat,
  formatValue,
}: DriveDiscCardProps) {
  const [pendingAddStat, setPendingAddStat] = useState("");
  const set = driveDiscSets.find((item) => item.set_id === disc?.set_id);
  const complete = Boolean(disc && isDriveDiscComplete(disc));
  const usedSubstats = useMemo(() => new Set(disc?.substats.map((item) => item.stat) ?? []), [disc]);
  const availableSubstats = substatOptions.filter(
    (item) => item.stat_key !== disc?.main_stat && !usedSubstats.has(item.stat_key),
  );
  const totalRolls = disc?.substats.reduce((sum, item) => sum + item.roll_count, 0) ?? 0;

  return (
    <article
      className={`drive-disc-card ${complete ? "drive-disc-complete" : "drive-disc-incomplete"}`}
      title={set ? `2件套：${set.two_piece_text}\n4件套：${set.four_piece_text}` : undefined}
    >
      <header className="drive-disc-card-header">
        <div className="drive-disc-identity">
          {set ? (
            <img alt="" src={set.icon_path} />
          ) : (
            <span className="drive-disc-placeholder" aria-hidden="true">{schema.slot}</span>
          )}
          <div>
            <span className="drive-disc-slot">SLOT {schema.slot}</span>
            <strong>{set?.display_name ?? "未装备驱动盘"}</strong>
          </div>
        </div>
        <span className={`drive-disc-status ${complete ? "complete" : "incomplete"}`}>
          {complete ? "完整" : disc ? "未完成" : "空槽"}
        </span>
      </header>

      <div className="drive-disc-section drive-disc-set-section">
        <div className="drive-disc-section-heading">
          <span>套装</span>
          <small>{set ? "已选择套装" : "先选择套装"}</small>
        </div>
        <select
          aria-label={`${schema.slot}号位套装`}
          value={disc?.set_id ?? ""}
          onChange={(event) => onSelectSet(event.target.value)}
        >
          <option value="">空槽</option>
          {driveDiscSets.map((item) => <option key={item.set_id} value={item.set_id}>{item.display_name}</option>)}
        </select>
      </div>

      {disc ? (
        <>
          <div className="drive-disc-section drive-disc-main-section">
            <div className="drive-disc-section-heading">
              <span>主词条</span>
              <small>{schema.main_stat_options.length === 1 ? "槽位固定" : "选择主词条"}</small>
            </div>
            <select
              aria-label={`${schema.slot}号位主词条`}
              value={disc.main_stat ?? ""}
              disabled={schema.main_stat_options.length === 1}
              onChange={(event) => onUpdateMain(event.target.value)}
            >
              {schema.main_stat_options.length > 1 && <option value="">未选择</option>}
              {schema.main_stat_options.map((item) => (
                <option key={item.stat_key} value={item.stat_key}>{item.label} +{formatValue(item.stat_key, item.value_per_roll)}</option>
              ))}
            </select>
            {preview?.main_stat && (
              <p className="drive-main-stat-preview">
                <span>{preview.main_stat.label}</span>
                <strong>+{preview.main_stat.display_total_value}</strong>
              </p>
            )}
          </div>

          <div className="drive-disc-section drive-disc-substats-section">
            <div className="drive-disc-section-heading">
              <span>副词条</span>
              <strong className="drive-substat-count">{disc.substats.length}/4</strong>
            </div>
            <div className="drive-substats">
              {disc.substats.map((substat, index) => {
                const rowOptions = substatOptions.filter(
                  (item) => item.stat_key === substat.stat
                    || (item.stat_key !== disc.main_stat && !disc.substats.some((other, otherIndex) => otherIndex !== index && other.stat === item.stat_key)),
                );
                const substatPreview = preview?.substats.find((item) => item.stat_key === substat.stat);
                const substatOption = substatOptions.find((item) => item.stat_key === substat.stat);
                const valuePerRoll = substatPreview?.value_per_roll ?? substatOption?.value_per_roll ?? 0;
                const singleValue = substatPreview?.display_value_per_roll
                  ?? formatValue(substat.stat, valuePerRoll);
                const totalValue = substatPreview?.display_total_value
                  ?? formatValue(substat.stat, valuePerRoll * substat.roll_count);
                return (
                  <div className="drive-substat-row" key={`${schema.slot}-${index}-${substat.stat}`}>
                    <div className="drive-substat-topline">
                      <label className="drive-substat-select">
                        <span>副词条属性</span>
                        <select
                          aria-label={`${schema.slot}号位副词条${index + 1}属性`}
                          value={substat.stat}
                          onChange={(event) => onUpdateSubstat(index, { ...substat, stat: event.target.value })}
                        >
                          {rowOptions.map((item) => <option key={item.stat_key} value={item.stat_key}>{item.label}</option>)}
                        </select>
                      </label>
                      <button
                        className="icon-button drive-substat-remove"
                        aria-label={`删除${schema.slot}号位副词条${index + 1}`}
                        type="button"
                        onClick={() => onRemoveSubstat(index)}
                      >
                        ×
                      </button>
                    </div>
                    <div className="drive-substat-rollline">
                      <span>单次 <strong>+{singleValue}</strong></span>
                      <span aria-hidden="true">×</span>
                      <div className="drive-roll-stepper" role="group" aria-label={`${schema.slot}号位副词条${index + 1}次数`}>
                        <button
                          className="stepper-button"
                          type="button"
                          aria-label="减少次数"
                          title={substat.roll_count <= 1 ? "最少 1 次" : "减少次数"}
                          disabled={substat.roll_count <= 1}
                          onClick={() => onUpdateRoll(index, -1)}
                        >
                          −
                        </button>
                        <span aria-live="polite">{substat.roll_count}</span>
                        <button
                          className="stepper-button"
                          type="button"
                          aria-label="增加次数"
                          title={substat.roll_count >= 6 ? "最多 6 次" : "增加次数"}
                          disabled={substat.roll_count >= 6}
                          onClick={() => onUpdateRoll(index, 1)}
                        >
                          +
                        </button>
                      </div>
                      <span className="drive-substat-total">= 总计 <strong>+{totalValue}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>

            {disc.substats.length < 4 && (
              <div className="drive-substat-add-row">
                <div className="drive-substat-add-copy">
                  <strong>添加副词条</strong>
                  <span>最多 4 条 · 已配置 {disc.substats.length}/4</span>
                </div>
                <select
                  aria-label={`${schema.slot}号位待添加副词条`}
                  value={pendingAddStat}
                  onChange={(event) => setPendingAddStat(event.target.value)}
                >
                  <option value="">选择属性…</option>
                  {availableSubstats.map((item) => <option key={item.stat_key} value={item.stat_key}>{item.label}</option>)}
                </select>
                <button
                  className="secondary-button add-substat-button"
                  type="button"
                  disabled={!pendingAddStat}
                  onClick={() => {
                    if (!pendingAddStat) return;
                    onAddSubstat(pendingAddStat);
                    setPendingAddStat("");
                  }}
                >
                  添加
                </button>
              </div>
            )}
            <div className={`drive-roll-total ${isDriveDiscComplete(disc) ? "complete" : "incomplete"}`}>
              <span>总词条次数</span>
              <strong>{totalRolls}</strong>
              <small>需要 8–9 次才能完整</small>
            </div>
          </div>

          {diagnostics
            .filter((item) => item.blocking && item.diagnostic_id.includes(`slot-${schema.slot}-`))
            .map((item) => <p className="drive-disc-diagnostic" key={item.diagnostic_id}>{item.message}</p>)}
        </>
      ) : (
        <div className="drive-disc-empty">
          <span>选择套装后配置主词条与副词条</span>
        </div>
      )}
    </article>
  );
}

export default DriveDiscCard;
