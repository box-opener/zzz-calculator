export type TraceDiagnostic = {
  message: string;
  blocking?: boolean;
};

export type TraceEffect = {
  effect_id: string;
  source_label: string | null;
  source_type?: string | null;
  status: string;
  diagnostics?: readonly TraceDiagnostic[];
};

export type TraceRuleMatch = {
  rule_id: string;
  source_label: string | null;
  source_type?: string | null;
  status: string;
  effects: readonly TraceEffect[];
  diagnostics?: readonly TraceDiagnostic[];
};

export type TraceModifier = {
  effect_id: string;
  source_label: string | null;
  source_type?: string | null;
  modifier_path: string;
  value: number | null;
};

export type EventTraceEnvelope = {
  rule_matches: readonly TraceRuleMatch[];
  applied_modifiers: readonly TraceModifier[];
  event_stat_modifiers: readonly TraceModifier[];
  event_multiplier_modifiers: readonly TraceModifier[];
};

export type TraceRuleDefinition = {
  rule_id: string;
  source_label: string;
  source_type?: string;
  availability: string;
  condition_ids: readonly string[];
};

export type TraceConditionDefinition = {
  condition_id: string;
  label: string;
  value: boolean | null;
  editable: boolean;
};

export type DisplayTraceRule = {
  rule_id: string;
  source_label: string;
  source_type?: string | null;
  status: string;
  effects: readonly TraceEffect[];
  diagnostics: readonly TraceDiagnostic[];
  condition_summary: readonly string[];
  synthetic: boolean;
};

type EventTraceDetailsProps = {
  trace: EventTraceEnvelope;
  rules: readonly TraceRuleDefinition[];
  conditions: readonly TraceConditionDefinition[];
  conditionValues: Record<string, boolean | null>;
  enabledRuleIds: ReadonlySet<string>;
  formatNumber: (value: number | null | undefined) => string;
  isEquipmentSource: (sourceType: string | null | undefined) => boolean;
};

const STATUS_LABELS: Record<string, string> = {
  matched: "已匹配",
  blocked: "被阻塞",
  "not-matched": "未命中",
  disabled: "已关闭",
};

function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status;
}

function selectedConditionValue(
  condition: TraceConditionDefinition,
  values: Record<string, boolean | null>,
) {
  return condition.condition_id in values ? values[condition.condition_id] : condition.value;
}

function conditionSummary(
  rule: TraceRuleDefinition | undefined,
  conditions: readonly TraceConditionDefinition[],
  values: Record<string, boolean | null>,
): string[] {
  if (!rule) return [];
  const byId = new Map(conditions.map((condition) => [condition.condition_id, condition]));
  return rule.condition_ids.flatMap((conditionId) => {
    const condition = byId.get(conditionId);
    if (!condition) return [];
    const value = selectedConditionValue(condition, values);
    return `${condition.label}：${value === true ? "是" : value === false ? "否" : "待指定"}`;
  });
}

function diagnosticMessages(...groups: readonly (readonly TraceDiagnostic[] | undefined)[]) {
  return groups.flatMap((group) => group?.map((item) => item.message) ?? []);
}

/**
 * Keep the actual matcher status while retaining context for active scenario
 * conditions whose effects did not enter the event trace. A synthetic row is
 * only a presentation of a RuleItem already returned by the editor view; it is
 * never treated as matched and never contributes a modifier.
 */
