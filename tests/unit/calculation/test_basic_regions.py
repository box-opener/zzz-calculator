from dataclasses import FrozenInstanceError, fields

import pytest

from core.calculation import (
    AnomalyCritRegionInput,
    BroadVulnerabilityRegionInput,
    CalculationResult,
    CritRegionInput,
    DefenseRegionInput,
    DischargeCritRegionInput,
    DischargeDamageBonusRegionInput,
    DisorderDamageBonusRegionInput,
    LuminanceAnomalyDamageBonusRegionInput,
    NormalDamageBonusRegionInput,
    ResistanceRegionInput,
    SpecialIndependentRegionInput,
    TurbulenceCritRegionInput,
    TurbulenceDamageBonusRegionInput,
    calculate_broad_vulnerability_region,
    calculate_anomaly_crit_region,
    calculate_crit_region,
    calculate_defense_region,
    calculate_discharge_crit_region,
    calculate_discharge_damage_bonus_region,
    calculate_disorder_damage_bonus_region,
    calculate_normal_damage_bonus_region,
    calculate_luminance_anomaly_damage_bonus_region,
    calculate_resistance_region,
    calculate_special_independent_region,
    calculate_turbulence_crit_region,
    calculate_turbulence_damage_bonus_region,
    defense_level_coefficient,
)
from core.types import (
    CalculationNode,
    Resolved,
)


def _breakdown(result: CalculationResult) -> dict[CalculationNode, float]:
    values: dict[CalculationNode, float] = {}
    for item in result.breakdown:
        assert isinstance(item.value, Resolved)
        values[item.node] = item.value.value
    return values


def test_defense_level_coefficient_uses_spec_table_and_level_60_cap() -> None:
    assert defense_level_coefficient(1) == 50.0
    assert defense_level_coefficient(60) == 794.0
    assert defense_level_coefficient(80) == 794.0
    with pytest.raises(ValueError, match="at least 1"):
        defense_level_coefficient(0)


def test_defense_region_applies_modifiers_in_spec_order() -> None:
    result = calculate_defense_region(
        DefenseRegionInput(
            attacker_level=60,
            initial_defense=1000.0,
            defense_increase=0.1,
            defense_reduction=0.2,
            defense_ignore=0.1,
            penetration_rate=0.25,
            penetration_flat=50.0,
        )
    )
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == pytest.approx(
        550.0
    )
    assert result.value == pytest.approx(794.0 / (550.0 + 794.0))
    assert breakdown[CalculationNode.DAMAGE_DEFENSE_REGION] == result.value
    assert result.unresolved == ()


def test_defense_region_caps_effective_defense_at_zero_and_region_at_one() -> None:
    result = calculate_defense_region(
        DefenseRegionInput(
            attacker_level=60,
            initial_defense=1000.0,
            defense_ignore=2.0,
        )
    )
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.ENEMY_CURRENT_EFFECTIVE_DEFENSE] == 0.0
    assert result.value == 1.0


def test_unmodified_equal_defense_and_coefficient_gives_half_region() -> None:
    result = calculate_defense_region(
        DefenseRegionInput(attacker_level=60, initial_defense=794.0)
    )

    assert result.value == 0.5


def test_resistance_region_linearly_adds_ignore_and_reduction() -> None:
    result = calculate_resistance_region(
        ResistanceRegionInput(
            base_resistance=0.2,
            resistance_ignore=0.1,
            resistance_reduction=0.05,
        )
    )
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.ENEMY_INITIAL_RESISTANCE_REGION] == 0.8
    assert result.value == pytest.approx(0.95)
    assert breakdown[CalculationNode.DAMAGE_RESISTANCE_REGION] == result.value


def test_resistance_region_cannot_be_negative() -> None:
    result = calculate_resistance_region(
        ResistanceRegionInput(base_resistance=1.2)
    )

    assert result.value == 0.0


def test_broad_vulnerability_multiplies_additive_and_reduction_regions() -> None:
    result = calculate_broad_vulnerability_region(
        BroadVulnerabilityRegionInput(
            stun_vulnerability=0.5,
            normal_vulnerability=0.2,
            move_vulnerability=0.1,
            damage_reduction=0.2,
        )
    )
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.DAMAGE_VULNERABILITY_ADDITIVE_REGION] == 1.8
    assert breakdown[CalculationNode.DAMAGE_REDUCTION_REGION] == 0.8
    assert result.value == pytest.approx(1.44)
    assert breakdown[CalculationNode.DAMAGE_BROAD_VULNERABILITY_REGION] == result.value


def test_crit_region_returns_expected_value_multiplier() -> None:
    result = calculate_crit_region(CritRegionInput(crit_rate=0.5, crit_damage=1.0))
    breakdown = _breakdown(result)

    assert result.value == 1.5
    assert breakdown[CalculationNode.DAMAGE_STANDARD_CRIT_REGION] == 1.5


