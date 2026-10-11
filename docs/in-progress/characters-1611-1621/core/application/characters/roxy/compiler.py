"""Compile Roxy's reviewed Nanoka source and current-state rules."""

from __future__ import annotations

from collections.abc import Mapping
import re

from core.types import CharacterRole, EffectSourceType, Element
from core.types import (
    AllCondition,
    AnyCondition,
    CalculationNode,
    CharacterRoleFilter,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectTarget,
    ElementFilter,
    EventTemplateId,
    EventTemplateIdFilter,
    FixedMultiplier,
    ModifierEffect,
    ModifierResult,
    NotFilter,
    PanelStatDerivedValue,
    Resolved,
    SnapshotRule,
    Unresolved,
)

from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from ...diagnostics import CalculationDiagnostic
from ...ids import RuleItemId, ScenarioConditionId
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import ConditionResolution, ScenarioCondition
from .config import ROXY_ID, RoxyCompileConfig
from .reviewed import (
    ROXY_EX_CANNON_MOVE_ID,
    ROXY_REVIEWED_MAPPING,
    ROXY_ULTIMATE_MOVE_ID,
)


ROXY_CORE_CRIT_BUFF_ACTIVE = ScenarioConditionId(
    "condition:character:1621:core-crit-damage-buff-active"
)
ROXY_C1_RESISTANCE_REDUCTION_ACTIVE = ScenarioConditionId(
    "condition:character:1621:cinema1-resistance-reduction-active"
)
ROXY_C2_STUN_VULNERABILITY_ACTIVE = ScenarioConditionId(
    "condition:character:1621:cinema2-stun-vulnerability-active"
)
ROXY_EXTRA_STUN_VULNERABILITY_ACTIVE = ScenarioConditionId(
    "condition:character:1621:extra-stun-vulnerability-active"
)
ROXY_ENEMY_WINDED = ScenarioConditionId("condition:character:1621:enemy-winded")

_ROXY_INFUSION_CONDITIONS = {
    Element.PHYSICAL: ScenarioConditionId(
        "condition:character:1621:infusion-physical-active"
    ),
    Element.FIRE: ScenarioConditionId("condition:character:1621:infusion-fire-active"),
    Element.ELECTRIC: ScenarioConditionId(
        "condition:character:1621:infusion-electric-active"
    ),
    Element.ICE: ScenarioConditionId("condition:character:1621:infusion-ice-active"),
    Element.ETHER: ScenarioConditionId("condition:character:1621:infusion-ether-active"),
    Element.WIND: ScenarioConditionId("condition:character:1621:infusion-wind-active"),
}
_CORE_RULE_ID = RuleItemId("rule:character:1621:core:initial-energy-bonuses")
_CORE_CINEMA7_DEFAULT = 7
_DIRECT = DamageTypeFilter(DamageType.DIRECT)


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(ROXY_ID))


def _validate_raw(raw: NanokaRawRecord, config: RoxyCompileConfig) -> None:
    if raw.character_id != config.character_id:
        raise ValueError("Roxy raw record and compile config IDs must match")
    if (
        raw.name != "洛克茜"
        or raw.code_name != "Roxy"
        or raw.rarity != 4
        or raw.specialty != "击破"
        or raw.element != "风属性"
        or raw.faction != "罗斯凯利法"
        or raw.icon != "IconRole68"
    ):
        raise ValueError("unexpected identity in Roxy live Nanoka source")
    if raw.source_version != "3.2" or raw.source_url != (
        "https://static.nanoka.cc/zzz/3.2/zh/character/1621.json"
    ):
        raise ValueError("Roxy provenance does not match Nanoka live3.2")
    if len(raw.core_levels) != 7 or len(raw.mindscapes) != 6:
        raise ValueError("Roxy source must contain seven Core levels and six Cinemas")
    expected = {spec.source_name for spec in ROXY_REVIEWED_MAPPING.moves}
    available = {move.name for move in raw.moves}
    if missing := expected - available:
        raise ValueError(f"raw Roxy record is missing reviewed moves: {sorted(missing)}")


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _number(text: str, pattern: str, label: str) -> float:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if len(matches) != 1:
        raise ValueError(f"{label} must contain exactly one source value")
    return float(matches[0].group("value"))


