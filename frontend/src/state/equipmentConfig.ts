import type { DriveDiscConfig, DriveDiscSlotSchema, DriveDiscStatOption } from "./driveDiscState";

export const EQUIPMENT_CONFIG_SCHEMA_VERSION = "zzz-character-equipment-v1" as const;

export type EquipmentWengineConfig = {
  id: string;
  level: number;
  refinement: number;
};

export type EquipmentConfig = {
  schema_version: typeof EQUIPMENT_CONFIG_SCHEMA_VERSION;
  character_id: string;
  wengine: EquipmentWengineConfig | null;
  drive_discs: DriveDiscConfig[];
};

export type EquipmentValidationCatalog = {
  wengines: readonly { wengine_id: string; specialty?: string }[];
  driveDiscSets: readonly { set_id: string }[];
  slotSchemas?: readonly DriveDiscSlotSchema[];
  substatOptions?: readonly DriveDiscStatOption[];
  characterSpecialty?: string;
};

export type EquipmentConfigParseResult =
  | { ok: true; config: EquipmentConfig }
  | { ok: false; message: string };

export const CHARACTER_CONFIG_SCHEMA_VERSION = "zzz-character-config-v2" as const;

const POTENTIAL_CONFIG_CHARACTER_IDS = new Set([
  "character:1021", // Nekomata
  "character:1041", // Soldier 11
  "character:1101", // Koleda
  "character:1141", // Lycaon
  "character:1171", // Burnice
  "character:1181", // Grace
  "character:1191", // Ellen
  "character:1201", // Harumasa
  "character:1211", // Rina
]);

export function characterConfigFilename(
  codeName: string | undefined,
  characterId: string,
): string {
  const safeCodeName = (codeName ?? "")
    .trim()
    .replace(/[^a-z0-9._-]+/gi, "_")
    .replace(/^_+|_+$/g, "");
  const safeCharacterId = characterId
    .replace(/[^a-z0-9._-]+/gi, "_")
    .replace(/^_+|_+$/g, "");
  return `zzz-character-${safeCodeName || "Character"}-${safeCharacterId || "character"}.json`;
}

export type CharacterBuildMode = "equipment-build";

export type CharacterConfig = {
  schema_version: typeof CHARACTER_CONFIG_SCHEMA_VERSION;
  character_id: string;
  character_level: number;
  build_mode: CharacterBuildMode;
  compile_config: Record<string, unknown>;
  wengine: EquipmentWengineConfig | null;
  drive_discs: DriveDiscConfig[];
  manual_panel_stats: null;
};

export type CharacterConfigParseResult =
  | {
    ok: true;
    config: CharacterConfig;
    equipment: EquipmentConfig;
    source: "v2" | "v1" | "drive-only";
    wengineProvided: boolean;
  }
  | { ok: false; message: string };

const MAIN_STAT_KEYS_BY_SLOT: Record<number, readonly string[]> = {
  1: ["hp-flat"],
  2: ["attack-flat"],
  3: ["defense-flat"],
  4: ["crit-rate", "crit-damage", "attack-percent", "defense-percent", "anomaly-proficiency-flat", "hp-percent"],
  5: ["attack-percent", "defense-percent", "hp-percent", "fire-damage-bonus", "ice-damage-bonus", "wind-damage-bonus", "electric-damage-bonus", "physical-damage-bonus", "ether-damage-bonus", "penetration-rate"],
  6: ["energy-regen-percent", "attack-percent", "defense-percent", "hp-percent", "anomaly-mastery-percent", "impact-percent"],
};

const FALLBACK_SUBSTAT_KEYS = [
  "attack-flat",
  "defense-flat",
  "hp-flat",
  "penetration-flat",
  "anomaly-proficiency-flat",
  "crit-rate",
  "crit-damage",
  "attack-percent",
  "hp-percent",
  "defense-percent",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const expected = new Set(keys);
  return Object.keys(value).length === expected.size
    && Object.keys(value).every((key) => expected.has(key));
}

