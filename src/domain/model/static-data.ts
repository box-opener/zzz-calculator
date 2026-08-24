import type { PanelModifier, BasePanelStats } from "./panel.js";
import type { BuffRule } from "./buff.js";

export interface CharacterStaticData {
  id: string;
  name: string;
  baseStats: BasePanelStats;
  role?: string;
  camp?: string;
  element?: string;
}

export interface WeaponStaticData {
  id: string;
  name: string;
  baseAtk: number;
  secondaryModifiers: PanelModifier[];
}

export interface DriveDiscSetStaticData {
  id: string;
  name: string;
  twoPieceModifiers: PanelModifier[];
  twoPieceRules?: readonly BuffRule[];
}

export interface StaticDataRegistry {
  characters: Record<string, CharacterStaticData>;
  weapons: Record<string, WeaponStaticData>;
  driveDiscSets: Record<string, DriveDiscSetStaticData>;
}
