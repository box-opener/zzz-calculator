from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.application.characters.claret import (
    CLARET_ID,
    CLARET_SOURCE_CURVES,
    ClaretCompileConfig,
    ClaretDamageSemantics,
    compile_claret,
    derive_initial_crit_rate,
    load_raw_record,
)
from core.application.characters.nanoka_compiler import effective_skill_level
from core.types import CalculationNode, DamageType, Element, SkillGroup


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "core" / "data" / "characters" / "claret.json"
SOURCE_VERSION = "3.2"
SOURCE_URL = "https://static.nanoka.cc/zzz/3.2/zh/character/1611.json"


def _source_data() -> dict[str, object]:
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def _compilation(config: ClaretCompileConfig | None = None):
    data = _source_data()
    raw = load_raw_record(data)
    return data, raw, compile_claret(config or ClaretCompileConfig(), raw, data)


def test_claret_source_identity_panel_and_provenance_are_reviewed() -> None:
    data, raw, compiled = _compilation()

    assert CLARET_ID == "character:1611"
    assert (raw.name, raw.code_name, raw.rarity) == ("克拉蕾", "Claret", 4)
    assert (raw.specialty, raw.element, raw.faction, raw.icon) == (
        "锋御",
        "电属性",
        "罗斯凯利法",
        "IconRole1611",
    )
    assert (raw.source_version, raw.source_url) == (SOURCE_VERSION, SOURCE_URL)
    assert (compiled.source_panel.base_crit_rate, compiled.source_panel.base_crit_damage) == (
        0.05,
        0.5,
    )
    assert compiled.source_panel.sharp_crit_damage == 1.5
    assert data["source_version"] == SOURCE_VERSION
    assert data["source_url"] == SOURCE_URL


def test_all_reviewed_damage_curves_match_the_raw_level_12_parameters() -> None:
    _, raw, compiled = _compilation()

    expected = {
        "1611001": 109.4,
        "1611002": 135.4,
        "1611003": 190.9,
        "1611004": 579.9,
        "1611005": 215.5,
        "1611006": 575.6,
        "1611007": 904.2,
        "1611029": 355.5,
        "1611008": 656.9,
        "1611016": 106.8,
        "1611018": 545.3,
        "1611019": 660.0,
        "1611009": 180.3,
        "1611010": 1249.6,
        "1611011": 153.6,
        "1611012": 175.7,
        "1611013": 1625.6,
        "1611014": 626.3,
        "1611020": 2116.2,
        "1611021": 4504.8,
        "1611022": 106.8,
        "1611023": 232.4,
        "1611027": 892.8,
        "1611028": 2306.9,
        "1611030": 1713.2,
    }
    actual = {item.spec.source_skill_id: item for item in compiled.curves}

    assert len(CLARET_SOURCE_CURVES) == 25
    assert set(actual) == set(expected)
    assert len(actual) == 25
    assert len(raw.moves) == 19
    for source_id, value in expected.items():
        assert actual[source_id].skill_level == 12
        assert actual[source_id].source_percent == pytest.approx(value)
        assert actual[source_id].multiplier == pytest.approx(value / 100.0)

    # The source-only compiler must not misclassify 锐化 as either ordinary
    # Direct damage or the distinct 锐暴/Sharp Explosion damage type.
    assert all(not hasattr(item.spec, "damage_type") for item in compiled.curves)
    assert DamageType.SHARP_EXPLOSION.value == "sharp-explosion"
    assert all(item.spec.element is Element.ELECTRIC for item in compiled.curves)
    assert all(
        item.spec.damage_basis_node is CalculationNode.CHARACTER_CURRENT_DEFENSE
        for item in compiled.curves
    )
    destroy = actual["1611013"].spec
    assert destroy.semantics is ClaretDamageSemantics.DESTROY
    assert destroy.source_move_id == actual["1611011"].spec.source_move_id
    assert set(destroy.triggering_move_ids) == {
        actual["1611011"].spec.source_move_id,
        actual["1611014"].spec.source_move_id,
    }
    assert destroy.event_move_id is None
    assert destroy.event_skill_group is None
    assert destroy.damage_tags == frozenset()
    assert len(
        {
            actual[f"161100{stage}"].spec.source_move_id
            for stage in range(1, 5)
        }
    ) == 1


