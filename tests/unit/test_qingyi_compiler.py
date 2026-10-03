from __future__ import annotations

from pathlib import Path

import pytest

from core.application.characters.qingyi import (
    QINGYI_ID,
    QINGYI_REVIEWED_MAPPING,
    QingyiCompileConfig,
    compile_qingyi,
    load_raw_record,
)
from core.application.rules import RuleEligibility
from core.data.loader import load_character_record
from core.presentation.base_stats import character_base_stats
from core.presentation.calculation_service import calculate_payload
from core.presentation.registry import (
    build_registered_build_preview,
    compile_registered_definition,
    registration_for,
)
from core.types import CharacterRole, Element, FixedMultiplier


QINGYI = str(QINGYI_ID)
YE = "character:1431"
CORE_RULE = "rule:character:1251:core:subjugation-stun-vulnerability"
CHAIN_RULE = "rule:character:1251:chain:damage-per-subjugation-layer"
EXTRA_ABILITY_RULE = "rule:character:1251:extra-ability:impact-to-attack"
C1_RULE = "rule:character:1251:cinema1:target-defense-and-qingyi-crit"
C2_RULE = "rule:character:1251:cinema2:subjugation-vulnerability-enhancement"
C6_CRIT_RULE = "rule:character:1251:cinema6:moon-turn-crit-damage"
C6_RESISTANCE_RULE = "rule:character:1251:cinema6:all-resistance-reduction-active"
FLASHOVER = "condition:qingyi:flashover-active"
C1_ACTIVE = "condition:qingyi:c1-target-debuff-active"
C6_RESISTANCE_ACTIVE = "condition:qingyi:c6-all-resistance-active"
SUBJUGATION_STACKS = "parameter:qingyi:subjugation-stacks"
FLASHOVER_EXCESS = "parameter:qingyi:flashover-excess-percent"
DISORDER_SECONDS = "parameter:qingyi:electric-disorder-remaining-seconds"
WEAPON_SOUL_LOCK_RULE = "rule:wengine:14136:owner:1251:soul-lock-impact"
WEAPON_SOUL_LOCK_MAX_RULE = "rule:wengine:14136:owner:1251:soul-lock-max-impact"
WEAPON_SOUL_LOCK_ACTIVE = "condition:wengine:14136:owner:1251:soul-lock-active"


def _stats(
    *,
    hp: float = 20_000.0,
    attack: float = 1_000.0,
    impact: float = 136.0,
    crit_rate: float = 0.20,
    crit_damage: float = 0.80,
    anomaly_proficiency: float = 93.0,
    element: str = "electric",
    element_bonus: float = 0.20,
) -> dict[str, object]:
    return {
        "hp": hp,
        "attack": attack,
        "defense": 600.0,
        "impact": impact,
        "crit_rate": crit_rate,
        "crit_damage": crit_damage,
        "anomaly_mastery": 94.0,
        "anomaly_proficiency": anomaly_proficiency,
        "energy_regen": 1.20,
        "penetration_rate": 0.0,
        "penetration_flat": 0.0,
        "element_damage_bonus": {element: element_bonus},
    }


