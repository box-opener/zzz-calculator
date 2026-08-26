"""Typed damage-event templates emitted by reviewed character compilers."""

from dataclasses import dataclass

from core.types import (
    CharacterId,
    CurrentAttackValueSource,
    DamageType,
    Element,
    MoveId,
    StandardCritRule,
)

from ..moves import DamageEventTemplateRef


@dataclass(frozen=True, slots=True)
class DirectDamageEventTemplate:
    ref: DamageEventTemplateRef
    damage_dealer: CharacterId
    element: Element
    base_source: CurrentAttackValueSource
    crit_rule: StandardCritRule
    move_id: MoveId | None

    def __post_init__(self) -> None:
        if self.ref.damage_type is not DamageType.DIRECT:
            raise ValueError("DirectDamageEventTemplate requires direct damage type")
        if self.ref.element is not self.element:
            raise ValueError("template ref element must match typed template element")
        if self.damage_dealer != self.base_source.character_id:
            raise ValueError("base attack source must match damage dealer")
        if self.damage_dealer != self.crit_rule.stat_owner:
            raise ValueError("crit stat owner must match damage dealer")
        if self.ref.skill_group is None and self.move_id is not None:
            raise ValueError(
                "a template with a move_id must have an explicit skill_group"
            )
