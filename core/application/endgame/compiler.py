"""Compile reviewed field clauses into the ordinary rule/effect pipeline."""
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from core.application.element_scope import element_scope_filter
from core.application.ids import RuleItemId, ScenarioConditionId
from core.application.rules import CalculationRuleItem, RuleEligibility
from core.application.scenario import ConditionResolution, ScenarioCondition
from core.types import (AnyFilter, CalculationNode as N, CharacterId, DamageTag, DamageTagFilter,
    DamageType, DamageTypeFilter, DamageSubtype, DamageSubtypeFilter, EffectId, EffectRule,
    EffectOperation, EffectSourceType, EffectTarget, Element, EnemyStateFilter, NotFilter,
    ModifierEffect, ModifierResult, Resolved, RuleSource, RuleSourceId, SnapshotRule, StateId,
    Unresolved, UnresolvedEffect, UnresolvedReason)
from .reviewed import REVIEWED, Clause

NODES = {
    'bonus': N.DAMAGE_NORMAL_BONUS, 'atk': N.CHARACTER_COMBAT_ATTACK_PERCENT_BONUS,
    'hp': N.CHARACTER_COMBAT_HP_PERCENT_BONUS, 'def': N.CHARACTER_COMBAT_DEFENSE_PERCENT_BONUS,
    'impact': N.CHARACTER_COMBAT_IMPACT_PERCENT_BONUS, 'ap': N.CHARACTER_COMBAT_ANOMALY_PROFICIENCY_FLAT_BONUS,
    'cd': N.CHARACTER_CURRENT_CRIT_DAMAGE, 'cr': N.CHARACTER_CURRENT_CRIT_RATE,
    'pen-rate': N.CHARACTER_CURRENT_PENETRATION_RATE, 'sheer': N.PENETRATION_DAMAGE_BONUS,
    'discharge': N.DISCHARGE_DAMAGE_BONUS, 'turbulence': N.TURBULENCE_DAMAGE_BONUS,
    'disorder': N.DISORDER_TRIGGER_DAMAGE_BONUS, 'def-reduction': N.ENEMY_DEFENSE_REDUCTION,
    'res-reduction': N.ENEMY_RESISTANCE_REDUCTION, 'ignore-def': N.DAMAGE_DEFENSE_IGNORE,
    'ignore-res': N.DAMAGE_RESISTANCE_IGNORE, 'anom-ignore-res': N.DAMAGE_RESISTANCE_IGNORE,
    'discharge-ignore-res': N.DAMAGE_RESISTANCE_IGNORE, 'stun': N.ENEMY_STUN_VULNERABILITY,
    'received-anom': N.ENEMY_NORMAL_VULNERABILITY, 'received-discharge': N.ENEMY_NORMAL_VULNERABILITY,
    'received': N.ENEMY_NORMAL_VULNERABILITY,
    'enemy-def-increase': N.ENEMY_DEFENSE_INCREASE,
    'received-turbulence': N.ENEMY_NORMAL_VULNERABILITY,
    'anom-ignore-def': N.DAMAGE_DEFENSE_IGNORE,
}
PANEL_KINDS = {'atk', 'hp', 'def', 'impact', 'ap', 'cd', 'cr', 'pen-rate'}
TAGS = {'basic': DamageTag.BASIC_ATTACK, 'dash': DamageTag.DASH_ATTACK,
    'special': DamageTag.SPECIAL_ATTACK, 'ex': DamageTag.EX_SPECIAL_ATTACK,
    'chain': DamageTag.CHAIN_ATTACK, 'ultimate': DamageTag.ULTIMATE,
    'follow-up': DamageTag.FOLLOW_UP_ATTACK, 'counter': DamageTag.DODGE_COUNTER, 'assist': DamageTag.ASSIST}
LABELS = {'bonus':'伤害加成','atk':'攻击力','hp':'生命值','def':'防御力','impact':'冲击力','ap':'异常精通',
    'cd':'暴击伤害','cr':'暴击率','pen-rate':'穿透率','sheer':'贯穿伤害','discharge':'异放伤害',
    'turbulence':'乱流伤害','disorder':'紊乱伤害','def-reduction':'防御降低','res-reduction':'抗性降低',
    'ignore-def':'无视防御','ignore-res':'无视抗性','anom-ignore-res':'异常无视抗性',
    'anom-ignore-def':'异常无视防御','discharge-ignore-res':'异放无视抗性','stun':'失衡易伤',
    'received-anom':'受到的异常伤害','received-discharge':'受到的异放伤害','received-turbulence':'受到的乱流伤害',
    'received':'受到的伤害','enemy-def-increase':'敌人防御提高','anom':'异常伤害','sharp':'锐化条款',
    'unknown':'未决条款','unknown-anom':'异常未决条款','unknown-crit':'暴击未决条款'}


