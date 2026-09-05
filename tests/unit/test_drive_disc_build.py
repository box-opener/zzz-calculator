from __future__ import annotations

import pytest

from core.application.build import assemble_build
from core.application.equipment import (
    DRIVE_DISC_REVIEWED_MAPPINGS,
    compile_drive_discs,
    load_drive_disc_raw_record,
    stable_set_id,
)
from core.data.drive_discs.loader import DRIVE_DISC_SET_IDS, SOURCE_VERSION
from core.types import (
    BuildMode,
    CharacterBuildDefinition,
    CharacterId,
    CharacterRole,
    CharacterStats,
    DamageTag,
    DriveDiscBuildInput,
    DriveDiscSlot,
    DriveDiscStatKey,
    DriveDiscSubstatRoll,
    Element,
    EquipmentOwnerCapabilities,
    EquippedDriveDisc,
    Resolved,
    SkillGroup,
)


OWNER = CharacterId("character:drive-test")


def _capabilities() -> EquipmentOwnerCapabilities:
    return EquipmentOwnerCapabilities(
        character_id=OWNER,
        role=CharacterRole.ATTACK,
        possible_elements=frozenset({Element.PHYSICAL}),
    )


def _disc(
    slot: DriveDiscSlot, set_id: str, main: DriveDiscStatKey, *, attack_rolls: int = 2
) -> EquippedDriveDisc:
    return EquippedDriveDisc(
        slot=slot,
        set_id=stable_set_id(set_id),
        main_stat=main,
        substats=(
            DriveDiscSubstatRoll(DriveDiscStatKey.ATTACK_FLAT, attack_rolls),
            DriveDiscSubstatRoll(DriveDiscStatKey.CRIT_RATE, 2),
            DriveDiscSubstatRoll(DriveDiscStatKey.CRIT_DAMAGE, 2),
            DriveDiscSubstatRoll(DriveDiscStatKey.PENETRATION_FLAT, 2),
        ),
    )


def _stats() -> CharacterStats:
    return CharacterStats(
        hp=Resolved(10000.0),
        attack=Resolved(1000.0),
        defense=Resolved(500.0),
        impact=Resolved(100.0),
        crit_rate=Resolved(0.05),
        crit_damage=Resolved(0.50),
        anomaly_mastery=Resolved(100.0),
        anomaly_proficiency=Resolved(100.0),
        penetration_rate=Resolved(0.0),
        penetration_flat=Resolved(0.0),
        energy_regen=Resolved(1.2),
        element_damage_bonus={},
    )


def test_frozen_catalog_and_review_manifest_cover_all_thirty_sets() -> None:
    assert len(DRIVE_DISC_SET_IDS) == 30
    assert set(DRIVE_DISC_SET_IDS) == set(DRIVE_DISC_REVIEWED_MAPPINGS)
    for set_id in DRIVE_DISC_SET_IDS:
        raw = load_drive_disc_raw_record(stable_set_id(set_id))
        assert raw.source_version == SOURCE_VERSION == "3.2.4+18409985"
        assert raw.two_piece_text
        assert raw.four_piece_text
        assert raw.icon.endswith(".png")


@pytest.mark.parametrize("set_id", DRIVE_DISC_SET_IDS)
def test_every_reviewed_set_compiles_its_four_piece_disposition(set_id: str) -> None:
    mains = (
        DriveDiscStatKey.HP_FLAT,
        DriveDiscStatKey.ATTACK_FLAT,
        DriveDiscStatKey.DEFENSE_FLAT,
        DriveDiscStatKey.ATTACK_PERCENT,
    )
    resolution = compile_drive_discs(
        DriveDiscBuildInput(
            OWNER,
            tuple(
                _disc(DriveDiscSlot(index), set_id, main)
                for index, main in enumerate(mains, start=1)
            ),
        ),
        owner_capabilities=EquipmentOwnerCapabilities(
            character_id=OWNER,
            role=CharacterRole.ATTACK,
            possible_elements=frozenset(Element),
            skill_groups=frozenset(SkillGroup),
            damage_tags=frozenset(DamageTag),
        ),
    )
    mapping = DRIVE_DISC_REVIEWED_MAPPINGS[set_id]
    if mapping.four_piece_disposition.value == "calculation-rule":
        assert resolution.rule_items
    else:
        assert not resolution.rule_items


