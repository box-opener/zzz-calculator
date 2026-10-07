export function formatMultiplierPercent(value: number): string {
  return `${new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 6 }).format(value * 100)}%`;
}

const CALCULATION_NODE_LABELS: Readonly<Record<string, string>> = {
  "anomaly.effect-strength": "所选异常记录强度",
  "disorder.base-multiplier": "紊乱基础倍率",
  "disorder.time-compensation-multiplier": "剩余时间补偿倍率",
  "disorder.extra-multiplier": "紊乱额外倍率",
  "disorder.total-multiplier": "紊乱倍率合计",
  "disorder.polar.multiplier": "极性紊乱倍率",
  "disorder.polar.ap-coefficient": "极性紊乱异常精通系数",
  "character.current.anomaly-proficiency": "当前异常精通",
  "damage.base-value": "伤害基值（防御前）",
};

export function calculationNodeLabel(node: string): string {
  return CALCULATION_NODE_LABELS[node] ?? node;
}
