from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from core.application.characters.config import CharacterSkillLevel
from core.application.characters.soldier0_anby import (
    SOLDIER0_ANBY_ID,
    Soldier0AnbyCompileConfig,
    compile_soldier0_anby,
    load_raw_record,
)
from core.application.characters.soldier0_anby.reviewed import (
    SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER,
    SOLDIER0_ANBY_CINEMA1_RULE_ID,
    SOLDIER0_ANBY_CINEMA6_RULE_ID,
    SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED,
    SOLDIER0_ANBY_CORE_RULE_ID,
    SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID,
    SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID,
    SOLDIER0_ANBY_SILVER_STAR_ACTIVE,
    SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE,
    SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID,
)
from core.application.equipment import SIGNATURE_WENGINE_BY_CHARACTER, load_wengine_raw_record
from core.application.equipment.wengine_ids import WENGINE_FUYUAN_CLEAN_ID
from core.data.loader import load_character_record, supported_character_ids
from core.presentation import calculation_service
from core.presentation.base_stats import character_base_stats
from core.presentation.catalog import supported_character_catalog
from core.presentation.registry import (
    equipment_capabilities_for_definition,
    registration_for,
)
from core.types import (
    CharacterId,
    DamageTag,
    FixedMultiplier,
    PanelStatDerivedValue,
    Resolved,
    SkillGroup,
    Unresolved,
    UnresolvedReason,
    WEngineId,
)
from web.api import app


client = TestClient(app)

ANBY = str(SOLDIER0_ANBY_ID)
RINA = "character:1211"
_BASIC_1 = "move-entry:soldier0-anby:1381:basic-stage-1"
_BASIC_3 = "move-entry:soldier0-anby:1381:basic-stage-3"
_EX = "move-entry:soldier0-anby:1381:ex-special-lightsplitter"
_CANGGUANG = "move-entry:soldier0-anby:1381:special-cangguang-main"
_WHITE_THUNDER = "move-entry:soldier0-anby:1381:white-thunder"
_CHAIN = "move-entry:soldier0-anby:1381:chain-thunder-leap"
_ULTIMATE = "move-entry:soldier0-anby:1381:ultimate-sky-sunder"
_CORE = str(SOLDIER0_ANBY_CORE_RULE_ID)
_EXTRA = str(SOLDIER0_ANBY_EXTRA_ABILITY_RULE_ID)
_C1 = str(SOLDIER0_ANBY_CINEMA1_RULE_ID)
_C6 = str(SOLDIER0_ANBY_CINEMA6_RULE_ID)
_P1_CRITICAL = str(SOLDIER0_ANBY_POTENTIAL_CRITICAL_RULE_ID)
_WHITE_RULE = "rule:character:1381:skill:cangguang-white-thunder"
_THUNDERCLAP_RULE = "rule:character:1381:skill:cangguang-thunderclap"
_WENGINE_STACK = "rule:wengine:14138:owner:1381:crit-damage-per-hit-category-stack"
_WENGINE_ELECTRIC = "rule:wengine:14138:owner:1381:electric-damage-at-three-stacks"
_ZHAO_CURTAIN = "condition:wengine:14134:owner:1341:ether-veil-team-crit-damage-active"
_ZHAO_CURTAIN_RULE = "rule:wengine:14134:owner:1341:team-crit-damage-after-ether-veil"


def _panel_stats(character_id: str) -> dict[str, object]:
    panel = character_base_stats(CharacterId(character_id))
    stats: dict[str, object] = {
        key: getattr(panel, key).value
        for key in (
            "hp",
            "attack",
            "defense",
            "impact",
            "crit_rate",
            "crit_damage",
            "anomaly_mastery",
            "anomaly_proficiency",
            "energy_regen",
            "penetration_rate",
            "penetration_flat",
        )
    }
    stats["element_damage_bonus"] = {
        element.value: value.value
        for element, value in panel.element_damage_bonus.items()
    }
    return stats