function invalid(message: string): never {
  throw new Error(message);
}

function integerInRange(value: unknown, min: number, max: number, label: string): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < min || value > max) {
    invalid(`${label} must be an integer between ${min} and ${max}`);
  }
  return value;
}

function stringValue(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) invalid(`${label} must be a non-empty string`);
  return value;
}

function validMainStatKeys(slot: number, catalog: EquipmentValidationCatalog): ReadonlySet<string> {
  const schema = catalog.slotSchemas?.find((item) => item.slot === slot);
  if (schema && schema.main_stat_options.length > 0) {
    return new Set(schema.main_stat_options.map((item) => item.stat_key));
  }
  return new Set(MAIN_STAT_KEYS_BY_SLOT[slot] ?? []);
}

function validSubstatKeys(catalog: EquipmentValidationCatalog): ReadonlySet<string> {
  return new Set(
    catalog.substatOptions?.length
      ? catalog.substatOptions.map((item) => item.stat_key)
      : FALLBACK_SUBSTAT_KEYS,
  );
}

function validateEquipmentObject(
  raw: unknown,
  expectedCharacterId: string,
  catalog: EquipmentValidationCatalog,
): EquipmentConfig {
  if (!isRecord(raw)) invalid("equipment config must be a JSON object");
  if (!hasExactKeys(raw, ["schema_version", "character_id", "wengine", "drive_discs"])) {
    invalid("equipment config has unexpected or missing fields");
  }
  if (raw.schema_version !== EQUIPMENT_CONFIG_SCHEMA_VERSION) {
    invalid(`unsupported equipment config schema: ${String(raw.schema_version)}`);
  }
  const characterId = stringValue(raw.character_id, "character_id");
  if (characterId !== expectedCharacterId) {
    invalid(`character_id ${characterId} does not match ${expectedCharacterId}`);
  }

  let wengine: EquipmentWengineConfig | null = null;
  if (raw.wengine !== null) {
    if (!isRecord(raw.wengine) || !hasExactKeys(raw.wengine, ["id", "level", "refinement"])) {
      invalid("wengine must be null or an object with id, level, and refinement");
    }
    const id = stringValue(raw.wengine.id, "wengine.id");
    const catalogItem = catalog.wengines.find((item) => item.wengine_id === id);
    if (!catalogItem) invalid(`unknown W-Engine: ${id}`);
    wengine = {
      id,
      level: integerInRange(raw.wengine.level, 1, 60, "wengine.level"),
      refinement: integerInRange(raw.wengine.refinement, 1, 5, "wengine.refinement"),
    };
  }

  if (!Array.isArray(raw.drive_discs)) invalid("drive_discs must be an array");
  if (raw.drive_discs.length > 6) invalid("drive_discs can contain at most six slots");
  const slots = new Set<number>();
  const substatKeys = validSubstatKeys(catalog);
  const driveDiscs: DriveDiscConfig[] = raw.drive_discs.map((rawDisc, index) => {
    if (!isRecord(rawDisc) || !hasExactKeys(rawDisc, ["slot", "set_id", "main_stat", "substats"])) {
      invalid(`drive_discs[${index}] has unexpected or missing fields`);
    }
    const slot = integerInRange(rawDisc.slot, 1, 6, `drive_discs[${index}].slot`);
    if (slots.has(slot)) invalid(`drive_discs contains duplicate slot ${slot}`);
    slots.add(slot);
    const setId = stringValue(rawDisc.set_id, `drive_discs[${index}].set_id`);
    if (!catalog.driveDiscSets.some((item) => item.set_id === setId)) {
      invalid(`unknown Drive Disc set: ${setId}`);
    }
    if (rawDisc.main_stat !== null && typeof rawDisc.main_stat !== "string") {
      invalid(`drive_discs[${index}].main_stat must be a string or null`);
    }
    const mainStat = rawDisc.main_stat === null ? null : stringValue(rawDisc.main_stat, `drive_discs[${index}].main_stat`);
    if (mainStat !== null && !validMainStatKeys(slot, catalog).has(mainStat)) {
      invalid(`invalid main stat ${mainStat} for Drive Disc slot ${slot}`);
    }
    if (!Array.isArray(rawDisc.substats) || rawDisc.substats.length > 4) {
      invalid(`drive_discs[${index}].substats must contain at most four items`);
    }
    const seenSubstats = new Set<string>();
    const substats = rawDisc.substats.map((rawSubstat, substatIndex) => {
      if (!isRecord(rawSubstat) || !hasExactKeys(rawSubstat, ["stat", "roll_count"])) {
        invalid(`drive_discs[${index}].substats[${substatIndex}] has unexpected or missing fields`);
      }
      const stat = stringValue(rawSubstat.stat, `drive_discs[${index}].substats[${substatIndex}].stat`);
      if (!substatKeys.has(stat)) invalid(`unknown Drive Disc substat: ${stat}`);
      if (stat === mainStat) invalid(`Drive Disc slot ${slot} main stat cannot also be a substat`);
      if (seenSubstats.has(stat)) invalid(`Drive Disc slot ${slot} substats must be unique`);
      seenSubstats.add(stat);
      return {
        stat,
        roll_count: integerInRange(rawSubstat.roll_count, 1, 6, `drive_discs[${index}].substats[${substatIndex}].roll_count`),
      };
    });
    return { slot, set_id: setId, main_stat: mainStat, substats };
  });

  return {
    schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
    character_id: characterId,
    wengine,
    drive_discs: driveDiscs,
  };
}

