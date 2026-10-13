import type { DriveDiscConfig } from '../state/driveDiscState';
import { EFFECTIVE_STAT_OPTIONS, effectiveStatCounts } from '../state/effectiveStats';

type Props = { discs: DriveDiscConfig[]; selected: string[]; specialty?: string; sourceLabel: string;
  officialCount?: number | null; collapsed: boolean; onChange: (stats:string[])=>void; onReset:()=>void };

export default function EffectiveStatsPanel({discs,selected,specialty,sourceLabel,officialCount,collapsed,onChange,onReset}:Props) {
  const {counts,total}=effectiveStatCounts(discs,selected);
  return <section className="effective-stats-panel" aria-label="有效词条统计">
    <div className="effective-stat-count"><span>总有效词条数量</span><strong>{total}<small> 条</small></strong><small>{sourceLabel}{officialCount != null ? ` · 米游社获取时 ${officialCount} 条` : ''}</small></div>
    <div className="effective-stat-chips">{EFFECTIVE_STAT_OPTIONS.filter(o=>selected.includes(o.key)).map(o=><span key={o.key}>
      {o.label} <strong>{counts[o.key]??0}</strong>{'flat' in o && <small title="固定数值副词条，不计入有效词条总数">+{counts[o.flat]??0}</small>}
    </span>)}{specialty !== 'rupture' && <span>穿透值 <small title="所有非命破角色的有效小词条，不计入总数">+{counts['penetration-flat']??0}</small></span>}</div>
    {!selected.length && <p className="control-section-hint">尚未选择有效词条，可在下方自行配置。</p>}
    {!collapsed && <details className="effective-stats-settings"><summary>配置有效词条</summary>
      <div className="effective-stats-options">{EFFECTIVE_STAT_OPTIONS.map(o=><label key={o.key}><input type="checkbox" checked={selected.includes(o.key)}
        onChange={e=>onChange(e.target.checked?[...selected,o.key]:selected.filter(s=>s!==o.key))}/>{o.label}</label>)}</div>
      <button className="secondary-button" type="button" onClick={onReset}>恢复默认方案</button>
      <p className="control-section-hint">小字 +N 为固定数值小词条，不计入总数。固定生命、攻击、防御和非命破角色的穿透值仍参与伤害及新增词条收益计算。</p>
    </details>}
  </section>;
}