def _payload(
    *,
    move_entry_id: str = "move-entry:character:1251:basic-drunken-cloud",
    core_level: int = 1,
    cinema_level: int = 0,
    primary: str = QINGYI,
    supporting: tuple[str, ...] = (),
    condition_values: dict[str, bool] | None = None,
    parameter_values: dict[str, int] | None = None,
    enabled_rule_item_ids: tuple[str, ...] = (),
    rule_stack_counts: dict[str, int] | None = None,
    character_stats: dict[str, dict[str, object]] | None = None,
    qingyi_equipment_build: bool = False,
    qingyi_wengine_id: str | None = None,
    is_stunned: bool = False,
) -> dict[str, object]:
    team = (primary, *supporting)
    compile_configs: dict[str, dict[str, object]] = {}
    builds: dict[str, dict[str, object]] = {}
    for character_id in team:
        if character_id == QINGYI:
            compile_configs[character_id] = {
                "core_level": core_level,
                "cinema_level": cinema_level,
            }
            if qingyi_equipment_build:
                builds[character_id] = {
                    "level": 60,
                    "build_mode": "equipment-build",
                    "wengine_id": qingyi_wengine_id,
                    "wengine_level": 60,
                    "wengine_refinement": 1,
                    "drive_discs": [],
                }
            else:
                builds[character_id] = {
                    "level": 60,
                    "out_of_combat_stats": (character_stats or {}).get(
                        character_id, _stats()
                    ),
                }
        elif character_id == YE:
            compile_configs[character_id] = {
                "core_level": 1,
                "cinema_level": 0,
                "mingxin_active": False,
                "entry_move_uses_linren": False,
            }
            builds[character_id] = {
                "level": 60,
                "out_of_combat_stats": (character_stats or {}).get(
                    character_id,
                    _stats(
                        hp=9_000.0,
                        attack=900.0,
                        impact=83.0,
                        element="physical",
                        element_bonus=0.0,
                    ),
                ),
            }
        else:
            raise AssertionError(f"missing Qingyi regression build for {character_id}")
    return {
        "primary_character_id": primary,
        "supporting_character_ids": list(supporting),
        "team_character_ids": list(team),
        "move_entry_id": move_entry_id,
        "compile_configs": compile_configs,
        "condition_values": condition_values or {},
        "parameter_values": parameter_values or {},
        "character_builds": builds,
        "enemy": {
            "enemy_id": "enemy:qingyi-test",
            "level": 60,
            "initial_defense": 1_000.0,
            "damage_resistance": {"electric": 0.20, "physical": 0.20},
            "damage_reduction": 0.0,
            "stun_vulnerability_bonus": 1.5,
            "is_stunned": is_stunned,
        },
        "enabled_rule_item_ids": list(enabled_rule_item_ids),
        "selected_trigger_inputs": [],
        "rule_stack_counts": rule_stack_counts or {},
    }


def _event(result: dict[str, object], semantic_id: str | None = None):
    events = result["events"]
    assert isinstance(events, list)
    return next(
        (item for item in events if item["semantic_id"] == semantic_id),
        None,
    ) if semantic_id is not None else events[0]


def _node(event, node: str, mode: str = "expected") -> float:
    breakdown = event["modes"][mode]["calculation_breakdown"]
    return next(item["value"] for item in breakdown if item["node"] == node)


