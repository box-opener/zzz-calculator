"""Closed vocabularies explicitly established by the project specifications."""

from enum import StrEnum


class CharacterRole(StrEnum):
    ATTACK = "attack"
    ANOMALY = "anomaly"
    SUPPORT = "support"
    DEFENSE = "defense"
    STUN = "stun"
    RUPTURE = "rupture"
    VANGUARD = "vanguard"  # 锋御，规范注明未实装


class CharacterStat(StrEnum):
    HP = "hp"
    ATTACK = "attack"
    DEFENSE = "defense"
    IMPACT = "impact"
    CRIT_RATE = "crit-rate"
    CRIT_DAMAGE = "crit-damage"
    ANOMALY_MASTERY = "anomaly-mastery"
    ANOMALY_PROFICIENCY = "anomaly-proficiency"
    PENETRATION_RATE = "penetration-rate"
    PENETRATION_FLAT = "penetration-flat"
    ENERGY_REGEN = "energy-regen"
    ELEMENT_DAMAGE_BONUS = "element-damage-bonus"


class Element(StrEnum):
    FIRE = "fire"
    ELECTRIC = "electric"
    PHYSICAL = "physical"
    ETHER = "ether"
    ICE = "ice"
    WIND = "wind"
    LUMINANCE = "luminance"

    # Keep both the original element and variant identity in one stable value.
    LIESHUANG = "ice:lieshuang"
    XUANMO = "ether:xuanmo"
    LINREN = "physical:linren"


BASE_ELEMENT_BY_ELEMENT: dict[Element, Element] = {
    Element.FIRE: Element.FIRE,
    Element.ELECTRIC: Element.ELECTRIC,
    Element.PHYSICAL: Element.PHYSICAL,
    Element.ETHER: Element.ETHER,
    Element.ICE: Element.ICE,
    Element.WIND: Element.WIND,
    Element.LUMINANCE: Element.LUMINANCE,
    Element.LIESHUANG: Element.ICE,
    Element.XUANMO: Element.ETHER,
    Element.LINREN: Element.PHYSICAL,
}

ANOMALY_ELEMENTS = frozenset(set(Element) - {Element.LUMINANCE})


class DamageType(StrEnum):
    DIRECT = "direct"
    ANOMALY = "anomaly"
    DISORDER = "disorder"
    PENETRATION = "penetration"
    SHARP_EXPLOSION = "sharp-explosion"  # 锐爆，规范注明未实装


class DamageSubtype(StrEnum):
    """Only anomaly damage has settlement subtypes in spec-v1."""

    ATTRIBUTE_ANOMALY = "attribute-anomaly"
    DISCHARGE = "discharge"
    TURBULENCE = "turbulence"
    LUMINANCE = "luminance"


class SkillGroup(StrEnum):
    BASIC_ATTACK = "basic-attack"
    SPECIAL_ATTACK = "special-attack"
    DODGE = "dodge"
    ASSIST = "assist"
    CHAIN_ATTACK = "chain-attack"
    ULTIMATE = "ultimate"


class DamageTag(StrEnum):
    BASIC_ATTACK = "basic-attack-damage"
    SPECIAL_ATTACK = "special-attack-damage"
    EX_SPECIAL_ATTACK = "ex-special-attack-damage"
    DASH_ATTACK = "dash-attack-damage"
    DODGE_COUNTER = "dodge-counter-damage"
    ASSIST = "assist-damage"
    CHAIN_ATTACK = "chain-attack-damage"
    ULTIMATE = "ultimate-damage"
    FOLLOW_UP_ATTACK = "follow-up-attack-damage"
    TREMOLO = "tremolo-damage"
    CLUSTER = "cluster-damage"


class DynamicIdentity(StrEnum):
    CURRENT_OPERATOR = "current-operator"
    DAMAGE_DEALER = "damage-dealer"
    ANOMALY_TRIGGER = "anomaly-trigger"
    ANOMALY_CONTRIBUTORS = "anomaly-contributors"
    DISORDER_TRIGGER = "disorder-trigger"
    WIND_ANOMALY_TRIGGER = "wind-anomaly-trigger"
    LUMINANCE_TRIGGER = "luminance-trigger"
    DISCHARGE_TRIGGER = "discharge-trigger"
    SUPPORT_ENTRY_CHARACTER = "support-entry-character"


class EffectTarget(StrEnum):
    """Dynamic identities intentionally do not belong to this enum."""

    SELF = "self"
    TEAM = "team"
    TEAM_OTHER = "team-other"
    ENEMY = "enemy"