def _payload(
    move_entry_id: str,
    *,
    supporting: tuple[str, ...] = (),
    cinema: int = 0,
    potential: int = 0,
    conditions: dict[str, bool] | None = None,
    enabled: tuple[str, ...] = (),
    stacks: dict[str, int] | None = None,
    wengine: str | None = None,
    refinement: int = 1,
) -> dict[str, object]:
    team = [ANBY, *supporting]
    configs: dict[str, dict[str, object]] = {
        character_id: {"core_level": 1, "cinema_level": 0}
        for character_id in team
    }
    configs[ANBY] = {
        "core_level": 7,
        "cinema_level": cinema,
        "potential_level": potential,
    }
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        build: dict[str, object] = {
            "level": 60,
            "build_mode": "equipment-build",
            "base_stats": _panel_stats(character_id),
            "drive_discs": [],
        }
        if character_id == ANBY and wengine is not None:
            build.update(
                {
                    "wengine_id": wengine,
                    "wengine_level": 60,
                    "wengine_refinement": refinement,
                }
            )
        builds[character_id] = build
    return {
        "primary_character_id": ANBY,
        "supporting_character_ids": team[1:],
        "team_character_ids": team,
        "formation_character_ids": team,
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": conditions or {},
        "parameter_values": {},
        "enabled_rule_item_ids": list(enabled),
        "selected_trigger_inputs": [],
        "rule_stack_counts": stacks or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:soldier0-anby-test",
            "level": 70,
            "initial_defense": 857.0,
            "damage_resistance": {
                key: 0.0
                for key in (
                    "physical",
                    "fire",
                    "ice",
                    "electric",
                    "ether",
                    "wind",
                    "luminance",
                )
            },
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": False,
        },
    }


