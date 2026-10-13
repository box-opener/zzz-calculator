export type EnemyVariant = {
  variant_id: string; code_name: string; base_defense: number; defense_curve: number[]; curve_ratio: number;
  damage_resistance: Record<string, number>; stun_multiplier: number; can_stun: boolean;
};
export type EnemyCatalogEntry = {
  enemy_id: string; display_name: string; rank?: string; faction?: string; default_variant_id?: string;
  variants: EnemyVariant[]; source_url: string; page_url?: string; issue?: string;
};
export type EnemyCatalog = { source_version: string; fetched_at: string; enemies: EnemyCatalogEntry[] };
export function enemyDefenseAtLevel(variant: EnemyVariant, level: number): number {
  return variant.base_defense * variant.defense_curve[level - 1] / variant.curve_ratio;
}
export function enemyStunVulnerabilityBonus(variant: EnemyVariant): number {
  return variant.stun_multiplier - 1;
}
