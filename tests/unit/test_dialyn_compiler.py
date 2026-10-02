from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from core.application.characters.dialyn import (
    DIALYN_ID,
    DIALYN_REVIEWED_MAPPING,
    DialynCompileConfig,
    compile_dialyn,
    load_raw_record,
)
from core.application.execution.event_factory import instantiate_damage_event
from core.application.execution.static_records import static_attribute_anomaly_record
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record, supported_character_ids
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    compile_registered_definition,
    config_fields_for,
    registration_for,
)
from core.types import (
    BattleStateId,
    CharacterSnapshot,
    DamageTag,
    DamageType,
    Element,
    EnemyId,
    FixedMultiplier,
    Resolved,
    SkillGroup,
)


DIALYN = str(DIALYN_ID)
ASTRA = "character:1311"
YE = "character:1431"
YIXUAN = "character:1371"
TRIGGER = "character:1361"


def _stats(
    element: str = "physical",
    *,
    hp: float = 16000.0,
    attack: float = 700.0,
    impact: float = 110.0,
    crit_rate: float = 0.194,
    crit_damage: float = 0.50,
) -> dict[str, object]:
    return {
        "hp": hp,
        "attack": attack,
        "defense": 500.0,
        "impact": impact,
        "anomaly_mastery": 94.0,
        "anomaly_proficiency": 93.0,
        "energy_regen": 1.20,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {"physical": 0.20, "ether": 0.0},
    }