def _calculate(payload: dict[str, object]) -> dict[str, object]:
    response = client.post("/api/v1/moves/calculate", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def _event(result: dict[str, object], semantic_fragment: str) -> dict[str, object]:
    return next(item for item in result["events"] if semantic_fragment in item["semantic_id"])


def _events(result: dict[str, object], semantic_fragment: str) -> list[dict[str, object]]:
    return [item for item in result["events"] if semantic_fragment in item["semantic_id"]]


def _template_events(result: dict[str, object], template_semantic_id: str) -> list[dict[str, object]]:
    return [
        item
        for item in result["events"]
        if item["semantic_id"].split(":source", 1)[0] == template_semantic_id
    ]


def _normal_bonus(event: dict[str, object]) -> float:
    return next(
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "damage.normal-bonus"
    )


def _crit_damage_values(event: dict[str, object]) -> list[float]:
    return [
        item["value"]
        for item in event["modes"]["expected"]["calculation_breakdown"]
        if item["node"] == "character.current.crit-damage"
    ]


def test_soldier0_anby_raw_registry_curves_and_neutral_white_thunder_scope() -> None:
    raw_data = load_character_record(ANBY)
    raw = load_raw_record(raw_data, potential_level=0)
    assert (raw.name, raw.code_name, raw.rarity) == ("零号·安比", "Soldier 0 - Anby", 4)
    assert (raw.source_version, raw.source_url) == (
        "3.2",
        "https://static.nanoka.cc/zzz/3.2/zh/character/1381.json",
    )
    assert ANBY in supported_character_ids()
    assert Soldier0AnbyCompileConfig().core_level == 7
    assert Soldier0AnbyCompileConfig().cinema_level == 0
    assert Soldier0AnbyCompileConfig().potential_level == 0
    assert SIGNATURE_WENGINE_BY_CHARACTER[SOLDIER0_ANBY_ID] == WENGINE_FUYUAN_CLEAN_ID
    assert load_wengine_raw_record(WENGINE_FUYUAN_CLEAN_ID).source_url.endswith("/weapon/14138.json")
    catalog = next(item for item in supported_character_catalog() if item.character_id == ANBY)
    assert catalog.code_name == "Soldier 0 - Anby"
    fields = {
        item.field_id: item.value
        for item in registration_for(SOLDIER0_ANBY_ID).config_fields({}, (SOLDIER0_ANBY_ID,))
    }
    assert fields["core_level"] == 7
    assert fields["cinema_level"] == 0
    assert fields["potential_level"] == 0
    assert fields["skill_level:ultimate"] == 12

    p0 = compile_soldier0_anby(Soldier0AnbyCompileConfig(), raw)
    p1_raw = load_raw_record(raw_data, potential_level=1)
    p1 = compile_soldier0_anby(Soldier0AnbyCompileConfig(potential_level=1), p1_raw)
    p0_basic_3 = next(item for item in p0.move_entries if str(item.entry_id) == _BASIC_3)
    p1_basic_3 = next(item for item in p1.move_entries if str(item.entry_id) == _BASIC_3)
    assert p0_basic_3.multiplier_variants[0].multiplier.value.value == pytest.approx(1.604)
    assert p1_basic_3.multiplier_variants[0].multiplier.value.value == pytest.approx(2.002)

    white = next(
        item
        for item in p0.damage_event_templates
        if "special-cangguang:white-thunder" in str(item.ref.semantic_id)
    )
    assert white.ref.skill_group is None
    assert white.move_id is None
    assert white.ref.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})
    capabilities = equipment_capabilities_for_definition(p0)
    assert any(
        scope.skill_group is None
        and scope.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})
        for scope in capabilities.damage_scopes or ()
    )
    assert SkillGroup.SPECIAL_ATTACK in capabilities.skill_groups

    c1 = compile_soldier0_anby(
        Soldier0AnbyCompileConfig(cinema_level=1), raw
    )
    c1_white = next(
        item
        for item in c1.damage_event_templates
        if item.ref.template_id == SOLDIER0_ANBY_WHITE_THUNDER_TEMPLATE_ID
    )
    assert c1_white.ref.skill_group is None
    assert c1_white.move_id is None
    assert c1_white.ref.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})

    standalone_white_entry = next(
        item for item in p0.move_entries if str(item.entry_id) == _WHITE_THUNDER
    )
    standalone_white = next(
        item
        for item in p0.damage_event_templates
        if item.ref.template_id == standalone_white_entry.main_damage_event.template_id
    )
    assert standalone_white_entry.move_id is None
    assert standalone_white_entry.skill_group is None
    assert standalone_white_entry.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})
    assert standalone_white.ref.skill_group is None
    assert standalone_white.move_id is None
    assert standalone_white.ref.damage_tags == frozenset({DamageTag.FOLLOW_UP_ATTACK})

    for potential_level in range(7):
        selected_raw = load_raw_record(raw_data, potential_level=potential_level)
        for cinema_level in range(7):
            definition = compile_soldier0_anby(
                Soldier0AnbyCompileConfig(
                    potential_level=potential_level,
                    cinema_level=cinema_level,
                    additional_ability_eligible=True,
                ),
                selected_raw,
            )
            assert any(str(item.rule_id) == _C6 for item in definition.rule_items)
            c6 = next(item for item in definition.rule_items if str(item.rule_id) == _C6)
            assert len(c6.effects) == (3 if cinema_level == 6 else 0)


