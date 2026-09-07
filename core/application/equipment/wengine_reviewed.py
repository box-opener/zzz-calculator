"""Human-reviewed semantics for the Stage18-2 signature W-Engines.

The values and original text stay in the raw fixtures.  This module only
states how those raw fields map into the current domain vocabulary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from core.types import BuildContributionLayer, CharacterStat, WEngineId

from .wengine_ids import (
    WENGINE_ASTRA_ID,
    WENGINE_BRIMSTONE_ID,
    WENGINE_CRYING_CRADLE_ID,
    WENGINE_DEEP_SEA_VISITOR_ID,
    WENGINE_DEFENSE_PATROL_ID,
    WENGINE_DREAM_FORGE_ID,
    WENGINE_HEART_OF_SWORD_ID,
    WENGINE_RESONAB_THREE_ID,
    WENGINE_SONG_OF_NOISE_ID,
    WENGINE_STEEL_CUSHION_ID,
    WENGINE_TREASURE_CHEST_ID,
    WENGINE_TRIGGER_ID,
    WENGINE_ALICE_ID,
    WENGINE_YUZUHA_ID,
    WENGINE_YE_ID,
)


@dataclass(frozen=True, slots=True)
class WEngineReviewedMapping:
    wengine_id: WEngineId
    advanced_stat: CharacterStat
    advanced_layer: BuildContributionLayer
    effect_family: str


WENGINE_REVIEWED_MAPPINGS: Mapping[WEngineId, WEngineReviewedMapping] = {
    WENGINE_RESONAB_THREE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_RESONAB_THREE_ID,
        advanced_stat=CharacterStat.HP,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="support-resonab-3",
    ),
    WENGINE_TREASURE_CHEST_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_TREASURE_CHEST_ID,
        advanced_stat=CharacterStat.ENERGY_REGEN,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="support-treasure-chest",
    ),
    WENGINE_ASTRA_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_ASTRA_ID,
        advanced_stat=CharacterStat.ATTACK,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="astra-elegant-vanity",
    ),
    WENGINE_STEEL_CUSHION_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_STEEL_CUSHION_ID,
        advanced_stat=CharacterStat.CRIT_RATE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="attack-steel-cushion",
    ),
    WENGINE_BRIMSTONE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_BRIMSTONE_ID,
        advanced_stat=CharacterStat.ATTACK,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="attack-brimstone",
    ),
    WENGINE_DEEP_SEA_VISITOR_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_DEEP_SEA_VISITOR_ID,
        advanced_stat=CharacterStat.CRIT_RATE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="attack-deep-sea-visitor",
    ),
    WENGINE_HEART_OF_SWORD_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_HEART_OF_SWORD_ID,
        advanced_stat=CharacterStat.CRIT_DAMAGE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="attack-heart-of-sword",
    ),
    WENGINE_CRYING_CRADLE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_CRYING_CRADLE_ID,
        advanced_stat=CharacterStat.PENETRATION_RATE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="support-crying-cradle",
    ),
    WENGINE_DEFENSE_PATROL_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_DEFENSE_PATROL_ID,
        advanced_stat=CharacterStat.CRIT_DAMAGE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="attack-defense-patrol",
    ),
    WENGINE_DREAM_FORGE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_DREAM_FORGE_ID,
        advanced_stat=CharacterStat.HP,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="support-dream-forge",
    ),
    WENGINE_SONG_OF_NOISE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_SONG_OF_NOISE_ID,
        advanced_stat=CharacterStat.ENERGY_REGEN,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="support-song-of-noise",
    ),
    WENGINE_YE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_YE_ID,
        advanced_stat=CharacterStat.CRIT_DAMAGE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="ye-cloudcleave-radiance",
    ),
    WENGINE_ALICE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_ALICE_ID,
        advanced_stat=CharacterStat.ATTACK,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="alice-practiced-perfection",
    ),
    WENGINE_YUZUHA_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_YUZUHA_ID,
        advanced_stat=CharacterStat.ENERGY_REGEN,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="yuzuha-metanukimorphosis",
    ),
    WENGINE_TRIGGER_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_TRIGGER_ID,
        advanced_stat=CharacterStat.CRIT_RATE,
        advanced_layer=BuildContributionLayer.DIRECT_RATIO,
        effect_family="trigger-spectral-gaze",
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
