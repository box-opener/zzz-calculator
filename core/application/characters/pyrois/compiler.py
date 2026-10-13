"""Compile Pyrois's reviewed Nanoka live 3.2 source."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    BattleEventKind,
    CalculationNode,
    CharacterRole,
    CurrentAttackValueSource,
    DamageDealerFilter,
    DamageTag,
    DamageTagFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EnemyStateFilter,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    SkillGroup,
    SnapshotRule,
    StandardCritRule,
    StateId,
    Unresolved,
)

from ...diagnostics import CalculationDiagnostic
from ...ids import DamageEventSemanticId, RuleItemId
from ...moves import DamageEventTemplateRef, DerivedDamageEventTemplateRef
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    effective_skill_level,
    raw_move_index,
    raw_multiplier,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ..templates import DirectDamageEventTemplate
from .config import PYROIS_ID, PyroisCompileConfig
from .reviewed import (
    PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,
    PYROIS_LEFT_CORE_EXTRA_ACTIVE,
    PYROIS_REVIEWED_MAPPING,
    PYROIS_RIGHT_CORE_EXTRA_ACTIVE,
    PYROIS_SUNFLAME_ACTIVE,
    PYROIS_SUNFLARE_ACTIVE,
)


_STUNNED = StateId("state:enemy:stunned")
_ULTIMATE_KEYS = (
    "ultimate-military-execution",
    "ultimate-victory-road",
    "ultimate-unbound-sword",
    "ultimate-eternal-prison",
)
_ULTIMATE_TEMPLATES = tuple(
    EventTemplateId(f"template:character:1551:{key}:main")
    for key in _ULTIMATE_KEYS
)
_EX_TEMPLATE = EventTemplateId(
    "template:character:1551:ex-sunflower:main"
)
_LEFT_TEMPLATE = EventTemplateId(
    "template:character:1551:ultimate-unbound-sword:main"
)
_RIGHT_TEMPLATE = EventTemplateId(
    "template:character:1551:ultimate-eternal-prison:main"
)


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    """Load the complete source while skipping Nanoka's empty prose sentinel."""

    skills = data.get("skill")
    if not isinstance(skills, Mapping):
        return load_nanoka_raw_record(data, expected_character_id=str(PYROIS_ID))
    special = skills.get("special")
    if not isinstance(special, Mapping):
        return load_nanoka_raw_record(data, expected_character_id=str(PYROIS_ID))
    descriptions = special.get("description")
    if not isinstance(descriptions, (list, tuple)):
        return load_nanoka_raw_record(data, expected_character_id=str(PYROIS_ID))

    # The verified raw record contains one empty `{name: "", param: []}` row.
    # It is source noise rather than an authored move; the production JSON stays
    # byte-for-byte complete, and only the parser input omits this sentinel.
    normalized_special = {
        **special,
        "description": tuple(
            item
            for item in descriptions
            if not (
                isinstance(item, Mapping)
                and not str(item.get("name", "")).strip()
                and not item.get("desc")
                and not item.get("param")
            )
        ),
    }
    normalized_data = {
        **data,
        "skill": {**skills, "special": normalized_special},
    }
    return load_nanoka_raw_record(
        normalized_data,
        expected_character_id=str(PYROIS_ID),
    )


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(matches)}")
    return float(matches[0].group("value"))


def _validate_raw(raw: NanokaRawRecord, config: PyroisCompileConfig) -> None:
    if raw.character_id != PYROIS_ID:
        raise ValueError("raw character does not match Pyrois")
    if (
        raw.name != "佩洛伊斯"
        or raw.code_name != "Pyrois"
        or raw.rarity != 4
        or raw.specialty != "强攻"
        or raw.element != "以太"
        or raw.faction != "法厄同"
        or raw.icon != "IconRole63"
    ):
        raise ValueError("raw identity does not match reviewed Pyrois source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1551.json"
    ):
        raise ValueError("raw Pyrois provenance does not match Nanoka live3.2")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("raw Pyrois record must contain seven Core levels and six cinemas")
    required = {spec.source_name for spec in PYROIS_REVIEWED_MAPPING.moves}
    required.add("特殊技：强袭训令")
    available = {item.name for item in raw.moves}
    missing = required - available
    if missing:
        raise ValueError(f"raw Pyrois record is missing reviewed moves: {sorted(missing)}")
    if not 1 <= config.core_level <= len(raw.core_levels):
        raise ValueError("configured Pyrois Core level is not available in raw source")