def test_soldier0_anby_cangguang_proc_and_c6_use_current_proc_and_enabled_white_rule() -> None:
    conditions = {
        str(SOLDIER0_ANBY_WHITE_THUNDER_ACTIVE): True,
        str(SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER): False,
        str(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED): True,
    }
    enabled = (_WHITE_RULE, _THUNDERCLAP_RULE, _C6, _P1_CRITICAL)
    six_not_third = _calculate(
        _payload(
            _CANGGUANG,
            cinema=6,
            potential=1,
            conditions=conditions,
            enabled=enabled,
        )
    )
    assert len(_events(six_not_third, "special-cangguang:white-thunder")) == 1
    assert len(_events(six_not_third, "electromagnetic-vortex")) == 1
    assert not _template_events(six_not_third, "event:soldier0-anby:1381:cinema1:thunderclap")
    assert not _events(six_not_third, "potential:critical-cangguang")

    disabled_white = _calculate(
        _payload(
            _CANGGUANG,
            cinema=6,
            potential=1,
            conditions=conditions,
            enabled=(_THUNDERCLAP_RULE, _C6, _P1_CRITICAL),
        )
    )
    assert len(disabled_white["events"]) == 1
    assert not _events(disabled_white, "electromagnetic-vortex")
    assert not _template_events(disabled_white, "event:soldier0-anby:1381:cinema1:thunderclap")

    third_and_white_disabled = _calculate(
        _payload(
            _CANGGUANG,
            cinema=6,
            potential=1,
            conditions={**conditions, str(SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER): True},
            enabled=(_THUNDERCLAP_RULE, _C6, _P1_CRITICAL),
        )
    )
    assert len(third_and_white_disabled["events"]) == 1
    assert not _events(third_and_white_disabled, "electromagnetic-vortex")
    assert not _template_events(third_and_white_disabled, "event:soldier0-anby:1381:cinema1:thunderclap")

    c6_off = _calculate(
        _payload(
            _CANGGUANG,
            cinema=6,
            potential=1,
            conditions=conditions,
            enabled=(_WHITE_RULE, _THUNDERCLAP_RULE, _P1_CRITICAL),
        )
    )
    assert len(_events(c6_off, "special-cangguang:white-thunder")) == 1
    assert not _events(c6_off, "electromagnetic-vortex")

    c6_locked = _calculate(
        _payload(
            _CANGGUANG,
            cinema=5,
            potential=1,
            conditions=conditions,
            enabled=(_WHITE_RULE, _THUNDERCLAP_RULE, _C6, _P1_CRITICAL),
        )
    )
    assert len(_events(c6_locked, "special-cangguang:white-thunder")) == 1
    assert not _events(c6_locked, "electromagnetic-vortex")

    third_proc = _calculate(
        _payload(
            _CANGGUANG,
            cinema=6,
            potential=1,
            conditions={**conditions, str(SOLDIER0_ANBY_CANGGUANG_THIRD_WHITE_THUNDER): True},
            enabled=enabled,
        )
    )
    assert len(_events(third_proc, "special-cangguang:white-thunder")) == 1
    assert len(_template_events(third_proc, "event:soldier0-anby:1381:cinema1:thunderclap")) == 1
    assert len(_events(third_proc, "potential:critical-cangguang")) == 1
    assert len(_events(third_proc, "electromagnetic-vortex")) == 1


def test_soldier0_anby_ex_c1_chain_creates_three_white_thunder_and_one_vortex() -> None:
    conditions = {str(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED): True}
    enabled = (_C1, _C6, _P1_CRITICAL)
    active = _calculate(
        _payload(_EX, cinema=6, potential=1, conditions=conditions, enabled=enabled)
    )
    white_events = _template_events(active, "event:soldier0-anby:1381:cinema1:white-thunder")
    assert len(white_events) == 1
    assert white_events[0]["repeat_count"] == 3
    direct_white = _calculate(
        _payload(
            _WHITE_THUNDER,
            cinema=6,
            potential=1,
            conditions={str(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED): False},
        )
    )
    direct_white_value = _event(direct_white, ":white-thunder:main")["modes"]["expected"]["known_value"]
    assert white_events[0]["modes"]["expected"]["known_value"] == pytest.approx(
        direct_white_value * 3
    )
    assert len(_template_events(active, "event:soldier0-anby:1381:cinema1:thunderclap")) == 1
    assert len(_events(active, "potential:critical-cangguang")) == 1
    assert len(_events(active, "electromagnetic-vortex")) == 1

    c1_off = _calculate(
        _payload(_EX, cinema=6, potential=1, conditions=conditions, enabled=(_C6, _P1_CRITICAL))
    )
    assert len(c1_off["events"]) == 1
    assert not _events(c1_off, "electromagnetic-vortex")
    assert not _template_events(c1_off, "event:soldier0-anby:1381:cinema1:white-thunder")


