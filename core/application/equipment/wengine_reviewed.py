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
    WENGINE_PRECIOUS_FOSSIL_ID,
    WENGINE_PRECISE_TRANSFORMER_ID,
    WENGINE_TWIN_CRYING_STARS_ID,
    WENGINE_ELECTRIC_LIP_GLOSS_ID,
    WENGINE_BUNNY_BAND_ID,
    WENGINE_SPRING_WARMTH_ID,
    WENGINE_FANTASY_CUBE_ID,
    WENGINE_GILDED_BLOSSOM_ID,
    WENGINE_RADIO_WAVE_WALK_ID,
    WENGINE_STRONG_ENOUGH_ID,
    WENGINE_REEL_PROJECTOR_ID,
    WENGINE_CATTY_LUCK_ID,
    WENGINE_BOISTEROUS_ECHOES_ID,
    WENGINE_CAULDRON_OF_CLARITY_ID,
    WENGINE_SIMMERING_POT_ID,
    WENGINE_BLOODMARROW_COFFER_ID,
    WENGINE_DEMARA_BATTERY_II_ID,
    WENGINE_HOUSEKEEPER_ID,
    WENGINE_STARLIGHT_ENGINE_REPLICA_ID,
    WENGINE_DRILL_RIG_RED_AXIS_ID,
    WENGINE_BIG_CYLINDER_ID,
    WENGINE_BASHFUL_DEMON_ID,
    WENGINE_KABOOM_THE_CANNON_ID,
    WENGINE_PEACEKEEPER_SPECIALIZED_ID,
    WENGINE_ROARING_RIDE_ID,
    WENGINE_BOX_CUTTER_ID,
    WENGINE_TREMOR_TRIGRAM_VESSEL_ID,
    WENGINE_GRILL_O_WISP_ID,
    WENGINE_CANNON_ROTOR_ID,
    WENGINE_UNFETTERED_GAME_BALL_ID,
    WENGINE_SIX_SHOOTER_ID,
    WENGINE_KRAKENS_CRADLE_ID,
    WENGINE_TUSKS_OF_FURY_ID,
    WENGINE_HAILSTORM_SHRINE_ID,
    WENGINE_HELLFIRE_GEARS_ID,
    WENGINE_RESTRAINED_ID,
    WENGINE_BLAZING_LAUREL_ID,
    WENGINE_FLAMEMAKER_SHAKER_ID,
    WENGINE_FUSION_COMPILER_ID,
    WENGINE_TIMEWEAVER_ID,
)


@dataclass(frozen=True, slots=True)
class WEngineReviewedMapping:
    wengine_id: WEngineId
    advanced_stat: CharacterStat
    advanced_layer: BuildContributionLayer
    effect_family: str


