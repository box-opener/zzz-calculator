"""Compile the supplied Nanoka Yuzuha record into application contracts."""

from __future__ import annotations

from core.types import (
    AnyFilter,
    CharacterId,
    CharacterRole,
    CalculationNode,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    Element,
    ElementFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    MoveId,
    MoveIdFilter,
    ModifierEffect,
    ModifierResult,
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
)

from ...ids import RuleItemId
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition, ScenarioRuleStack
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaReviewedMapping,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from .config import YuzuhaCompileConfig
from .reviewed import (
    EXTRA_ABILITY_ACTIVE_CONDITION_ID,
    SWEET_SCARE_ACTIVE_CONDITION_ID,
    TANUKI_ATTACK_CONDITION_ID,
    TANUKI_SELF_ATTACK_CONDITION_ID,
    TANUKI_WISH_ACTIVE_CONDITION_ID,
    YUZUHA_ID,
    YUZUHA_REVIEWED_MAPPING,
)


# The source descriptions expose one reviewed cap at each core level.  The
# values are kept as a level curve (rather than a single level-12 constant),
# and the compiler always selects the requested core level.
TANUKI_WISH_ATTACK_CAPS = (600.0, 700.0, 800.0, 900.0, 1000.0, 1100.0, 1200.0)


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=None,
    )


def _rule(
    rule_id: str,
    source: RuleSource,
    display_name: str,
    original_text: str,
    eligibility: RuleEligibility,
    effects=(),
    *,
    condition_ids=(),
    stack_count=None,
    stack_min=None,
    stack_max=None,
    non_stacking_group_id: str | None = None,
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(rule_id),
        owner=YUZUHA_ID,
        source=source,
        display_name=display_name,
        original_text=original_text,
        eligibility=eligibility,
        condition_ids=tuple(condition_ids),
        effects=tuple(effects),
        stack_count=stack_count,
        stack_min=stack_min,
        stack_max=stack_max,
        non_stacking_group_id=non_stacking_group_id,
    )