def _source(key: str, source_type: EffectSourceType, label: str, text: str):
    return source_for(ROXY_ID, key, source_type, label, text)


def _condition(condition_id, label: str, text: str) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=False,
    )


def _rule(key: str, source, label: str, text: str, eligibility, *, effects=()):
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1621:{key}"),
        owner=ROXY_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
    )


def _modifier(
    key: str,
    source,
    path: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    condition=None,
    operation: EffectOperation = EffectOperation.ADD,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1621:{key}"),
            source=source,
            owner=ROXY_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=tuple(filters),
            condition=condition,
        ),
        result=ModifierResult(
            modifier_path=path,
            operation=operation,
            value=value,
        ),
    )


def _move_filter(entry_key: str):
    return EventTemplateIdFilter(
        EventTemplateId(f"template:{ROXY_ID}:{entry_key}:main")
    )


def _core_cap(raw: NanokaRawRecord, level: int, label: str, pattern: str) -> float:
    text = raw.core_levels[level - 1].description
    return _number(text, pattern, label) / 100.0


def _current_infusions(raw: NanokaRawRecord) -> tuple[ScenarioCondition, ...]:
    text = raw.core_levels[0].description
    labels = {
        Element.PHYSICAL: "物理",
        Element.FIRE: "火",
        Element.ELECTRIC: "电",
        Element.ICE: "冰",
        Element.ETHER: "以太",
        Element.WIND: "风",
    }
    return tuple(
        _condition(
            condition_id,
            f"当前仍存在{labels[element]}属性[浸染/净化]增益",
            text,
        )
        for element, condition_id in _ROXY_INFUSION_CONDITIONS.items()
    )


def _core_effects(raw: NanokaRawRecord, level: int, source):
    text = raw.core_levels[level - 1].description
    attack_cap = _number(
        text,
        r"攻击力提升5点，最多提升<color=[^>]*>(?P<value>\d+(?:\.\d+)?)</color>点",
        "Roxy Core Initial ER ATK cap",
    )
    impact_cap = _number(
        text,
        r"冲击力提升0\.4点，最多提升<color=[^>]*>(?P<value>\d+(?:\.\d+)?)</color>点",
        "Roxy Core Initial ER Impact cap",
    )
    cd_cap = _number(
        text,
        r"暴击伤害提升0\.4%，最多提升<color=[^>]*>(?P<value>\d+(?:\.\d+)?)%</color>",
        "Roxy Core Crit Damage cap",
    ) / 100.0
    initial_er_attack = PanelStatDerivedValue(
        source_character_id=ROXY_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        coefficient=Resolved(5.0),
        threshold=Resolved(1.2),
        step_size=Resolved(0.01),
        cap_max=Resolved(attack_cap),
    )
    initial_er_impact = PanelStatDerivedValue(
        source_character_id=ROXY_ID,
        source_node=CalculationNode.CHARACTER_INITIAL_ENERGY_REGEN,
        coefficient=Resolved(0.4),
        threshold=Resolved(1.2),
        step_size=Resolved(0.01),
        cap_max=Resolved(impact_cap),
    )
    current_cr_cd = PanelStatDerivedValue(
        source_character_id=ROXY_ID,
        source_node=CalculationNode.CHARACTER_CURRENT_CRIT_RATE,
        coefficient=Resolved(0.004),
        threshold=Resolved(0.0),
        step_size=Resolved(0.01),
        cap_max=Resolved(cd_cap),
    )
    recipient_filters = (NotFilter(CharacterRoleFilter(CharacterRole.VANGUARD)),)
    elements = tuple(element for element in _ROXY_INFUSION_CONDITIONS if element is not Element.WIND)
    effects = [
        _modifier(
            "core:initial-er-attack-flat",
            source,
            CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
            initial_er_attack,
            target=EffectTarget.SELF,
        ),
        _modifier(
            "core:initial-er-impact-flat",
            source,
            CalculationNode.CHARACTER_COMBAT_IMPACT_FLAT_BONUS,
            initial_er_impact,
            target=EffectTarget.SELF,
        ),
    ]
    # Every active attribute buff grants its corresponding Direct element.
    # Wind is added once through a single AnyCondition effect, even when several
    # attribute buffs coexist.
    for element in elements:
        effects.append(
            _modifier(
                f"core:team-crit-damage:{element.value}",
                source,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                current_cr_cd,
                target=EffectTarget.TEAM,
                filters=(DamageTypeFilter(DamageType.DIRECT), ElementFilter(element), *recipient_filters),
                condition=AllCondition(
                    (
                        __import__("core.types", fromlist=["ScenarioCondition"]).ScenarioCondition,  # replaced below
                    )
                ),
            )
        )
    return effects


