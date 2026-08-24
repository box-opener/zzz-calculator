import type { BuffRule } from "../../src/domain/model/buff.js";

/**
 * 已从旧版平面数字字段迁移的无条件 2 件套规则。
 * 这里只放已被 UID 16241824 参考面板验证过的两套，其他套装继续走旧兼容字段。
 */
export const DRIVE_DISC_2PC_RULES: Readonly<Record<string, readonly BuffRule[]>> = {
  "31800": [
    {
      schemaVersion: 1,
      id: "set:31800:2pc",
      source: {
        type: "drive-disc-set",
        id: "31800",
        label: "混沌爵士 2 件套",
        provider: "reference",
      },
      status: "verified",
      target: "self",
      phase: "panel",
      timing: "permanent",
      condition: { type: "always" },
      rawDescription: "异常精通 +30。",
      effects: [
        {
          kind: "stat",
          stat: "anomalyProficiency",
          operation: "add-flat",
          value: 30,
        },
      ],
    },
  ],
  "32600": [
    {
      schemaVersion: 1,
      id: "set:32600:2pc",
      source: {
        type: "drive-disc-set",
        id: "32600",
        label: "獠牙重金属 2 件套",
        provider: "reference",
      },
      status: "verified",
      target: "self",
      phase: "panel",
      timing: "permanent",
      condition: { type: "always" },
      rawDescription: "物理伤害加成 +10%。",
      effects: [
        {
          kind: "stat",
          stat: "physicalDmgBonus",
          operation: "add-flat",
          value: 10,
        },
      ],
    },
  ],
};
