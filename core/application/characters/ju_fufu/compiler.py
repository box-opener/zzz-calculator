"""Compile Ju Fufu's reviewed Nanoka 3.2 direct moves and current-state rules."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import (
    BattleEventKind,
    CalculationNode,
    CharacterRole,
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
    PanelStatDerivedValue,
    Resolved,
    RuleSource,
    SnapshotRule,
    StateId,
    Unresolved,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DiagnosticId, RuleItemId, ScenarioConditionId
from ...moves import MultiplierRelation
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    raw_move_index,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from .config import JU_FUFU_ID, JuFufuCompileConfig
from .reviewed import JU_FUFU_REVIEWED_MAPPING


JU_FUFU_TIGER_ROAR_ACTIVE = ScenarioConditionId(
    "condition:character:1391:tiger-roar-active"
)
JU_FUFU_C1_TARGET_DEBUFF_ACTIVE = ScenarioConditionId(
    "condition:character:1391:c1-chain-target-debuff-active"
)
_ENEMY_STUNNED = StateId("state:enemy:stunned")
_FIERY_SPIN_TEMPLATE = EventTemplateId(
    "template:character:1391:dash-tiger-cauldron-fire:main"
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, subject: str) -> float:
    found = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(found) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(found)}")
    return float(found[0].group("value"))


def _condition(
    condition_id: ScenarioConditionId,
    label: str,
    original_text: str,
    value: bool,
) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=original_text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(
    key: str,
    kind: EffectSourceType,
    label: str,
    original_text: str,
) -> RuleSource:
    return source_for(JU_FUFU_ID, key, kind, label, original_text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    original_text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1391:{key}"),
        owner=JU_FUFU_ID,
        source=source,
        display_name=label,
        original_text=original_text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1391:{key}"),
            source=source,
            owner=JU_FUFU_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _note(key: str, message: str, original_text: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"unsupported:character:1391:{key}"),
        kind=DiagnosticKind.UNSUPPORTED_CALCULATOR,
        message=message,
        blocking=False,
        original_text=original_text,
    )


def _validate_raw(raw: NanokaRawRecord, config: JuFufuCompileConfig) -> None:
    if (
        raw.character_id != JU_FUFU_ID
        or raw.name != "橘福福"
        or raw.code_name != "Ju Fufu"
        or raw.specialty != "击破"
        or raw.element != "火属性"
        or raw.faction != "云岿山"
        or raw.icon != "IconRole43"
        or raw.rarity != 4
    ):
        raise ValueError("raw identity does not match reviewed Ju Fufu source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1391.json"
    ):
        raise ValueError("Ju Fufu provenance must identify Nanoka 3.2 character 1391")
    if raw.potential_details:
        raise ValueError("Ju Fufu 3.2 source does not have Potential variants")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Ju Fufu source must contain seven Core levels and six Cinemas")
    if config.character_id != JU_FUFU_ID:
        raise ValueError("Ju Fufu compile config has an unexpected character ID")


def _cinema(raw: NanokaRawRecord, level: int):
    match = next((item for item in raw.mindscapes if item.level == level), None)
    if match is None:
        raise ValueError(f"Ju Fufu source is missing Cinema {level}")
    return match


def _core_values(raw: NanokaRawRecord, level: int) -> tuple[float, ...]:
    core = raw.core_levels[level - 1]
    text = core.description
    base_crit_damage = _number(
        text,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Ju Fufu Core team Crit Damage",
    ) / 100.0
    ratio_match = re.search(
        r"连携技.{0,45}?终结技.{0,20}?提升[\s\S]*?(?P<chain>[\d.]+)%/(?P<ultimate>[\d.]+)%",
        _plain(text),
    )
    if ratio_match is None:
        raise ValueError("Ju Fufu Core must expose Chain and Ultimate damage bonuses")
    impact = _number(
        text,
        r"冲击力提升(?P<value>[\d.]+)点",
        "Ju Fufu Core Impact",
    )
    threshold = _number(
        text,
        r"初始攻击力大于等于(?P<value>\d+(?:\.\d+)?)点",
        "Ju Fufu Core initial ATK threshold",
    )
    step = _number(
        text,
        r"每超过(?P<value>\d+(?:\.\d+)?)点攻击力",
        "Ju Fufu Core initial ATK step",
    )
    per_step = _number(
        text,
        r"每超过[\d.]+点攻击力会使暴击伤害额外提升(?P<value>[\d.]+)%",
        "Ju Fufu Core Crit Damage per ATK step",
    ) / 100.0
    cap = _number(
        text,
        r"最多额外提升(?P<value>[\d.]+)%",
        "Ju Fufu Core extra Crit Damage cap",
    ) / 100.0
    return (
        base_crit_damage,
        float(ratio_match.group("chain")) / 100.0,
        float(ratio_match.group("ultimate")) / 100.0,
        impact,
        threshold,
        step,
        per_step,
        cap,
    )


def _fire_spin_popcorn_effects(
    source: RuleSource,
    original_text: str,
    *,
    count: int,
    ratio: float,
) -> tuple[EventCreationEffect, ...]:
    effects = []
    for ordinal in range(1, count + 1):
        unresolved = Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
            notes=(
                f"The source requires popcorn packet {ordinal} of {count} for the selected 威势 spin. "
                f"Its known amount is {ratio:.4g} × Ju Fufu ATK; it is Ju Fufu-owned Chain Attack damage with no MoveId. "
                "The source does not specify the child packet's element."
            ),
            original_text=original_text,
        )
        effects.append(
            EventCreationEffect(
                rule=EffectRule(
                    effect_id=EffectId(
                        f"effect:character:1391:cinema6:popcorn-{ordinal}"
                    ),
                    source=source,
                    owner=JU_FUFU_ID,
                    target=EffectTarget.TEAM,
                    snapshot_rule=SnapshotRule.SETTLEMENT,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(JU_FUFU_ID),
                        EventTemplateIdFilter(_FIERY_SPIN_TEMPLATE),
                    ),
                ),
                result=EventCreationResult(
                    event_kind=BattleEventKind.DAMAGE,
                    unresolved_template=unresolved,
                    unique_per_source_event=True,
                ),
            )
        )
    return tuple(effects)


def compile_ju_fufu(
    config: JuFufuCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    """Compile selectable Direct entries and current state without replaying combat."""

    _validate_raw(raw_record, config)
    entries, templates, move_diagnostics = compile_direct_moves(
        character_id=JU_FUFU_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=JU_FUFU_REVIEWED_MAPPING,
        id_namespace="character:1391",
    )
    raw_moves = raw_move_index(raw_record)
    core = raw_record.core_levels[config.core_level - 1]
    cinemas = {level: _cinema(raw_record, level) for level in range(1, 7)}
    core_source = _source(
        "core-passive",
        EffectSourceType.CORE_PASSIVE,
        core.name,
        core.description,
    )
    cinema_sources = {
        level: _source(
            f"cinema-{level}",
            EffectSourceType.CINEMA,
            item.name,
            item.description,
        )
        for level, item in cinemas.items()
    }
    (
        core_crit_damage,
        core_chain_bonus,
        core_ultimate_bonus,
        core_impact,
        core_attack_threshold,
        core_attack_step,
        core_crit_damage_per_step,
        core_crit_damage_cap,
    ) = _core_values(raw_record, config.core_level)

    conditions = [
        _condition(
            JU_FUFU_TIGER_ROAR_ACTIVE,
            "虎啸当前生效",
            core.description,
            config.tiger_roar_active,
        )
    ]
    rules: list[CalculationRuleItem] = []
    rules.append(
        _rule(
            "core:tiger-roar",
            core_source,
            f"核心被动：虎啸当前生效时全队暴伤+{core_crit_damage:.1%}，连携/终结伤害+{core_chain_bonus:.1%}/{core_ultimate_bonus:.1%}",
            core.description,
            RuleEligibility.ELIGIBLE,
            condition_ids=(JU_FUFU_TIGER_ROAR_ACTIVE,),
            effects=(
                _modifier(
                    "core:tiger-roar:team-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(core_crit_damage),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "core:tiger-roar:initial-attack-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    PanelStatDerivedValue(
                        source_character_id=JU_FUFU_ID,
                        source_node=CalculationNode.CHARACTER_INITIAL_ATTACK,
                        coefficient=Resolved(core_crit_damage_per_step),
                        threshold=Resolved(core_attack_threshold),
                        step_size=Resolved(core_attack_step),
                        cap_max=Resolved(core_crit_damage_cap),
                    ),
                    target=EffectTarget.TEAM,
                ),
                _modifier(
                    "core:tiger-roar:chain-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_chain_bonus),
                    target=EffectTarget.TEAM,
                    filters=(DamageTagFilter(DamageTag.CHAIN_ATTACK),),
                ),
                _modifier(
                    "core:tiger-roar:ultimate-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_ultimate_bonus),
                    target=EffectTarget.TEAM,
                    filters=(DamageTagFilter(DamageTag.ULTIMATE),),
                ),
                _modifier(
                    "core:tiger-roar:ju-fufu-impact",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
                    Resolved(core_impact),
                    target=EffectTarget.SELF,
                ),
            ),
        )
    )
    extra_note = _note(
        "extra-ability:decibel-resource",
        (
            "The Extra Ability is eligible for the current roster. It grants +1000 Decibel cap and Ultimate Decibel recovery; "
            "the current result does not simulate Decibel or energy resources."
            if config.additional_ability_eligible
            else "The Extra Ability is ineligible for the current roster. If enabled by another Attack or Rupture agent, its +1000 Decibel cap and Ultimate Decibel recovery are resource effects; the current result does not simulate Decibel or energy resources."
        ),
        raw_record.extra_ability_description,
    )

    c1 = cinemas[1]
    c1_text = c1.description
    c1_crit_rate = _number(
        c1_text,
        r"暴击率提升(?P<value>[\d.]+)%",
        "Ju Fufu Cinema 1 Crit Rate",
    ) / 100.0
    c1_stun_vulnerability = _number(
        c1_text,
        r"失衡易伤倍率提升(?P<value>[\d.]+)%",
        "Ju Fufu Cinema 1 target Stun Vulnerability",
    ) / 100.0
    c1_unlocked = config.cinema_level >= 1
    rules.append(
        _rule(
            "cinema1:crit-rate",
            cinema_sources[1],
            f"1影：入场后自身暴击率+{c1_crit_rate:.0%}",
            c1_text,
            RuleEligibility.ELIGIBLE if c1_unlocked else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:crit-rate",
                    cinema_sources[1],
                    CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
                    Resolved(c1_crit_rate),
                    target=EffectTarget.SELF,
                ),
            ) if c1_unlocked else (),
        )
    )
    rules.append(
        _rule(
            "cinema1:chain-target-stun-vulnerability",
            cinema_sources[1],
            f"1影：标记目标失衡时失衡易伤倍率+{c1_stun_vulnerability:.0%}",
            c1_text,
            RuleEligibility.ELIGIBLE if c1_unlocked else RuleEligibility.INELIGIBLE,
            condition_ids=(JU_FUFU_C1_TARGET_DEBUFF_ACTIVE,) if c1_unlocked else (),
            effects=(
                _modifier(
                    "cinema1:chain-target-stun-vulnerability",
                    cinema_sources[1],
                    CalculationNode.ENEMY_STUN_VULNERABILITY,
                    Resolved(c1_stun_vulnerability),
                    target=EffectTarget.ENEMY,
                    filters=(EnemyStateFilter(_ENEMY_STUNNED),),
                ),
            ) if c1_unlocked else (),
        )
    )
    if c1_unlocked:
        conditions.append(
            _condition(
                JU_FUFU_C1_TARGET_DEBUFF_ACTIVE,
                "当前目标仍处于橘福福连携技施加的失衡易伤提升状态",
                c1_text,
                config.c1_target_debuff_active,
            )
        )

    c2 = cinemas[2]
    c2_bonus = _number(
        c2.description,
        r"暴击伤害额外提升(?P<value>[\d.]+)%",
        "Ju Fufu Cinema 2 team Crit Damage",
    ) / 100.0
    c2_unlocked = config.cinema_level >= 2
    rules.append(
        _rule(
            "cinema2:tiger-roar-team-crit-damage",
            cinema_sources[2],
            f"2影：虎啸期间全队暴击伤害额外+{c2_bonus:.0%}",
            c2.description,
            RuleEligibility.ELIGIBLE if c2_unlocked else RuleEligibility.INELIGIBLE,
            condition_ids=(JU_FUFU_TIGER_ROAR_ACTIVE,) if c2_unlocked else (),
            effects=(
                _modifier(
                    "cinema2:tiger-roar-team-crit-damage",
                    cinema_sources[2],
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c2_bonus),
                    target=EffectTarget.TEAM,
                ),
            ) if c2_unlocked else (),
        )
    )

    for level in (3, 5):
        cinema = cinemas[level]
        unlocked = config.cinema_level >= level
        rules.append(
            _rule(
                f"cinema{level}:skill-levels",
                cinema_sources[level],
                f"{level}影：技能等级+2（包括终结技，受16级上限约束）",
                cinema.description,
                RuleEligibility.ELIGIBLE if unlocked else RuleEligibility.INELIGIBLE,
            )
        )

    c4 = cinemas[4]
    c4_bonus = _number(
        c4.description,
        r"自身的暴击伤害提升(?P<value>[\d.]+)%",
        "Ju Fufu Cinema 4 Crit Damage",
    ) / 100.0
    c4_unlocked = config.cinema_level >= 4
    rules.append(
        _rule(
            "cinema4:tiger-roar-self-crit-damage",
            cinema_sources[4],
            f"4影：虎啸期间自身暴击伤害+{c4_bonus:.0%}",
            c4.description,
            RuleEligibility.ELIGIBLE if c4_unlocked else RuleEligibility.INELIGIBLE,
            condition_ids=(JU_FUFU_TIGER_ROAR_ACTIVE,) if c4_unlocked else (),
            effects=(
                _modifier(
                    "cinema4:tiger-roar-self-crit-damage",
                    cinema_sources[4],
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c4_bonus),
                    target=EffectTarget.SELF,
                ),
            ) if c4_unlocked else (),
        )
    )

    c6 = cinemas[6]
    c6_ratio_match = re.search(
        r"发射(?P<count>\d+)个爆米花，每个爆米花造成福福攻击力(?P<ratio>[\d.]+)%的伤害",
        _plain(c6.description),
    )
    if c6_ratio_match is None:
        raise ValueError("Ju Fufu Cinema 6 must expose popcorn count and ATK ratio")
    c6_count = int(c6_ratio_match.group("count"))
    c6_popcorn_ratio = float(c6_ratio_match.group("ratio")) / 100.0
    c6_chain_bonus = _number(
        c6.description,
        r"\[连携技\].{0,10}?造成的伤害提升(?P<value>[\d.]+)%",
        "Ju Fufu Cinema 6 Chain damage bonus",
    ) / 100.0
    c6_unlocked = config.cinema_level >= 6
    rules.append(
        _rule(
            "cinema6:chain-damage",
            cinema_sources[6],
            f"6影：自身连携技伤害+{c6_chain_bonus:.0%}",
            c6.description,
            RuleEligibility.ELIGIBLE if c6_unlocked else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema6:chain-damage",
                    cinema_sources[6],
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(c6_chain_bonus),
                    target=EffectTarget.SELF,
                    filters=(
                        DamageTypeFilter(DamageType.DIRECT),
                        DamageDealerFilter(JU_FUFU_ID),
                        DamageTagFilter(DamageTag.CHAIN_ATTACK),
                    ),
                ),
            ) if c6_unlocked else (),
        )
    )
    rules.append(
        _rule(
            "cinema6:fire-spin-popcorn",
            cinema_sources[6],
            f"6影：威势旋转命中后生成{c6_count}枚爆米花追加伤害（属性待明确）",
            c6.description,
            RuleEligibility.ELIGIBLE if c6_unlocked else RuleEligibility.INELIGIBLE,
            effects=(
                _fire_spin_popcorn_effects(
                    cinema_sources[6],
                    c6.description,
                    count=c6_count,
                    ratio=c6_popcorn_ratio,
                )
                if c6_unlocked else ()
            ),
        )
    )

    parry = raw_moves.get("招架支援：岿然虎踞")
    parry_note = (
        (
            _note(
                "assist-parry:daze-only",
                "The source lists Daze multipliers but no damage ratio. The current result has no Daze output, so no damage entry is created.",
                parry.description,
            ),
        )
        if parry is not None
        else ()
    )
    all_diagnostics = (*move_diagnostics, extra_note, *parry_note)
    return build_definition(
        character_id=JU_FUFU_ID,
        role=CharacterRole.STUN,
        element=Element.FIRE,
        source=_source(
            "character",
            EffectSourceType.SKILL,
            raw_record.name,
            f"{raw_record.code_name}; Nanoka {raw_record.source_version}: {raw_record.source_url}",
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        diagnostics=all_diagnostics,
    )


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(JU_FUFU_ID))


__all__ = ["compile_ju_fufu", "load_raw_record"]
