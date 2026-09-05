"""Human-reviewed Drive Disc set mappings for Nanoka 3.2.4.

Raw names and descriptions stay in ``core.data.drive_discs``.  This table is
the exhaustive disposition manifest: every two-piece and four-piece clause
has a reviewed static/rule/ignored destination.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

from core.types import (
    BuildContributionLayer,
    CharacterStat,
    Element,
)


class DriveDiscClauseDisposition(StrEnum):
    STATIC_CONTRIBUTION = "static-contribution"
    CALCULATION_RULE = "calculation-rule"
    IGNORED_NON_DAMAGE = "ignored-non-damage"


@dataclass(frozen=True, slots=True)
class DriveDiscStaticEffect:
    stat: CharacterStat
    layer: BuildContributionLayer
    value: float
    element: Element | None = None


@dataclass(frozen=True, slots=True)
class DriveDiscReviewedMapping:
    set_id: str
    two_piece_disposition: DriveDiscClauseDisposition
    four_piece_disposition: DriveDiscClauseDisposition
    two_piece_static: DriveDiscStaticEffect | None = None
    two_piece_rule_family: str | None = None
    four_piece_rule_family: str | None = None
    ignored_two_piece_reason: str | None = None
    ignored_four_piece_reason: str | None = None

    def __post_init__(self) -> None:
        if self.two_piece_disposition is DriveDiscClauseDisposition.STATIC_CONTRIBUTION:
            if self.two_piece_static is None:
                raise ValueError("static two-piece mapping requires a contribution")
        elif self.two_piece_disposition is DriveDiscClauseDisposition.CALCULATION_RULE:
            if not self.two_piece_rule_family:
                raise ValueError("rule two-piece mapping requires a rule family")
        elif not self.ignored_two_piece_reason:
            raise ValueError("ignored two-piece mapping requires a reason")
        if self.four_piece_disposition is DriveDiscClauseDisposition.CALCULATION_RULE:
            if not self.four_piece_rule_family:
                raise ValueError("four-piece mapping requires a rule family")
        elif not self.ignored_four_piece_reason:
            raise ValueError("ignored four-piece mapping requires a reason")


S = DriveDiscClauseDisposition.STATIC_CONTRIBUTION
R = DriveDiscClauseDisposition.CALCULATION_RULE
I = DriveDiscClauseDisposition.IGNORED_NON_DAMAGE
PERCENT = BuildContributionLayer.OUT_OF_COMBAT_PERCENT
FLAT = BuildContributionLayer.OUT_OF_COMBAT_FLAT
RATIO = BuildContributionLayer.DIRECT_RATIO


def _static(
    stat: CharacterStat,
    layer: BuildContributionLayer,
    value: float,
    element: Element | None = None,
) -> DriveDiscStaticEffect:
    return DriveDiscStaticEffect(stat, layer, value, element)


DRIVE_DISC_REVIEWED_MAPPINGS: Mapping[str, DriveDiscReviewedMapping] = {
    "31000": DriveDiscReviewedMapping(
        "31000",
        S,
        R,
        _static(CharacterStat.CRIT_RATE, RATIO, 0.08),
        four_piece_rule_family="woodpecker",
    ),
    "31100": DriveDiscReviewedMapping(
        "31100",
        S,
        R,
        _static(CharacterStat.PENETRATION_RATE, RATIO, 0.08),
        four_piece_rule_family="puffer",
    ),
    "31200": DriveDiscReviewedMapping(
        "31200",
        S,
        I,
        _static(CharacterStat.IMPACT, PERCENT, 0.06),
        ignored_four_piece_reason="失衡值提升不改变伤害结算值",
    ),
    "31300": DriveDiscReviewedMapping(
        "31300",
        S,
        I,
        _static(CharacterStat.ANOMALY_PROFICIENCY, FLAT, 30),
        ignored_four_piece_reason="异常积蓄抗性不改变单次伤害结算值",
    ),
    "31400": DriveDiscReviewedMapping(
        "31400",
        S,
        R,
        _static(CharacterStat.ATTACK, PERCENT, 0.10),
        four_piece_rule_family="hormone",
    ),
    "31500": DriveDiscReviewedMapping(
        "31500",
        S,
        I,
        _static(CharacterStat.DEFENSE, PERCENT, 0.16),
        ignored_four_piece_reason="承受伤害降低不属于输出伤害计算",
    ),
    "31600": DriveDiscReviewedMapping(
        "31600",
        S,
        R,
        _static(CharacterStat.ENERGY_REGEN, PERCENT, 0.20),
        four_piece_rule_family="swing",
    ),
    "31800": DriveDiscReviewedMapping(
        "31800",
        S,
        R,
        _static(CharacterStat.ANOMALY_PROFICIENCY, FLAT, 30),
        four_piece_rule_family="chaos-jazz",
    ),
    "31900": DriveDiscReviewedMapping(
        "31900",
        I,
        R,
        ignored_two_piece_reason="护盾量不属于输出伤害计算",
        four_piece_rule_family="proto-punk",
    ),
    "32200": DriveDiscReviewedMapping(
        "32200",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.FIRE),
        four_piece_rule_family="inferno",
    ),
    "32300": DriveDiscReviewedMapping(
        "32300",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ETHER),
        four_piece_rule_family="chaos-metal",
    ),
    "32400": DriveDiscReviewedMapping(
        "32400",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ELECTRIC),
        four_piece_rule_family="thunder",
    ),
    "32500": DriveDiscReviewedMapping(
        "32500",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ICE),
        four_piece_rule_family="polar",
    ),
    "32600": DriveDiscReviewedMapping(
        "32600",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.PHYSICAL),
        four_piece_rule_family="fanged",
    ),
    "32700": DriveDiscReviewedMapping(
        "32700",
        S,
        R,
        _static(CharacterStat.CRIT_DAMAGE, RATIO, 0.16),
        four_piece_rule_family="branch-blade",
    ),
    "32800": DriveDiscReviewedMapping(
        "32800",
        S,
        R,
        _static(CharacterStat.ATTACK, PERCENT, 0.10),
        four_piece_rule_family="astral-voice",
    ),
    "32900": DriveDiscReviewedMapping(
        "32900",
        R,
        R,
        two_piece_rule_family="shadow-2pc",
        four_piece_rule_family="shadow-4pc",
    ),
    "33000": DriveDiscReviewedMapping(
        "33000",
        S,
        R,
        _static(CharacterStat.ANOMALY_MASTERY, PERCENT, 0.08),
        four_piece_rule_family="phaethon",
    ),
    "33100": DriveDiscReviewedMapping(
        "33100",
        S,
        R,
        _static(CharacterStat.HP, PERCENT, 0.10),
        four_piece_rule_family="yunkui",
    ),
    "33200": DriveDiscReviewedMapping(
        "33200",
        I,
        R,
        ignored_two_piece_reason="失衡值提升不改变伤害结算值",
        four_piece_rule_family="summit",
    ),
    "33300": DriveDiscReviewedMapping(
        "33300",
        R,
        R,
        two_piece_rule_family="dawns-bloom-2pc",
        four_piece_rule_family="dawns-bloom-4pc",
    ),
    "33400": DriveDiscReviewedMapping(
        "33400",
        S,
        R,
        _static(CharacterStat.ENERGY_REGEN, PERCENT, 0.20),
        four_piece_rule_family="moonlight",
    ),
    "33500": DriveDiscReviewedMapping(
        "33500",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.PHYSICAL),
        four_piece_rule_family="white-water",
    ),
    "33600": DriveDiscReviewedMapping(
        "33600",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ETHER),
        four_piece_rule_family="shining-aria",
    ),
    "33700": DriveDiscReviewedMapping(
        "33700",
        S,
        R,
        _static(CharacterStat.HP, PERCENT, 0.10),
        four_piece_rule_family="bunny",
    ),
    "33800": DriveDiscReviewedMapping(
        "33800",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ICE),
        four_piece_rule_family="chained-notes",
    ),
    "33900": DriveDiscReviewedMapping(
        "33900",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.WIND),
        four_piece_rule_family="wuthering",
    ),
    "34000": DriveDiscReviewedMapping(
        "34000",
        S,
        R,
        _static(CharacterStat.ELEMENT_DAMAGE_BONUS, RATIO, 0.10, Element.ETHER),
        four_piece_rule_family="sky-ablaze",
    ),
    "34100": DriveDiscReviewedMapping(
        "34100",
        S,
        R,
        _static(CharacterStat.ANOMALY_PROFICIENCY, FLAT, 30),
        four_piece_rule_family="feathered-fate",
    ),
    "34200": DriveDiscReviewedMapping(
        "34200",
        S,
        R,
        _static(CharacterStat.DEFENSE, PERCENT, 0.16),
        four_piece_rule_family="thorned-rose",
    ),
}


__all__ = [
    "DRIVE_DISC_REVIEWED_MAPPINGS",
    "DriveDiscClauseDisposition",
    "DriveDiscReviewedMapping",
    "DriveDiscStaticEffect",
]
