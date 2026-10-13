import type { DriveDiscConfig } from './driveDiscState';

export const EFFECTIVE_STAT_OPTIONS = [
  {key:'attack-percent',label:'攻击力%',flat:'attack-flat'},
  {key:'hp-percent',label:'生命值%',flat:'hp-flat'},
  {key:'defense-percent',label:'防御力%',flat:'defense-flat'},
  {key:'crit-rate',label:'暴击率'},
  {key:'crit-damage',label:'暴击伤害'},
  {key:'anomaly-proficiency-flat',label:'异常精通'},
] as const;
export const EFFECTIVE_STATS_STORAGE_KEY = 'zzz-effective-stats-v1';
export function validateEffectiveStats(raw: unknown): string[] | null {
  if (!Array.isArray(raw) || raw.length > EFFECTIVE_STAT_OPTIONS.length
    || raw.some(key=>typeof key !== 'string' || !EFFECTIVE_STAT_OPTIONS.some(o=>o.key === key))
    || new Set(raw).size !== raw.length) return null;
  return [...raw] as string[];
}
export function readEffectivePreferences(): Record<string,string[]> {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(EFFECTIVE_STATS_STORAGE_KEY) ?? '{}');
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {};
    return Object.fromEntries(Object.entries(raw).filter(([id,stats])=>/^character:\d+$/.test(id) && validateEffectiveStats(stats) !== null));
  } catch { return {}; }
}
export function defaultEffectiveStats(specialty?: string): string[] {
  if (specialty === 'anomaly') return ['attack-percent','anomaly-proficiency-flat'];
  if (specialty === 'rupture') return ['hp-percent','attack-percent','crit-rate','crit-damage'];
  return ['attack-percent','crit-rate','crit-damage'];
}
export function miyousheEffectiveStats(source: Record<string,unknown>): string[] | null {
  const plan = source.equip_plan_info;
  if (!plan || typeof plan !== 'object' || Array.isArray(plan)) return null;
  const stats = (plan as Record<string,unknown>).effective_substats;
  if (!Array.isArray(stats)) return null;
  return validateEffectiveStats(stats.filter(key=>EFFECTIVE_STAT_OPTIONS.some(o=>o.key === key)));
}
export function effectiveStatCounts(discs: readonly DriveDiscConfig[], selected: readonly string[]) {
  const counts: Record<string,number> = {};
  for (const disc of discs) for (const sub of disc.substats) counts[sub.stat] = (counts[sub.stat] ?? 0) + sub.roll_count;
  return {counts, total:selected.reduce((sum,key)=>sum+(counts[key] ?? 0),0)};
}
