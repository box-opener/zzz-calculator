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
    if (catalog.characterSpecialty && catalogItem.specialty && catalogItem.specialty !== catalog.characterSpecialty) {
      invalid(`W-Engine ${id} is not compatible with ${expectedCharacterId}`);
    }
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
    const raw: unknown = JSON.parse(source);
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