export function parseEquipmentConfig(
  source: string,
  expectedCharacterId: string,
  catalog: EquipmentValidationCatalog,
): EquipmentConfigParseResult {
  try {
    const parsed: unknown = JSON.parse(source);
    const raw = legacyDriveOnlyPayload(parsed)
      ? {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: expectedCharacterId,
        wengine: null,
        drive_discs: Array.isArray(parsed) ? parsed : parsed.drive_discs,
      }
      : parsed;
    return { ok: true, config: validateEquipmentObject(raw, expectedCharacterId, catalog) };
  } catch (error) {
    return { ok: false, message: (error as Error).message };
  }
}

export function createEquipmentConfig(
  characterId: string,
  wengine: EquipmentWengineConfig | null,
  driveDiscs: readonly DriveDiscConfig[],
): EquipmentConfig {
  return {
    schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
    character_id: characterId,
    wengine: wengine ? { ...wengine } : null,
    drive_discs: driveDiscs.map((disc) => ({
      ...disc,
      substats: disc.substats.map((substat) => ({ ...substat })),
    })),
  };
}

export function serializeEquipmentConfig(config: EquipmentConfig): string {
  return `${JSON.stringify(config, null, 2)}\n`;
}

function legacyDriveOnlyPayload(value: unknown): value is DriveDiscConfig[] | { drive_discs: unknown } {
  return Array.isArray(value)
    || (isRecord(value)
      && Object.keys(value).length === 1
      && Object.prototype.hasOwnProperty.call(value, "drive_discs"));
}

