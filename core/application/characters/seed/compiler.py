"""Compile Seed's reviewed Nanoka 3.2 source into the calculation contracts."""

from __future__ import annotations

import re

from core.types import (
    AnyFilter,
    BattleEventKind,
    CalculationNode,
    CharacterId,
    CharacterRole,
    DamageDealerFilter,
    DamageType,
    DamageTypeFilter,
    EffectId,
    EffectOperation,
    EffectRule,
    EffectSourceType,
    EffectTarget,
    Element,
    EventCreationEffect,
    EventCreationResult,
    EventTemplateId,
    EventTemplateIdFilter,
    ModifierEffect,
    ModifierResult,
    Resolved,
    RuleSource,
    ScenarioParameterDerivedValue,
    SnapshotRule,
    Unresolved,
    UnresolvedEffect,
    UnresolvedReason,
)

from ...diagnostics import CalculationDiagnostic, DiagnosticKind
from ...ids import DiagnosticId, RuleItemId
from ...moves import MoveCalculationEntry
from ...rules import CalculationRuleItem, RuleEligibility
from ...scenario import (
    ConditionResolution,
    ParameterResolution,
    ScenarioCondition,
    ScenarioIntegerParameter,
)
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import (
    NanokaRawRecord,
    build_definition,
    compile_direct_moves,
    source_for,
)
from ..nanoka_source import load_nanoka_raw_record
from .config import SEED_ID, SeedCompileConfig
from .reviewed import (
    CINEMA2_ENERGY_INTERVALS_SPENT,
    CINEMA6_LASER_PROC_ACTIVE,
    PARTNER_EX_BUFF_ACTIVE,
    PARTNER_SURROUND_HUNT_ACTIVE,
    SEED_EX_BUFF_ACTIVE,
    SEED_SURROUND_HUNT_ACTIVE,
    SEED_REVIEWED_MAPPING,
)


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _values(text: str, pattern: str, subject: str) -> tuple[float, ...]:
    matches = tuple(re.finditer(pattern, _plain(text), re.DOTALL))
    if not matches:
        raise ValueError(f"{subject} source value was not found")
    return tuple(float(match.group("value")) for match in matches)


def _one(text: str, pattern: str, subject: str) -> float:
    found = _values(text, pattern, subject)
    if len(found) != 1:
        raise ValueError(f"{subject} must contain one source value; found {len(found)}")
    return found[0]


def _repeated(text: str, pattern: str, subject: str) -> float:
    found = _values(text, pattern, subject)
    if len(set(found)) != 1:
        raise ValueError(f"{subject} repeated source values disagree: {found}")
    return found[0]


def _condition(condition_id, label: str, text: str, value: bool) -> ScenarioCondition:
    return ScenarioCondition(
        condition_id=condition_id,
        label=label,
        original_text=text,
        resolution=ConditionResolution.USER_SELECTED,
        value=value,
    )


def _source(key: str, kind: EffectSourceType, label: str, text: str) -> RuleSource:
    return source_for(SEED_ID, key, kind, label, text)


def _rule(
    key: str,
    source: RuleSource,
    label: str,
    text: str,
    eligibility: RuleEligibility,
    *,
    effects=(),
    condition_ids=(),
    diagnostics=(),
) -> CalculationRuleItem:
    return CalculationRuleItem(
        rule_id=RuleItemId(f"rule:character:1461:{key}"),
        owner=SEED_ID,
        source=source,
        display_name=label,
        original_text=text,
        eligibility=eligibility,
        effects=tuple(effects),
        condition_ids=tuple(condition_ids),
        diagnostics=tuple(diagnostics),
    )


def _modifier(
    key: str,
    source: RuleSource,
    node: CalculationNode,
    value,
    *,
    target: EffectTarget,
    filters=(),
    condition=None,
    recipient_character_id=None,
) -> ModifierEffect:
    return ModifierEffect(
        rule=EffectRule(
            effect_id=EffectId(f"effect:character:1461:{key}"),
            source=source,
            owner=SEED_ID,
            target=target,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            condition=condition,
            filters=tuple(filters),
            recipient_character_id=recipient_character_id,
        ),
        result=ModifierResult(
            modifier_path=node,
            operation=EffectOperation.ADD,
            value=value,
        ),
    )