@pytest.mark.parametrize("move_entry_id", (_CHAIN, _ULTIMATE))
def test_soldier0_anby_potential_followup_identity_obeys_extra_eligibility_and_toggle(
    move_entry_id: str,
) -> None:
    marked = {str(SOLDIER0_ANBY_SILVER_STAR_ACTIVE): True}
    active = _calculate(
        _payload(
            move_entry_id,
            supporting=(RINA,),
            potential=1,
            conditions=marked,
            enabled=(_EXTRA,),
        )
    )
    assert _normal_bonus(_event(active, "chain" if move_entry_id == _CHAIN else "ultimate")) == pytest.approx(0.25)

    disabled = _calculate(
        _payload(move_entry_id, supporting=(RINA,), potential=1, conditions=marked, enabled=())
    )
    assert _normal_bonus(disabled["events"][0]) == pytest.approx(0.0)

    ineligible = _calculate(
        _payload(move_entry_id, potential=1, conditions=marked, enabled=(_EXTRA,))
    )
    assert _normal_bonus(ineligible["events"][0]) == pytest.approx(0.0)

    no_potential = _calculate(
        _payload(move_entry_id, supporting=(RINA,), conditions=marked, enabled=(_EXTRA,))
    )
    assert _normal_bonus(no_potential["events"][0]) == pytest.approx(0.0)


def test_soldier0_anby_signature_14138_three_stack_electric_scope_and_disabled_stack_rule() -> None:
    common = _payload(
        "move-entry:soldier0-anby:1381:special-star-thunder",
        wengine="wengine:14138",
        refinement=1,
        enabled=(_WENGINE_STACK, _WENGINE_ELECTRIC),
        stacks={_WENGINE_STACK: 3},
    )
    full = _calculate(common)
    assert full["resolved_character_snapshots"][0]["stats"]["crit_damage"] > _panel_stats(ANBY)["crit_damage"]
    assert _normal_bonus(full["events"][0]) == pytest.approx(0.20)

    stack_rule_disabled = _calculate(
        {
            **common,
            "enabled_rule_item_ids": [_WENGINE_ELECTRIC],
        }
    )
    assert _normal_bonus(stack_rule_disabled["events"][0]) == pytest.approx(0.0)

    two_stacks = _calculate({**common, "rule_stack_counts": {_WENGINE_STACK: 2}})
    assert _normal_bonus(two_stacks["events"][0]) == pytest.approx(0.0)


def test_soldier0_anby_standalone_white_thunder_has_neutral_identity_and_c6_gate() -> None:
    conditions = {str(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED): True}
    active = _calculate(
        _payload(_WHITE_THUNDER, cinema=6, conditions=conditions, enabled=(_C6,))
    )
    assert len(_template_events(active, "event:soldier0-anby:1381:white-thunder:main")) == 1
    assert len(_events(active, "electromagnetic-vortex")) == 1

    c6_off = _calculate(_payload(_WHITE_THUNDER, cinema=6, conditions=conditions))
    assert not _events(c6_off, "electromagnetic-vortex")

    c6_locked = _calculate(
        _payload(_WHITE_THUNDER, cinema=5, conditions=conditions, enabled=(_C6,))
    )
    assert not _events(c6_locked, "electromagnetic-vortex")

    no_current_sixth = _calculate(
        _payload(
            _WHITE_THUNDER,
            cinema=6,
            conditions={str(SOLDIER0_ANBY_CINEMA6_VORTEX_TRIGGERED): False},
            enabled=(_C6,),
        )
    )
    assert not _events(no_current_sixth, "electromagnetic-vortex")


