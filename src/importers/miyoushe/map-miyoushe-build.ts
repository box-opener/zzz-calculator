import type {
  CharacterBuild,
  DriveDiscStat,
  ImportedShowcase,
  SkillCategory,
  SourcePanelStat,
} from "../../domain/model/character-build.js";
import { ENKA_PROPERTY_MAP as PROPERTY_MAP } from "../enka/property-map.js";
import type {
  MiyousheAvatarDetail,
  MiyousheDetailResponse,
  MiyoushePanelProperty,
  MiyousheProperty,
} from "./types.js";

const SKILL_CATEGORY_MAP: Readonly<Record<number, SkillCategory>> = {
  0: "basic",
  1: "special",
  2: "dodge",
  3: "chain",
  5: "core",
  6: "assist",
};

function parseNumber(value: string | number | undefined): number | undefined {
  if (value === undefined || value === "") return undefined;
  const parsed = Number(String(value).replace("%", ""));
  return Number.isFinite(parsed) ? parsed : undefined;
}

function mapStat(property: MiyousheProperty): DriveDiscStat {
  const value = parseNumber(property.base);
  return {
    propertyId: property.property_id,
    ...(PROPERTY_MAP[property.property_id]
      ? { key: PROPERTY_MAP[property.property_id] }
      : {}),
    ...(value !== undefined ? { value, rawValue: value } : {}),
    ...(property.add !== undefined ? { rolls: Number(property.add) } : {}),
  };
}

function mapPanelStat(property: MiyoushePanelProperty): SourcePanelStat {
  const base = parseNumber(property.base);
  const add = parseNumber(property.add);
  return {
    propertyId: property.property_id,
    ...(property.property_name ? { name: property.property_name } : {}),
    ...(base !== undefined ? { base } : {}),
    ...(add !== undefined ? { add } : {}),
    final: parseNumber(property.final_val) ?? 0,
  };
}

function mapAvatar(uid: string, detail: MiyousheAvatarDetail): CharacterBuild {
  const warnings: string[] = [];
  const skills: CharacterBuild["character"]["skillLevels"] = {};
  let coreLevel = 0;
  for (const skill of detail.avatar.skills ?? []) {
    const category = SKILL_CATEGORY_MAP[skill.skill_type];
    if (category) skills[category] = skill.level;
    if (category === "core") coreLevel = skill.level;
  }

  const discs = (detail.equip ?? []).map((equip) => ({
    id: String(equip.id),
    ...(equip.equip_suit?.suit_id
      ? { setId: String(equip.equip_suit.suit_id) }
      : {}),
    slot: equip.equipment_type as 1 | 2 | 3 | 4 | 5 | 6,
    level: equip.level,
    ...(equip.rarity === "S" ? { rarity: 5 } : {}),
    mainStats: (equip.main_properties ?? []).map(mapStat),
    subStats: (equip.properties ?? []).map(mapStat),
  }));
  if (discs.length !== 6) warnings.push(`米游社返回了 ${discs.length}/6 个驱动盘。`);

  return {
    schemaVersion: 1,
    source: {
      type: "miyoushe",
      provider: "米游社官方养成指南",
      uid,
      importedAt: new Date().toISOString(),
    },
    character: {
      id: String(detail.avatar.id),
      level: detail.avatar.level,
      promotion: detail.avatar.promotes ?? 0,
      cinema: detail.avatar.rank ?? 0,
      coreLevel,
      skillLevels: skills,
    },
    weapon: detail.weapon
      ? {
          id: String(detail.weapon.id),
          level: detail.weapon.level,
          refinement: detail.weapon.star ?? 1,
        }
      : null,
    driveDiscs: discs,
    reportedPanel: (detail.avatar.properties ?? []).map(mapPanelStat),
    warnings,
  };
}

export function mapMiyousheResponse(
  uid: string,
  response: MiyousheDetailResponse,
): ImportedShowcase {
  if (response.retcode !== 0) {
    throw new Error(response.message ?? `米游社接口错误：${response.retcode}`);
  }
  const details = response.data?.list ?? [];
  return {
    uid,
    builds: details
      .filter((detail) => detail.avatar.level > 0)
      .map((detail) => mapAvatar(uid, detail)),
    warnings: details.length === 0 ? ["米游社响应中没有角色详情。"] : [],
  };
}
