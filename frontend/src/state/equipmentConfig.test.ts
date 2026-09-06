import { describe, expect, it } from "vitest";
import {
  createEquipmentConfig,
  EQUIPMENT_CONFIG_SCHEMA_VERSION,
  parseEquipmentConfig,
  serializeEquipmentConfig,
} from "./equipmentConfig";

const catalog = {
  wengines: [
    { wengine_id: "wengine:demo", specialty: "attack" },
  ],
  driveDiscSets: [{ set_id: "drive-disc:31000" }],
  slotSchemas: [
    { slot: 1, main_stat_options: [{ stat_key: "hp-flat", label: "生命值", value_per_roll: 2200 }] },
    { slot: 4, main_stat_options: [{ stat_key: "crit-rate", label: "暴击率", value_per_roll: .24 }] },
  ],
  substatOptions: [
    { stat_key: "attack-flat", label: "攻击力", value_per_roll: 19 },
    { stat_key: "crit-rate", label: "暴击率", value_per_roll: .024 },
  ],
  characterSpecialty: "attack",
};

const config = createEquipmentConfig("character:demo", { id: "wengine:demo", level: 60, refinement: 2 }, [
  {
    slot: 1,
    set_id: "drive-disc:31000",
    main_stat: "hp-flat",
    substats: [{ stat: "attack-flat", roll_count: 2 }],
  },
]);

describe("equipment config JSON", () => {
  it("round-trips a versioned character equipment config", () => {
    const parsed = parseEquipmentConfig(serializeEquipmentConfig(config), "character:demo", catalog);
    expect(parsed).toEqual({ ok: true, config });
    expect(config.schema_version).toBe(EQUIPMENT_CONFIG_SCHEMA_VERSION);
  });

  it("allows partial discs with a null main stat", () => {
    const partial = createEquipmentConfig("character:demo", null, [{
      ...config.drive_discs[0],
      main_stat: null,
    }]);
    expect(parseEquipmentConfig(serializeEquipmentConfig(partial), "character:demo", catalog).ok).toBe(true);
  });

  it("rejects an unsupported schema version", () => {
    const invalid = JSON.stringify({ ...config, schema_version: "zzz-character-equipment-v0" });
    const result = parseEquipmentConfig(invalid, "character:demo", catalog);
    expect(result.ok).toBe(false);
    expect(result).toMatchObject({ message: expect.stringContaining("unsupported equipment config schema") });
  });

  it("rejects a config for another character", () => {
    const result = parseEquipmentConfig(serializeEquipmentConfig(config), "character:other", catalog);
    expect(result.ok).toBe(false);
    expect(result).toMatchObject({ message: expect.stringContaining("does not match character:other") });
  });

  it("rejects illegal catalog, slot, stat, roll, and weapon values", () => {
    const unknownSet = { ...config, drive_discs: [{ ...config.drive_discs[0], set_id: "drive-disc:nope" }] };
    expect(parseEquipmentConfig(JSON.stringify(unknownSet), "character:demo", catalog).ok).toBe(false);
    const wrongMain = { ...config, drive_discs: [{ ...config.drive_discs[0], main_stat: "crit-rate" }] };
    expect(parseEquipmentConfig(JSON.stringify(wrongMain), "character:demo", catalog).ok).toBe(false);
    const badRoll = { ...config, drive_discs: [{ ...config.drive_discs[0], substats: [{ stat: "attack-flat", roll_count: 7 }] }] };
    expect(parseEquipmentConfig(JSON.stringify(badRoll), "character:demo", catalog).ok).toBe(false);
    const badWeapon = { ...config, wengine: { id: "wengine:nope", level: 60, refinement: 1 } };
    expect(parseEquipmentConfig(JSON.stringify(badWeapon), "character:demo", catalog).ok).toBe(false);
  });
});
