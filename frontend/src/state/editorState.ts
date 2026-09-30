export type EditorState = {
  conditionValues: Record<string, boolean | null>;
  parameterValues: Record<string, number | null>;
  enabledRules: Set<string>;
  disabledRules: Set<string>;
  triggerActors: Record<string, string>;
  stacks: Record<string, number>;
};

export type MoveVariantProjection = {
  optionKey: string;
  entryId: string;
  label: string;
  variantId: string | null;
  variantIndex: number | null;
  conditionIds: string[];
  multiplierRelation: string;
};

type MoveProjectionInput = {
  entry_id: string;
  label: string;
  multiplier_relation: string;
  variants: readonly {
    variant_id?: string;
    label: string;
    condition_ids: readonly string[];
  }[];
};

type VariantConditionView = {
  condition_id: string;
  editable: boolean;
};

/**
 * Project domain MoveView entries into the one dropdown used by the UI.
 *
 * A mutually-exclusive entry contributes one presentation option per
 * multiplier variant.  The option key is intentionally UI-only; the request
 * still carries the original entry ID and its condition values.
 */
export function projectMoveOptions(
  moves: readonly MoveProjectionInput[],
): MoveVariantProjection[] {
  return moves.flatMap<MoveVariantProjection>((move) => {
    if (move.multiplier_relation !== "mutually-exclusive-variant") {
      return [{
        optionKey: move.entry_id,
        entryId: move.entry_id,
        label: move.label,
        variantId: null,
        variantIndex: null,
        conditionIds: [],
        multiplierRelation: move.multiplier_relation,
      }];
    }
    return move.variants.map((variant, variantIndex) => ({
      optionKey: `${move.entry_id}::${variant.variant_id ?? variantIndex}`,
      entryId: move.entry_id,
      label: `${move.label}（${variantDisplayLabel(variant.label)}）`,
      variantId: variant.variant_id ?? null,
      variantIndex,
      conditionIds: [...variant.condition_ids],
      multiplierRelation: move.multiplier_relation,
    }));
  });
}

function variantDisplayLabel(label: string): string {
  const shortened = label.replace(/(?:伤害)?倍率\s*$/, "").trim();
  return shortened || label;
}

/** Return the variants whose condition conjunction is currently true. */
export function matchingMoveVariantIndexes(
  move: MoveProjectionInput,
  values: Readonly<Record<string, boolean | null>>,
): number[] {
  if (move.multiplier_relation !== "mutually-exclusive-variant") return [];
  return move.variants.reduce<number[]>((matches, variant, index) => {
    if (variant.condition_ids.length > 0
      && variant.condition_ids.every((conditionId) => values[conditionId] === true)) {
      matches.push(index);
    }
    return matches;
  }, []);
}

/**
 * Set one move's editable variant conditions atomically.
 *
 * Static condition values are deliberately left untouched.  A shared
 * condition ID is written once from the selected variant's condition set,
 * rather than being overwritten by a later variant in a nested loop.
 */
export function selectMoveVariantConditions(
  previous: Readonly<Record<string, boolean | null>>,
  move: MoveProjectionInput,
  variantIndex: number,
  conditions: readonly VariantConditionView[] = [],
): Record<string, boolean | null> {
  if (move.multiplier_relation !== "mutually-exclusive-variant"
    || !move.variants[variantIndex]) {
    return { ...previous };
  }
  const conditionMetadata = new Map(
    conditions.map((condition) => [condition.condition_id, condition]),
  );
  const allVariantConditionIds = new Set(
    move.variants.flatMap((variant) => variant.condition_ids),
  );
  const selectedConditionIds = new Set(move.variants[variantIndex].condition_ids);
  const next = { ...previous };
  allVariantConditionIds.forEach((conditionId) => {
    const metadata = conditionMetadata.get(conditionId);
    if (metadata && !metadata.editable) return;
    next[conditionId] = selectedConditionIds.has(conditionId);
  });
  return next;
}

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