function validateCompileConfig(raw: unknown, characterId: string): Record<string, unknown> {
  if (!isRecord(raw)) invalid("compile_config must be an object");
  const allowed = new Set([
    "core_level",
    "cinema_level",
    "skill_levels",
    "mingxin_active",
    "entry_move_uses_linren",
  ]);
  const supportsPotential = POTENTIAL_CONFIG_CHARACTER_IDS.has(characterId);
  if (supportsPotential) allowed.add("potential_level");
  const unknown = Object.keys(raw).filter((key) => !allowed.has(key));
  if (unknown.length > 0) {
    invalid(`compile_config has unsupported fields: ${unknown.join(", ")}`);
  }
  const coreLevel = "core_level" in raw
    ? integerInRange(raw.core_level, 1, 7, "compile_config.core_level")
    : 7;
  const cinemaLevel = "cinema_level" in raw
    ? integerInRange(raw.cinema_level, 0, 6, "compile_config.cinema_level")
    : 0;
  if (supportsPotential && "potential_level" in raw) {
    integerInRange(raw.potential_level, 0, 6, "compile_config.potential_level");
  }
  for (const key of ["mingxin_active", "entry_move_uses_linren"]) {
    if (key in raw && typeof raw[key] !== "boolean") invalid(`compile_config.${key} must be boolean`);
  }
  if ("skill_levels" in raw) {
    if (!isRecord(raw.skill_levels)) invalid("compile_config.skill_levels must be an object");
    const groups = new Set(["basic-attack", "dodge", "special-attack", "chain-attack", "assist", "ultimate"]);
    for (const [group, value] of Object.entries(raw.skill_levels)) {
      if (!groups.has(group)) invalid(`unknown skill group in compile_config.skill_levels: ${group}`);
      integerInRange(value, 1, 16, `compile_config.skill_levels.${group}`);
    }
  }
  return {
    ...(JSON.parse(JSON.stringify(raw)) as Record<string, unknown>),
    core_level: coreLevel,
    cinema_level: cinemaLevel,
  };
}

function validateManualPanelStats(raw: unknown): Record<string, unknown> | null {
  if (raw === null) return null;
  if (!isRecord(raw)) invalid("manual_panel_stats must be null or an object");
  const allowed = new Set([
    "hp",
    "attack",
    "defense",
    "impact",
    "anomaly_mastery",
    "anomaly_proficiency",
    "energy_regen",
    "crit_rate",
    "crit_damage",
    "penetration_rate",
    "penetration_flat",
    "element_damage_bonus",
  ]);
  const unknown = Object.keys(raw).filter((key) => !allowed.has(key));
  if (unknown.length > 0) invalid(`manual_panel_stats has unsupported fields: ${unknown.join(", ")}`);
  for (const key of Object.keys(raw).filter((item) => item !== "element_damage_bonus")) {
    if (typeof raw[key] !== "number" || !Number.isFinite(raw[key] as number)) {
      invalid(`manual_panel_stats.${key} must be a finite number`);
    }
  }
  if ("element_damage_bonus" in raw) {
    if (!isRecord(raw.element_damage_bonus)) invalid("manual_panel_stats.element_damage_bonus must be an object");
    for (const [element, value] of Object.entries(raw.element_damage_bonus)) {
      if (typeof value !== "number" || !Number.isFinite(value)) invalid(`manual_panel_stats.element_damage_bonus.${element} must be a finite number`);
    }
  }
  return JSON.parse(JSON.stringify(raw)) as Record<string, unknown>;
}

function validateCharacterObject(
  raw: unknown,
  expectedCharacterId: string,
  catalog: EquipmentValidationCatalog,
): { config: CharacterConfig; equipment: EquipmentConfig } {
  if (!isRecord(raw)) invalid("character config must be a JSON object");
  if (!hasExactKeys(raw, [
    "schema_version",
    "character_id",
    "character_level",
    "build_mode",
    "compile_config",
    "wengine",
    "drive_discs",
    "manual_panel_stats",
  ])) {
    invalid("character config has unexpected or missing fields");
  }
  if (raw.schema_version !== CHARACTER_CONFIG_SCHEMA_VERSION) {
    invalid(`unsupported character config schema: ${String(raw.schema_version)}`);
  }
  const characterId = stringValue(raw.character_id, "character_id");
  if (characterId !== expectedCharacterId) invalid(`character_id ${characterId} does not match ${expectedCharacterId}`);
  const characterLevel = integerInRange(raw.character_level, 1, 60, "character_level");
  if (raw.build_mode !== "manual-panel" && raw.build_mode !== "equipment-build") {
    invalid("build_mode must be manual-panel or equipment-build");
  }
  const compileConfig = validateCompileConfig(raw.compile_config, characterId);
  validateManualPanelStats(raw.manual_panel_stats);
  const equipment = validateEquipmentObject({
    schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
    character_id: characterId,
    wengine: raw.wengine,
    drive_discs: raw.drive_discs,
  }, expectedCharacterId, catalog);
  return {
    config: {
      schema_version: CHARACTER_CONFIG_SCHEMA_VERSION,
      character_id: characterId,
      character_level: characterLevel,
      // v2 files may still declare the retired manual-panel mode.  Their
      // equipment selection and progression remain useful, but imported
      // panel numbers are never treated as build inputs.
      build_mode: "equipment-build",
      compile_config: compileConfig,
      wengine: equipment.wengine,
      drive_discs: equipment.drive_discs,
      manual_panel_stats: null,
    },
    equipment,
  };
}

