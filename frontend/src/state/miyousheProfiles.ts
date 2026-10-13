import { createCharacterConfig, parseCharacterConfig, type CharacterConfig, type EquipmentValidationCatalog } from "./equipmentConfig";

export const MIYOUSHE_STORAGE_KEY = "zzz-miyoushe-profiles-v1";
export type MiyousheCharacter = {
  character_id: string;
  display_name: string;
  level: number | null;
  cinema: number | null;
  configuration: CharacterConfig | null;
  issues: string[];
  source_data: Record<string, unknown>;
};
export type MiyousheProfile = {
  schema_version: "zzz-miyoushe-profile-v1";
  provider: "miyoushe";
  uid: string;
  server: "prod_gf_cn";
  fetched_at: string;
  characters: MiyousheCharacter[];
};

/** Imported account snapshots may only be replaced by a new import. */
function freezeSnapshot<T>(value: T): T {
  if (value && typeof value === "object") {
    for (const child of Object.values(value)) freezeSnapshot(child);
    Object.freeze(value);
  }
  return value;
}

/** Hand the editor an independent draft, including nested skills and substats. */
export function createMiyousheDraft(config: CharacterConfig): CharacterConfig {
  return createCharacterConfig(config.character_id, config.character_level, config.build_mode,
    config.compile_config, config.wengine, config.drive_discs, null, config.effective_substats);
}

/** The official count belongs to the fetched drive-disc build, not final panel stats. */
export function miyousheEffectiveStatCount(source: Record<string, unknown>): number | null {
  const plan = source.equip_plan_info;
  if (!plan || typeof plan !== "object" || Array.isArray(plan)) return null;
  const count = (plan as Record<string, unknown>).valid_property_cnt;
  return typeof count === "number" && Number.isSafeInteger(count) && count >= 0 ? count : null;
}

function safeSource(value: unknown, depth = 0): unknown {
  if (depth > 7) return null;
  if (value === null || typeof value === "boolean" || typeof value === "number") return value;
  if (typeof value === "string") return value.slice(0, 200);
  if (Array.isArray(value)) return value.slice(0, 100).map((v) => safeSource(v, depth + 1));
  if (value && typeof value === "object") return Object.fromEntries(
    Object.entries(value).filter(([k]) => !/cookie|token|password|authorization|__proto__|constructor/i.test(k))
      .map(([k, v]) => [k, safeSource(v, depth + 1)]),
  );
  return null;
}

export function validateMiyousheProfile(raw: unknown, catalog: EquipmentValidationCatalog): MiyousheProfile {
  if (!raw || typeof raw !== "object") throw new Error("米游社资料格式无效。");
  const p = raw as Record<string, unknown>;
  if (p.schema_version !== "zzz-miyoushe-profile-v1" || p.provider !== "miyoushe"
      || typeof p.uid !== "string" || !/^[1-9]\d{5,8}$/.test(p.uid) || p.server !== "prod_gf_cn"
      || typeof p.fetched_at !== "string" || !Number.isFinite(Date.parse(p.fetched_at))
      || !Array.isArray(p.characters) || p.characters.length > 100) throw new Error("米游社资料版本或内容无效。");
  const ids = new Set<string>();
  const characters = p.characters.map((row: unknown): MiyousheCharacter => {
    if (!row || typeof row !== "object") throw new Error("米游社角色资料无效。");
    const r = row as Record<string, unknown>;
    if (typeof r.character_id !== "string" || !/^character:\d+$/.test(r.character_id)
        || ids.has(r.character_id) || typeof r.display_name !== "string" || !Array.isArray(r.issues)) throw new Error("米游社角色资料无效。");
    ids.add(r.character_id);
    let configuration: CharacterConfig | null = null;
    if (r.configuration !== null) {
      const result = parseCharacterConfig(JSON.stringify(r.configuration), r.character_id, catalog);
      if (!result.ok) throw new Error(`角色配置无法读取：${result.message}`);
      configuration = result.config;
    }
    const source = safeSource(r.source_data);
    return {
      character_id: r.character_id, display_name: r.display_name.slice(0, 80),
      level: typeof r.level === "number" ? r.level : null,
      cinema: typeof r.cinema === "number" ? r.cinema : null,
      configuration, issues: r.issues.filter((s): s is string => typeof s === "string").map((s) => s.slice(0, 200)),
      source_data: source && typeof source === "object" && !Array.isArray(source) ? source as Record<string, unknown> : {},
    };
  });
  return freezeSnapshot({ schema_version: "zzz-miyoushe-profile-v1", provider: "miyoushe", uid: p.uid,
    server: "prod_gf_cn", fetched_at: p.fetched_at, characters } as MiyousheProfile);
}

export function readMiyousheProfiles(storage: Pick<Storage, "getItem">, catalog: EquipmentValidationCatalog): MiyousheProfile[] {
  const text = storage.getItem(MIYOUSHE_STORAGE_KEY);
  if (!text) return [];
  const rows: unknown = JSON.parse(text);
  if (!Array.isArray(rows)) throw new Error("本地米游社资料格式损坏，请清除后重新获取。");
  return rows.slice(0, 5).map((row) => validateMiyousheProfile(row, catalog));
}

export function saveMiyousheProfile(profiles: MiyousheProfile[], incoming: MiyousheProfile): MiyousheProfile[] {
  return [freezeSnapshot(structuredClone(incoming)), ...profiles.filter((p) => p.uid !== incoming.uid)].slice(0, 5);
}
