import { describe, expect, it } from "vitest";
import { MIYOUSHE_STORAGE_KEY, createMiyousheDraft, readMiyousheProfiles, saveMiyousheProfile, validateMiyousheProfile, miyousheEffectiveStatCount } from "./miyousheProfiles";
import { createCharacterConfig, parseCharacterConfig, serializeCharacterConfig } from "./equipmentConfig";

const catalog = { wengines: [], driveDiscSets: [] };
function snapshot(uid = "12345678") {
  return { schema_version: "zzz-miyoushe-profile-v1", provider: "miyoushe", server: "prod_gf_cn", uid,
    fetched_at: "2026-10-13T05:00:00Z", cookie: "should-not-persist",
    characters: [{ character_id: "character:1381", display_name: "零号·安比", level: 60, cinema: 6,
      configuration: createCharacterConfig("character:1381", 60, "equipment-build", { core_level: 7, cinema_level: 6, potential_level: 2 }, null, [], null),
      issues: [], source_data: { level: 60, ltoken_v2: "should-not-persist", nested: { cookie: "should-not-persist" } },
    }],
  };
}

describe("saved Miyoushe profiles", () => {
  it("keeps nested imported equipment and skills immutable while edited exports round-trip separately", () => {
    const raw = snapshot();
    const equipmentCatalog = { wengines: [{ wengine_id: "wengine:14138" }], driveDiscSets: [{ set_id: "drive-disc:31000" }] };
    raw.characters[0].configuration = createCharacterConfig("character:1381", 60, "equipment-build",
      { core_level: 7, cinema_level: 6, skill_levels: { "basic-attack": 12 } },
      { id: "wengine:14138", level: 60, refinement: 1 },
      [{ slot: 1, set_id: "drive-disc:31000", main_stat: "hp-flat", substats: [{ stat: "attack-percent", roll_count: 2 }] }], null, ["attack-percent"]);
    const saved = saveMiyousheProfile([], validateMiyousheProfile(raw, equipmentCatalog));
    const before = JSON.stringify(saved);
    const original = saved[0].characters[0].configuration!;
    expect(() => { original.drive_discs[0].substats[0].roll_count = 5; }).toThrow(TypeError);
    const draft = createMiyousheDraft(original);
    draft.drive_discs[0].substats[0].roll_count = 5;
    (draft.compile_config.skill_levels as Record<string, number>)["basic-attack"] = 15;
    draft.wengine!.refinement = 3;
    draft.effective_substats!.push("crit-rate");
    const edited = parseCharacterConfig(serializeCharacterConfig(draft), draft.character_id, equipmentCatalog);
    expect(edited.ok && edited.config.drive_discs[0].substats[0].roll_count).toBe(5);
    draft.drive_discs = [];
    expect(JSON.stringify(saved)).toBe(before);
    const reloaded = readMiyousheProfiles({ getItem: () => before }, equipmentCatalog);
    expect(createMiyousheDraft(reloaded[0].characters[0].configuration!)).toEqual(original);
  });

  it("overwrites a refreshed UID with a detached immutable snapshot", () => {
    const old = validateMiyousheProfile(snapshot(), catalog);
    const raw = snapshot();
    raw.characters[0].configuration.compile_config.cinema_level = 2;
    raw.characters[0].cinema = 2;
    const incoming = structuredClone(validateMiyousheProfile(raw, catalog));
    const next = saveMiyousheProfile([old], incoming);
    incoming.characters[0].configuration!.compile_config.cinema_level = 4;
    expect(next).toHaveLength(1);
    expect(next[0].characters[0].configuration!.compile_config.cinema_level).toBe(2);
    expect(old.characters[0].configuration!.compile_config.cinema_level).toBe(6);
  });

  it("retains the official drive-disc count offline, including zero, without inferring it from stats", () => {
    const raw = snapshot();
    raw.characters[0].source_data = { ...raw.characters[0].source_data, ...{ equip_plan_info: { valid_property_cnt: 37 } } };
    const profile = validateMiyousheProfile(raw, catalog);
    const saved = readMiyousheProfiles({ getItem: () => JSON.stringify([profile]) }, catalog);
    expect(miyousheEffectiveStatCount(saved[0].characters[0].source_data)).toBe(37);
    expect(miyousheEffectiveStatCount({ equip_plan_info: { valid_property_cnt: 0 } })).toBe(0);
    expect(miyousheEffectiveStatCount({ properties: [{ final: 3500 }] })).toBeNull();
    for (const invalid of [-1, 1.5, true, "37", Number.MAX_SAFE_INTEGER + 1]) {
      expect(miyousheEffectiveStatCount({ equip_plan_info: { valid_property_cnt: invalid } })).toBeNull();
    }
  });
  it("reloads real configuration offline and excludes credentials", () => {
    const profile = validateMiyousheProfile(snapshot(), catalog);
    const text = JSON.stringify([profile]);
    expect(text).not.toContain("should-not-persist");
    const saved = readMiyousheProfiles({ getItem: (key) => key === MIYOUSHE_STORAGE_KEY ? text : null }, catalog);
    expect(saved[0].characters[0].configuration?.compile_config.potential_level).toBe(2);
    expect(saved[0].characters[0].configuration?.wengine).toBeNull();
  });
  it("keeps distinct UIDs and replaces only the refreshed account with a bounded cache", () => {
    let rows = [validateMiyousheProfile(snapshot(), catalog)];
    for (let i = 0; i < 7; i++) rows = saveMiyousheProfile(rows, validateMiyousheProfile(snapshot(`1234568${i}`), catalog));
    expect(rows).toHaveLength(5);
    const refreshed = { ...rows[2], fetched_at: "2026-10-14T01:00:00Z" };
    const next = saveMiyousheProfile(rows, refreshed);
    expect(next).toHaveLength(5);
    expect(next[0]).toEqual(refreshed);
    expect(new Set(next.map((p) => p.uid)).size).toBe(5);
  });
  it("rejects stale schema and damaged cache instead of loading invented configuration", () => {
    expect(() => validateMiyousheProfile({ ...snapshot(), schema_version: "old" }, catalog)).toThrow();
    expect(() => readMiyousheProfiles({ getItem: () => "bad json" }, catalog)).toThrow();
    expect(readMiyousheProfiles({ getItem: () => null }, catalog)).toEqual([]);
  });
  it("preserves unsupported source data without making it selectable", () => {
    const original = snapshot();
    const raw = { ...original, characters: [{ ...original.characters[0], configuration: null, issues: ["未支持的等级"] }] };
    const profile = validateMiyousheProfile(raw, catalog);
    expect(profile.characters[0].configuration).toBeNull();
    expect(profile.characters[0].source_data.level).toBe(60);
  });
});
