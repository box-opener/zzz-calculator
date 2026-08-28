from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from core.application import assemble_build
from core.types import (
    BuildContributionLayer,
    BuildMode,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    CharacterBuildDefinition,
    CharacterId,
    CharacterStat,
    CharacterStats,
    Element,
    Resolved,
    Unresolved,
    UnresolvedReason,
)


def _base_stats(*, attack: float = 1000.0) -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(attack),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.05),
        crit_damage=Resolved(0.50),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={Element.PHYSICAL: Resolved(0.0)},
    )


def _source(source_id: str = "drive:one") -> BuildSource:
    return BuildSource(
        source_id=source_id,
        source_type=BuildSourceType.DRIVE_DISC,
        label="测试驱动盘",
    )


def _contribution(
    contribution_id: str,
    stat: CharacterStat,
    layer: BuildContributionLayer,
    value: float,
    *,
    element: Element | None = None,
) -> BuildStatContribution:
    return BuildStatContribution(
        contribution_id=contribution_id,
        source=_source(),
        stat=stat,
        layer=layer,
        value=Resolved(value),
        element=element,
    )


def test_equipment_build_assembles_white_percent_and_flat_layers_in_order() -> None:
    definition = CharacterBuildDefinition(
        character_id=CharacterId("character:test"),
        level=60,
        mode=BuildMode.EQUIPMENT_BUILD,
        base_stats=_base_stats(),
        contributions=(
            BuildStatContribution(
                contribution_id="weapon:attack",
                source=BuildSource(
                    source_id="weapon:test",
                    source_type=BuildSourceType.WENGINE,
                    label="测试音擎",
                ),
                stat=CharacterStat.ATTACK,
                layer=BuildContributionLayer.WHITE_VALUE,
                value=Resolved(713.0),
            ),
            _contribution(
                "disc:attack-percent",
                CharacterStat.ATTACK,
                BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
                0.60,
            ),
            _contribution(
                "disc:attack-flat",
                CharacterStat.ATTACK,
                BuildContributionLayer.OUT_OF_COMBAT_FLAT,
                316.0,
            ),
        ),
    )

    result = assemble_build(definition)

    assert result.complete is True
    assert result.initial_stats.attack == Resolved(3056.8)
    assert result.initial_snapshot.initial_stats.attack == Resolved(3056.8)
    assert result.character_snapshot.settlement_stats.attack == Resolved(3056.8)
    assert [item.contribution_id for item in result.provenance] == [
        "weapon:attack",
        "disc:attack-percent",
        "disc:attack-flat",
    ]


def test_empty_equipment_has_no_fabricated_drive_disc_stats() -> None:
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
        )
    )

    assert result.initial_stats.hp == Resolved(10000.0)
    assert result.initial_stats.attack == Resolved(1000.0)
    assert result.initial_stats.defense == Resolved(500.0)
    assert result.provenance == ()


def test_element_damage_bonus_keeps_element_identity_and_ratio_units() -> None:
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
            contributions=(
                _contribution(
                    "disc:physical-bonus",
                    CharacterStat.ELEMENT_DAMAGE_BONUS,
                    BuildContributionLayer.DIRECT_RATIO,
                    0.30,
                    element=Element.PHYSICAL,
                ),
            ),
        )
    )

    assert result.initial_stats.element_damage_bonus[Element.PHYSICAL] == Resolved(0.30)
    assert result.provenance[0].element is Element.PHYSICAL


@pytest.mark.parametrize(
    ("stat", "field_name", "base", "percent", "expected"),
    (
        (CharacterStat.HP, "hp", 10000.0, 0.30, 13000.0),
        (CharacterStat.DEFENSE, "defense", 500.0, 0.48, 740.0),
        (CharacterStat.IMPACT, "impact", 100.0, 0.18, 118.0),
        (CharacterStat.ANOMALY_MASTERY, "anomaly_mastery", 100.0, 0.30, 130.0),
        (CharacterStat.ENERGY_REGEN, "energy_regen", 1.2, 0.60, 1.92),
    ),
)
def test_out_of_combat_percent_supports_all_current_white_value_stats(
    stat: CharacterStat,
    field_name: str,
    base: float,
    percent: float,
    expected: float,
) -> None:
    stats = replace(_base_stats(), **{field_name: Resolved(base)})
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=stats,
            contributions=(
                _contribution(
                    f"disc:{stat.value}-percent",
                    stat,
                    BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
                    percent,
                ),
            ),
        )
    )

    assert getattr(result.initial_stats, field_name) == Resolved(expected)