def test_soldier0_anby_selected_potential_and_skill_levels_match_exact_source_curves() -> None:
    raw_data = load_character_record(ANBY)
    source_levels = (
        (0, 12, 34.707, 3.344),
        (3, 14, 37.863, 3.648),
        (5, 16, 41.019, 3.952),
    )
    for cinema, effective_level, expected_ultimate, expected_white in source_levels:
        raw = load_raw_record(raw_data, potential_level=1)
        definition = compile_soldier0_anby(
            Soldier0AnbyCompileConfig(
                cinema_level=cinema,
                potential_level=1,
                skill_levels=(
                    CharacterSkillLevel(SkillGroup.ULTIMATE, 12),
                    CharacterSkillLevel(SkillGroup.SPECIAL_ATTACK, 12),
                ),
            ),
            raw,
        )
        ultimate = next(item for item in definition.move_entries if str(item.entry_id) == _ULTIMATE)
        white = next(item for item in definition.move_entries if str(item.entry_id) == _WHITE_THUNDER)
        assert ultimate.multiplier_variants[0].multiplier.value.value == pytest.approx(expected_ultimate)
        assert white.multiplier_variants[0].multiplier.value.value == pytest.approx(expected_white)
        assert effective_level == 12 + (2 if cinema >= 3 else 0) + (2 if cinema >= 5 else 0)

    raw = load_raw_record(raw_data, potential_level=1)
    capped = compile_soldier0_anby(
        Soldier0AnbyCompileConfig(
            cinema_level=5,
            potential_level=1,
            skill_levels=(
                CharacterSkillLevel(SkillGroup.ULTIMATE, 16),
                CharacterSkillLevel(SkillGroup.SPECIAL_ATTACK, 16),
            ),
        ),
        raw,
    )
    assert next(item for item in capped.move_entries if str(item.entry_id) == _ULTIMATE).multiplier_variants[0].multiplier.value.value == pytest.approx(41.019)

    c6 = compile_soldier0_anby(
        Soldier0AnbyCompileConfig(cinema_level=6, potential_level=1), raw
    )
    child_values = {
        str(item.template.template_id): item.multiplier.value.value
        for item in c6.independent_derived_damage_events
        if isinstance(item.multiplier, FixedMultiplier)
        and isinstance(item.multiplier.value, Resolved)
    }
    assert child_values["template:soldier0-anby:1381:cinema1:white-thunder"] == pytest.approx(3.952)
    assert child_values["template:soldier0-anby:1381:cinema1:thunderclap"] == pytest.approx(4.446)
    assert child_values["template:soldier0-anby:1381:potential:critical-cangguang"] == pytest.approx(5.899)
    assert child_values["template:soldier0-anby:1381:cinema6:electromagnetic-vortex"] == pytest.approx(10.0)
    assert next(
        item.multiplier_variants[0].multiplier.value.value
        for item in c6.move_entries
        if str(item.entry_id) == _EX
    ) == pytest.approx(8.986)
    assert child_values["template:soldier0-anby:1381:cinema1:white-thunder"] * 3 == pytest.approx(11.856)
    assert next(
        item.repeat_count
        for item in c6.independent_derived_damage_events
        if str(item.template.template_id) == "template:soldier0-anby:1381:cinema1:white-thunder"
    ) == 3