def _unresolved_partner_effect(
    key: str,
    source: RuleSource,
    candidate_id: CharacterId,
    candidate_ids: tuple[CharacterId, ...],
    *,
    original_text: str,
    known_effect: str,
    extra_filters=(),
) -> UnresolvedEffect:
    candidate_suffix = str(candidate_id).replace(":", "_")
    return UnresolvedEffect(
        rule=EffectRule(
            effect_id=EffectId(
                f"effect:character:1461:{key}:candidate:{candidate_suffix}"
            ),
            source=source,
            owner=SEED_ID,
            target=EffectTarget.TEAM,
            snapshot_rule=SnapshotRule.SETTLEMENT,
            filters=(DamageDealerFilter(candidate_id), *extra_filters),
        ),
        unresolved=Unresolved(
            reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
            notes=(
                f"The known Seed Core effect ({known_effect}) applies to the other "
                "Attack teammate with the highest Initial ATK, "
                "but that recipient is not uniquely resolved. This candidate's damage cannot be reported as complete while "
                "the corresponding condition and rule are active."
            ),
            original_text=original_text,
            candidates=tuple(str(item) for item in candidate_ids),
        ),
    )


def _validate_raw_record(raw: NanokaRawRecord, config: SeedCompileConfig) -> None:
    if raw.character_id != SEED_ID:
        raise ValueError(f"Seed compiler requires {SEED_ID}; got {raw.character_id}")
    if raw.code_name != "Seed" or raw.rarity != 4:
        raise ValueError("Seed compiler requires the reviewed S-rank Seed source")
    if (raw.specialty, raw.element, raw.faction) != (
        "强攻",
        "电属性",
        "新艾利都防卫军",
    ):
        raise ValueError("Seed raw identity no longer matches the reviewed source")
    if (
        len(raw.core_levels) != 7
        or tuple(item.level for item in raw.core_levels) != tuple(range(1, 8))
    ):
        raise ValueError("Seed raw record must contain Core levels 1 through 7")
    if tuple(item.level for item in raw.mindscapes) != tuple(range(1, 7)):
        raise ValueError("Seed raw record must contain Cinema levels 1 through 6")
    if config.partner_character_id == SEED_ID:
        raise ValueError("Seed cannot be its own Core partner")
    if config.partner_character_id is not None and not config.additional_ability_eligible:
        raise ValueError(
            "a resolved Core partner is another Attack agent and enables the Additional Ability"
        )


def _event_filter(entry: MoveCalculationEntry) -> EventTemplateIdFilter:
    return EventTemplateIdFilter(EventTemplateId(str(entry.main_damage_event.template_id)))