def _source(
    key: str,
    kind: EffectSourceType,
    label: str,
    text: str,
) -> RuleSource:
    return source_for(PYROIS_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1551:{key}"),
        owner=PYROIS_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value: float,
    *,
    target: EffectTarget = EffectTarget.SELF,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1551:{key}"),
            source=source,
            owner=PYROIS_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=Resolved(value),
        ),
    )


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _core_ratio(core: NanokaRawRecord, pattern: str, subject: str) -> float:
    return _number(core.description, pattern, subject) / 100.0


def compile_pyrois(
    config: PyroisCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    _validate_raw(raw_record, config)
    entries, direct_templates, move_diagnostics = compile_direct_moves(
        character_id=PYROIS_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=PYROIS_REVIEWED_MAPPING,
        id_namespace="character:1551",
    )
    templates = list(direct_templates)
    independent_derived: list[DerivedDamageEventTemplateRef] = []
    core = raw_record.core_levels[config.core_level - 1]
    rules: list[CalculationRuleItem] = []
    conditions = [
        _condition(
            PYROIS_SUNFLAME_ACTIVE,
            "当前处于[阳炎]状态",
            core.description,
        ),
        _condition(
            PYROIS_SUNFLARE_ACTIVE,
            "当前处于[耀斑]状态",
            core.description,
        ),
        _condition(
            PYROIS_LEFT_CORE_EXTRA_ACTIVE,
            "当前左分支重击命中处于[浸染]状态的敌人",
            core.description,
        ),
        _condition(
            PYROIS_RIGHT_CORE_EXTRA_ACTIVE,
            "当前右分支重击命中失衡敌人",
            core.description,
        ),
        _condition(
            PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,
            "当前强化特殊技触发[强袭训令]（2.5秒触发间隔已满足）",
            next(
                item.description
                for item in raw_record.moves
                if item.name == "特殊技：强袭训令"
            ),
        ),
    ]

    core_source = _source(
        "core-passive:branch-effects",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    sunflame_crit_damage = _number(
        core.description,
        r"\[阳炎\]状态下，佩洛伊斯发动\[终结技\].*?暴击伤害提升(?P<value>[\d.]+)%",
        "Pyrois Sunflame Ultimate Crit Damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "core:sunflame-ultimate-crit-damage",
            core_source,
            f"核心被动：[阳炎]终结技暴击伤害+{sunflame_crit_damage:.0%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(PYROIS_SUNFLAME_ACTIVE,),
            effects=(
                _modifier(
                    "core:sunflame-ultimate-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    sunflame_crit_damage,
                    filters=(
                        DamageDealerFilter(PYROIS_ID),
                        DamageTagFilter(DamageTag.ULTIMATE),
                        EnemyStateFilter(_STUNNED),
                    ),
                ),
            ),
        )
    )

    sunflare_normal_bonus = _number(
        core.description,
        r"\[耀斑\]状态下.*?造成的伤害提升(?P<value>[\d.]+)%",
        "Pyrois Sunflare normal damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "core:sunflare-normal-damage-bonus",
            core_source,
            f"核心被动：[耀斑]伤害+{sunflare_normal_bonus:.1%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(PYROIS_SUNFLARE_ACTIVE,),
            effects=(
                _modifier(
                    "core:sunflare-normal-damage-bonus",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    sunflare_normal_bonus,
                    filters=(DamageDealerFilter(PYROIS_ID),),
                ),
            ),
        )
    )

    left_ratio = _core_ratio(
        core,
        r"重击命中\[浸染\]状态下的敌人时，额外造成等同于(?P<value>[\d.]+)%攻击力",
        "Pyrois left-branch heavy-hit extra damage ratio",
    )
    right_ratio = _core_ratio(
        core,
        r"重击命中失衡敌人触发.*?额外造成等同于(?P<value>[\d.]+)%攻击力",
        "Pyrois right-branch heavy-hit extra damage ratio",
    )
    for key, label, ratio, condition_id, source_template in (
        (
            "left-core-extra-damage",
            "核心被动：左分支重击命中浸染敌人时的额外伤害",
            left_ratio,
            PYROIS_LEFT_CORE_EXTRA_ACTIVE,
            _LEFT_TEMPLATE,
        ),
        (
            "right-core-extra-damage",
            "核心被动：右分支重击命中失衡敌人时的额外伤害",
            right_ratio,
            PYROIS_RIGHT_CORE_EXTRA_ACTIVE,
            _RIGHT_TEMPLATE,
        ),
    ):
        original_text = core.description
        rule_id = RuleItemId(f"rule:character:1551:core:{key}")
        child_id = EventTemplateId(f"template:character:1551:core:{key}:ether-ultimate")
        child_ref = DamageEventTemplateRef(
            template_id=child_id,
            semantic_id=DamageEventSemanticId(f"event:character:1551:core:{key}:ether-ultimate"),
            label=f"核心被动：{label}（以太终结技追加伤害）",
            damage_type=DamageType.DIRECT,
            skill_group=SkillGroup.ULTIMATE,
            damage_tags=frozenset({DamageTag.ULTIMATE}),
            element=Element.ETHER,
            source_rule_item_id=rule_id,
        )
        templates.append(
            DirectDamageEventTemplate(
                ref=child_ref,
                damage_dealer=PYROIS_ID,
                element=Element.ETHER,
                base_source=CurrentAttackValueSource(PYROIS_ID),
                crit_rule=StandardCritRule(PYROIS_ID),
                move_id=None,
            )
        )
        independent_derived.append(
            DerivedDamageEventTemplateRef(
                template=child_ref,
                multiplier=FixedMultiplier(Resolved(ratio)),
            )
        )
        rules.append(
            _rule(
                f"core:{key}",
                core_source,
                label,
                original_text,
                RuleEligibility.ELIGIBLE,
                condition_ids=(condition_id,),
                effects=(
                    EventCreationEffect(
                        rule=EffectRule(
                            effect_id=EffectId(f"effect:character:1551:core:{key}"),
                            source=core_source,
                            owner=PYROIS_ID,
                            target=EffectTarget.TEAM,
                            snapshot_rule=SnapshotRule.SETTLEMENT,
                            filters=(
                                DamageDealerFilter(PYROIS_ID),
                                DamageTypeFilter(DamageType.DIRECT),
                                EventTemplateIdFilter(source_template),
                                *(
                                    (EnemyStateFilter(_STUNNED),)
                                    if key == "right-core-extra-damage"
                                    else ()
                                ),
                            ),
                        ),
                        result=EventCreationResult(
                            event_kind=BattleEventKind.DAMAGE,
                            event_template_id=child_id,
                            unique_per_source_event=True,
                        ),
                    ),
                ),
            )
        )

    extra_source = _source(
        "extra-ability:team-stun-or-support",
        EffectSourceType.ADDITIONAL_ABILITY,
        raw_record.extra_ability_name,
        raw_record.extra_ability_description,
    )
    extra_crit_damage = _number(
        raw_record.extra_ability_description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Pyrois Additional Ability Crit Damage bonus",
    ) / 100.0
    rules.append(
        _rule(
            "extra-ability:team-stun-or-support-crit-damage",
            extra_source,
            f"额外能力：队伍含击破或支援时暴击伤害+{extra_crit_damage:.0%}",
            raw_record.extra_ability_description,
            (
                RuleEligibility.ELIGIBLE
                if config.additional_ability_eligible
                else RuleEligibility.INELIGIBLE
            ),
            effects=(
                _modifier(
                    "extra-ability:team-stun-or-support-crit-damage",
                    extra_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    extra_crit_damage,
                ),
            ),
        )
    )

    cinema1 = raw_record.mindscapes[0]
    cinema1_source = _source(
        "cinema1:crit-rate",
        EffectSourceType.CINEMA,
        f"1影：{cinema1.name}",
        cinema1.description,
    )
    cinema1_crit_rate = _number(
        cinema1.description,
        r"暴击率提升(?P<value>[\d.]+)%",
        "Pyrois Cinema 1 Crit Rate bonus",
    ) / 100.0
    rules.append(
        _rule(
            "cinema1:crit-rate",
            cinema1_source,
            f"1影：暴击率+{cinema1_crit_rate:.0%}",
            cinema1.description,
            (
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= 1
                else RuleEligibility.INELIGIBLE
            ),
            effects=(
                _modifier(
                    "cinema1:crit-rate",
                    cinema1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    cinema1_crit_rate,
                ),
            ),
        )
    )

    # C2 and C4 are resource/shield/Daze-only. C6 explicitly says its effect
    # has not been revealed, so neither is represented as an empty damage row.
    order_move = next(
        item for item in raw_record.moves if item.name == "特殊技：强袭训令"
    )
    order_source = _source(
        "skill:special-battle-order",
        EffectSourceType.SKILL,
        order_move.name,
        order_move.description,
    )
    order_diagnostics: list[CalculationDiagnostic] = []
    order_ratio = raw_multiplier(
        raw_move_index(raw_record),
        order_move.name,
        "伤害倍率",
        effective_skill_level(config, SkillGroup.SPECIAL_ATTACK),
        "character:1551:special-battle-order",
        order_diagnostics,
        "1551022",
    )
    if isinstance(order_ratio, Unresolved):
        ratio_note = order_ratio.notes
    else:
        ratio_note = f"Known selected-level independent Special damage curve: {order_ratio:.4g}x ATK."

    order_rule_id = RuleItemId("rule:character:1551:skill:special-battle-order-ultimate-trigger")
    order_template_id = EventTemplateId("template:character:1551:special-battle-order:ether")
    order_ref = DamageEventTemplateRef(
        template_id=order_template_id,
        semantic_id=DamageEventSemanticId("event:character:1551:special-battle-order:ether"),
        label="特殊技：强袭训令（以太伤害）",
        damage_type=DamageType.DIRECT,
        skill_group=SkillGroup.SPECIAL_ATTACK,
        damage_tags=frozenset({DamageTag.SPECIAL_ATTACK}),
        element=Element.ETHER,
        source_rule_item_id=order_rule_id,
    )
    templates.append(
        DirectDamageEventTemplate(
            ref=order_ref,
            damage_dealer=PYROIS_ID,
            element=Element.ETHER,
            base_source=CurrentAttackValueSource(PYROIS_ID),
            crit_rule=StandardCritRule(PYROIS_ID),
            move_id=None,
        )
    )
    independent_derived.append(
        DerivedDamageEventTemplateRef(
            template=order_ref,
            multiplier=FixedMultiplier(
                order_ratio if isinstance(order_ratio, Unresolved) else Resolved(order_ratio)
            ),
        )
    )
    def _order_trigger_effect(effect_suffix: str, parent: EventTemplateId):
        return EventCreationEffect(
            rule=EffectRule(
                effect_id=EffectId(
                    f"effect:character:1551:skill:special-battle-order:{effect_suffix}"
                ),
                source=order_source,
                owner=PYROIS_ID,
                target=EffectTarget.TEAM,
                snapshot_rule=SnapshotRule.SETTLEMENT,
                filters=(
                    DamageTypeFilter(DamageType.DIRECT),
                    DamageDealerFilter(PYROIS_ID),
                    EventTemplateIdFilter(parent),
                ),
            ),
            result=EventCreationResult(
                event_kind=BattleEventKind.DAMAGE,
                event_template_id=order_template_id,
                unique_per_source_event=True,
            ),
        )

    ult_order_rule_id = RuleItemId(
        "rule:character:1551:skill:special-battle-order-ultimate-trigger"
    )
    rules.append(
        _rule(
            "skill:special-battle-order-ultimate-trigger",
            order_source,
            "特殊技：强袭训令（终结技必定触发；伤害归属佩洛伊斯）",
            order_move.description,
            RuleEligibility.ELIGIBLE,
            effects=tuple(
                _order_trigger_effect(f"ultimate-{index}", template_id)
                for index, template_id in enumerate(_ULTIMATE_TEMPLATES, start=1)
            ),
        )
    )
    rules.append(
        _rule(
            "skill:special-battle-order-ex-trigger",
            order_source,
            "特殊技：强袭训令（强化特殊技触发间隔已满足时）",
            order_move.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(PYROIS_EX_ASSIST_ORDER_PROC_ACTIVE,),
            effects=(_order_trigger_effect("ex-special", _EX_TEMPLATE),),
        )
    )

    return build_definition(
        character_id=PYROIS_ID,
        role=CharacterRole.ATTACK,
        element=Element.ETHER,
        source=source_for(
            PYROIS_ID,
            "live-source",
            EffectSourceType.SKILL,
            raw_record.name,
            f"Nanoka {raw_record.source_version}: {raw_record.source_url}",
        ),
        entries=entries,
        templates=templates,
        independent_derived_damage_events=independent_derived,
        rules=rules,
        conditions=conditions,
        diagnostics=(*move_diagnostics, *order_diagnostics),
    )


__all__ = ["compile_pyrois", "load_raw_record"]
