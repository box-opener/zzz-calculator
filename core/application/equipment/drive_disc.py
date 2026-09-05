"""Compile six equipped Drive Discs into Build contributions and rules."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from core.application.diagnostics import CalculationDiagnostic, DiagnosticKind
from core.application.ids import DiagnosticId
from core.application.rules import CalculationRuleItem
from core.application.scenario import ScenarioCondition
from core.data.drive_discs.loader import (
    DRIVE_DISC_SET_IDS,
    SOURCE_PROVIDER,
    SOURCE_VERSION,
    load_drive_disc_record,
    source_url_for,
)
from core.types import (
    BuildContributionLayer,
    BuildSource,
    BuildSourceType,
    BuildStatContribution,
    CharacterStat,
    DriveDiscBuildInput,
    DriveDiscSetId,
    DriveDiscStatKey,
    Element,
    EquipmentOwnerCapabilities,
    Resolved,
)

from .drive_disc_reviewed import (
    DRIVE_DISC_REVIEWED_MAPPINGS,
    DriveDiscClauseDisposition,
)


@dataclass(frozen=True, slots=True)
class DriveDiscRawRecord:
    set_id: DriveDiscSetId
    name: str
    two_piece_text: str
    four_piece_text: str
    icon: str
    source_provider: str
    source_version: str
    source_url: str


@dataclass(frozen=True, slots=True)
class DriveDiscBuildResolution:
    build_input: DriveDiscBuildInput
    set_counts: tuple[tuple[DriveDiscSetId, int], ...]
    contributions: tuple[BuildStatContribution, ...]
    rule_items: tuple[CalculationRuleItem, ...] = ()
    scenario_conditions: tuple[ScenarioCondition, ...] = ()
    diagnostics: tuple[CalculationDiagnostic, ...] = ()

    @property
    def complete(self) -> bool:
        return not any(item.blocking for item in self.diagnostics)


def _raw_id(set_id: DriveDiscSetId | str) -> str:
    value = str(set_id)
    return value.removeprefix("drive-disc:")


def stable_set_id(raw_id: str) -> DriveDiscSetId:
    if raw_id not in DRIVE_DISC_SET_IDS:
        raise ValueError(f"unsupported reviewed Drive Disc set: {raw_id}")
    return DriveDiscSetId(f"drive-disc:{raw_id}")


def load_drive_disc_raw_record(set_id: DriveDiscSetId | str) -> DriveDiscRawRecord:
    raw_id = _raw_id(set_id)
    payload = load_drive_disc_record(raw_id)
    if (
        payload.get("source_provider") != SOURCE_PROVIDER
        or payload.get("source_version") != SOURCE_VERSION
        or payload.get("source_url") != source_url_for(raw_id)
    ):
        raise ValueError(f"Drive Disc fixture source metadata is invalid: {raw_id}")
    return DriveDiscRawRecord(
        set_id=stable_set_id(raw_id),
        name=str(payload["name"]).strip(),
        two_piece_text=str(payload["desc2"]).strip(),
        four_piece_text=str(payload["desc4"]).strip(),
        icon=str(payload["icon"]).strip(),
        source_provider=str(payload["source_provider"]),
        source_version=str(payload["source_version"]),
        source_url=str(payload["source_url"]),
    )


_STAT_MAPPING: dict[
    DriveDiscStatKey, tuple[CharacterStat, BuildContributionLayer, Element | None]
] = {
    DriveDiscStatKey.HP_FLAT: (
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        None,
    ),
    DriveDiscStatKey.ATTACK_FLAT: (
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        None,
    ),
    DriveDiscStatKey.DEFENSE_FLAT: (
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        None,
    ),
    DriveDiscStatKey.PENETRATION_FLAT: (
        CharacterStat.PENETRATION_FLAT,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        None,
    ),
    DriveDiscStatKey.ANOMALY_PROFICIENCY_FLAT: (
        CharacterStat.ANOMALY_PROFICIENCY,
        BuildContributionLayer.OUT_OF_COMBAT_FLAT,
        None,
    ),
    DriveDiscStatKey.CRIT_RATE: (
        CharacterStat.CRIT_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        None,
    ),
    DriveDiscStatKey.CRIT_DAMAGE: (
        CharacterStat.CRIT_DAMAGE,
        BuildContributionLayer.DIRECT_RATIO,
        None,
    ),
    DriveDiscStatKey.HP_PERCENT: (
        CharacterStat.HP,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.ATTACK_PERCENT: (
        CharacterStat.ATTACK,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.DEFENSE_PERCENT: (
        CharacterStat.DEFENSE,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.IMPACT_PERCENT: (
        CharacterStat.IMPACT,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.ANOMALY_MASTERY_PERCENT: (
        CharacterStat.ANOMALY_MASTERY,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.ENERGY_REGEN_PERCENT: (
        CharacterStat.ENERGY_REGEN,
        BuildContributionLayer.OUT_OF_COMBAT_PERCENT,
        None,
    ),
    DriveDiscStatKey.PENETRATION_RATE: (
        CharacterStat.PENETRATION_RATE,
        BuildContributionLayer.DIRECT_RATIO,
        None,
    ),
    DriveDiscStatKey.FIRE_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.FIRE,
    ),
    DriveDiscStatKey.ICE_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.ICE,
    ),
    DriveDiscStatKey.WIND_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.WIND,
    ),
    DriveDiscStatKey.ELECTRIC_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.ELECTRIC,
    ),
    DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.PHYSICAL,
    ),
    DriveDiscStatKey.ETHER_DAMAGE_BONUS: (
        CharacterStat.ELEMENT_DAMAGE_BONUS,
        BuildContributionLayer.DIRECT_RATIO,
        Element.ETHER,
    ),
}


def _contribution(
    source: BuildSource, contribution_id: str, key: DriveDiscStatKey, value: float
) -> BuildStatContribution:
    stat, layer, element = _STAT_MAPPING[key]
    return BuildStatContribution(
        contribution_id=contribution_id,
        source=source,
        stat=stat,
        layer=layer,
        value=Resolved(value),
        element=element,
    )


def _diagnostic(owner: str, suffix: str, message: str) -> CalculationDiagnostic:
    return CalculationDiagnostic(
        diagnostic_id=DiagnosticId(f"drive-disc:{owner}:{suffix}"),
        kind=DiagnosticKind.MISSING_DATA,
        message=message,
        blocking=True,
    )


def compile_drive_discs(
    build_input: DriveDiscBuildInput,
    *,
    owner_capabilities: EquipmentOwnerCapabilities,
) -> DriveDiscBuildResolution:
    if owner_capabilities.character_id != build_input.equipped_character_id:
        raise ValueError("Drive Disc owner capabilities must match build owner")
    owner = str(build_input.equipped_character_id).replace(":", "_")
    contributions: list[BuildStatContribution] = []
    rules: list[CalculationRuleItem] = []
    conditions: list[ScenarioCondition] = []
    diagnostics: list[CalculationDiagnostic] = []
    counts: Counter[DriveDiscSetId] = Counter()
    for disc in build_input.discs:
        raw = load_drive_disc_raw_record(disc.set_id)
        counts[raw.set_id] += 1
        source = BuildSource(
            source_id=f"{raw.set_id}:owner:{owner}:slot:{int(disc.slot)}",
            source_type=BuildSourceType.DRIVE_DISC,
            label=f"{raw.name}·{int(disc.slot)}号盘",
        )
        from core.types import DRIVE_DISC_MAIN_STAT_VALUES, DRIVE_DISC_SUBSTAT_VALUES

        contributions.append(
            _contribution(
                source,
                f"{source.source_id}:main:{disc.main_stat.value}",
                disc.main_stat,
                DRIVE_DISC_MAIN_STAT_VALUES[disc.main_stat],
            )
        )
        for substat in disc.substats:
            contributions.append(
                _contribution(
                    source,
                    f"{source.source_id}:sub:{substat.stat.value}",
                    substat.stat,
                    DRIVE_DISC_SUBSTAT_VALUES[substat.stat] * substat.roll_count,
                )
            )
        if not disc.complete:
            diagnostics.append(
                _diagnostic(
                    owner,
                    f"slot-{int(disc.slot)}-incomplete",
                    f"Drive Disc slot {int(disc.slot)} requires four substats and 8 or 9 total rolls",
                )
            )

    for stable_id, count in sorted(counts.items(), key=lambda item: str(item[0])):
        raw_id = _raw_id(stable_id)
        mapping = DRIVE_DISC_REVIEWED_MAPPINGS[raw_id]
        if (
            count >= 2
            and mapping.two_piece_disposition
            is DriveDiscClauseDisposition.STATIC_CONTRIBUTION
        ):
            assert mapping.two_piece_static is not None
            raw = load_drive_disc_raw_record(stable_id)
            static = mapping.two_piece_static
            contributions.append(
                BuildStatContribution(
                    contribution_id=f"{stable_id}:owner:{owner}:2pc",
                    source=BuildSource(
                        source_id=f"{stable_id}:owner:{owner}:2pc",
                        source_type=BuildSourceType.DRIVE_DISC_SET,
                        label=f"{raw.name}·2件套",
                    ),
                    stat=static.stat,
                    layer=static.layer,
                    value=Resolved(static.value),
                    element=static.element,
                )
            )

        from .drive_disc_rules import compile_reviewed_drive_disc_rules

        compiled = compile_reviewed_drive_disc_rules(
            load_drive_disc_raw_record(stable_id),
            mapping,
            count,
            build_input.equipped_character_id,
            owner_capabilities,
        )
        rules.extend(compiled.rule_items)
        conditions.extend(compiled.scenario_conditions)

    # Rule compilation is intentionally a separate reviewed pass below; this
    # build contract already guarantees that no raw text is interpreted here.
    return DriveDiscBuildResolution(
        build_input=build_input,
        set_counts=tuple(sorted(counts.items(), key=lambda item: str(item[0]))),
        contributions=tuple(contributions),
        rule_items=tuple(rules),
        scenario_conditions=tuple(conditions),
        diagnostics=tuple(diagnostics),
    )


__all__ = [
    "DriveDiscBuildResolution",
    "DriveDiscRawRecord",
    "compile_drive_discs",
    "load_drive_disc_raw_record",
    "stable_set_id",
]