def test_known_core_initial_crit_conversion_and_current_scarlet_rate() -> None:
    _, _, compiled = _compilation()

    assert compiled.core_initial_crit_conversion.source_node is CalculationNode.CHARACTER_INITIAL_CRIT_DAMAGE
    assert compiled.core_initial_crit_conversion.target_node is CalculationNode.CHARACTER_INITIAL_CRIT_RATE
    assert compiled.core_initial_crit_conversion.coefficient == pytest.approx(0.35)
    assert compiled.core_scarlet_crit_source_node is CalculationNode.CHARACTER_CURRENT_CRIT_RATE
    assert derive_initial_crit_rate(0.05, 0.5, core_conversion_enabled=True) == pytest.approx(0.225)
    assert derive_initial_crit_rate(0.05, 0.5, core_conversion_enabled=False) == pytest.approx(0.05)
    assert compiled.core_scarlet_crit_rate_bonus == pytest.approx(0.30)

    expected_scarlet = (0.15, 0.175, 0.20, 0.225, 0.25, 0.275, 0.30)
    for core_level, expected in enumerate(expected_scarlet, start=1):
        assert _compilation(ClaretCompileConfig(core_level=core_level))[2].core_scarlet_crit_rate_bonus == pytest.approx(expected)


def test_cinema_numbers_and_named_move_scopes_are_read_from_raw_source() -> None:
    data, raw, compiled = _compilation()
    mindscapes = {item.level: item.description for item in raw.mindscapes}
    core_scope = compiled.core_scarlet_crit_scope_text

    assert compiled.cinema_values.cinema1_mark_buildup_bonus == pytest.approx(0.20)
    assert compiled.cinema_values.cinema1_destroy_multiplier == pytest.approx(1.30)
    assert compiled.cinema_values.cinema2_mark_duration_bonus_seconds == pytest.approx(2.0)
    assert compiled.cinema_values.cinema2_electric_resistance_ignore == pytest.approx(0.18)
    assert compiled.cinema_values.cinema4_named_move_damage_bonus == pytest.approx(0.20)
    assert compiled.cinema_values.cinema6_destroy_trigger_count == 1
    assert "猩红铭刻" in core_scope
    assert all(term in core_scope for term in ("连携技", "终结技", "反制支援", "支援突击"))
    assert "[普通攻击：血华誓·锻星]第三段" in mindscapes[4]
    assert "[连携技：血华誓·血契共鸣]" in mindscapes[4]
    assert "[终结技：血华誓·千锤百炼]" in mindscapes[4]
    assert "不消耗[残痕]直接触发1次单体[毁伤]" in mindscapes[6]
    assert data["talent"]["2"]["desc"].find("无视目标18%") >= 0


def test_cinema_three_and_five_levels_include_ultimate_with_cap_sixteen() -> None:
    assert effective_skill_level(ClaretCompileConfig(cinema_level=0), SkillGroup.ULTIMATE) == 12
    assert effective_skill_level(ClaretCompileConfig(cinema_level=3), SkillGroup.ULTIMATE) == 14
    assert effective_skill_level(ClaretCompileConfig(cinema_level=5), SkillGroup.ULTIMATE) == 16
    config = ClaretCompileConfig(cinema_level=5)
    assert effective_skill_level(config, SkillGroup.BASIC_ATTACK) == 16


@pytest.mark.parametrize("core_level", [0, 8])
def test_core_level_is_bounded(core_level: int) -> None:
    with pytest.raises(ValueError, match="core_level"):
        ClaretCompileConfig(core_level=core_level)
