/** Pure display helpers for values returned by the Build Preview contract. */

export function formatPreviewNumber(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "—"
    : new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 2 }).format(value);
}

export function formatPreviewRatio(value: number | null | undefined): string {
  return value === null || value === undefined
    ? "—"
    : `${formatPreviewNumber(value * 100)}%`;
}

export function formatDriveStatValue(stat: string, value: number): string {
  const ratio = stat.includes("percent")
    || stat === "crit-rate"
    || stat === "crit-damage"
    || stat === "penetration-rate"
    || stat.includes("damage-bonus");
  return ratio ? formatPreviewRatio(value) : formatPreviewNumber(value);
}

export function formatBuildContributionValue(item: {
  value: number | null;
  stat: string;
  layer: string;
}): string {
  if (item.value === null) return "—";
  const ratio = item.layer === "out-of-combat-percent"
    || item.layer === "direct-ratio"
    || ["crit_rate", "crit_damage", "penetration_rate", "element_damage_bonus"].includes(item.stat);
  return ratio
    ? `+${formatPreviewRatio(item.value)}`
    : `+${formatPreviewNumber(item.value)}`;
}
