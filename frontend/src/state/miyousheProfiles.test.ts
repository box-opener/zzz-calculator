import { describe, expect, it } from "vitest";
import { MIYOUSHE_STORAGE_KEY, readMiyousheProfiles, saveMiyousheProfile, validateMiyousheProfile } from "./miyousheProfiles";
import { createCharacterConfig } from "./equipmentConfig";

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
