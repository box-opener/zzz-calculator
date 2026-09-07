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
      result.ruleItems.push(...equipment.rule_items);
      result.conditions.push(...equipment.scenario_conditions);
      result.parameters.push(...equipment.scenario_parameters ?? []);
      result.triggers.push(...equipment.scenario_trigger_inputs);
    }
  }
  return result;
}
