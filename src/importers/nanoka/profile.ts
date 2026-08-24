export interface NanokaCharacterProfile {
  id: string;
  name: string;
  role?: string;
  element?: string;
  camp?: string;
}

function firstString(value: unknown): string | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  const first = Object.values(value as Record<string, unknown>)[0];
  return typeof first === "string" && first.length > 0 ? first : undefined;
}

/** 从 Nanoka 角色详情提取队伍条件所需的稳定标签。 */
export function mapNanokaCharacterProfile(
  id: string,
  detail: Record<string, unknown>,
): NanokaCharacterProfile {
  const name = typeof detail.name === "string" ? detail.name : `角色 ${id}`;
  const role = firstString(detail.weapon_type);
  const element = firstString(detail.element_type);
  const camp = firstString(detail.camp);
  return {
    id,
    name,
    ...(role ? { role } : {}),
    ...(element ? { element } : {}),
    ...(camp ? { camp } : {}),
  };
}

export function mapNanokaCharacterProfiles(
  details: Readonly<Record<string, Record<string, unknown>>>,
): NanokaCharacterProfile[] {
  return Object.entries(details).map(([id, detail]) =>
    mapNanokaCharacterProfile(id, detail),
  );
}

/** 为 BuffCondition evaluator 生成不含旧版硬编码表的队伍上下文。 */
export function buildNanokaTeamConditionValues(
  selfId: string,
  profiles: readonly NanokaCharacterProfile[],
): Readonly<Record<string, unknown>> {
  const self = profiles.find((profile) => profile.id === selfId);
  return {
    team: {
      members: profiles,
      ...(self ? { self } : {}),
    },
  };
}