def _drive_discs():
    def substats(*keys: str):
        return [{"stat": key, "roll_count": 2} for key in keys]

    return [
        {"slot": 1, "set_id": "drive-disc:31000", "main_stat": "hp-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 2, "set_id": "drive-disc:31000", "main_stat": "attack-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 3, "set_id": "drive-disc:31000", "main_stat": "defense-flat", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 4, "set_id": "drive-disc:31000", "main_stat": "attack-percent", "substats": substats("crit-rate", "crit-damage", "penetration-flat", "anomaly-proficiency-flat")},
        {"slot": 5, "set_id": "drive-disc:31000", "main_stat": "physical-damage-bonus", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
        {"slot": 6, "set_id": "drive-disc:31000", "main_stat": "energy-regen-percent", "substats": substats("attack-percent", "crit-rate", "crit-damage", "anomaly-proficiency-flat")},
    ]


def _payload(
    *,
    primary: str = DIALYN,
    supporting: tuple[str, ...] = (),
    move_entry_id: str = "move-entry:character:1481:basic-service-1",
    core_level: int = 1,
    cinema_level: int = 0,
    skill_levels: dict[str, int] | None = None,
    condition_values: dict[str, bool] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    selected_trigger_inputs: tuple[dict[str, object], ...] = (),
    parameter_values: dict[str, int] | None = None,
    is_stunned: bool = False,
    manual_stats: dict[str, dict[str, object]] | None = None,
    equipment_build: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        configs[character_id] = {"core_level": 1, "cinema_level": 0}
        if character_id == DIALYN:
            configs[character_id] = {"core_level": core_level, "cinema_level": cinema_level}
            if skill_levels:
                configs[character_id]["skill_levels"] = skill_levels
            builds[character_id] = (
                {"level": 60, "build_mode": "equipment-build", "drive_discs": _drive_discs()}
                if equipment_build
                else {"level": 60, "out_of_combat_stats": (manual_stats or {}).get(character_id, _stats())}
            )
        elif character_id == ASTRA:
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (manual_stats or {}).get(
                    character_id,
                    _stats("ether", hp=10000.0, attack=800.0, crit_rate=0.30, crit_damage=0.30),
                ),
            }
        elif character_id == YIXUAN:
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (manual_stats or {}).get(
                    character_id,
                    _stats("ether", hp=12000.0, attack=1000.0, crit_rate=0.70, crit_damage=1.10),
                ),
            }
        elif character_id == TRIGGER:
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (manual_stats or {}).get(
                    character_id,
                    _stats("physical", hp=9000.0, attack=700.0, crit_rate=0.20, crit_damage=0.50),
                ),
            }
        else:
            raise AssertionError(f"no Dialyn test build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:dialyn-test",
            "level": 60,
            "initial_defense": 1000.0,
            "damage_resistance": {"physical": 0.20, "ether": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": is_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": list(selected_trigger_inputs),
        "rule_stack_counts": {},
    }


def _event(result, semantic_id: str | None = None):
    events = result["events"]
    return next(item for item in events if item["semantic_id"] == semantic_id) if semantic_id else events[0]


def _breakdown(event, mode: str = "expected"):
    return event["modes"][mode]["calculation_breakdown"]


def _node(event, name: str, mode: str = "expected"):
    return next(item for item in _breakdown(event, mode) if item["node"] == name)


def _modifier(event, effect_id: str):
    return next(
        item
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["effect_id"] == effect_id
    )


def _raw():
    return load_raw_record(load_character_record(DIALYN))


def test_dialyn_source_registration_panel_and_all_raw_damage_curves() -> None:
    raw = _raw()
    assert raw.character_id == DIALYN_ID
    assert raw.name == "琉音"
    assert raw.code_name == "Dialyn"
    assert raw.specialty == "击破"
    assert raw.element == "物理"
    assert raw.rarity == 4
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1481.json"
    assert DIALYN in supported_character_ids()

    mapped = {
        (spec.source_name, parameter.parameter_name, parameter.source_skill_id)
        for spec in DIALYN_REVIEWED_MAPPING.moves
        for parameter in spec.parameters
    }
    raw_damage_curves = {
        (move.name, parameter.name, source_skill_id)
        for move in raw.moves
        for parameter in move.parameters
        if parameter.format == "%" and "伤害倍率" in parameter.name
        for source_skill_id, _curve in parameter.source_curves
    }
    assert mapped == raw_damage_curves
    assert not any("招架支援：拒绝通话" in spec.source_name for spec in DIALYN_REVIEWED_MAPPING.moves)
    guessing = [item for item in DIALYN_REVIEWED_MAPPING.moves if item.source_name == "普通攻击：猜拳把戏"]
    assert [(item.parameters[0].parameter_name, item.parameters[0].source_skill_id) for item in guessing] == [
        ("一段伤害倍率", "1481005"),
        ("二段伤害倍率", "1481006"),
        ("三段伤害倍率", "1481007"),
        ("四段伤害倍率", "1481008"),
    ]

    registration = registration_for(DIALYN)
    assert registration.role.value == "stun"
    assert registration.base_element is Element.PHYSICAL
    assert registration.catalog.rarity == "S"
    assert registration.equipment_capabilities.possible_elements == {Element.PHYSICAL}
    assert (Path(__file__).parents[2] / "frontend" / "public" / "characters" / "IconRole54.webp").is_file()
    base = character_base_stats(DIALYN)
    assert base.hp.value == pytest.approx(8250.5871)
    assert base.attack.value == pytest.approx(758.2048)
    assert base.defense.value == pytest.approx(612.6038)
    assert base.impact.value == pytest.approx(110.0)
    assert base.crit_rate.value == pytest.approx(0.194)
    assert base.crit_damage.value == pytest.approx(0.50)
    assert base.anomaly_mastery.value == pytest.approx(94.0)
    assert base.anomaly_proficiency.value == pytest.approx(93.0)
    assert base.energy_regen.value == pytest.approx(1.20)
    fields = config_fields_for(DIALYN, {"core_level": 7, "cinema_level": 4}, (DIALYN,))
    assert {field.field_id for field in fields} >= {"core_level", "cinema_level", "skill_level:ultimate"}


def test_dialyn_all_damage_moves_use_raw_curve_and_real_crit_modes() -> None:
    result = calculate_payload(_payload())
    event = _event(result)
    assert event["damage_type"] == DamageType.DIRECT.value
    assert _node(event, "damage.skill-multiplier")["value"] == pytest.approx(0.520)
    assert event["modes"]["non-crit"]["known_value"] < event["modes"]["expected"]["known_value"]
    assert event["modes"]["expected"]["known_value"] < event["modes"]["full-crit"]["known_value"]


@pytest.mark.parametrize(
    ("initial_crit_rate", "core_level", "expected_bonus"),
    ((0.40, 7, 0.0), (0.80, 7, 60.0), (1.00, 7, 100.0), (0.80, 1, 42.0)),
)
def test_dialyn_core_impact_reads_initial_crit_rate_and_caps(
    initial_crit_rate: float,
    core_level: int,
    expected_bonus: float,
) -> None:
    result = calculate_payload(
        _payload(
            core_level=core_level,
            manual_stats={DIALYN: _stats(impact=110.0, crit_rate=initial_crit_rate)},
            enabled_rule_item_ids=("rule:character:1481:core:initial-crit-impact",),
        )
    )
    snapshot = result["resolved_character_snapshots"][0]["stats"]
    assert snapshot["impact"] == pytest.approx(110.0 + expected_bonus)
    trace = next(
        item
        for item in result["panel_traces"]
        if item["effect_id"] == "effect:character:1481:core:initial-crit-impact"
    )
    assert trace["resolved_value"] == pytest.approx(expected_bonus)
    baseline = calculate_payload(
        _payload(
            core_level=core_level,
            manual_stats={DIALYN: _stats(impact=110.0, crit_rate=initial_crit_rate)},
        )
    )
    assert baseline["totals"]["expected"]["value"] == pytest.approx(
        result["totals"]["expected"]["value"]
    )


def test_dialyn_initial_crit_impact_reaches_the_static_anomaly_record() -> None:
    result = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-assault",
            core_level=7,
            manual_stats={DIALYN: _stats(impact=110.0, crit_rate=0.80)},
            enabled_rule_item_ids=("rule:character:1481:core:initial-crit-impact",),
        )
    )
    settlement_impact = next(
        item["stats"]["impact"]
        for item in result["resolved_character_snapshots"]
        if item["character_id"] == DIALYN
    )
    assert settlement_impact == pytest.approx(170.0)
    definition = compile_dialyn(DialynCompileConfig(core_level=7), _raw())
    template = next(
        item
        for item in definition.damage_event_templates
        if str(item.ref.template_id) == "template:character:1481:physical-assault"
    )
    event = instantiate_damage_event(
        template,
        FixedMultiplier(Resolved(1.0)),
        battle_state_id=BattleStateId("battle:dialyn-impact-record"),
        target_enemy=EnemyId("enemy:dialyn-impact-record"),
        created_at=0.0,
    ).event
    panel = replace(character_base_stats(DIALYN), impact=Resolved(settlement_impact))
    assembly = static_attribute_anomaly_record(
        event,
        (CharacterSnapshot(DIALYN_ID, 60, panel),),
    )
    assert assembly is not None and assembly.record is not None
    assert assembly.record.weighted_impact_strength == Resolved(246.5)