def test_manual_panel_mode_bypasses_equipment_aggregation() -> None:
    manual = _base_stats(attack=2844.0)
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.MANUAL_PANEL,
            manual_panel_stats=manual,
        )
    )

    assert result.initial_stats is manual
    assert result.base_stats is None
    assert result.character_snapshot.settlement_stats is manual
    assert result.provenance
    assert all(
        item.source.source_type is BuildSourceType.MANUAL_PANEL
        for item in result.provenance
    )
    assert all(
        item.layer is BuildContributionLayer.MANUAL_PANEL
        for item in result.provenance
    )


def test_unresolved_contribution_does_not_default_to_zero() -> None:
    unresolved = Unresolved(UnresolvedReason.MISSING_DATA, "missing drive disc value")
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
            contributions=(
                BuildStatContribution(
                    contribution_id="disc:unknown-attack",
                    source=_source(),
                    stat=CharacterStat.ATTACK,
                    layer=BuildContributionLayer.OUT_OF_COMBAT_FLAT,
                    value=unresolved,
                ),
            ),
        )
    )

    assert result.complete is False
    assert isinstance(result.initial_stats.attack, Unresolved)
    assert result.unresolved == (unresolved,)
    assert result.diagnostics[0].blocking is True


def test_build_contract_rejects_element_missing_from_element_bonus() -> None:
    with pytest.raises(ValueError, match="requires an element"):
        _contribution(
            "disc:element-bonus",
            CharacterStat.ELEMENT_DAMAGE_BONUS,
            BuildContributionLayer.DIRECT_RATIO,
            0.30,
        )


def test_drive_disc_attack_white_value_is_rejected() -> None:
    with pytest.raises(ValueError, match="must come from a WENGINE"):
        BuildStatContribution(
            contribution_id="disc:attack-white",
            source=_source(),
            stat=CharacterStat.ATTACK,
            layer=BuildContributionLayer.WHITE_VALUE,
            value=Resolved(316.0),
        )


def test_only_attack_accepts_an_equipment_white_value_in_stage18_1() -> None:
    with pytest.raises(ValueError, match="does not support stat hp"):
        BuildStatContribution(
            contribution_id="weapon:hp-white",
            source=BuildSource(
                source_id="weapon:test",
                source_type=BuildSourceType.WENGINE,
                label="测试音擎",
            ),
            stat=CharacterStat.HP,
            layer=BuildContributionLayer.WHITE_VALUE,
            value=Resolved(100.0),
        )


def test_drive_flat_attack_is_not_added_to_white_value() -> None:
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
            contributions=(
                _contribution(
                    "disc:attack-flat",
                    CharacterStat.ATTACK,
                    BuildContributionLayer.OUT_OF_COMBAT_FLAT,
                    316.0,
                ),
                _contribution(
                    "disc:attack-percent",
                    CharacterStat.ATTACK,
                    BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
                    0.60,
                ),
            ),
        )
    )

    assert result.initial_stats.attack == Resolved(1916.0)


def test_build_contract_rejects_duplicate_contribution_ids() -> None:
    contribution = _contribution(
        "disc:attack-flat",
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        19.0,
    )
    with pytest.raises(ValueError, match="IDs must be unique"):
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
            contributions=(contribution, contribution),
        )


def test_build_outputs_are_frozen() -> None:
    result = assemble_build(
        CharacterBuildDefinition(
            character_id=CharacterId("character:test"),
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_base_stats(),
        )
    )
    with pytest.raises(FrozenInstanceError):
        result.initial_stats = _base_stats()  # type: ignore[misc]
