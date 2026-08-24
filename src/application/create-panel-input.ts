import type { CharacterBuild } from "../domain/model/character-build.js";
import type {
  PanelCalculationInput,
  PanelModifier,
} from "../domain/model/panel.js";
import type { StaticDataRegistry } from "../domain/model/static-data.js";
import { evaluatePanelBuffRules } from "../domain/engine/evaluate-buff-rules.js";
import { DRIVE_DISC_2PC_RULES } from "../../data/rules/drive-disc-2pc.js";
import { REVIEWED_DRIVE_DISC_BUFF_RULES } from "../../data/rules/reviewed-buff-registry.js";

export interface CreatePanelInputResult {
  input: PanelCalculationInput;
  warnings: string[];
}

export function createPanelInput(
  build: CharacterBuild,
  registry: StaticDataRegistry,
): CreatePanelInputResult {
  const warnings = [...build.warnings];
  const character = registry.characters[build.character.id];
  if (!character) {
    throw new Error(`静态数据库缺少角色 ${build.character.id}`);
  }

  const modifiers: PanelModifier[] = [];
  let weaponBaseAtk = 0;
  if (build.weapon) {
    const weapon = registry.weapons[build.weapon.id];
    if (!weapon) {
      warnings.push(`静态数据库缺少音擎 ${build.weapon.id}，暂不计入音擎属性。`);
    } else {
      weaponBaseAtk = weapon.baseAtk;
      modifiers.push(...weapon.secondaryModifiers);
    }
  }

  const setCounts = new Map<string, number>();
  for (const disc of build.driveDiscs) {
    if (disc.setId) {
      setCounts.set(disc.setId, (setCounts.get(disc.setId) ?? 0) + 1);
    } else {
      warnings.push(`驱动盘分区 ${disc.slot} 缺少套装 ID。`);
    }

    for (const [kind, stats] of [
      ["main", disc.mainStats],
      ["sub", disc.subStats],
    ] as const) {
      stats.forEach((stat, index) => {
        if (!stat.key || stat.value === undefined) {
          warnings.push(
            `驱动盘分区 ${disc.slot} 的 ${kind} 属性 ${stat.propertyId} 尚未完成单位换算。`,
          );
          return;
        }
        modifiers.push({
          sourceId: `disc:${disc.slot}:${kind}:${index}`,
          label: `驱动盘 ${disc.slot} ${kind === "main" ? "主词条" : "副词条"}`,
          stat: stat.key,
          value: stat.value,
        });
      });
    }
  }

  for (const [setId, count] of setCounts) {
    if (count < 2) continue;
    const setData = registry.driveDiscSets[setId];
    if (!setData) {
      warnings.push(`静态数据库缺少驱动盘套装 ${setId}。`);
      continue;
    }
    const reviewedRules = REVIEWED_DRIVE_DISC_BUFF_RULES.filter((rule) =>
      rule.source.id === setId && rule.phase === "panel" && rule.equippedCountAtLeast === 2,
    );
    const migratedRules = setData.twoPieceRules ??
      (reviewedRules.length > 0 ? reviewedRules : DRIVE_DISC_2PC_RULES[setId]);
    if (migratedRules) {
      const evaluated = evaluatePanelBuffRules(migratedRules);
      modifiers.push(...evaluated.modifiers);
      warnings.push(...evaluated.warnings);
    } else {
      // 兼容尚未迁移的旧静态数据；迁移完成后删除该分支。
      modifiers.push(...setData.twoPieceModifiers);
    }
  }

  return {
    input: {
      character: character.baseStats,
      weaponBaseAtk,
      modifiers,
    },
    warnings,
  };
}