def test_dialyn_core_skill_levels_use_real_raw_curves() -> None:
    c0 = calculate_payload(_payload(move_entry_id="move-entry:character:1481:ex-paper"))
    c3 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:ex-paper",
            cinema_level=3,
        )
    )
    assert _node(_event(c0), "damage.skill-multiplier")["value"] == pytest.approx(14.035)
    assert _node(_event(c3), "damage.skill-multiplier")["value"] == pytest.approx(15.311)


def test_dialyn_good_review_c1_c4_and_extra_ability_have_separate_scopes() -> None:
    extra_rule = "rule:character:1481:extra-ability:good-review-team-damage"
    c1_rule = "rule:character:1481:cinema1:good-review-resistance-ignore"
    c4_rule = "rule:character:1481:cinema4:good-review-attack"
    solo = compile_registered_definition(
        DIALYN,
        {"core_level": 1, "cinema_level": 4},
        (DIALYN,),
    )
    with_rupture = compile_registered_definition(
        DIALYN,
        {"core_level": 1, "cinema_level": 4},
        (DIALYN, YIXUAN),
    )
    with_attack = compile_registered_definition(
        DIALYN,
        {"core_level": 1, "cinema_level": 4},
        (DIALYN, YE),
    )
    solo_extra = next(item for item in solo.rule_items if str(item.rule_id) == extra_rule)
    team_extra = next(item for item in with_rupture.rule_items if str(item.rule_id) == extra_rule)
    attack_extra = next(item for item in with_attack.rule_items if str(item.rule_id) == extra_rule)
    assert solo_extra.eligibility is RuleEligibility.INELIGIBLE
    assert team_extra.eligibility is RuleEligibility.ELIGIBLE
    assert attack_extra.eligibility is RuleEligibility.ELIGIBLE

    result = calculate_payload(
        _payload(
            supporting=(YIXUAN,),
            move_entry_id="move-entry:character:1481:ex-stone",
            cinema_level=4,
            condition_values={"condition:dialyn:good-review-active": True},
            enabled_rule_item_ids=(
                extra_rule,
                "rule:character:1481:extra-ability:ex-special-crit-damage",
                c1_rule,
                c4_rule,
            ),
            manual_stats={DIALYN: _stats(attack=700.0, crit_rate=0.80)},
        )
    )
    event = _event(result)
    dialyn_snapshot = next(item["stats"] for item in result["resolved_character_snapshots"] if item["character_id"] == DIALYN)
    yixuan_snapshot = next(item["stats"] for item in result["resolved_character_snapshots"] if item["character_id"] == YIXUAN)
    assert dialyn_snapshot["attack"] == pytest.approx(1200.0)
    assert yixuan_snapshot["attack"] == pytest.approx(1000.0)
    assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.40)
    assert _node(event, "resistance.damage-ignore")["value"] == pytest.approx(0.15)
    assert any(
        item["effect_id"] == "effect:character:1481:extra-ability:ex-special-crit-damage"
        and item["value"] == pytest.approx(0.50)
        for item in event["common_application_trace"]["event_stat_modifiers"]
    )

    locked = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:ex-stone",
            cinema_level=4,
            condition_values={"condition:dialyn:good-review-active": True},
            enabled_rule_item_ids=(
                extra_rule,
                "rule:character:1481:extra-ability:ex-special-crit-damage",
                c1_rule,
                c4_rule,
            ),
            manual_stats={DIALYN: _stats(attack=700.0, crit_rate=0.80)},
        )
    )
    locked_snapshot = locked["resolved_character_snapshots"][0]["stats"]
    assert locked_snapshot["attack"] == pytest.approx(700.0)
    assert _node(_event(locked), "damage.normal-bonus")["value"] == pytest.approx(0.0)
    assert _node(_event(locked), "resistance.damage-ignore")["value"] == pytest.approx(0.0)


