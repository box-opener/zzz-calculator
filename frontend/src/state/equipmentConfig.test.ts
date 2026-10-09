import { describe, expect, it } from "vitest";
import {
  createCharacterConfig,
  createEquipmentConfig,
  characterConfigFilename,
  EQUIPMENT_CONFIG_SCHEMA_VERSION,
  parseCharacterConfig,
  parseEquipmentConfig,
  serializeCharacterConfig,
  serializeEquipmentConfig,
} from "./equipmentConfig";

const roundTripWengines = [
  { id: "wengine:13103", characterId: "character:1031", specialty: "support" },
  { id: "wengine:14102", characterId: "character:1021", specialty: "attack" },
  { id: "wengine:12001", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:12002", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:12003", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:12004", characterId: "character:1311", specialty: "support" },
  { id: "wengine:12005", characterId: "character:1311", specialty: "support" },
  { id: "wengine:12007", characterId: "character:1251", specialty: "stun" },
  { id: "wengine:12008", characterId: "character:1251", specialty: "stun" },
  { id: "wengine:12009", characterId: "character:1251", specialty: "stun" },
  { id: "wengine:12010", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:12011", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:12012", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:12013", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:12014", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:12015", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:13001", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13002", characterId: "character:1311", specialty: "support" },
  { id: "wengine:13003", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:13004", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13005", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:13006", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:13007", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13008", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:13009", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:13010", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13011", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13012", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:13013", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13014", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:13015", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13016", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13018", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:13019", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:13020", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:13101", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:13106", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13108", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14121", characterId: "character:1211", specialty: "support" },
  { id: "wengine:13111", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:13112", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13113", characterId: "character:1411", specialty: "support" },
  { id: "wengine:13115", characterId: "character:1311", specialty: "support" },
  { id: "wengine:13127", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13128", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:13135", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:13142", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:13144", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:14001", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14002", characterId: "character:1311", specialty: "support" },
  { id: "wengine:14003", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:14105", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:14107", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:14109", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:14110", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:14114", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:14116", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:14117", characterId: "character:1171", specialty: "anomaly" },
  { id: "wengine:14118", characterId: "character:1181", specialty: "anomaly" },
  { id: "wengine:14122", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:14125", characterId: "character:1361", specialty: "stun" },
  { id: "wengine:14126", characterId: "character:1401", specialty: "anomaly" },
  { id: "wengine:14129", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14130", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14132", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14133", characterId: "character:1331", specialty: "anomaly" },
  { id: "wengine:14134", characterId: "character:1341", specialty: "defense" },
  { id: "wengine:14137", characterId: "character:1371", specialty: "rupture" },
  { id: "wengine:14138", characterId: "character:1431", specialty: "attack" },
  { id: "wengine:14139", characterId: "character:1361", specialty: "stun" },
];

describe("character config filenames", () => {
  it("uses the source English name and a filesystem-safe character ID", () => {
    expect(characterConfigFilename("Yidhari", "character:1051"))
      .toBe("zzz-character-Yidhari-character_1051.json");
    expect(characterConfigFilename("Soldier 11", "character:1041"))
      .toBe("zzz-character-Soldier_11-character_1041.json");
  });
});

const catalog = {
  wengines: [
    { wengine_id: "wengine:demo", specialty: "attack" },
    ...roundTripWengines.map((wengine) => ({
      wengine_id: wengine.id,
      specialty: wengine.specialty,
    })),
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

  it("exports only equipment-build character configs", () => {
    const full = createCharacterConfig(
      "character:demo",
      48,
      "equipment-build",
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
    expect(full.build_mode).toBe("equipment-build");
    expect(full.manual_panel_stats).toBeNull();
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

  it("migrates legacy manual-panel v2 files to raw-base equipment builds and preserves no W-Engine", () => {
    const legacy = {
      schema_version: "zzz-character-config-v2",
      character_id: "character:demo",
      character_level: 48,
      build_mode: "manual-panel",
      compile_config: { core_level: 6, cinema_level: 4 },
      wengine: null,
      drive_discs: [],
      manual_panel_stats: manualStats,
    };
    const parsed = parseCharacterConfig(JSON.stringify(legacy), "character:demo", catalog);
    expect(parsed).toMatchObject({
      ok: true,
      source: "v2",
      wengineProvided: true,
      config: {
        build_mode: "equipment-build",
        manual_panel_stats: null,
        character_level: 48,
        wengine: null,
      },
      equipment: { wengine: null, drive_discs: [] },
    });
  });

  it("defaults only missing core/cinema values to 7/0 and keeps explicit progress", () => {
    const base = {
      schema_version: "zzz-character-config-v2",
      character_id: "character:demo",
      character_level: 60,
      build_mode: "equipment-build",
      compile_config: {},
      wengine: null,
      drive_discs: [],
      manual_panel_stats: null,
    };
    const defaulted = parseCharacterConfig(JSON.stringify(base), "character:demo", catalog);
    expect(defaulted).toMatchObject({
      ok: true,
      config: { compile_config: { core_level: 7, cinema_level: 0 } },
    });

    const explicit = parseCharacterConfig(JSON.stringify({
      ...base,
      compile_config: { core_level: 3, cinema_level: 5 },
    }), "character:demo", catalog);
    expect(explicit).toMatchObject({
      ok: true,
      config: { compile_config: { core_level: 3, cinema_level: 5 } },
    });
  });

  it("accepts cross-specialty W-Engines and retains their explicit equipment selection", () => {
    const config = createCharacterConfig(
      "character:demo",
      60,
      "equipment-build",
      { core_level: 1, cinema_level: 0 },
      { id: "wengine:demo", level: 60, refinement: 5 },
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(config),
      "character:demo",
      { ...catalog, characterSpecialty: "support" },
    );
    expect(parsed).toMatchObject({
      ok: true,
      config: { build_mode: "equipment-build", wengine: { id: "wengine:demo", refinement: 5 } },
      equipment: { wengine: { id: "wengine:demo", refinement: 5 } },
    });
  });

  it("round-trips Nekomata's compile fields and signature W-Engine through v2", () => {
    const nekomata = createCharacterConfig(
      "character:1021",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 12,
          dodge: 12,
          "special-attack": 12,
          "chain-attack": 12,
          assist: 12,
          ultimate: 12,
        },
      },
      { id: "wengine:14102", level: 60, refinement: 1 },
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(nekomata),
      "character:1021",
      { ...catalog, characterSpecialty: "attack" },
    );
    expect(parsed).toMatchObject({
      ok: true,
      config: nekomata,
      source: "v2",
      wengineProvided: true,
      equipment: {
        character_id: "character:1021",
        wengine: { id: "wengine:14102", level: 60, refinement: 1 },
      },
    });
  });

  it("round-trips Nicole's support compile fields and A-rank R5 signature through v2", () => {
    const nicole = createCharacterConfig(
      "character:1031",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 16,
          dodge: 16,
          "special-attack": 16,
          "chain-attack": 16,
          assist: 16,
          ultimate: 16,
        },
      },
      { id: "wengine:13103", level: 60, refinement: 5 },
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(nicole),
      "character:1031",
      { ...catalog, characterSpecialty: "support" },
    );
    expect(parsed).toMatchObject({
      ok: true,
      config: nicole,
      source: "v2",
      wengineProvided: true,
      equipment: {
        character_id: "character:1031",
        wengine: { id: "wengine:13103", level: 60, refinement: 5 },
      },
    });
  });

  it.each(roundTripWengines)(
    "round-trips $id and refinement through v2",
    ({ id: wengineId, characterId, specialty }) => {
      const pleniluna = createCharacterConfig(
        characterId,
        60,
        "equipment-build",
        {
          core_level: 1,
          cinema_level: 0,
          mingxin_active: false,
          entry_move_uses_linren: false,
        },
        { id: wengineId, level: 60, refinement: 5 },
        [],
        null,
      );
      const parsed = parseCharacterConfig(
        serializeCharacterConfig(pleniluna),
        characterId,
        { ...catalog, characterSpecialty: specialty },
      );

      expect(parsed).toEqual({
        ok: true,
        config: pleniluna,
        equipment: {
          schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
          character_id: characterId,
          wengine: { id: wengineId, level: 60, refinement: 5 },
          drive_discs: [],
        },
        source: "v2",
        wengineProvided: true,
      });
    },
  );

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

  it("round-trips Nekomata's potential slider value through v2", () => {
    const nekomata = createCharacterConfig(
      "character:1021",
      60,
      "equipment-build",
      { core_level: 1, cinema_level: 0, potential_level: 6 },
      { id: "wengine:14102", level: 60, refinement: 1 },
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(nekomata),
      "character:1021",
      catalog,
    );

    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.config.compile_config.potential_level).toBe(6);
  });

  it("rejects a Nekomata potential value outside its slider range", () => {
    const nekomata = createCharacterConfig(
      "character:1021",
      60,
      "equipment-build",
      { core_level: 1, cinema_level: 0, potential_level: 7 },
      null,
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(nekomata),
      "character:1021",
      catalog,
    );
    expect(parsed.ok).toBe(false);
  });

  it("round-trips Potential sliders for every registered Potential character", () => {
    const characterIds = [
      "character:1021",
      "character:1041",
      "character:1101",
      "character:1141",
      "character:1171",
      "character:1181",
      "character:1191",
      "character:1201",
      "character:1211",
      "character:1261",
    ];
    for (const characterId of characterIds) {
      const character = createCharacterConfig(
        characterId,
        60,
        "equipment-build",
        { core_level: 7, cinema_level: 0, potential_level: 6 },
        null,
        [],
        null,
      );
      const parsed = parseCharacterConfig(
        serializeCharacterConfig(character),
        characterId,
        catalog,
      );
      expect(parsed.ok).toBe(true);
      if (parsed.ok) expect(parsed.config.compile_config.potential_level).toBe(6);
    }
  });

  it("rejects out-of-range Potential values for registered Potential characters", () => {
    const characterIds = [
      "character:1021",
      "character:1041",
      "character:1101",
      "character:1141",
      "character:1171",
      "character:1181",
      "character:1191",
      "character:1201",
      "character:1211",
      "character:1261",
    ];
    for (const characterId of characterIds) {
      const character = createCharacterConfig(
        characterId,
        60,
        "equipment-build",
        { core_level: 7, cinema_level: 0, potential_level: 7 },
        null,
        [],
        null,
      );
      expect(
        parseCharacterConfig(
          serializeCharacterConfig(character),
          characterId,
          catalog,
        ).ok,
      ).toBe(false);
    }
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

  it("round-trips Dialyn's core, cinema, and skill levels through v2", () => {
    const dialyn = createCharacterConfig(
      "character:1481",
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
      serializeCharacterConfig(dialyn),
      "character:1481",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: dialyn,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1481",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Vivian's core, cinema, and skill levels through v2", () => {
    const vivian = createCharacterConfig(
      "character:1331",
      60,
      "equipment-build",
      {
        core_level: 7,
        cinema_level: 6,
        skill_levels: {
          "basic-attack": 16,
          dodge: 14,
          "special-attack": 15,
          "chain-attack": 12,
          assist: 13,
          ultimate: 10,
        },
      },
      null,
      [],
      null,
    );
    const parsed = parseCharacterConfig(
      serializeCharacterConfig(vivian),
      "character:1331",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: vivian,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1331",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Zhao's core, cinema, and skill levels through v2", () => {
    const zhao = createCharacterConfig(
      "character:1341",
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
      serializeCharacterConfig(zhao),
      "character:1341",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: zhao,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1341",
        wengine: null,
        drive_discs: [],
      },
      source: "v2",
      wengineProvided: true,
    });
  });

  it("round-trips Qingyi's core, cinema, and skill levels through v2", () => {
    const qingyi = createCharacterConfig(
      "character:1251",
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
      serializeCharacterConfig(qingyi),
      "character:1251",
      catalog,
    );

    expect(parsed).toEqual({
      ok: true,
      config: qingyi,
      equipment: {
        schema_version: EQUIPMENT_CONFIG_SCHEMA_VERSION,
        character_id: "character:1251",
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
    expect(explicitNull).toMatchObject({
      ok: true,
      source: "v1",
      wengineProvided: true,
      config: { compile_config: { core_level: 7, cinema_level: 0 } },
    });
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
