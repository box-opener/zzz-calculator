export type EditorState = {
  conditionValues: Record<string, boolean | null>;
  parameterValues: Record<string, number | null>;
  enabledRules: Set<string>;
  disabledRules: Set<string>;
  triggerActors: Record<string, string>;
  stacks: Record<string, number>;
};

type ConditionView = {
  condition_id: string;
  value: boolean | null;
  editable: boolean;
};

/**
 * Merge the current user selections with the conditions returned by the
 * authoritative character editor previews.  Static conditions always come
 * from the latest character response; user-selected values are preserved.
 */
export function resolveAuthoritativeConditionContext(
  previous: Record<string, boolean | null>,
  characterConditions: ConditionView[],
): Record<string, boolean | null> {
  const resolved = { ...previous };
  for (const condition of characterConditions) {
    if (!condition.editable || !(condition.condition_id in resolved)) {
      resolved[condition.condition_id] = condition.value;
    }
  }
  return resolved;
}

type ParameterView = {
  parameter_id: string;
  value: number | null;
  minimum: number;
  maximum: number | null;
};

type RuleView = {
  rule_id: string;
  availability: string;
  enabled_by_default: boolean;
  toggleable: boolean;
  stack: { default: number | null; minimum: number | null; maximum: number | null };
};

type TriggerView = {
  input_id: string;
  actor_options: string[];
  selected_actor: string | null;
};

export type EditorStateViews = {
  conditions: ConditionView[];
  parameters: ParameterView[];
  rules: RuleView[];
  triggers: TriggerView[];
};

/**
 * Select the latest known condition values for a calculation request.
 *
 * Editor responses are allowed to arrive with a default value while a user
 * selection is in flight. The local selection is authoritative for editable
 * conditions; static values continue to come from the response. Filtering to
 * the current view also prevents a condition from a previous team from being
 * sent to the API.
 */
export function conditionValuesForViews(
  selected: Record<string, boolean | null>,
  conditions: ConditionView[],
): Record<string, boolean | null> {
  const values: Record<string, boolean | null> = {};
  for (const condition of conditions) {
    if (!condition.editable) continue;
    values[condition.condition_id] = condition.condition_id in selected
      ? selected[condition.condition_id]
      : condition.value;
  }
  return values;
}

export function reconcileEditorState(
  previous: EditorState,
  views: EditorStateViews,
  activeTeam: string[],
): EditorState {
  const conditionValues: Record<string, boolean | null> = {};
  for (const condition of views.conditions) {
    conditionValues[condition.condition_id] = condition.editable
      ? previous.conditionValues[condition.condition_id] ?? condition.value
      : condition.value;
  }

  const parameterValues: Record<string, number | null> = {};
  for (const parameter of views.parameters) {
    const previousValue = previous.parameterValues[parameter.parameter_id];
    const inBounds = previousValue !== undefined
      && previousValue !== null
      && previousValue >= parameter.minimum
      && (parameter.maximum === null || previousValue <= parameter.maximum);
    parameterValues[parameter.parameter_id] = inBounds
      ? previousValue
      : parameter.value;
  }

  const enabledRules = new Set<string>();
  const disabledRules = new Set<string>();
  for (const rule of views.rules) {
    const available = rule.availability === "available" && rule.toggleable;
    // Keep an explicit user-off choice even while a prerequisite condition
    // temporarily makes the rule unavailable. Without this, toggling ARIA (or
    // another prerequisite) back on silently re-enables a rule the user had
    // deliberately disabled.
    if (!available) {
      if (previous.disabledRules.has(rule.rule_id)) {
        disabledRules.add(rule.rule_id);
      }
      continue;
    }
    if (previous.enabledRules.has(rule.rule_id)) {
      enabledRules.add(rule.rule_id);
    } else if (!previous.disabledRules.has(rule.rule_id) && rule.enabled_by_default) {
      enabledRules.add(rule.rule_id);
    } else {
      disabledRules.add(rule.rule_id);
    }
  }

  const triggerActors: Record<string, string> = {};
  for (const trigger of views.triggers) {
    const previousActor = previous.triggerActors[trigger.input_id];
    if (previousActor && activeTeam.includes(previousActor) && trigger.actor_options.includes(previousActor)) {
      triggerActors[trigger.input_id] = previousActor;
    } else if (trigger.selected_actor && activeTeam.includes(trigger.selected_actor) && trigger.actor_options.includes(trigger.selected_actor)) {
      triggerActors[trigger.input_id] = trigger.selected_actor;
    }
  }

  const stacks: Record<string, number> = {};
  for (const rule of views.rules) {
    if (rule.stack.minimum === null || rule.availability !== "available") continue;
    const previousValue = previous.stacks[rule.rule_id];
    if (previousValue !== undefined
      && previousValue >= rule.stack.minimum
      && (rule.stack.maximum === null || previousValue <= rule.stack.maximum)) {
      stacks[rule.rule_id] = previousValue;
    }
  }

  return {
    conditionValues,
    parameterValues,
    enabledRules,
    disabledRules,
    triggerActors,
    stacks,
  };
}