def test_dialyn_complaint_core_and_cinema2_apply_enemy_vulnerability_and_team_damage() -> None:
    ids = (
        "rule:character:1481:core:paper-malicious-complaint-stun-vulnerability",
        "rule:character:1481:cinema2:complaint-stun-vulnerability",
        "rule:character:1481:cinema2:complaint-damage-bonus",
    )
    result = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(DIALYN,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            core_level=7,
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=ids,
            is_stunned=True,
        )
    )
    event = _event(result)
    assert event["damage_type"] == DamageType.PENETRATION.value
    assert _node(event, "damage.normal-bonus")["value"] == pytest.approx(0.15)
    stun_values = [
        item["value"]
        for item in event["common_application_trace"]["applied_modifiers"]
        if item["modifier_path"] == "vulnerability.enemy-stun"
        and item["effect_id"].startswith("effect:character:1481:")
    ]
    assert sum(stun_values) == pytest.approx(0.50)

    not_stunned = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(DIALYN,),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            core_level=7,
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=ids,
            is_stunned=False,
        )
    )
    assert _node(_event(not_stunned), "damage.normal-bonus")["value"] == pytest.approx(0.15)
    assert _node(_event(not_stunned), "vulnerability.effective-stun")["value"] == pytest.approx(0.0)


def test_dialyn_static_physical_assault_and_disorder_absorb_cinema2_normal_bonus_once() -> None:
    complaint_rule = "rule:character:1481:cinema2:complaint-damage-bonus"
    stats = {
        DIALYN: {
            **_stats(hp=12000.0, attack=1000.0, impact=110.0, crit_rate=0.80, crit_damage=0.90),
            "anomaly_proficiency": 100.0,
            "element_damage_bonus": {"physical": 0.30, "ether": 0.0},
        }
    }
    anomaly_base = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-assault",
            manual_stats=stats,
        )
    )
    anomaly_bonus = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-assault",
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=(complaint_rule,),
            manual_stats=stats,
        )
    )
    anomaly_trace = _event(anomaly_bonus)["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert anomaly_base["totals"]["expected"]["value"] == pytest.approx(6563.733333333334)
    assert anomaly_bonus["totals"]["expected"]["value"] == pytest.approx(7321.08717948718)
    assert anomaly_trace["element_bonus"] == pytest.approx(0.30)
    assert anomaly_trace["normal_bonus"] == pytest.approx(0.15)
    assert anomaly_trace["final_strength"] == pytest.approx(2900.0)
    assert anomaly_base["events"][0]["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"] == pytest.approx(2600.0)
    assert _event(anomaly_bonus)["damage_type"] == "anomaly"
    assert _node(_event(anomaly_bonus), "anomaly.attribute.multiplier")["value"] == pytest.approx(7.13)
    assert anomaly_bonus["totals"]["expected"]["complete"] is True
    assert anomaly_bonus["display_modes"] == ["expected"]

    disorder_base = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-disorder",
            manual_stats=stats,
        )
    )
    assert _node(_event(disorder_base), "disorder.total-multiplier")["value"] == pytest.approx(5.25)
    for seconds, expected_multiplier in ((0, 4.5), (5, 4.875)):
        selected_duration = calculate_payload(
            _payload(
                move_entry_id="move-entry:character:1481:physical-disorder",
                parameter_values={"parameter:dialyn:physical-disorder-remaining-seconds": seconds},
                manual_stats=stats,
            )
        )
        assert _node(_event(selected_duration), "disorder.total-multiplier")["value"] == pytest.approx(expected_multiplier)
    disorder_bonus = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-disorder",
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=(complaint_rule,),
            parameter_values={"parameter:dialyn:physical-disorder-remaining-seconds": 10},
            manual_stats=stats,
        )
    )
    disorder = _event(disorder_bonus)
    disorder_trace = disorder["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert disorder["damage_type"] == "disorder"
    assert disorder_trace["normal_bonus"] == pytest.approx(0.15)
    assert disorder_trace["final_strength"] == pytest.approx(2900.0)
    assert _node(disorder, "disorder.total-multiplier")["value"] == pytest.approx(5.25)
    assert disorder_bonus["totals"]["expected"]["complete"] is True
    assert _event(disorder_base)["modes"]["expected"]["anomaly_effect_strength_trace"]["final_strength"] == pytest.approx(2600.0)

    complaint_rules = (
        complaint_rule,
        "rule:character:1481:core:paper-malicious-complaint-stun-vulnerability",
        "rule:character:1481:cinema2:complaint-stun-vulnerability",
    )
    stunned_anomaly = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-assault",
            core_level=7,
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=complaint_rules,
            is_stunned=True,
            manual_stats=stats,
        )
    )
    stunned_disorder = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1481:physical-disorder",
            core_level=7,
            cinema_level=2,
            condition_values={"condition:dialyn:malicious-complaint-active": True},
            enabled_rule_item_ids=complaint_rules,
            parameter_values={"parameter:dialyn:physical-disorder-remaining-seconds": 10},
            is_stunned=True,
            manual_stats=stats,
        )
    )
    for result in (stunned_anomaly, stunned_disorder):
        event = _event(result)
        assert _node(event, "vulnerability.effective-stun")["value"] == pytest.approx(2.0)
        assert _node(event, "vulnerability.broad-region")["value"] == pytest.approx(3.0)
        assert event["modes"]["expected"]["anomaly_effect_strength_trace"]["normal_bonus"] == pytest.approx(0.15)


