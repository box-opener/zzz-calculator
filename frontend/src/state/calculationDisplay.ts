export function formatMultiplierPercent(value: number): string {
  return `${new Intl.NumberFormat("zh-CN", { maximumFractionDigits: 6 }).format(value * 100)}%`;
}