def test_qingyi_live_raw_mapping_and_reviewed_scope() -> None:
    raw_json = load_character_record(QINGYI)
    raw = load_raw_record(raw_json)
    assert raw.name == "青衣"
    assert raw.code_name == "QingYi"
    assert raw.rarity == 4
    assert raw.specialty == "击破"
    assert raw.element == "电属性"
    assert raw.faction == "新艾利都治安局"
    assert raw.source_version == "3.2"
    assert raw.source_url == "https://static.nanoka.cc/zzz/3.2/zh/character/1251.json"

    source_ids = {
        spec.source_skill_id
        for move in QINGYI_REVIEWED_MAPPING.moves
        for spec in move.parameters
    }
    assert source_ids == {
        "1251007",
        "1251012",
        "1251013",
        "1251010",
        "1251014",
        "1251015",
        "1251016",
        "1251020",
    }
    definition = compile_qingyi(
        QingyiCompileConfig(core_level=1, cinema_level=0),
        raw,
    )
    entries = {str(item.entry_id): item for item in definition.move_entries}
    assert len(entries) == 19
    assert entries["move-entry:character:1251:basic-drunken-cloud"].multiplier_variants[0].multiplier.value.value == pytest.approx(1.714)
    assert entries["move-entry:character:1251:dash-entry"].multiplier_variants[0].multiplier.value.value == pytest.approx(0.99)
    assert entries["move-entry:character:1251:chain-peaceful-order"].multiplier_variants[0].multiplier.value.value == pytest.approx(12.958)
    assert entries["move-entry:character:1251:ultimate-eight-sounds-ganzhou"].multiplier_variants[0].multiplier.value.value == pytest.approx(33.416)
    assert entries["move-entry:character:1251:ex-special-moon-over-sea-begonia"].multiplier_variants[0].multiplier.value.value == pytest.approx(12.067)
    assert "1251011=301.4% + 1251021=422.2% + 1251022=483.1%" in entries["move-entry:character:1251:ex-special-moon-over-sea-begonia"].original_text

    raw_yisha = next(item for item in raw.moves if item.name == "普通攻击：一煞")
    raw_first = next(item for item in raw_yisha.parameters if item.name == "一段伤害倍率")
    assert isinstance(entries["move-entry:character:1251:basic-yisha-1"].multiplier_variants[0].multiplier, FixedMultiplier)
    assert entries["move-entry:character:1251:basic-yisha-1"].multiplier_variants[0].multiplier.value.value == pytest.approx(raw_first.value_for_level(12, "1251001") / 100.0)
    assert not any("basic-yisha-derived" in item for item in entries)
    assert entries["move-entry:character:1251:moon-turn-rush"].multiplier_variants[0].multiplier.value.value == pytest.approx(8.975)
    assert entries["move-entry:character:1251:moon-turn-finisher"].multiplier_variants[0].multiplier.value.value == pytest.approx(7.893)
    assert entries["move-entry:character:1251:moon-turn-full-sequence"].multiplier_variants[0].multiplier.value.value == pytest.approx(16.868)
    assert "1251017" not in source_ids  # Defensive Assist has daze curves only.

    template_map = {str(item.ref.template_id): item for item in definition.damage_event_templates}
    for stage in (1, 2):
        assert template_map[f"template:character:1251:basic-yisha-{stage}:main"].element is Element.PHYSICAL
    for stage in (3, 4):
        assert template_map[f"template:character:1251:basic-yisha-{stage}:main"].element is Element.ELECTRIC
    assert template_map["template:character:1251:basic-yisha-4-enhanced:main"].element is Element.ELECTRIC
    for entry_id in (
        *(f"move-entry:character:1251:basic-yisha-{stage}" for stage in range(1, 5)),
        "move-entry:character:1251:basic-yisha-4-enhanced",
    ):
        result = calculate_payload(_payload(move_entry_id=entry_id))
        assert len(result["events"]) == 1
        assert result["totals"]["expected"]["complete"] is True

    registration = registration_for(QINGYI)
    assert registration.catalog.display_name == "青衣"
    assert registration.catalog.rarity == "S"
    assert registration.role is CharacterRole.STUN
    assert registration.base_element is Element.ELECTRIC
    assert (Path(__file__).parents[2] / "frontend/public/characters/IconRole29.webp").is_file()


def test_qingyi_level60_panel_and_impact_drive_disc_preview() -> None:
    base = character_base_stats(QINGYI)
    assert base.hp.value == pytest.approx(8_250.5871)
    assert base.attack.value == pytest.approx(758.2048)
    assert base.impact.value == pytest.approx(136.0)
    assert base.anomaly_mastery.value == 94.0
    assert base.anomaly_proficiency.value == 93.0

    discs = [
        {
            "slot": 6,
            "set_id": "drive-disc:31000",
            "main_stat": "impact-percent",
            "substats": [
                {"stat": "attack-percent", "roll_count": 2},
                {"stat": "crit-rate", "roll_count": 2},
                {"stat": "crit-damage", "roll_count": 2},
                {"stat": "anomaly-proficiency-flat", "roll_count": 2},
            ],
        }
    ]
    preview = build_registered_build_preview(QINGYI, level=60, discs=discs)
    assert preview.complete is True
    assert preview.base_stats["impact"] == pytest.approx(136.0)
    assert preview.out_of_combat_stats["impact"] == pytest.approx(160.48)
    assert any(
        item.stat == "impact" and item.layer == "out-of-combat-percent"
        for item in preview.provenance
    )


