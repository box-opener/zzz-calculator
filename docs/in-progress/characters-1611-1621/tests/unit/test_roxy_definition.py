from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.nanoka_compiler import effective_skill_level
from core.application.characters.roxy import (
    ROXY_ID,
    ROXY_REVIEWED_MAPPING,
    RoxyCompileConfig,
    compile_roxy,
    load_raw_record,
)
from core.types import DamageTag, DamageType, Element, SkillGroup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "roxy.json"


def _raw():
    return load_raw_record(json.loads(SOURCE_PATH.read_text(encoding="utf-8")))


def test_roxy_live_source_identity_provenance_and_fifteen_direct_entries():
    raw = _raw()
    definition = compile_roxy(RoxyCompileConfig(), raw)

    assert (raw.name, raw.code_name, raw.specialty, raw.element, raw.icon) == (
        "洛克茜",
        "Roxy",
        "击破",
        "风属性",
        "IconRole68",
    )
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1621.json"
    assert definition.character_id == ROXY_ID
    assert definition.base_element is Element.WIND
    assert not any(
        item.ref.damage_type is not DamageType.DIRECT
        for item in definition.damage_event_templates
    )
    assert len(definition.move_entries) == 15
    assert len(definition.damage_event_templates) == 15


def test_roxy_default_level_twelve_compiles_every_reviewed_damage_curve():
    raw = _raw()
    definition = compile_roxy(RoxyCompileConfig(), raw)
    indexed = {str(entry.entry_id).rsplit(":", 1)[-1]: entry for entry in definition.move_entries}

    expected_level_twelve = {
        "basic-please-stop-stage-1": 1.052,
        "basic-please-stop-stage-2": 2.168,
        "basic-please-stop-stage-3": 3.451,
        "basic-please-stop-stage-4": 3.850,
        "dash-excuse-me": 0.719,
        "counter-courtesy": 7.847,
        "special-after-you": 1.026,
        "special-no-further": 5.008,
        "ex-mind-the-cold": 0.280,
        "ex-rest-in-peace": 0.638,
        "chain-wind-hammer": 18.053,
        "ultimate-night-dirge": 42.633,
        "assist-stay-late": 0.786,
        "quick-assist-at-your-service": 2.020,
        "assist-strike-midnight-protocol": 12.232,
    }
    assert set(indexed) == set(expected_level_twelve)
    for key, expected in expected_level_twelve.items():
        multiplier = indexed[key].multiplier_variants[0].multiplier.value.value
        assert multiplier == pytest.approx(expected)


def test_roxy_cinema_three_and_five_raise_ultimate_skill_level_including_caps():
    assert effective_skill_level(
        RoxyCompileConfig(cinema_level=3), SkillGroup.ULTIMATE
    ) == 14
    assert effective_skill_level(
        RoxyCompileConfig(cinema_level=5), SkillGroup.ULTIMATE
    ) == 16
    assert effective_skill_level(
        RoxyCompileConfig(
            cinema_level=5,
            skill_levels=(CharacterSkillLevel(SkillGroup.ULTIMATE, 14),),
        ),
        SkillGroup.ULTIMATE,
    ) == 16


def test_roxy_assist_that_source_says_counts_as_basic_has_both_tags():
    assist = next(
        item for item in ROXY_REVIEWED_MAPPING.moves if item.entry_key == "assist-stay-late"
    )
    assert assist.skill_group is SkillGroup.ASSIST
    assert assist.damage_tags == frozenset(
        {DamageTag.ASSIST, DamageTag.BASIC_ATTACK}
    )