def compile_seed(
    config: SeedCompileConfig,
    raw_record: NanokaRawRecord,
) -> CharacterCalculationDefinition:
    """Compile the source's damage moves and static, user-selected current states."""

    _validate_raw_record(raw_record, config)
    entries, templates, move_diagnostics = compile_direct_moves(
        character_id=SEED_ID,
        config=config,
        raw_record=raw_record,
        reviewed_mapping=SEED_REVIEWED_MAPPING,
        id_namespace="character:1461",
    )
    entry_by_key = {
        str(item.entry_id).rsplit(":", 1)[-1]: item for item in entries
    }

    core = raw_record.core_levels[config.core_level - 1]
    core_source = _source("core-passive", EffectSourceType.CORE_PASSIVE, core.name, core.description)
    core_attack = _repeated(
        core.description,
        r"提升[^。；\n]*?(?P<value>[\d.]+)点攻击力",
        "Seed Core attack bonus",
    )
    core_crit_damage = _repeated(
        core.description,
        r"(?P<value>[\d.]+)%暴击伤害",
        "Seed Core Crit Damage bonus",
    ) / 100.0
    core_surround_bonus = _one(
        core.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Seed Core Surround Hunt damage bonus",
    ) / 100.0

    conditions: list[ScenarioCondition] = []
    partner_exists = (
        config.partner_character_id is not None or config.partner_selection_unresolved
    )
    if partner_exists:
        conditions.extend(
            (
                _condition(
                    PARTNER_EX_BUFF_ACTIVE,
                    "正兵强化特殊技后的强袭当前生效于席德",
                    "正兵释放强化特殊技后，席德的强袭当前仍生效；不回放进退场与持续时间。",
                    config.partner_ex_buff_active,
                ),
            )
        )
    conditions.append(
        _condition(
            SEED_SURROUND_HUNT_ACTIVE,
            "席德当前处于围杀状态",
            "明攻与强袭同时存在时席德获得围杀；按当前状态输入，不回放时间轴。",
            config.seed_surround_hunt_active,
        )
    )
    if partner_exists:
        conditions.extend(
            (
                _condition(
                    SEED_EX_BUFF_ACTIVE,
                    "席德强化特殊技后的明攻当前生效于正兵",
                    "席德释放强化特殊技后，正兵的明攻当前仍生效；不回放进退场与持续时间。",
                    config.seed_ex_buff_active,
                ),
                _condition(
                    PARTNER_SURROUND_HUNT_ACTIVE,
                    "正兵当前处于围杀状态",
                    "明攻与强袭状态同时存在时正兵获得围杀；按当前状态输入，不回放时间轴。",
                    config.partner_surround_hunt_active,
                ),
            )
        )

    rules: list[CalculationRuleItem] = []
    core_diagnostics: list[CalculationDiagnostic] = []
    if config.partner_selection_unresolved:
        core_diagnostics.append(
            CalculationDiagnostic(
                diagnostic_id=DiagnosticId("ambiguous:character:1461:core-partner-selection"),
                kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
                message=(
                    "Seed's Core selects the other Attack teammate with the highest Initial ATK. "
                    "The team has not resolved a unique partner from candidate Initial panels, "
                    "so recipient effects are omitted instead of guessing a character or slot."
                ),
                blocking=False,
                original_text=core.description,
            )
        )
    if partner_exists:
        seed_buff_effects = (
            _modifier(
                "core:seed-strong-assault-attack",
                core_source,
                CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                Resolved(core_attack),
                target=EffectTarget.RECIPIENT,
                recipient_character_id=SEED_ID,
            ),
            _modifier(
                "core:seed-strong-assault-crit-damage",
                core_source,
                CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                Resolved(core_crit_damage),
                target=EffectTarget.RECIPIENT,
                recipient_character_id=SEED_ID,
            ),
        )
        rules.append(
            _rule(
                "core:seed-strong-assault",
                core_source,
                f"核心被动：强袭当前生效（攻击力+{core_attack:g}、暴击伤害+{core_crit_damage:.1%}）",
                core.description,
                RuleEligibility.ELIGIBLE,
                effects=seed_buff_effects,
                condition_ids=(PARTNER_EX_BUFF_ACTIVE,),
            )
        )

    if partner_exists:
        partner = config.partner_character_id
        if partner is not None:
            partner_buff_effects = (
                _modifier(
                    "core:partner-bright-attack-attack",
                    core_source,
                    CalculationNode.CHARACTER_COMBAT_ATTACK_FLAT_BONUS,
                    Resolved(core_attack),
                    target=EffectTarget.RECIPIENT,
                    recipient_character_id=partner,
                ),
                _modifier(
                    "core:partner-bright-attack-crit-damage",
                    core_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(core_crit_damage),
                    target=EffectTarget.RECIPIENT,
                    recipient_character_id=partner,
                ),
            )
        elif config.partner_selection_unresolved:
            partner_buff_effects = tuple(
                _unresolved_partner_effect(
                    "core:partner-bright-attack-attack",
                    core_source,
                    candidate,
                    config.partner_candidate_ids,
                    original_text=core.description,
                    known_effect=f"+{core_attack:g} flat Attack",
                )
                for candidate in config.partner_candidate_ids
            ) + tuple(
                _unresolved_partner_effect(
                    "core:partner-bright-attack-crit-damage",
                    core_source,
                    candidate,
                    config.partner_candidate_ids,
                    original_text=core.description,
                    known_effect=f"+{core_crit_damage:.1%} Crit Damage",
                )
                for candidate in config.partner_candidate_ids
            )
        else:
            partner_buff_effects = ()
        rules.append(
            _rule(
                "core:partner-bright-attack",
                core_source,
                (
                    f"核心被动：明攻当前生效（正兵攻击力+{core_attack:g}、暴击伤害+{core_crit_damage:.1%}）"
                    if partner is not None
                    else "核心被动：正兵明攻（等待最高初始攻击力队友自动判定）"
                ),
                core.description,
                RuleEligibility.ELIGIBLE,
                effects=partner_buff_effects,
                condition_ids=(SEED_EX_BUFF_ACTIVE,),
                diagnostics=core_diagnostics,
            )
        )
        if partner is not None:
            partner_hunt_effects = (
                _modifier(
                    "core:partner-surround-hunt-damage",
                    core_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(core_surround_bonus),
                    target=EffectTarget.TEAM,
                    filters=(DamageDealerFilter(partner),),
                ),
            )
        elif config.partner_selection_unresolved:
            partner_hunt_effects = tuple(
                _unresolved_partner_effect(
                    "core:partner-surround-hunt-damage",
                    core_source,
                    candidate,
                    config.partner_candidate_ids,
                    original_text=core.description,
                    known_effect=f"+{core_surround_bonus:.1%} normal damage bonus",
                )
                    for candidate in config.partner_candidate_ids
                )
        else:
            partner_hunt_effects = ()
        rules.append(
            _rule(
                "core:partner-surround-hunt",
                core_source,
                (
                    f"核心被动：正兵围杀伤害+{core_surround_bonus:.1%}"
                    if partner is not None
                    else "核心被动：正兵围杀伤害（等待最高初始攻击力队友自动判定）"
                ),
                core.description,
                RuleEligibility.ELIGIBLE,
                effects=partner_hunt_effects,
                condition_ids=(PARTNER_SURROUND_HUNT_ACTIVE,),
                diagnostics=core_diagnostics,
            )
        )

    if partner_exists:
        rules.append(
            _rule(
                "core:seed-surround-hunt",
                core_source,
                f"核心被动：席德围杀伤害+{core_surround_bonus:.1%}",
                core.description,
                RuleEligibility.ELIGIBLE,
                effects=(
                    _modifier(
                        "core:seed-surround-hunt-damage",
                        core_source,
                        CalculationNode.DAMAGE_NORMAL_BONUS,
                        Resolved(core_surround_bonus),
                        target=EffectTarget.TEAM,
                        filters=(DamageDealerFilter(SEED_ID),),
                    ),
                ),
                condition_ids=(SEED_SURROUND_HUNT_ACTIVE,),
            )
        )
    else:
        rules.append(
            _rule(
                "core:passive",
                core_source,
                "核心被动：花链协议（正兵由队伍初始攻击力确定）",
                core.description,
                RuleEligibility.ELIGIBLE,
                diagnostics=core_diagnostics,
            )
        )

    extra_source = _source(
        "extra-ability",
        EffectSourceType.ADDITIONAL_ABILITY,
        core.extra_ability_name,
        core.extra_ability_description,
    )
    extra_damage_bonus = _one(
        core.extra_ability_description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Seed Additional Ability damage bonus",
    ) / 100.0
    extra_electric_resistance_ignore = _one(
        core.extra_ability_description,
        r"无视敌人(?P<value>[\d.]+)%电属性伤害抗性",
        "Seed Additional Ability Electric resistance ignore",
    ) / 100.0
    qualifying_entries = tuple(
        entry_by_key[key]
        for key in (
            "heavy-strike",
            "falling-crash-1",
            "falling-crash-2",
            "ultimate",
        )
    )
    qualifying_filter = AnyFilter(
        tuple(_event_filter(item) for item in qualifying_entries)
    )
    rules.append(
        _rule(
            "extra-ability:damage-and-electric-resistance",
            extra_source,
            f"额外能力：重戮、崩坠与终结技伤害+{extra_damage_bonus:.0%}并无视电抗{extra_electric_resistance_ignore:.0%}",
            core.extra_ability_description,
            RuleEligibility.ELIGIBLE
            if config.additional_ability_eligible
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "extra-ability:normal-damage-bonus",
                    extra_source,
                    CalculationNode.DAMAGE_NORMAL_BONUS,
                    Resolved(extra_damage_bonus),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(SEED_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        qualifying_filter,
                    ),
                ),
                _modifier(
                    "extra-ability:electric-resistance-ignore",
                    extra_source,
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE,
                    Resolved(extra_electric_resistance_ignore),
                    target=EffectTarget.TEAM,
                    filters=(
                        DamageDealerFilter(SEED_ID),
                        DamageTypeFilter(DamageType.DIRECT),
                        qualifying_filter,
                    ),
                ),
            ),
        )
    )

    cinema_rules: list[CalculationRuleItem] = []
    parameters: list[ScenarioIntegerParameter] = []
    cinema1, cinema2, cinema3, cinema4, cinema5, cinema6 = raw_record.mindscapes

    c1_source = _source("cinema-1", EffectSourceType.CINEMA, cinema1.name, cinema1.description)
    c1_crit_damage = _one(
        cinema1.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Seed Cinema 1 Falling Crash Crit Damage",
    ) / 100.0
    falling_crash_filter = AnyFilter(
        tuple(_event_filter(entry_by_key[key]) for key in ("falling-crash-1", "falling-crash-2"))
    )
    cinema_rules.append(
        _rule(
            "cinema1:falling-crash-crit-damage",
            c1_source,
            f"1影：崩坠暴击伤害+{c1_crit_damage:.0%}",
            cinema1.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 1
            else RuleEligibility.INELIGIBLE,
            effects=(
                _modifier(
                    "cinema1:falling-crash-crit-damage",
                    c1_source,
                    CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
                    Resolved(c1_crit_damage),
                    target=EffectTarget.TEAM,
                    filters=(DamageDealerFilter(SEED_ID), DamageTypeFilter(DamageType.DIRECT), falling_crash_filter),
                ),
            )
            if config.cinema_level >= 1
            else (),
        )
    )

    c2_source = _source("cinema-2", EffectSourceType.CINEMA, cinema2.name, cinema2.description)
    c2_defense_ignore = _one(
        cinema2.description,
        r"无视(?P<value>[\d.]+)%防御力",
        "Seed Cinema 2 defense ignore",
    ) / 100.0
    c2_step_energy = int(
        _one(cinema2.description, r"每消耗(?P<value>[\d.]+)点能量", "Seed Cinema 2 energy step")
    )
    c2_damage_per_step = _one(
        cinema2.description,
        r"伤害提升(?P<value>[\d.]+)%",
        "Seed Cinema 2 linked Heavy Strike damage bonus per energy step",
    ) / 100.0
    c2_energy_limits = _values(
        cinema2.description,
        r"累计消耗(?P<value>[\d.]+)点能量",
        "Seed Cinema 2 energy limits",
    )
    if len(c2_energy_limits) != 2:
        raise ValueError(
            "Seed Cinema 2 must describe both its extension threshold and energy cap"
        )
    c2_max_energy = int(max(c2_energy_limits))
    if c2_max_energy % c2_step_energy:
        raise ValueError("Seed Cinema 2 maximum energy must align to its source step")
    c2_eligible = config.cinema_level >= 2
    if c2_eligible:
        maximum_energy_intervals = c2_max_energy // c2_step_energy
        parameters.append(
            ScenarioIntegerParameter(
                parameter_id=CINEMA2_ENERGY_INTERVALS_SPENT,
                label=f"本次强化特殊技已消耗的{c2_step_energy}点能量档数",
                original_text=(
                    f"表示与本次强化特殊技衔接的重戮所对应的累计能量消耗：每满{c2_step_energy}点计1档，"
                    f"最多{c2_max_energy}点；这是当前输入，不模拟资源时间轴。"
                ),
                resolution=ParameterResolution.USER_SELECTED,
                value=config.cinema2_energy_intervals_spent,
                minimum=0,
                maximum=maximum_energy_intervals,
            )
        )
        if partner_exists:
            if config.partner_character_id is not None:
                c2_partner_effects = (
                    _modifier(
                        "cinema2:partner-defense-ignore",
                        c2_source,
                        CalculationNode.DAMAGE_DEFENSE_IGNORE,
                        Resolved(c2_defense_ignore),
                        target=EffectTarget.TEAM,
                        filters=(
                            DamageDealerFilter(config.partner_character_id),
                            DamageTypeFilter(DamageType.DIRECT),
                        ),
                    ),
                )
            elif config.partner_selection_unresolved:
                c2_partner_effects = tuple(
                    _unresolved_partner_effect(
                        "cinema2:partner-defense-ignore",
                        c2_source,
                        candidate,
                        config.partner_candidate_ids,
                        original_text=cinema2.description,
                        known_effect=(
                            f"ignore {c2_defense_ignore:.0%} DEF on Direct damage"
                        ),
                        extra_filters=(DamageTypeFilter(DamageType.DIRECT),),
                    )
                    for candidate in config.partner_candidate_ids
                )
            else:
                c2_partner_effects = ()
            cinema_rules.append(
                _rule(
                    "cinema2:partner-surround-hunt-defense-ignore",
                    c2_source,
                    (
                        f"2影：围杀中的正兵无视防御{c2_defense_ignore:.0%}"
                        if config.partner_character_id is not None
                        else "2影：正兵围杀无视防御（等待自动判定）"
                    ),
                    cinema2.description,
                    RuleEligibility.ELIGIBLE,
                    effects=c2_partner_effects,
                    condition_ids=(PARTNER_SURROUND_HUNT_ACTIVE,),
                    diagnostics=core_diagnostics,
                )
            )
        c2_seed_effect = _modifier(
            "cinema2:seed-defense-ignore",
            c2_source,
            CalculationNode.DAMAGE_DEFENSE_IGNORE,
            Resolved(c2_defense_ignore),
            target=EffectTarget.TEAM,
            filters=(DamageDealerFilter(SEED_ID), DamageTypeFilter(DamageType.DIRECT)),
        )
        cinema_rules.append(
            _rule(
                "cinema2:seed-surround-hunt-defense-ignore",
                c2_source,
                f"2影：围杀中的席德无视防御{c2_defense_ignore:.0%}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                effects=(c2_seed_effect,),
                condition_ids=(SEED_SURROUND_HUNT_ACTIVE,),
            )
        )
        c2_heavy_bonus = _modifier(
            "cinema2:linked-heavy-damage-bonus",
            c2_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            ScenarioParameterDerivedValue(
                parameter_id=str(CINEMA2_ENERGY_INTERVALS_SPENT),
                coefficient=Resolved(c2_damage_per_step),
                cap_max=Resolved(maximum_energy_intervals * c2_damage_per_step),
            ),
            target=EffectTarget.TEAM,
            filters=(DamageDealerFilter(SEED_ID), _event_filter(entry_by_key["heavy-strike"])),
        )
        cinema_rules.append(
            _rule(
                "cinema2:linked-heavy-damage-bonus",
                c2_source,
                f"2影：本次EX每{c2_step_energy}点能量使衔接重戮伤害+{c2_damage_per_step:.0%}",
                cinema2.description,
                RuleEligibility.ELIGIBLE,
                effects=(c2_heavy_bonus,),
            )
        )
    else:
        cinema_rules.append(
            _rule(
                "cinema2:damage-mechanics",
                c2_source,
                f"2影：围杀无视防御{c2_defense_ignore:.0%}；EX能量消耗增强衔接重戮",
                cinema2.description,
                RuleEligibility.INELIGIBLE,
            )
        )

    for cinema in (cinema3, cinema5):
        cinema_rules.append(
            _rule(
                f"cinema{cinema.level}:skill-levels",
                _source(f"cinema-{cinema.level}", EffectSourceType.CINEMA, cinema.name, cinema.description),
                f"{cinema.level}影：技能等级提升（含终结技）",
                cinema.description,
                RuleEligibility.ELIGIBLE
                if config.cinema_level >= cinema.level
                else RuleEligibility.INELIGIBLE,
            )
        )

    c4_source = _source("cinema-4", EffectSourceType.CINEMA, cinema4.name, cinema4.description)
    c4_ultimate_bonus = _one(
        cinema4.description,
        r"造成的伤害提升(?P<value>[\d.]+)%",
        "Seed Cinema 4 Ultimate damage bonus",
    ) / 100.0
    c4_effects = (
        _modifier(
            "cinema4:ultimate-damage-bonus",
            c4_source,
            CalculationNode.DAMAGE_NORMAL_BONUS,
            Resolved(c4_ultimate_bonus),
            target=EffectTarget.TEAM,
            filters=(DamageDealerFilter(SEED_ID), _event_filter(entry_by_key["ultimate"])),
        ),
    )
    cinema_rules.append(
        _rule(
            "cinema4:surround-hunt-ultimate-damage",
            c4_source,
            f"4影：席德围杀当前生效时终结技伤害+{c4_ultimate_bonus:.0%}",
            cinema4.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 4
            else RuleEligibility.INELIGIBLE,
            effects=c4_effects if config.cinema_level >= 4 else (),
            condition_ids=(SEED_SURROUND_HUNT_ACTIVE,),
        )
    )

    c6_source = _source("cinema-6", EffectSourceType.CINEMA, cinema6.name, cinema6.description)
    c6_crit_damage = _one(
        cinema6.description,
        r"暴击伤害提升(?P<value>[\d.]+)%",
        "Seed Cinema 6 Crit Damage",
    ) / 100.0
    c6_crit_effects = (
        _modifier(
            "cinema6:self-crit-damage",
            c6_source,
            CalculationNode.CHARACTER_CURRENT_CRIT_DAMAGE,
            Resolved(c6_crit_damage),
            target=EffectTarget.SELF,
        ),
    )
    cinema_rules.append(
        _rule(
            "cinema6:self-crit-damage",
            c6_source,
            f"6影：席德暴击伤害+{c6_crit_damage:.0%}",
            cinema6.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=c6_crit_effects if config.cinema_level >= 6 else (),
        )
    )

    laser_event_unresolved = Unresolved(
        reason=UnresolvedReason.AMBIGUOUS_IDENTITY,
        notes=(
            "Cinema 6 gives the extra laser trigger (Heavy Strike), count (3), and ratio "
            "(165% ATK each), but does not identify the child event's element, damage tag, "
            "or independent move identity. Preserve the known 3 × 165% source inputs and "
            "leave only that child unresolved; do not fabricate a Direct event classification."
        ),
        original_text=cinema6.description,
    )
    laser_diagnostic = CalculationDiagnostic(
        diagnostic_id=DiagnosticId("ambiguous:character:1461:cinema6-laser-event-identity"),
        kind=DiagnosticKind.AMBIGUOUS_SEMANTICS,
        message=(
            "The current heavy-strike event remains calculated. The C6 laser child preserves "
            "its source count and multiplier but lacks source-defined event identity, element, "
            "and tag, so it remains local-unresolved."
        ),
        blocking=False,
        original_text=cinema6.description,
    )
    conditions.append(
        _condition(
            CINEMA6_LASER_PROC_ACTIVE,
            "本次重戮满足6影激光3秒触发间隔",
            "按当前查询选择该次重戮是否触发6影激光；不推演3秒冷却。",
            config.cinema6_laser_proc_active,
        )
    )
    laser_trigger_rule = EffectRule(
        effect_id=EffectId("effect:character:1461:cinema6:laser-followup"),
        source=c6_source,
        owner=SEED_ID,
        target=EffectTarget.TEAM,
        snapshot_rule=SnapshotRule.SETTLEMENT,
        filters=(
            DamageDealerFilter(SEED_ID),
            _event_filter(entry_by_key["heavy-strike"]),
        ),
    )
    cinema_rules.append(
        _rule(
            "cinema6:heavy-strike-laser-child",
            c6_source,
            "6影：重戮额外3道激光（每道165%攻击力；事件分类待源明确）",
            cinema6.description,
            RuleEligibility.ELIGIBLE
            if config.cinema_level >= 6
            else RuleEligibility.INELIGIBLE,
            effects=(
                EventCreationEffect(
                    rule=laser_trigger_rule,
                    result=EventCreationResult(
                        event_kind=BattleEventKind.DAMAGE,
                        unresolved_template=laser_event_unresolved,
                        unique_per_source_event=True,
                    ),
                ),
            )
            if config.cinema_level >= 6
            else (),
            condition_ids=(CINEMA6_LASER_PROC_ACTIVE,),
            diagnostics=(laser_diagnostic,) if config.cinema_level >= 6 else (),
        )
    )

    diagnostics = list(move_diagnostics)
    if core_diagnostics:
        diagnostics.extend(core_diagnostics)
    return build_definition(
        character_id=SEED_ID,
        role=CharacterRole.ATTACK,
        element=Element.ELECTRIC,
        source=_source(
            "live-source",
            EffectSourceType.SKILL,
            raw_record.name,
            f"Nanoka {raw_record.source_version}: {raw_record.source_url}",
        ),
        entries=entries,
        templates=templates,
        rules=(*rules, *cinema_rules),
        conditions=conditions,
        parameters=parameters,
        diagnostics=diagnostics,
    )


def load_raw_record(data) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(SEED_ID))


__all__ = ["compile_seed", "load_raw_record"]