def test_cinema3_and5_apply_to_nonultimate_source_curves_only() -> None:
    base = compile_registered_definition(
        QINGYI,
        {
            "core_level": 1,
            "cinema_level": 0,
            "skill_levels": {"special-attack": 12, "ultimate": 12},
        },
        (QINGYI,),
    )
    cinema3 = compile_registered_definition(
        QINGYI,
        {
            "core_level": 1,
            "cinema_level": 3,
            "skill_levels": {"special-attack": 12, "ultimate": 12},
        },
        (QINGYI,),
    )
    cinema5 = compile_registered_definition(
        QINGYI,
        {
            "core_level": 1,
            "cinema_level": 5,
            "skill_levels": {"special-attack": 12, "ultimate": 12},
        },
        (QINGYI,),
    )

    def multiplier(definition, suffix: str) -> float:
        entry = next(item for item in definition.move_entries if str(item.entry_id).endswith(suffix))
        return entry.multiplier_variants[0].multiplier.value.value

    assert multiplier(base, "special-day-brocade-hall") == pytest.approx(1.251)
    assert multiplier(cinema3, "special-day-brocade-hall") == pytest.approx(1.365)
    assert multiplier(cinema5, "special-day-brocade-hall") == pytest.approx(1.479)
    assert multiplier(base, "ultimate-eight-sounds-ganzhou") == pytest.approx(33.416)
    assert multiplier(cinema3, "ultimate-eight-sounds-ganzhou") == pytest.approx(33.416)
    assert multiplier(cinema5, "ultimate-eight-sounds-ganzhou") == pytest.approx(33.416)


def test_additional_ability_reads_current_impact_after_real_engine_panel_buff() -> None:
    result = calculate_payload(
        _payload(
            primary=YE,
            supporting=(QINGYI,),
            move_entry_id="move-entry:ye:1431:basic-fast-1",
            qingyi_equipment_build=True,
            qingyi_wengine_id="wengine:14136",
            condition_values={WEAPON_SOUL_LOCK_ACTIVE: True},
            enabled_rule_item_ids=(
                EXTRA_ABILITY_RULE,
                WEAPON_SOUL_LOCK_RULE,
                WEAPON_SOUL_LOCK_MAX_RULE,
            ),
            rule_stack_counts={WEAPON_SOUL_LOCK_RULE: 3},
        )
    )
    snapshots = {item["character_id"]: item["stats"] for item in result["resolved_character_snapshots"]}
    assert snapshots[QINGYI]["impact"] == pytest.approx(163.2)
    assert snapshots[QINGYI]["attack"] == pytest.approx(1_730.4048)
    assert snapshots[YE]["attack"] == pytest.approx(900.0)
    traces = result["panel_traces"]
    impact_extra = next(
        item
        for item in traces
        if item["effect_id"] == "effect:character:1251:extra-ability:impact-to-attack"
    )
    assert impact_extra["recipient_character_id"] == QINGYI
    assert impact_extra["resolved_value"] == pytest.approx(259.2)
    weapon_impacts = [
        item["resolved_value"]
        for item in traces
        if item["recipient_character_id"] == QINGYI
        and item["effect_id"].startswith("effect:wengine:14136:owner:1251:soul-lock-")
    ]
    assert sorted(weapon_impacts) == pytest.approx([10.88, 16.32])
    assert result["totals"]["expected"]["complete"] is True

    capped = calculate_payload(
        _payload(
            supporting=(YE,),
            move_entry_id="move-entry:character:1251:basic-drunken-cloud",
            enabled_rule_item_ids=(EXTRA_ABILITY_RULE,),
            character_stats={QINGYI: _stats(impact=220.0)},
        )
    )
    capped_stats = capped["resolved_character_snapshots"][0]["stats"]
    assert capped_stats["attack"] == pytest.approx(1_600.0)
    assert next(
        item
        for item in capped["panel_traces"]
        if item["effect_id"] == "effect:character:1251:extra-ability:impact-to-attack"
    )["resolved_value"] == pytest.approx(600.0)


