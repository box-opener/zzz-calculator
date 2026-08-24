import type {
  BasePanelStats,
  FinalPanelStats,
  PanelCalculationInput,
  PanelCalculationResult,
  PanelModifier,
  PanelTraceEntry,
} from "../model/panel.js";
import type { StatKey } from "../model/character-build.js";

const DIRECT_STAT_MAP: Partial<Record<StatKey, keyof FinalPanelStats>> = {
  hp: "hp",
  atk: "atk",
  def: "def",
  impact: "impact",
  critRate: "critRate",
  critDmg: "critDmg",
  penRate: "penRate",
  penFlat: "penFlat",
  anomalyProficiency: "anomalyProficiency",
  anomalyMastery: "anomalyMastery",
  energyRegen: "energyRegen",
  physicalDmgBonus: "physicalDmgBonus",
  fireDmgBonus: "fireDmgBonus",
  iceDmgBonus: "iceDmgBonus",
  electricDmgBonus: "electricDmgBonus",
  etherDmgBonus: "etherDmgBonus",
  windDmgBonus: "windDmgBonus",
};

const PERCENT_STAT_MAP: Partial<Record<StatKey, keyof FinalPanelStats>> = {
  hpPct: "hp",
  atkPct: "atk",
  defPct: "def",
  impactPct: "impact",
  anomalyMasteryPct: "anomalyMastery",
  energyRegenPct: "energyRegen",
};

function emptyLike(source: BasePanelStats): FinalPanelStats {
  const result: FinalPanelStats = {
    hp: Math.floor(source.hp),
    atk: Math.floor(source.atk),
    def: Math.floor(source.def),
    impact: source.impact,
    critRate: source.critRate,
    critDmg: source.critDmg,
    anomalyMastery: source.anomalyMastery,
    anomalyProficiency: source.anomalyProficiency,
    penRate: source.penRate,
    penFlat: source.penFlat,
    energyRegen: source.energyRegen,
    physicalDmgBonus: source.physicalDmgBonus,
    fireDmgBonus: source.fireDmgBonus,
    iceDmgBonus: source.iceDmgBonus,
    electricDmgBonus: source.electricDmgBonus,
    etherDmgBonus: source.etherDmgBonus,
  };
  if (source.windDmgBonus !== undefined) result.windDmgBonus = source.windDmgBonus;
  return result;
}

function sumModifiers(modifiers: PanelModifier[], stat: StatKey): number {
  return modifiers
    .filter((modifier) => modifier.stat === stat)
    .reduce((sum, modifier) => sum + modifier.value, 0);
}

function pushModifierTrace(
  trace: PanelTraceEntry[],
  modifiers: PanelModifier[],
): void {
  for (const modifier of modifiers) {
    const directStat = DIRECT_STAT_MAP[modifier.stat];
    const percentStat = PERCENT_STAT_MAP[modifier.stat];
    const stat = directStat ?? percentStat;
    if (!stat) continue;

    trace.push({
      stat,
      sourceId: modifier.sourceId,
      label: modifier.label,
      operation: percentStat ? "add-percent" : "add-flat",
      value: modifier.value,
    });
  }
}

function applyRoundedPrimaryStat(
  base: number,
  pct: number,
  flat: number,
): { final: number; pctContribution: number } {
  const pctContribution = Math.round((base * pct) / 100);
  return {
    final: base + pctContribution + flat,
    pctContribution,
  };
}

export function calculatePanel(
  input: PanelCalculationInput,
): PanelCalculationResult {
  const warnings: string[] = [];
  const trace: PanelTraceEntry[] = [];

  const base = emptyLike(input.character);
  base.atk = Math.floor(input.character.atk) + Math.floor(input.weaponBaseAtk);

  for (const [stat, value] of Object.entries(base) as Array<
    [keyof FinalPanelStats, number]
  >) {
    trace.push({
      stat,
      sourceId: "base",
      label: stat === "atk" ? "角色与音擎基础攻击" : "角色基础属性",
      operation: "base",
      value,
    });
  }

  pushModifierTrace(trace, input.modifiers);

  const final: FinalPanelStats = { ...base };
  if (input.modifiers.some((modifier) => modifier.stat === "windDmgBonus") &&
      final.windDmgBonus === undefined) {
    final.windDmgBonus = 0;
  }
  const hpPct = sumModifiers(input.modifiers, "hpPct");
  const atkPct = sumModifiers(input.modifiers, "atkPct");
  const defPct = sumModifiers(input.modifiers, "defPct");
  const impactPct = sumModifiers(input.modifiers, "impactPct");
  const masteryPct = sumModifiers(input.modifiers, "anomalyMasteryPct");
  const energyRegenPct = sumModifiers(input.modifiers, "energyRegenPct");

  const hpResult = applyRoundedPrimaryStat(
    base.hp,
    hpPct,
    sumModifiers(input.modifiers, "hp"),
  );
  const atkResult = applyRoundedPrimaryStat(
    base.atk,
    atkPct,
    sumModifiers(input.modifiers, "atk"),
  );
  const defResult = applyRoundedPrimaryStat(
    base.def,
    defPct,
    sumModifiers(input.modifiers, "def"),
  );

  final.hp = hpResult.final;
  final.atk = atkResult.final;
  final.def = defResult.final;
  final.impact = Math.floor(
    base.impact * (1 + impactPct / 100) +
      sumModifiers(input.modifiers, "impact"),
  );
  final.anomalyMastery = Math.floor(
    base.anomalyMastery * (1 + masteryPct / 100) +
      sumModifiers(input.modifiers, "anomalyMastery"),
  );
  final.energyRegen = base.energyRegen * (1 + energyRegenPct / 100);

  for (const [modifierKey, targetKey] of Object.entries(
    DIRECT_STAT_MAP,
  ) as Array<[StatKey, keyof FinalPanelStats]>) {
    if (["hp", "atk", "def", "impact", "anomalyMastery"].includes(modifierKey)) {
      continue;
    }
    const modifierValue = sumModifiers(input.modifiers, modifierKey);
    if (final[targetKey] === undefined && modifierValue === 0) continue;
    final[targetKey] = (final[targetKey] ?? 0) + modifierValue;
  }

  trace.push(
    {
      stat: "hp",
      sourceId: "formula:primary-stat",
      label: "生命值百分比贡献取整",
      operation: "finalize",
      value: hpResult.pctContribution,
      note: `round(${base.hp} × ${hpPct}%)`,
    },
    {
      stat: "atk",
      sourceId: "formula:primary-stat",
      label: "攻击力百分比贡献取整",
      operation: "finalize",
      value: atkResult.pctContribution,
      note: `round(${base.atk} × ${atkPct}%)`,
    },
    {
      stat: "def",
      sourceId: "formula:primary-stat",
      label: "防御力百分比贡献取整",
      operation: "finalize",
      value: defResult.pctContribution,
      note: `round(${base.def} × ${defPct}%)`,
    },
    {
      stat: "anomalyMastery",
      sourceId: "formula:anomaly-mastery",
      label: "异常掌控最终取整",
      operation: "finalize",
      value: final.anomalyMastery,
      note: `floor(${base.anomalyMastery} × (1 + ${masteryPct}%))`,
    },
  );

  if (input.weaponBaseAtk < 0) {
    warnings.push("音擎基础攻击不能为负数。");
  }

  return { base, final, trace, warnings };
}