export function selectTraceRulesForDisplay(
  trace: EventTraceEnvelope,
  rules: readonly TraceRuleDefinition[],
  conditions: readonly TraceConditionDefinition[],
  conditionValues: Record<string, boolean | null>,
  enabledRuleIds: ReadonlySet<string>,
): DisplayTraceRule[] {
  const definitions = new Map(rules.map((rule) => [rule.rule_id, rule]));
  const activeConditionIds = new Set(
    conditions
      .filter((condition) => selectedConditionValue(condition, conditionValues) === true)
      .map((condition) => condition.condition_id),
  );
  const displayed = new Map<string, DisplayTraceRule>();

  for (const match of trace.rule_matches) {
    const definition = definitions.get(match.rule_id);
    const active = Boolean(definition?.condition_ids.some((id) => activeConditionIds.has(id)));
    if (match.status === "not-matched" && !active) continue;
    const effects = match.effects.length > 0
      ? match.effects
      : [];
    const messages = diagnosticMessages(
      match.diagnostics,
      ...effects.map((effect) => effect.diagnostics),
    );
    displayed.set(match.rule_id, {
      rule_id: match.rule_id,
      source_label: match.source_label ?? definition?.source_label ?? match.rule_id,
      source_type: match.source_type ?? definition?.source_type,
      status: match.status,
      effects,
      diagnostics: messages.map((message) => ({ message })),
      condition_summary: conditionSummary(definition, conditions, conditionValues),
      synthetic: false,
    });
  }

  for (const definition of rules) {
    if (displayed.has(definition.rule_id)) continue;
    const active = definition.condition_ids.some((id) => activeConditionIds.has(id));
    // A blocked rule can be omitted from enabled_rule_item_ids by the editor
    // reconciliation. Preserve its real blocked state in the trace context.
    if (!active || definition.availability !== "blocked") continue;
    const unmet = conditionSummary(definition, conditions, conditionValues)
      .filter((item) => item.endsWith("：否") || item.endsWith("：待指定"));
    displayed.set(definition.rule_id, {
      rule_id: definition.rule_id,
      source_label: definition.source_label,
      source_type: definition.source_type,
      status: "blocked",
      effects: [],
      diagnostics: [{ message: unmet.length > 0 ? `独立条件未满足：${unmet.join("、")}` : "存在未满足的独立条件" }],
      condition_summary: conditionSummary(definition, conditions, conditionValues),
      synthetic: true,
    });
  }

  for (const definition of rules) {
    if (displayed.has(definition.rule_id)) continue;
    const active = definition.condition_ids.some((id) => activeConditionIds.has(id));
    if (!active || definition.availability !== "available" || enabledRuleIds.has(definition.rule_id)) continue;
    displayed.set(definition.rule_id, {
      rule_id: definition.rule_id,
      source_label: definition.source_label,
      source_type: definition.source_type,
      status: "disabled",
      effects: [],
      diagnostics: [{ message: "该 Rule 已由用户关闭" }],
      condition_summary: conditionSummary(definition, conditions, conditionValues),
      synthetic: true,
    });
  }

  return [...displayed.values()];
}

function TraceDiagnosticList({ diagnostics }: { diagnostics: readonly TraceDiagnostic[] }) {
  return diagnostics.length > 0 ? (
    <div className="trace-diagnostics">
      {diagnostics.map((item, index) => <small key={`${item.message}-${index}`}>⚠ {item.message}</small>)}
    </div>
  ) : null;
}

export function EventTraceDetails({
  trace,
  rules,
  conditions,
  conditionValues,
  enabledRuleIds,
  formatNumber,
  isEquipmentSource,
}: EventTraceDetailsProps) {
  const displayedRules = selectTraceRulesForDisplay(
    trace,
    rules,
    conditions,
    conditionValues,
    enabledRuleIds,
  );
  const activeConditions = conditions.filter(
    (condition) => selectedConditionValue(condition, conditionValues) === true,
  );
  const modifiers = [
    ...trace.applied_modifiers,
    ...trace.event_stat_modifiers,
    ...trace.event_multiplier_modifiers,
  ];

  return (
    <div className="application-trace">
      <p className="eyebrow">RULE / EFFECT TRACE</p>
      {activeConditions.length > 0 && (
        <div className="trace-context-row">
          <span>场景状态</span>
          <div>{activeConditions.map((condition) => <strong key={condition.condition_id}>{condition.label}</strong>)}</div>
        </div>
      )}
      {displayedRules.length > 0 ? displayedRules.map((match) => (
        <div className={`trace-match ${match.synthetic ? "trace-match-context" : ""}`} key={match.rule_id}>
          <strong className={isEquipmentSource(match.source_type) ? "equipment-source" : undefined}>{match.source_label}</strong>
          <span className={`trace-status trace-status-${match.status}`}>{statusLabel(match.status)}</span>
          {match.condition_summary.length > 0 && <small className="trace-condition-summary">条件：{match.condition_summary.join(" · ")}</small>}
          {match.effects.map((effect) => (
            <div className="trace-effect-row" key={effect.effect_id}>
              <span>↳ {effect.source_label ?? effect.effect_id}</span>
              <small className={`trace-status trace-status-${effect.status}`}>{statusLabel(effect.status)}</small>
              <TraceDiagnosticList diagnostics={effect.diagnostics ?? []} />
            </div>
          ))}
          <TraceDiagnosticList diagnostics={match.diagnostics} />
          {match.status === "not-matched" && match.effects.length > 0 && match.diagnostics.length === 0 && (
            <small className="trace-explanation">当前事件未满足该 Rule 的效果筛选条件。</small>
          )}
        </div>
      )) : <p className="trace-empty">当前事件没有可展示的已启用 Rule。</p>}
      {modifiers.map((modifier) => (
        <div className="trace-match trace-modifier-row" key={modifier.effect_id}>
          <strong className={isEquipmentSource(modifier.source_type) ? "equipment-source" : undefined}>{modifier.source_label ?? modifier.effect_id}</strong>
          <span>{modifier.modifier_path}</span>
          <small>{formatNumber(modifier.value)}</small>
        </div>
      ))}
    </div>
  );
}

export default EventTraceDetails;
