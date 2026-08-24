import type { BuffRule } from "../../src/domain/model/buff.js";

/**
 * Nanoka 3.2.1+17934514 音擎与驱动盘已确认规则。
 *
 * 音擎规则带 weaponRefinement，只激活当前精炼档位；驱动盘规则带
 * equippedCountAtLeast，只在满足 2/4 件套时激活。范围外条目不在此文件中。
 */
export const NANOKA_EQUIPMENT_REVIEWED_RULES: readonly BuffRule[] = [
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31000_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31000",
      "label": "啄木鸟电音｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31000.json",
      "key": "equipment:31000:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "暴击率+8%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31000_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31000",
      "label": "啄木鸟电音｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31000.json",
      "key": "equipment:31000:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[强化特殊技]</color>命中敌人并触发暴击时，分别为装备者提供1层增益效果，每层增益效果使装备者的攻击力提升9%，持续6秒，不同招式分别结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31100_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31100",
      "label": "河豚电音｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31100.json",
      "key": "equipment:31100:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "penRate",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "穿透率+8%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31100_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31100",
      "label": "河豚电音｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31100.json",
      "key": "equipment:31100:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[终结技]</color>造成的伤害提升20%；发动<color=#FFFFFF>[终结技]</color>时，装备者的攻击力提升15%，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31200_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31200",
      "label": "震星迪斯科｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31200.json",
      "key": "equipment:31200:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "冲击力+6%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31200_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31200",
      "label": "震星迪斯科｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31200.json",
      "key": "equipment:31200:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>对主要攻击目标造成的失衡值提升20%。",
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31300_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31300",
      "label": "自由蓝调｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31300.json",
      "key": "equipment:31300:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 30
      }
    ],
    "rawDescription": "异常精通+30点。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31400_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31400",
      "label": "激素朋克｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31400.json",
      "key": "equipment:31400:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "攻击力+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31400_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31400",
      "label": "激素朋克｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31400.json",
      "key": "equipment:31400:desc4"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升25%，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31500_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "31500",
      "label": "灵魂摇滚｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31500.json",
      "key": "equipment:31500:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "防御力+16%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31600_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31600",
      "label": "摇摆爵士｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31600.json",
      "key": "equipment:31600:desc4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色造成的伤害提升15%，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "equippedCountAtLeast": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31800_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31800",
      "label": "混沌爵士｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31800.json",
      "key": "equipment:31800:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ],
          "elements": [
            "fire",
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FF5521>火属性伤害</color>和<color=#2EB6FF>电属性伤害</color>提升15%；位于后场时，<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[支援攻击]</color>造成的伤害提升20%，换入前场后，该增益效果仍然保留，持续5秒，保留效果7.5秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_31900_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "31900",
      "label": "原始朋克｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/31900.json",
      "key": "equipment:31900:desc4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[招架支援]</color>或<color=#FFFFFF>[回避支援]</color>时，全队角色造成的伤害提升15%，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "equippedCountAtLeast": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32200_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32200",
      "label": "炎狱重金属｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32200.json",
      "key": "equipment:32200:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#FF5521>火属性伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32200_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32200",
      "label": "炎狱重金属｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32200.json",
      "key": "equipment:32200:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "state",
      "target": "enemy",
      "state": "灼烧",
      "equals": true
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      }
    ],
    "rawDescription": "攻击命中处于<color=#FF5521>[灼烧]</color>状态下的敌人时，装备者的暴击率提升28%，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32300_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32300",
      "label": "混沌重金属｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32300.json",
      "key": "equipment:32300:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#FE437E>以太伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32300_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32300",
      "label": "混沌重金属｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32300.json",
      "key": "equipment:32300:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "装备者的暴击伤害提升20%，队伍中任意角色触发<color=#FE437E>[侵蚀]</color>伤害时，该增益效果额外提升5.5%，最多叠加6层，持续8秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32400_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32400",
      "label": "雷暴重金属｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32400.json",
      "key": "equipment:32400:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32400_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32400",
      "label": "雷暴重金属｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32400.json",
      "key": "equipment:32400:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "state",
      "target": "enemy",
      "state": "感电",
      "equals": true
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 28
      }
    ],
    "rawDescription": "当场上存在处于<color=#2EB6FF>[感电]</color>状态下的敌人时，装备者的攻击力提升28%。",
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32500_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32500",
      "label": "极地重金属｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32500.json",
      "key": "equipment:32500:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32500_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32500",
      "label": "极地重金属｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32500.json",
      "key": "equipment:32500:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的伤害提升20%，队伍中任意角色对敌人施加<color=#98EFF0>[冻结]</color>或触发<color=#98EFF0>[碎冰]</color>效果时，该增益效果额外提升20%，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "equippedCountAtLeast": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32700_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32700",
      "label": "折枝剑歌｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32700.json",
      "key": "equipment:32700:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "暴击伤害+16%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32700_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32700",
      "label": "折枝剑歌｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32700.json",
      "key": "equipment:32700:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 12
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 30
      }
    ],
    "rawDescription": "异常掌控大于等于115点时，装备者的暴击伤害提升30%；队伍中任意角色对敌人施加<color=#98EFF0>[冻结]</color>或触发<color=#98EFF0>[碎冰]</color>效果时，装备者的暴击率提升12%，持续15秒。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32800_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32800",
      "label": "静听嘉音｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32800.json",
      "key": "equipment:32800:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "攻击力+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32800_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32800",
      "label": "静听嘉音｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32800.json",
      "key": "equipment:32800:desc4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": {
          "type": "per-stack",
          "base": 0,
          "perStack": 8
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>入场时，全队角色获得1层<color=#FFFFFF>[嘉音]</color>，最多叠加3层，持续15秒，重复触发时刷新持续时间，每拥有1层<color=#FFFFFF>[嘉音]</color>，通过<color=#FFFFFF>[快速支援]</color>入场的角色造成的伤害提升8%，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。；规则修订：满拐静态结算视当前伤害角色为快速支援入场角色，3层按3×8%=24%计入其后续伤害。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32900_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "32900",
      "label": "如影相随｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32900.json",
      "key": "equipment:32900:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[追加攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的伤害提升15%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_32900_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "32900",
      "label": "如影相随｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/32900.json",
      "key": "equipment:32900:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 4
      },
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 4
      }
    ],
    "rawDescription": "<color=#FFFFFF>[追加攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中敌人时，若造成的伤害与装备者的属性一致，则获得1层增益效果，同一招式内最多触发一次；每拥有1层增益效果，装备者的攻击力提升4%，暴击率提升4%，最多叠加3层，持续15秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33000_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33000",
      "label": "法厄同之歌｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33000.json",
      "key": "equipment:33000:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMasteryPct",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "异常掌控+8%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33000_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33000",
      "label": "法厄同之歌｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33000.json",
      "key": "equipment:33000:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 45
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升45点，持续8秒；如果发动<color=#FFFFFF>[强化特殊技]</color>的角色不是装备者本人时，装备者造成的<color=#FE437E>以太伤害</color>提升25%。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33100_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33100",
      "label": "云岿如我｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33100.json",
      "key": "equipment:33100:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "生命值+10%",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33100_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33100",
      "label": "云岿如我｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33100.json",
      "key": "equipment:33100:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，暴击率提升4%，最多叠加3层，持续15秒，重复触发时刷新持续时间，拥有3层效果时，造成的贯穿伤害提升10%。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33200_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33200",
      "label": "山大王｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33200.json",
      "key": "equipment:33200:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "攻击造成的失衡值提升6%",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33200_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33200",
      "label": "山大王｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33200.json",
      "key": "equipment:33200:desc4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者为[击破]角色时，发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>会使全队角色暴击伤害提升15%，装备者的暴击率大于等于50%时暴击伤害额外提升15%，持续15秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "equippedCountAtLeast": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33300_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33300",
      "label": "拂晓生花｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33300.json",
      "key": "equipment:33300:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>造成的伤害提升15%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33300_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33300",
      "label": "拂晓生花｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33300.json",
      "key": "equipment:33300:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "ultimate"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>造成的伤害提升20%，装备者为[强攻]角色时，发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>会使<color=#FFFFFF>[普通攻击]</color>造成的伤害额外提升20%，持续25秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "equippedCountAtLeast": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33500_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33500",
      "label": "沧浪行歌｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33500.json",
      "key": "equipment:33500:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33500_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33500",
      "label": "沧浪行歌｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33500.json",
      "key": "equipment:33500:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "装备者处于任意<color=#FFFFFF>[以太帷幕]</color>中时，自身暴击率提高10%，离开<color=#FFFFFF>[以太帷幕]</color>后，该增益效果仍然保留，持续15秒；装备者为<color=#FFFFFF>[强攻]</color>角色时，开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间会使自身暴击率提升10%和攻击力提升10%，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "equippedCountAtLeast": 4,
    "notes": "原文包含多个持续时间：15、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33600_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33600",
      "label": "流光咏叹｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33600.json",
      "key": "equipment:33600:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#FE437E>以太伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33600_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33600",
      "label": "流光咏叹｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33600.json",
      "key": "equipment:33600:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 36
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[普通攻击]</color>命中敌人时，自身异常精通提升36点，持续8秒，重复触发时刷新持续时间；当场上有敌人进入失衡状态时，装备者造成的伤害提升25%，持续18秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "equippedCountAtLeast": 4,
    "notes": "原文包含多个持续时间：8、18 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33700_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33700",
      "label": "雪兔梦游仙境 ｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33700.json",
      "key": "equipment:33700:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "生命值+10%",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33700_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33700",
      "label": "雪兔梦游仙境 ｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33700.json",
      "key": "equipment:33700:desc4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 6,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "[防护]角色装备时：装备者发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意队友发动<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>时，全队角色造成伤害提升6%，最多叠加3层，持续25秒，层数逐层衰减，获得或者衰减时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33800_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33800",
      "label": "囚徒手记｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33800.json",
      "key": "equipment:33800:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33800_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33800",
      "label": "囚徒手记｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33800.json",
      "key": "equipment:33800:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 48
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[异放]</color>时，装备者异常精通提升48点，持续30秒；重复触发时刷新持续时间；装备者触发<color=#FFFFFF>[冻结]</color>效果时，装备者造成的所有属性异常伤害、<color=#FFFFFF>[紊乱]</color>伤害提升16%，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33900_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "33900",
      "label": "呼啸沙龙｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33900.json",
      "key": "equipment:33900:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "windDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#A6C5FD>风属性伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_33900_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "33900",
      "label": "呼啸沙龙｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/33900.json",
      "key": "equipment:33900:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 25
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者异常精通提升25点，最多叠加2层，持续40秒，重复触发时刷新持续时间；装备者触发<color=#A6C5FD>[风化]</color>效果后，装备者造成的伤害提升18%，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34000_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "34000",
      "label": "拂晓行纪｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34000.json",
      "key": "equipment:34000:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "<color=#FE437E>以太伤害</color>+10%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34000_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "34000",
      "label": "拂晓行纪｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34000.json",
      "key": "equipment:34000:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 30
      }
    ],
    "rawDescription": "装备者为<color=#FE437E>以太属性</color>代理人时，暴击伤害提升30%；装备者发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者的攻击力提升10%，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "equippedCountAtLeast": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34100_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "34100",
      "label": "谶羽之誓｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34100.json",
      "key": "equipment:34100:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 30
      }
    ],
    "rawDescription": "异常精通+30点。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34100_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "34100",
      "label": "谶羽之誓｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34100.json",
      "key": "equipment:34100:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 50
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者进入战场时，或被切换为当前操作中角色时，获得增益效果：异常精通提升50点，若装备者为<color=#FFA9DD>流明属性</color>，造成的属性异常伤害提升15%，持续15秒；\n当装备者为非操作中角色时，则始终持有该增益效果。",
    "trigger": "state-entered",
    "durationSeconds": 15,
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34200_desc2",
    "source": {
      "type": "drive-disc-set",
      "id": "34200",
      "label": "荆棘玫瑰｜2件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34200.json",
      "key": "equipment:34200:desc2"
    },
    "status": "verified",
    "target": "self",
    "phase": "panel",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "防御力+16%。",
    "equippedCountAtLeast": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:equipment_34200_desc4",
    "source": {
      "type": "drive-disc-set",
      "id": "34200",
      "label": "荆棘玫瑰｜4件套",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/equipment/34200.json",
      "key": "equipment:34200:desc4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-flat",
        "value": 8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者造成的伤害提升15%，装备者初始防御力大于等于1000/1800点时，暴击率提升8/16%",
    "equippedCountAtLeast": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12001_talent_1",
    "source": {
      "type": "weapon",
      "id": "12001",
      "label": "「月相」-望｜满月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12001.json",
      "key": "weapon:12001:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 12,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>造成的伤害提升<color=#2BAD00>12%</color>。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12001_talent_2",
    "source": {
      "type": "weapon",
      "id": "12001",
      "label": "「月相」-望｜满月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12001.json",
      "key": "weapon:12001:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>造成的伤害提升<color=#2BAD00>14%</color>。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12001_talent_3",
    "source": {
      "type": "weapon",
      "id": "12001",
      "label": "「月相」-望｜满月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12001.json",
      "key": "weapon:12001:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>造成的伤害提升<color=#2BAD00>16%</color>。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12001_talent_4",
    "source": {
      "type": "weapon",
      "id": "12001",
      "label": "「月相」-望｜满月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12001.json",
      "key": "weapon:12001:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>造成的伤害提升<color=#2BAD00>18%</color>。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12001_talent_5",
    "source": {
      "type": "weapon",
      "id": "12001",
      "label": "「月相」-望｜满月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12001.json",
      "key": "weapon:12001:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic",
            "dodge",
            "dash"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>、<color=#FFFFFF>[闪避反击]</color>造成的伤害提升<color=#2BAD00>20%</color>。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12002_talent_1",
    "source": {
      "type": "weapon",
      "id": "12002",
      "label": "「月相」-晦｜残月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12002.json",
      "key": "weapon:12002:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者造成的伤害提升<color=#2BAD00>15%</color>，持续6秒。",
    "trigger": "skill-used",
    "durationSeconds": 6,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12002_talent_2",
    "source": {
      "type": "weapon",
      "id": "12002",
      "label": "「月相」-晦｜残月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12002.json",
      "key": "weapon:12002:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.5,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者造成的伤害提升<color=#2BAD00>17.5%</color>，持续6秒。",
    "trigger": "skill-used",
    "durationSeconds": 6,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12002_talent_3",
    "source": {
      "type": "weapon",
      "id": "12002",
      "label": "「月相」-晦｜残月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12002.json",
      "key": "weapon:12002:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者造成的伤害提升<color=#2BAD00>20%</color>，持续6秒。",
    "trigger": "skill-used",
    "durationSeconds": 6,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12002_talent_4",
    "source": {
      "type": "weapon",
      "id": "12002",
      "label": "「月相」-晦｜残月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12002.json",
      "key": "weapon:12002:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 22.5,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者造成的伤害提升<color=#2BAD00>22.5%</color>，持续6秒。",
    "trigger": "skill-used",
    "durationSeconds": 6,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12002_talent_5",
    "source": {
      "type": "weapon",
      "id": "12002",
      "label": "「月相」-晦｜残月",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12002.json",
      "key": "weapon:12002:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，装备者造成的伤害提升<color=#2BAD00>25%</color>，持续6秒。",
    "trigger": "skill-used",
    "durationSeconds": 6,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12005_talent_1",
    "source": {
      "type": "weapon",
      "id": "12005",
      "label": "「残响」-Ⅱ型｜音浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12005.json",
      "key": "weapon:12005:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 10
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，全队角色异常掌控和异常精通提升<color=#2BAD00>10</color>点，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12005_talent_2",
    "source": {
      "type": "weapon",
      "id": "12005",
      "label": "「残响」-Ⅱ型｜音浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12005.json",
      "key": "weapon:12005:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 12
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，全队角色异常掌控和异常精通提升<color=#2BAD00>12</color>点，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12005_talent_3",
    "source": {
      "type": "weapon",
      "id": "12005",
      "label": "「残响」-Ⅱ型｜音浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12005.json",
      "key": "weapon:12005:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 13
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，全队角色异常掌控和异常精通提升<color=#2BAD00>13</color>点，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12005_talent_4",
    "source": {
      "type": "weapon",
      "id": "12005",
      "label": "「残响」-Ⅱ型｜音浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12005.json",
      "key": "weapon:12005:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 15
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，全队角色异常掌控和异常精通提升<color=#2BAD00>15</color>点，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12005_talent_5",
    "source": {
      "type": "weapon",
      "id": "12005",
      "label": "「残响」-Ⅱ型｜音浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12005.json",
      "key": "weapon:12005:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 16
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，全队角色异常掌控和异常精通提升<color=#2BAD00>16</color>点，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12006_talent_1",
    "source": {
      "type": "weapon",
      "id": "12006",
      "label": "「残响」-Ⅲ型｜强音",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12006.json",
      "key": "weapon:12006:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色攻击力提升<color=#2BAD00>8%</color>，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12006_talent_2",
    "source": {
      "type": "weapon",
      "id": "12006",
      "label": "「残响」-Ⅲ型｜强音",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12006.json",
      "key": "weapon:12006:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色攻击力提升<color=#2BAD00>9%</color>，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12006_talent_3",
    "source": {
      "type": "weapon",
      "id": "12006",
      "label": "「残响」-Ⅲ型｜强音",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12006.json",
      "key": "weapon:12006:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色攻击力提升<color=#2BAD00>10%</color>，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12006_talent_4",
    "source": {
      "type": "weapon",
      "id": "12006",
      "label": "「残响」-Ⅲ型｜强音",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12006.json",
      "key": "weapon:12006:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色攻击力提升<color=#2BAD00>11%</color>，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12006_talent_5",
    "source": {
      "type": "weapon",
      "id": "12006",
      "label": "「残响」-Ⅲ型｜强音",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12006.json",
      "key": "weapon:12006:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>时，全队角色攻击力提升<color=#2BAD00>12%</color>，持续10秒，20秒内最多触发一次，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12007_talent_1",
    "source": {
      "type": "weapon",
      "id": "12007",
      "label": "「湍流」-铳型｜暗涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12007.json",
      "key": "weapon:12007:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>造成的失衡值提升<color=#2BAD00>10%</color>。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12007_talent_2",
    "source": {
      "type": "weapon",
      "id": "12007",
      "label": "「湍流」-铳型｜暗涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12007.json",
      "key": "weapon:12007:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>造成的失衡值提升<color=#2BAD00>11.5%</color>。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12007_talent_3",
    "source": {
      "type": "weapon",
      "id": "12007",
      "label": "「湍流」-铳型｜暗涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12007.json",
      "key": "weapon:12007:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>造成的失衡值提升<color=#2BAD00>13%</color>。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12007_talent_4",
    "source": {
      "type": "weapon",
      "id": "12007",
      "label": "「湍流」-铳型｜暗涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12007.json",
      "key": "weapon:12007:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>造成的失衡值提升<color=#2BAD00>14.5%</color>。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12007_talent_5",
    "source": {
      "type": "weapon",
      "id": "12007",
      "label": "「湍流」-铳型｜暗涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12007.json",
      "key": "weapon:12007:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>造成的失衡值提升<color=#2BAD00>16%</color>。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12008_talent_1",
    "source": {
      "type": "weapon",
      "id": "12008",
      "label": "「湍流」-矢型｜巨浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12008.json",
      "key": "weapon:12008:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "攻击命中敌人时，装备者对主要攻击目标造成的失衡值提升<color=#2BAD00>8%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12008_talent_2",
    "source": {
      "type": "weapon",
      "id": "12008",
      "label": "「湍流」-矢型｜巨浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12008.json",
      "key": "weapon:12008:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 9
      }
    ],
    "rawDescription": "攻击命中敌人时，装备者对主要攻击目标造成的失衡值提升<color=#2BAD00>9%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12008_talent_3",
    "source": {
      "type": "weapon",
      "id": "12008",
      "label": "「湍流」-矢型｜巨浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12008.json",
      "key": "weapon:12008:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "攻击命中敌人时，装备者对主要攻击目标造成的失衡值提升<color=#2BAD00>10%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12008_talent_4",
    "source": {
      "type": "weapon",
      "id": "12008",
      "label": "「湍流」-矢型｜巨浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12008.json",
      "key": "weapon:12008:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11
      }
    ],
    "rawDescription": "攻击命中敌人时，装备者对主要攻击目标造成的失衡值提升<color=#2BAD00>11%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12008_talent_5",
    "source": {
      "type": "weapon",
      "id": "12008",
      "label": "「湍流」-矢型｜巨浪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12008.json",
      "key": "weapon:12008:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "攻击命中敌人时，装备者对主要攻击目标造成的失衡值提升<color=#2BAD00>12%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12010_talent_1",
    "source": {
      "type": "weapon",
      "id": "12010",
      "label": "「电磁暴」-壹式｜紊乱电流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12010.json",
      "key": "weapon:12010:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 25
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常掌控提升<color=#2BAD00>25</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12010_talent_2",
    "source": {
      "type": "weapon",
      "id": "12010",
      "label": "「电磁暴」-壹式｜紊乱电流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12010.json",
      "key": "weapon:12010:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 28
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常掌控提升<color=#2BAD00>28</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12010_talent_3",
    "source": {
      "type": "weapon",
      "id": "12010",
      "label": "「电磁暴」-壹式｜紊乱电流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12010.json",
      "key": "weapon:12010:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 32
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常掌控提升<color=#2BAD00>32</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12010_talent_4",
    "source": {
      "type": "weapon",
      "id": "12010",
      "label": "「电磁暴」-壹式｜紊乱电流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12010.json",
      "key": "weapon:12010:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 36
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常掌控提升<color=#2BAD00>36</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12010_talent_5",
    "source": {
      "type": "weapon",
      "id": "12010",
      "label": "「电磁暴」-壹式｜紊乱电流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12010.json",
      "key": "weapon:12010:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 40
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常掌控提升<color=#2BAD00>40</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12011_talent_1",
    "source": {
      "type": "weapon",
      "id": "12011",
      "label": "「电磁暴」-贰式｜高压电涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12011.json",
      "key": "weapon:12011:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 25
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常精通提升<color=#2BAD00>25</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12011_talent_2",
    "source": {
      "type": "weapon",
      "id": "12011",
      "label": "「电磁暴」-贰式｜高压电涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12011.json",
      "key": "weapon:12011:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 28
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常精通提升<color=#2BAD00>28</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12011_talent_3",
    "source": {
      "type": "weapon",
      "id": "12011",
      "label": "「电磁暴」-贰式｜高压电涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12011.json",
      "key": "weapon:12011:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 32
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常精通提升<color=#2BAD00>32</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12011_talent_4",
    "source": {
      "type": "weapon",
      "id": "12011",
      "label": "「电磁暴」-贰式｜高压电涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12011.json",
      "key": "weapon:12011:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 36
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常精通提升<color=#2BAD00>36</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12011_talent_5",
    "source": {
      "type": "weapon",
      "id": "12011",
      "label": "「电磁暴」-贰式｜高压电涌",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12011.json",
      "key": "weapon:12011:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 40
      }
    ],
    "rawDescription": "累积属性异常积蓄值时，装备者的异常精通提升<color=#2BAD00>40</color>点，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12013_talent_1",
    "source": {
      "type": "weapon",
      "id": "12013",
      "label": "「恒等式」-本格｜沉击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12013.json",
      "key": "weapon:12013:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "受到敌方攻击时，装备者的防御力提升<color=#2BAD00>20%</color>，持续8秒。",
    "durationSeconds": 8,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12013_talent_2",
    "source": {
      "type": "weapon",
      "id": "12013",
      "label": "「恒等式」-本格｜沉击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12013.json",
      "key": "weapon:12013:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 23
      }
    ],
    "rawDescription": "受到敌方攻击时，装备者的防御力提升<color=#2BAD00>23%</color>，持续8秒。",
    "durationSeconds": 8,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12013_talent_3",
    "source": {
      "type": "weapon",
      "id": "12013",
      "label": "「恒等式」-本格｜沉击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12013.json",
      "key": "weapon:12013:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 26
      }
    ],
    "rawDescription": "受到敌方攻击时，装备者的防御力提升<color=#2BAD00>26%</color>，持续8秒。",
    "durationSeconds": 8,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12013_talent_4",
    "source": {
      "type": "weapon",
      "id": "12013",
      "label": "「恒等式」-本格｜沉击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12013.json",
      "key": "weapon:12013:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 29
      }
    ],
    "rawDescription": "受到敌方攻击时，装备者的防御力提升<color=#2BAD00>29%</color>，持续8秒。",
    "durationSeconds": 8,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12013_talent_5",
    "source": {
      "type": "weapon",
      "id": "12013",
      "label": "「恒等式」-本格｜沉击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12013.json",
      "key": "weapon:12013:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 32
      }
    ],
    "rawDescription": "受到敌方攻击时，装备者的防御力提升<color=#2BAD00>32%</color>，持续8秒。",
    "durationSeconds": 8,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12015_talent_1",
    "source": {
      "type": "weapon",
      "id": "12015",
      "label": "「灰烬」-钴蓝｜黯火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12015.json",
      "key": "weapon:12015:talent:1"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 7.2
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升<color=#2BAD00>7.2%</color>，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12015_talent_2",
    "source": {
      "type": "weapon",
      "id": "12015",
      "label": "「灰烬」-钴蓝｜黯火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12015.json",
      "key": "weapon:12015:talent:2"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8.2
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升<color=#2BAD00>8.2%</color>，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12015_talent_3",
    "source": {
      "type": "weapon",
      "id": "12015",
      "label": "「灰烬」-钴蓝｜黯火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12015.json",
      "key": "weapon:12015:talent:3"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9.3
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升<color=#2BAD00>9.3%</color>，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12015_talent_4",
    "source": {
      "type": "weapon",
      "id": "12015",
      "label": "「灰烬」-钴蓝｜黯火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12015.json",
      "key": "weapon:12015:talent:4"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10.4
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升<color=#2BAD00>10.4%</color>，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12015_talent_5",
    "source": {
      "type": "weapon",
      "id": "12015",
      "label": "「灰烬」-钴蓝｜黯火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12015.json",
      "key": "weapon:12015:talent:5"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "成为接战状态下的当前操作角色时，装备者的攻击力提升<color=#2BAD00>11.5%</color>，持续10秒，20秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12016_talent_1",
    "source": {
      "type": "weapon",
      "id": "12016",
      "label": "「月相」-弦｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12016.json",
      "key": "weapon:12016:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，[普通攻击]造成的伤害提升<color=#2BAD00>18%</color>，持续10秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12016_talent_2",
    "source": {
      "type": "weapon",
      "id": "12016",
      "label": "「月相」-弦｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12016.json",
      "key": "weapon:12016:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 21,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，[普通攻击]造成的伤害提升<color=#2BAD00>21%</color>，持续10秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12016_talent_3",
    "source": {
      "type": "weapon",
      "id": "12016",
      "label": "「月相」-弦｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12016.json",
      "key": "weapon:12016:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，[普通攻击]造成的伤害提升<color=#2BAD00>24%</color>，持续10秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12016_talent_4",
    "source": {
      "type": "weapon",
      "id": "12016",
      "label": "「月相」-弦｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12016.json",
      "key": "weapon:12016:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 27,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，[普通攻击]造成的伤害提升<color=#2BAD00>27%</color>，持续10秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_12016_talent_5",
    "source": {
      "type": "weapon",
      "id": "12016",
      "label": "「月相」-弦｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/12016.json",
      "key": "weapon:12016:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 30,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，[普通攻击]造成的伤害提升<color=#2BAD00>30%</color>，持续10秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13001_talent_1",
    "source": {
      "type": "weapon",
      "id": "13001",
      "label": "街头巨星｜火热腔调",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13001.json",
      "key": "weapon:13001:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[连携技]</color>时，为装备者提供1层充能效果，最多叠加3层；发动<color=#FFFFFF>[终结技]</color>时，消耗所有充能，每层充能效果使招式造成的伤害提升<color=#2BAD00>15%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13001_talent_2",
    "source": {
      "type": "weapon",
      "id": "13001",
      "label": "街头巨星｜火热腔调",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13001.json",
      "key": "weapon:13001:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.2,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[连携技]</color>时，为装备者提供1层充能效果，最多叠加3层；发动<color=#FFFFFF>[终结技]</color>时，消耗所有充能，每层充能效果使招式造成的伤害提升<color=#2BAD00>17.2%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13001_talent_3",
    "source": {
      "type": "weapon",
      "id": "13001",
      "label": "街头巨星｜火热腔调",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13001.json",
      "key": "weapon:13001:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 19.5,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[连携技]</color>时，为装备者提供1层充能效果，最多叠加3层；发动<color=#FFFFFF>[终结技]</color>时，消耗所有充能，每层充能效果使招式造成的伤害提升<color=#2BAD00>19.5%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13001_talent_4",
    "source": {
      "type": "weapon",
      "id": "13001",
      "label": "街头巨星｜火热腔调",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13001.json",
      "key": "weapon:13001:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 21.7,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[连携技]</color>时，为装备者提供1层充能效果，最多叠加3层；发动<color=#FFFFFF>[终结技]</color>时，消耗所有充能，每层充能效果使招式造成的伤害提升<color=#2BAD00>21.7%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13001_talent_5",
    "source": {
      "type": "weapon",
      "id": "13001",
      "label": "街头巨星｜火热腔调",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13001.json",
      "key": "weapon:13001:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "skillCategories": [
            "chain",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色发动<color=#FFFFFF>[连携技]</color>时，为装备者提供1层充能效果，最多叠加3层；发动<color=#FFFFFF>[终结技]</color>时，消耗所有充能，每层充能效果使招式造成的伤害提升<color=#2BAD00>24%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13003_talent_1",
    "source": {
      "type": "weapon",
      "id": "13003",
      "label": "雨林饕客｜开饭了！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13003.json",
      "key": "weapon:13003:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.5
      }
    ],
    "rawDescription": "每消耗10点能量值，获得1层增益效果，每层增益效果使装备者的攻击力提升<color=#2BAD00>2.5%</color>，最多叠加10层，持续10秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13003_talent_2",
    "source": {
      "type": "weapon",
      "id": "13003",
      "label": "雨林饕客｜开饭了！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13003.json",
      "key": "weapon:13003:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.8
      }
    ],
    "rawDescription": "每消耗10点能量值，获得1层增益效果，每层增益效果使装备者的攻击力提升<color=#2BAD00>2.8%</color>，最多叠加10层，持续10秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13003_talent_3",
    "source": {
      "type": "weapon",
      "id": "13003",
      "label": "雨林饕客｜开饭了！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13003.json",
      "key": "weapon:13003:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.2
      }
    ],
    "rawDescription": "每消耗10点能量值，获得1层增益效果，每层增益效果使装备者的攻击力提升<color=#2BAD00>3.2%</color>，最多叠加10层，持续10秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13003_talent_4",
    "source": {
      "type": "weapon",
      "id": "13003",
      "label": "雨林饕客｜开饭了！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13003.json",
      "key": "weapon:13003:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.6
      }
    ],
    "rawDescription": "每消耗10点能量值，获得1层增益效果，每层增益效果使装备者的攻击力提升<color=#2BAD00>3.6%</color>，最多叠加10层，持续10秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13003_talent_5",
    "source": {
      "type": "weapon",
      "id": "13003",
      "label": "雨林饕客｜开饭了！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13003.json",
      "key": "weapon:13003:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 4
      }
    ],
    "rawDescription": "每消耗10点能量值，获得1层增益效果，每层增益效果使装备者的攻击力提升<color=#2BAD00>4%</color>，最多叠加10层，持续10秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13004_talent_1",
    "source": {
      "type": "weapon",
      "id": "13004",
      "label": "星徽引擎｜骑士连打",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13004.json",
      "key": "weapon:13004:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[快速支援]</color>时，装备者的攻击力提升<color=#2BAD00>12%</color>，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13004_talent_2",
    "source": {
      "type": "weapon",
      "id": "13004",
      "label": "星徽引擎｜骑士连打",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13004.json",
      "key": "weapon:13004:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 13.8
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[快速支援]</color>时，装备者的攻击力提升<color=#2BAD00>13.8%</color>，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13004_talent_3",
    "source": {
      "type": "weapon",
      "id": "13004",
      "label": "星徽引擎｜骑士连打",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13004.json",
      "key": "weapon:13004:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 15.6
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[快速支援]</color>时，装备者的攻击力提升<color=#2BAD00>15.6%</color>，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13004_talent_4",
    "source": {
      "type": "weapon",
      "id": "13004",
      "label": "星徽引擎｜骑士连打",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13004.json",
      "key": "weapon:13004:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 17.4
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[快速支援]</color>时，装备者的攻击力提升<color=#2BAD00>17.4%</color>，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13004_talent_5",
    "source": {
      "type": "weapon",
      "id": "13004",
      "label": "星徽引擎｜骑士连打",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13004.json",
      "key": "weapon:13004:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 19.2
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[快速支援]</color>时，装备者的攻击力提升<color=#2BAD00>19.2%</color>，持续12秒。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13006_talent_1",
    "source": {
      "type": "weapon",
      "id": "13006",
      "label": "贵重骨核｜巨兽猎手",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13006.json",
      "key": "weapon:13006:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "敌方生命值大于等于50%时，装备者对目标造成的失衡值提升<color=#2BAD00>10%</color>，敌方生命值大于等于75%时，该增益效果额外提升<color=#2BAD00>10%</color>。",
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13006_talent_2",
    "source": {
      "type": "weapon",
      "id": "13006",
      "label": "贵重骨核｜巨兽猎手",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13006.json",
      "key": "weapon:13006:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "敌方生命值大于等于50%时，装备者对目标造成的失衡值提升<color=#2BAD00>11.5%</color>，敌方生命值大于等于75%时，该增益效果额外提升<color=#2BAD00>11.5%</color>。",
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13006_talent_3",
    "source": {
      "type": "weapon",
      "id": "13006",
      "label": "贵重骨核｜巨兽猎手",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13006.json",
      "key": "weapon:13006:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 13
      }
    ],
    "rawDescription": "敌方生命值大于等于50%时，装备者对目标造成的失衡值提升<color=#2BAD00>13%</color>，敌方生命值大于等于75%时，该增益效果额外提升<color=#2BAD00>13%</color>。",
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13006_talent_4",
    "source": {
      "type": "weapon",
      "id": "13006",
      "label": "贵重骨核｜巨兽猎手",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13006.json",
      "key": "weapon:13006:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 14.5
      }
    ],
    "rawDescription": "敌方生命值大于等于50%时，装备者对目标造成的失衡值提升<color=#2BAD00>14.5%</color>，敌方生命值大于等于75%时，该增益效果额外提升<color=#2BAD00>14.5%</color>。",
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13006_talent_5",
    "source": {
      "type": "weapon",
      "id": "13006",
      "label": "贵重骨核｜巨兽猎手",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13006.json",
      "key": "weapon:13006:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "敌方生命值大于等于50%时，装备者对目标造成的失衡值提升<color=#2BAD00>16%</color>，敌方生命值大于等于75%时，该增益效果额外提升<color=#2BAD00>16%</color>。",
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13008_talent_1",
    "source": {
      "type": "weapon",
      "id": "13008",
      "label": "双生泣星｜呜咽余波",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13008.json",
      "key": "weapon:13008:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 30
      }
    ],
    "rawDescription": "队伍中任意角色对敌人施加属性异常效果时，为装备者提供1层增益效果，每层增益效果使装备者的异常精通提升<color=#2BAD00>30</color>点，最多叠加4层，目标从失衡状态恢复或死亡时，对应增益效果结束，每层效果单独结算持续时间。",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13008_talent_2",
    "source": {
      "type": "weapon",
      "id": "13008",
      "label": "双生泣星｜呜咽余波",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13008.json",
      "key": "weapon:13008:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 34
      }
    ],
    "rawDescription": "队伍中任意角色对敌人施加属性异常效果时，为装备者提供1层增益效果，每层增益效果使装备者的异常精通提升<color=#2BAD00>34</color>点，最多叠加4层，目标从失衡状态恢复或死亡时，对应增益效果结束，每层效果单独结算持续时间。",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13008_talent_3",
    "source": {
      "type": "weapon",
      "id": "13008",
      "label": "双生泣星｜呜咽余波",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13008.json",
      "key": "weapon:13008:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 38
      }
    ],
    "rawDescription": "队伍中任意角色对敌人施加属性异常效果时，为装备者提供1层增益效果，每层增益效果使装备者的异常精通提升<color=#2BAD00>38</color>点，最多叠加4层，目标从失衡状态恢复或死亡时，对应增益效果结束，每层效果单独结算持续时间。",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13008_talent_4",
    "source": {
      "type": "weapon",
      "id": "13008",
      "label": "双生泣星｜呜咽余波",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13008.json",
      "key": "weapon:13008:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 42
      }
    ],
    "rawDescription": "队伍中任意角色对敌人施加属性异常效果时，为装备者提供1层增益效果，每层增益效果使装备者的异常精通提升<color=#2BAD00>42</color>点，最多叠加4层，目标从失衡状态恢复或死亡时，对应增益效果结束，每层效果单独结算持续时间。",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13008_talent_5",
    "source": {
      "type": "weapon",
      "id": "13008",
      "label": "双生泣星｜呜咽余波",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13008.json",
      "key": "weapon:13008:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 48
      }
    ],
    "rawDescription": "队伍中任意角色对敌人施加属性异常效果时，为装备者提供1层增益效果，每层增益效果使装备者的异常精通提升<color=#2BAD00>48</color>点，最多叠加4层，目标从失衡状态恢复或死亡时，对应增益效果结束，每层效果单独结算持续时间。",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13009_talent_1",
    "source": {
      "type": "weapon",
      "id": "13009",
      "label": "触电唇彩｜致命拥吻",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13009.json",
      "key": "weapon:13009:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升<color=#2BAD00>10%</color>，对目标造成的伤害额外提升<color=#2BAD00>15%</color>。",
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13009_talent_2",
    "source": {
      "type": "weapon",
      "id": "13009",
      "label": "触电唇彩｜致命拥吻",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13009.json",
      "key": "weapon:13009:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.5
      }
    ],
    "rawDescription": "当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升<color=#2BAD00>11.5%</color>，对目标造成的伤害额外提升<color=#2BAD00>17.5%</color>。",
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13009_talent_3",
    "source": {
      "type": "weapon",
      "id": "13009",
      "label": "触电唇彩｜致命拥吻",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13009.json",
      "key": "weapon:13009:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 13
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升<color=#2BAD00>13%</color>，对目标造成的伤害额外提升<color=#2BAD00>20%</color>。",
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13009_talent_4",
    "source": {
      "type": "weapon",
      "id": "13009",
      "label": "触电唇彩｜致命拥吻",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13009.json",
      "key": "weapon:13009:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 14.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 22.5
      }
    ],
    "rawDescription": "当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升<color=#2BAD00>14.5%</color>，对目标造成的伤害额外提升<color=#2BAD00>22.5%</color>。",
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13009_talent_5",
    "source": {
      "type": "weapon",
      "id": "13009",
      "label": "触电唇彩｜致命拥吻",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13009.json",
      "key": "weapon:13009:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 16
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "当场上存在处于属性异常状态下的敌人时，装备者的攻击力提升<color=#2BAD00>16%</color>，对目标造成的伤害额外提升<color=#2BAD00>25%</color>。",
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13010_talent_1",
    "source": {
      "type": "weapon",
      "id": "13010",
      "label": "兔能环｜摸摸兔兔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13010.json",
      "key": "weapon:13010:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "生命值上限提升<color=#2BAD00>8%</color>；拥有护盾时，装备者的攻击力提升<color=#2BAD00>10%</color>。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13010_talent_2",
    "source": {
      "type": "weapon",
      "id": "13010",
      "label": "兔能环｜摸摸兔兔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13010.json",
      "key": "weapon:13010:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "生命值上限提升<color=#2BAD00>9.2%</color>；拥有护盾时，装备者的攻击力提升<color=#2BAD00>11.5%</color>。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13010_talent_3",
    "source": {
      "type": "weapon",
      "id": "13010",
      "label": "兔能环｜摸摸兔兔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13010.json",
      "key": "weapon:13010:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 13
      }
    ],
    "rawDescription": "生命值上限提升<color=#2BAD00>10.4%</color>；拥有护盾时，装备者的攻击力提升<color=#2BAD00>13%</color>。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13010_talent_4",
    "source": {
      "type": "weapon",
      "id": "13010",
      "label": "兔能环｜摸摸兔兔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13010.json",
      "key": "weapon:13010:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 14.5
      }
    ],
    "rawDescription": "生命值上限提升<color=#2BAD00>11.6%</color>；拥有护盾时，装备者的攻击力提升<color=#2BAD00>14.5%</color>。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13010_talent_5",
    "source": {
      "type": "weapon",
      "id": "13010",
      "label": "兔能环｜摸摸兔兔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13010.json",
      "key": "weapon:13010:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "生命值上限提升<color=#2BAD00>12.8%</color>；拥有护盾时，装备者的攻击力提升<color=#2BAD00>16%</color>。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13011_talent_1",
    "source": {
      "type": "weapon",
      "id": "13011",
      "label": "春日融融｜热泉汤",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13011.json",
      "key": "weapon:13011:talent:1"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>7.5%</color>；受到敌方攻击时，装备者的能量获得效率提升<color=#2BAD00>10%</color>，持续12秒；装备者换回后场时，该增益效果将传递给当前操作中的角色，并刷新持续时间，同名被动效果之间不可叠加。",
    "durationSeconds": 12,
    "weaponRefinement": 1,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13011_talent_2",
    "source": {
      "type": "weapon",
      "id": "13011",
      "label": "春日融融｜热泉汤",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13011.json",
      "key": "weapon:13011:talent:2"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>8.5%</color>；受到敌方攻击时，装备者的能量获得效率提升<color=#2BAD00>11.5%</color>，持续12秒；装备者换回后场时，该增益效果将传递给当前操作中的角色，并刷新持续时间，同名被动效果之间不可叠加。",
    "durationSeconds": 12,
    "weaponRefinement": 2,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13011_talent_3",
    "source": {
      "type": "weapon",
      "id": "13011",
      "label": "春日融融｜热泉汤",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13011.json",
      "key": "weapon:13011:talent:3"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 13
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>9.5%</color>；受到敌方攻击时，装备者的能量获得效率提升<color=#2BAD00>13%</color>，持续12秒；装备者换回后场时，该增益效果将传递给当前操作中的角色，并刷新持续时间，同名被动效果之间不可叠加。",
    "durationSeconds": 12,
    "weaponRefinement": 3,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13011_talent_4",
    "source": {
      "type": "weapon",
      "id": "13011",
      "label": "春日融融｜热泉汤",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13011.json",
      "key": "weapon:13011:talent:4"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 14.5
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>10.5%</color>；受到敌方攻击时，装备者的能量获得效率提升<color=#2BAD00>14.5%</color>，持续12秒；装备者换回后场时，该增益效果将传递给当前操作中的角色，并刷新持续时间，同名被动效果之间不可叠加。",
    "durationSeconds": 12,
    "weaponRefinement": 4,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13011_talent_5",
    "source": {
      "type": "weapon",
      "id": "13011",
      "label": "春日融融｜热泉汤",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13011.json",
      "key": "weapon:13011:talent:5"
    },
    "status": "verified",
    "target": "active-character",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 16
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>12%</color>；受到敌方攻击时，装备者的能量获得效率提升<color=#2BAD00>16%</color>，持续12秒；装备者换回后场时，该增益效果将传递给当前操作中的角色，并刷新持续时间，同名被动效果之间不可叠加。",
    "durationSeconds": 12,
    "weaponRefinement": 5,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13012_talent_1",
    "source": {
      "type": "weapon",
      "id": "13012",
      "label": "幻变魔方｜奇机弄巧",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13012.json",
      "key": "weapon:13012:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 16
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，装备者暴击伤害提升<color=#2BAD00>16%</color>，持续12秒；且若目标当前生命值低于最大值的50%时，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>20%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13012_talent_2",
    "source": {
      "type": "weapon",
      "id": "13012",
      "label": "幻变魔方｜奇机弄巧",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13012.json",
      "key": "weapon:13012:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 18.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 23,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，装备者暴击伤害提升<color=#2BAD00>18.4%</color>，持续12秒；且若目标当前生命值低于最大值的50%时，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>23%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13012_talent_3",
    "source": {
      "type": "weapon",
      "id": "13012",
      "label": "幻变魔方｜奇机弄巧",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13012.json",
      "key": "weapon:13012:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 20.8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 26,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，装备者暴击伤害提升<color=#2BAD00>20.8%</color>，持续12秒；且若目标当前生命值低于最大值的50%时，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>26%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13012_talent_4",
    "source": {
      "type": "weapon",
      "id": "13012",
      "label": "幻变魔方｜奇机弄巧",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13012.json",
      "key": "weapon:13012:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 23.2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 29,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，装备者暴击伤害提升<color=#2BAD00>23.2%</color>，持续12秒；且若目标当前生命值低于最大值的50%时，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>29%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13012_talent_5",
    "source": {
      "type": "weapon",
      "id": "13012",
      "label": "幻变魔方｜奇机弄巧",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13012.json",
      "key": "weapon:13012:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 25.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>时，装备者暴击伤害提升<color=#2BAD00>25.6%</color>，持续12秒；且若目标当前生命值低于最大值的50%时，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>32%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13013_talent_1",
    "source": {
      "type": "weapon",
      "id": "13013",
      "label": "鎏金花信｜超规防盗措施",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13013.json",
      "key": "weapon:13013:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>6</color>%，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>15</color>%。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13013_talent_2",
    "source": {
      "type": "weapon",
      "id": "13013",
      "label": "鎏金花信｜超规防盗措施",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13013.json",
      "key": "weapon:13013:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 6.9
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.2,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>6.9</color>%，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>17.2</color>%。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13013_talent_3",
    "source": {
      "type": "weapon",
      "id": "13013",
      "label": "鎏金花信｜超规防盗措施",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13013.json",
      "key": "weapon:13013:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 7.8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 19.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>7.8</color>%，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>19.5</color>%。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13013_talent_4",
    "source": {
      "type": "weapon",
      "id": "13013",
      "label": "鎏金花信｜超规防盗措施",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13013.json",
      "key": "weapon:13013:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8.7
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 21.8,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>8.7</color>%，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>21.8</color>%。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13013_talent_5",
    "source": {
      "type": "weapon",
      "id": "13013",
      "label": "鎏金花信｜超规防盗措施",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13013.json",
      "key": "weapon:13013:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>9.6</color>%，<color=#FFFFFF>[强化特殊技]</color>造成的伤害提升<color=#2BAD00>24</color>%。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13015_talent_1",
    "source": {
      "type": "weapon",
      "id": "13015",
      "label": "强音热望｜躁动全场",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13015.json",
      "key": "weapon:13015:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>6%</color>，持续8秒；目标处于属性异常状态下时，该增益效果额外提升<color=#2BAD00>6%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13015_talent_2",
    "source": {
      "type": "weapon",
      "id": "13015",
      "label": "强音热望｜躁动全场",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13015.json",
      "key": "weapon:13015:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 6.9
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>6.9%</color>，持续8秒；目标处于属性异常状态下时，该增益效果额外提升<color=#2BAD00>6.9%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13015_talent_3",
    "source": {
      "type": "weapon",
      "id": "13015",
      "label": "强音热望｜躁动全场",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13015.json",
      "key": "weapon:13015:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 7.8
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>7.8%</color>，持续8秒；目标处于属性异常状态下时，该增益效果额外提升<color=#2BAD00>7.8%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13015_talent_4",
    "source": {
      "type": "weapon",
      "id": "13015",
      "label": "强音热望｜躁动全场",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13015.json",
      "key": "weapon:13015:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8.7
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>8.7%</color>，持续8秒；目标处于属性异常状态下时，该增益效果额外提升<color=#2BAD00>8.7%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13015_talent_5",
    "source": {
      "type": "weapon",
      "id": "13015",
      "label": "强音热望｜躁动全场",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13015.json",
      "key": "weapon:13015:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9.6
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>9.6%</color>，持续8秒；目标处于属性异常状态下时，该增益效果额外提升<color=#2BAD00>9.6%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13017_talent_1",
    "source": {
      "type": "weapon",
      "id": "13017",
      "label": "喵运当头｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13017.json",
      "key": "weapon:13017:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "防御力提升<color=#2BAD00>6%</color>；释放<color=#FFFFFF>[强化特殊技]</color>时，防御力额外提升<color=#2BAD00>6%</color>，持续15秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13017_talent_2",
    "source": {
      "type": "weapon",
      "id": "13017",
      "label": "喵运当头｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13017.json",
      "key": "weapon:13017:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 7
      }
    ],
    "rawDescription": "防御力提升<color=#2BAD00>7%</color>；释放<color=#FFFFFF>[强化特殊技]</color>时，防御力额外提升<color=#2BAD00>7%</color>，持续15秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13017_talent_3",
    "source": {
      "type": "weapon",
      "id": "13017",
      "label": "喵运当头｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13017.json",
      "key": "weapon:13017:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "防御力提升<color=#2BAD00>8%</color>；释放<color=#FFFFFF>[强化特殊技]</color>时，防御力额外提升<color=#2BAD00>8%</color>，持续15秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13017_talent_4",
    "source": {
      "type": "weapon",
      "id": "13017",
      "label": "喵运当头｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13017.json",
      "key": "weapon:13017:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 9
      }
    ],
    "rawDescription": "防御力提升<color=#2BAD00>9%</color>；释放<color=#FFFFFF>[强化特殊技]</color>时，防御力额外提升<color=#2BAD00>9%</color>，持续15秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13017_talent_5",
    "source": {
      "type": "weapon",
      "id": "13017",
      "label": "喵运当头｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13017.json",
      "key": "weapon:13017:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "defPct",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "防御力提升<color=#2BAD00>10%</color>；释放<color=#FFFFFF>[强化特殊技]</color>时，防御力额外提升<color=#2BAD00>10%</color>，持续15秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13018_talent_1",
    "source": {
      "type": "weapon",
      "id": "13018",
      "label": "咚哒回声｜铿锵鸣鼓",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13018.json",
      "key": "weapon:13018:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[乱流]</color>效果时，为自身回复<color=#2BAD00>2</color>点能量，10秒内最多触发一次；装备者攻击处于属性异常状态下的敌人时，造成的伤害提升<color=#2BAD00>11.5%</color>。",
    "trigger": "skill-used",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13018_talent_2",
    "source": {
      "type": "weapon",
      "id": "13018",
      "label": "咚哒回声｜铿锵鸣鼓",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13018.json",
      "key": "weapon:13018:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13.2
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[乱流]</color>效果时，为自身回复<color=#2BAD00>2.3</color>点能量，10秒内最多触发一次；装备者攻击处于属性异常状态下的敌人时，造成的伤害提升<color=#2BAD00>13.2%</color>。",
    "trigger": "skill-used",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13018_talent_3",
    "source": {
      "type": "weapon",
      "id": "13018",
      "label": "咚哒回声｜铿锵鸣鼓",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13018.json",
      "key": "weapon:13018:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[乱流]</color>效果时，为自身回复<color=#2BAD00>2.6</color>点能量，10秒内最多触发一次；装备者攻击处于属性异常状态下的敌人时，造成的伤害提升<color=#2BAD00>15%</color>。",
    "trigger": "skill-used",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13018_talent_4",
    "source": {
      "type": "weapon",
      "id": "13018",
      "label": "咚哒回声｜铿锵鸣鼓",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13018.json",
      "key": "weapon:13018:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16.7
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[乱流]</color>效果时，为自身回复<color=#2BAD00>2.9</color>点能量，10秒内最多触发一次；装备者攻击处于属性异常状态下的敌人时，造成的伤害提升<color=#2BAD00>16.7%</color>。",
    "trigger": "skill-used",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13018_talent_5",
    "source": {
      "type": "weapon",
      "id": "13018",
      "label": "咚哒回声｜铿锵鸣鼓",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13018.json",
      "key": "weapon:13018:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18.4
      }
    ],
    "rawDescription": "装备者触发<color=#FFFFFF>[乱流]</color>效果时，为自身回复<color=#2BAD00>3.2</color>点能量，10秒内最多触发一次；装备者攻击处于属性异常状态下的敌人时，造成的伤害提升<color=#2BAD00>18.4%</color>。",
    "trigger": "skill-used",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13019_talent_1",
    "source": {
      "type": "weapon",
      "id": "13019",
      "label": "青漪灵鼎｜玄音唤灵",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13019.json",
      "key": "weapon:13019:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 6.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 4,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color> 时可获得1层增益效果，每层增益效果使装备者造成的伤害提升<color=#2BAD00>4%</color>，最多叠加3层，持续20秒，每0.5秒最多触发1次，重复触发时刷新持续时间；拥有3层增益效果时，装备者的暴击率提升<color=#2BAD00>6.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13019_talent_2",
    "source": {
      "type": "weapon",
      "id": "13019",
      "label": "青漪灵鼎｜玄音唤灵",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13019.json",
      "key": "weapon:13019:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 7.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 4.6,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color> 时可获得1层增益效果，每层增益效果使装备者造成的伤害提升<color=#2BAD00>4.6%</color>，最多叠加3层，持续20秒，每0.5秒最多触发1次，重复触发时刷新持续时间；拥有3层增益效果时，装备者的暴击率提升<color=#2BAD00>7.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13019_talent_3",
    "source": {
      "type": "weapon",
      "id": "13019",
      "label": "青漪灵鼎｜玄音唤灵",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13019.json",
      "key": "weapon:13019:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 8.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 5.2,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color> 时可获得1层增益效果，每层增益效果使装备者造成的伤害提升<color=#2BAD00>5.2%</color>，最多叠加3层，持续20秒，每0.5秒最多触发1次，重复触发时刷新持续时间；拥有3层增益效果时，装备者的暴击率提升<color=#2BAD00>8.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13019_talent_4",
    "source": {
      "type": "weapon",
      "id": "13019",
      "label": "青漪灵鼎｜玄音唤灵",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13019.json",
      "key": "weapon:13019:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 9.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 5.8,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color> 时可获得1层增益效果，每层增益效果使装备者造成的伤害提升<color=#2BAD00>5.8%</color>，最多叠加3层，持续20秒，每0.5秒最多触发1次，重复触发时刷新持续时间；拥有3层增益效果时，装备者的暴击率提升<color=#2BAD00>9.4%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13019_talent_5",
    "source": {
      "type": "weapon",
      "id": "13019",
      "label": "青漪灵鼎｜玄音唤灵",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13019.json",
      "key": "weapon:13019:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 10.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 6.4,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者发动<color=#FFFFFF>[强化特殊技]</color> 时可获得1层增益效果，每层增益效果使装备者造成的伤害提升<color=#2BAD00>6.4%</color>，最多叠加3层，持续20秒，每0.5秒最多触发1次，重复触发时刷新持续时间；拥有3层增益效果时，装备者的暴击率提升<color=#2BAD00>10.4%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13020_talent_1",
    "source": {
      "type": "weapon",
      "id": "13020",
      "label": "炎炙沸釜｜红油辣锅",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13020.json",
      "key": "weapon:13020:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 7.2
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 7.2
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[支援突击]</color> 时，装备者对目标造成的失衡值提升<color=#2BAD00>7.2%</color>，装备者造成的伤害提升<color=#2BAD00>7.2%</color>，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13020_talent_2",
    "source": {
      "type": "weapon",
      "id": "13020",
      "label": "炎炙沸釜｜红油辣锅",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13020.json",
      "key": "weapon:13020:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 8.2
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 8.2
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[支援突击]</color> 时，装备者对目标造成的失衡值提升<color=#2BAD00>8.2%</color>，装备者造成的伤害提升<color=#2BAD00>8.2%</color>，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13020_talent_3",
    "source": {
      "type": "weapon",
      "id": "13020",
      "label": "炎炙沸釜｜红油辣锅",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13020.json",
      "key": "weapon:13020:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 9.2
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 9.2
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[支援突击]</color> 时，装备者对目标造成的失衡值提升<color=#2BAD00>9.2%</color>，装备者造成的伤害提升<color=#2BAD00>9.2%</color>，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13020_talent_4",
    "source": {
      "type": "weapon",
      "id": "13020",
      "label": "炎炙沸釜｜红油辣锅",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13020.json",
      "key": "weapon:13020:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10.2
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10.2
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[支援突击]</color> 时，装备者对目标造成的失衡值提升<color=#2BAD00>10.2%</color>，装备者造成的伤害提升<color=#2BAD00>10.2%</color>，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13020_talent_5",
    "source": {
      "type": "weapon",
      "id": "13020",
      "label": "炎炙沸釜｜红油辣锅",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13020.json",
      "key": "weapon:13020:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11.5
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[支援突击]</color> 时，装备者对目标造成的失衡值提升<color=#2BAD00>11.5%</color>，装备者造成的伤害提升<color=#2BAD00>11.5%</color>，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13021_talent_1",
    "source": {
      "type": "weapon",
      "id": "13021",
      "label": "血髓秘匣｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13021.json",
      "key": "weapon:13021:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 0.4
      }
    ],
    "rawDescription": "装备者暴击率大于<color=#2BAD00>100%</color>时，每超出1%暴击率，使装备者造成的伤害提升<color=#2BAD00>0.4%</color>，至多提升<color=#2BAD00>20%</color>。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13021_talent_2",
    "source": {
      "type": "weapon",
      "id": "13021",
      "label": "血髓秘匣｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13021.json",
      "key": "weapon:13021:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 0.46
      }
    ],
    "rawDescription": "装备者暴击率大于<color=#2BAD00>100%</color>时，每超出1%暴击率，使装备者造成的伤害提升<color=#2BAD00>0.46%</color>，至多提升<color=#2BAD00>23%</color>。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13021_talent_3",
    "source": {
      "type": "weapon",
      "id": "13021",
      "label": "血髓秘匣｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13021.json",
      "key": "weapon:13021:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 0.52
      }
    ],
    "rawDescription": "装备者暴击率大于<color=#2BAD00>100%</color>时，每超出1%暴击率，使装备者造成的伤害提升<color=#2BAD00>0.52%</color>，至多提升<color=#2BAD00>26%</color>。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13021_talent_4",
    "source": {
      "type": "weapon",
      "id": "13021",
      "label": "血髓秘匣｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13021.json",
      "key": "weapon:13021:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 0.58
      }
    ],
    "rawDescription": "装备者暴击率大于<color=#2BAD00>100%</color>时，每超出1%暴击率，使装备者造成的伤害提升<color=#2BAD00>0.58%</color>，至多提升<color=#2BAD00>29%</color>。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13021_talent_5",
    "source": {
      "type": "weapon",
      "id": "13021",
      "label": "血髓秘匣｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13021.json",
      "key": "weapon:13021:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 0.64
      }
    ],
    "rawDescription": "装备者暴击率大于<color=#2BAD00>100%</color>时，每超出1%暴击率，使装备者造成的伤害提升<color=#2BAD00>0.64%</color>，至多提升<color=#2BAD00>32%</color>。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13101_talent_1",
    "source": {
      "type": "weapon",
      "id": "13101",
      "label": "德玛拉电池Ⅱ型｜电光石火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13101.json",
      "key": "weapon:13101:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 18
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>15%</color>；<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者的能量获得效率提升<color=#2BAD00>18%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13101_talent_2",
    "source": {
      "type": "weapon",
      "id": "13101",
      "label": "德玛拉电池Ⅱ型｜电光石火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13101.json",
      "key": "weapon:13101:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 20.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 17.5
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>17.5%</color>；<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者的能量获得效率提升<color=#2BAD00>20.5%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13101_talent_3",
    "source": {
      "type": "weapon",
      "id": "13101",
      "label": "德玛拉电池Ⅱ型｜电光石火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13101.json",
      "key": "weapon:13101:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>20%</color>；<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者的能量获得效率提升<color=#2BAD00>23%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13101_talent_4",
    "source": {
      "type": "weapon",
      "id": "13101",
      "label": "德玛拉电池Ⅱ型｜电光石火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13101.json",
      "key": "weapon:13101:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 25
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 22
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>22%</color>；<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者的能量获得效率提升<color=#2BAD00>25%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13101_talent_5",
    "source": {
      "type": "weapon",
      "id": "13101",
      "label": "德玛拉电池Ⅱ型｜电光石火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13101.json",
      "key": "weapon:13101:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-percent",
        "value": 27.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 24
      }
    ],
    "rawDescription": "<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>24%</color>；<color=#FFFFFF>[闪避反击]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者的能量获得效率提升<color=#2BAD00>27.5%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13103_talent_1",
    "source": {
      "type": "weapon",
      "id": "13103",
      "label": "聚宝箱｜财迷心窍",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13103.json",
      "key": "weapon:13103:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#FE437E>以太伤害</color>时，所有单位对目标造成的伤害提升<color=#2BAD00>15%</color>，装备者的能量自动回复提升<color=#2BAD00>0.5</color>点/秒，持续2秒，同名被动效果之间不可叠加。",
    "durationSeconds": 2,
    "weaponRefinement": 1,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13103_talent_2",
    "source": {
      "type": "weapon",
      "id": "13103",
      "label": "聚宝箱｜财迷心窍",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13103.json",
      "key": "weapon:13103:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.58
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.5,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#FE437E>以太伤害</color>时，所有单位对目标造成的伤害提升<color=#2BAD00>17.5%</color>，装备者的能量自动回复提升<color=#2BAD00>0.58</color>点/秒，持续2秒，同名被动效果之间不可叠加。",
    "durationSeconds": 2,
    "weaponRefinement": 2,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13103_talent_3",
    "source": {
      "type": "weapon",
      "id": "13103",
      "label": "聚宝箱｜财迷心窍",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13103.json",
      "key": "weapon:13103:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.65
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#FE437E>以太伤害</color>时，所有单位对目标造成的伤害提升<color=#2BAD00>20%</color>，装备者的能量自动回复提升<color=#2BAD00>0.65</color>点/秒，持续2秒，同名被动效果之间不可叠加。",
    "durationSeconds": 2,
    "weaponRefinement": 3,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13103_talent_4",
    "source": {
      "type": "weapon",
      "id": "13103",
      "label": "聚宝箱｜财迷心窍",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13103.json",
      "key": "weapon:13103:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.72
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 22,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#FE437E>以太伤害</color>时，所有单位对目标造成的伤害提升<color=#2BAD00>22%</color>，装备者的能量自动回复提升<color=#2BAD00>0.72</color>点/秒，持续2秒，同名被动效果之间不可叠加。",
    "durationSeconds": 2,
    "weaponRefinement": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13103_talent_5",
    "source": {
      "type": "weapon",
      "id": "13103",
      "label": "聚宝箱｜财迷心窍",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13103.json",
      "key": "weapon:13103:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#FE437E>以太伤害</color>时，所有单位对目标造成的伤害提升<color=#2BAD00>24%</color>，装备者的能量自动回复提升<color=#2BAD00>0.8</color>点/秒，持续2秒，同名被动效果之间不可叠加。",
    "durationSeconds": 2,
    "weaponRefinement": 5,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13106_talent_1",
    "source": {
      "type": "weapon",
      "id": "13106",
      "label": "家政员｜安心家用轮锯",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13106.json",
      "key": "weapon:13106:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.45
      },
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 3
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.45</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>命中敌人时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>3%</color>，最多叠加15层，持续1秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 1,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 15,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13106_talent_2",
    "source": {
      "type": "weapon",
      "id": "13106",
      "label": "家政员｜安心家用轮锯",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13106.json",
      "key": "weapon:13106:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.52
      },
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 3.5
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.52</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>命中敌人时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>3.5%</color>，最多叠加15层，持续1秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 1,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 15,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13106_talent_3",
    "source": {
      "type": "weapon",
      "id": "13106",
      "label": "家政员｜安心家用轮锯",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13106.json",
      "key": "weapon:13106:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.58
      },
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 4
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.58</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>命中敌人时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>4%</color>，最多叠加15层，持续1秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 1,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 15,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13106_talent_4",
    "source": {
      "type": "weapon",
      "id": "13106",
      "label": "家政员｜安心家用轮锯",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13106.json",
      "key": "weapon:13106:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.65
      },
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 4.4
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.65</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>命中敌人时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>4.4%</color>，最多叠加15层，持续1秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 1,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 15,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13106_talent_5",
    "source": {
      "type": "weapon",
      "id": "13106",
      "label": "家政员｜安心家用轮锯",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13106.json",
      "key": "weapon:13106:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.72
      },
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 4.8
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.72</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>命中敌人时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>4.8%</color>，最多叠加15层，持续1秒，重复触发时刷新持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 1,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 15,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13108_talent_1",
    "source": {
      "type": "weapon",
      "id": "13108",
      "label": "仿制星徽引擎｜骑士光波：改",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13108.json",
      "key": "weapon:13108:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 36
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中6米外的敌人时，装备者对目标造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>36%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13108_talent_2",
    "source": {
      "type": "weapon",
      "id": "13108",
      "label": "仿制星徽引擎｜骑士光波：改",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13108.json",
      "key": "weapon:13108:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 41
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中6米外的敌人时，装备者对目标造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>41%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13108_talent_3",
    "source": {
      "type": "weapon",
      "id": "13108",
      "label": "仿制星徽引擎｜骑士光波：改",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13108.json",
      "key": "weapon:13108:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 46.5
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中6米外的敌人时，装备者对目标造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>46.5%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13108_talent_4",
    "source": {
      "type": "weapon",
      "id": "13108",
      "label": "仿制星徽引擎｜骑士光波：改",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13108.json",
      "key": "weapon:13108:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 52
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中6米外的敌人时，装备者对目标造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>52%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13108_talent_5",
    "source": {
      "type": "weapon",
      "id": "13108",
      "label": "仿制星徽引擎｜骑士光波：改",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13108.json",
      "key": "weapon:13108:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 57.5
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>命中6米外的敌人时，装备者对目标造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>57.5%</color>，持续8秒。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13111_talent_1",
    "source": {
      "type": "weapon",
      "id": "13111",
      "label": "旋钻机-赤轴｜红莲电机",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13111.json",
      "key": "weapon:13111:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 50
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>50%</color>，持续10秒，15秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13111_talent_2",
    "source": {
      "type": "weapon",
      "id": "13111",
      "label": "旋钻机-赤轴｜红莲电机",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13111.json",
      "key": "weapon:13111:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 57.5
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>57.5%</color>，持续10秒，15秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13111_talent_3",
    "source": {
      "type": "weapon",
      "id": "13111",
      "label": "旋钻机-赤轴｜红莲电机",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13111.json",
      "key": "weapon:13111:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 65
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>65%</color>，持续10秒，15秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13111_talent_4",
    "source": {
      "type": "weapon",
      "id": "13111",
      "label": "旋钻机-赤轴｜红莲电机",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13111.json",
      "key": "weapon:13111:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 72.5
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>72.5%</color>，持续10秒，15秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13111_talent_5",
    "source": {
      "type": "weapon",
      "id": "13111",
      "label": "旋钻机-赤轴｜红莲电机",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13111.json",
      "key": "weapon:13111:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 80
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[连携技]</color>时，<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>80%</color>，持续10秒，15秒内最多触发一次。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13112_talent_1",
    "source": {
      "type": "weapon",
      "id": "13112",
      "label": "比格气缸｜万斤顶",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13112.json",
      "key": "weapon:13112:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.def",
          "scale": 6
        }
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>7.5%</color>；受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者<color=#2BAD00>600%</color>防御力的伤害，且必定触发暴击，7.5秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 1,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13112_talent_2",
    "source": {
      "type": "weapon",
      "id": "13112",
      "label": "比格气缸｜万斤顶",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13112.json",
      "key": "weapon:13112:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.def",
          "scale": 6.9
        }
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>8.5%</color>；受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者<color=#2BAD00>690%</color>防御力的伤害，且必定触发暴击，7.5秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 2,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13112_talent_3",
    "source": {
      "type": "weapon",
      "id": "13112",
      "label": "比格气缸｜万斤顶",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13112.json",
      "key": "weapon:13112:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.def",
          "scale": 7.8
        }
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>9.5%</color>；受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者<color=#2BAD00>780%</color>防御力的伤害，且必定触发暴击，7.5秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 3,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13112_talent_4",
    "source": {
      "type": "weapon",
      "id": "13112",
      "label": "比格气缸｜万斤顶",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13112.json",
      "key": "weapon:13112:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.def",
          "scale": 8.7
        }
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>10.5%</color>；受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者<color=#2BAD00>870%</color>防御力的伤害，且必定触发暴击，7.5秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 4,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13112_talent_5",
    "source": {
      "type": "weapon",
      "id": "13112",
      "label": "比格气缸｜万斤顶",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13112.json",
      "key": "weapon:13112:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.def",
          "scale": 9.6
        }
      }
    ],
    "rawDescription": "受到的伤害降低<color=#2BAD00>12%</color>；受到敌方攻击后，下一次攻击命中敌人时，额外造成装备者<color=#2BAD00>960%</color>防御力的伤害，且必定触发暴击，7.5秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 5,
    "notes": "涉及减伤或护盾量倍率，当前模型没有对应的通用效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13113_talent_1",
    "source": {
      "type": "weapon",
      "id": "13113",
      "label": "含羞恶面｜饕餮相",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13113.json",
      "key": "weapon:13113:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>15%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，全队角色攻击力提升<color=#2BAD00>2%</color>，最多叠加4层，持续12秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13113_talent_2",
    "source": {
      "type": "weapon",
      "id": "13113",
      "label": "含羞恶面｜饕餮相",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13113.json",
      "key": "weapon:13113:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.3
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 17.5
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>17.5%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，全队角色攻击力提升<color=#2BAD00>2.3%</color>，最多叠加4层，持续12秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13113_talent_3",
    "source": {
      "type": "weapon",
      "id": "13113",
      "label": "含羞恶面｜饕餮相",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13113.json",
      "key": "weapon:13113:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.6
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>20%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，全队角色攻击力提升<color=#2BAD00>2.6%</color>，最多叠加4层，持续12秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13113_talent_4",
    "source": {
      "type": "weapon",
      "id": "13113",
      "label": "含羞恶面｜饕餮相",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13113.json",
      "key": "weapon:13113:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.9
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 22
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>22%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，全队角色攻击力提升<color=#2BAD00>2.9%</color>，最多叠加4层，持续12秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13113_talent_5",
    "source": {
      "type": "weapon",
      "id": "13113",
      "label": "含羞恶面｜饕餮相",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13113.json",
      "key": "weapon:13113:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.2
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 24
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>24%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，全队角色攻击力提升<color=#2BAD00>3.2%</color>，最多叠加4层，持续12秒，重复触发时刷新持续时间，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 12,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13115_talent_1",
    "source": {
      "type": "weapon",
      "id": "13115",
      "label": "好斗的阿炮｜踩踏事故",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13115.json",
      "key": "weapon:13115:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.5
      }
    ],
    "rawDescription": "队伍中任意友方单位攻击命中敌人时，队伍中所有友方单位的攻击力提升<color=#2BAD00>2.5%</color>，最多叠加4层，持续8秒，每层效果单独结算持续时间，每名友方单位最多提供1层增益效果，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13115_talent_2",
    "source": {
      "type": "weapon",
      "id": "13115",
      "label": "好斗的阿炮｜踩踏事故",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13115.json",
      "key": "weapon:13115:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 2.8
      }
    ],
    "rawDescription": "队伍中任意友方单位攻击命中敌人时，队伍中所有友方单位的攻击力提升<color=#2BAD00>2.8%</color>，最多叠加4层，持续8秒，每层效果单独结算持续时间，每名友方单位最多提供1层增益效果，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13115_talent_3",
    "source": {
      "type": "weapon",
      "id": "13115",
      "label": "好斗的阿炮｜踩踏事故",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13115.json",
      "key": "weapon:13115:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.2
      }
    ],
    "rawDescription": "队伍中任意友方单位攻击命中敌人时，队伍中所有友方单位的攻击力提升<color=#2BAD00>3.2%</color>，最多叠加4层，持续8秒，每层效果单独结算持续时间，每名友方单位最多提供1层增益效果，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13115_talent_4",
    "source": {
      "type": "weapon",
      "id": "13115",
      "label": "好斗的阿炮｜踩踏事故",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13115.json",
      "key": "weapon:13115:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.6
      }
    ],
    "rawDescription": "队伍中任意友方单位攻击命中敌人时，队伍中所有友方单位的攻击力提升<color=#2BAD00>3.6%</color>，最多叠加4层，持续8秒，每层效果单独结算持续时间，每名友方单位最多提供1层增益效果，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13115_talent_5",
    "source": {
      "type": "weapon",
      "id": "13115",
      "label": "好斗的阿炮｜踩踏事故",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13115.json",
      "key": "weapon:13115:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 4
      }
    ],
    "rawDescription": "队伍中任意友方单位攻击命中敌人时，队伍中所有友方单位的攻击力提升<color=#2BAD00>4%</color>，最多叠加4层，持续8秒，每层效果单独结算持续时间，每名友方单位最多提供1层增益效果，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 4,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13128_talent_1",
    "source": {
      "type": "weapon",
      "id": "13128",
      "label": "轰鸣座驾｜碰撞势能",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13128.json",
      "key": "weapon:13128:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 40
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>命中敌人时，随机触发以下三种效果中的一种，持续5秒，0.3秒内最多触发一次，同类效果不可叠加，重复触发时刷新持续时间，多个效果可以同时存在：装备者的攻击力提升<color=#2BAD00>8%</color>；装备者的异常精通提升<color=#2BAD00>40</color>点；装备者的属性异常积蓄效率提升<color=#2BAD00>25%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "weaponRefinement": 1,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13128_talent_2",
    "source": {
      "type": "weapon",
      "id": "13128",
      "label": "轰鸣座驾｜碰撞势能",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13128.json",
      "key": "weapon:13128:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9.2
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 46
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>命中敌人时，随机触发以下三种效果中的一种，持续5秒，0.3秒内最多触发一次，同类效果不可叠加，重复触发时刷新持续时间，多个效果可以同时存在：装备者的攻击力提升<color=#2BAD00>9.2%</color>；装备者的异常精通提升<color=#2BAD00>46</color>点；装备者的属性异常积蓄效率提升<color=#2BAD00>28%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "weaponRefinement": 2,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13128_talent_3",
    "source": {
      "type": "weapon",
      "id": "13128",
      "label": "轰鸣座驾｜碰撞势能",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13128.json",
      "key": "weapon:13128:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10.4
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 52
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>命中敌人时，随机触发以下三种效果中的一种，持续5秒，0.3秒内最多触发一次，同类效果不可叠加，重复触发时刷新持续时间，多个效果可以同时存在：装备者的攻击力提升<color=#2BAD00>10.4%</color>；装备者的异常精通提升<color=#2BAD00>52</color>点；装备者的属性异常积蓄效率提升<color=#2BAD00>32%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "weaponRefinement": 3,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13128_talent_4",
    "source": {
      "type": "weapon",
      "id": "13128",
      "label": "轰鸣座驾｜碰撞势能",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13128.json",
      "key": "weapon:13128:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11.6
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 58
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>命中敌人时，随机触发以下三种效果中的一种，持续5秒，0.3秒内最多触发一次，同类效果不可叠加，重复触发时刷新持续时间，多个效果可以同时存在：装备者的攻击力提升<color=#2BAD00>11.6%</color>；装备者的异常精通提升<color=#2BAD00>58</color>点；装备者的属性异常积蓄效率提升<color=#2BAD00>36%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "weaponRefinement": 4,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13128_talent_5",
    "source": {
      "type": "weapon",
      "id": "13128",
      "label": "轰鸣座驾｜碰撞势能",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13128.json",
      "key": "weapon:13128:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 12.8
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 64
      }
    ],
    "rawDescription": "<color=#FFFFFF>[强化特殊技]</color>命中敌人时，随机触发以下三种效果中的一种，持续5秒，0.3秒内最多触发一次，同类效果不可叠加，重复触发时刷新持续时间，多个效果可以同时存在：装备者的攻击力提升<color=#2BAD00>12.8%</color>；装备者的异常精通提升<color=#2BAD00>64</color>点；装备者的属性异常积蓄效率提升<color=#2BAD00>40%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "weaponRefinement": 5,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13135_talent_1",
    "source": {
      "type": "weapon",
      "id": "13135",
      "label": "裁纸刀｜小心手指",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13135.json",
      "key": "weapon:13135:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[追加攻击]</color>时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>15%</color>，造成的失衡值提升<color=#2BAD00>10%</color>，持续10秒。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13135_talent_2",
    "source": {
      "type": "weapon",
      "id": "13135",
      "label": "裁纸刀｜小心手指",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13135.json",
      "key": "weapon:13135:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 17.3
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[追加攻击]</color>时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>17.3%</color>，造成的失衡值提升<color=#2BAD00>11.5%</color>，持续10秒。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13135_talent_3",
    "source": {
      "type": "weapon",
      "id": "13135",
      "label": "裁纸刀｜小心手指",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13135.json",
      "key": "weapon:13135:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 19.5
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[追加攻击]</color>时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>19.5%</color>，造成的失衡值提升<color=#2BAD00>13%</color>，持续10秒。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13135_talent_4",
    "source": {
      "type": "weapon",
      "id": "13135",
      "label": "裁纸刀｜小心手指",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13135.json",
      "key": "weapon:13135:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 21.8
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[追加攻击]</color>时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>21.8%</color>，造成的失衡值提升<color=#2BAD00>14.5%</color>，持续10秒。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13135_talent_5",
    "source": {
      "type": "weapon",
      "id": "13135",
      "label": "裁纸刀｜小心手指",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13135.json",
      "key": "weapon:13135:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 24
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[追加攻击]</color>时，装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>24%</color>，造成的失衡值提升<color=#2BAD00>16%</color>，持续10秒。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13142_talent_1",
    "source": {
      "type": "weapon",
      "id": "13142",
      "label": "震元奇枢｜寻经定络",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13142.json",
      "key": "weapon:13142:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[终结技]</color>造成的伤害增加<color=#2BAD00>25%</color>；队伍中任意角色受到伤害或回复生命时，为装备者回复<color=#2BAD00>2</color>点能量，5秒内最多触发一次；",
    "trigger": "skill-used",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13142_talent_2",
    "source": {
      "type": "weapon",
      "id": "13142",
      "label": "震元奇枢｜寻经定络",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13142.json",
      "key": "weapon:13142:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 28.7,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[终结技]</color>造成的伤害增加<color=#2BAD00>28.7%</color>；队伍中任意角色受到伤害或回复生命时，为装备者回复<color=#2BAD00>2.3</color>点能量，5秒内最多触发一次；",
    "trigger": "skill-used",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13142_talent_3",
    "source": {
      "type": "weapon",
      "id": "13142",
      "label": "震元奇枢｜寻经定络",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13142.json",
      "key": "weapon:13142:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32.5,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[终结技]</color>造成的伤害增加<color=#2BAD00>32.5%</color>；队伍中任意角色受到伤害或回复生命时，为装备者回复<color=#2BAD00>2.6</color>点能量，5秒内最多触发一次；",
    "trigger": "skill-used",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13142_talent_4",
    "source": {
      "type": "weapon",
      "id": "13142",
      "label": "震元奇枢｜寻经定络",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13142.json",
      "key": "weapon:13142:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 36.2,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[终结技]</color>造成的伤害增加<color=#2BAD00>36.2%</color>；队伍中任意角色受到伤害或回复生命时，为装备者回复<color=#2BAD00>2.9</color>点能量，5秒内最多触发一次；",
    "trigger": "skill-used",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13142_talent_5",
    "source": {
      "type": "weapon",
      "id": "13142",
      "label": "震元奇枢｜寻经定络",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13142.json",
      "key": "weapon:13142:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>和<color=#FFFFFF>[终结技]</color>造成的伤害增加<color=#2BAD00>40%</color>；队伍中任意角色受到伤害或回复生命时，为装备者回复<color=#2BAD00>3.2</color>点能量，5秒内最多触发一次；",
    "trigger": "skill-used",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13144_talent_1",
    "source": {
      "type": "weapon",
      "id": "13144",
      "label": "燔火胧夜｜笼中火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13144.json",
      "key": "weapon:13144:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者造成的<color=#FF5521>火属性伤害</color>提升<color=#2BAD00>15%</color>；装备者的生命值降低时，暴击率提升<color=#2BAD00>15%</color>，持续5秒。",
    "durationSeconds": 5,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13144_talent_2",
    "source": {
      "type": "weapon",
      "id": "13144",
      "label": "燔火胧夜｜笼中火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13144.json",
      "key": "weapon:13144:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 17.25
      },
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 17.25
      }
    ],
    "rawDescription": "装备者造成的<color=#FF5521>火属性伤害</color>提升<color=#2BAD00>17.25%</color>；装备者的生命值降低时，暴击率提升<color=#2BAD00>17.25%</color>，持续5秒。",
    "durationSeconds": 5,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13144_talent_3",
    "source": {
      "type": "weapon",
      "id": "13144",
      "label": "燔火胧夜｜笼中火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13144.json",
      "key": "weapon:13144:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 19.5
      },
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 19.5
      }
    ],
    "rawDescription": "装备者造成的<color=#FF5521>火属性伤害</color>提升<color=#2BAD00>19.5%</color>；装备者的生命值降低时，暴击率提升<color=#2BAD00>19.5%</color>，持续5秒。",
    "durationSeconds": 5,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13144_talent_4",
    "source": {
      "type": "weapon",
      "id": "13144",
      "label": "燔火胧夜｜笼中火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13144.json",
      "key": "weapon:13144:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 21.75
      },
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 21.75
      }
    ],
    "rawDescription": "装备者造成的<color=#FF5521>火属性伤害</color>提升<color=#2BAD00>21.75%</color>；装备者的生命值降低时，暴击率提升<color=#2BAD00>21.75%</color>，持续5秒。",
    "durationSeconds": 5,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_13144_talent_5",
    "source": {
      "type": "weapon",
      "id": "13144",
      "label": "燔火胧夜｜笼中火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/13144.json",
      "key": "weapon:13144:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 24
      },
      {
        "kind": "stat",
        "stat": "fireDmgBonus",
        "operation": "add-percent",
        "value": 24
      }
    ],
    "rawDescription": "装备者造成的<color=#FF5521>火属性伤害</color>提升<color=#2BAD00>24%</color>；装备者的生命值降低时，暴击率提升<color=#2BAD00>24%</color>，持续5秒。",
    "durationSeconds": 5,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14001_talent_1",
    "source": {
      "type": "weapon",
      "id": "14001",
      "label": "加农转子｜口径超规",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14001.json",
      "key": "weapon:14001:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 7.5
      },
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.atk",
          "scale": 2
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>7.5%</color>；攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害，<color=#2BAD00>8</color>秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14001_talent_2",
    "source": {
      "type": "weapon",
      "id": "14001",
      "label": "加农转子｜口径超规",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14001.json",
      "key": "weapon:14001:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 8.6
      },
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.atk",
          "scale": 2
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>8.6%</color>；攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害，<color=#2BAD00>7.5</color>秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14001_talent_3",
    "source": {
      "type": "weapon",
      "id": "14001",
      "label": "加农转子｜口径超规",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14001.json",
      "key": "weapon:14001:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 9.7
      },
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.atk",
          "scale": 2
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>9.7%</color>；攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害，<color=#2BAD00>7</color>秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14001_talent_4",
    "source": {
      "type": "weapon",
      "id": "14001",
      "label": "加农转子｜口径超规",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14001.json",
      "key": "weapon:14001:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10.8
      },
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.atk",
          "scale": 2
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>10.8%</color>；攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害，<color=#2BAD00>6.5</color>秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14001_talent_5",
    "source": {
      "type": "weapon",
      "id": "14001",
      "label": "加农转子｜口径超规",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14001.json",
      "key": "weapon:14001:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 12
      },
      {
        "kind": "damage-instance",
        "operation": "add",
        "damageKind": "direct",
        "value": {
          "type": "source-stat",
          "path": "self.atk",
          "scale": 2
        }
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>12%</color>；攻击命中敌人并触发暴击时，额外造成200%攻击力的伤害，<color=#2BAD00>6</color>秒内最多触发一次。",
    "trigger": "attack-hit",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14002_talent_1",
    "source": {
      "type": "weapon",
      "id": "14002",
      "label": "逍遥游球｜电玩，启动！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14002.json",
      "key": "weapon:14002:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "装备者攻击命中敌人时，若触发属性克制效果，则所有单位对该目标的暴击率提升<color=#2BAD00>12%</color>，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 12,
    "weaponRefinement": 1,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14002_talent_2",
    "source": {
      "type": "weapon",
      "id": "14002",
      "label": "逍遥游球｜电玩，启动！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14002.json",
      "key": "weapon:14002:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 13.5
      }
    ],
    "rawDescription": "装备者攻击命中敌人时，若触发属性克制效果，则所有单位对该目标的暴击率提升<color=#2BAD00>13.5%</color>，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 12,
    "weaponRefinement": 2,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14002_talent_3",
    "source": {
      "type": "weapon",
      "id": "14002",
      "label": "逍遥游球｜电玩，启动！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14002.json",
      "key": "weapon:14002:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 15.5
      }
    ],
    "rawDescription": "装备者攻击命中敌人时，若触发属性克制效果，则所有单位对该目标的暴击率提升<color=#2BAD00>15.5%</color>，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 12,
    "weaponRefinement": 3,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14002_talent_4",
    "source": {
      "type": "weapon",
      "id": "14002",
      "label": "逍遥游球｜电玩，启动！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14002.json",
      "key": "weapon:14002:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 17.5
      }
    ],
    "rawDescription": "装备者攻击命中敌人时，若触发属性克制效果，则所有单位对该目标的暴击率提升<color=#2BAD00>17.5%</color>，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 12,
    "weaponRefinement": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14002_talent_5",
    "source": {
      "type": "weapon",
      "id": "14002",
      "label": "逍遥游球｜电玩，启动！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14002.json",
      "key": "weapon:14002:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "装备者攻击命中敌人时，若触发属性克制效果，则所有单位对该目标的暴击率提升<color=#2BAD00>20%</color>，持续12秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 12,
    "weaponRefinement": 5,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14003_talent_1",
    "source": {
      "type": "weapon",
      "id": "14003",
      "label": "左轮转子｜开火！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14003.json",
      "key": "weapon:14003:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 4,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "每3秒为装备者提供1层充能效果，最多叠加6层；发动<color=#FFFFFF>[强化特殊技]</color>时，消耗所有充能，每层充能效果使招式造成的失衡值提升<color=#2BAD00>4%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14003_talent_2",
    "source": {
      "type": "weapon",
      "id": "14003",
      "label": "左轮转子｜开火！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14003.json",
      "key": "weapon:14003:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 4.6,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "每3秒为装备者提供1层充能效果，最多叠加6层；发动<color=#FFFFFF>[强化特殊技]</color>时，消耗所有充能，每层充能效果使招式造成的失衡值提升<color=#2BAD00>4.6%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14003_talent_3",
    "source": {
      "type": "weapon",
      "id": "14003",
      "label": "左轮转子｜开火！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14003.json",
      "key": "weapon:14003:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 5.2,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "每3秒为装备者提供1层充能效果，最多叠加6层；发动<color=#FFFFFF>[强化特殊技]</color>时，消耗所有充能，每层充能效果使招式造成的失衡值提升<color=#2BAD00>5.2%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14003_talent_4",
    "source": {
      "type": "weapon",
      "id": "14003",
      "label": "左轮转子｜开火！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14003.json",
      "key": "weapon:14003:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 5.8,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "每3秒为装备者提供1层充能效果，最多叠加6层；发动<color=#FFFFFF>[强化特殊技]</color>时，消耗所有充能，每层充能效果使招式造成的失衡值提升<color=#2BAD00>5.8%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14003_talent_5",
    "source": {
      "type": "weapon",
      "id": "14003",
      "label": "左轮转子｜开火！",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14003.json",
      "key": "weapon:14003:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 6.4,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "每3秒为装备者提供1层充能效果，最多叠加6层；发动<color=#FFFFFF>[强化特殊技]</color>时，消耗所有充能，每层充能效果使招式造成的失衡值提升<color=#2BAD00>6.4%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14102_talent_1",
    "source": {
      "type": "weapon",
      "id": "14102",
      "label": "钢铁肉垫｜合金猫爪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14102.json",
      "key": "weapon:14102:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>20%</color>；从背后攻击命中敌人时，装备者造成的伤害提升<color=#2BAD00>25%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14102_talent_2",
    "source": {
      "type": "weapon",
      "id": "14102",
      "label": "钢铁肉垫｜合金猫爪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14102.json",
      "key": "weapon:14102:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 25
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 31.5,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>25%</color>；从背后攻击命中敌人时，装备者造成的伤害提升<color=#2BAD00>31.5%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14102_talent_3",
    "source": {
      "type": "weapon",
      "id": "14102",
      "label": "钢铁肉垫｜合金猫爪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14102.json",
      "key": "weapon:14102:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 30
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 38,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>30%</color>；从背后攻击命中敌人时，装备者造成的伤害提升<color=#2BAD00>38%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14102_talent_4",
    "source": {
      "type": "weapon",
      "id": "14102",
      "label": "钢铁肉垫｜合金猫爪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14102.json",
      "key": "weapon:14102:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 35
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 44,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>35%</color>；从背后攻击命中敌人时，装备者造成的伤害提升<color=#2BAD00>44%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14102_talent_5",
    "source": {
      "type": "weapon",
      "id": "14102",
      "label": "钢铁肉垫｜合金猫爪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14102.json",
      "key": "weapon:14102:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 50,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>40%</color>；从背后攻击命中敌人时，装备者造成的伤害提升<color=#2BAD00>50%</color>。",
    "trigger": "attack-hit",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14104_talent_1",
    "source": {
      "type": "weapon",
      "id": "14104",
      "label": "硫磺石｜炽烈吐息",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14104.json",
      "key": "weapon:14104:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 3.5
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>或<color=#FFFFFF>[闪避反击]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>3.5%</color>，最多叠加8层，持续8秒，0.5秒内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14104_talent_2",
    "source": {
      "type": "weapon",
      "id": "14104",
      "label": "硫磺石｜炽烈吐息",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14104.json",
      "key": "weapon:14104:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 4.4
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>或<color=#FFFFFF>[闪避反击]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>4.4%</color>，最多叠加8层，持续8秒，0.5秒内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14104_talent_3",
    "source": {
      "type": "weapon",
      "id": "14104",
      "label": "硫磺石｜炽烈吐息",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14104.json",
      "key": "weapon:14104:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 5.2
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>或<color=#FFFFFF>[闪避反击]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>5.2%</color>，最多叠加8层，持续8秒，0.5秒内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14104_talent_4",
    "source": {
      "type": "weapon",
      "id": "14104",
      "label": "硫磺石｜炽烈吐息",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14104.json",
      "key": "weapon:14104:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>或<color=#FFFFFF>[闪避反击]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>6%</color>，最多叠加8层，持续8秒，0.5秒内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14104_talent_5",
    "source": {
      "type": "weapon",
      "id": "14104",
      "label": "硫磺石｜炽烈吐息",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14104.json",
      "key": "weapon:14104:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 7
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[冲刺攻击]</color>或<color=#FFFFFF>[闪避反击]</color>命中敌人时，装备者的攻击力提升<color=#2BAD00>7%</color>，最多叠加8层，持续8秒，0.5秒内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14105_talent_1",
    "source": {
      "type": "weapon",
      "id": "14105",
      "label": "海妖摇篮｜触抚心拥",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14105.json",
      "key": "weapon:14105:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 6
      }
    ],
    "rawDescription": "装备者的生命值降低时，造成的<color=#98EFF0>冰属性贯穿伤害</color>提升<color=#2BAD00>6%</color>，最多叠加3层，持续25秒，每层效果单独结算持续时间，0.5秒内最多触发一次；装备者生命值降低至最大值的50%时，暴击率提升<color=#2BAD00>20%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14105_talent_2",
    "source": {
      "type": "weapon",
      "id": "14105",
      "label": "海妖摇篮｜触抚心拥",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14105.json",
      "key": "weapon:14105:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 7
      }
    ],
    "rawDescription": "装备者的生命值降低时，造成的<color=#98EFF0>冰属性贯穿伤害</color>提升<color=#2BAD00>7%</color>，最多叠加3层，持续25秒，每层效果单独结算持续时间，0.5秒内最多触发一次；装备者生命值降低至最大值的50%时，暴击率提升<color=#2BAD00>23%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14105_talent_3",
    "source": {
      "type": "weapon",
      "id": "14105",
      "label": "海妖摇篮｜触抚心拥",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14105.json",
      "key": "weapon:14105:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 8
      }
    ],
    "rawDescription": "装备者的生命值降低时，造成的<color=#98EFF0>冰属性贯穿伤害</color>提升<color=#2BAD00>8%</color>，最多叠加3层，持续25秒，每层效果单独结算持续时间，0.5秒内最多触发一次；装备者生命值降低至最大值的50%时，暴击率提升<color=#2BAD00>26%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14105_talent_4",
    "source": {
      "type": "weapon",
      "id": "14105",
      "label": "海妖摇篮｜触抚心拥",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14105.json",
      "key": "weapon:14105:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 9
      }
    ],
    "rawDescription": "装备者的生命值降低时，造成的<color=#98EFF0>冰属性贯穿伤害</color>提升<color=#2BAD00>9%</color>，最多叠加3层，持续25秒，每层效果单独结算持续时间，0.5秒内最多触发一次；装备者生命值降低至最大值的50%时，暴击率提升<color=#2BAD00>29%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14105_talent_5",
    "source": {
      "type": "weapon",
      "id": "14105",
      "label": "海妖摇篮｜触抚心拥",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14105.json",
      "key": "weapon:14105:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10
      }
    ],
    "rawDescription": "装备者的生命值降低时，造成的<color=#98EFF0>冰属性贯穿伤害</color>提升<color=#2BAD00>10%</color>，最多叠加3层，持续25秒，每层效果单独结算持续时间，0.5秒内最多触发一次；装备者生命值降低至最大值的50%时，暴击率提升<color=#2BAD00>32%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14107_talent_1",
    "source": {
      "type": "weapon",
      "id": "14107",
      "label": "奔袭獠牙｜不破铁骑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14107.json",
      "key": "weapon:14107:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "装备者施加的护盾值提升<color=#2BAD00>30%</color>；队伍中任意角色触发<color=#FFFFFF>[破招]</color>或<color=#FFFFFF>[极限闪避]</color>时，全队角色造成的伤害提升<color=#2BAD00>18%</color>，造成的失衡值提升<color=#2BAD00>12%</color>，持续20秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "weaponRefinement": 1,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14107_talent_2",
    "source": {
      "type": "weapon",
      "id": "14107",
      "label": "奔袭獠牙｜不破铁骑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14107.json",
      "key": "weapon:14107:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 22.5
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "装备者施加的护盾值提升<color=#2BAD00>38%</color>；队伍中任意角色触发<color=#FFFFFF>[破招]</color>或<color=#FFFFFF>[极限闪避]</color>时，全队角色造成的伤害提升<color=#2BAD00>22.5%</color>，造成的失衡值提升<color=#2BAD00>15%</color>，持续20秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "weaponRefinement": 2,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14107_talent_3",
    "source": {
      "type": "weapon",
      "id": "14107",
      "label": "奔袭獠牙｜不破铁骑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14107.json",
      "key": "weapon:14107:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 27
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 18
      }
    ],
    "rawDescription": "装备者施加的护盾值提升<color=#2BAD00>46%</color>；队伍中任意角色触发<color=#FFFFFF>[破招]</color>或<color=#FFFFFF>[极限闪避]</color>时，全队角色造成的伤害提升<color=#2BAD00>27%</color>，造成的失衡值提升<color=#2BAD00>18%</color>，持续20秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "weaponRefinement": 3,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14107_talent_4",
    "source": {
      "type": "weapon",
      "id": "14107",
      "label": "奔袭獠牙｜不破铁骑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14107.json",
      "key": "weapon:14107:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 31.5
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 21
      }
    ],
    "rawDescription": "装备者施加的护盾值提升<color=#2BAD00>52%</color>；队伍中任意角色触发<color=#FFFFFF>[破招]</color>或<color=#FFFFFF>[极限闪避]</color>时，全队角色造成的伤害提升<color=#2BAD00>31.5%</color>，造成的失衡值提升<color=#2BAD00>21%</color>，持续20秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "weaponRefinement": 4,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14107_talent_5",
    "source": {
      "type": "weapon",
      "id": "14107",
      "label": "奔袭獠牙｜不破铁骑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14107.json",
      "key": "weapon:14107:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 36
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 24
      }
    ],
    "rawDescription": "装备者施加的护盾值提升<color=#2BAD00>60%</color>；队伍中任意角色触发<color=#FFFFFF>[破招]</color>或<color=#FFFFFF>[极限闪避]</color>时，全队角色造成的伤害提升<color=#2BAD00>36%</color>，造成的失衡值提升<color=#2BAD00>24%</color>，持续20秒，同名被动效果之间不可叠加。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "weaponRefinement": 5,
    "notes": "包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14109_talent_1",
    "source": {
      "type": "weapon",
      "id": "14109",
      "label": "霰落星殿｜霜染寒星",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14109.json",
      "key": "weapon:14109:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 50
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>50%</color>；发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意角色对敌人施加属性异常效果时，装备者造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>20%</color>，最多叠加2层，持续15秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14109_talent_2",
    "source": {
      "type": "weapon",
      "id": "14109",
      "label": "霰落星殿｜霜染寒星",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14109.json",
      "key": "weapon:14109:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 57
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 23
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>57%</color>；发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意角色对敌人施加属性异常效果时，装备者造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>23%</color>，最多叠加2层，持续15秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14109_talent_3",
    "source": {
      "type": "weapon",
      "id": "14109",
      "label": "霰落星殿｜霜染寒星",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14109.json",
      "key": "weapon:14109:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 65
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 26
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>65%</color>；发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意角色对敌人施加属性异常效果时，装备者造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>26%</color>，最多叠加2层，持续15秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14109_talent_4",
    "source": {
      "type": "weapon",
      "id": "14109",
      "label": "霰落星殿｜霜染寒星",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14109.json",
      "key": "weapon:14109:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 72
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 29
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>72%</color>；发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意角色对敌人施加属性异常效果时，装备者造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>29%</color>，最多叠加2层，持续15秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14109_talent_5",
    "source": {
      "type": "weapon",
      "id": "14109",
      "label": "霰落星殿｜霜染寒星",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14109.json",
      "key": "weapon:14109:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 80
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 32
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>80%</color>；发动<color=#FFFFFF>[强化特殊技]</color>或队伍中任意角色对敌人施加属性异常效果时，装备者造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>32%</color>，最多叠加2层，持续15秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14114_talent_1",
    "source": {
      "type": "weapon",
      "id": "14114",
      "label": "拘缚者｜束缚枷锁",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14114.json",
      "key": "weapon:14114:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 6,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "攻击命中敌人时，<color=#FFFFFF>[普通攻击]</color>造成的伤害和失衡值提升<color=#2BAD00>6%</color>，最多叠加5层，持续8秒，同一招式内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 5,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14114_talent_2",
    "source": {
      "type": "weapon",
      "id": "14114",
      "label": "拘缚者｜束缚枷锁",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14114.json",
      "key": "weapon:14114:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 7.5,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "攻击命中敌人时，<color=#FFFFFF>[普通攻击]</color>造成的伤害和失衡值提升<color=#2BAD00>7.5%</color>，最多叠加5层，持续8秒，同一招式内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 5,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14114_talent_3",
    "source": {
      "type": "weapon",
      "id": "14114",
      "label": "拘缚者｜束缚枷锁",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14114.json",
      "key": "weapon:14114:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 9,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "攻击命中敌人时，<color=#FFFFFF>[普通攻击]</color>造成的伤害和失衡值提升<color=#2BAD00>9%</color>，最多叠加5层，持续8秒，同一招式内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 5,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14114_talent_4",
    "source": {
      "type": "weapon",
      "id": "14114",
      "label": "拘缚者｜束缚枷锁",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14114.json",
      "key": "weapon:14114:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10.5,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "攻击命中敌人时，<color=#FFFFFF>[普通攻击]</color>造成的伤害和失衡值提升<color=#2BAD00>10.5%</color>，最多叠加5层，持续8秒，同一招式内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 5,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14114_talent_5",
    "source": {
      "type": "weapon",
      "id": "14114",
      "label": "拘缚者｜束缚枷锁",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14114.json",
      "key": "weapon:14114:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 12,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "攻击命中敌人时，<color=#FFFFFF>[普通攻击]</color>造成的伤害和失衡值提升<color=#2BAD00>12%</color>，最多叠加5层，持续8秒，同一招式内最多触发一次，每层效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 5,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14116_talent_1",
    "source": {
      "type": "weapon",
      "id": "14116",
      "label": "焰心桂冠｜流动之火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14116.json",
      "key": "weapon:14116:talent:1"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 25
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 1.5
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[快速支援]</color>或<color=#FFFFFF>[极限支援]</color>时，装备者的冲击力提升<color=#2BAD00>25%</color>，持续8秒；装备者的<color=#FFFFFF>[普通攻击]</color>命中敌人时，对目标施加一层<color=#FFFFFF>[萎靡]</color>，最多叠加20层，持续30秒，重复触发时刷新持续时间；队伍中任意角色攻击命中敌人时，目标每拥有一层<color=#FFFFFF>[萎靡]</color>，本次攻击中<color=#98EFF0>冰属性伤害</color>和<color=#FF5521>火属性伤害</color>的暴击伤害提升<color=#2BAD00>1.5%</color>，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 20,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "原文包含多个持续时间：8、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14116_talent_2",
    "source": {
      "type": "weapon",
      "id": "14116",
      "label": "焰心桂冠｜流动之火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14116.json",
      "key": "weapon:14116:talent:2"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 28.75
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 1.72
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[快速支援]</color>或<color=#FFFFFF>[极限支援]</color>时，装备者的冲击力提升<color=#2BAD00>28.75%</color>，持续8秒；装备者的<color=#FFFFFF>[普通攻击]</color>命中敌人时，对目标施加一层<color=#FFFFFF>[萎靡]</color>，最多叠加20层，持续30秒，重复触发时刷新持续时间；队伍中任意角色攻击命中敌人时，目标每拥有一层<color=#FFFFFF>[萎靡]</color>，本次攻击中<color=#98EFF0>冰属性伤害</color>和<color=#FF5521>火属性伤害</color>的暴击伤害提升<color=#2BAD00>1.72%</color>，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 20,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "原文包含多个持续时间：8、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14116_talent_3",
    "source": {
      "type": "weapon",
      "id": "14116",
      "label": "焰心桂冠｜流动之火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14116.json",
      "key": "weapon:14116:talent:3"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 32.5
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 1.95
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[快速支援]</color>或<color=#FFFFFF>[极限支援]</color>时，装备者的冲击力提升<color=#2BAD00>32.5%</color>，持续8秒；装备者的<color=#FFFFFF>[普通攻击]</color>命中敌人时，对目标施加一层<color=#FFFFFF>[萎靡]</color>，最多叠加20层，持续30秒，重复触发时刷新持续时间；队伍中任意角色攻击命中敌人时，目标每拥有一层<color=#FFFFFF>[萎靡]</color>，本次攻击中<color=#98EFF0>冰属性伤害</color>和<color=#FF5521>火属性伤害</color>的暴击伤害提升<color=#2BAD00>1.95%</color>，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 20,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "原文包含多个持续时间：8、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14116_talent_4",
    "source": {
      "type": "weapon",
      "id": "14116",
      "label": "焰心桂冠｜流动之火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14116.json",
      "key": "weapon:14116:talent:4"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 36.25
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 2.17
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[快速支援]</color>或<color=#FFFFFF>[极限支援]</color>时，装备者的冲击力提升<color=#2BAD00>36.25%</color>，持续8秒；装备者的<color=#FFFFFF>[普通攻击]</color>命中敌人时，对目标施加一层<color=#FFFFFF>[萎靡]</color>，最多叠加20层，持续30秒，重复触发时刷新持续时间；队伍中任意角色攻击命中敌人时，目标每拥有一层<color=#FFFFFF>[萎靡]</color>，本次攻击中<color=#98EFF0>冰属性伤害</color>和<color=#FF5521>火属性伤害</color>的暴击伤害提升<color=#2BAD00>2.17%</color>，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 20,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "原文包含多个持续时间：8、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14116_talent_5",
    "source": {
      "type": "weapon",
      "id": "14116",
      "label": "焰心桂冠｜流动之火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14116.json",
      "key": "weapon:14116:talent:5"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 2.4
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[快速支援]</color>或<color=#FFFFFF>[极限支援]</color>时，装备者的冲击力提升<color=#2BAD00>40%</color>，持续8秒；装备者的<color=#FFFFFF>[普通攻击]</color>命中敌人时，对目标施加一层<color=#FFFFFF>[萎靡]</color>，最多叠加20层，持续30秒，重复触发时刷新持续时间；队伍中任意角色攻击命中敌人时，目标每拥有一层<color=#FFFFFF>[萎靡]</color>，本次攻击中<color=#98EFF0>冰属性伤害</color>和<color=#FF5521>火属性伤害</color>的暴击伤害提升<color=#2BAD00>2.4%</color>，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 20,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "原文包含多个持续时间：8、30 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14117_talent_1",
    "source": {
      "type": "weapon",
      "id": "14117",
      "label": "灼心摇壶｜焦油斟注",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14117.json",
      "key": "weapon:14117:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 3.5,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.6</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者造成的伤害提升<color=#2BAD00>3.5%</color>，最多叠加10层，持续6秒，0.3秒内最多触发一次，位于后场时叠加效率翻倍，重复触发时刷新持续时间；获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升<color=#2BAD00>50</color>点，异常精通提升效果不可叠加，持续6秒。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14117_talent_2",
    "source": {
      "type": "weapon",
      "id": "14117",
      "label": "灼心摇壶｜焦油斟注",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14117.json",
      "key": "weapon:14117:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.75
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 4.4,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.75</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者造成的伤害提升<color=#2BAD00>4.4%</color>，最多叠加10层，持续6秒，0.3秒内最多触发一次，位于后场时叠加效率翻倍，重复触发时刷新持续时间；获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升<color=#2BAD00>62</color>点，异常精通提升效果不可叠加，持续6秒。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14117_talent_3",
    "source": {
      "type": "weapon",
      "id": "14117",
      "label": "灼心摇壶｜焦油斟注",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14117.json",
      "key": "weapon:14117:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.9
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 5.2,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>0.9</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者造成的伤害提升<color=#2BAD00>5.2%</color>，最多叠加10层，持续6秒，0.3秒内最多触发一次，位于后场时叠加效率翻倍，重复触发时刷新持续时间；获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升<color=#2BAD00>75</color>点，异常精通提升效果不可叠加，持续6秒。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14117_talent_4",
    "source": {
      "type": "weapon",
      "id": "14117",
      "label": "灼心摇壶｜焦油斟注",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14117.json",
      "key": "weapon:14117:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 1.05
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 6.1,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>1.05</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者造成的伤害提升<color=#2BAD00>6.1%</color>，最多叠加10层，持续6秒，0.3秒内最多触发一次，位于后场时叠加效率翻倍，重复触发时刷新持续时间；获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升<color=#2BAD00>87</color>点，异常精通提升效果不可叠加，持续6秒。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14117_talent_5",
    "source": {
      "type": "weapon",
      "id": "14117",
      "label": "灼心摇壶｜焦油斟注",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14117.json",
      "key": "weapon:14117:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 1.2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 7,
        "scope": {
          "skillCategories": [
            "special",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>1.2</color>点/秒；<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[支援攻击]</color>命中敌人时，装备者造成的伤害提升<color=#2BAD00>7%</color>，最多叠加10层，持续6秒，0.3秒内最多触发一次，位于后场时叠加效率翻倍，重复触发时刷新持续时间；获得伤害提升效果时，若叠加层数大于等于5层，则装备者的异常精通额外提升<color=#2BAD00>100</color>点，异常精通提升效果不可叠加，持续6秒。",
    "trigger": "attack-hit",
    "durationSeconds": 6,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 10,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14118_talent_1",
    "source": {
      "type": "weapon",
      "id": "14118",
      "label": "嵌合编译器｜数据洪流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14118.json",
      "key": "weapon:14118:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 12
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 25
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>12%</color>；发动<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升<color=#2BAD00>25</color>点，最多叠加3层，持续8秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14118_talent_2",
    "source": {
      "type": "weapon",
      "id": "14118",
      "label": "嵌合编译器｜数据洪流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14118.json",
      "key": "weapon:14118:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 31
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>15%</color>；发动<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升<color=#2BAD00>31</color>点，最多叠加3层，持续8秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14118_talent_3",
    "source": {
      "type": "weapon",
      "id": "14118",
      "label": "嵌合编译器｜数据洪流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14118.json",
      "key": "weapon:14118:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 18
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 37
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>18%</color>；发动<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升<color=#2BAD00>37</color>点，最多叠加3层，持续8秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14118_talent_4",
    "source": {
      "type": "weapon",
      "id": "14118",
      "label": "嵌合编译器｜数据洪流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14118.json",
      "key": "weapon:14118:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 21
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 43
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>21%</color>；发动<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升<color=#2BAD00>43</color>点，最多叠加3层，持续8秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14118_talent_5",
    "source": {
      "type": "weapon",
      "id": "14118",
      "label": "嵌合编译器｜数据洪流",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14118.json",
      "key": "weapon:14118:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 24
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 50
      }
    ],
    "rawDescription": "攻击力提升<color=#2BAD00>24%</color>；发动<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>时，装备者的异常精通提升<color=#2BAD00>50</color>点，最多叠加3层，持续8秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14119_talent_1",
    "source": {
      "type": "weapon",
      "id": "14119",
      "label": "深海访客｜诸洋之王",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14119.json",
      "key": "weapon:14119:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>25%</color>；<color=#FFFFFF>[普通攻击]</color>命中敌人时，装备者的暴击率提升<color=#2BAD00>10%</color>，持续8秒；<color=#FFFFFF>[冲刺攻击]</color>造成<color=#98EFF0>冰属性伤害</color>时，装备者的暴击率额外提升<color=#2BAD00>10%</color>，持续15秒，每种增益效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 1,
    "notes": "原文包含多个持续时间：8、15 秒。；涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14119_talent_2",
    "source": {
      "type": "weapon",
      "id": "14119",
      "label": "深海访客｜诸洋之王",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14119.json",
      "key": "weapon:14119:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 12.5
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 31.5
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>31.5%</color>；<color=#FFFFFF>[普通攻击]</color>命中敌人时，装备者的暴击率提升<color=#2BAD00>12.5%</color>，持续8秒；<color=#FFFFFF>[冲刺攻击]</color>造成<color=#98EFF0>冰属性伤害</color>时，装备者的暴击率额外提升<color=#2BAD00>12.5%</color>，持续15秒，每种增益效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 2,
    "notes": "原文包含多个持续时间：8、15 秒。；涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14119_talent_3",
    "source": {
      "type": "weapon",
      "id": "14119",
      "label": "深海访客｜诸洋之王",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14119.json",
      "key": "weapon:14119:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 38
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>38%</color>；<color=#FFFFFF>[普通攻击]</color>命中敌人时，装备者的暴击率提升<color=#2BAD00>15%</color>，持续8秒；<color=#FFFFFF>[冲刺攻击]</color>造成<color=#98EFF0>冰属性伤害</color>时，装备者的暴击率额外提升<color=#2BAD00>15%</color>，持续15秒，每种增益效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 3,
    "notes": "原文包含多个持续时间：8、15 秒。；涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14119_talent_4",
    "source": {
      "type": "weapon",
      "id": "14119",
      "label": "深海访客｜诸洋之王",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14119.json",
      "key": "weapon:14119:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 17.5
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 44.5
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>44.5%</color>；<color=#FFFFFF>[普通攻击]</color>命中敌人时，装备者的暴击率提升<color=#2BAD00>17.5%</color>，持续8秒；<color=#FFFFFF>[冲刺攻击]</color>造成<color=#98EFF0>冰属性伤害</color>时，装备者的暴击率额外提升<color=#2BAD00>17.5%</color>，持续15秒，每种增益效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 4,
    "notes": "原文包含多个持续时间：8、15 秒。；涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14119_talent_5",
    "source": {
      "type": "weapon",
      "id": "14119",
      "label": "深海访客｜诸洋之王",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14119.json",
      "key": "weapon:14119:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 50
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>50%</color>；<color=#FFFFFF>[普通攻击]</color>命中敌人时，装备者的暴击率提升<color=#2BAD00>20%</color>，持续8秒；<color=#FFFFFF>[冲刺攻击]</color>造成<color=#98EFF0>冰属性伤害</color>时，装备者的暴击率额外提升<color=#2BAD00>20%</color>，持续15秒，每种增益效果单独结算持续时间。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "weaponRefinement": 5,
    "notes": "原文包含多个持续时间：8、15 秒。；涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14120_talent_1",
    "source": {
      "type": "weapon",
      "id": "14120",
      "label": "残心青囊｜啖若逆修",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14120.json",
      "key": "weapon:14120:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 40
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>10%</color>；<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>40%</color>；队伍中任意角色对敌人施加属性异常效果或造成失衡时，装备者的暴击率额外提升<color=#2BAD00>10%</color>，持续15秒。",
    "durationSeconds": 15,
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14120_talent_2",
    "source": {
      "type": "weapon",
      "id": "14120",
      "label": "残心青囊｜啖若逆修",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14120.json",
      "key": "weapon:14120:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 11.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 46
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>11.5%</color>；<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>46%</color>；队伍中任意角色对敌人施加属性异常效果或造成失衡时，装备者的暴击率额外提升<color=#2BAD00>11.5%</color>，持续15秒。",
    "durationSeconds": 15,
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14120_talent_3",
    "source": {
      "type": "weapon",
      "id": "14120",
      "label": "残心青囊｜啖若逆修",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14120.json",
      "key": "weapon:14120:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 13
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 52
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>13%</color>；<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>52%</color>；队伍中任意角色对敌人施加属性异常效果或造成失衡时，装备者的暴击率额外提升<color=#2BAD00>13%</color>，持续15秒。",
    "durationSeconds": 15,
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14120_talent_4",
    "source": {
      "type": "weapon",
      "id": "14120",
      "label": "残心青囊｜啖若逆修",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14120.json",
      "key": "weapon:14120:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 14.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 58
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>14.5%</color>；<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>58%</color>；队伍中任意角色对敌人施加属性异常效果或造成失衡时，装备者的暴击率额外提升<color=#2BAD00>14.5%</color>，持续15秒。",
    "durationSeconds": 15,
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14120_talent_5",
    "source": {
      "type": "weapon",
      "id": "14120",
      "label": "残心青囊｜啖若逆修",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14120.json",
      "key": "weapon:14120:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 16
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 64
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>16%</color>；<color=#FFFFFF>[冲刺攻击]</color>造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>64%</color>；队伍中任意角色对敌人施加属性异常效果或造成失衡时，装备者的暴击率额外提升<color=#2BAD00>16%</color>，持续15秒。",
    "durationSeconds": 15,
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14122_talent_1",
    "source": {
      "type": "weapon",
      "id": "14122",
      "label": "时流贤者｜时喰奇谋",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14122.json",
      "key": "weapon:14122:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 75
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#2EB6FF>电属性异常积蓄效率</color>提升<color=#2BAD00>30%</color>；<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>命中处于属性异常状态下的敌人时，装备者的异常精通提升<color=#2BAD00>75</color>点，持续15秒；\n当装备者的异常精通大于等于375点时，由装备者造成的<color=#FFFFFF>[紊乱]</color>伤害提升<color=#2BAD00>25%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14122_talent_2",
    "source": {
      "type": "weapon",
      "id": "14122",
      "label": "时流贤者｜时喰奇谋",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14122.json",
      "key": "weapon:14122:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 85
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 27.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#2EB6FF>电属性异常积蓄效率</color>提升<color=#2BAD00>35%</color>；<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>命中处于属性异常状态下的敌人时，装备者的异常精通提升<color=#2BAD00>85</color>点，持续15秒；\n当装备者的异常精通大于等于375点时，由装备者造成的<color=#FFFFFF>[紊乱]</color>伤害提升<color=#2BAD00>27.5%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14122_talent_3",
    "source": {
      "type": "weapon",
      "id": "14122",
      "label": "时流贤者｜时喰奇谋",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14122.json",
      "key": "weapon:14122:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 95
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 30,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#2EB6FF>电属性异常积蓄效率</color>提升<color=#2BAD00>40%</color>；<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>命中处于属性异常状态下的敌人时，装备者的异常精通提升<color=#2BAD00>95</color>点，持续15秒；\n当装备者的异常精通大于等于375点时，由装备者造成的<color=#FFFFFF>[紊乱]</color>伤害提升<color=#2BAD00>30%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14122_talent_4",
    "source": {
      "type": "weapon",
      "id": "14122",
      "label": "时流贤者｜时喰奇谋",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14122.json",
      "key": "weapon:14122:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 105
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#2EB6FF>电属性异常积蓄效率</color>提升<color=#2BAD00>45%</color>；<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>命中处于属性异常状态下的敌人时，装备者的异常精通提升<color=#2BAD00>105</color>点，持续15秒；\n当装备者的异常精通大于等于375点时，由装备者造成的<color=#FFFFFF>[紊乱]</color>伤害提升<color=#2BAD00>32.5%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14122_talent_5",
    "source": {
      "type": "weapon",
      "id": "14122",
      "label": "时流贤者｜时喰奇谋",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14122.json",
      "key": "weapon:14122:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 115
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 35,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#2EB6FF>电属性异常积蓄效率</color>提升<color=#2BAD00>50%</color>；<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[强化特殊技]</color>命中处于属性异常状态下的敌人时，装备者的异常精通提升<color=#2BAD00>115</color>点，持续15秒；\n当装备者的异常精通大于等于375点时，由装备者造成的<color=#FFFFFF>[紊乱]</color>伤害提升<color=#2BAD00>35%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 15,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14124_talent_1",
    "source": {
      "type": "weapon",
      "id": "14124",
      "label": "防暴者Ⅵ型｜安全巡查",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14124.json",
      "key": "weapon:14124:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 35,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "dash"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>15%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，为装备者提供8层充能效果，最多叠加8层；<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>造成<color=#FE437E>以太伤害</color>时，消耗1层充能，使当前招式造成的伤害提升<color=#2BAD00>35%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14124_talent_2",
    "source": {
      "type": "weapon",
      "id": "14124",
      "label": "防暴者Ⅵ型｜安全巡查",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14124.json",
      "key": "weapon:14124:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 18.8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 43.5,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "dash"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>18.8%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，为装备者提供8层充能效果，最多叠加8层；<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>造成<color=#FE437E>以太伤害</color>时，消耗1层充能，使当前招式造成的伤害提升<color=#2BAD00>43.5%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14124_talent_3",
    "source": {
      "type": "weapon",
      "id": "14124",
      "label": "防暴者Ⅵ型｜安全巡查",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14124.json",
      "key": "weapon:14124:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 22.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 52,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "dash"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>22.6%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，为装备者提供8层充能效果，最多叠加8层；<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>造成<color=#FE437E>以太伤害</color>时，消耗1层充能，使当前招式造成的伤害提升<color=#2BAD00>52%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14124_talent_4",
    "source": {
      "type": "weapon",
      "id": "14124",
      "label": "防暴者Ⅵ型｜安全巡查",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14124.json",
      "key": "weapon:14124:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 60.5,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "dash"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>26.4%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，为装备者提供8层充能效果，最多叠加8层；<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>造成<color=#FE437E>以太伤害</color>时，消耗1层充能，使当前招式造成的伤害提升<color=#2BAD00>60.5%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14124_talent_5",
    "source": {
      "type": "weapon",
      "id": "14124",
      "label": "防暴者Ⅵ型｜安全巡查",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14124.json",
      "key": "weapon:14124:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 30
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 70,
        "scope": {
          "skillCategories": [
            "basic",
            "special",
            "dash"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>30%</color>；发动<color=#FFFFFF>[强化特殊技]</color>时，为装备者提供8层充能效果，最多叠加8层；<color=#FFFFFF>[普通攻击]</color>或<color=#FFFFFF>[冲刺攻击]</color>造成<color=#FE437E>以太伤害</color>时，消耗1层充能，使当前招式造成的伤害提升<color=#2BAD00>70%</color>。",
    "trigger": "skill-used",
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 8,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14125_talent_1",
    "source": {
      "type": "weapon",
      "id": "14125",
      "label": "玉壶青冰｜泠泠连奏",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14125.json",
      "key": "weapon:14125:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 0.7
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>命中敌人时，获得1层<color=#FFFFFF>[茶劲]</color>，每层<color=#FFFFFF>[茶劲]</color>使装备者的冲击力提升<color=#2BAD00>0.7%</color>，最多叠加30层，持续8秒，每层效果单独结算持续时间；获得<color=#FFFFFF>[茶劲]</color>时，若装备者拥有的<color=#FFFFFF>[茶劲]</color>层数大于等于15层，全队角色造成的伤害提升<color=#2BAD00>20%</color>，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 30,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "原文包含多个持续时间：8、10 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14125_talent_2",
    "source": {
      "type": "weapon",
      "id": "14125",
      "label": "玉壶青冰｜泠泠连奏",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14125.json",
      "key": "weapon:14125:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 0.88
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 23,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>命中敌人时，获得1层<color=#FFFFFF>[茶劲]</color>，每层<color=#FFFFFF>[茶劲]</color>使装备者的冲击力提升<color=#2BAD00>0.88%</color>，最多叠加30层，持续8秒，每层效果单独结算持续时间；获得<color=#FFFFFF>[茶劲]</color>时，若装备者拥有的<color=#FFFFFF>[茶劲]</color>层数大于等于15层，全队角色造成的伤害提升<color=#2BAD00>23%</color>，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 30,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "原文包含多个持续时间：8、10 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14125_talent_3",
    "source": {
      "type": "weapon",
      "id": "14125",
      "label": "玉壶青冰｜泠泠连奏",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14125.json",
      "key": "weapon:14125:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 1.05
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 26,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>命中敌人时，获得1层<color=#FFFFFF>[茶劲]</color>，每层<color=#FFFFFF>[茶劲]</color>使装备者的冲击力提升<color=#2BAD00>1.05%</color>，最多叠加30层，持续8秒，每层效果单独结算持续时间；获得<color=#FFFFFF>[茶劲]</color>时，若装备者拥有的<color=#FFFFFF>[茶劲]</color>层数大于等于15层，全队角色造成的伤害提升<color=#2BAD00>26%</color>，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 30,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "原文包含多个持续时间：8、10 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14125_talent_4",
    "source": {
      "type": "weapon",
      "id": "14125",
      "label": "玉壶青冰｜泠泠连奏",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14125.json",
      "key": "weapon:14125:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 1.22
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 29,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>命中敌人时，获得1层<color=#FFFFFF>[茶劲]</color>，每层<color=#FFFFFF>[茶劲]</color>使装备者的冲击力提升<color=#2BAD00>1.22%</color>，最多叠加30层，持续8秒，每层效果单独结算持续时间；获得<color=#FFFFFF>[茶劲]</color>时，若装备者拥有的<color=#FFFFFF>[茶劲]</color>层数大于等于15层，全队角色造成的伤害提升<color=#2BAD00>29%</color>，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 30,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "原文包含多个持续时间：8、10 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14125_talent_5",
    "source": {
      "type": "weapon",
      "id": "14125",
      "label": "玉壶青冰｜泠泠连奏",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14125.json",
      "key": "weapon:14125:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 1.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32,
        "scope": {
          "skillCategories": [
            "basic"
          ]
        }
      }
    ],
    "rawDescription": "<color=#FFFFFF>[普通攻击]</color>命中敌人时，获得1层<color=#FFFFFF>[茶劲]</color>，每层<color=#FFFFFF>[茶劲]</color>使装备者的冲击力提升<color=#2BAD00>1.4%</color>，最多叠加30层，持续8秒，每层效果单独结算持续时间；获得<color=#FFFFFF>[茶劲]</color>时，若装备者拥有的<color=#FFFFFF>[茶劲]</color>层数大于等于15层，全队角色造成的伤害提升<color=#2BAD00>32%</color>，持续10秒，同名被动效果之间不可叠加。",
    "trigger": "attack-hit",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 30,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "原文包含多个持续时间：8、10 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14126_talent_1",
    "source": {
      "type": "weapon",
      "id": "14126",
      "label": "淬锋钳刺｜恣横猎心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14126.json",
      "key": "weapon:14126:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 12
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[冲刺攻击]</color>时，获得1层<color=#FFFFFF>[猎意]</color>，每层<color=#FFFFFF>[猎意]</color>使装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>12%</color>，最多叠加3层，持续10秒，0.5秒内最多触发一次，重复触发时刷新持续时间；进入接战状态或触发<color=#FFFFFF>[极限闪避]</color>时，直接获得3层<color=#FFFFFF>[猎意]</color>；<color=#FFFFFF>[猎意]</color>叠加至层数上限后，装备者的属性异常积蓄效率提升<color=#2BAD00>40%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14126_talent_2",
    "source": {
      "type": "weapon",
      "id": "14126",
      "label": "淬锋钳刺｜恣横猎心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14126.json",
      "key": "weapon:14126:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 15
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[冲刺攻击]</color>时，获得1层<color=#FFFFFF>[猎意]</color>，每层<color=#FFFFFF>[猎意]</color>使装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>15%</color>，最多叠加3层，持续10秒，0.5秒内最多触发一次，重复触发时刷新持续时间；进入接战状态或触发<color=#FFFFFF>[极限闪避]</color>时，直接获得3层<color=#FFFFFF>[猎意]</color>；<color=#FFFFFF>[猎意]</color>叠加至层数上限后，装备者的属性异常积蓄效率提升<color=#2BAD00>50%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14126_talent_3",
    "source": {
      "type": "weapon",
      "id": "14126",
      "label": "淬锋钳刺｜恣横猎心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14126.json",
      "key": "weapon:14126:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 18
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[冲刺攻击]</color>时，获得1层<color=#FFFFFF>[猎意]</color>，每层<color=#FFFFFF>[猎意]</color>使装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>18%</color>，最多叠加3层，持续10秒，0.5秒内最多触发一次，重复触发时刷新持续时间；进入接战状态或触发<color=#FFFFFF>[极限闪避]</color>时，直接获得3层<color=#FFFFFF>[猎意]</color>；<color=#FFFFFF>[猎意]</color>叠加至层数上限后，装备者的属性异常积蓄效率提升<color=#2BAD00>60%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14126_talent_4",
    "source": {
      "type": "weapon",
      "id": "14126",
      "label": "淬锋钳刺｜恣横猎心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14126.json",
      "key": "weapon:14126:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 21
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[冲刺攻击]</color>时，获得1层<color=#FFFFFF>[猎意]</color>，每层<color=#FFFFFF>[猎意]</color>使装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>21%</color>，最多叠加3层，持续10秒，0.5秒内最多触发一次，重复触发时刷新持续时间；进入接战状态或触发<color=#FFFFFF>[极限闪避]</color>时，直接获得3层<color=#FFFFFF>[猎意]</color>；<color=#FFFFFF>[猎意]</color>叠加至层数上限后，装备者的属性异常积蓄效率提升<color=#2BAD00>70%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14126_talent_5",
    "source": {
      "type": "weapon",
      "id": "14126",
      "label": "淬锋钳刺｜恣横猎心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14126.json",
      "key": "weapon:14126:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "physicalDmgBonus",
        "operation": "add-percent",
        "value": 24
      }
    ],
    "rawDescription": "发动<color=#FFFFFF>[冲刺攻击]</color>时，获得1层<color=#FFFFFF>[猎意]</color>，每层<color=#FFFFFF>[猎意]</color>使装备者造成的<color=#F0D12B>物理伤害</color>提升<color=#2BAD00>24%</color>，最多叠加3层，持续10秒，0.5秒内最多触发一次，重复触发时刷新持续时间；进入接战状态或触发<color=#FFFFFF>[极限闪避]</color>时，直接获得3层<color=#FFFFFF>[猎意]</color>；<color=#FFFFFF>[猎意]</color>叠加至层数上限后，装备者的属性异常积蓄效率提升<color=#2BAD00>80%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14129_talent_1",
    "source": {
      "type": "weapon",
      "id": "14129",
      "label": "千面日陨｜万千非我",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14129.json",
      "key": "weapon:14129:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 45
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>45%</color>；<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>造成<color=#98EFF0>冰属性伤害</color>时，角色获得<color=#FFFFFF>[零度处刑宣言]</color>效果，持续3秒；<color=#FFFFFF>[零度处刑宣言]</color>效果期间，角色命中敌人时无视<color=#2BAD00>25%</color>防御力。",
    "trigger": "attack-hit",
    "durationSeconds": 3,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14129_talent_2",
    "source": {
      "type": "weapon",
      "id": "14129",
      "label": "千面日陨｜万千非我",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14129.json",
      "key": "weapon:14129:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 51.75
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>51.75%</color>；<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>造成<color=#98EFF0>冰属性伤害</color>时，角色获得<color=#FFFFFF>[零度处刑宣言]</color>效果，持续3秒；<color=#FFFFFF>[零度处刑宣言]</color>效果期间，角色命中敌人时无视<color=#2BAD00>28.75%</color>防御力。",
    "trigger": "attack-hit",
    "durationSeconds": 3,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14129_talent_3",
    "source": {
      "type": "weapon",
      "id": "14129",
      "label": "千面日陨｜万千非我",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14129.json",
      "key": "weapon:14129:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 58.5
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>58.5%</color>；<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>造成<color=#98EFF0>冰属性伤害</color>时，角色获得<color=#FFFFFF>[零度处刑宣言]</color>效果，持续3秒；<color=#FFFFFF>[零度处刑宣言]</color>效果期间，角色命中敌人时无视<color=#2BAD00>32.5%</color>防御力。",
    "trigger": "attack-hit",
    "durationSeconds": 3,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14129_talent_4",
    "source": {
      "type": "weapon",
      "id": "14129",
      "label": "千面日陨｜万千非我",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14129.json",
      "key": "weapon:14129:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 65.25
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>65.25%</color>；<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>造成<color=#98EFF0>冰属性伤害</color>时，角色获得<color=#FFFFFF>[零度处刑宣言]</color>效果，持续3秒；<color=#FFFFFF>[零度处刑宣言]</color>效果期间，角色命中敌人时无视<color=#2BAD00>36.25%</color>防御力。",
    "trigger": "attack-hit",
    "durationSeconds": 3,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14129_talent_5",
    "source": {
      "type": "weapon",
      "id": "14129",
      "label": "千面日陨｜万千非我",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14129.json",
      "key": "weapon:14129:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 72
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>72%</color>；<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>造成<color=#98EFF0>冰属性伤害</color>时，角色获得<color=#FFFFFF>[零度处刑宣言]</color>效果，持续3秒；<color=#FFFFFF>[零度处刑宣言]</color>效果期间，角色命中敌人时无视<color=#2BAD00>40%</color>防御力。",
    "trigger": "attack-hit",
    "durationSeconds": 3,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14130_talent_1",
    "source": {
      "type": "weapon",
      "id": "14130",
      "label": "嚣枪喧焰｜喋声吞炎",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14130.json",
      "key": "weapon:14130:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>20%</color>；装备者发动<color=#FFFFFF>[追加攻击]</color>造成<color=#FF5521>火属性伤害</color>时，装备者的攻击对敌人造成的伤害无视<color=#2BAD00>15%</color>防御力，持续8秒，3秒内最多获得1层，最多叠加2层，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14130_talent_2",
    "source": {
      "type": "weapon",
      "id": "14130",
      "label": "嚣枪喧焰｜喋声吞炎",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14130.json",
      "key": "weapon:14130:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>23%</color>；装备者发动<color=#FFFFFF>[追加攻击]</color>造成<color=#FF5521>火属性伤害</color>时，装备者的攻击对敌人造成的伤害无视<color=#2BAD00>17.2%</color>防御力，持续8秒，3秒内最多获得1层，最多叠加2层，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14130_talent_3",
    "source": {
      "type": "weapon",
      "id": "14130",
      "label": "嚣枪喧焰｜喋声吞炎",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14130.json",
      "key": "weapon:14130:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>26%</color>；装备者发动<color=#FFFFFF>[追加攻击]</color>造成<color=#FF5521>火属性伤害</color>时，装备者的攻击对敌人造成的伤害无视<color=#2BAD00>19.5%</color>防御力，持续8秒，3秒内最多获得1层，最多叠加2层，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14130_talent_4",
    "source": {
      "type": "weapon",
      "id": "14130",
      "label": "嚣枪喧焰｜喋声吞炎",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14130.json",
      "key": "weapon:14130:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 29
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>29%</color>；装备者发动<color=#FFFFFF>[追加攻击]</color>造成<color=#FF5521>火属性伤害</color>时，装备者的攻击对敌人造成的伤害无视<color=#2BAD00>21.7%</color>防御力，持续8秒，3秒内最多获得1层，最多叠加2层，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14130_talent_5",
    "source": {
      "type": "weapon",
      "id": "14130",
      "label": "嚣枪喧焰｜喋声吞炎",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14130.json",
      "key": "weapon:14130:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>32%</color>；装备者发动<color=#FFFFFF>[追加攻击]</color>造成<color=#FF5521>火属性伤害</color>时，装备者的攻击对敌人造成的伤害无视<color=#2BAD00>24%</color>防御力，持续8秒，3秒内最多获得1层，最多叠加2层，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 8,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14131_talent_1",
    "source": {
      "type": "weapon",
      "id": "14131",
      "label": "玲珑妆匣｜卓卓千华",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14131.json",
      "key": "weapon:14131:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": {
          "type": "per-stack",
          "base": 0,
          "perStack": 10
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>入场时，为装备者回复<color=#2BAD00>5</color>点能量，5秒内最多触发一次；装备者消耗25点或以上能量时，全队角色造成的伤害提升<color=#2BAD00>10%</color>，最多叠加2层，持续20秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。；规则修订：10% 是每层全队造成的伤害，满拐按2层=20%，不把触发动作误当成伤害作用域。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14131_talent_2",
    "source": {
      "type": "weapon",
      "id": "14131",
      "label": "玲珑妆匣｜卓卓千华",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14131.json",
      "key": "weapon:14131:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "chain",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>入场时，为装备者回复<color=#2BAD00>5.5</color>点能量，5秒内最多触发一次；装备者消耗25点或以上能量时，全队角色造成的伤害提升<color=#2BAD00>11.5%</color>，最多叠加2层，持续20秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14131_talent_3",
    "source": {
      "type": "weapon",
      "id": "14131",
      "label": "玲珑妆匣｜卓卓千华",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14131.json",
      "key": "weapon:14131:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "chain",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>入场时，为装备者回复<color=#2BAD00>6</color>点能量，5秒内最多触发一次；装备者消耗25点或以上能量时，全队角色造成的伤害提升<color=#2BAD00>13%</color>，最多叠加2层，持续20秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14131_talent_4",
    "source": {
      "type": "weapon",
      "id": "14131",
      "label": "玲珑妆匣｜卓卓千华",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14131.json",
      "key": "weapon:14131:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "chain",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>入场时，为装备者回复<color=#2BAD00>6.5</color>点能量，5秒内最多触发一次；装备者消耗25点或以上能量时，全队角色造成的伤害提升<color=#2BAD00>14.5%</color>，最多叠加2层，持续20秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14131_talent_5",
    "source": {
      "type": "weapon",
      "id": "14131",
      "label": "玲珑妆匣｜卓卓千华",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14131.json",
      "key": "weapon:14131:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "chain",
            "assist"
          ]
        }
      }
    ],
    "rawDescription": "队伍中任意角色通过<color=#FFFFFF>[快速支援]</color>、<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[招架支援]</color>、<color=#FFFFFF>[回避支援]</color>入场时，为装备者回复<color=#2BAD00>7</color>点能量，5秒内最多触发一次；装备者消耗25点或以上能量时，全队角色造成的伤害提升<color=#2BAD00>16%</color>，最多叠加2层，持续20秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及能量/资源回复，当前 BuffEffect 尚未定义资源效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14132_talent_1",
    "source": {
      "type": "weapon",
      "id": "14132",
      "label": "心弦夜响｜弦音相随",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14132.json",
      "key": "weapon:14132:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 50
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 12.5,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>50%</color>；装备者进入接战状态、发动<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，获得1层<color=#FFFFFF>[心弦]</color>，每层<color=#FFFFFF>[心弦]</color>会使装备者的<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>无视目标<color=#2BAD00>12.5%</color><color=#FF5521>火属性伤害抗性</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14132_talent_2",
    "source": {
      "type": "weapon",
      "id": "14132",
      "label": "心弦夜响｜弦音相随",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14132.json",
      "key": "weapon:14132:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 57.5
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>57.5%</color>；装备者进入接战状态、发动<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，获得1层<color=#FFFFFF>[心弦]</color>，每层<color=#FFFFFF>[心弦]</color>会使装备者的<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>无视目标<color=#2BAD00>14.5%</color><color=#FF5521>火属性伤害抗性</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14132_talent_3",
    "source": {
      "type": "weapon",
      "id": "14132",
      "label": "心弦夜响｜弦音相随",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14132.json",
      "key": "weapon:14132:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 65
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 16.5,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>65%</color>；装备者进入接战状态、发动<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，获得1层<color=#FFFFFF>[心弦]</color>，每层<color=#FFFFFF>[心弦]</color>会使装备者的<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>无视目标<color=#2BAD00>16.5%</color><color=#FF5521>火属性伤害抗性</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14132_talent_4",
    "source": {
      "type": "weapon",
      "id": "14132",
      "label": "心弦夜响｜弦音相随",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14132.json",
      "key": "weapon:14132:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 72.5
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 18.5,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>72.5%</color>；装备者进入接战状态、发动<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，获得1层<color=#FFFFFF>[心弦]</color>，每层<color=#FFFFFF>[心弦]</color>会使装备者的<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>无视目标<color=#2BAD00>18.5%</color><color=#FF5521>火属性伤害抗性</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14132_talent_5",
    "source": {
      "type": "weapon",
      "id": "14132",
      "label": "心弦夜响｜弦音相随",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14132.json",
      "key": "weapon:14132:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 80
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>80%</color>；装备者进入接战状态、发动<color=#FFFFFF>[连携技]</color>、<color=#FFFFFF>[终结技]</color>时，获得1层<color=#FFFFFF>[心弦]</color>，每层<color=#FFFFFF>[心弦]</color>会使装备者的<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>无视目标<color=#2BAD00>20%</color><color=#FF5521>火属性伤害抗性</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14133_talent_1",
    "source": {
      "type": "weapon",
      "id": "14133",
      "label": "飞鸟星梦｜银刺幽羽",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14133.json",
      "key": "weapon:14133:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 20
      }
    ],
    "rawDescription": "属性异常积蓄效率提升<color=#2BAD00>40%</color>；装备者造成<color=#FE437E>以太伤害</color>时，自身异常精通提升<color=#2BAD00>20</color>点，持续5秒，最多叠加6层，0.5秒内最多触发一次，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14133_talent_2",
    "source": {
      "type": "weapon",
      "id": "14133",
      "label": "飞鸟星梦｜银刺幽羽",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14133.json",
      "key": "weapon:14133:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 23
      }
    ],
    "rawDescription": "属性异常积蓄效率提升<color=#2BAD00>46%</color>；装备者造成<color=#FE437E>以太伤害</color>时，自身异常精通提升<color=#2BAD00>23</color>点，持续5秒，最多叠加6层，0.5秒内最多触发一次，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14133_talent_3",
    "source": {
      "type": "weapon",
      "id": "14133",
      "label": "飞鸟星梦｜银刺幽羽",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14133.json",
      "key": "weapon:14133:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 26
      }
    ],
    "rawDescription": "属性异常积蓄效率提升<color=#2BAD00>52%</color>；装备者造成<color=#FE437E>以太伤害</color>时，自身异常精通提升<color=#2BAD00>26</color>点，持续5秒，最多叠加6层，0.5秒内最多触发一次，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14133_talent_4",
    "source": {
      "type": "weapon",
      "id": "14133",
      "label": "飞鸟星梦｜银刺幽羽",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14133.json",
      "key": "weapon:14133:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 29
      }
    ],
    "rawDescription": "属性异常积蓄效率提升<color=#2BAD00>58%</color>；装备者造成<color=#FE437E>以太伤害</color>时，自身异常精通提升<color=#2BAD00>29</color>点，持续5秒，最多叠加6层，0.5秒内最多触发一次，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14133_talent_5",
    "source": {
      "type": "weapon",
      "id": "14133",
      "label": "飞鸟星梦｜银刺幽羽",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14133.json",
      "key": "weapon:14133:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 32
      }
    ],
    "rawDescription": "属性异常积蓄效率提升<color=#2BAD00>64%</color>；装备者造成<color=#FE437E>以太伤害</color>时，自身异常精通提升<color=#2BAD00>32</color>点，持续5秒，最多叠加6层，0.5秒内最多触发一次，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 6,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及属性异常积蓄或积蓄效率，当前模型尚未定义该效果。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14134_talent_1",
    "source": {
      "type": "weapon",
      "id": "14134",
      "label": "半糖雪兔｜易碎之甜",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14134.json",
      "key": "weapon:14134:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 30
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.46
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.46</color>点/秒；全队角色攻击力提升<color=#2BAD00>10%</color>，最大生命值提升<color=#2BAD00>10%</color>，该效果全队唯一；装备者开启或延长<color=#FFFFFF>[以太帷幕]</color>时，使全队角色的暴击伤害提升<color=#2BAD00>30%</color>，持续60秒，重复触发刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 60,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14134_talent_2",
    "source": {
      "type": "weapon",
      "id": "14134",
      "label": "半糖雪兔｜易碎之甜",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14134.json",
      "key": "weapon:14134:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 11.5
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 11.5
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 34.5
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.53
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.53</color>点/秒；全队角色攻击力提升<color=#2BAD00>11.5%</color>，最大生命值提升<color=#2BAD00>11.5%</color>，该效果全队唯一；装备者开启或延长<color=#FFFFFF>[以太帷幕]</color>时，使全队角色的暴击伤害提升<color=#2BAD00>34.5%</color>，持续60秒，重复触发刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 60,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14134_talent_3",
    "source": {
      "type": "weapon",
      "id": "14134",
      "label": "半糖雪兔｜易碎之甜",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14134.json",
      "key": "weapon:14134:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 13
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 13
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 39
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.6
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.6</color>点/秒；全队角色攻击力提升<color=#2BAD00>13%</color>，最大生命值提升<color=#2BAD00>13%</color>，该效果全队唯一；装备者开启或延长<color=#FFFFFF>[以太帷幕]</color>时，使全队角色的暴击伤害提升<color=#2BAD00>39%</color>，持续60秒，重复触发刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 60,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14134_talent_4",
    "source": {
      "type": "weapon",
      "id": "14134",
      "label": "半糖雪兔｜易碎之甜",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14134.json",
      "key": "weapon:14134:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 14.5
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 14.5
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 43.5
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.67
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.67</color>点/秒；全队角色攻击力提升<color=#2BAD00>14.5%</color>，最大生命值提升<color=#2BAD00>14.5%</color>，该效果全队唯一；装备者开启或延长<color=#FFFFFF>[以太帷幕]</color>时，使全队角色的暴击伤害提升<color=#2BAD00>43.5%</color>，持续60秒，重复触发刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 60,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14134_talent_5",
    "source": {
      "type": "weapon",
      "id": "14134",
      "label": "半糖雪兔｜易碎之甜",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14134.json",
      "key": "weapon:14134:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "hpPct",
        "operation": "add-percent",
        "value": 16
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": 16
      },
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 48
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.74
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.74</color>点/秒；全队角色攻击力提升<color=#2BAD00>16%</color>，最大生命值提升<color=#2BAD00>16%</color>，该效果全队唯一；装备者开启或延长<color=#FFFFFF>[以太帷幕]</color>时，使全队角色的暴击伤害提升<color=#2BAD00>48%</color>，持续60秒，重复触发刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 60,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14136_talent_1",
    "source": {
      "type": "weapon",
      "id": "14136",
      "label": "索魂影眸｜捕风寻踪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14136.json",
      "key": "weapon:14136:talent:1"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 4
      },
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 8
      },
      {
        "kind": "def-shred",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人并造成<color=#2EB6FF>电属性伤害</color>时，目标的防御力降低<color=#2BAD00>25%</color>，持续5秒，同名被动效果之间不可叠加；该效果触发时，如果自身不是当前操作中的角色，则装备者获得1层<color=#FFFFFF>[魂锁]</color>，最多叠加3层，同一招式内最多触发一次；每层<color=#FFFFFF>[魂锁]</color>，可使装备者的冲击力提升<color=#2BAD00>4%</color>，持续12秒，每层效果单独结算持续时间，<color=#FFFFFF>[魂锁]</color>层数叠满时，额外给装备者的冲击力提升<color=#2BAD00>8%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "原文包含多个持续时间：5、12 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14136_talent_2",
    "source": {
      "type": "weapon",
      "id": "14136",
      "label": "索魂影眸｜捕风寻踪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14136.json",
      "key": "weapon:14136:talent:2"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 4.6
      },
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 9.2
      },
      {
        "kind": "def-shred",
        "operation": "add-percent",
        "value": 28.75
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人并造成<color=#2EB6FF>电属性伤害</color>时，目标的防御力降低<color=#2BAD00>28.75%</color>，持续5秒，同名被动效果之间不可叠加；该效果触发时，如果自身不是当前操作中的角色，则装备者获得1层<color=#FFFFFF>[魂锁]</color>，最多叠加3层，同一招式内最多触发一次；每层<color=#FFFFFF>[魂锁]</color>，可使装备者的冲击力提升<color=#2BAD00>4.6%</color>，持续12秒，每层效果单独结算持续时间，<color=#FFFFFF>[魂锁]</color>层数叠满时，额外给装备者的冲击力提升<color=#2BAD00>9.2%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "原文包含多个持续时间：5、12 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14136_talent_3",
    "source": {
      "type": "weapon",
      "id": "14136",
      "label": "索魂影眸｜捕风寻踪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14136.json",
      "key": "weapon:14136:talent:3"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 5.2
      },
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 10.4
      },
      {
        "kind": "def-shred",
        "operation": "add-percent",
        "value": 32.5
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人并造成<color=#2EB6FF>电属性伤害</color>时，目标的防御力降低<color=#2BAD00>32.5%</color>，持续5秒，同名被动效果之间不可叠加；该效果触发时，如果自身不是当前操作中的角色，则装备者获得1层<color=#FFFFFF>[魂锁]</color>，最多叠加3层，同一招式内最多触发一次；每层<color=#FFFFFF>[魂锁]</color>，可使装备者的冲击力提升<color=#2BAD00>5.2%</color>，持续12秒，每层效果单独结算持续时间，<color=#FFFFFF>[魂锁]</color>层数叠满时，额外给装备者的冲击力提升<color=#2BAD00>10.4%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "原文包含多个持续时间：5、12 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14136_talent_4",
    "source": {
      "type": "weapon",
      "id": "14136",
      "label": "索魂影眸｜捕风寻踪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14136.json",
      "key": "weapon:14136:talent:4"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 5.8
      },
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 11.6
      },
      {
        "kind": "def-shred",
        "operation": "add-percent",
        "value": 36.25
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人并造成<color=#2EB6FF>电属性伤害</color>时，目标的防御力降低<color=#2BAD00>36.25%</color>，持续5秒，同名被动效果之间不可叠加；该效果触发时，如果自身不是当前操作中的角色，则装备者获得1层<color=#FFFFFF>[魂锁]</color>，最多叠加3层，同一招式内最多触发一次；每层<color=#FFFFFF>[魂锁]</color>，可使装备者的冲击力提升<color=#2BAD00>5.8%</color>，持续12秒，每层效果单独结算持续时间，<color=#FFFFFF>[魂锁]</color>层数叠满时，额外给装备者的冲击力提升<color=#2BAD00>11.6%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "原文包含多个持续时间：5、12 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14136_talent_5",
    "source": {
      "type": "weapon",
      "id": "14136",
      "label": "索魂影眸｜捕风寻踪",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14136.json",
      "key": "weapon:14136:talent:5"
    },
    "status": "verified",
    "target": "enemy",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 6.4
      },
      {
        "kind": "stat",
        "stat": "impactPct",
        "operation": "add-percent",
        "value": 12.8
      },
      {
        "kind": "def-shred",
        "operation": "add-percent",
        "value": 40
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人并造成<color=#2EB6FF>电属性伤害</color>时，目标的防御力降低<color=#2BAD00>40%</color>，持续5秒，同名被动效果之间不可叠加；该效果触发时，如果自身不是当前操作中的角色，则装备者获得1层<color=#FFFFFF>[魂锁]</color>，最多叠加3层，同一招式内最多触发一次；每层<color=#FFFFFF>[魂锁]</color>，可使装备者的冲击力提升<color=#2BAD00>6.4%</color>，持续12秒，每层效果单独结算持续时间，<color=#FFFFFF>[魂锁]</color>层数叠满时，额外给装备者的冲击力提升<color=#2BAD00>12.8%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 5,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "原文包含多个持续时间：5、12 秒。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；包含同名效果互斥规则，需要加入 exclusiveGroup 或场景级处理。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14137_talent_1",
    "source": {
      "type": "weapon",
      "id": "14137",
      "label": "青溟笼舍｜云流运转",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14137.json",
      "key": "weapon:14137:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>20%</color>；装备者释放<color=#FFFFFF>[强化特殊技]</color>时角色获得1层<color=#FFFFFF>[青溟同行]</color>效果，最多叠加2层，持续15秒，进入接战状态时直接获得2层，重复触发时刷新持续时间；每层<color=#FFFFFF>[青溟同行]</color>效果使装备者造成的<color=#FE437E>以太伤害</color>提升<color=#2BAD00>8%</color>，[终结技]或[强化特殊技]造成的<color=#FE437E>以太贯穿伤害</color>提升<color=#2BAD00>10%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14137_talent_2",
    "source": {
      "type": "weapon",
      "id": "14137",
      "label": "青溟笼舍｜云流运转",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14137.json",
      "key": "weapon:14137:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 9.2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>23%</color>；装备者释放<color=#FFFFFF>[强化特殊技]</color>时角色获得1层<color=#FFFFFF>[青溟同行]</color>效果，最多叠加2层，持续15秒，进入接战状态时直接获得2层，重复触发时刷新持续时间；每层<color=#FFFFFF>[青溟同行]</color>效果使装备者造成的<color=#FE437E>以太伤害</color>提升<color=#2BAD00>9.2%</color>，[终结技]或[强化特殊技]造成的<color=#FE437E>以太贯穿伤害</color>提升<color=#2BAD00>11.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14137_talent_3",
    "source": {
      "type": "weapon",
      "id": "14137",
      "label": "青溟笼舍｜云流运转",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14137.json",
      "key": "weapon:14137:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 10.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>26%</color>；装备者释放<color=#FFFFFF>[强化特殊技]</color>时角色获得1层<color=#FFFFFF>[青溟同行]</color>效果，最多叠加2层，持续15秒，进入接战状态时直接获得2层，重复触发时刷新持续时间；每层<color=#FFFFFF>[青溟同行]</color>效果使装备者造成的<color=#FE437E>以太伤害</color>提升<color=#2BAD00>10.4%</color>，[终结技]或[强化特殊技]造成的<color=#FE437E>以太贯穿伤害</color>提升<color=#2BAD00>13%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14137_talent_4",
    "source": {
      "type": "weapon",
      "id": "14137",
      "label": "青溟笼舍｜云流运转",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14137.json",
      "key": "weapon:14137:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 11.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>29%</color>；装备者释放<color=#FFFFFF>[强化特殊技]</color>时角色获得1层<color=#FFFFFF>[青溟同行]</color>效果，最多叠加2层，持续15秒，进入接战状态时直接获得2层，重复触发时刷新持续时间；每层<color=#FFFFFF>[青溟同行]</color>效果使装备者造成的<color=#FE437E>以太伤害</color>提升<color=#2BAD00>11.6%</color>，[终结技]或[强化特殊技]造成的<color=#FE437E>以太贯穿伤害</color>提升<color=#2BAD00>14.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14137_talent_5",
    "source": {
      "type": "weapon",
      "id": "14137",
      "label": "青溟笼舍｜云流运转",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14137.json",
      "key": "weapon:14137:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "stat",
        "stat": "etherDmgBonus",
        "operation": "add-percent",
        "value": 12.8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "special",
            "ultimate"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>32%</color>；装备者释放<color=#FFFFFF>[强化特殊技]</color>时角色获得1层<color=#FFFFFF>[青溟同行]</color>效果，最多叠加2层，持续15秒，进入接战状态时直接获得2层，重复触发时刷新持续时间；每层<color=#FFFFFF>[青溟同行]</color>效果使装备者造成的<color=#FE437E>以太伤害</color>提升<color=#2BAD00>12.8%</color>，[终结技]或[强化特殊技]造成的<color=#FE437E>以太贯穿伤害</color>提升<color=#2BAD00>16%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14138_talent_1",
    "source": {
      "type": "weapon",
      "id": "14138",
      "label": "牺牲洁纯｜光静花冷",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14138.json",
      "key": "weapon:14138:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 30
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>30%</color>；装备者发动<color=#FFFFFF>[普通攻击]</color> 、<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[追加攻击]</color>命中敌人时，可分别获得1层增益效果，每层增益效果使装备者的暴击伤害额外提升<color=#2BAD00>10%</color>，最多叠加3层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有3层增益效果时，装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>20%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14138_talent_2",
    "source": {
      "type": "weapon",
      "id": "14138",
      "label": "牺牲洁纯｜光静花冷",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14138.json",
      "key": "weapon:14138:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 34.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 23
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>34.5%</color>；装备者发动<color=#FFFFFF>[普通攻击]</color> 、<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[追加攻击]</color>命中敌人时，可分别获得1层增益效果，每层增益效果使装备者的暴击伤害额外提升<color=#2BAD00>11.5%</color>，最多叠加3层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有3层增益效果时，装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>23%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14138_talent_3",
    "source": {
      "type": "weapon",
      "id": "14138",
      "label": "牺牲洁纯｜光静花冷",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14138.json",
      "key": "weapon:14138:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 39
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 26
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>39%</color>；装备者发动<color=#FFFFFF>[普通攻击]</color> 、<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[追加攻击]</color>命中敌人时，可分别获得1层增益效果，每层增益效果使装备者的暴击伤害额外提升<color=#2BAD00>13%</color>，最多叠加3层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有3层增益效果时，装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>26%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14138_talent_4",
    "source": {
      "type": "weapon",
      "id": "14138",
      "label": "牺牲洁纯｜光静花冷",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14138.json",
      "key": "weapon:14138:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 43.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 29
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>43.5%</color>；装备者发动<color=#FFFFFF>[普通攻击]</color> 、<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[追加攻击]</color>命中敌人时，可分别获得1层增益效果，每层增益效果使装备者的暴击伤害额外提升<color=#2BAD00>14.5%</color>，最多叠加3层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有3层增益效果时，装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>29%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14138_talent_5",
    "source": {
      "type": "weapon",
      "id": "14138",
      "label": "牺牲洁纯｜光静花冷",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14138.json",
      "key": "weapon:14138:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 48
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 32
      }
    ],
    "rawDescription": "暴击伤害提升<color=#2BAD00>48%</color>；装备者发动<color=#FFFFFF>[普通攻击]</color> 、<color=#FFFFFF>[特殊技]</color>或<color=#FFFFFF>[追加攻击]</color>命中敌人时，可分别获得1层增益效果，每层增益效果使装备者的暴击伤害额外提升<color=#2BAD00>16%</color>，最多叠加3层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有3层增益效果时，装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>32%</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14139_talent_1",
    "source": {
      "type": "weapon",
      "id": "14139",
      "label": "福虓炉炉｜虎气融融",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14139.json",
      "key": "weapon:14139:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 28,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>造成的失衡值提升<color=#2BAD00>28%</color>；\n发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>并造成<color=#FF5521>火属性伤害</color>时，全队角色造成伤害提升<color=#2BAD00>10%</color>，最多叠加2层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14139_talent_2",
    "source": {
      "type": "weapon",
      "id": "14139",
      "label": "福虓炉炉｜虎气融融",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14139.json",
      "key": "weapon:14139:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 32.2,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>造成的失衡值提升<color=#2BAD00>32.2%</color>；\n发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>并造成<color=#FF5521>火属性伤害</color>时，全队角色造成伤害提升<color=#2BAD00>11.5%</color>，最多叠加2层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14139_talent_3",
    "source": {
      "type": "weapon",
      "id": "14139",
      "label": "福虓炉炉｜虎气融融",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14139.json",
      "key": "weapon:14139:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 36.4,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>造成的失衡值提升<color=#2BAD00>36.4%</color>；\n发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>并造成<color=#FF5521>火属性伤害</color>时，全队角色造成伤害提升<color=#2BAD00>13%</color>，最多叠加2层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14139_talent_4",
    "source": {
      "type": "weapon",
      "id": "14139",
      "label": "福虓炉炉｜虎气融融",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14139.json",
      "key": "weapon:14139:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 40.6,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>造成的失衡值提升<color=#2BAD00>40.6%</color>；\n发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>并造成<color=#FF5521>火属性伤害</color>时，全队角色造成伤害提升<color=#2BAD00>14.5%</color>，最多叠加2层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14139_talent_5",
    "source": {
      "type": "weapon",
      "id": "14139",
      "label": "福虓炉炉｜虎气融融",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14139.json",
      "key": "weapon:14139:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 44.8,
        "scope": {
          "skillCategories": [
            "special",
            "chain",
            "ultimate"
          ],
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>、<color=#FFFFFF>[连携技]</color>和<color=#FFFFFF>[终结技]</color>造成的失衡值提升<color=#2BAD00>44.8%</color>；\n发动<color=#FFFFFF>[连携技]</color>或<color=#FFFFFF>[终结技]</color>并造成<color=#FF5521>火属性伤害</color>时，全队角色造成伤害提升<color=#2BAD00>16%</color>，最多叠加2层，持续30秒，每层效果单独结算持续时间，同一招式内最多触发一次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14141_talent_1",
    "source": {
      "type": "weapon",
      "id": "14141",
      "label": "狸法七变化｜机巧玲珑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14141.json",
      "key": "weapon:14141:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 60
      },
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 30
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#F0D12B>物理伤害</color>时，装备者<color=#FFFFFF>异常掌控</color>提升<color=#2BAD00>30</color>点，持续40秒；装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人时，使全队角色的<color=#FFFFFF>异常精通</color>提升<color=#2BAD00>60</color>点，持续40秒，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 40,
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14141_talent_2",
    "source": {
      "type": "weapon",
      "id": "14141",
      "label": "狸法七变化｜机巧玲珑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14141.json",
      "key": "weapon:14141:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 69
      },
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 34
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#F0D12B>物理伤害</color>时，装备者<color=#FFFFFF>异常掌控</color>提升<color=#2BAD00>34</color>点，持续40秒；装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人时，使全队角色的<color=#FFFFFF>异常精通</color>提升<color=#2BAD00>69</color>点，持续40秒，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 40,
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14141_talent_3",
    "source": {
      "type": "weapon",
      "id": "14141",
      "label": "狸法七变化｜机巧玲珑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14141.json",
      "key": "weapon:14141:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 78
      },
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 39
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#F0D12B>物理伤害</color>时，装备者<color=#FFFFFF>异常掌控</color>提升<color=#2BAD00>39</color>点，持续40秒；装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人时，使全队角色的<color=#FFFFFF>异常精通</color>提升<color=#2BAD00>78</color>点，持续40秒，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 40,
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14141_talent_4",
    "source": {
      "type": "weapon",
      "id": "14141",
      "label": "狸法七变化｜机巧玲珑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14141.json",
      "key": "weapon:14141:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 87
      },
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 43
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#F0D12B>物理伤害</color>时，装备者<color=#FFFFFF>异常掌控</color>提升<color=#2BAD00>43</color>点，持续40秒；装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人时，使全队角色的<color=#FFFFFF>异常精通</color>提升<color=#2BAD00>87</color>点，持续40秒，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 40,
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14141_talent_5",
    "source": {
      "type": "weapon",
      "id": "14141",
      "label": "狸法七变化｜机巧玲珑",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14141.json",
      "key": "weapon:14141:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 96
      },
      {
        "kind": "stat",
        "stat": "anomalyMastery",
        "operation": "add-flat",
        "value": 48
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[终结技]</color>造成<color=#F0D12B>物理伤害</color>时，装备者<color=#FFFFFF>异常掌控</color>提升<color=#2BAD00>48</color>点，持续40秒；装备者的<color=#FFFFFF>[追加攻击]</color>命中敌人时，使全队角色的<color=#FFFFFF>异常精通</color>提升<color=#2BAD00>96</color>点，持续40秒，该效果全队唯一。",
    "trigger": "attack-hit",
    "durationSeconds": 40,
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14143_talent_1",
    "source": {
      "type": "weapon",
      "id": "14143",
      "label": "云霓孤光｜玉魄冰心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14143.json",
      "key": "weapon:14143:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 25
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者造成的伤害无视目标<color=#2BAD00>20%</color><color=#F0D12B>物理属性伤害抗性</color>；装备者开启<color=#FFFFFF>[以太帷幕]</color>时，自身造成的伤害提升<color=#2BAD00>25%</color>，暴击伤害提升<color=#2BAD00>25%</color>，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14143_talent_2",
    "source": {
      "type": "weapon",
      "id": "14143",
      "label": "云霓孤光｜玉魄冰心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14143.json",
      "key": "weapon:14143:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 28.7
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 28.7,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 22,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者造成的伤害无视目标<color=#2BAD00>22%</color><color=#F0D12B>物理属性伤害抗性</color>；装备者开启<color=#FFFFFF>[以太帷幕]</color>时，自身造成的伤害提升<color=#2BAD00>28.7%</color>，暴击伤害提升<color=#2BAD00>28.7%</color>，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14143_talent_3",
    "source": {
      "type": "weapon",
      "id": "14143",
      "label": "云霓孤光｜玉魄冰心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14143.json",
      "key": "weapon:14143:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 32.5
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32.5,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者造成的伤害无视目标<color=#2BAD00>24%</color><color=#F0D12B>物理属性伤害抗性</color>；装备者开启<color=#FFFFFF>[以太帷幕]</color>时，自身造成的伤害提升<color=#2BAD00>32.5%</color>，暴击伤害提升<color=#2BAD00>32.5%</color>，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14143_talent_4",
    "source": {
      "type": "weapon",
      "id": "14143",
      "label": "云霓孤光｜玉魄冰心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14143.json",
      "key": "weapon:14143:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 36.2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 36.2,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 26,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者造成的伤害无视目标<color=#2BAD00>26%</color><color=#F0D12B>物理属性伤害抗性</color>；装备者开启<color=#FFFFFF>[以太帷幕]</color>时，自身造成的伤害提升<color=#2BAD00>36.2%</color>，暴击伤害提升<color=#2BAD00>36.2%</color>，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14143_talent_5",
    "source": {
      "type": "weapon",
      "id": "14143",
      "label": "云霓孤光｜玉魄冰心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14143.json",
      "key": "weapon:14143:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 28,
        "scope": {
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者造成的伤害无视目标<color=#2BAD00>28%</color><color=#F0D12B>物理属性伤害抗性</color>；装备者开启<color=#FFFFFF>[以太帷幕]</color>时，自身造成的伤害提升<color=#2BAD00>40%</color>，暴击伤害提升<color=#2BAD00>40%</color>，持续40秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14145_talent_1",
    "source": {
      "type": "weapon",
      "id": "14145",
      "label": "铸梦炉歌｜月引颂篇",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14145.json",
      "key": "weapon:14145:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.4</color>点/秒；当装备者开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间时，全队角色造成伤害提升<color=#2BAD00>25%</color>，生命值上限提升<color=#2BAD00>15%</color>，效果持续45秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14145_talent_2",
    "source": {
      "type": "weapon",
      "id": "14145",
      "label": "铸梦炉歌｜月引颂篇",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14145.json",
      "key": "weapon:14145:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.46
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 28.8
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.46</color>点/秒；当装备者开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间时，全队角色造成伤害提升<color=#2BAD00>28.8%</color>，生命值上限提升<color=#2BAD00>17.3%</color>，效果持续45秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14145_talent_3",
    "source": {
      "type": "weapon",
      "id": "14145",
      "label": "铸梦炉歌｜月引颂篇",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14145.json",
      "key": "weapon:14145:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.52
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32.5
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.52</color>点/秒；当装备者开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间时，全队角色造成伤害提升<color=#2BAD00>32.5%</color>，生命值上限提升<color=#2BAD00>19.5%</color>，效果持续45秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14145_talent_4",
    "source": {
      "type": "weapon",
      "id": "14145",
      "label": "铸梦炉歌｜月引颂篇",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14145.json",
      "key": "weapon:14145:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.58
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 36.3
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.58</color>点/秒；当装备者开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间时，全队角色造成伤害提升<color=#2BAD00>36.3%</color>，生命值上限提升<color=#2BAD00>21.8%</color>，效果持续45秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14145_talent_5",
    "source": {
      "type": "weapon",
      "id": "14145",
      "label": "铸梦炉歌｜月引颂篇",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14145.json",
      "key": "weapon:14145:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.64
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      }
    ],
    "rawDescription": "装备者的能量自动回复提升<color=#2BAD00>0.64</color>点/秒；当装备者开启<color=#FFFFFF>[以太帷幕]</color>或延长<color=#FFFFFF>[以太帷幕]</color>的持续时间时，全队角色造成伤害提升<color=#2BAD00>40%</color>，生命值上限提升<color=#2BAD00>24%</color>，效果持续45秒，重复触发时刷新持续时间，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14146_talent_1",
    "source": {
      "type": "weapon",
      "id": "14146",
      "label": "机巧心种｜芽生炉心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14146.json",
      "key": "weapon:14146:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 15
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 12.5
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>15%</color>；装备者的<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[强化特殊技]</color>造成伤害时，可分别获得1层增益效果，每层增益效果使装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>12.5%</color>，最多叠加2层，持续40秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有2层增益效果时，装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[终结技]</color>对敌人造成的伤害无视<color=#2BAD00>20%</color>防御力。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14146_talent_2",
    "source": {
      "type": "weapon",
      "id": "14146",
      "label": "机巧心种｜芽生炉心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14146.json",
      "key": "weapon:14146:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 17
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 14.5
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>17%</color>；装备者的<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[强化特殊技]</color>造成伤害时，可分别获得1层增益效果，每层增益效果使装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>14.5%</color>，最多叠加2层，持续40秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有2层增益效果时，装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[终结技]</color>对敌人造成的伤害无视<color=#2BAD00>23%</color>防御力。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14146_talent_3",
    "source": {
      "type": "weapon",
      "id": "14146",
      "label": "机巧心种｜芽生炉心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14146.json",
      "key": "weapon:14146:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 19
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 16.5
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>19%</color>；装备者的<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[强化特殊技]</color>造成伤害时，可分别获得1层增益效果，每层增益效果使装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>16.5%</color>，最多叠加2层，持续40秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有2层增益效果时，装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[终结技]</color>对敌人造成的伤害无视<color=#2BAD00>26%</color>防御力。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14146_talent_4",
    "source": {
      "type": "weapon",
      "id": "14146",
      "label": "机巧心种｜芽生炉心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14146.json",
      "key": "weapon:14146:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 21
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 18.5
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>21%</color>；装备者的<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[强化特殊技]</color>造成伤害时，可分别获得1层增益效果，每层增益效果使装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>18.5%</color>，最多叠加2层，持续40秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有2层增益效果时，装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[终结技]</color>对敌人造成的伤害无视<color=#2BAD00>29%</color>防御力。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14146_talent_5",
    "source": {
      "type": "weapon",
      "id": "14146",
      "label": "机巧心种｜芽生炉心",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14146.json",
      "key": "weapon:14146:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>23%</color>；装备者的<color=#FFFFFF>[普通攻击]</color>、<color=#FFFFFF>[强化特殊技]</color>造成伤害时，可分别获得1层增益效果，每层增益效果使装备者造成的<color=#2EB6FF>电属性伤害</color>提升<color=#2BAD00>20%</color>，最多叠加2层，持续40秒，每层效果单独结算持续时间，同一招式内最多触发一次；拥有2层增益效果时，装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[终结技]</color>对敌人造成的伤害无视<color=#2BAD00>32%</color>防御力。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14147_talent_1",
    "source": {
      "type": "weapon",
      "id": "14147",
      "label": "怒目金刚｜焚心业火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14147.json",
      "key": "weapon:14147:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 9,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>20%</color>；装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者造成的<color=#FF5521>火属性贯穿伤害</color>提升<color=#2BAD00>9%</color>，最多叠加2层，持续20秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14147_talent_2",
    "source": {
      "type": "weapon",
      "id": "14147",
      "label": "怒目金刚｜焚心业火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14147.json",
      "key": "weapon:14147:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10.35,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>23%</color>；装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者造成的<color=#FF5521>火属性贯穿伤害</color>提升<color=#2BAD00>10.35%</color>，最多叠加2层，持续20秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14147_talent_3",
    "source": {
      "type": "weapon",
      "id": "14147",
      "label": "怒目金刚｜焚心业火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14147.json",
      "key": "weapon:14147:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.7,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>26%</color>；装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者造成的<color=#FF5521>火属性贯穿伤害</color>提升<color=#2BAD00>11.7%</color>，最多叠加2层，持续20秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14147_talent_4",
    "source": {
      "type": "weapon",
      "id": "14147",
      "label": "怒目金刚｜焚心业火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14147.json",
      "key": "weapon:14147:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13.05,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>29%</color>；装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者造成的<color=#FF5521>火属性贯穿伤害</color>提升<color=#2BAD00>13.05%</color>，最多叠加2层，持续20秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14147_talent_5",
    "source": {
      "type": "weapon",
      "id": "14147",
      "label": "怒目金刚｜焚心业火",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14147.json",
      "key": "weapon:14147:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.4,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>32%</color>；装备者发动<color=#FFFFFF>[强化特殊技]</color>时，装备者造成的<color=#FF5521>火属性贯穿伤害</color>提升<color=#2BAD00>14.4%</color>，最多叠加2层，持续20秒，每层效果单独结算持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14148_talent_1",
    "source": {
      "type": "weapon",
      "id": "14148",
      "label": "昨夜来电｜7×24",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14148.json",
      "key": "weapon:14148:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 1.5
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 9,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>1.5</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理属性</color>伤害时，装备者攻击造成的失衡值提升<color=#2BAD00>9%</color>，最多叠加3层，持续10秒，叠加到3层时，全队角色暴击伤害额外提升<color=#2BAD00>30%</color>，持续40秒，重复触发时刷新持续时间，暴击伤害提升效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "原文包含多个持续时间：10、40 秒。；涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14148_talent_2",
    "source": {
      "type": "weapon",
      "id": "14148",
      "label": "昨夜来电｜7×24",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14148.json",
      "key": "weapon:14148:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 1.7
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 10.3,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>1.7</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理属性</color>伤害时，装备者攻击造成的失衡值提升<color=#2BAD00>10.3%</color>，最多叠加3层，持续10秒，叠加到3层时，全队角色暴击伤害额外提升<color=#2BAD00>34.5%</color>，持续40秒，重复触发时刷新持续时间，暴击伤害提升效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "原文包含多个持续时间：10、40 秒。；涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14148_talent_3",
    "source": {
      "type": "weapon",
      "id": "14148",
      "label": "昨夜来电｜7×24",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14148.json",
      "key": "weapon:14148:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 1.9
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 11.7,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>1.9</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理属性</color>伤害时，装备者攻击造成的失衡值提升<color=#2BAD00>11.7%</color>，最多叠加3层，持续10秒，叠加到3层时，全队角色暴击伤害额外提升<color=#2BAD00>39%</color>，持续40秒，重复触发时刷新持续时间，暴击伤害提升效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "原文包含多个持续时间：10、40 秒。；涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14148_talent_4",
    "source": {
      "type": "weapon",
      "id": "14148",
      "label": "昨夜来电｜7×24",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14148.json",
      "key": "weapon:14148:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2.1
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>2.1</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理属性</color>伤害时，装备者攻击造成的失衡值提升<color=#2BAD00>13%</color>，最多叠加3层，持续10秒，叠加到3层时，全队角色暴击伤害额外提升<color=#2BAD00>43.5%</color>，持续40秒，重复触发时刷新持续时间，暴击伤害提升效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "原文包含多个持续时间：10、40 秒。；涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14148_talent_5",
    "source": {
      "type": "weapon",
      "id": "14148",
      "label": "昨夜来电｜7×24",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14148.json",
      "key": "weapon:14148:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2.3
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "位于后场时，装备者的能量自动回复提升<color=#2BAD00>2.3</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理属性</color>伤害时，装备者攻击造成的失衡值提升<color=#2BAD00>14.5%</color>，最多叠加3层，持续10秒，叠加到3层时，全队角色暴击伤害额外提升<color=#2BAD00>48%</color>，持续40秒，重复触发时刷新持续时间，暴击伤害提升效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 10,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "原文包含多个持续时间：10、40 秒。；涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14149_talent_1",
    "source": {
      "type": "weapon",
      "id": "14149",
      "label": "思络成歌｜喧响独白",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14149.json",
      "key": "weapon:14149:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.6
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": {
          "type": "per-stack",
          "base": 0,
          "perStack": 12.5
        }
      },
      {
        "kind": "stat",
        "stat": "atkPct",
        "operation": "add-percent",
        "value": {
          "type": "per-stack",
          "base": 0,
          "perStack": 5
        }
      }
    ],
    "rawDescription": "装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.6</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理伤害</color>时，使全队角色获得增益效果：角色造成伤害提升<color=#2BAD00>12.5%</color>，效果持续40秒，最多叠加2层，重复触发时刷新持续时间；拥有2层效果时，角色的攻击力额外提升<color=#2BAD00>10%</color>，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。；规则修订：12.5% 是触发后全队角色造成的伤害，满拐按2层=25%，触发用强化特殊技和物理标签不属于被增伤技能范围。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14149_talent_2",
    "source": {
      "type": "weapon",
      "id": "14149",
      "label": "思络成歌｜喧响独白",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14149.json",
      "key": "weapon:14149:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.69
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.3,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.69</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理伤害</color>时，使全队角色获得增益效果：角色造成伤害提升<color=#2BAD00>14.3%</color>，效果持续40秒，最多叠加2层，重复触发时刷新持续时间；拥有2层效果时，角色的攻击力额外提升<color=#2BAD00>11.5%</color>，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14149_talent_3",
    "source": {
      "type": "weapon",
      "id": "14149",
      "label": "思络成歌｜喧响独白",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14149.json",
      "key": "weapon:14149:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.78
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16.1,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.78</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理伤害</color>时，使全队角色获得增益效果：角色造成伤害提升<color=#2BAD00>16.1%</color>，效果持续40秒，最多叠加2层，重复触发时刷新持续时间；拥有2层效果时，角色的攻击力额外提升<color=#2BAD00>13%</color>，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14149_talent_4",
    "source": {
      "type": "weapon",
      "id": "14149",
      "label": "思络成歌｜喧响独白",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14149.json",
      "key": "weapon:14149:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.87
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.9,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.87</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理伤害</color>时，使全队角色获得增益效果：角色造成伤害提升<color=#2BAD00>17.9%</color>，效果持续40秒，最多叠加2层，重复触发时刷新持续时间；拥有2层效果时，角色的攻击力额外提升<color=#2BAD00>14.5%</color>，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14149_talent_5",
    "source": {
      "type": "weapon",
      "id": "14149",
      "label": "思络成歌｜喧响独白",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14149.json",
      "key": "weapon:14149:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.96
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "physical"
          ]
        }
      }
    ],
    "rawDescription": "装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.96</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#F0D12B>物理伤害</color>时，使全队角色获得增益效果：角色造成伤害提升<color=#2BAD00>20%</color>，效果持续40秒，最多叠加2层，重复触发时刷新持续时间；拥有2层效果时，角色的攻击力额外提升<color=#2BAD00>16%</color>，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14150_talent_1",
    "source": {
      "type": "weapon",
      "id": "14150",
      "label": "壳中之灵｜元气一击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14150.json",
      "key": "weapon:14150:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 90
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>90</color>点；<color=#FE437E>以太属性</color>的装备者进入前场或发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时获得增益效果：对处于属性异常状态下的敌人造成的伤害提升<color=#2BAD00>20%</color>，触发的所有属性异常伤害和[紊乱]伤害提升<color=#2BAD00>10%</color>，效果持续15秒，重复触发时刷新持续时间，换回后场时该效果移除。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14150_talent_2",
    "source": {
      "type": "weapon",
      "id": "14150",
      "label": "壳中之灵｜元气一击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14150.json",
      "key": "weapon:14150:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 103
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 23,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>103</color>点；<color=#FE437E>以太属性</color>的装备者进入前场或发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时获得增益效果：对处于属性异常状态下的敌人造成的伤害提升<color=#2BAD00>23%</color>，触发的所有属性异常伤害和[紊乱]伤害提升<color=#2BAD00>11.5%</color>，效果持续15秒，重复触发时刷新持续时间，换回后场时该效果移除。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14150_talent_3",
    "source": {
      "type": "weapon",
      "id": "14150",
      "label": "壳中之灵｜元气一击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14150.json",
      "key": "weapon:14150:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 117
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 26,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>117</color>点；<color=#FE437E>以太属性</color>的装备者进入前场或发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时获得增益效果：对处于属性异常状态下的敌人造成的伤害提升<color=#2BAD00>26%</color>，触发的所有属性异常伤害和[紊乱]伤害提升<color=#2BAD00>13%</color>，效果持续15秒，重复触发时刷新持续时间，换回后场时该效果移除。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14150_talent_4",
    "source": {
      "type": "weapon",
      "id": "14150",
      "label": "壳中之灵｜元气一击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14150.json",
      "key": "weapon:14150:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 130
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 29,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>130</color>点；<color=#FE437E>以太属性</color>的装备者进入前场或发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时获得增益效果：对处于属性异常状态下的敌人造成的伤害提升<color=#2BAD00>29%</color>，触发的所有属性异常伤害和[紊乱]伤害提升<color=#2BAD00>14.5%</color>，效果持续15秒，重复触发时刷新持续时间，换回后场时该效果移除。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14150_talent_5",
    "source": {
      "type": "weapon",
      "id": "14150",
      "label": "壳中之灵｜元气一击",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14150.json",
      "key": "weapon:14150:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 144
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>144</color>点；<color=#FE437E>以太属性</color>的装备者进入前场或发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时获得增益效果：对处于属性异常状态下的敌人造成的伤害提升<color=#2BAD00>32%</color>，触发的所有属性异常伤害和[紊乱]伤害提升<color=#2BAD00>16%</color>，效果持续15秒，重复触发时刷新持续时间，换回后场时该效果移除。",
    "trigger": "skill-used",
    "durationSeconds": 15,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14151_talent_1",
    "source": {
      "type": "weapon",
      "id": "14151",
      "label": "霓虹妄想｜迪斯科恶魔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14151.json",
      "key": "weapon:14151:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 90
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>90</color>点；装备者<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[普通攻击]</color>造成<color=#FE437E>以太属性伤害</color>时，全队角色造成的伤害提升<color=#2BAD00>15%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>60</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14151_talent_2",
    "source": {
      "type": "weapon",
      "id": "14151",
      "label": "霓虹妄想｜迪斯科恶魔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14151.json",
      "key": "weapon:14151:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 103
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>103</color>点；装备者<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[普通攻击]</color>造成<color=#FE437E>以太属性伤害</color>时，全队角色造成的伤害提升<color=#2BAD00>17%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>69</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14151_talent_3",
    "source": {
      "type": "weapon",
      "id": "14151",
      "label": "霓虹妄想｜迪斯科恶魔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14151.json",
      "key": "weapon:14151:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 117
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 19.5,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>117</color>点；装备者<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[普通攻击]</color>造成<color=#FE437E>以太属性伤害</color>时，全队角色造成的伤害提升<color=#2BAD00>19.5%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>78</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14151_talent_4",
    "source": {
      "type": "weapon",
      "id": "14151",
      "label": "霓虹妄想｜迪斯科恶魔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14151.json",
      "key": "weapon:14151:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 130
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 21,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>130</color>点；装备者<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[普通攻击]</color>造成<color=#FE437E>以太属性伤害</color>时，全队角色造成的伤害提升<color=#2BAD00>21%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>87</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14151_talent_5",
    "source": {
      "type": "weapon",
      "id": "14151",
      "label": "霓虹妄想｜迪斯科恶魔",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14151.json",
      "key": "weapon:14151:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 145
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "skillCategories": [
            "basic",
            "special"
          ],
          "elements": [
            "ether"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>145</color>点；装备者<color=#FFFFFF>[强化特殊技]</color>或<color=#FFFFFF>[普通攻击]</color>造成<color=#FE437E>以太属性伤害</color>时，全队角色造成的伤害提升<color=#2BAD00>24%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者的异常精通额外提升<color=#2BAD00>96</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14152_talent_1",
    "source": {
      "type": "weapon",
      "id": "14152",
      "label": "鳞齿寻踪｜仿生毒素",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14152.json",
      "key": "weapon:14152:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 25
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>25%</color>；装备者单次消耗的能量达到20点时，每消耗20点能量，获得3秒增益效果：造成<color=#2EB6FF>电属性伤害</color>时无视目标<color=#2BAD00>28%</color>防御力；重复获得时，延长持续时间，至多延长至30秒；进入接战状态时，获得10秒该增益；装备者为非当前操作中角色时，持续时间不再减少。",
    "trigger": "skill-used",
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14152_talent_2",
    "source": {
      "type": "weapon",
      "id": "14152",
      "label": "鳞齿寻踪｜仿生毒素",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14152.json",
      "key": "weapon:14152:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28.8
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>28.8%</color>；装备者单次消耗的能量达到20点时，每消耗20点能量，获得3秒增益效果：造成<color=#2EB6FF>电属性伤害</color>时无视目标<color=#2BAD00>31.5%</color>防御力；重复获得时，延长持续时间，至多延长至30秒；进入接战状态时，获得10秒该增益；装备者为非当前操作中角色时，持续时间不再减少。",
    "trigger": "skill-used",
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14152_talent_3",
    "source": {
      "type": "weapon",
      "id": "14152",
      "label": "鳞齿寻踪｜仿生毒素",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14152.json",
      "key": "weapon:14152:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32.5
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>32.5%</color>；装备者单次消耗的能量达到20点时，每消耗20点能量，获得3秒增益效果：造成<color=#2EB6FF>电属性伤害</color>时无视目标<color=#2BAD00>35%</color>防御力；重复获得时，延长持续时间，至多延长至30秒；进入接战状态时，获得10秒该增益；装备者为非当前操作中角色时，持续时间不再减少。",
    "trigger": "skill-used",
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14152_talent_4",
    "source": {
      "type": "weapon",
      "id": "14152",
      "label": "鳞齿寻踪｜仿生毒素",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14152.json",
      "key": "weapon:14152:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 36.3
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>36.3%</color>；装备者单次消耗的能量达到20点时，每消耗20点能量，获得3秒增益效果：造成<color=#2EB6FF>电属性伤害</color>时无视目标<color=#2BAD00>38.5%</color>防御力；重复获得时，延长持续时间，至多延长至30秒；进入接战状态时，获得10秒该增益；装备者为非当前操作中角色时，持续时间不再减少。",
    "trigger": "skill-used",
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14152_talent_5",
    "source": {
      "type": "weapon",
      "id": "14152",
      "label": "鳞齿寻踪｜仿生毒素",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14152.json",
      "key": "weapon:14152:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 40
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>40%</color>；装备者单次消耗的能量达到20点时，每消耗20点能量，获得3秒增益效果：造成<color=#2EB6FF>电属性伤害</color>时无视目标<color=#2BAD00>42%</color>防御力；重复获得时，延长持续时间，至多延长至30秒；进入接战状态时，获得10秒该增益；装备者为非当前操作中角色时，持续时间不再减少。",
    "trigger": "skill-used",
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14153_talent_1",
    "source": {
      "type": "weapon",
      "id": "14153",
      "label": "辉骑面铠｜骑士气势",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14153.json",
      "key": "weapon:14153:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>20%</color>；装备者发动<color=#FFFFFF>[特殊技]</color>时，装备者造成的<color=#F0D12B>物理贯穿伤害</color>提升<color=#2BAD00>10%</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14153_talent_2",
    "source": {
      "type": "weapon",
      "id": "14153",
      "label": "辉骑面铠｜骑士气势",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14153.json",
      "key": "weapon:14153:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>23%</color>；装备者发动<color=#FFFFFF>[特殊技]</color>时，装备者造成的<color=#F0D12B>物理贯穿伤害</color>提升<color=#2BAD00>11.5%</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14153_talent_3",
    "source": {
      "type": "weapon",
      "id": "14153",
      "label": "辉骑面铠｜骑士气势",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14153.json",
      "key": "weapon:14153:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>26%</color>；装备者发动<color=#FFFFFF>[特殊技]</color>时，装备者造成的<color=#F0D12B>物理贯穿伤害</color>提升<color=#2BAD00>13%</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14153_talent_4",
    "source": {
      "type": "weapon",
      "id": "14153",
      "label": "辉骑面铠｜骑士气势",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14153.json",
      "key": "weapon:14153:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.5,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>29%</color>；装备者发动<color=#FFFFFF>[特殊技]</color>时，装备者造成的<color=#F0D12B>物理贯穿伤害</color>提升<color=#2BAD00>14.5%</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14153_talent_5",
    "source": {
      "type": "weapon",
      "id": "14153",
      "label": "辉骑面铠｜骑士气势",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14153.json",
      "key": "weapon:14153:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升<color=#2BAD00>32%</color>；装备者发动<color=#FFFFFF>[特殊技]</color>时，装备者造成的<color=#F0D12B>物理贯穿伤害</color>提升<color=#2BAD00>16%</color>，最多叠加2层，持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14154_talent_1",
    "source": {
      "type": "weapon",
      "id": "14154",
      "label": "朔月裁霜｜终末裁决",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14154.json",
      "key": "weapon:14154:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 35,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性</color>的装备者发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时，自身造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>20%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者造成的<color=#FFFFFF>[异放]</color>伤害额外提升<color=#2BAD00>35%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14154_talent_2",
    "source": {
      "type": "weapon",
      "id": "14154",
      "label": "朔月裁霜｜终末裁决",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14154.json",
      "key": "weapon:14154:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 38.5,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性</color>的装备者发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时，自身造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>23%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者造成的<color=#FFFFFF>[异放]</color>伤害额外提升<color=#2BAD00>38.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14154_talent_3",
    "source": {
      "type": "weapon",
      "id": "14154",
      "label": "朔月裁霜｜终末裁决",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14154.json",
      "key": "weapon:14154:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 42,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性</color>的装备者发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时，自身造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>26%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者造成的<color=#FFFFFF>[异放]</color>伤害额外提升<color=#2BAD00>42%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14154_talent_4",
    "source": {
      "type": "weapon",
      "id": "14154",
      "label": "朔月裁霜｜终末裁决",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14154.json",
      "key": "weapon:14154:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 45.5,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性</color>的装备者发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时，自身造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>29%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者造成的<color=#FFFFFF>[异放]</color>伤害额外提升<color=#2BAD00>45.5%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14154_talent_5",
    "source": {
      "type": "weapon",
      "id": "14154",
      "label": "朔月裁霜｜终末裁决",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14154.json",
      "key": "weapon:14154:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "iceDmgBonus",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 50,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "<color=#98EFF0>冰属性</color>的装备者发动<color=#FFFFFF>[特殊技]</color>、<color=#FFFFFF>[强化特殊技]</color>时，自身造成的<color=#98EFF0>冰属性伤害</color>提升<color=#2BAD00>32%</color>，持续40秒，最多叠加2层，同一招式内最多触发一次，重复触发时刷新持续时间，拥有2层效果时，装备者造成的<color=#FFFFFF>[异放]</color>伤害额外提升<color=#2BAD00>50%</color>。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及动态换算或分段条件，需要确认公式和边界。；涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14155_talent_1",
    "source": {
      "type": "weapon",
      "id": "14155",
      "label": "日冕遗蜕｜日蚀效应",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14155.json",
      "key": "weapon:14155:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升20%；装备者为佩洛伊斯时，发动<color=#FFFFFF>[终结技]</color>获得[日蚀]效果，[日蚀]效果下，装备者造成的伤害无视<color=#2BAD00>16%</color><color=#FE437E>以太伤害抗性</color>，持续45秒，重复触发时刷新持续时间，进入接战状态时，获得[日蚀]效果。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14155_talent_2",
    "source": {
      "type": "weapon",
      "id": "14155",
      "label": "日冕遗蜕｜日蚀效应",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14155.json",
      "key": "weapon:14155:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升20%；装备者为佩洛伊斯时，发动<color=#FFFFFF>[终结技]</color>获得[日蚀]效果，[日蚀]效果下，装备者造成的伤害无视<color=#2BAD00>17.5%</color><color=#FE437E>以太伤害抗性</color>，持续45秒，重复触发时刷新持续时间，进入接战状态时，获得[日蚀]效果。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14155_talent_3",
    "source": {
      "type": "weapon",
      "id": "14155",
      "label": "日冕遗蜕｜日蚀效应",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14155.json",
      "key": "weapon:14155:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升20%；装备者为佩洛伊斯时，发动<color=#FFFFFF>[终结技]</color>获得[日蚀]效果，[日蚀]效果下，装备者造成的伤害无视<color=#2BAD00>19%</color><color=#FE437E>以太伤害抗性</color>，持续45秒，重复触发时刷新持续时间，进入接战状态时，获得[日蚀]效果。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14155_talent_4",
    "source": {
      "type": "weapon",
      "id": "14155",
      "label": "日冕遗蜕｜日蚀效应",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14155.json",
      "key": "weapon:14155:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升20%；装备者为佩洛伊斯时，发动<color=#FFFFFF>[终结技]</color>获得[日蚀]效果，[日蚀]效果下，装备者造成的伤害无视<color=#2BAD00>20.5%</color><color=#FE437E>以太伤害抗性</color>，持续45秒，重复触发时刷新持续时间，进入接战状态时，获得[日蚀]效果。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14155_talent_5",
    "source": {
      "type": "weapon",
      "id": "14155",
      "label": "日冕遗蜕｜日蚀效应",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14155.json",
      "key": "weapon:14155:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 20
      }
    ],
    "rawDescription": "暴击率提升20%；装备者为佩洛伊斯时，发动<color=#FFFFFF>[终结技]</color>获得[日蚀]效果，[日蚀]效果下，装备者造成的伤害无视<color=#2BAD00>22%</color><color=#FE437E>以太伤害抗性</color>，持续45秒，重复触发时刷新持续时间，进入接战状态时，获得[日蚀]效果。",
    "trigger": "skill-used",
    "durationSeconds": 45,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14156_talent_1",
    "source": {
      "type": "weapon",
      "id": "14156",
      "label": "琳琅鎏心｜无懈之礼",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14156.json",
      "key": "weapon:14156:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 70
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 60
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 7,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>70</color>点；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#A6C5FD>风属性伤害</color>时，自身造成的<color=#FFFFFF>[乱流]</color>和<color=#A6C5FD>[风化]</color>伤害提升<color=#2BAD00>7%</color>，持续40秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发一次，拥有2层该效果时，全队代理人的异常精通提升<color=#2BAD00>60</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14156_talent_2",
    "source": {
      "type": "weapon",
      "id": "14156",
      "label": "琳琅鎏心｜无懈之礼",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14156.json",
      "key": "weapon:14156:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 80
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 69
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 8,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>80</color>点；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#A6C5FD>风属性伤害</color>时，自身造成的<color=#FFFFFF>[乱流]</color>和<color=#A6C5FD>[风化]</color>伤害提升<color=#2BAD00>8%</color>，持续40秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发一次，拥有2层该效果时，全队代理人的异常精通提升<color=#2BAD00>69</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14156_talent_3",
    "source": {
      "type": "weapon",
      "id": "14156",
      "label": "琳琅鎏心｜无懈之礼",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14156.json",
      "key": "weapon:14156:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 90
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 78
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 9,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>90</color>点；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#A6C5FD>风属性伤害</color>时，自身造成的<color=#FFFFFF>[乱流]</color>和<color=#A6C5FD>[风化]</color>伤害提升<color=#2BAD00>9%</color>，持续40秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发一次，拥有2层该效果时，全队代理人的异常精通提升<color=#2BAD00>78</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14156_talent_4",
    "source": {
      "type": "weapon",
      "id": "14156",
      "label": "琳琅鎏心｜无懈之礼",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14156.json",
      "key": "weapon:14156:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 100
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 87
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 10,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>100</color>点；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#A6C5FD>风属性伤害</color>时，自身造成的<color=#FFFFFF>[乱流]</color>和<color=#A6C5FD>[风化]</color>伤害提升<color=#2BAD00>10%</color>，持续40秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发一次，拥有2层该效果时，全队代理人的异常精通提升<color=#2BAD00>87</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14156_talent_5",
    "source": {
      "type": "weapon",
      "id": "14156",
      "label": "琳琅鎏心｜无懈之礼",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14156.json",
      "key": "weapon:14156:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 110
      },
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 96
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 11,
        "scope": {
          "skillCategories": [
            "special"
          ]
        }
      }
    ],
    "rawDescription": "装备者的异常精通提升<color=#2BAD00>110</color>点；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#A6C5FD>风属性伤害</color>时，自身造成的<color=#FFFFFF>[乱流]</color>和<color=#A6C5FD>[风化]</color>伤害提升<color=#2BAD00>11%</color>，持续40秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发一次，拥有2层该效果时，全队代理人的异常精通提升<color=#2BAD00>96</color>点，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 40,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14157_talent_1",
    "source": {
      "type": "weapon",
      "id": "14157",
      "label": "首席跟班｜天才的扈从",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14157.json",
      "key": "weapon:14157:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impact",
        "operation": "add-flat",
        "value": 30
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.4
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 12.5,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 15,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的冲击力提升<color=#2BAD00>30</color>点，造成的伤害无视目标<color=#2BAD00>15%</color><color=#FF5521>火属性伤害抗性</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.4</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#FF5521>火属性伤害</color>时，使全队代理人造成的伤害提升<color=#2BAD00>12.5%</color>，持续30秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发1次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14157_talent_2",
    "source": {
      "type": "weapon",
      "id": "14157",
      "label": "首席跟班｜天才的扈从",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14157.json",
      "key": "weapon:14157:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impact",
        "operation": "add-flat",
        "value": 33
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.46
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 14.4,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 17.2,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的冲击力提升<color=#2BAD00>33</color>点，造成的伤害无视目标<color=#2BAD00>17.2%</color><color=#FF5521>火属性伤害抗性</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.46</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#FF5521>火属性伤害</color>时，使全队代理人造成的伤害提升<color=#2BAD00>14.4%</color>，持续30秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发1次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14157_talent_3",
    "source": {
      "type": "weapon",
      "id": "14157",
      "label": "首席跟班｜天才的扈从",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14157.json",
      "key": "weapon:14157:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impact",
        "operation": "add-flat",
        "value": 36
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.52
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 16.3,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 19.5,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的冲击力提升<color=#2BAD00>36</color>点，造成的伤害无视目标<color=#2BAD00>19.5%</color><color=#FF5521>火属性伤害抗性</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.52</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#FF5521>火属性伤害</color>时，使全队代理人造成的伤害提升<color=#2BAD00>16.3%</color>，持续30秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发1次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14157_talent_4",
    "source": {
      "type": "weapon",
      "id": "14157",
      "label": "首席跟班｜天才的扈从",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14157.json",
      "key": "weapon:14157:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impact",
        "operation": "add-flat",
        "value": 39
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.58
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 18.1,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 21.7,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的冲击力提升<color=#2BAD00>39</color>点，造成的伤害无视目标<color=#2BAD00>21.7%</color><color=#FF5521>火属性伤害抗性</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.58</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#FF5521>火属性伤害</color>时，使全队代理人造成的伤害提升<color=#2BAD00>18.1%</color>，持续30秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发1次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14157_talent_5",
    "source": {
      "type": "weapon",
      "id": "14157",
      "label": "首席跟班｜天才的扈从",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14157.json",
      "key": "weapon:14157:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "impact",
        "operation": "add-flat",
        "value": 42
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 0.64
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "skillCategories": [
            "special"
          ],
          "elements": [
            "fire"
          ]
        }
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 24,
        "scope": {
          "elements": [
            "fire"
          ]
        }
      }
    ],
    "rawDescription": "装备者的冲击力提升<color=#2BAD00>42</color>点，造成的伤害无视目标<color=#2BAD00>24%</color><color=#FF5521>火属性伤害抗性</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>0.64</color>点/秒；装备者发动<color=#FFFFFF>[强化特殊技]</color>造成<color=#FF5521>火属性伤害</color>时，使全队代理人造成的伤害提升<color=#2BAD00>20%</color>，持续30秒，最多叠加2层，重复触发时刷新持续时间，同一招式内最多触发1次，该效果全队唯一。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14158_talent_1",
    "source": {
      "type": "weapon",
      "id": "14158",
      "label": "空羽复归之诗｜失乐园",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14158.json",
      "key": "weapon:14158:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 96
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 20
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 30
      }
    ],
    "rawDescription": "异常精通提升<color=#2BAD00>96</color>点；装备者触发<color=#FFA9DD>[异化]</color>反应时，自身获得属性异常伤害提升<color=#2BAD00>20%</color>的效果，并为全队角色施加造成的伤害提升<color=#2BAD00>30%</color>效果，效果均持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14158_talent_2",
    "source": {
      "type": "weapon",
      "id": "14158",
      "label": "空羽复归之诗｜失乐园",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14158.json",
      "key": "weapon:14158:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 105
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 23
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 34.5
      }
    ],
    "rawDescription": "异常精通提升<color=#2BAD00>105</color>点；装备者触发<color=#FFA9DD>[异化]</color>反应时，自身获得属性异常伤害提升<color=#2BAD00>23%</color>的效果，并为全队角色施加造成的伤害提升<color=#2BAD00>34.5%</color>效果，效果均持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14158_talent_3",
    "source": {
      "type": "weapon",
      "id": "14158",
      "label": "空羽复归之诗｜失乐园",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14158.json",
      "key": "weapon:14158:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 115
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 26
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 39
      }
    ],
    "rawDescription": "异常精通提升<color=#2BAD00>115</color>点；装备者触发<color=#FFA9DD>[异化]</color>反应时，自身获得属性异常伤害提升<color=#2BAD00>26%</color>的效果，并为全队角色施加造成的伤害提升<color=#2BAD00>39%</color>效果，效果均持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14158_talent_4",
    "source": {
      "type": "weapon",
      "id": "14158",
      "label": "空羽复归之诗｜失乐园",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14158.json",
      "key": "weapon:14158:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 125
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 29
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 43.5
      }
    ],
    "rawDescription": "异常精通提升<color=#2BAD00>125</color>点；装备者触发<color=#FFA9DD>[异化]</color>反应时，自身获得属性异常伤害提升<color=#2BAD00>29%</color>的效果，并为全队角色施加造成的伤害提升<color=#2BAD00>43.5%</color>效果，效果均持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14158_talent_5",
    "source": {
      "type": "weapon",
      "id": "14158",
      "label": "空羽复归之诗｜失乐园",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14158.json",
      "key": "weapon:14158:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "anomalyProficiency",
        "operation": "add-flat",
        "value": 135
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 48
      }
    ],
    "rawDescription": "异常精通提升<color=#2BAD00>135</color>点；装备者触发<color=#FFA9DD>[异化]</color>反应时，自身获得属性异常伤害提升<color=#2BAD00>32%</color>的效果，并为全队角色施加造成的伤害提升<color=#2BAD00>48%</color>效果，效果均持续30秒，重复触发时刷新持续时间。",
    "trigger": "skill-used",
    "durationSeconds": 30,
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14159_talent_1",
    "source": {
      "type": "weapon",
      "id": "14159",
      "label": "骁骑礼赞｜骑士仪典",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14159.json",
      "key": "weapon:14159:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 32
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 20,
        "scope": {
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[强化特殊技]</color>的重击命中敌人时，获得1层<color=#FFFFFF>[兵锋]</color>，使暴击伤害提升<color=#2BAD00>32%</color>，持续25秒；<color=#FFFFFF>[兵锋]</color>最多叠加2层，且每种招式类型最多提供1层，重复触发时，刷新所有<color=#FFFFFF>[兵锋]</color>持续时间；\n拥有2层<color=#FFFFFF>[兵锋]</color>时，获得<color=#FFFFFF>[彻骨]</color>：装备者造成的伤害无视目标<color=#2BAD00>20%</color><color=#98EFF0>冰属性伤害抗性</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14159_talent_2",
    "source": {
      "type": "weapon",
      "id": "14159",
      "label": "骁骑礼赞｜骑士仪典",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14159.json",
      "key": "weapon:14159:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 36.8
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 23,
        "scope": {
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[强化特殊技]</color>的重击命中敌人时，获得1层<color=#FFFFFF>[兵锋]</color>，使暴击伤害提升<color=#2BAD00>36.8%</color>，持续25秒；<color=#FFFFFF>[兵锋]</color>最多叠加2层，且每种招式类型最多提供1层，重复触发时，刷新所有<color=#FFFFFF>[兵锋]</color>持续时间；\n拥有2层<color=#FFFFFF>[兵锋]</color>时，获得<color=#FFFFFF>[彻骨]</color>：装备者造成的伤害无视目标<color=#2BAD00>23%</color><color=#98EFF0>冰属性伤害抗性</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14159_talent_3",
    "source": {
      "type": "weapon",
      "id": "14159",
      "label": "骁骑礼赞｜骑士仪典",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14159.json",
      "key": "weapon:14159:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 41.6
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 26,
        "scope": {
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[强化特殊技]</color>的重击命中敌人时，获得1层<color=#FFFFFF>[兵锋]</color>，使暴击伤害提升<color=#2BAD00>41.6%</color>，持续25秒；<color=#FFFFFF>[兵锋]</color>最多叠加2层，且每种招式类型最多提供1层，重复触发时，刷新所有<color=#FFFFFF>[兵锋]</color>持续时间；\n拥有2层<color=#FFFFFF>[兵锋]</color>时，获得<color=#FFFFFF>[彻骨]</color>：装备者造成的伤害无视目标<color=#2BAD00>26%</color><color=#98EFF0>冰属性伤害抗性</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14159_talent_4",
    "source": {
      "type": "weapon",
      "id": "14159",
      "label": "骁骑礼赞｜骑士仪典",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14159.json",
      "key": "weapon:14159:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 46.4
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 29,
        "scope": {
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[强化特殊技]</color>的重击命中敌人时，获得1层<color=#FFFFFF>[兵锋]</color>，使暴击伤害提升<color=#2BAD00>46.4%</color>，持续25秒；<color=#FFFFFF>[兵锋]</color>最多叠加2层，且每种招式类型最多提供1层，重复触发时，刷新所有<color=#FFFFFF>[兵锋]</color>持续时间；\n拥有2层<color=#FFFFFF>[兵锋]</color>时，获得<color=#FFFFFF>[彻骨]</color>：装备者造成的伤害无视目标<color=#2BAD00>29%</color><color=#98EFF0>冰属性伤害抗性</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14159_talent_5",
    "source": {
      "type": "weapon",
      "id": "14159",
      "label": "骁骑礼赞｜骑士仪典",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14159.json",
      "key": "weapon:14159:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critDmg",
        "operation": "add-percent",
        "value": 51.2
      },
      {
        "kind": "resistance-ignore",
        "operation": "add-percent",
        "value": 32,
        "scope": {
          "elements": [
            "ice"
          ]
        }
      }
    ],
    "rawDescription": "装备者的<color=#FFFFFF>[普通攻击]</color>和<color=#FFFFFF>[强化特殊技]</color>的重击命中敌人时，获得1层<color=#FFFFFF>[兵锋]</color>，使暴击伤害提升<color=#2BAD00>51.2%</color>，持续25秒；<color=#FFFFFF>[兵锋]</color>最多叠加2层，且每种招式类型最多提供1层，重复触发时，刷新所有<color=#FFFFFF>[兵锋]</color>持续时间；\n拥有2层<color=#FFFFFF>[兵锋]</color>时，获得<color=#FFFFFF>[彻骨]</color>：装备者造成的伤害无视目标<color=#2BAD00>32%</color><color=#98EFF0>冰属性伤害抗性</color>。",
    "trigger": "attack-hit",
    "durationSeconds": 25,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 2,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14161_talent_1",
    "source": {
      "type": "weapon",
      "id": "14161",
      "label": "腥红渴望｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14161.json",
      "key": "weapon:14161:talent:1"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 25
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 7
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 12,
        "scope": {
          "elements": [
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升25%；装备者攻击命中敌人并触发锐爆后，获得1层<color=#FFFFFF>[强化]</color>：\n使自身造成的<color=#2EB6FF>电属性伤害</color>增加7%，持续20秒；最多叠加3层，重复触发时，刷新所有<color=#FFFFFF>[强化]</color>持续时间，每0.1秒最多触发1次；\n拥有3层该效果时，额外使自身造成的<color=#2EB6FF>电属性锐化伤害</color>增加12%。",
    "trigger": "attack-hit",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 1,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14161_talent_2",
    "source": {
      "type": "weapon",
      "id": "14161",
      "label": "腥红渴望｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14161.json",
      "key": "weapon:14161:talent:2"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28.7
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 8
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 13.8,
        "scope": {
          "elements": [
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升28.7%；装备者攻击命中敌人并触发锐爆后，获得1层<color=#FFFFFF>[强化]</color>：\n使自身造成的<color=#2EB6FF>电属性伤害</color>增加8%，持续20秒；最多叠加3层，重复触发时，刷新所有<color=#FFFFFF>[强化]</color>持续时间，每0.1秒最多触发1次；\n拥有3层该效果时，额外使自身造成的<color=#2EB6FF>电属性锐化伤害</color>增加13.8%。",
    "trigger": "attack-hit",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 2,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14161_talent_3",
    "source": {
      "type": "weapon",
      "id": "14161",
      "label": "腥红渴望｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14161.json",
      "key": "weapon:14161:talent:3"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 32.5
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 9
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 15.6,
        "scope": {
          "elements": [
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升32.5%；装备者攻击命中敌人并触发锐爆后，获得1层<color=#FFFFFF>[强化]</color>：\n使自身造成的<color=#2EB6FF>电属性伤害</color>增加9%，持续20秒；最多叠加3层，重复触发时，刷新所有<color=#FFFFFF>[强化]</color>持续时间，每0.1秒最多触发1次；\n拥有3层该效果时，额外使自身造成的<color=#2EB6FF>电属性锐化伤害</color>增加15.6%。",
    "trigger": "attack-hit",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 3,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14161_talent_4",
    "source": {
      "type": "weapon",
      "id": "14161",
      "label": "腥红渴望｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14161.json",
      "key": "weapon:14161:talent:4"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 36.2
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 10
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 17.4,
        "scope": {
          "elements": [
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升36.2%；装备者攻击命中敌人并触发锐爆后，获得1层<color=#FFFFFF>[强化]</color>：\n使自身造成的<color=#2EB6FF>电属性伤害</color>增加10%，持续20秒；最多叠加3层，重复触发时，刷新所有<color=#FFFFFF>[强化]</color>持续时间，每0.1秒最多触发1次；\n拥有3层该效果时，额外使自身造成的<color=#2EB6FF>电属性锐化伤害</color>增加17.4%。",
    "trigger": "attack-hit",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 4,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14161_talent_5",
    "source": {
      "type": "weapon",
      "id": "14161",
      "label": "腥红渴望｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14161.json",
      "key": "weapon:14161:talent:5"
    },
    "status": "verified",
    "target": "self",
    "phase": "combat",
    "timing": "on-trigger",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "stat",
        "stat": "electricDmgBonus",
        "operation": "add-percent",
        "value": 11
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 19.2,
        "scope": {
          "elements": [
            "electric"
          ]
        }
      }
    ],
    "rawDescription": "暴击率提升40%；装备者攻击命中敌人并触发锐爆后，获得1层<color=#FFFFFF>[强化]</color>：\n使自身造成的<color=#2EB6FF>电属性伤害</color>增加11%，持续20秒；最多叠加3层，重复触发时，刷新所有<color=#FFFFFF>[强化]</color>持续时间，每0.1秒最多触发1次；\n拥有3层该效果时，额外使自身造成的<color=#2EB6FF>电属性锐化伤害</color>增加19.2%。",
    "trigger": "attack-hit",
    "durationSeconds": 20,
    "stacks": {
      "mode": "derived",
      "min": 0,
      "max": 3,
      "initial": 0
    },
    "weaponRefinement": 5,
    "notes": "涉及状态刷新、消费、重置或单次攻击归属，需要确认事件顺序。；原文包含多个分句，可能需要拆成多条规则或多个作用对象。；原文声明了叠层上限，但没有明确每层数值与总值关系。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14162_talent_1",
    "source": {
      "type": "weapon",
      "id": "14162",
      "label": "...｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14162.json",
      "key": "weapon:14162:talent:1"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 36
      }
    ],
    "rawDescription": "装备者暴击率提升<color=#2BAD00>28%</color>；造成的伤害无视目标<color=#2BAD00>12%</color><color=#A6C5FD>风属性伤害抗性</color>；造成的失衡值提升<color=#2BAD00>36%</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>2</color>点/秒；\n全队角色造成的伤害提升<color=#2BAD00>40%</color>，该效果全队唯一。",
    "weaponRefinement": 1,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14162_talent_2",
    "source": {
      "type": "weapon",
      "id": "14162",
      "label": "...｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14162.json",
      "key": "weapon:14162:talent:2"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 41.4
      }
    ],
    "rawDescription": "装备者暴击率提升<color=#2BAD00>28%</color>；造成的伤害无视目标<color=#2BAD00>13.8%</color><color=#A6C5FD>风属性伤害抗性</color>；造成的失衡值提升<color=#2BAD00>41.4%</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>2</color>点/秒；\n全队角色造成的伤害提升<color=#2BAD00>40%</color>，该效果全队唯一。",
    "weaponRefinement": 2,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14162_talent_3",
    "source": {
      "type": "weapon",
      "id": "14162",
      "label": "...｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14162.json",
      "key": "weapon:14162:talent:3"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 46.8
      }
    ],
    "rawDescription": "装备者暴击率提升<color=#2BAD00>28%</color>；造成的伤害无视目标<color=#2BAD00>15.6%</color><color=#A6C5FD>风属性伤害抗性</color>；造成的失衡值提升<color=#2BAD00>46.8%</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>2</color>点/秒；\n全队角色造成的伤害提升<color=#2BAD00>40%</color>，该效果全队唯一。",
    "weaponRefinement": 3,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14162_talent_4",
    "source": {
      "type": "weapon",
      "id": "14162",
      "label": "...｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14162.json",
      "key": "weapon:14162:talent:4"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 52.2
      }
    ],
    "rawDescription": "装备者暴击率提升<color=#2BAD00>28%</color>；造成的伤害无视目标<color=#2BAD00>17.4%</color><color=#A6C5FD>风属性伤害抗性</color>；造成的失衡值提升<color=#2BAD00>52.2%</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>2</color>点/秒；\n全队角色造成的伤害提升<color=#2BAD00>40%</color>，该效果全队唯一。",
    "weaponRefinement": 4,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  },
  {
    "schemaVersion": 1,
    "id": "nanoka:weapon_14162_talent_5",
    "source": {
      "type": "weapon",
      "id": "14162",
      "label": "...｜...",
      "provider": "nanoka",
      "version": "3.2.1+17934514",
      "url": "https://static.nanoka.cc/zzz/3.2.1+17934514/zh/weapon/14162.json",
      "key": "weapon:14162:talent:5"
    },
    "status": "verified",
    "target": "all-allies",
    "phase": "combat",
    "timing": "permanent",
    "condition": {
      "type": "always"
    },
    "effects": [
      {
        "kind": "stat",
        "stat": "critRate",
        "operation": "add-percent",
        "value": 28
      },
      {
        "kind": "stat",
        "stat": "energyRegen",
        "operation": "add-flat",
        "value": 2
      },
      {
        "kind": "damage-bonus",
        "operation": "add-percent",
        "value": 40
      },
      {
        "kind": "daze-bonus",
        "operation": "add-percent",
        "value": 57.6
      }
    ],
    "rawDescription": "装备者暴击率提升<color=#2BAD00>28%</color>；造成的伤害无视目标<color=#2BAD00>19.2%</color><color=#A6C5FD>风属性伤害抗性</color>；造成的失衡值提升<color=#2BAD00>57.6%</color>；装备者为非操作中角色时，能量自动回复提升<color=#2BAD00>2</color>点/秒；\n全队角色造成的伤害提升<color=#2BAD00>40%</color>，该效果全队唯一。",
    "weaponRefinement": 5,
    "notes": "自动接收：解析结果无语义警告，已通过 BuffRule 校验。；用户确认：音擎和驱动盘按 Nanoka 当前版本原文直接解析；范围外效果仍由计算范围控制。"
  }
];

export const NANOKA_EQUIPMENT_REVIEWED_RULES_BY_ID: Readonly<Record<string, BuffRule>> =
  Object.fromEntries(NANOKA_EQUIPMENT_REVIEWED_RULES.map((rule) => [rule.id, rule]));
