export type BuildSourceType =
  | "enka"
  | "miyoushe"
  | "manual"
  | "legacy"
  | "reference-image";

export type SkillCategory =
  | "basic"
  | "dash"
  | "special"
  | "dodge"
  | "chain"
  | "ultimate"
  | "core"
  | "assist";

export type StatKey =
  | "hp"
  | "hpPct"
  | "atk"
  | "atkPct"
  | "def"
  | "defPct"
  | "impact"
  | "impactPct"
  | "critRate"
  | "critDmg"
  | "penRate"
  | "penFlat"
  | "anomalyProficiency"
  | "anomalyMastery"
  | "anomalyMasteryPct"
  | "energyRegen"
  | "energyRegenPct"
  | "physicalDmgBonus"
  | "fireDmgBonus"
  | "iceDmgBonus"
  | "electricDmgBonus"
  | "etherDmgBonus"
  | "windDmgBonus";

export interface BuildSource {
  type: BuildSourceType;
  importedAt: string;
  uid?: string;
  provider?: string;
  dataVersion?: string;
}

export interface CharacterBuildInfo {
  id: string;
  level: number;
  promotion: number;
  cinema: number;
  coreLevel: number;
  skillLevels: Partial<Record<SkillCategory, number>>;
  /** Nanoka 静态资料中的职业，例如「强攻」「击破」「支援」。 */
  role?: string;
  /** Nanoka 静态资料中的阵营，例如「狡兔屋」。 */
  camp?: string;
  /** Nanoka 静态资料中的元素标签，例如「电属性」。 */
  element?: string;
}

export interface WeaponBuild {
  uid?: string;
  id: string;
  level: number;
  refinement: number;
}

export interface DriveDiscStat {
  propertyId: number;
  key?: StatKey;
  value?: number;
  rawValue?: number;
  rolls?: number;
}

export interface DriveDiscBuild {
  uid?: string;
  id: string;
  setId?: string;
  slot: 1 | 2 | 3 | 4 | 5 | 6;
  level: number;
  rarity?: number;
  mainStats: DriveDiscStat[];
  subStats: DriveDiscStat[];
}

export interface CharacterBuild {
  schemaVersion: 1;
  source: BuildSource;
  character: CharacterBuildInfo;
  weapon: WeaponBuild | null;
  driveDiscs: DriveDiscBuild[];
  reportedPanel?: SourcePanelStat[];
  warnings: string[];
}

export interface SourcePanelStat {
  propertyId: number;
  name?: string;
  base?: number;
  add?: number;
  final: number;
}

export interface ImportedShowcase {
  uid: string;
  nickname?: string;
  ttl?: number;
  builds: CharacterBuild[];
  warnings: string[];
}
