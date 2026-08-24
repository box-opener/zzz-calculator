import type {
  CharacterBuild,
  DriveDiscBuild,
  DriveDiscStat,
  ImportedShowcase,
  SkillCategory,
} from "../../domain/model/character-build.js";
import { ENKA_PROPERTY_MAP } from "./property-map.js";
import type {
  EnkaAvatar,
  EnkaEquipment,
  EnkaResponse,
  EnkaSkillLevel,
  EnkaStat,
} from "./types.js";

const SKILL_CATEGORY_MAP: Readonly<Record<number, SkillCategory>> = {
  0: "basic",
  1: "special",
  2: "dodge",
  3: "chain",
  5: "core",
  6: "assist",
};

function mapStat(stat: EnkaStat): DriveDiscStat {
  const mappedKey = ENKA_PROPERTY_MAP[stat.PropertyId];
  return {
    propertyId: stat.PropertyId,
    rawValue: stat.PropertyValue,
    ...(mappedKey ? { key: mappedKey } : {}),
    ...(stat.PropertyLevel !== undefined ? { rolls: stat.PropertyLevel } : {}),
  };
}

function mapDisc(slot: number, equipment: EnkaEquipment): DriveDiscBuild {
  if (slot < 1 || slot > 6) {
    throw new Error(`未知驱动盘分区：${slot}`);
  }

  const mainStats = equipment.MainStatList ?? equipment.MainPropertyList ?? [];
  return {
    ...(equipment.Uid !== undefined ? { uid: String(equipment.Uid) } : {}),
    id: String(equipment.Id),
    slot: slot as DriveDiscBuild["slot"],
    level: equipment.Level,
    mainStats: mainStats.map(mapStat),
    subStats: (equipment.RandomPropertyList ?? []).map(mapStat),
  };
}

function mapSkillLevels(
  skillLevels: EnkaAvatar["SkillLevelList"],
): CharacterBuild["character"]["skillLevels"] {
  const result: CharacterBuild["character"]["skillLevels"] = {};
  if (!skillLevels) return result;

  if (!Array.isArray(skillLevels)) {
    for (const [rawIndex, level] of Object.entries(skillLevels)) {
      const category = SKILL_CATEGORY_MAP[Number(rawIndex)];
      if (category) result[category] = level;
    }
    return result;
  }

  for (const skill of skillLevels as EnkaSkillLevel[]) {
    const index = skill.Index ?? skill.SkillType;
    const level = skill.Level ?? skill.SkillLevel;
    if (index === undefined || level === undefined) continue;
    const category = SKILL_CATEGORY_MAP[index];
    if (category) result[category] = level;
  }
  return result;
}

function mapAvatar(uid: string, avatar: EnkaAvatar): CharacterBuild {
  const warnings: string[] = [];
  const discs = (avatar.EquippedList ?? []).map((item) =>
    mapDisc(item.Slot, item.Equipment),
  );

  if (discs.length !== 6) {
    warnings.push(`公开展示只返回了 ${discs.length}/6 个驱动盘。`);
  }

  return {
    schemaVersion: 1,
    source: {
      type: "enka",
      provider: "enka.network",
      uid,
      importedAt: new Date().toISOString(),
    },
    character: {
      id: String(avatar.Id),
      level: avatar.Level,
      promotion: avatar.PromotionLevel ?? 0,
      cinema: avatar.TalentLevel ?? 0,
      coreLevel: avatar.CoreSkillEnhancement ?? 0,
      skillLevels: mapSkillLevels(avatar.SkillLevelList),
    },
    weapon: avatar.Weapon
      ? {
          ...(avatar.Weapon.Uid !== undefined
            ? { uid: String(avatar.Weapon.Uid) }
            : {}),
          id: String(avatar.Weapon.Id),
          level: avatar.Weapon.Level,
          refinement: avatar.Weapon.UpgradeLevel ?? 1,
        }
      : null,
    driveDiscs: discs,
    warnings,
  };
}

export function mapEnkaShowcase(response: EnkaResponse): ImportedShowcase {
  const uid = String(response.uid ?? "");
  const avatars = response.PlayerInfo?.ShowcaseDetail?.AvatarList ?? [];
  const warnings: string[] = [];

  if (!uid) warnings.push("接口响应缺少 UID。");
  if (avatars.length === 0) {
    warnings.push("未读取到公开展示角色；展示可能为空或未公开。");
  }

  return {
    uid,
    ...(response.PlayerInfo?.SocialDetail?.ProfileDetail?.Nickname
      ? { nickname: response.PlayerInfo.SocialDetail.ProfileDetail.Nickname }
      : {}),
    ...(response.ttl !== undefined ? { ttl: response.ttl } : {}),
    builds: avatars.map((avatar) => mapAvatar(uid, avatar)),
    warnings,
  };
}