@lru_cache(maxsize=1)
def evidence():
    return json.loads(Path(__file__).with_name('reviewed-evidence.json').read_text(encoding='utf-8'))


@dataclass(frozen=True)
class CompiledEndgame:
    rules: tuple[CalculationRuleItem, ...]
    conditions: tuple[ScenarioCondition, ...]
    controls: tuple[dict, ...]
    clauses: tuple[dict, ...]


def compile_endgame(context: dict, buffs: list[dict], definitions: tuple, states: dict) -> CompiledEndgame:
    rules, conditions, controls, clauses = [], [], {}, []
    prefix = f"endgame:{context['mode']}:{context['season_id']}:{context['stage_id']}:{context['room_id']}"
    if states.get('buff:69013903:残翳层数', 0) and states.get('buff:69013903:裂伤层数', 0):
        raise ValueError('残翳与裂伤不能同时存在；进入失衡后残翳转换为裂伤')
    for buff in buffs:
        bid = buff['buff_id']
        source = RuleSource(RuleSourceId(f'{prefix}:buff:{bid}'), EffectSourceType.ENVIRONMENT,
            f"{context['mode_label']} {context['season_id']} · {buff['title']}", buff['text'])
        mapping = REVIEWED.get(bid, (Clause('unknown', 0, note='该历史条款尚未确认正式乘区；已保留原文并标记不完整'),))
        if evidence().get(bid, {}).get('sha256') != hashlib.sha256(buff['text'].encode()).hexdigest():
            mapping = (Clause('unknown', 0, note='条款文本与已审核证据不一致，需要重新审核'),)
        if not mapping:
            clauses.append({'buff_id': bid, 'status': 'out_of_scope', 'message': '计分、资源或战斗过程条款，不改变本次静态伤害'})
        for index, clause in enumerate(mapping):
            candidates = [d for d in definitions if not clause.roles or d.role.value in clause.roles]
            personal_recipients = candidates if clause.personal or clause.kind in PANEL_KINDS and not (clause.elements or clause.tags or clause.enemy_state) else [None]
            for recipient in personal_recipients:
                owner_suffix = f':recipient:{recipient.character_id}' if recipient else ''
                rid = RuleItemId(f'rule:{prefix}:buff:{bid}:clause:{index}{owner_suffix}')
                state_key = f'buff:{bid}:{clause.state}' + (f':{recipient.character_id}' if clause.personal and recipient else '')
                condition_ids = ()
                count = 1
                if clause.state:
                    maximum = clause.maximum
                    controls[state_key] = {'key': state_key, 'label': clause.state + (f' · {recipient.source.label}' if clause.personal and recipient else ''), 'maximum': maximum, 'value': states.get(state_key, 0)}
                    value = states.get(state_key, 0)
                    if type(value) is not int or not 0 <= value <= maximum:
                        raise ValueError(f'终局状态范围为 0–{maximum}: {state_key}')
                    count = value if maximum > 1 else 1
                    condition_id = ScenarioConditionId(f'condition:{prefix}:{state_key}')
                    condition_ids = (condition_id,)
                    if not any(c.condition_id == condition_id for c in conditions):
                        conditions.append(ScenarioCondition(condition_id, clause.state, buff['text'], ConditionResolution.USER_SELECTED, value > 0))
                filters = []
                if clause.elements:
                    filters.append(AnyFilter(tuple(element_scope_filter(Element(e)) for e in clause.elements)))
                if clause.tags:
                    filters.append(AnyFilter(tuple(DamageTagFilter(TAGS[t]) for t in clause.tags)))
                if clause.roles and not recipient:
                    from core.types import DamageDealerFilter
                    filters.append(AnyFilter(tuple(DamageDealerFilter(d.character_id) for d in candidates)))
                if clause.enemy_state:
                    f = EnemyStateFilter(StateId('state:enemy:stunned'))
                    filters.append(NotFilter(f) if clause.enemy_state == 'not-stunned' else f)
                if clause.kind in {'sheer', 'unknown-crit'}:
                    filters.append(AnyFilter(tuple(DamageTypeFilter(t) for t in ((DamageType.DIRECT, DamageType.PENETRATION) if clause.kind == 'unknown-crit' else (DamageType.PENETRATION,)))))
                if clause.kind in {'discharge', 'received-discharge', 'discharge-ignore-res'}:
                    filters.append(DamageSubtypeFilter(DamageSubtype.DISCHARGE))
                if clause.kind == 'turbulence':
                    filters.append(DamageSubtypeFilter(DamageSubtype.TURBULENCE))
                if clause.kind == 'received-turbulence':
                    filters.append(DamageSubtypeFilter(DamageSubtype.TURBULENCE))
                if clause.kind == 'unknown-anom':
                    filters.append(AnyFilter((DamageTypeFilter(DamageType.ANOMALY), DamageTypeFilter(DamageType.DISORDER))))
                if clause.kind in {'received-anom', 'anom-ignore-res', 'anom-ignore-def'}:
                    filters.append(DamageTypeFilter(DamageType.ANOMALY))
                if clause.kind == 'sharp':
                    filters.append(DamageTypeFilter(DamageType.SHARP_EXPLOSION))
                if clause.kind == 'disorder':
                    filters.append(DamageTypeFilter(DamageType.DISORDER))
                target = EffectTarget.RECIPIENT if recipient else EffectTarget.ENEMY if clause.kind in {'def-reduction', 'enemy-def-increase', 'res-reduction', 'stun', 'received-anom', 'received-discharge', 'received-turbulence', 'received'} else EffectTarget.TEAM
                rule = EffectRule(EffectId(f'effect:{rid}'), source, target=target, owner=None,
                    recipient_character_id=recipient.character_id if recipient else None, snapshot_rule=SnapshotRule.LIVE, filters=tuple(filters))
                value = clause.value
                if clause.state_values:
                    value = clause.state_values[states.get(state_key, 0)]
                    count = 1
                if clause.team_count:
                    role, min1, value1, min2, value2 = clause.team_count
                    team_count = sum(d.role.value == role for d in definitions)
                    value = value2 if team_count >= min2 else value1 if team_count >= min1 else 0
                unresolved = clause.kind.startswith('unknown') or clause.kind == 'sharp' or clause.note is not None
                if unresolved:
                    effects = (UnresolvedEffect(rule, Unresolved(UnresolvedReason.MISSING_DATA,
                        notes=clause.note or '锐化/锐暴伤害类型尚未实装，不映射为贯穿伤害')),)
                elif clause.kind == 'anom':
                    # Attribute anomaly, its inherited record bonus, and Luminance use distinct nodes.
                    effects = tuple(ModifierEffect(
                        EffectRule(EffectId(f'effect:{rid}:{node.value}'), source, target=target, owner=None,
                            recipient_character_id=recipient.character_id if recipient else None,
                            snapshot_rule=SnapshotRule.LIVE, filters=tuple(filters) + ((DamageSubtypeFilter(DamageSubtype.LUMINANCE),) if node is N.LUMINANCE_ANOMALY_DAMAGE_BONUS else (DamageTypeFilter(DamageType.ANOMALY), NotFilter(DamageSubtypeFilter(DamageSubtype.LUMINANCE))))),
                        ModifierResult(node, EffectOperation.ADD, Resolved(value)))
                        for node in (N.ANOMALY_DAMAGE_BONUS, N.LUMINANCE_ANOMALY_DAMAGE_BONUS))
                else:
                    effects = (ModifierEffect(rule, ModifierResult(NODES[clause.kind], EffectOperation.ADD, Resolved(value))),)
                rules.append(CalculationRuleItem(rid, None, source, f"{buff['title']} · {LABELS[clause.kind]}" + (f' · {recipient.source.label}' if recipient else ''),
                    buff['text'], RuleEligibility.SCENARIO_REQUIRED if condition_ids else RuleEligibility.ELIGIBLE,
                    condition_ids=condition_ids, effects=effects,
                    stack_count=count if clause.maximum > 1 and not clause.state_values else None,
                    stack_min=0 if clause.maximum > 1 and not clause.state_values else None, stack_max=clause.maximum if clause.maximum > 1 and not clause.state_values else None))
                clauses.append({'rule_id': str(rid), 'buff_id': bid, 'status': 'unresolved' if unresolved else 'implemented',
                    'message': clause.note or ('锐化/锐暴类型尚未纳入内核' if clause.kind == 'sharp' else LABELS[clause.kind])})
    unknown_states = set(states) - set(controls)
    if unknown_states:
        raise ValueError(f'终局状态不属于当前场地或队伍: {sorted(unknown_states)}')
    return CompiledEndgame(tuple(rules), tuple(conditions), tuple(controls.values()), tuple(clauses))