class AttributeAnomalyDamageKind(StrEnum):
    ASSAULT = "assault"
    SHATTER = "shatter"
    BURN = "burn"
    SHOCK = "shock"
    CORRUPTION = "corruption"
    WEATHERING = "weathering"


class AttributeAnomalyStateKind(StrEnum):
    FLINCH = "flinch"
    FROSTBITE = "frostbite"
    LIESHUANG_FROSTBITE = "lieshuang-frostbite"
    BURN = "burn"
    SHOCK = "shock"
    CORRUPTION = "corruption"
    WEATHERING = "weathering"


ANOMALY_DAMAGE_KIND_BY_ELEMENT: dict[Element, AttributeAnomalyDamageKind] = {
    Element.PHYSICAL: AttributeAnomalyDamageKind.ASSAULT,
    Element.LINREN: AttributeAnomalyDamageKind.ASSAULT,
    Element.ICE: AttributeAnomalyDamageKind.SHATTER,
    Element.LIESHUANG: AttributeAnomalyDamageKind.SHATTER,
    Element.FIRE: AttributeAnomalyDamageKind.BURN,
    Element.ELECTRIC: AttributeAnomalyDamageKind.SHOCK,
    Element.ETHER: AttributeAnomalyDamageKind.CORRUPTION,
    Element.XUANMO: AttributeAnomalyDamageKind.CORRUPTION,
    Element.WIND: AttributeAnomalyDamageKind.WEATHERING,
}

ANOMALY_STATE_KIND_BY_ELEMENT: dict[Element, AttributeAnomalyStateKind] = {
    Element.PHYSICAL: AttributeAnomalyStateKind.FLINCH,
    Element.LINREN: AttributeAnomalyStateKind.FLINCH,
    Element.ICE: AttributeAnomalyStateKind.FROSTBITE,
    Element.LIESHUANG: AttributeAnomalyStateKind.LIESHUANG_FROSTBITE,
    Element.FIRE: AttributeAnomalyStateKind.BURN,
    Element.ELECTRIC: AttributeAnomalyStateKind.SHOCK,
    Element.ETHER: AttributeAnomalyStateKind.CORRUPTION,
    Element.XUANMO: AttributeAnomalyStateKind.CORRUPTION,
    Element.WIND: AttributeAnomalyStateKind.WEATHERING,
}


class BattleEventKind(StrEnum):
    SKILL_HIT = "skill-hit"
    DAMAGE = "damage"
    DAZE = "daze"
    ANOMALY_BUILDUP = "anomaly-buildup"
    ANOMALY_TRIGGER = "anomaly-trigger"
    DISORDER_TRIGGER = "disorder-trigger"
    TURBULENCE_TRIGGER = "turbulence-trigger"
    DISCHARGE_TRIGGER = "discharge-trigger"
    LUMINANCE_TRIGGER = "luminance-trigger"
    RESOURCE_CHANGE = "resource-change"
    STATE_CHANGE = "state-change"
    FINISHER = "finisher"
    SUPPORT_ENTRY = "support-entry"


class EffectOperation(StrEnum):
    ADD = "add"
    MULTIPLY = "multiply"
    SET = "set"
    OVERRIDE = "override"
    CAP = "cap"


class EffectSourceType(StrEnum):
    CORE_PASSIVE = "core-passive"
    ADDITIONAL_ABILITY = "additional-ability"
    SKILL = "skill"
    CINEMA = "cinema"
    WEAPON = "weapon"
    DRIVE_DISC = "drive-disc"
    STATE = "state"
    SPECIAL_MECHANISM = "special-mechanism"


class StateKind(StrEnum):
    BUFF = "buff"
    DEBUFF = "debuff"
    ATTRIBUTE_ANOMALY = "attribute-anomaly"
    STUN = "stun"
    ENVIRONMENT = "environment"
    OTHER = "other"


class SnapshotRule(StrEnum):
    LIVE = "live"
    EFFECT_TRIGGER = "effect-trigger"
    ANOMALY_BUILDUP = "anomaly-buildup"
    ANOMALY_TRIGGER = "anomaly-trigger"
    SETTLEMENT = "settlement"
    INHERITED = "inherited"


class FieldPosition(StrEnum):
    FRONT = "front"
    BACK = "back"


class OperationState(StrEnum):
    OPERATED = "operated"
    NOT_OPERATED = "not-operated"


class StateChangeAction(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    REFRESH = "refresh"
    REMOVE = "remove"


class ResourceKind(StrEnum):
    ENERGY = "energy"
    FLASH_ENERGY = "flash-energy"
