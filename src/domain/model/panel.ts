import type { StatKey } from "./character-build.js";

export interface BasePanelStats {
  hp: number;
  atk: number;
  def: number;
  impact: number;
  critRate: number;
  critDmg: number;
  anomalyMastery: number;
  anomalyProficiency: number;
  penRate: number;
  penFlat: number;
  energyRegen: number;
  physicalDmgBonus: number;
  fireDmgBonus: number;
  iceDmgBonus: number;
  electricDmgBonus: number;
  etherDmgBonus: number;
  windDmgBonus?: number;
}

export interface PanelModifier {
  sourceId: string;
  label: string;
  stat: StatKey;
  value: number;
}

export interface PanelCalculationInput {
  character: BasePanelStats;
  weaponBaseAtk: number;
  modifiers: PanelModifier[];
}

export interface FinalPanelStats {
  hp: number;
  atk: number;
  def: number;
  impact: number;
  critRate: number;
  critDmg: number;
  anomalyMastery: number;
  anomalyProficiency: number;
  penRate: number;
  penFlat: number;
  energyRegen: number;
  physicalDmgBonus: number;
  fireDmgBonus: number;
  iceDmgBonus: number;
  electricDmgBonus: number;
  etherDmgBonus: number;
  windDmgBonus?: number;
}

export interface PanelTraceEntry {
  stat: keyof FinalPanelStats;
  sourceId: string;
  label: string;
  operation: "base" | "add-flat" | "add-percent" | "finalize";
  value: number;
  note?: string;
}

export interface PanelCalculationResult {
  base: FinalPanelStats;
  final: FinalPanelStats;
  trace: PanelTraceEntry[];
  warnings: string[];
}
