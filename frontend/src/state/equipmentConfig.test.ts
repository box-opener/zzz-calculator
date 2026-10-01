import { describe, expect, it } from "vitest";
import {
  createCharacterConfig,
  createEquipmentConfig,
  EQUIPMENT_CONFIG_SCHEMA_VERSION,
  parseCharacterConfig,
  parseEquipmentConfig,
  serializeCharacterConfig,
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

describe("complete character config v2", () => {
  const manualStats = {
    hp: 12345,
    attack: 2345,
    defense: 678,
    impact: 111,
    anomaly_mastery: 222,
    anomaly_proficiency: 333,
    energy_regen: 1.4,
    crit_rate: 0.55,
    crit_damage: 1.2,
    penetration_rate: 0.08,
    penetration_flat: 17,
    element_damage_bonus: { physical: 0.12, ether: 0.2, electric: 0.03 },
  };

  it("round-trips progress, compile flags, equipment, and manual stats", () => {
    const full = createCharacterConfig(
      "character:demo",
      48,
      "manual-panel",
      {
        core_level: 6,
        cinema_level: 4,
        skill_levels: {
          "basic-attack": 12,
          dodge: 14,
          "special-attack": 16,
          "chain-attack": 12,
          assist: 14,
          ultimate: 16,
        },
        mingxin_active: true,
      },
      { id: "wengine:demo", level: 60, refinement: 5 },
      [{ slot: 1, set_id: "drive-disc:31000", main_stat: null, substats: [] }],
      manualStats,
    );
    const parsed = parseCharacterConfig(serializeCharacterConfig(full), "character:demo", catalog);
    expect(parsed).toEqual({
      ok: true,
      config: full,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:demo",
        wengine: full.wengine,
        drive_discs: full.drive_discs,
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Miyabi's standard compiler fields through v2", () => {
    const miyabi = createCharacterConfig(
      "character:1091",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 12,
          dodge: 14,
          "special-attack": 16,
          "chain-attack": 12,
          assist: 14,
          ultimate: 16,
        },
      },
      null,
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(miyabi),
      "character:1091",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: miyabi,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1091",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Yixuan's core, cinema, and skill levels through v2", () => {
    const yixuan = createCharacterConfig(
      "character:1371",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 12,
          dodge: 14,
          "special-attack": 16,
          "chain-attack": 12,
          assist: 14,
          ultimate: 16,
        },
      },
      null,
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(yixuan),
      "character:1371",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: yixuan,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1371",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Lucia's core, cinema, and skill levels through v2", () => {
    const lucia = createCharacterConfig(
      "character:1451",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 12,
          dodge: 14,
          "special-attack": 16,
          "chain-attack": 12,
          assist: 14,
          ultimate: 16,
        },
      },
      null,
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(lucia),
      "character:1451",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: lucia,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1451",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("keeps current weapon semantics distinct for v1 null and drive-only legacy files", () => {
    const v1 = JSON.stringify({
      schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
      character_id: "character:demo",
      wengine: null,
      drive_discs: [],
    });
    const explicitNull = parseCharacterConfig(v1, "character:demo", catalog);
    expect(explicitNull).toMatchObject({ ok: true, source: "v1", wengineProvided: true });
    const missingWeapon = parseCharacterConfig(JSON.stringify({
      schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
      character_id: "character:demo",
      drive_discs: [],
    }), "character:demo", catalog);
    expect(missingWeapon).toMatchObject({ ok: true, source: "v1", wengineProvided: false });
    const driveOnly = parseCharacterConfig(JSON.stringify({ drive_discs: [] }), "character:demo", catalog);
    expect(driveOnly).toMatchObject({ ok: true, source: "drive-only", wengineProvided: false });
    expect(parseCharacterConfig(JSON.stringify([{ slot: 1, set_id: "drive-disc:31000", main_stat: null, substats: [] }]), "character:demo", catalog)).toMatchObject({ ok: true, source: "drive-only", wengineProvided: false });
  });

  it("rejects derived eligibility and invalid progress fields", () => {
    const full = createCharacterConfig("character:demo", 60, "equipment-build", { core_level: 1, cinema_level: 0 }, null, [], null);
    const derived = JSON.parse(serializeCharacterConfig(full)) as Record<string, unknown>;
    derived.compile_config = { core_level: 1, cinema_level: 0, additional_ability_eligible: true };
    expect(parseCharacterConfig(JSON.stringify(derived), "character:demo", catalog).ok).toBe(false);
    const badLevel = { ...JSON.parse(serializeCharacterConfig(full)), character_level: 61 };
    expect(parseCharacterConfig(JSON.stringify(badLevel), "character:demo", catalog).ok).toBe(false);
  });
});