def test_soldier0_anby_potential_derived_values_do_not_stack_potential_increases() -> None:
    raw_data = load_character_record(ANBY)
    expected_extra = (0.25, 0.25, 0.34, 0.38, 0.42, 0.46, 0.50)
    for potential_level, expected_bonus in enumerate(expected_extra):
        raw = load_raw_record(raw_data, potential_level=potential_level)
        definition = compile_soldier0_anby(
            Soldier0AnbyCompileConfig(
                potential_level=potential_level,
                additional_ability_eligible=True,
            ),
            raw,
        )
        core = next(item for item in definition.rule_items if str(item.rule_id) == _CORE)
        core_value = next(
            effect.result.value
            for effect in core.effects
            if isinstance(effect.result.value, PanelStatDerivedValue)
        )
        assert isinstance(core_value.coefficient, Resolved)
        assert core_value.coefficient.value == pytest.approx(0.30 if potential_level == 0 else 0.35)
        extra = next(item for item in definition.rule_items if str(item.rule_id) == _EXTRA)
        extra_value = next(
            effect.result.value
            for effect in extra.effects
            if isinstance(effect.result.value, Resolved)
            and effect.result.modifier_path.value == "damage.normal-bonus"
        )
        assert extra_value.value == pytest.approx(expected_bonus)


def test_soldier0_anby_core_reads_owner_final_crit_damage_not_recipient_crit_damage() -> None:
    pulchra = "character:1351"
    zhao = "character:1341"

    def calculate(recipient_crit_damage: float) -> dict[str, object]:
        team = [pulchra, ANBY, zhao]
        configs = {
            pulchra: {"core_level": 7, "cinema_level": 0},
            ANBY: {"core_level": 7, "cinema_level": 0, "potential_level": 1},
            zhao: {"core_level": 7, "cinema_level": 0},
        }
        pulchra_stats = _panel_stats(pulchra)
        pulchra_stats["crit_damage"] = recipient_crit_damage
        builds: dict[str, dict[str, object]] = {
            pulchra: {
                "level": 60,
                "build_mode": "manual-panel",
                "out_of_combat_stats": pulchra_stats,
            },
            ANBY: {
                "level": 60,
                "build_mode": "equipment-build",
                "base_stats": _panel_stats(ANBY),
                "drive_discs": [],
                "wengine_id": "wengine:14138",
                "wengine_level": 60,
                "wengine_refinement": 1,
            },
            zhao: {
                "level": 60,
                "build_mode": "equipment-build",
                "base_stats": _panel_stats(zhao),
                "drive_discs": [],
                "wengine_id": "wengine:14134",
                "wengine_level": 60,
                "wengine_refinement": 5,
            },
        }
        return _calculate(
            {
                **_payload(_CHAIN),
                "primary_character_id": pulchra,
                "supporting_character_ids": [ANBY, zhao],
                "team_character_ids": team,
                "formation_character_ids": team,
                "move_entry_id": "move-entry:pulchra:1351:nightmare-shadow-main",
                "compile_configs": configs,
                "enabled_rule_item_ids": [
                    _CORE,
                    "rule:wengine:14138:owner:1381:crit-damage",
                    _WENGINE_STACK,
                    _ZHAO_CURTAIN_RULE,
                ],
                "rule_stack_counts": {_WENGINE_STACK: 3},
                "condition_values": {
                    str(SOLDIER0_ANBY_SILVER_STAR_ACTIVE): True,
                    _ZHAO_CURTAIN: True,
                },
                "character_builds": builds,
            }
        )

    baseline = calculate(0.50)
    recipient_changed = calculate(0.90)
    owner_snapshot = next(
        item
        for item in baseline["resolved_character_snapshots"]
        if item["character_id"] == ANBY
    )
    changed_owner_snapshot = next(
        item
        for item in recipient_changed["resolved_character_snapshots"]
        if item["character_id"] == ANBY
    )
    # 14138's permanent + stack Crit Damage and Zhao's active TEAM Crit Damage
    # all contribute to Anby's final current value used as the Core source.
    assert owner_snapshot["stats"]["crit_damage"] == pytest.approx(2.06)
    assert changed_owner_snapshot["stats"]["crit_damage"] == pytest.approx(2.06)
    recipient_snapshot = next(
        item
        for item in baseline["resolved_character_snapshots"]
        if item["character_id"] == pulchra
    )
    changed_recipient_snapshot = next(
        item
        for item in recipient_changed["resolved_character_snapshots"]
        if item["character_id"] == pulchra
    )
    assert recipient_snapshot["stats"]["crit_damage"] == pytest.approx(0.98)
    assert changed_recipient_snapshot["stats"]["crit_damage"] == pytest.approx(1.38)
    baseline_event = _event(baseline, "nightmare-shadow-main")
    changed_event = _event(recipient_changed, "nightmare-shadow-main")
    baseline_value = _crit_damage_values(baseline_event)
    changed_value = _crit_damage_values(changed_event)
    assert baseline_value == [pytest.approx(0.98 + 2.06 * 0.35)]
    assert changed_value == [pytest.approx(1.38 + 2.06 * 0.35)]
    assert changed_value[0] - 1.38 == pytest.approx(baseline_value[0] - 0.98)
    assert _normal_bonus(baseline_event) == pytest.approx(0.0)


