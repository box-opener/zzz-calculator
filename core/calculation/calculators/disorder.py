"""Disorder damage from one explicitly settled anomaly record."""

from __future__ import annotations

import math
from dataclasses import replace

from core.types import (
    ANOMALY_DAMAGE_KIND_BY_ELEMENT,
    ANOMALY_STATE_KIND_BY_ELEMENT,
    BASE_ELEMENT_BY_ELEMENT,
    AnomalyRecord,
    AnomalyRecordId,
    CalculationContext,
    CalculationNode,
    CalculationNodeMultiplier,
    CharacterId,
    CharacterSnapshot,
    DisorderDamageEvent,
    PolarDisorderDamageEvent,
    Element,
    EffectId,
    EffectOperation,
    FixedMultiplier,
    Modifier,
    NoCritRule,
    NoAnomalyCrit,
    Resolvable,
    Resolved,
    SnapshotRule,
    Unresolved,
    UnresolvedReason,
)

from ..nodes import CalculationNodeValue
from ..regions import (
    BroadVulnerabilityRegionInput,
    DefenseRegionInput,
    DisorderDamageBonusRegionInput,
    ResistanceRegionInput,
    calculate_broad_vulnerability_region,
    calculate_defense_region,
    calculate_disorder_damage_bonus_region,
    calculate_resistance_region,
)
from ..result import CalculationResult
from .errors import InvalidCalculationContextError


_SUPPORTED_MODIFIER_PATHS = frozenset(
    {
        CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS,
        CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS,
        CalculationNode.DISORDER_EXTRA_MULTIPLIER,
        CalculationNode.POLAR_DISORDER_MULTIPLIER,
        CalculationNode.ENEMY_DEFENSE_INCREASE,
        CalculationNode.ENEMY_DEFENSE_REDUCTION,
        CalculationNode.DAMAGE_DEFENSE_IGNORE,
        CalculationNode.DAMAGE_PENETRATION_RATE,
        CalculationNode.DAMAGE_PENETRATION_FLAT,
        CalculationNode.DAMAGE_RESISTANCE_IGNORE,
        CalculationNode.ENEMY_RESISTANCE_REDUCTION,
        CalculationNode.ENEMY_STUN_VULNERABILITY,
        CalculationNode.ENEMY_NORMAL_VULNERABILITY,
        CalculationNode.ENEMY_MOVE_VULNERABILITY,
        CalculationNode.ENEMY_DAMAGE_REDUCTION,
    }
)


def _node(node: CalculationNode, value: float) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=Resolved(value),
        read_rule=SnapshotRule.SETTLEMENT,
    )


def _snapshot_index(
    snapshots: tuple[CharacterSnapshot, ...],
) -> dict[CharacterId, CharacterSnapshot]:
    index: dict[CharacterId, CharacterSnapshot] = {}
    for snapshot in snapshots:
        if snapshot.character_id in index:
            raise InvalidCalculationContextError(
                f"duplicate character snapshot: {snapshot.character_id}"
            )
        index[snapshot.character_id] = snapshot
    return index


def _required_snapshot(
    snapshots: dict[CharacterId, CharacterSnapshot],
    character_id: CharacterId,
) -> CharacterSnapshot:
    try:
        return snapshots[character_id]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing damage dealer character snapshot: {character_id}"
        ) from error


def _record_index(
    records: tuple[AnomalyRecord, ...],
) -> dict[AnomalyRecordId, AnomalyRecord]:
    index: dict[AnomalyRecordId, AnomalyRecord] = {}
    for record in records:
        if record.record_id in index:
            raise InvalidCalculationContextError(
                f"duplicate anomaly record: {record.record_id}"
            )
        index[record.record_id] = record
    return index


def _required_record(
    records: dict[AnomalyRecordId, AnomalyRecord],
    record_id: AnomalyRecordId,
) -> AnomalyRecord:
    try:
        return records[record_id]
    except KeyError as error:
        raise InvalidCalculationContextError(
            f"missing anomaly record: {record_id}"
        ) from error


def _resolved_number(
    value: Resolvable[float],
    unresolved: list[Unresolved],
) -> float | None:
    if isinstance(value, Resolved):
        return value.value
    unresolved.append(value)
    return None


def _unsupported_modifier(modifier: Modifier) -> Unresolved:
    return Unresolved(
        reason=UnresolvedReason.MISSING_SPEC_RULE,
        notes=(
            f"DisorderDamageCalculator does not support {modifier.operation.value} "
            f"for {modifier.modifier_path.value} from {modifier.effect_id}"
        ),
    )


