"""Source compiler for Claret (character:1611).

Vanguard Sharp Damage does not yet have a calculator event type.  Until that
shared execution contract exists, this compiler retains and resolves every
reviewed Nanoka curve without labelling it as Direct or Sharp Explosion.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from core.types import CalculationNode, CharacterId, SkillGroup

from ...ids import DamageEventSemanticId, MoveEntryId, MultiplierVariantId
from ...moves import DamageEventTemplateRef, MoveCalculationEntry, MultiplierRelation, MultiplierVariant
from ..definition import CharacterCalculationDefinition
from ..nanoka_compiler import effective_skill_level, raw_move_index
from ..nanoka_source import NanokaRawRecord, load_nanoka_raw_record
from ..nanoka_compiler import source_for
from ..templates import UnresolvedSharpenedDamageEventTemplate
from core.types import (
    CharacterRole,
    CurrentDefenseValueSource,
    DamageType,
    EffectSourceType,
    FixedMultiplier,
    Resolved,
    Unresolved,
    UnresolvedReason,
)
from .config import CLARET_ID, ClaretCompileConfig
from .reviewed import (
    CLARET_CURRENT_SCARLET_CRIT_NODE,
    CLARET_INITIAL_CRIT_CONVERSION,
    CLARET_SOURCE_CURVES,
    ClaretInitialCritConversionSpec,
    ClaretSourceCurveSpec,
)


@dataclass(frozen=True, slots=True)
class ClaretSourcePanel:
    base_crit_rate: float
    base_crit_damage: float
    sharp_crit_damage: float


@dataclass(frozen=True, slots=True)
class ClaretCinemaSourceValues:
    cinema1_mark_buildup_bonus: float
    cinema1_destroy_multiplier: float
    cinema2_mark_duration_bonus_seconds: float
    cinema2_electric_resistance_ignore: float
    cinema4_named_move_damage_bonus: float
    cinema6_destroy_trigger_count: int


@dataclass(frozen=True, slots=True)
class ClaretCompiledCurve:
    spec: ClaretSourceCurveSpec
    skill_level: int
    source_percent: float

    @property
    def multiplier(self) -> float:
        return self.source_percent / 100.0


@dataclass(frozen=True, slots=True)
class ClaretSourceCompilation:
    raw_record: NanokaRawRecord
    config: ClaretCompileConfig
    source_panel: ClaretSourcePanel
    curves: tuple[ClaretCompiledCurve, ...]
    core_initial_crit_conversion: ClaretInitialCritConversionSpec
    core_scarlet_crit_source_node: CalculationNode
    core_scarlet_crit_scope_text: str
    core_scarlet_crit_rate_bonus: float
    cinema_values: ClaretCinemaSourceValues
    notes: tuple[str, ...]


def load_raw_record(data: Mapping[str, object]) -> NanokaRawRecord:
    return load_nanoka_raw_record(data, expected_character_id=str(CLARET_ID))


def _raw_stats(data: Mapping[str, object]) -> Mapping[str, object]:
    stats = data.get("stats")
    if not isinstance(stats, Mapping):
        raise ValueError("Claret source record is missing its stats object")
    return stats


def _plain(text: str) -> str:
    return re.sub(r"<[^>]*>", "", text)


def _source_initial_conversion(raw: NanokaRawRecord) -> float:
    text = _plain(raw.core_levels[0].description)
    match = re.search(
        r"每拥有\s*1%\s*的初始暴击伤害，初始暴击率提升\s*([\d.]+)%",
        text,
    )
    if match is None:
        raise ValueError("Claret Core source no longer contains its initial-crit conversion")
    # The raw text states a percent-per-percent conversion.  Both panel values
    # are ratio-valued (for example 50% crit damage is 0.5), so 0.35% per each
    # 1% becomes a ratio-to-ratio coefficient of 0.35.
    source_coefficient = float(match.group(1))
    if source_coefficient != CLARET_INITIAL_CRIT_CONVERSION.coefficient:
        raise ValueError("Claret reviewed initial-crit conversion differs from source")
    return source_coefficient


def _source_scarlet_crit_rate(raw: NanokaRawRecord, core_level: int) -> float:
    text = _plain(raw.core_levels[core_level - 1].description)
    match = re.search(r"处于\[猩红铭刻\].*?暴击率提升\s*([\d.]+)%", text, re.DOTALL)
    if match is None:
        raise ValueError(f"Claret Core {core_level} source lacks the Scarlet crit-rate value")
    return float(match.group(1)) / 100.0


def _source_scarlet_crit_scope(raw: NanokaRawRecord, core_level: int) -> str:
    text = _plain(raw.core_levels[core_level - 1].description)
    line = next(
        (
            line
            for line in text.splitlines()
            if "猩红铭刻" in line and "暴击率提升" in line
        ),
        None,
    )
    if line is None:
        raise ValueError(f"Claret Core {core_level} source lacks Scarlet crit scope")
    return line.split("暴击率提升", maxsplit=1)[0].strip().rstrip("，")


def _source_cinema_values(raw: NanokaRawRecord) -> ClaretCinemaSourceValues:
    by_level = {item.level: _plain(item.description) for item in raw.mindscapes}
    if set(by_level) != {1, 2, 3, 4, 5, 6}:
        raise ValueError("Claret source must contain all six Mindscape descriptions")

    def number(level: int, pattern: str, label: str) -> float:
        match = re.search(pattern, by_level[level])
        if match is None:
            raise ValueError(f"Claret Cinema {level} source lacks {label}")
        return float(match.group("value"))

    destroy_count = number(
        6,
        r"直接触发\s*(?P<value>\d+)次单体\[毁伤\]",
        "its single-target Destroy count",
    )
    return ClaretCinemaSourceValues(
        cinema1_mark_buildup_bonus=(
            number(1, r"残痕积蓄效率提升\s*(?P<value>[\d.]+)%", "mark buildup")
            / 100.0
        ),
        cinema1_destroy_multiplier=(
            number(
                1,
                r"毁伤\]造成的伤害倍率提升至原本的\s*(?P<value>[\d.]+)%",
                "the Destroy multiplier",
            )
            / 100.0
        ),
        cinema2_mark_duration_bonus_seconds=number(
            2,
            r"最大持续时间延长\s*(?P<value>[\d.]+)秒",
            "the Scarlet mark duration",
        ),
        cinema2_electric_resistance_ignore=(
            number(
                2,
                r"无视目标\s*(?P<value>[\d.]+)%.*?电属性伤害抗性",
                "Electric resistance ignore",
            )
            / 100.0
        ),
        cinema4_named_move_damage_bonus=(
            number(4, r"造成的伤害提升\s*(?P<value>[\d.]+)%", "named-move damage")
            / 100.0
        ),
        cinema6_destroy_trigger_count=int(destroy_count),
    )


def derive_initial_crit_rate(
    initial_crit_rate: float,
    initial_crit_damage: float,
    *,
    core_conversion_enabled: bool,
) -> float:
    """Apply the reviewed immutable-initial-panel conversion as a pure rule."""

    if initial_crit_rate < 0 or initial_crit_damage < 0:
        raise ValueError("initial crit values must be non-negative")
    if not isinstance(core_conversion_enabled, bool):
        raise ValueError("core_conversion_enabled must be boolean")
    if not core_conversion_enabled:
        return initial_crit_rate
    return initial_crit_rate + initial_crit_damage * CLARET_INITIAL_CRIT_CONVERSION.coefficient


def compile_claret(
    config: ClaretCompileConfig,
    raw_record: NanokaRawRecord,
    source_data: Mapping[str, object],
) -> ClaretSourceCompilation:
    if raw_record.character_id != CLARET_ID:
        raise ValueError("Claret compiler requires character:1611")
    if (
        raw_record.code_name != "Claret"
        or raw_record.name != "克拉蕾"
        or raw_record.rarity != 4
        or raw_record.specialty != "锋御"
        or raw_record.element != "电属性"
        or raw_record.faction != "罗斯凯利法"
        or raw_record.icon != "IconRole1611"
    ):
        raise ValueError("Claret raw identity does not match reviewed source")
    stats = _raw_stats(source_data)
    try:
        panel = ClaretSourcePanel(
            base_crit_rate=float(stats["crit"]) / 10000.0,
            base_crit_damage=float(stats["crit_damage"]) / 10000.0,
            sharp_crit_damage=float(stats["sharp_critical_damage"]) / 10000.0,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Claret source panel lacks reviewed crit fields") from exc

    raw_moves = raw_move_index(raw_record)
    curves: list[ClaretCompiledCurve] = []
    for spec in CLARET_SOURCE_CURVES:
        raw_move = raw_moves.get(spec.source_name)
        if raw_move is None:
            raise ValueError(f"Claret source is missing move {spec.source_name}")
        parameter = next(
            (
                item
                for item in raw_move.parameters
                if item.name == spec.parameter_name
            ),
            None,
        )
        level = effective_skill_level(config, spec.source_skill_group)
        value = (
            parameter.value_for_level(level, spec.source_skill_id)
            if parameter is not None
            else None
        )
        if parameter is None or parameter.format != "%" or value is None:
            raise ValueError(
                f"Claret source curve {spec.source_skill_id} is missing "
                f"{spec.parameter_name} at level {level}"
            )
        curves.append(
            ClaretCompiledCurve(
                spec=spec,
                skill_level=level,
                source_percent=float(value),
            )
        )

    _source_initial_conversion(raw_record)
    return ClaretSourceCompilation(
        raw_record=raw_record,
        config=config,
        source_panel=panel,
        curves=tuple(curves),
        core_initial_crit_conversion=CLARET_INITIAL_CRIT_CONVERSION,
        core_scarlet_crit_source_node=CLARET_CURRENT_SCARLET_CRIT_NODE,
        core_scarlet_crit_scope_text=_source_scarlet_crit_scope(
            raw_record,
            config.core_level,
        ),
        core_scarlet_crit_rate_bonus=_source_scarlet_crit_rate(
            raw_record,
            config.core_level,
        ),
        cinema_values=_source_cinema_values(raw_record),
        notes=(
            "Reviewed Sharp Damage curves are retained but cannot yet be "
            "executed because the shared typed Vanguard event is not implemented.",
            "Sharp Crit Damage remains separate from ordinary Crit Damage.",
        ),
    )


def compile_claret_definition(
    config: ClaretCompileConfig,
    raw_record: NanokaRawRecord,
    source_data: Mapping[str, object],
) -> CharacterCalculationDefinition:
    """Build Claret's selectable Sharp Damage entries from reviewed source curves."""

    compiled = compile_claret(config, raw_record, source_data)
    source = source_for(
        CLARET_ID,
        "nanoka-sharp-curves",
        EffectSourceType.SKILL,
        "克拉蕾技能倍率",
        "纳诺卡 3.2 技能倍率；锐化伤害结算公式未由项目规范定义。",
    )
    templates: list[UnresolvedSharpenedDamageEventTemplate] = []
    entries: list[MoveCalculationEntry] = []
    unresolved = Unresolved(
        reason=UnresolvedReason.MISSING_SPEC_RULE,
        notes=(
            "锐化伤害的通用结算公式和锐暴机制尚未由项目规范定义；"
            "保留已知电属性、当前防御力基准与技能倍率，不计算伤害。"
        ),
    )
    for curve in compiled.curves:
        spec = curve.spec
        event_move_id = spec.event_move_id
        group = spec.event_skill_group
        tags = spec.damage_tags
        key = spec.key
        ref = DamageEventTemplateRef(
            template_id=f"template:character:1611:{key}",
            semantic_id=DamageEventSemanticId(f"event:character:1611:{key}"),
            label=f"锐化伤害：{spec.source_name}·{spec.parameter_name}",
            damage_type=DamageType.SHARPENED,
            skill_group=group,
            damage_tags=tags,
            element=spec.element,
        )
        templates.append(
            UnresolvedSharpenedDamageEventTemplate(
                ref=ref,
                damage_dealer=CLARET_ID,
                element=spec.element,
                base_source=CurrentDefenseValueSource(CLARET_ID),
                move_id=event_move_id,
                unresolved=unresolved,
            )
        )
        is_basic_stage = key.startswith("basic-forge-") and spec.stage_index is not None
        entries.append(
            MoveCalculationEntry(
                entry_id=MoveEntryId(f"move-entry:character:1611:{key}"),
                character_id=CLARET_ID,
                move_id=event_move_id,
                display_name=(
                    f"{spec.source_name}·{spec.parameter_name}"
                    if spec.semantics.value != "destroy"
                    else "单体毁伤·特殊技触发"
                ),
                original_text=(
                    f"{spec.source_name}；{spec.parameter_name}；"
                    f"源技能ID {spec.source_skill_id}"
                ),
                skill_group=group,
                damage_tags=tags,
                multiplier_relation=(
                    MultiplierRelation.SEQUENTIAL_STAGE
                    if is_basic_stage
                    else MultiplierRelation.COMPLETE
                ),
                multiplier_variants=(
                    MultiplierVariant(
                        variant_id=MultiplierVariantId(
                            f"variant:character:1611:{key}"
                        ),
                        label=f"{spec.parameter_name}（纳诺卡源倍率）",
                        parameter_name=spec.parameter_name,
                        multiplier=FixedMultiplier(Resolved(curve.multiplier)),
                    ),
                ),
                main_damage_event=ref,
                stage_index=spec.stage_index if is_basic_stage else None,
            )
        )
    return CharacterCalculationDefinition(
        character_id=CLARET_ID,
        role=CharacterRole.VANGUARD,
        base_element=compiled.curves[0].spec.element,
        source=source,
        move_entries=tuple(entries),
        rule_items=(),
        scenario_conditions=(),
        scenario_parameters=(),
        damage_event_templates=tuple(templates),
    )


__all__ = [
    "ClaretCinemaSourceValues",
    "ClaretCompiledCurve",
    "ClaretSourceCompilation",
    "ClaretSourcePanel",
    "compile_claret",
    "compile_claret_definition",
    "derive_initial_crit_rate",
    "load_raw_record",
]
