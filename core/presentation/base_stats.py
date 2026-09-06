"""Reviewed character panel inputs for the equipment-build presentation.

The combat compilers intentionally do not own character panel numbers.  This
module is the single presentation boundary for the level-60 values used by
Build Assembly.  Astra's packaged record already contains normalized level-60
values.  Ye's values were normalized from the fixed Nanoka 3.2.4 detail
record:

* ``level[6]``: HP 2117 / ATK 241 / DEF 167
* ``extra_level[6]``: base ATK +75 / CRIT +1440 (1/10000 units)
* raw growth fields are applied for levels 1 through 60

The resulting values are kept in the same normalized shape as Astra's
``stats`` object, so the rest of the build pipeline has one input contract.
Only level 60 is currently reviewed in the packaged source records.  A
different level is rejected instead of silently using a level-60 panel.
"""

from __future__ import annotations

from collections.abc import Mapping

from core.data.loader import load_character_record
from core.types import CharacterId, CharacterStats, Element, Resolved


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

    def number(key: str) -> float:
        value = stats.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"character base stat {key!r} is not numeric: {character_id}"
            )
        return float(value)

    base_element = _element(str(raw.get("element", "")))
    element_bonuses = {base_element: Resolved(0.0)}
    return CharacterStats(
        hp=Resolved(number("hp")),
        attack=Resolved(number("atk")),
        defense=Resolved(number("def")),
        impact=Resolved(number("impact")),
        crit_rate=Resolved(number("crit_rate") / 100.0),
        crit_damage=Resolved(number("crit_dmg") / 100.0),
        anomaly_mastery=Resolved(number("anomaly_mastery")),
        anomaly_proficiency=Resolved(number("anomaly_proficiency")),
        penetration_rate=Resolved(number("pen_rate") / 100.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(number("sp_recovery")),
        element_damage_bonus=element_bonuses,
    )


def _element(value: str) -> Element:
    mapping = {
        "物理": Element.PHYSICAL,
        "physical": Element.PHYSICAL,
        "以太": Element.ETHER,
        "ether": Element.ETHER,
        "火": Element.FIRE,
        "fire": Element.FIRE,
        "冰": Element.ICE,
        "ice": Element.ICE,
        "电": Element.ELECTRIC,
        "electric": Element.ELECTRIC,
        "风": Element.WIND,
        "wind": Element.WIND,
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise ValueError(f"unsupported character base element: {value}") from exc


__all__ = ["BASE_STATS_LEVEL", "character_base_stats"]
