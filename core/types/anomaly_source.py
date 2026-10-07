"""Explicit static source selection for anomaly-based calculations."""

from __future__ import annotations

from dataclasses import dataclass

from .common import AnomalyRecordId, CharacterId
from .enums import ANOMALY_ELEMENTS, Element


@dataclass(frozen=True, slots=True)
class AnomalySourceChoice:
    """One active character and reviewed anomaly element selected as a source."""

    source_character_id: CharacterId
    element: Element

    def __post_init__(self) -> None:
        if not str(self.source_character_id):
            raise ValueError("anomaly source character ID must not be empty")
        if self.element not in ANOMALY_ELEMENTS:
            raise ValueError("ordinary anomaly sources cannot use Luminance")


def anomaly_source_record_id(choice: AnomalySourceChoice) -> AnomalyRecordId:
    element_key = choice.element.value.replace(":", "-")
    return AnomalyRecordId(
        f"anomaly:static-source:{choice.source_character_id}:{element_key}"
    )


__all__ = ["AnomalySourceChoice", "anomaly_source_record_id"]