def _reject_duplicate_disorder_attribution(
    modifiers: tuple[Modifier, ...],
) -> None:
    trigger_effects: set[EffectId] = set()
    contributor_effects: set[EffectId] = set()
    for modifier in modifiers:
        if modifier.modifier_path is CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS:
            trigger_effects.add(modifier.effect_id)
        elif (
            modifier.modifier_path
            is CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS
        ):
            contributor_effects.add(modifier.effect_id)
    duplicate_effects = trigger_effects & contributor_effects
    if duplicate_effects:
        duplicate_list = ", ".join(sorted(str(effect) for effect in duplicate_effects))
        raise InvalidCalculationContextError(
            "same disorder modifier effect cannot be attributed to both identities: "
            f"{duplicate_list}"
        )


def _modifier_totals(
    context: CalculationContext,
    unresolved: list[Unresolved],
) -> dict[CalculationNode, float]:
    _reject_duplicate_disorder_attribution(context.modifiers)
    totals = {node: 0.0 for node in _SUPPORTED_MODIFIER_PATHS}
    for modifier in context.modifiers:
        if modifier.modifier_path not in _SUPPORTED_MODIFIER_PATHS:
            continue
        if modifier.operation is not EffectOperation.ADD:
            unresolved.append(_unsupported_modifier(modifier))
            continue
        value = _resolved_number(modifier.value, unresolved)
        if value is not None:
            totals[modifier.modifier_path] += value
    return totals


