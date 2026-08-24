"""Rule provenance shared by States and Effects."""

from dataclasses import dataclass

from .common import RuleSourceId
from .enums import EffectSourceType


@dataclass(frozen=True, slots=True)
class RuleSource:
    source_id: RuleSourceId
    source_type: EffectSourceType
    label: str
    raw_text: str | None = None