def test_previous_teammate_extra_damage_is_blocked_only_on_its_three_ex_hits() -> None:
    rule_id = "rule:character:1481:extra-ability:previous-teammate-extra-hit"
    eligible = calculate_payload(
        _payload(
            supporting=(YIXUAN,),
            move_entry_id="move-entry:character:1481:ex-stone",
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert _event(eligible)["modes"]["expected"]["known_value"] is not None
    assert eligible["totals"]["expected"]["complete"] is False
    diagnostic = next(
        item
        for item in eligible["totals"]["expected"]["diagnostics"]
        if item["diagnostic_id"].endswith(":unresolved-template")
    )
    assert diagnostic["kind"] == "ambiguous-semantics"
    assert any("320%" in item for item in diagnostic["candidates"])
    assert any("400%" in item for item in diagnostic["candidates"])
    assert "previous-teammate" in diagnostic["message"]

    unrelated = calculate_payload(
        _payload(
            supporting=(YIXUAN,),
            move_entry_id="move-entry:character:1481:basic-service-1",
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert unrelated["totals"]["expected"]["complete"] is True

    ineligible = calculate_payload(
        _payload(
            supporting=(ASTRA,),
            move_entry_id="move-entry:character:1481:ex-stone",
            enabled_rule_item_ids=(rule_id,),
        )
    )
    assert ineligible["totals"]["expected"]["complete"] is True
    assert not any(
        item["diagnostic_id"].endswith(":unresolved-template")
        for item in ineligible["totals"]["expected"]["diagnostics"]
    )


def test_dialyn_c6_after_sound_uses_explicit_beneficiary_hit_and_bounded_count() -> None:
    c6_rule = "rule:character:1481:cinema6:after-sound-hit"
    conditions = {"condition:dialyn:after-sound-active": True}
    astra_holder_entry = (
        {
            "input_id": "scenario-trigger:effect:character:1481:cinema6:after-sound-hit:actor",
            "actor_id": ASTRA,
        },
    )
    astra_entry = (*astra_holder_entry, {
        "input_id": "scenario-trigger:effect:astra:1311:extra-entry-tremolo:actor",
        "actor_id": YIXUAN,
    })
    repeated = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(DIALYN, YIXUAN),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            parameter_values={"parameter:dialyn:after-sound-hit-count": 2},
            selected_trigger_inputs=astra_entry,
            manual_stats={DIALYN: _stats(hp=10000.0, attack=900.0, crit_rate=0.70, crit_damage=1.10)},
        )
    )
    assert len(repeated["events"]) == 2
    child = repeated["events"][1]
    assert child["repeat_count"] == 2
    assert child["semantic_id"] == "event:character:1481:cinema6-after-sound-hit"
    assert child["label"] == "6影：余音命中后的额外物理伤害"
    assert child["common_application_trace"]["created_by_effect_id"] == "effect:character:1481:cinema6:after-sound-hit"
    assert child["modes"]["expected"]["known_value"] > child["modes"]["non-crit"]["known_value"]
    definition = compile_registered_definition(
        DIALYN,
        {"core_level": 1, "cinema_level": 6},
        (ASTRA, DIALYN, YIXUAN),
    )
    template = next(
        item
        for item in definition.damage_event_templates
        if str(item.ref.template_id) == "template:character:1481:cinema6-after-sound-hit"
    )
    assert template.damage_dealer == DIALYN_ID
    assert template.base_source.character_id == DIALYN_ID
    assert template.crit_rule.stat_owner == DIALYN_ID
    assert template.element is Element.PHYSICAL
    assert template.move_id is None
    assert template.ref.skill_group is SkillGroup.SPECIAL_ATTACK
    assert template.ref.damage_tags == frozenset(
        {DamageTag.SPECIAL_ATTACK, DamageTag.EX_SPECIAL_ATTACK}
    )
    typed_child = instantiate_damage_event(
        template,
        FixedMultiplier(Resolved(0.48)),
        battle_state_id=BattleStateId("battle:dialyn-after-sound"),
        target_enemy=EnemyId("enemy:dialyn-after-sound"),
        created_at=0.0,
    ).event
    assert typed_child.metadata.move_id is None
    assert typed_child.metadata.skill_group is SkillGroup.SPECIAL_ATTACK
    assert typed_child.metadata.damage_tags == template.ref.damage_tags

    missing_count = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(DIALYN, YIXUAN),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            selected_trigger_inputs=astra_entry,
            manual_stats={DIALYN: _stats(hp=10000.0, attack=900.0, crit_rate=0.70, crit_damage=1.10)},
        )
    )
    assert len(missing_count["events"]) == 1
    assert missing_count["events"][0]["modes"]["expected"]["known_value"] is not None
    assert missing_count["totals"]["expected"]["complete"] is False
    assert any(
        "repeat-count" in item["message"]
        for item in missing_count["totals"]["expected"]["diagnostics"]
    )

    zero = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(DIALYN,),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            parameter_values={"parameter:dialyn:after-sound-hit-count": 0},
            selected_trigger_inputs=astra_holder_entry,
        )
    )
    assert len(zero["events"]) == 1
    assert zero["totals"]["expected"]["complete"] is True

    locked_before_c6 = calculate_payload(
        _payload(
            primary=ASTRA,
            supporting=(DIALYN,),
            move_entry_id="move-entry:astra:1311:basic-rhapsody-1",
            cinema_level=5,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            selected_trigger_inputs=astra_holder_entry,
        )
    )
    assert len(locked_before_c6["events"]) == 1
    assert locked_before_c6["totals"]["expected"]["complete"] is True

    wrong_holder_hit = calculate_payload(
        _payload(
            primary=DIALYN,
            supporting=(YIXUAN, ASTRA),
            move_entry_id="move-entry:character:1481:ex-stone",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            parameter_values={"parameter:dialyn:after-sound-hit-count": 1},
            selected_trigger_inputs=astra_entry,
        )
    )
    assert len(wrong_holder_hit["events"]) == 1
    assert wrong_holder_hit["totals"]["expected"]["complete"] is True

    yixuan_holder = (
        {
            "input_id": "scenario-trigger:effect:character:1481:cinema6:after-sound-hit:actor",
            "actor_id": YIXUAN,
        },
        {
            "input_id": "scenario-trigger:effect:astra:1311:extra-entry-tremolo:actor",
            "actor_id": ASTRA,
        },
    )
    holder_astra_main_yixuan = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(DIALYN, ASTRA),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            parameter_values={"parameter:dialyn:after-sound-hit-count": 1},
            selected_trigger_inputs=astra_entry,
        )
    )
    assert len(holder_astra_main_yixuan["events"]) == 1
    assert holder_astra_main_yixuan["totals"]["expected"]["complete"] is True

    holder_yixuan_main_yixuan = calculate_payload(
        _payload(
            primary=YIXUAN,
            supporting=(DIALYN, ASTRA),
            move_entry_id="move-entry:character:1371:basic-xiaoyun-jin-1",
            cinema_level=6,
            condition_values=conditions,
            enabled_rule_item_ids=(c6_rule,),
            parameter_values={"parameter:dialyn:after-sound-hit-count": 1},
            selected_trigger_inputs=yixuan_holder,
        )
    )
    assert len(holder_yixuan_main_yixuan["events"]) == 2
    assert holder_yixuan_main_yixuan["events"][1]["repeat_count"] == 1
    assert holder_yixuan_main_yixuan["events"][1]["common_application_trace"]["created_by_effect_id"] == (
        "effect:character:1481:cinema6:after-sound-hit"
    )


def test_dialyn_actual_equipment_build_uses_packaged_level60_panel() -> None:
    result = calculate_payload(_payload(equipment_build=True))
    snapshot = result["resolved_character_snapshots"][0]["stats"]
    assert snapshot["hp"] > 8250.5871
    assert snapshot["attack"] > 758.2048
    assert snapshot["crit_rate"] > 0.194
    assert result["totals"]["expected"]["complete"] is True
