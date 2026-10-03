"""Reviewed character panel inputs for the equipment-build presentation.

The combat compilers intentionally do not own character panel numbers.  This
module is the single presentation boundary for the level-60 values used by
Build Assembly.  Astra's packaged record already contains normalized level-60
values.  Ye's values were normalized from the fixed Nanoka 3.2.4 detail
record:

* ``level[6]``: HP 2117 / ATK 241 / DEF 167
* ``extra_level[6]``: base ATK +75 / CRIT +1440 (1/10000 units)
* raw growth fields are applied for levels 1 through 60

The resulting white values are kept in the same normalized shape as Astra's
``stats`` object. Nanoka out-of-combat percentage properties are returned
separately by ``character_base_stat_contributions`` so equipment percentages
add in the same layer. Only level 60 is currently reviewed in the packaged
source records. A different level is rejected instead of silently using a
level-60 panel.
"""

from __future__ import annotations

from collections.abc import Mapping

from core.data.loader import load_character_record
from core.types import (
    BuildContributionLayer,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    CharacterId,
    CharacterStat,
    CharacterStats,
    Element,
    Resolved,
)


BASE_STATS_LEVEL = 60


def character_base_stats(
    character_id: str | CharacterId,
    *,
    level: int = BASE_STATS_LEVEL,
) -> CharacterStats:
    """Return reviewed level-specific base stats for one supported character."""

    if level != BASE_STATS_LEVEL:
        raise ValueError(
            f"reviewed character base stats are only available at level {BASE_STATS_LEVEL}"
        )
    raw = load_character_record(str(character_id))
    stats = raw.get("stats")
    if not isinstance(stats, Mapping):
        raise ValueError(f"character base stats are missing: {character_id}")

    # Astra/Ye use the already normalized review fixture.  New production
    # records are lossless Nanoka detail payloads; normalize their level-60
    # panel from the source's level-1 value, level-50→60 increment, growth
    # curve, and level-60 extra-level values.
    if "atk" in stats:
        def number(key: str) -> float:
            value = stats.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"character base stat {key!r} is not numeric: {character_id}"
                )
            return float(value)
        normalized = {
            "hp": number("hp"),
            "attack": number("atk"),
            "defense": number("def"),
            "impact": number("impact"),
            "crit_rate": number("crit_rate") / 100.0,
            "crit_damage": number("crit_dmg") / 100.0,
            "anomaly_mastery": number("anomaly_mastery"),
            "anomaly_proficiency": number("anomaly_proficiency"),
            "penetration_rate": number("pen_rate"),
            "energy_regen": number("sp_recovery"),
        }
        raw_element = str(raw.get("element", ""))
    else:
        def source_number(key: str) -> float:
            value = stats.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"character base stat {key!r} is not numeric: {character_id}"
                )
            return float(value)

        level_values = raw.get("level")
        if not isinstance(level_values, Mapping):
            raise ValueError(f"character level data is missing: {character_id}")
        level_60 = level_values.get("6")
        if not isinstance(level_60, Mapping):
            raise ValueError(f"character level-60 data is missing: {character_id}")
        extra_values = raw.get("extra_level")
        if not isinstance(extra_values, Mapping):
            raise ValueError(f"character extra-level data is missing: {character_id}")
        extra_60 = extra_values.get("6")
        if not isinstance(extra_60, Mapping):
            raise ValueError(f"character extra level-60 data is missing: {character_id}")
        extra_map = extra_60.get("extra", {})
        if not isinstance(extra_map, Mapping):
            raise ValueError(f"character extra-level values are invalid: {character_id}")

        def level_number(key: str) -> float:
            value = level_60.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(
                    f"character level-60 stat {key!r} is not numeric: {character_id}"
                )
            return float(value)

        def extra_number(prop: str) -> float:
            value = extra_map.get(prop, {})
            if not isinstance(value, Mapping):
                return 0.0
            result = value.get("value", 0.0)
            if isinstance(result, bool) or not isinstance(result, (int, float)):
                raise ValueError(
                    f"character extra stat {prop!r} is not numeric: {character_id}"
                )
            return float(result)

        # Nanoka stores growth in 1/10000 units and level[6] is the
        # level-50→60 increment.  Level 60 therefore has 59 growth steps.
        growth = {
            "hp": source_number("hp_growth") / 10000.0,
            "attack": source_number("attack_growth") / 10000.0,
            "defense": source_number("defence_growth") / 10000.0,
        }
        normalized = {
            "hp": (
                source_number("hp_max")
                + level_number("hp_max")
                + growth["hp"] * 59.0
                + extra_number("11101")
            ),
            "attack": source_number("attack") + level_number("attack") + growth["attack"] * 59.0 + extra_number("12101"),
            "defense": source_number("defence") + level_number("defence") + growth["defense"] * 59.0,
            "impact": source_number("break_stun") + extra_number("12201"),
            "crit_rate": source_number("crit") / 10000.0 + extra_number("20101") / 10000.0,
            "crit_damage": source_number("crit_damage") / 10000.0,
            # Nanoka's names are the inverse of the domain's normalized
            # fields: element_mystery is 异常精通, while
            # element_abnormal_power is 异常掌控.  The extra-level 31401
            # entry is an anomaly-mastery (掌控) flat bonus.
            "anomaly_mastery": source_number("element_abnormal_power") + extra_number("31401"),
            # Nanoka assigns different property IDs to the two anomaly
            # attributes: 31401 is Anomaly Mastery (掌控), while 31201 is
            # Anomaly Proficiency (精通).  Both contribute to the displayed
            # level-60 panel when present on an ascension record.
            "anomaly_proficiency": source_number("element_mystery") + extra_number("31201"),
            "penetration_rate": source_number("pen_rate") / 10000.0,
            "energy_regen": (
                source_number("sp_recover") / 100.0
                + extra_number("30501") / 100.0
            ),
        }
        raw_elements = raw.get("element_type", {})
        if isinstance(raw_elements, Mapping) and raw_elements:
            raw_element = str(next(iter(raw_elements.values())))
        else:
            raw_element = ""

    base_element = _element(raw_element)
    element_bonuses = {base_element: Resolved(0.0)}
    return CharacterStats(
        hp=Resolved(normalized["hp"]),
        attack=Resolved(normalized["attack"]),
        defense=Resolved(normalized["defense"]),
        impact=Resolved(normalized["impact"]),
        crit_rate=Resolved(normalized["crit_rate"]),
        crit_damage=Resolved(normalized["crit_damage"]),
        anomaly_mastery=Resolved(normalized["anomaly_mastery"]),
        anomaly_proficiency=Resolved(normalized["anomaly_proficiency"]),
        penetration_rate=Resolved(normalized["penetration_rate"]),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(normalized["energy_regen"]),
        element_damage_bonus=element_bonuses,
    )


