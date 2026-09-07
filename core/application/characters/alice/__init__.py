"""Reviewed Alice (character:1401) compiler."""

from .compiler import ALICE_ID, compile_alice
from .config import AliceCompileConfig
from .reviewed import (
    ALICE_REVIEWED_MAPPING,
    ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID,
    ALICE_PHYSICAL_ANOMALY_RECORD_ID,
    ALICE_REMAINING_DURATION_PARAMETER_ID,
    ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID,
    PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID,
    POLAR_ASSAULT_CONDITION_ID,
    STAR_DANCE_1_CONDITION_ID,
    STAR_DANCE_2_CONDITION_ID,
    STAR_DANCE_3_CONDITION_ID,
    VICTORY_STATE_ACTIVE_CONDITION_ID,
)
from core.application.characters.nanoka_source import (
    NanokaRawCoreLevel,
    NanokaRawMindscape,
    NanokaRawMoveRecord,
    NanokaRawRecord,
    NanokaRawSkillParameter,
    load_nanoka_raw_record,
)


load_raw_record = load_nanoka_raw_record

__all__ = [
    "ALICE_ID",
    "ALICE_REVIEWED_MAPPING",
    "ALICE_PERIODIC_TICK_COUNT_PARAMETER_ID",
    "ALICE_PHYSICAL_ANOMALY_RECORD_ID",
    "ALICE_REMAINING_DURATION_PARAMETER_ID",
    "ALICE_VICTORY_ATTACK_COUNT_PARAMETER_ID",
    "AliceCompileConfig",
    "NanokaRawCoreLevel",
    "NanokaRawMindscape",
    "NanokaRawMoveRecord",
    "NanokaRawRecord",
    "NanokaRawSkillParameter",
    "PHYSICAL_ANOMALY_ACTIVE_CONDITION_ID",
    "POLAR_ASSAULT_CONDITION_ID",
    "STAR_DANCE_1_CONDITION_ID",
    "STAR_DANCE_2_CONDITION_ID",
    "STAR_DANCE_3_CONDITION_ID",
    "VICTORY_STATE_ACTIVE_CONDITION_ID",
    "compile_alice",
    "load_raw_record",
]
