export type CharacterEditorProjection<R, C, P, T, F> = {
  rule_items: readonly R[];
  scenario_conditions: readonly C[];
  scenario_parameters: readonly P[];
  scenario_trigger_inputs: readonly T[];
  compile_config_fields: readonly F[];
};

export type EquipmentEditorProjection<R, C, P, T> = {
  rule_items: readonly R[];
  scenario_conditions: readonly C[];
  scenario_parameters?: readonly P[];
  scenario_trigger_inputs: readonly T[];
};

export type EditorAggregation<R, C, P, T, F> = {
  ruleItems: R[];
  conditions: C[];
  parameters: P[];
  triggers: T[];
  configFields: { owner: string; field: F }[];
};

type EquipmentRuleControls = {
  rule_id?: string;
  eligibility?: string;
  condition_ids?: readonly string[];
  condition_not_ids?: readonly string[];
};

function eligibleEquipmentControls<R, C, T>(equipment: EquipmentEditorProjection<R, C, unknown, T>) {
  const eligibleRuleIds = new Set<string>();
  const referencedConditionIds = new Set<string>();
  for (const rawRule of equipment.rule_items) {
    const rule = rawRule as unknown as EquipmentRuleControls;
    if (rule.eligibility === "ineligible") continue;
    if (rule.rule_id) eligibleRuleIds.add(rule.rule_id);
    rule.condition_ids?.forEach((conditionId) => referencedConditionIds.add(conditionId));
    rule.condition_not_ids?.forEach((conditionId) => referencedConditionIds.add(conditionId));
  }
  const conditions = equipment.scenario_conditions.filter((rawCondition) => {
    const condition = rawCondition as unknown as { condition_id?: string; id?: string };
    const conditionId = condition.condition_id ?? condition.id;
    return conditionId !== undefined && referencedConditionIds.has(conditionId);
  });
  const triggers = equipment.scenario_trigger_inputs.filter((rawTrigger) => {
    const trigger = rawTrigger as unknown as { rule_item_id?: string | null };
    return trigger.rule_item_id == null || eligibleRuleIds.has(trigger.rule_item_id);
  });
  return { conditions, triggers };
}

/**
 * Merge only active team members, in stable slot order.  This is shared by
 * the UI and its tests so removing a member can never leave an equipment or
 * character rule in the active request projection.
 */
export function aggregateEditorViews<
  R,
  C,
  P,
  T,
  F,
>(
  teamCharacterIds: readonly string[],
  editorViews: Readonly<Record<string, CharacterEditorProjection<R, C, P, T, F> | null | undefined>>,
  wengineViews: Readonly<Record<string, EquipmentEditorProjection<R, C, P, T> | null | undefined>> = {},
  driveDiscViews: Readonly<Record<string, EquipmentEditorProjection<R, C, P, T> | null | undefined>> = {},
): EditorAggregation<R, C, P, T, F> {
  const result: EditorAggregation<R, C, P, T, F> = {
    ruleItems: [],
    conditions: [],
    parameters: [],
    triggers: [],
    configFields: [],
  };
  for (const owner of teamCharacterIds) {
    const character = editorViews[owner];
    if (character) {
      result.ruleItems.push(...character.rule_items);
      result.conditions.push(...character.scenario_conditions);
      result.parameters.push(...character.scenario_parameters);
      result.triggers.push(...character.scenario_trigger_inputs);
      result.configFields.push(...character.compile_config_fields.map((field) => ({ owner, field })));
    }
    for (const equipment of [wengineViews[owner], driveDiscViews[owner]]) {
      if (!equipment) continue;
      const activeControls = eligibleEquipmentControls(equipment);
      result.ruleItems.push(...equipment.rule_items);
      result.conditions.push(...activeControls.conditions);
      result.parameters.push(...equipment.scenario_parameters ?? []);
      result.triggers.push(...activeControls.triggers);
    }
  }
  return result;
}
