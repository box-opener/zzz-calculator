"""Calculation-node identities shared by domain events and calculators."""

from enum import StrEnum


class CalculationNode(StrEnum):
    # Panel and current attributes.
    CHARACTER_BASE_ATTACK = "character.base.attack"
    CHARACTER_ATTACK_WHITE_VALUE = "character.white.attack"
    CHARACTER_INITIAL_HP = "character.initial.hp"
    CHARACTER_INITIAL_ATTACK = "character.initial.attack"
    CHARACTER_INITIAL_DEFENSE = "character.initial.defense"
    CHARACTER_INITIAL_IMPACT = "character.initial.impact"
    CHARACTER_INITIAL_CRIT_RATE = "character.initial.crit-rate"
    CHARACTER_INITIAL_CRIT_DAMAGE = "character.initial.crit-damage"
    CHARACTER_INITIAL_ANOMALY_MASTERY = "character.initial.anomaly-mastery"
    CHARACTER_INITIAL_ANOMALY_PROFICIENCY = "character.initial.anomaly-proficiency"
    CHARACTER_INITIAL_PENETRATION_RATE = "character.initial.penetration-rate"
    CHARACTER_INITIAL_PENETRATION_FLAT = "character.initial.penetration-flat"
    CHARACTER_INITIAL_ENERGY_REGEN = "character.initial.energy-regen"
    CHARACTER_CURRENT_MAX_HP = "character.current.max-hp"
    CHARACTER_CURRENT_ATTACK = "character.current.attack"
    CHARACTER_CURRENT_DEFENSE = "character.current.defense"
    CHARACTER_CURRENT_IMPACT = "character.current.impact"
    CHARACTER_CURRENT_CRIT_RATE = "character.current.crit-rate"
    CHARACTER_CURRENT_CRIT_DAMAGE = "character.current.crit-damage"
    CHARACTER_CURRENT_ANOMALY_MASTERY = "character.current.anomaly-mastery"
    CHARACTER_CURRENT_ANOMALY_PROFICIENCY = "character.current.anomaly-proficiency"
    CHARACTER_CURRENT_PENETRATION_RATE = "character.current.penetration-rate"
    CHARACTER_CURRENT_PENETRATION_FLAT = "character.current.penetration-flat"
    CHARACTER_CURRENT_ENERGY_REGEN = "character.current.energy-regen"
    CHARACTER_CURRENT_ELEMENT_DAMAGE_BONUS = "character.current.element-damage-bonus"
    CHARACTER_COMBAT_HP_PERCENT_BONUS = "character.combat.hp-percent-bonus"
    CHARACTER_COMBAT_HP_FLAT_BONUS = "character.combat.hp-flat-bonus"
    CHARACTER_COMBAT_ATTACK_PERCENT_BONUS = "character.combat.attack-percent-bonus"
    CHARACTER_COMBAT_ATTACK_FLAT_BONUS = "character.combat.attack-flat-bonus"
    CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS = "character.combat.defense-percent-bonus"
    CHARACTER_COMBAT_DEFENSE_FLAT_BONUS = "character.combat.defense-flat-bonus"
    CHARACTER_COMBAT_IMPACT_PERCENT_BONUS = "character.combat.impact-percent-bonus"
    CHARACTER_COMBAT_IMPACT_FLAT_BONUS = "character.combat.impact-flat-bonus"
    CHARACTER_COMBAT_ANOMALY_MASTERY_PERCENT_BONUS = (
        "character.combat.anomaly-mastery-percent-bonus"
    )
    CHARACTER_COMBAT_ANOMALY_MASTERY_FLAT_BONUS = (
        "character.combat.anomaly-mastery-flat-bonus"
    )
    CHARACTER_COMBAT_ANOMALY_PROFICIENCY_PERCENT_BONUS = (
        "character.combat.anomaly-proficiency-percent-bonus"
    )
    CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS = (
        "character.combat.anomaly-proficiency-flat-bonus"
    )
    CHARACTER_COMBAT_ENERGY_REGEN_PERCENT_BONUS = (
        "character.combat.energy-regen-percent-bonus"
    )
    CHARACTER_COMBAT_ENERGY_REGEN_FLAT_BONUS = (
        "character.combat.energy-regen-flat-bonus"
    )

    # Shared damage inputs and regions.
    DAMAGE_SKILL_MULTIPLIER = "damage.skill-multiplier"
    DAMAGE_BASE_VALUE = "damage.base-value"
    DAMAGE_STANDARD_CRIT_REGION = "damage.standard-crit-region"
    DAMAGE_NORMAL_BONUS = "damage.normal-bonus"
    DAMAGE_NORMAL_BONUS_REGION = "damage.normal-bonus-region"
    DAMAGE_SPECIAL_INDEPENDENT_REGION = "damage.special-independent-region"

    # Anomaly effect strength and attribute-anomaly damage.
    ANOMALY_ATTACK_LEVEL_COEFFICIENT = "anomaly.attack-level-coefficient"
    ANOMALY_PROFICIENCY_REGION = "anomaly.proficiency-region"
    ANOMALY_MUTATION_COEFFICIENT = "anomaly.mutation-coefficient"
    ANOMALY_EFFECT_STRENGTH = "anomaly.effect-strength"
    ATTRIBUTE_ANOMALY_MULTIPLIER = "anomaly.attribute.multiplier"
    ANOMALY_CRIT_REGION = "anomaly.attribute.crit-region"
    ANOMALY_DAMAGE_BONUS = "anomaly.attribute.damage-bonus"
    ANOMALY_DAMAGE_BONUS_REGION = "anomaly.attribute.damage-bonus-region"

    # Discharge.
    DISCHARGE_ORIGINAL_ANOMALY_MULTIPLIER = (
        "anomaly.discharge.original-anomaly-multiplier"
    )
    DISCHARGE_MULTIPLIER = "anomaly.discharge.multiplier"
    DISCHARGE_TOTAL_MULTIPLIER = "anomaly.discharge.total-multiplier"
    DISCHARGE_CRIT_REGION = "anomaly.discharge.crit-region"
    DISCHARGE_DAMAGE_BONUS = "anomaly.discharge.damage-bonus"
    DISCHARGE_DAMAGE_BONUS_REGION = "anomaly.discharge.damage-bonus-region"

    # Turbulence.
    TURBULENCE_BASE_MULTIPLIER = "anomaly.turbulence.base-multiplier"
    TURBULENCE_TIME_COMPENSATION_MULTIPLIER = (
        "anomaly.turbulence.time-compensation-multiplier"
    )
    TURBULENCE_EXTRA_MULTIPLIER = "anomaly.turbulence.extra-multiplier"
    TURBULENCE_TOTAL_MULTIPLIER = "anomaly.turbulence.total-multiplier"
    TURBULENCE_CRIT_REGION = "anomaly.turbulence.crit-region"
    TURBULENCE_DAMAGE_BONUS = "anomaly.turbulence.damage-bonus"
    TURBULENCE_DAMAGE_BONUS_REGION = "anomaly.turbulence.damage-bonus-region"

    # Luminance.
    LUMINANCE_MULTIPLIER = "anomaly.luminance.multiplier"
    LUMINANCE_ANOMALY_DAMAGE_BONUS = "anomaly.luminance.anomaly-damage-bonus"
    LUMINANCE_ANOMALY_DAMAGE_BONUS_REGION = (
        "anomaly.luminance.anomaly-damage-bonus-region"
    )

    # Disorder and polar disorder.
    DISORDER_BASE_MULTIPLIER = "disorder.base-multiplier"
    DISORDER_TIME_COMPENSATION_MULTIPLIER = (
        "disorder.time-compensation-multiplier"
    )
    DISORDER_EXTRA_MULTIPLIER = "disorder.extra-multiplier"
    DISORDER_TOTAL_MULTIPLIER = "disorder.total-multiplier"
    DISORDER_TRIGGER_DAMAGE_BONUS = "disorder.trigger.damage-bonus"
    DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS = (
        "disorder.settled-contributor.damage-bonus"
    )
    DISORDER_DAMAGE_BONUS_REGION = "disorder.damage-bonus-region"
    POLAR_DISORDER_MULTIPLIER = "disorder.polar.multiplier"
    POLAR_DISORDER_ADDITIONAL_EQUIVALENT_MULTIPLIER = (
        "disorder.polar.additional-equivalent-multiplier"
    )

    # Penetration damage.
    PENETRATION_FORCE = "penetration.force"
    PENETRATION_DAMAGE_BONUS = "penetration.damage-bonus"
    PENETRATION_DAMAGE_BONUS_REGION = "penetration.damage-bonus-region"

    # Defense.
    DEFENSE_LEVEL_COEFFICIENT = "defense.level-coefficient"
    ENEMY_INITIAL_DEFENSE = "defense.enemy-initial"
    ENEMY_DEFENSE_INCREASE = "defense.enemy-increase"
    ENEMY_DEFENSE_REDUCTION = "defense.enemy-reduction"
    DAMAGE_DEFENSE_IGNORE = "defense.damage-ignore"
    DAMAGE_PENETRATION_RATE = "defense.damage-penetration-rate"
    DAMAGE_PENETRATION_FLAT = "defense.damage-penetration-flat"
    ENEMY_CURRENT_EFFECTIVE_DEFENSE = "defense.enemy-current-effective"
    DAMAGE_DEFENSE_REGION = "defense.region"

    # Resistance.
    ENEMY_INITIAL_RESISTANCE_REGION = "resistance.enemy-initial-region"
    DAMAGE_RESISTANCE_IGNORE = "resistance.damage-ignore"
    ENEMY_RESISTANCE_REDUCTION = "resistance.enemy-reduction"
    DAMAGE_RESISTANCE_REGION = "resistance.region"

    # Vulnerability and damage reduction.
    ENEMY_STUN_VULNERABILITY = "vulnerability.enemy-stun"
    ENEMY_NORMAL_VULNERABILITY = "vulnerability.enemy-normal"
    ENEMY_MOVE_VULNERABILITY = "vulnerability.enemy-move"
    DAMAGE_VULNERABILITY_ADDITIVE_REGION = "vulnerability.additive-region"
    ENEMY_DAMAGE_REDUCTION = "vulnerability.enemy-damage-reduction"
    DAMAGE_REDUCTION_REGION = "vulnerability.reduction-region"
    DAMAGE_BROAD_VULNERABILITY_REGION = "vulnerability.broad-region"

    # Daze, including the independent disorder-daze result.
    DAZE_SKILL_MULTIPLIER = "daze.skill-multiplier"
    DAZE_RESISTANCE_REGION = "daze.resistance-region"
    DAZE_OUTGOING_BONUS = "daze.outgoing-bonus"
    DAZE_OUTGOING_REGION = "daze.outgoing-region"
    DAZE_INCOMING_BONUS = "daze.incoming-bonus"
    DAZE_INCOMING_REGION = "daze.incoming-region"
    DAZE_VALUE = "daze.value"
    DISORDER_IMPACT_LEVEL_COEFFICIENT = "daze.disorder-impact-level-coefficient"
    DISORDER_IMPACT_STRENGTH = "daze.disorder-impact-strength"
    DISORDER_WEIGHTED_IMPACT_STRENGTH = "daze.disorder-weighted-impact-strength"
    DISORDER_DAZE_MULTIPLIER = "daze.disorder-multiplier"
    DISORDER_DAZE_VALUE = "daze.disorder-value"

    # Anomaly buildup.
    ANOMALY_BUILDUP_EFFICIENCY = "anomaly-buildup.efficiency"
    ANOMALY_BUILDUP_MASTERY_REGION = "anomaly-buildup.mastery-region"
    ANOMALY_BUILDUP_SKILL_BASE = "anomaly-buildup.skill-base"
    ANOMALY_BUILDUP_INCREASE = "anomaly-buildup.increase"
    ANOMALY_BUILDUP_REDUCTION = "anomaly-buildup.reduction"
    ANOMALY_BUILDUP_BONUS_REGION = "anomaly-buildup.bonus-region"
    ANOMALY_BUILDUP_RESISTANCE = "anomaly-buildup.resistance"
    ANOMALY_BUILDUP_RESISTANCE_REGION = "anomaly-buildup.resistance-region"
    ANOMALY_BUILDUP_ACTUAL_VALUE = "anomaly-buildup.actual-value"

    # Energy regeneration.
    ENERGY_INITIAL_AUTO_REGEN = "energy.initial-auto-regen"
    ENERGY_RECOVERY_EFFICIENCY = "energy.recovery-efficiency"
    ENERGY_AUTO_REGEN_FLAT = "energy.auto-regen-flat"
    ENERGY_CURRENT_AUTO_REGEN = "energy.current-auto-regen"
