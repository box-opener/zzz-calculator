from .crit import CritRegionInput, calculate_crit_region
from .damage_bonus import (
    NormalDamageBonusRegionInput,
    calculate_normal_damage_bonus_region,
)
from .defense import (
    DefenseRegionInput,
    calculate_defense_region,
    defense_level_coefficient,
)
from .resistance import ResistanceRegionInput, calculate_resistance_region
from .special_independent import (
    SpecialIndependentRegionInput,
    calculate_special_independent_region,
)
from .vulnerability import (
    BroadVulnerabilityRegionInput,
    calculate_broad_vulnerability_region,
)

__all__ = [
    "BroadVulnerabilityRegionInput",
    "CritRegionInput",
    "DefenseRegionInput",
    "NormalDamageBonusRegionInput",
    "ResistanceRegionInput",
    "SpecialIndependentRegionInput",
    "calculate_broad_vulnerability_region",
    "calculate_crit_region",
    "calculate_defense_region",
    "calculate_normal_damage_bonus_region",
    "calculate_resistance_region",
    "calculate_special_independent_region",
    "defense_level_coefficient",
]
