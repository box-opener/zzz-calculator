"""Human-reviewed semantics for the Stage18-2 signature W-Engines.

The values and original text stay in the raw fixtures.  This module only
states how those raw fields map into the current domain vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.types import BuildContributionLayer, CharacterStat, WEngineId

from .wengine_ids import WENGINE_ASTRA_ID, WENGINE_YE_ID


@dataclass(frozen=True, slots=True)
class WEngineReviewedMapping:
    wengine_id: WEngineId
    advanced_stat: CharacterStat
    advanced_layer: BuildContributionLayer
    effect_family: str


WENGINE_REVIEWED_MAPPINGS: Mapping[WEngineId, WEngineReviewedMapping] = {
    WENGINE_ASTRA_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_ASTRA_ID,
        advanced_stat=CharacterStat.ATTACK,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="astra-elegant-vanity",
    ),
    WENGINE_YE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_YE_ID,
        advanced_stat=CharacterStat.CRIT_DAMAGE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="ye-cloudcleave-radiance",
    ),
}


def reviewed_mapping_for(wengine_id: WEngineId) -> WEngineReviewedMapping:
    try:
        return WENGINE_REVIEWED_MAPPINGS[wengine_id]
    except KeyError as exc:
        raise ValueError(f"no reviewed mapping for {wengine_id}") from exc


__all__ = [
    "WEngineReviewedMapping",
    "WENGINE_REVIEWED_MAPPINGS",
    "reviewed_mapping_for",
]