def test_subjugation_core_and_cinema2_use_one_layer_parameter() -> None:
    default_max = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:chain-peaceful-order",
            core_level=7,
            condition_values={},
            enabled_rule_item_ids=(CORE_RULE, CHAIN_RULE),
        )
    )
    explicit_zero = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:chain-peaceful-order",
            core_level=7,
            condition_values={},
            parameter_values={SUBJUGATION_STACKS: 0},
            enabled_rule_item_ids=(CORE_RULE, CHAIN_RULE),
        )
    )
    c0 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:chain-peaceful-order",
            condition_values={},
            parameter_values={SUBJUGATION_STACKS: 10},
            enabled_rule_item_ids=(CORE_RULE, CHAIN_RULE),
        )
    )
    c2 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:chain-peaceful-order",
            cinema_level=2,
            parameter_values={SUBJUGATION_STACKS: 10},
            enabled_rule_item_ids=(CORE_RULE, CHAIN_RULE, C2_RULE),
        )
    )
    event0, event2 = _event(c0), _event(c2)
    assert _node(_event(default_max), "vulnerability.enemy-stun") == pytest.approx(2.3)
    assert _node(_event(explicit_zero), "vulnerability.enemy-stun") == pytest.approx(1.5)
    assert _node(event0, "vulnerability.enemy-stun") == pytest.approx(1.7)
    assert _node(event0, "damage.normal-bonus") == pytest.approx(0.30)
    assert _node(event2, "damage.normal-bonus") == pytest.approx(0.30)
    assert _node(event0, "vulnerability.effective-stun") == pytest.approx(0.0)
    assert _node(event2, "vulnerability.effective-stun") == pytest.approx(0.0)
    assert _node(event0, "vulnerability.enemy-stun") == pytest.approx(
        _node(event2, "vulnerability.enemy-stun") - 0.07
    )
    assert c0["totals"]["expected"]["complete"] is True
    assert c2["totals"]["expected"]["complete"] is True


def test_cinema1_target_status_and_cinema6_move_status_are_scoped() -> None:
    c1 = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:basic-drunken-cloud",
            cinema_level=1,
            condition_values={C1_ACTIVE: True},
            enabled_rule_item_ids=(C1_RULE,),
        )
    )
    event = _event(c1)
    assert c1["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(0.20)
    assert _node(event, "character.current.crit-rate") == pytest.approx(0.40)
    assert _node(event, "defense.enemy-current-effective") == pytest.approx(850.0)

    finisher = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:moon-turn-finisher",
            cinema_level=6,
            condition_values={FLASHOVER: True, C6_RESISTANCE_ACTIVE: True},
            parameter_values={FLASHOVER_EXCESS: 25},
            enabled_rule_item_ids=(
                "rule:character:1251:basic:moon-turn-flashover-damage",
                C6_CRIT_RULE,
                C6_RESISTANCE_RULE,
            ),
            character_stats={QINGYI: _stats(crit_rate=0.20, crit_damage=0.80)},
        )
    )
    event = _event(finisher, "event:character:1251:moon-turn-finisher:main")
    # Cinema 3 and 5 are both unlocked: input Basic Lv12 is effective Lv16.
    assert _node(event, "damage.skill-multiplier") == pytest.approx(9.329)
    assert _node(event, "damage.normal-bonus") == pytest.approx(0.25)
    assert _node(event, "damage.normal-bonus-region") == pytest.approx(1.45)
    assert _node(event, "character.current.crit-damage") == pytest.approx(1.80)
    assert _node(event, "resistance.region") == pytest.approx(1.0)
    formal_stats = finisher["resolved_character_snapshots"][0]["stats"]
    assert formal_stats["crit_damage"] == pytest.approx(0.80)
    assert formal_stats["crit_rate"] == pytest.approx(0.20)
    assert finisher["totals"]["expected"]["complete"] is True

    no_excess = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:moon-turn-finisher",
            condition_values={FLASHOVER: True},
            parameter_values={FLASHOVER_EXCESS: 0},
            enabled_rule_item_ids=(
                "rule:character:1251:basic:moon-turn-flashover-damage",
            ),
        )
    )
    no_excess_event = _event(no_excess)
    assert _node(no_excess_event, "damage.skill-multiplier") == pytest.approx(7.893)
    assert _node(no_excess_event, "damage.normal-bonus-region") == pytest.approx(1.20)


