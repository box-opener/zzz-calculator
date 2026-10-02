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
    WENGINE_LUNAR_PLENILUNA_ID,
    WENGINE_LUNAR_DECRESCENT_ID,
    WENGINE_LUNAR_NOVILUNA_ID,
    WENGINE_REVERB_MARK_I_ID,
    WENGINE_REVERB_MARK_II_ID,
    WENGINE_TURBULENCE_CANNON_ID,
    WENGINE_TURBULENCE_ARROW_ID,
    WENGINE_TURBULENCE_AXE_ID,
    WENGINE_ELECTRO_STORM_I_ID,
    WENGINE_ELECTRO_STORM_II_ID,
    WENGINE_ELECTRO_STORM_III_ID,
    WENGINE_IDENTITY_STANDARD_ID,
    WENGINE_IDENTITY_ALTERNATE_ID,
    WENGINE_ASH_COBALT_BLUE_ID,
    WENGINE_LUNAR_STRING_ID,
    WENGINE_STREET_SUPERSTAR_ID,
    WENGINE_TIME_SLICE_ID,
    WENGINE_RAINFOREST_GOURMAND_ID,
    WENGINE_STARLIGHT_ENGINE_ID,
    WENGINE_HUMAN_IS_MEAT_ID,
)


@dataclass(frozen=True, slots=True)
class WEngineReviewedMapping:
    wengine_id: WEngineId
    advanced_stat: CharacterStat
    advanced_layer: BuildContributionLayer
    effect_family: str


WENGINE_REVIEWED_MAPPINGS: Mapping[WEngineId, WEngineReviewedMapping] = {
    WENGINE_ELECTRO_STORM_III_ID: WEngineReviewedMapping(
        WENGINE_ELECTRO_STORM_III_ID,
        CharacterStat.PENETRATION_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "anomaly-electro-storm-iii",
    ),
    WENGINE_IDENTITY_STANDARD_ID: WEngineReviewedMapping(
        WENGINE_IDENTITY_STANDARD_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-identity-standard",
    ),
    WENGINE_IDENTITY_ALTERNATE_ID: WEngineReviewedMapping(
        WENGINE_IDENTITY_ALTERNATE_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-identity-alternate",
    ),
    WENGINE_ASH_COBALT_BLUE_ID: WEngineReviewedMapping(
        WENGINE_ASH_COBALT_BLUE_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-ash-cobalt-blue",
    ),
    WENGINE_LUNAR_STRING_ID: WEngineReviewedMapping(
        WENGINE_LUNAR_STRING_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "vanguard-lunar-string",
    ),
    WENGINE_STREET_SUPERSTAR_ID: WEngineReviewedMapping(
        WENGINE_STREET_SUPERSTAR_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-street-superstar",
    ),
    WENGINE_TIME_SLICE_ID: WEngineReviewedMapping(
        WENGINE_TIME_SLICE_ID,
        CharacterStat.PENETRATION_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "support-time-slice",
    ),
    WENGINE_RAINFOREST_GOURMAND_ID: WEngineReviewedMapping(
        WENGINE_RAINFOREST_GOURMAND_ID,
        CharacterStat.ANOMALY_PROFICIENCY,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        "anomaly-rainforest-gourmand",
    ),
    WENGINE_STARLIGHT_ENGINE_ID: WEngineReviewedMapping(
        WENGINE_STARLIGHT_ENGINE_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-starlight-engine",
    ),
    WENGINE_HUMAN_IS_MEAT_ID: WEngineReviewedMapping(
        WENGINE_HUMAN_IS_MEAT_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-human-is-meat",
    ),
    WENGINE_LUNAR_DECRESCENT_ID: WEngineReviewedMapping(
        WENGINE_LUNAR_DECRESCENT_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-lunar-decrescent",
    ),
    WENGINE_LUNAR_NOVILUNA_ID: WEngineReviewedMapping(
        WENGINE_LUNAR_NOVILUNA_ID,
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "attack-lunar-noviluna",
    ),
    WENGINE_REVERB_MARK_I_ID: WEngineReviewedMapping(
        WENGINE_REVERB_MARK_I_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "support-reverb-mark-i",
    ),
    WENGINE_REVERB_MARK_II_ID: WEngineReviewedMapping(
        WENGINE_REVERB_MARK_II_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "support-reverb-mark-ii",
    ),
    WENGINE_LUNAR_PLENILUNA_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_LUNAR_PLENILUNA_ID,
        advanced_stat=CharacterStat.ATTACK,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="attack-lunar-pleniluna",
    ),
    WENGINE_RESONAB_THREE_ID: WEngineReviewedMapping(
        wengine_id=WENGINE_RESONAB_THREE_ID,
        advanced_stat=CharacterStat.HP,
        advanced_layer=BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        effect_family="support-resonab-3",
    ),
    WENGINE_TURBULENCE_CANNON_ID: WEngineReviewedMapping(
        WENGINE_TURBULENCE_CANNON_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-turbulence-cannon",
    ),
    WENGINE_TURBULENCE_ARROW_ID: WEngineReviewedMapping(
        WENGINE_TURBULENCE_ARROW_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-turbulence-arrow",
    ),
    WENGINE_TURBULENCE_AXE_ID: WEngineReviewedMapping(
        WENGINE_TURBULENCE_AXE_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-turbulence-axe",
    ),
    WENGINE_ELECTRO_STORM_I_ID: WEngineReviewedMapping(
        WENGINE_ELECTRO_STORM_I_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "anomaly-electro-storm-i",
    ),
    WENGINE_ELECTRO_STORM_II_ID: WEngineReviewedMapping(
        WENGINE_ELECTRO_STORM_II_ID,
        CharacterStat.ANOMALY_PROFICIENCY,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        "anomaly-electro-storm-ii",
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