def test_soldier0_anby_missing_owner_current_crit_damage_is_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pulchra = "character:1351"
    team = [pulchra, ANBY]
    configs = {
        pulchra: {"core_level": 7, "cinema_level": 0},
        ANBY: {"core_level": 7, "cinema_level": 0, "potential_level": 0},
    }
    builds: dict[str, dict[str, object]] = {
        pulchra: {
            "level": 60,
            "build_mode": "manual-panel",
            "out_of_combat_stats": _panel_stats(pulchra),
        },
        ANBY: {
            "level": 60,
            "build_mode": "equipment-build",
            "base_stats": _panel_stats(ANBY),
            "drive_discs": [],
        },
    }

    original_build_records = calculation_service._build_records

    def with_missing_anby_current_crit_damage(build_inputs, definitions):
        records = original_build_records(build_inputs, definitions)
        updated = []
        for record in records:
            if record.snapshot.character_id == CharacterId(ANBY):
                unresolved_cd = Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="test fixture: Anby's current Crit Damage is unavailable",
                )
                current_stats = replace(
                    record.snapshot.settlement_stats,
                    crit_damage=unresolved_cd,
                )
                record = replace(
                    record,
                    snapshot=replace(record.snapshot, settlement_stats=current_stats),
                )
            updated.append(record)
        return tuple(updated)

    monkeypatch.setattr(
        calculation_service, "_build_records", with_missing_anby_current_crit_damage
    )

    def calculate(move_entry_id: str, *, core_enabled: bool = True):
        return _calculate(
            {
                **_payload(_BASIC_1),
                "primary_character_id": pulchra,
                "supporting_character_ids": [ANBY],
                "team_character_ids": team,
                "formation_character_ids": team,
                "move_entry_id": move_entry_id,
                "compile_configs": configs,
                "enabled_rule_item_ids": [_CORE] if core_enabled else [],
                "condition_values": {
                    str(SOLDIER0_ANBY_SILVER_STAR_ACTIVE): True,
                },
                "character_builds": builds,
            }
        )

    basic = calculate("move-entry:pulchra:1351:basic-jab-1")
    assert basic["totals"]["expected"]["complete"] is True
    assert _event(basic, "basic-jab-1")["modes"]["expected"]["status"] == "calculated"

    followup = calculate("move-entry:pulchra:1351:nightmare-shadow-main")
    assert followup["totals"]["expected"]["complete"] is False
    followup_event = _event(followup, "nightmare-shadow-main")
    assert followup_event["modes"]["expected"]["status"] == "blocked"
    assert any(
        "crit damage" in item["message"].lower()
        for item in followup_event["modes"]["expected"]["diagnostics"]
    )

    core_disabled = calculate(
        "move-entry:pulchra:1351:nightmare-shadow-main", core_enabled=False
    )
    assert core_disabled["totals"]["expected"]["complete"] is True
