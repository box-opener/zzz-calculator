export type DisorderDurationMove = {
  damage_type: string;
  element: string | null;
  variants: readonly { parameter_value_id: string | null }[];
};

export type DisorderDurationParameter = {
  parameter_id: string;
  label: string;
  original_text: string;
};

export type DisorderDurationControl = {
  value: number | null;
  maximum: number;
};

export function disorderDurationExtraRuleId(element: string | null): string {
  return element === "ice" || element === "ice:lieshuang"
    ? "rule:character:1541:extra-ability:frost-chill-duration"
    : "rule:character:1501:extra-ability:ether-corrosion-duration";
}

export function isDisorderDurationParameter(
  move: DisorderDurationMove | undefined,
  parameter: DisorderDurationParameter,
): boolean {
  if (!move || move.damage_type !== "disorder" || !["ether", "ether:xuanmo", "ice", "ice:lieshuang"].includes(move.element ?? "")) {
    return false;
  }
  if (!move.variants.some((variant) => variant.parameter_value_id === parameter.parameter_id)) {
    return false;
  }
  const sourceText = `${parameter.label} ${parameter.original_text}`.toLowerCase();
  return /(剩余|remaining)/.test(sourceText)
    && /(秒|second|0\.5|半秒|half)/.test(sourceText);
}

export function disorderDurationControl(
  parameter: DisorderDurationParameter,
  extraEnabled: boolean,
  explicitlySelected: boolean,
  selectedValue: number | null,
  baseDurationSeconds = 10,
): DisorderDurationControl {
  const sourceText = `${parameter.label} ${parameter.original_text}`.toLowerCase();
  const unitsPerSecond = /(半秒|0\.5|half)/.test(sourceText) ? 2 : 1;
  const seconds = baseDurationSeconds + (extraEnabled ? 3 : 0);
  return {
    value: explicitlySelected ? selectedValue : seconds * unitsPerSecond,
    maximum: seconds * unitsPerSecond,
  };
}

export function retainKnownParameterIds(
  selected: ReadonlySet<string>,
  knownParameterIds: ReadonlySet<string>,
): Set<string> {
  return new Set([...selected].filter((parameterId) => knownParameterIds.has(parameterId)));
}
