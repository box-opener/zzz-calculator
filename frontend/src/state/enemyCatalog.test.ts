import {describe,expect,it} from 'vitest';
import {enemyDefenseAtLevel} from './enemyCatalog';
describe('enemy level curve',()=>{
  it('reads source level index and ratio without rounding the calculation input',()=>{
    const variant={variant_id:'1',code_name:'',base_defense:54,defense_curve:[100,1588],curve_ratio:100,damage_resistance:{fire:.2},stun_multiplier:1.5,can_stun:true};
    expect(enemyDefenseAtLevel(variant,1)).toBe(54);expect(enemyDefenseAtLevel(variant,2)).toBe(857.52);
  });
});