def test_all_reviewed_set_instance_ids_are_unique_for_one_owner() -> None:
    owner = OWNER
    rule_ids = []
    effect_ids = []
    condition_ids = []
    for set_id in DRIVE_DISC_SET_IDS:
        resolution = compile_drive_discs(
            DriveDiscBuildInput(
                owner,
                (
                    _disc(DriveDiscSlot.ONE, set_id, DriveDiscStatKey.HP_FLAT),
                    _disc(DriveDiscSlot.TWO, set_id, DriveDiscStatKey.ATTACK_FLAT),
                    _disc(DriveDiscSlot.THREE, set_id, DriveDiscStatKey.DEFENSE_FLAT),
                    _disc(DriveDiscSlot.FOUR, set_id, DriveDiscStatKey.ATTACK_PERCENT),
                ),
            ),
            owner_capabilities=EquipmentOwnerCapabilities(
                character_id=owner,
                role=CharacterRole.ATTACK,
                possible_elements=frozenset(Element),
                skill_groups=frozenset(SkillGroup),
                damage_tags=frozenset(DamageTag),
            ),
        )
        rule_ids.extend(item.rule_id for item in resolution.rule_items)
        effect_ids.extend(
            effect.rule.effect_id
            for item in resolution.rule_items
            for effect in item.effects
        )
        condition_ids.extend(
            item.condition_id for item in resolution.scenario_conditions
        )
    assert len(rule_ids) == len(set(rule_ids))
    assert len(effect_ids) == len(set(effect_ids))
    assert len(condition_ids) == len(set(condition_ids))


def test_slot_main_stat_and_substat_invariants() -> None:
    with pytest.raises(ValueError, match="invalid main stat"):
        _disc(DriveDiscSlot.ONE, "31000", DriveDiscStatKey.CRIT_RATE)
    with pytest.raises(ValueError, match="cannot also be a substat"):
        EquippedDriveDisc(
            slot=DriveDiscSlot.FOUR,
            set_id=stable_set_id("31000"),
            main_stat=DriveDiscStatKey.CRIT_RATE,
            substats=(DriveDiscSubstatRoll(DriveDiscStatKey.CRIT_RATE, 1),),
        )
    with pytest.raises(ValueError, match="slots must be unique"):
        DriveDiscBuildInput(
            OWNER,
            (
                _disc(DriveDiscSlot.ONE, "31000", DriveDiscStatKey.HP_FLAT),
                _disc(DriveDiscSlot.ONE, "31100", DriveDiscStatKey.HP_FLAT),
            ),
        )


def test_attack_substat_is_nineteen_per_roll_and_incomplete_disc_blocks() -> None:
    complete = compile_drive_discs(
        DriveDiscBuildInput(
            OWNER,
            (
                _disc(
                    DriveDiscSlot.TWO,
                    "31000",
                    DriveDiscStatKey.ATTACK_FLAT,
                    attack_rolls=3,
                ),
            ),
        ),
        owner_capabilities=_capabilities(),
    )
    attack_sub = next(
        item
        for item in complete.contributions
        if ":sub:attack-flat" in item.contribution_id
    )
    assert attack_sub.value == Resolved(57.0)
    assert complete.complete is True
    assert "requires four substats" not in " ".join(
        item.message for item in complete.diagnostics
    )

    incomplete = compile_drive_discs(
        DriveDiscBuildInput(
            OWNER,
            (
                EquippedDriveDisc(
                    DriveDiscSlot.ONE,
                    stable_set_id("31000"),
                    DriveDiscStatKey.HP_FLAT,
                ),
            ),
        ),
        owner_capabilities=_capabilities(),
    )
    assert incomplete.complete is False
    assert incomplete.diagnostics[0].blocking is True


def test_four_plus_two_and_static_two_piece_contributions_assemble_once() -> None:
    discs = (
        _disc(DriveDiscSlot.ONE, "31000", DriveDiscStatKey.HP_FLAT),
        _disc(DriveDiscSlot.TWO, "31000", DriveDiscStatKey.ATTACK_FLAT),
        _disc(DriveDiscSlot.THREE, "31000", DriveDiscStatKey.DEFENSE_FLAT),
        _disc(DriveDiscSlot.FOUR, "31000", DriveDiscStatKey.ATTACK_PERCENT),
        _disc(DriveDiscSlot.FIVE, "31400", DriveDiscStatKey.PHYSICAL_DAMAGE_BONUS),
        _disc(DriveDiscSlot.SIX, "31400", DriveDiscStatKey.IMPACT_PERCENT),
    )
    resolution = compile_drive_discs(
        DriveDiscBuildInput(OWNER, discs),
        owner_capabilities=_capabilities(),
    )
    assert resolution.complete is True
    assert dict(resolution.set_counts) == {
        stable_set_id("31000"): 4,
        stable_set_id("31400"): 2,
    }
    assert (
        sum(item.contribution_id.endswith(":2pc") for item in resolution.contributions)
        == 2
    )
    build = assemble_build(
        CharacterBuildDefinition(
            character_id=OWNER,
            level=60,
            mode=BuildMode.EQUIPMENT_BUILD,
            base_stats=_stats(),
            contributions=resolution.contributions,
        )
    )
    # 1000 * (1 + slot4 30% + Hormone Punk 10%) + slot2 316 + six 2-roll ATK subs.
    assert build.initial_stats.attack == Resolved(1944.0)
    assert build.initial_stats.crit_rate.value == pytest.approx(0.418)
