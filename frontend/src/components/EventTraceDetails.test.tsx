import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import EventTraceDetails, { selectTraceRulesForDisplay, type EventTraceEnvelope, type TraceConditionDefinition, type TraceRuleDefinition } from "./EventTraceDetails";

const aria = "condition:astra:aria-active";
const energy = "condition:astra:energy-derived-active";
const ruleId = "rule:astra:1311:extra-ability-entry";

const conditions: TraceConditionDefinition[] = [
  { condition_id: aria, label: "当前处于咏叹华彩", value: null, editable: true },
  { condition_id: energy, label: "本次场景能量足够触发追加伤害", value: null, editable: true },
];

const rules: TraceRuleDefinition[] = [
  {
    rule_id: ruleId,
    source_label: "额外能力：《月华乱舞》：入场追加",
    source_type: "additional-ability",
    availability: "available",
    condition_ids: [aria, energy],
  },
];

const emptyModifiers = {
  applied_modifiers: [],
  event_stat_modifiers: [],
  event_multiplier_modifiers: [],
};

function trace(status: string, effectStatus: string, message?: string): EventTraceEnvelope {
  return {
    ...emptyModifiers,
    rule_matches: [{
      rule_id: ruleId,
      source_label: rules[0].source_label,
      source_type: rules[0].source_type,
      status,
      effects: [{
        effect_id: "effect:astra:1311:extra-entry-tremolo",
        source_label: "入场追加震音",
        source_type: "additional-ability",
        status: effectStatus,
        diagnostics: message ? [{ message }] : [],
      }],
      diagnostics: [],
    }],
  };
}

const render = (traceData: EventTraceEnvelope, selected: Record<string, boolean | null>) => renderToStaticMarkup(
  <EventTraceDetails
    trace={traceData}
    rules={rules}
    conditions={conditions}
    conditionValues={selected}
    enabledRuleIds={new Set([ruleId])}
    formatNumber={(value) => String(value ?? "—")}
    isEquipmentSource={() => false}
  />,
);

describe("EventTraceDetails", () => {
  it("shows active ARIA and a matched reviewed effect from the production trace", () => {
    const markup = render(trace("matched", "matched"), { [aria]: true, [energy]: true });

    expect(markup).toContain("当前处于咏叹华彩");
    expect(markup).toContain("额外能力：《月华乱舞》：入场追加");
    expect(markup).toContain("入场追加震音");
    expect(markup).toContain("已匹配");
  });

  it("keeps an active ARIA rule visible with an independent blocked-gate diagnostic", () => {
    const markup = render(trace("blocked", "blocked", "Effect trigger has no scenario trigger fact"), { [aria]: true, [energy]: true });

    expect(markup).toContain("当前处于咏叹华彩");
    expect(markup).toContain("被阻塞");
    expect(markup).toContain("Effect trigger has no scenario trigger fact");
  });

  it("does not show ARIA as active when the condition is false", () => {
    const markup = render(trace("not-matched", "not-matched"), { [aria]: false, [energy]: true });

    expect(markup).not.toContain("<strong>当前处于咏叹华彩</strong>");
    expect(markup).toContain("未命中");
  });

  it("shows the applied guaranteed-crit effect with its source Rule", () => {
    const baseTrace = trace("matched", "matched");
    const eventTrace: EventTraceEnvelope = {
      ...baseTrace,
      guaranteed_crit_effect_ids: ["effect:lucia:cinema6:chorus-guaranteed-crit"],
      rule_matches: baseTrace.rule_matches.map((match) => ({
        ...match,
        effects: [{
          effect_id: "effect:lucia:cinema6:chorus-guaranteed-crit",
          source_label: "卢西娅6影：合唱必定暴击",
          source_type: "cinema",
          status: "matched",
          diagnostics: [],
        }],
      })),
    };
    const markup = render(eventTrace, { [aria]: true, [energy]: true });

    expect(markup).toContain("保证暴击");
    expect(markup).toContain("卢西娅6影：合唱必定暴击");
    expect(markup).toContain(ruleId);
    expect(markup).toContain("effect:lucia:cinema6:chorus-guaranteed-crit");
  });

  it("shows a negated scenario fact when its positive field condition is active", () => {
    const fieldAnomaly = "condition:wengine:13009:owner:1401:field-anomaly";
    const targetAnomaly = "condition:wengine:13009:owner:1401:target-anomaly";
    const scopeRule: TraceRuleDefinition = {
      rule_id: "rule:wengine:13009:owner:1401:target-damage-scope-ambiguous",
      source_label: "触电唇彩·目标增伤范围",
      availability: "available",
      condition_ids: [fieldAnomaly],
      condition_not_ids: [targetAnomaly],
    };
    const fieldConditions: TraceConditionDefinition[] = [
      { condition_id: fieldAnomaly, label: "场上有敌人处于异常状态", value: false, editable: true },
      { condition_id: targetAnomaly, label: "本次目标处于异常状态", value: false, editable: true },
    ];
    const fieldTrace: EventTraceEnvelope = {
      ...emptyModifiers,
      rule_matches: [{
        rule_id: scopeRule.rule_id,
        source_label: scopeRule.source_label,
        status: "blocked",
        effects: [],
        diagnostics: [{ message: "target anomaly damage scope is ambiguous", blocking: true }],
      }],
    };
    const displayed = selectTraceRulesForDisplay(
      fieldTrace,
      [scopeRule],
      fieldConditions,
      { [fieldAnomaly]: true, [targetAnomaly]: false },
      new Set([scopeRule.rule_id]),
    );

    expect(displayed).toHaveLength(1);
    expect(displayed[0].status).toBe("blocked");
    expect(displayed[0].condition_summary).toEqual([
      "场上有敌人处于异常状态：是",
      "本次目标处于异常状态：否（本分支要求否）",
    ]);
  });
});