def test_ex_special_base_sum_is_complete_without_a_long_press_option() -> None:
    baseline = calculate_payload(
        _payload(move_entry_id="move-entry:character:1251:ex-special-moon-over-sea-begonia")
    )
    assert baseline["totals"]["expected"]["complete"] is True
    assert _node(_event(baseline), "damage.skill-multiplier") == pytest.approx(12.067)

    definition = compile_qingyi(QingyiCompileConfig(), load_raw_record(load_character_record(QINGYI)))
    assert not any(str(item.rule_id) == "rule:character:1251:ex-special:long-press-extra-turns" for item in definition.rule_items)
    assert not any(str(item.condition_id) == "condition:qingyi:ex-special-extra-turns-active" for item in definition.scenario_conditions)


def test_moon_turn_rush_is_five_hit_total_and_full_entry_adds_finisher_once() -> None:
    expected_ratios = {
        "move-entry:character:1251:moon-turn-rush": 8.975,
        "move-entry:character:1251:moon-turn-finisher": 7.893,
        "move-entry:character:1251:moon-turn-full-sequence": 16.868,
    }
    for entry_id, expected_ratio in expected_ratios.items():
        result = calculate_payload(
            _payload(move_entry_id=entry_id, condition_values={FLASHOVER: True})
        )
        assert result["totals"]["expected"]["complete"] is True
        assert _node(_event(result), "damage.skill-multiplier") == pytest.approx(expected_ratio)


def test_static_electric_anomaly_disorder_and_no_crit_modes() -> None:
    anomaly = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:electric-anomaly",
            character_stats={QINGYI: _stats(anomaly_proficiency=100.0)},
        )
    )
    anomaly_event = _event(anomaly)
    assert anomaly_event["damage_type"] == "anomaly"
    assert anomaly_event["repeat_count"] == 10
    assert anomaly["totals"]["non-crit"]["value"] == pytest.approx(
        anomaly["totals"]["full-crit"]["value"]
    )
    trace = anomaly_event["modes"]["expected"]["anomaly_effect_strength_trace"]
    assert trace["final_strength"] == pytest.approx(2_400.0)
    assert _node(anomaly_event, "anomaly.attribute.multiplier") == pytest.approx(1.25)

    disorder_zero = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:electric-disorder",
            parameter_values={DISORDER_SECONDS: 0},
        )
    )
    disorder_full = calculate_payload(
        _payload(move_entry_id="move-entry:character:1251:electric-disorder")
    )
    assert _node(_event(disorder_zero), "disorder.total-multiplier") == pytest.approx(4.5)
    assert _node(_event(disorder_full), "disorder.total-multiplier") == pytest.approx(17.0)
    assert disorder_full["totals"]["non-crit"]["value"] == pytest.approx(
        disorder_full["totals"]["expected"]["value"]
    )

    stunned = calculate_payload(
        _payload(
            move_entry_id="move-entry:character:1251:electric-anomaly",
            core_level=1,
            cinema_level=6,
            is_stunned=True,
            condition_values={C1_ACTIVE: True, C6_RESISTANCE_ACTIVE: True},
            parameter_values={SUBJUGATION_STACKS: 20},
            enabled_rule_item_ids=(CORE_RULE, C1_RULE, C6_RESISTANCE_RULE),
            character_stats={QINGYI: _stats(anomaly_proficiency=100.0)},
        )
    )
    stunned_event = _event(stunned)
    assert stunned["resolved_character_snapshots"][0]["stats"]["crit_rate"] == pytest.approx(0.20)
    assert stunned["totals"]["non-crit"]["value"] == pytest.approx(
        stunned["totals"]["full-crit"]["value"]
    )
    assert _node(stunned_event, "vulnerability.effective-stun") > 0.0
    assert _node(stunned_event, "resistance.region") == pytest.approx(1.0)


def test_additional_ability_qualification_and_versioned_v2_fixture() -> None:
    solo = compile_registered_definition(QINGYI, {"core_level": 1, "cinema_level": 0}, (QINGYI,))
    with_attack = compile_registered_definition(
        QINGYI,
        {"core_level": 1, "cinema_level": 0},
        (QINGYI, YE),
    )
    rule_id = "rule:character:1251:extra-ability:impact-to-attack"
    assert next(item for item in solo.rule_items if str(item.rule_id) == rule_id).eligibility is RuleEligibility.INELIGIBLE
    assert next(item for item in with_attack.rule_items if str(item.rule_id) == rule_id).eligibility is RuleEligibility.ELIGIBLE
