from .crit import (
    AnomalyCritRegionInput,
    CritRegionInput,
    DischargeCritRegionInput,
    TurbulenceCritRegionInput,
    calculate_anomaly_crit_region,
    calculate_crit_region,
    calculate_discharge_crit_region,
    calculate_turbulence_crit_region,
)
from .damage_bonus import (
    NormalDamageBonusRegionInput,
    calculate_normal_damage_bonus_region,
)
from .defense import (
    DefenseRegionInput,
    calculate_defense_region,
    defense_level_coefficient,
)
from .disorder import (
    DisorderDamageBonusRegionInput,
    calculate_disorder_damage_bonus_region,
)
from .derived_anomaly import (
    DischargeDamageBonusRegionInput,
    LuminanceAnomalyDamageBonusRegionInput,
    TurbulenceDamageBonusRegionInput,
    calculate_discharge_damage_bonus_region,
    calculate_luminance_anomaly_damage_bonus_region,
    calculate_turbulence_damage_bonus_region,
)
from .penetration_damage import (
    PenetrationDamageBonusRegionInput,
    PenetrationForceInput,
    calculate_penetration_damage_bonus_region,
    calculate_penetration_force,
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
    "AnomalyCritRegionInput",
    "CritRegionInput",
    "DefenseRegionInput",
    "DischargeCritRegionInput",
    "DischargeDamageBonusRegionInput",
    "DisorderDamageBonusRegionInput",
    "NormalDamageBonusRegionInput",
    "LuminanceAnomalyDamageBonusRegionInput",
    "PenetrationDamageBonusRegionInput",
    "PenetrationForceInput",
    "ResistanceRegionInput",
    "SpecialIndependentRegionInput",
    "TurbulenceCritRegionInput",
    "TurbulenceDamageBonusRegionInput",
    "calculate_broad_vulnerability_region",
    "calculate_anomaly_crit_region",
    "calculate_crit_region",
    "calculate_defense_region",
    "calculate_discharge_crit_region",
    "calculate_discharge_damage_bonus_region",
    "calculate_disorder_damage_bonus_region",
    "calculate_normal_damage_bonus_region",
    "calculate_luminance_anomaly_damage_bonus_region",
    "calculate_penetration_damage_bonus_region",
    "calculate_penetration_force",
    "calculate_resistance_region",
    "calculate_special_independent_region",
    "calculate_turbulence_crit_region",
    "calculate_turbulence_damage_bonus_region",
    "defense_level_coefficient",
]