def _modifier(
    effect_key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1411:{effect_key}"),
            source=source,
            owner=YUZUHA_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _raw_core(raw: NanokaRawRecord, level: int):
    try:
        return raw.core_levels[level - 1]
    except IndexError as exc:
        raise ValueError("raw Yuzuha record must contain all seven core levels") from exc


def _raw_talent(raw: NanokaRawRecord, level: int):
    try:
        return next(item for item in raw.mindscapes if item.level == level)
    except StopIteration as exc:
        raise ValueError(f"raw Yuzuha record is missing cinema {level}") from exc


def compile_yuzuha(
    config: YuzuhaCompileConfig,
    raw_record: NanokaRawRecord,
    reviewed_mapping: NanokaReviewedMapping = YUZUHA_REVIEWED_MAPPING,
) -> CharacterCalculationDefinition:
    _validate_raw_record(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=YUZUHA_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=reviewed_mapping,
        id_namespace="yuzuha:1411",
    )
    core = _raw_core(raw_record, config.core_level)
    core_source = source_for(
        YUZUHA_ID,
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    conditions = (
        _condition(
            TANUKI_WISH_ACTIVE_CONDITION_ID,
            "当前已拥有狸之愿",
            "拥有[狸之愿]效果",
        ),
        _condition(
            TANUKI_ATTACK_CONDITION_ID,
            "狸猫阿釜协同柚叶攻击",
            "狸猫阿釜协同柚叶攻击",
        ),
        _condition(
            TANUKI_SELF_ATTACK_CONDITION_ID,
            "狸猫阿釜自主攻击",
            "狸猫阿釜自主攻击",
        ),
        _condition(
            EXTRA_ABILITY_ACTIVE_CONDITION_ID,
            "额外能力：人多乐趣大已生效",
            "队伍中存在异常角色或同阵营角色，且异常掌控超过100点",
        ),
        _condition(
            SWEET_SCARE_ACTIVE_CONDITION_ID,
            "目标处于甜蜜惊吓",
            "处于[甜蜜惊吓]状态下的敌人",
        ),
    )

    rules: list[CalculationRuleItem] = []
    cap = TANUKI_WISH_ATTACK_CAPS[config.core_level - 1]
    core_effect = _modifier(
        "core:tanuki-wish-attack",
        core_source,
        CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
        PanelStatDerivedValue(
            source_character_id=YUZUHA_ID,
            source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
            coefficient=Resolved(0.40),
            cap_max=Resolved(cap),
        ),
        target=EffectTarget.TEAM,
    )
    core_damage = _modifier(
        "core:tanuki-wish-damage",
        core_source,
        CalculationNode.DAMAGE_NORMAL_BONUS,
        Resolved(0.15),
        target=EffectTarget.TEAM,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:core-passive",
            core_source,
            core.name,
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=(core_effect, core_damage),
            condition_ids=(TANUKI_WISH_ACTIVE_CONDITION_ID,),
            non_stacking_group_id="yuzuha:tanuki-wish",
        )
    )

    extra_source = source_for(
        YUZUHA_ID,
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    # The mastery-to-bonus conversion is deliberately left as a reviewed
    # scenario boundary until the panel-derived-value contract supports a
    # capped current anomaly-mastery source.  The eligibility and original
    # rule remain visible, and no incorrect fixed 20% is applied to damage.
    rules.append(
        _rule(
            "rule:yuzuha:1411:extra-ability",
            extra_source,
            raw_record.extra_ability_name,
            raw_record.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            condition_ids=(EXTRA_ABILITY_ACTIVE_CONDITION_ID,),
        )
    )

    # 1C adds a global resistance reduction while Sweet Scare is present.
    c1 = _raw_talent(raw_record, 1)
    c1_source = source_for(
        YUZUHA_ID,
        "cinema-1",
        EffectSourceType.CINEMA,
        f"1影：{c1.name}",
        c1.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema1",
            c1_source,
            f"1影：{c1.name}",
            c1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:sweet-scare-resistance",
                    c1_source,
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION,
                    Resolved(0.10),
                    target=EffectTarget.ENEMY,
                    condition=None,
                    filters=(
                        AnyFilter(
                            tuple(ElementFilter(element) for element in Element if element in {
                                Element.PHYSICAL,
                                Element.FIRE,
                                Element.ELECTRIC,
                                Element.ICE,
                                Element.ETHER,
                                Element.WIND,
                            })
                        ),
                    ),
                ),
            ),
            condition_ids=(SWEET_SCARE_ACTIVE_CONDITION_ID,),
        )
    )

    c2 = _raw_talent(raw_record, 2)
    c2_source = source_for(
        YUZUHA_ID,
        "cinema-2",
        EffectSourceType.CINEMA,
        f"2影：{c2.name}",
        c2.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema2",
            c2_source,
            f"2影：{c2.name}",
            c2.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 2
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema2:team-damage",
                    c2_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "cinema2:team-buildup",
                    c2_source,
                    CalculationNode.ANOMALY_BUILDUP_EFFICIENCY,
                    Resolved(0.15),
                    target=EffectTarget.TEAM,
                ),
            ),
            condition_ids=(TANUKI_WISH_ACTIVE_CONDITION_ID,),
        )
    )

    c3 = _raw_talent(raw_record, 3)
    c3_source = source_for(
        YUZUHA_ID,
        "cinema-3",
        EffectSourceType.CINEMA,
        f"3影：{c3.name}",
        c3.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema3",
            c3_source,
            f"3影：{c3.name}",
            c3.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 3
            else RuleEligibility.INELIGIBLE,
        )
    )

    c4 = _raw_talent(raw_record, 4)
    c4_source = source_for(
        YUZUHA_ID,
        "cinema-4",
        EffectSourceType.CINEMA,
        f"4影：{c4.name}",
        c4.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema4",
            c4_source,
            f"4影：{c4.name}",
            c4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema4:assist-damage",
                    c4_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(0.30),
                    target=EffectTarget.SELF,
                    filters=(
                        AnyFilter(
                            (
                                MoveIdFilter(MoveId("move:yuzuha:cookie")),
                                MoveIdFilter(MoveId("move:yuzuha:stuffed-candy")),
                            )
                        ),
                    ),
                ),
            ),
        )
    )

    c5 = _raw_talent(raw_record, 5)
    c5_source = source_for(
        YUZUHA_ID,
        "cinema-5",
        EffectSourceType.CINEMA,
        f"5影：{c5.name}",
        c5.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema5",
            c5_source,
            f"5影：{c5.name}",
            c5.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 5
            else RuleEligibility.INELIGIBLE,
        )
    )

    c6 = _raw_talent(raw_record, 6)
    c6_source = source_for(
        YUZUHA_ID,
        "cinema-6",
        EffectSourceType.CINEMA,
        f"6影：{c6.name}",
        c6.description,
    )
    rules.append(
        _rule(
            "rule:yuzuha:1411:cinema6",
            c6_source,
            f"6影：{c6.name}",
            c6.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:disorder-damage",
                    c6_source,
                    CalculationNode.DISORDER_EXTRA_MULTIPLIER,
                    Resolved(1.05),
                    target=EffectTarget.TEAM,
                ),
            ),
            stack_count=3,
            stack_min=0,
            stack_max=3,
        )
    )

    return build_definition(
        character_id=YUZUHA_ID,
        role=CharacterRole.SUPPORT,
        element=Element.PHYSICAL,
        source=core_source,
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        diagnostics=diagnostics,
    )


def _validate_raw_record(raw: NanokaRawRecord, config: YuzuhaCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("raw record and compile config character IDs must match")
    if raw.name != "柚叶":
        raise ValueError("unexpected character name in raw Yuzuha record")
    if raw.code_name != "Yuzuha":
        raise ValueError("unexpected Yuzuha code name in raw record")
    if raw.specialty != "支援":
        raise ValueError("unexpected Yuzuha specialty in raw record")
    if raw.element != "物理":
        raise ValueError("unexpected Yuzuha element in raw record")
    if len(raw.core_levels) != 7:
        raise ValueError("raw Yuzuha record must contain all seven core levels")
    if len(raw.mindscapes) != 6:
        raise ValueError("raw Yuzuha record must contain all six mindscapes")


def load_raw_record(data):
    return load_nanoka_raw_record(data, expected_character_id=str(YUZUHA_ID))


__all__ = [
    "TANUKI_WISH_ATTACK_CAPS",
    "TANUKI_WISH_ACTIVE_CONDITION_ID",
    "YUZUHA_ID",
    "compile_yuzuha",
    "load_raw_record",
]
