import pytest
from core.calculation.regions.crit import (
    calculate_crit_region, calculate_anomaly_crit_region, calculate_discharge_crit_region,
    calculate_turbulence_crit_region, CritRegionInput, AnomalyCritRegionInput, DischargeCritRegionInput, TurbulenceCritRegionInput,
)

@pytest.mark.parametrize('calculator,input_type',[
    (calculate_crit_region,CritRegionInput),(calculate_anomaly_crit_region,AnomalyCritRegionInput),
    (calculate_discharge_crit_region,DischargeCritRegionInput),(calculate_turbulence_crit_region,TurbulenceCritRegionInput)])
def test_probability_bounds_do_not_mutate_the_original_panel(calculator,input_type):
    original=input_type(crit_rate=1.4,crit_damage=2)
    assert calculator(original).value==3
    assert original.crit_rate==1.4
    assert calculator(input_type(crit_rate=-.2,crit_damage=2)).value==1
    assert calculator(input_type(crit_rate=.7,crit_damage=2)).value==pytest.approx(2.4)
