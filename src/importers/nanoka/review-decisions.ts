import type { BuffRule } from "../../domain/model/buff.js";
import type { NanokaParsedBuff } from "./parse-buff.js";

export type NanokaReviewDecision =
  | { action: "ignore"; reason: string }
  | { action: "promote"; rule?: BuffRule | undefined; rules?: readonly BuffRule[]; reason: string };

export function applyNanokaReviewDecisions(
  parsed: readonly NanokaParsedBuff[],
  decisions: Readonly<Record<string, NanokaReviewDecision>>,
): NanokaParsedBuff[] {
  return parsed.map((item) => {
    const decision = decisions[item.key];
    if (!decision) return item;
    if (decision.action === "ignore") {
      return {
        ...item,
        disposition: "ignored",
        reviewReasons: [decision.reason],
      };
    }
    const rules = decision.rules ?? (decision.rule ? [decision.rule] : item.rules ?? (item.rule ? [item.rule] : []));
    if (rules.length === 0) {
      throw new Error(`人工确认要求提升规则，但没有可用规则：${item.key}`);
    }
    const verifiedRules = rules.map((rule) => ({
      ...rule,
      status: "verified" as const,
      notes: [rule.notes, `人工确认：${decision.reason}`]
        .filter((value): value is string => Boolean(value))
        .join("；"),
    }));
    return {
      ...item,
      status: "parsed",
      rule: verifiedRules[0] as BuffRule,
      ...(verifiedRules.length > 1 ? { rules: verifiedRules } : {}),
      issues: [],
      disposition: "auto-accepted",
      reviewReasons: [],
    };
  });
}
