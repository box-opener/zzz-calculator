import type { BuffCondition } from "../model/buff.js";

/**
 * 旧计算器已经使用的额外能力队伍触发规则：同属性、同职业或同阵营。
 * 1401（爱丽丝）和 1071（凯撒）的特殊职业触发也在这里集中表达，
 * 这样角色数据不需要再维护一张硬编码阵营表。
 */
export function buildExtraAbilityActivationCondition(
  characterId?: string,
): BuffCondition {
  const conditions: BuffCondition[] = [
    { type: "team-match", relation: "element" },
    { type: "team-match", relation: "role" },
    { type: "team-match", relation: "camp" },
  ];
  if (characterId === "1401") {
    conditions.push(
      { type: "team-role", role: "异常" },
      { type: "team-role", role: "支援" },
    );
  }
  if (characterId === "1071") {
    conditions.push({ type: "team-role", role: "防护" });
  }
  return { type: "any", conditions };
}