WENGINE_REVIEWED_MAPPINGS: Mapping[WEngineId, WEngineReviewedMapping] = {
    WENGINE_SIX_SHOOTER_ID: WEngineReviewedMapping(
        WENGINE_SIX_SHOOTER_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-six-shooter",
    ),
    WENGINE_KRAKENS_CRADLE_ID: WEngineReviewedMapping(
        WENGINE_KRAKENS_CRADLE_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-krakens-cradle",
    ),
    WENGINE_TUSKS_OF_FURY_ID: WEngineReviewedMapping(
        WENGINE_TUSKS_OF_FURY_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-tusks-of-fury",
    ),
    WENGINE_HAILSTORM_SHRINE_ID: WEngineReviewedMapping(
        WENGINE_HAILSTORM_SHRINE_ID,
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "anomaly-hailstorm-shrine",
    ),
    WENGINE_HELLFIRE_GEARS_ID: WEngineReviewedMapping(
        WENGINE_HELLFIRE_GEARS_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-hellfire-gears",
    ),
    WENGINE_RESTRAINED_ID: WEngineReviewedMapping(
        WENGINE_RESTRAINED_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-restrained",
    ),
    WENGINE_BLAZING_LAUREL_ID: WEngineReviewedMapping(
        WENGINE_BLAZING_LAUREL_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-blazing-laurel",
    ),
    WENGINE_FLAMEMAKER_SHAKER_ID: WEngineReviewedMapping(
        WENGINE_FLAMEMAKER_SHAKER_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "anomaly-flamemaker-shaker",
    ),
    WENGINE_FUSION_COMPILER_ID: WEngineReviewedMapping(
        WENGINE_FUSION_COMPILER_ID,
        CharacterStat.PENETRATION_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "anomaly-fusion-compiler",
    ),
    WENGINE_TIMEWEAVER_ID: WEngineReviewedMapping(
        WENGINE_TIMEWEAVER_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "anomaly-timeweaver",
    ),
    WENGINE_BIG_CYLINDER_ID: WEngineReviewedMapping(
        WENGINE_BIG_CYLINDER_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-big-cylinder",
    ),
    WENGINE_BASHFUL_DEMON_ID: WEngineReviewedMapping(
        WENGINE_BASHFUL_DEMON_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "support-bashful-demon",
    ),
    WENGINE_KABOOM_THE_CANNON_ID: WEngineReviewedMapping(
        WENGINE_KABOOM_THE_CANNON_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "support-kaboom-the-cannon",
    ),
    WENGINE_PEACEKEEPER_SPECIALIZED_ID: WEngineReviewedMapping(
        WENGINE_PEACEKEEPER_SPECIALIZED_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-peacekeeper-specialized",
    ),
    WENGINE_ROARING_RIDE_ID: WEngineReviewedMapping(
        WENGINE_ROARING_RIDE_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "anomaly-roaring-ride",
    ),
    WENGINE_BOX_CUTTER_ID: WEngineReviewedMapping(
        WENGINE_BOX_CUTTER_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-box-cutter",
    ),
    WENGINE_TREMOR_TRIGRAM_VESSEL_ID: WEngineReviewedMapping(
        WENGINE_TREMOR_TRIGRAM_VESSEL_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-tremor-trigram-vessel",
    ),
    WENGINE_GRILL_O_WISP_ID: WEngineReviewedMapping(
        WENGINE_GRILL_O_WISP_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-grill-o-wisp",
    ),
    WENGINE_CANNON_ROTOR_ID: WEngineReviewedMapping(
        WENGINE_CANNON_ROTOR_ID,
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "attack-cannon-rotor",
    ),
    WENGINE_UNFETTERED_GAME_BALL_ID: WEngineReviewedMapping(
        WENGINE_UNFETTERED_GAME_BALL_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "support-unfettered-game-ball",
    ),
    WENGINE_REEL_PROJECTOR_ID: WEngineReviewedMapping(
        WENGINE_REEL_PROJECTOR_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-reel-projector",
    ),
    WENGINE_CATTY_LUCK_ID: WEngineReviewedMapping(
        WENGINE_CATTY_LUCK_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "vanguard-cattery-luck",
    ),
    WENGINE_BOISTEROUS_ECHOES_ID: WEngineReviewedMapping(
        WENGINE_BOISTEROUS_ECHOES_ID,
        CharacterStat.ANOMALY_PROFICIENCY,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        "anomaly-boisterous-echoes",
    ),
    WENGINE_CAULDRON_OF_CLARITY_ID: WEngineReviewedMapping(
        WENGINE_CAULDRON_OF_CLARITY_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-cauldron-of-clarity",
    ),
    WENGINE_SIMMERING_POT_ID: WEngineReviewedMapping(
        WENGINE_SIMMERING_POT_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-simmering-pot",
    ),
    WENGINE_BLOODMARROW_COFFER_ID: WEngineReviewedMapping(
        WENGINE_BLOODMARROW_COFFER_ID,
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "vanguard-bloodmarrow-coffer",
    ),
    WENGINE_DEMARA_BATTERY_II_ID: WEngineReviewedMapping(
        WENGINE_DEMARA_BATTERY_II_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-demara-battery-ii",
    ),
    WENGINE_HOUSEKEEPER_ID: WEngineReviewedMapping(
        WENGINE_HOUSEKEEPER_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-housekeeper",
    ),
    WENGINE_STARLIGHT_ENGINE_REPLICA_ID: WEngineReviewedMapping(
        WENGINE_STARLIGHT_ENGINE_REPLICA_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-starlight-engine-replica",
    ),
    WENGINE_DRILL_RIG_RED_AXIS_ID: WEngineReviewedMapping(
        WENGINE_DRILL_RIG_RED_AXIS_ID,
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-drill-rig-red-axis",
    ),
    WENGINE_PRECIOUS_FOSSIL_ID: WEngineReviewedMapping(
        WENGINE_PRECIOUS_FOSSIL_ID,
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "stun-precious-fossil",
    ),
    WENGINE_PRECISE_TRANSFORMER_ID: WEngineReviewedMapping(
        WENGINE_PRECISE_TRANSFORMER_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-precise-transformer",
    ),
    WENGINE_TWIN_CRYING_STARS_ID: WEngineReviewedMapping(
        WENGINE_TWIN_CRYING_STARS_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "anomaly-twin-crying-stars",
    ),
    WENGINE_ELECTRIC_LIP_GLOSS_ID: WEngineReviewedMapping(
        WENGINE_ELECTRIC_LIP_GLOSS_ID,
        CharacterStat.ANOMALY_PROFICIENCY,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        "anomaly-electric-lip-gloss",
    ),
    WENGINE_BUNNY_BAND_ID: WEngineReviewedMapping(
        WENGINE_BUNNY_BAND_ID,
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-bunny-band",
    ),
    WENGINE_SPRING_WARMTH_ID: WEngineReviewedMapping(
        WENGINE_SPRING_WARMTH_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "defense-spring-warmth",
    ),
    WENGINE_FANTASY_CUBE_ID: WEngineReviewedMapping(
        WENGINE_FANTASY_CUBE_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-fantasy-cube",
    ),
    WENGINE_GILDED_BLOSSOM_ID: WEngineReviewedMapping(
        WENGINE_GILDED_BLOSSOM_ID,
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "attack-gilded-blossom",
    ),
    WENGINE_RADIO_WAVE_WALK_ID: WEngineReviewedMapping(
        WENGINE_RADIO_WAVE_WALK_ID,
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        "rupture-radio-wave-walk",
    ),
    WENGINE_STRONG_ENOUGH_ID: WEngineReviewedMapping(
        WENGINE_STRONG_ENOUGH_ID,
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        "attack-strong-enough",
    ),
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