def test_anomaly_crit_region_does_not_emit_ordinary_crit_nodes() -> None:
    result = calculate_anomaly_crit_region(
        AnomalyCritRegionInput(crit_rate=1.0, crit_damage=0.5)
    )
    breakdown = _breakdown(result)

    assert result.value == 1.5
    assert breakdown == {CalculationNode.ANOMALY_CRIT_REGION: 1.5}


def test_disorder_bonus_region_keeps_two_identity_sources_separate() -> None:
    result = calculate_disorder_damage_bonus_region(
        DisorderDamageBonusRegionInput(
            trigger_damage_bonus=0.2,
            settled_contributor_damage_bonus=0.15,
        )
    )
    breakdown = _breakdown(result)

    assert result.value == pytest.approx(1.35)
    assert breakdown[CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS] == 0.2
    assert (
        breakdown[CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS]
        == 0.15
    )
    assert breakdown[CalculationNode.DISORDER_DAMAGE_BONUS_REGION] == pytest.approx(
        1.35
    )


def test_disorder_bonus_region_defaults_to_one() -> None:
    result = calculate_disorder_damage_bonus_region(
        DisorderDamageBonusRegionInput()
    )

    assert result.value == 1.0


def test_historical_anomaly_subtype_bonus_regions_use_distinct_nodes() -> None:
    discharge = calculate_discharge_damage_bonus_region(
        DischargeDamageBonusRegionInput(0.1)
    )
    turbulence = calculate_turbulence_damage_bonus_region(
        TurbulenceDamageBonusRegionInput(0.2)
    )
    luminance = calculate_luminance_anomaly_damage_bonus_region(
        LuminanceAnomalyDamageBonusRegionInput(0.3)
    )

    assert _breakdown(discharge) == {
        CalculationNode.DISCHARGE_DAMAGE_BONUS: 0.1,
        CalculationNode.DISCHARGE_DAMAGE_BONUS_REGION: 1.1,
    }
    assert _breakdown(turbulence) == {
        CalculationNode.TURBULENCE_DAMAGE_BONUS: 0.2,
        CalculationNode.TURBULENCE_DAMAGE_BONUS_REGION: 1.2,
    }
    assert _breakdown(luminance) == {
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS: 0.3,
        CalculationNode.LUMINANCE_ANOMALY_DAMAGE_BONUS_REGION: 1.3,
    }


def test_discharge_and_turbulence_crit_regions_use_distinct_nodes() -> None:
    discharge = calculate_discharge_crit_region(
        DischargeCritRegionInput(1.0, 0.5)
    )
    turbulence = calculate_turbulence_crit_region(
        TurbulenceCritRegionInput(1.0, 0.5)
    )

    assert _breakdown(discharge) == {CalculationNode.DISCHARGE_CRIT_REGION: 1.5}
    assert _breakdown(turbulence) == {
        CalculationNode.TURBULENCE_CRIT_REGION: 1.5
    }


def test_normal_damage_bonus_region_adds_all_three_bonus_sources() -> None:
    result = calculate_normal_damage_bonus_region(
        NormalDamageBonusRegionInput(
            element_damage_bonus=0.3,
            matched_damage_bonus=0.2,
            generic_damage_bonus=0.1,
        )
    )
    breakdown = _breakdown(result)

    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS] == pytest.approx(0.3)
    assert result.value == pytest.approx(1.6)
    assert breakdown[CalculationNode.DAMAGE_NORMAL_BONUS_REGION] == result.value


def test_special_independent_region_is_separate_from_normal_bonus() -> None:
    result = calculate_special_independent_region(
        SpecialIndependentRegionInput(independent_bonus=0.1)
    )
    breakdown = _breakdown(result)

    assert result.value == 1.1
    assert breakdown[CalculationNode.DAMAGE_SPECIAL_INDEPENDENT_REGION] == 1.1
    assert CalculationNode.DAMAGE_NORMAL_BONUS_REGION not in breakdown


def test_region_inputs_are_frozen() -> None:
    input = CritRegionInput(crit_rate=0.5, crit_damage=1.0)

    with pytest.raises(FrozenInstanceError):
        input.crit_rate = 1.0  # type: ignore[misc]


def test_defense_region_input_uses_one_canonical_naming_direction() -> None:
    field_names = {field.name for field in fields(DefenseRegionInput)}

    assert field_names == {
        "attacker_level",
        "initial_defense",
        "defense_increase",
        "defense_reduction",
        "defense_ignore",
        "penetration_rate",
        "penetration_flat",
    }
    assert "ignore_defense" not in field_names