def compile_roxy(
    config: RoxyCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    """Compile ordinary reviewed Direct entries before adding Roxy's effects."""

    _validate_raw(raw_record, config)
    entries, templates, diagnostics = compile_direct_moves(
        character_id=ROXY_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=ROXY_REVIEWED_MAPPING,
    )
    raw_moves = {move.name: move for move in raw_record.moves}
    core = raw_record.core_levels[config.core_level - 1]
    extra_text = core.extra_ability_description
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    extra_source = _source("extra-ability", EffectSourceType.ADDITIONAL_ABILITY, core.extra_ability_name, extra_text)
    cinemas = {item.level: item for item in raw_record.mindscapes}
    cinema_sources = {
        level: _source(f"cinema{level}", EffectSourceType.CINEMA, item.name, item.description)
        for level, item in cinemas.items()
    }

    conditions = [*_current_infusions(raw_record)]
    conditions.extend(
        (
            _condition(
                ROXY_CORE_CRIT_BUFF_ACTIVE,
                "当前存在洛克茜的[浸染/净化]全队增益",
                core.description,
            ),
            _condition(
                ROXY_C1_RESISTANCE_REDUCTION_ACTIVE,
                "当前敌人仍处于[敬请安息]命中后的全属性抗性降低期间",
                cinemas[1].description,
            ),
            _condition(
                ROXY_C2_STUN_VULNERABILITY_ACTIVE,
                "当前敌人仍处于[小心风寒]命中后的失衡易伤提升期间",
                cinemas[2].description,
            ),
            _condition(
                ROXY_EXTRA_STUN_VULNERABILITY_ACTIVE,
                "当前敌人仍处于队伍角色攻击命中后的额外能力失衡易伤期间",
                extra_text,
            ),
            _condition(ROXY_ENEMY_WINDED, "目标当前处于队伍造成的[风化]状态", extra_text),
        )
    )
    core_effects = _core_effects(raw_record, config.core_level, core_source)

    rules = [
        _rule(
            "core:initial-energy-bonuses",
            core_source,
            "核心被动：初始能量自动回复与当前暴击率增益",
            core.description,
            RuleEligibility.ELIGIBLE,
            effects=core_effects,
        )
    ]

    return build_definition(
        character_id=ROXY_ID,
        role=CharacterRole.STUN,
        element=Element.WIND,
        source=source_for(
            ROXY_ID,
            "live-source",
            EffectSourceType.SPECIAL_MECHANISM,
            raw_record.name,
            f"{raw_record.source_url} (source_version={raw_record.source_version})",
        ),
        entries=entries,
        templates=templates,
        rules=rules,
        conditions=conditions,
        diagnostics=diagnostics,
    )


__all__ = ["compile_roxy", "load_raw_record"]