export function createCharacterConfig(
  characterId: string,
  characterLevel: number,
  _buildMode: CharacterBuildMode,
  compileConfig: Record<string, unknown>,
  wengine: EquipmentWengineConfig | null,
  driveDiscs: readonly DriveDiscConfig[],
  _manualPanelStats: Record<string, unknown> | null,
): CharacterConfig {
  return {
    schema_version: CHARACTER_CONFIG_SCHEMA_VERSION,
    character_id: characterId,
    character_level: characterLevel,
    build_mode: "equipment-build",
    compile_config: JSON.parse(JSON.stringify(compileConfig)) as Record<string, unknown>,
    wengine: wengine ? { ...wengine } : null,
    drive_discs: driveDiscs.map((disc) => ({
      ...disc,
      substats: disc.substats.map((substat) => ({ ...substat })),
    })),
    manual_panel_stats: null,
  };
}

export function serializeCharacterConfig(config: CharacterConfig): string {
  return `${JSON.stringify(config, null, 2)}\n`;
}

/** Parse v2 plus the repository's pre-v2 equipment exports without guessing. */
export function parseCharacterConfig(
  source: string,
  expectedCharacterId: string,
  catalog: EquipmentValidationCatalog,
): CharacterConfigParseResult {
  try {
    const parsed: unknown = JSON.parse(source);
    if (isRecord(parsed) && parsed.schema_version === CHARACTER_CONFIG_SCHEMA_VERSION) {
      const validated = validateCharacterObject(parsed, expectedCharacterId, catalog);
      return {
        ok: true,
        config: validated.config,
        equipment: validated.equipment,
        source: "v2",
        wengineProvided: true,
      };
    }
    if (isRecord(parsed) && "schema_version" in parsed) {
      if (parsed.schema_version !== EQUIPMENT_CONFIG_SCHEMA_VERSION) {
        invalid(`unsupported character config schema: ${String(parsed.schema_version)}`);
      }
      const weaponMissing = hasExactKeys(parsed, ["schema_version", "character_id", "drive_discs"]);
      const equipment = validateEquipmentObject(
        weaponMissing
          ? {
            schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
            character_id: parsed.character_id,
            wengine: null,
            drive_discs: parsed.drive_discs,
          }
          : parsed,
        expectedCharacterId,
        catalog,
      );
      return {
        ok: true,
        config: createCharacterConfig(expectedCharacterId, 60, "equipment-build", { core_level: 7, cinema_level: 0 }, equipment.wengine, equipment.drive_discs, null),
        equipment,
        source: "v1",
        wengineProvided: !weaponMissing,
      };
    }
    if (legacyDriveOnlyPayload(parsed)) {
      const rawDiscs = Array.isArray(parsed) ? parsed : parsed.drive_discs;
      const equipment = validateEquipmentObject({
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: expectedCharacterId,
        wengine: null,
        drive_discs: rawDiscs,
      }, expectedCharacterId, catalog);
      return {
        ok: true,
        config: createCharacterConfig(expectedCharacterId, 60, "equipment-build", { core_level: 7, cinema_level: 0 }, null, equipment.drive_discs, null),
        equipment,
        source: "drive-only",
        wengineProvided: false,
      };
    }
    invalid("character config must declare a supported schema_version");
  } catch (error) {
    return { ok: false, message: (error as Error).message };
  }
}