def character_base_stat_contributions(
    character_id: str | CharacterId,
) -> tuple[BuildStatContribution, ...]:
    """Return level-60 character modifiers that belong in Build's percent layer.

    Nanoka property 11102 is an out-of-combat HP percentage.  Keep it separate
    from the white HP value so equipment percentages add in the same layer.
    """

    raw = load_character_record(str(character_id))
    stats = raw.get("stats")
    if not isinstance(stats, Mapping) or "atk" in stats:
        return ()
    extra_values = raw.get("extra_level")
    if not isinstance(extra_values, Mapping):
        return ()
    extra_60 = extra_values.get("6")
    if not isinstance(extra_60, Mapping):
        return ()
    extra_map = extra_60.get("extra", {})
    if not isinstance(extra_map, Mapping):
        return ()
    raw_hp_percent = extra_map.get("11102", {})
    if not isinstance(raw_hp_percent, Mapping):
        return ()
    value = raw_hp_percent.get("value", 0.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"character extra stat '11102' is not numeric: {character_id}")
    percentage = float(value) / 10000.0
    if percentage == 0.0:
        return ()
    owner = CharacterId(str(character_id))
    source = BuildSource(
        source_id=f"{owner}:extra-level-6:11102",
        source_type=BuildSourceType.CHARACTER,
        label="角色额外等级·生命值百分比",
    )
    return (
        BuildStatContribution(
            contribution_id=f"{source.source_id}:hp-percent",
            source=source,
            stat=CharacterStat.HP,
            layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
            value=Resolved(percentage),
        ),
    )


def _element(value: str) -> Element:
    mapping = {
        "物理": Element.PHYSICAL,
        "物理属性": Element.PHYSICAL,
        "physical": Element.PHYSICAL,
        "以太": Element.ETHER,
        "以太属性": Element.ETHER,
        "ether": Element.ETHER,
        "火": Element.FIRE,
        "火属性": Element.FIRE,
        "fire": Element.FIRE,
        "冰": Element.ICE,
        "ice": Element.ICE,
        "冰属性": Element.ICE,
        "电": Element.ELECTRIC,
        "电属性": Element.ELECTRIC,
        "electric": Element.ELECTRIC,
        "风": Element.WIND,
        "风属性": Element.WIND,
        "wind": Element.WIND,
        "明光": Element.LUMINANCE,
        "luminance": Element.LUMINANCE,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported character base element: {value}") from exc


__all__ = [
    "BASE_STATS_LEVEL",
    "character_base_stat_contributions",
    "character_base_stats",
]