class DisorderDamageCalculator:
    """Calculate disorder damage only; disorder daze is a separate result."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, DisorderDamageEvent):
            raise InvalidCalculationContextError(
                "DisorderDamageCalculator only accepts DisorderDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )

        records = _record_index(context.history_records)
        record = _required_record(records, event.history_record_source)
        if record.target_enemy != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "anomaly record target does not match DamageEvent target"
            )
        if record.element != event.metadata.element:
            raise InvalidCalculationContextError(
                "anomaly record element does not match DamageEvent element"
            )

        snapshots = _snapshot_index(context.character_snapshots)
        damage_dealer = _required_snapshot(
            snapshots,
            event.metadata.damage_dealer,
        )
        unresolved: list[Unresolved] = []
        if isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
        elif not isinstance(event.crit_rule, NoCritRule):
            raise InvalidCalculationContextError(
                "disorder damage must use NoCritRule"
            )

        anomaly_effect_strength = _resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        if isinstance(event.multiplier, FixedMultiplier):
            disorder_multiplier = _resolved_number(event.multiplier.value, unresolved)
        elif isinstance(event.multiplier, CalculationNodeMultiplier):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_SPEC_RULE,
                    notes=(
                        "DisorderDamageCalculator only supports FixedMultiplier; "
                        f"received node {event.multiplier.node.value}"
                    ),
                )
            )
            disorder_multiplier = None
        else:
            unresolved.append(event.multiplier)
            disorder_multiplier = None

        penetration_rate = _resolved_number(
            damage_dealer.settlement_stats.penetration_rate,
            unresolved,
        )
        penetration_flat = _resolved_number(
            damage_dealer.settlement_stats.penetration_flat,
            unresolved,
        )
        initial_defense = _resolved_number(
            context.target_snapshot.initial_defense,
            unresolved,
        )
        damage_reduction = _resolved_number(
            context.target_snapshot.damage_reduction,
            unresolved,
        )
        base_element = BASE_ELEMENT_BY_ELEMENT[event.metadata.element]
        base_resistance = _resolved_number(
            context.target_snapshot.damage_resistance.get(
                base_element,
                Resolved(0.0),
            ),
            unresolved,
        )
        modifiers = _modifier_totals(context, unresolved)

        required_values = (
            anomaly_effect_strength,
            disorder_multiplier,
            penetration_rate,
            penetration_flat,
            initial_defense,
            damage_reduction,
            base_resistance,
        )
        if unresolved or any(value is None for value in required_values):
            return CalculationResult(
                value=None,
                breakdown=(),
                unresolved=tuple(unresolved),
                anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
                anomaly_record_id=str(record.record_id),
            )

        assert anomaly_effect_strength is not None
        assert disorder_multiplier is not None
        assert penetration_rate is not None
        assert penetration_flat is not None
        assert initial_defense is not None
        assert damage_reduction is not None
        assert base_resistance is not None

        total_multiplier = disorder_multiplier + modifiers[
            CalculationNode.DISORDER_EXTRA_MULTIPLIER
        ]
        base_damage = anomaly_effect_strength * total_multiplier
        disorder_bonus = calculate_disorder_damage_bonus_region(
            DisorderDamageBonusRegionInput(
                trigger_damage_bonus=modifiers[
                    CalculationNode.DISORDER_TRIGGER_DAMAGE_BONUS
                ],
                settled_contributor_damage_bonus=modifiers[
                    CalculationNode.DISORDER_SETTLED_CONTRIBUTOR_DAMAGE_BONUS
                ],
            )
        )
        defense = calculate_defense_region(
            DefenseRegionInput(
                attacker_level=damage_dealer.level,
                initial_defense=initial_defense,
                defense_increase=modifiers[
                    CalculationNode.ENEMY_DEFENSE_INCREASE
                ],
                defense_reduction=modifiers[
                    CalculationNode.ENEMY_DEFENSE_REDUCTION
                ],
                defense_ignore=modifiers[CalculationNode.DAMAGE_DEFENSE_IGNORE],
                penetration_rate=(
                    penetration_rate
                    + modifiers[CalculationNode.DAMAGE_PENETRATION_RATE]
                ),
                penetration_flat=(
                    penetration_flat
                    + modifiers[CalculationNode.DAMAGE_PENETRATION_FLAT]
                ),
            )
        )
        resistance = calculate_resistance_region(
            ResistanceRegionInput(
                base_resistance=base_resistance,
                resistance_ignore=modifiers[
                    CalculationNode.DAMAGE_RESISTANCE_IGNORE
                ],
                resistance_reduction=modifiers[
                    CalculationNode.ENEMY_RESISTANCE_REDUCTION
                ],
            )
        )
        vulnerability = calculate_broad_vulnerability_region(
            BroadVulnerabilityRegionInput(
                is_stunned=context.target_snapshot.is_stunned,
                stun_vulnerability=modifiers[
                    CalculationNode.ENEMY_STUN_VULNERABILITY
                ],
                normal_vulnerability=modifiers[
                    CalculationNode.ENEMY_NORMAL_VULNERABILITY
                ],
                move_vulnerability=modifiers[
                    CalculationNode.ENEMY_MOVE_VULNERABILITY
                ],
                damage_reduction=(
                    damage_reduction
                    + modifiers[CalculationNode.ENEMY_DAMAGE_REDUCTION]
                ),
                settlement_policy=context.vulnerability_policy,
            )
        )
        final_damage = (
            base_damage
            * disorder_bonus.value
            * defense.value
            * resistance.value
            * vulnerability.value
        )
        assert final_damage is not None
        base_breakdown = (
            _node(
                CalculationNode.ANOMALY_EFFECT_STRENGTH,
                anomaly_effect_strength,
            ),
            _node(CalculationNode.DISORDER_TOTAL_MULTIPLIER, total_multiplier),
            _node(CalculationNode.DAMAGE_BASE_VALUE, base_damage),
        )
        return CalculationResult(
            value=final_damage,
            breakdown=(
                *base_breakdown,
                *disorder_bonus.breakdown,
                *defense.breakdown,
                *resistance.breakdown,
                *vulnerability.breakdown,
            ),
            unresolved=(
                *disorder_bonus.unresolved,
                *defense.unresolved,
                *resistance.unresolved,
                *vulnerability.unresolved,
            ),
            anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
            anomaly_record_id=str(record.record_id),
        )


def _polar_time_compensation(element, duration, unresolved: list[Unresolved]) -> float | None:
    if element is Element.WIND:
        return 0.0
    seconds = _resolved_number(duration, unresolved)
    if seconds is None:
        return None
    seconds = max(float(seconds), 0.0)
    ticks = math.floor(seconds + 1e-9)
    if element in {Element.PHYSICAL, Element.LINREN, Element.ICE}:
        return ticks * 0.075
    if element is Element.LIESHUANG:
        return ticks * 0.75
    if element is Element.FIRE:
        return math.floor(seconds / 0.5 + 1e-9) * 0.50
    if element is Element.ELECTRIC:
        return ticks * 1.25
    if element in {Element.ETHER, Element.XUANMO}:
        return math.floor(seconds / 0.5 + 1e-9) * 0.625
    unresolved.append(
        Unresolved(
            reason=UnresolvedReason.MISSING_SPEC_RULE,
            notes=f"No Polar Disorder time rule is defined for {element.value}.",
        )
    )
    return None


class PolarDisorderDamageCalculator:
    """Calculate Yanagi's confirmed additive Polar Disorder base."""

    def calculate(self, context: CalculationContext) -> CalculationResult:
        event = context.event
        if not isinstance(event, PolarDisorderDamageEvent):
            raise InvalidCalculationContextError(
                "PolarDisorderDamageCalculator only accepts PolarDisorderDamageEvent"
            )
        if context.battle_state_id != event.metadata.battle_state_id:
            raise InvalidCalculationContextError(
                "CalculationContext battle_state_id does not match DamageEvent"
            )
        if context.target_snapshot.enemy_id != event.metadata.target_enemy:
            raise InvalidCalculationContextError(
                "target snapshot does not match DamageEvent target"
            )

        records = _record_index(context.history_records)
        record = records.get(event.history_record_source)
        unresolved: list[Unresolved] = []
        if record is None:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes=(
                        "The selected anomaly source record is missing; the inherited "
                        "Polar Disorder base cannot be resolved."
                    ),
                )
            )
            record = AnomalyRecord(
                record_id=event.history_record_source,
                target_enemy=event.metadata.target_enemy,
                element=event.metadata.element,
                damage_kind=ANOMALY_DAMAGE_KIND_BY_ELEMENT[event.metadata.element],
                state_kind=ANOMALY_STATE_KIND_BY_ELEMENT[event.metadata.element],
                weighted_anomaly_effect_strength=Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="selected anomaly record strength is missing",
                ),
                weighted_impact_strength=Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="selected anomaly record impact is missing",
                ),
                anomaly_damage_bonus_region=Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="selected anomaly record provenance is missing",
                ),
                contributors=(event.source_anomaly_character_id,),
                anomaly_triggerer=event.source_anomaly_character_id,
                crit_capability=NoAnomalyCrit(),
                triggered_at=event.metadata.created_at,
                duration=Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="selected anomaly record duration is missing",
                ),
            )
        else:
            if record.target_enemy != event.metadata.target_enemy:
                raise InvalidCalculationContextError(
                    "anomaly record target does not match Polar Disorder target"
                )
            if record.element != event.metadata.element:
                raise InvalidCalculationContextError(
                    "anomaly record element does not match Polar Disorder element"
                )
            if (
                record.anomaly_triggerer != event.source_anomaly_character_id
                or event.source_anomaly_character_id not in record.contributors
            ):
                raise InvalidCalculationContextError(
                    "selected Polar anomaly record actor does not match its source identity"
                )

        snapshots = _snapshot_index(context.character_snapshots)
        damage_dealer = _required_snapshot(snapshots, event.metadata.damage_dealer)
        if isinstance(event.crit_rule, Unresolved):
            unresolved.append(event.crit_rule)
        elif not isinstance(event.crit_rule, NoCritRule):
            raise InvalidCalculationContextError(
                "Polar Disorder damage must use NoCritRule"
            )

        source_strength = _resolved_number(
            record.weighted_anomaly_effect_strength,
            unresolved,
        )
        time_compensation = _polar_time_compensation(
            event.metadata.element,
            record.duration,
            unresolved,
        )
        anomaly_proficiency = _resolved_number(
            damage_dealer.settlement_stats.anomaly_proficiency,
            unresolved,
        )
        modifiers = _modifier_totals(context, unresolved)
        if isinstance(event.polarity_multiplier, bool) or not math.isfinite(
            float(event.polarity_multiplier)
        ):
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="Polar Disorder multiplier is not a finite number.",
                )
            )
        base_multiplier = 4.5
        core_extra = modifiers[CalculationNode.DISORDER_EXTRA_MULTIPLIER]
        polarity_multiplier = event.polarity_multiplier + modifiers[
            CalculationNode.POLAR_DISORDER_MULTIPLIER
        ]

        inherited_base: float | None = None
        unresolved_pre_modifier = any(
            modifier.modifier_path
            in {
                CalculationNode.DISORDER_EXTRA_MULTIPLIER,
                CalculationNode.POLAR_DISORDER_MULTIPLIER,
            }
            and not isinstance(modifier.value, Resolved)
            for modifier in context.modifiers
        )
        if (
            source_strength is not None
            and time_compensation is not None
            and not unresolved_pre_modifier
        ):
            inherited_base = source_strength * (
                base_multiplier + time_compensation + core_extra
            ) * polarity_multiplier
        else:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes=(
                        "The inherited Polar Disorder component is unresolved because "
                        "the selected record strength or duration is unavailable."
                    ),
                )
            )
        ap_addition = (
            event.anomaly_proficiency_coefficient * anomaly_proficiency
            if anomaly_proficiency is not None
            else None
        )
        if ap_addition is None:
            unresolved.append(
                Unresolved(
                    reason=UnresolvedReason.MISSING_DATA,
                    notes="Yanagi's current Anomaly Proficiency is unavailable.",
                )
            )

        known_base = (inherited_base or 0.0) + (ap_addition or 0.0)
        if inherited_base is None and ap_addition is None:
            return CalculationResult(
                value=None,
                breakdown=(
                    _node(CalculationNode.DISORDER_BASE_MULTIPLIER, base_multiplier),
                    _node(
                        CalculationNode.POLAR_DISORDER_MULTIPLIER,
                        polarity_multiplier,
                    ),
                ),
                unresolved=tuple(unresolved),
                anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
                anomaly_record_id=str(record.record_id),
            )

        # Feed the already-combined pre-defense base through the ordinary
        # Disorder regions once. The core Disorder multiplier has already been
        # applied to the inherited component and must not multiply the AP term.
        post_record = replace(
            record,
            weighted_anomaly_effect_strength=Resolved(known_base),
        )
        post_event = DisorderDamageEvent(
            metadata=event.metadata,
            disorder_triggerer=event.disorder_triggerer,
            base_settlement_data_source=event.base_settlement_data_source,
            history_record_source=event.history_record_source,
            multiplier=FixedMultiplier(Resolved(1.0)),
            crit_rule=NoCritRule(),
        )
        post_modifiers = tuple(
            modifier
            for modifier in context.modifiers
            if modifier.modifier_path
            not in {
                CalculationNode.DISORDER_EXTRA_MULTIPLIER,
                CalculationNode.POLAR_DISORDER_MULTIPLIER,
                CalculationNode.POLAR_DISORDER_AP_COEFFICIENT,
            }
        )
        post_history = [
            post_record if item.record_id == post_record.record_id else item
            for item in context.history_records
        ]
        if not any(item.record_id == post_record.record_id for item in post_history):
            post_history.append(post_record)
        post_result = DisorderDamageCalculator().calculate(
            replace(
                context,
                event=post_event,
                history_records=tuple(post_history),
                modifiers=post_modifiers,
            )
        )
        breakdown = (
            _node(CalculationNode.ANOMALY_EFFECT_STRENGTH, source_strength)
            if source_strength is not None
            else _node_unresolved(
                CalculationNode.ANOMALY_EFFECT_STRENGTH,
                record.weighted_anomaly_effect_strength,
            ),
            _node(CalculationNode.DISORDER_BASE_MULTIPLIER, base_multiplier),
            _node(CalculationNode.DISORDER_TIME_COMPENSATION_MULTIPLIER, time_compensation)
            if time_compensation is not None
            else _node_unresolved(
                CalculationNode.DISORDER_TIME_COMPENSATION_MULTIPLIER,
                record.duration,
            ),
            _node(CalculationNode.DISORDER_EXTRA_MULTIPLIER, core_extra),
            _node(
                CalculationNode.DISORDER_TOTAL_MULTIPLIER,
                base_multiplier + (time_compensation or 0.0) + core_extra,
            ),
            _node(CalculationNode.POLAR_DISORDER_MULTIPLIER, polarity_multiplier),
            _node(
                CalculationNode.POLAR_DISORDER_AP_COEFFICIENT,
                event.anomaly_proficiency_coefficient,
            ),
            _node(CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY, anomaly_proficiency)
            if anomaly_proficiency is not None
            else _node_unresolved(
                CalculationNode.CHARACTER_CURRENT_ANOMALY_PROFICIENCY,
                damage_dealer.settlement_stats.anomaly_proficiency,
            ),
            _node(CalculationNode.DAMAGE_BASE_VALUE, known_base),
        )
        unresolved.extend(post_result.unresolved)
        return replace(
            post_result,
            breakdown=(
                *breakdown,
                *(
                    item
                    for item in post_result.breakdown
                    if item.node
                    not in {
                        CalculationNode.ANOMALY_EFFECT_STRENGTH,
                        CalculationNode.DISORDER_TOTAL_MULTIPLIER,
                        CalculationNode.DAMAGE_BASE_VALUE,
                    }
                ),
            ),
            unresolved=tuple(unresolved),
            anomaly_effect_strength_trace=record.anomaly_effect_strength_trace,
            anomaly_record_id=str(record.record_id),
        )


def _node_unresolved(node: CalculationNode, value) -> CalculationNodeValue:
    return CalculationNodeValue(
        node=node,
        value=value,
        read_rule=SnapshotRule.SETTLEMENT,
    )
