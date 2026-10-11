from __future__ import annotations

from types import SimpleNamespace

import pytest

import core.presentation.registry as presentation_registry
from core.types import CharacterId, CharacterRole


@pytest.fixture
def raw_team_records(monkeypatch: pytest.MonkeyPatch) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {
        "character:1411": {"camp": {"11": "旧阵营名称"}}
    }
    monkeypatch.setattr(
        presentation_registry,
        "load_character_record",
        lambda character_id: records[str(character_id)],
    )
    return records


def _register_team_member(
    monkeypatch: pytest.MonkeyPatch,
    records: dict[str, dict[str, object]],
    character_id: str,
    role: CharacterRole,
    camp: dict[str, str],
) -> CharacterId:
    parsed_id = CharacterId(character_id)
    monkeypatch.setitem(
        presentation_registry._REGISTRATIONS,
        parsed_id,
        SimpleNamespace(role=role),
    )
    records[character_id] = {"camp": camp}
    return parsed_id


def test_yuzuha_eligibility_reads_matching_faction_from_raw_records(
    monkeypatch: pytest.MonkeyPatch,
    raw_team_records: dict[str, dict[str, object]],
) -> None:
    future_same_faction = _register_team_member(
        monkeypatch,
        raw_team_records,
        "character:9991",
        CharacterRole.ATTACK,
        {"11": "重命名后的阵营"},
    )

    assert presentation_registry._yuzuha_eligibility((future_same_faction,))


def test_yuzuha_eligibility_still_accepts_anomaly_teammates(
    monkeypatch: pytest.MonkeyPatch,
    raw_team_records: dict[str, dict[str, object]],
) -> None:
    anomaly = _register_team_member(
        monkeypatch,
        raw_team_records,
        "character:9992",
        CharacterRole.ANOMALY,
        {"77": "其他阵营"},
    )

    assert presentation_registry._yuzuha_eligibility((anomaly,))


def test_yuzuha_eligibility_rejects_unrelated_roles_and_factions(
    monkeypatch: pytest.MonkeyPatch,
    raw_team_records: dict[str, dict[str, object]],
) -> None:
    unrelated = _register_team_member(
        monkeypatch,
        raw_team_records,
        "character:9993",
        CharacterRole.SUPPORT,
        {"77": "旧阵营名称"},
    )

    assert not presentation_registry._yuzuha_eligibility((unrelated,))


def test_yuzuha_does_not_qualify_itself(
    raw_team_records: dict[str, dict[str, object]],
) -> None:
    yuzuha = CharacterId("character:1411")

    assert not presentation_registry._yuzuha_eligibility((yuzuha,))
