import {describe,expect,it} from 'vitest';
import {effectiveStatCounts,miyousheEffectiveStats,validateEffectiveStats} from './effectiveStats';
import {createCharacterConfig,parseCharacterConfig,serializeCharacterConfig} from './equipmentConfig';

describe('effective drive-disc stats',()=>{
  it('counts only selected substat rolls, excluding flat companions, penetration and main stats',()=>{
    const discs=[{slot:1,set_id:'31000',main_stat:'hp-flat',substats:[{stat:'attack-percent',roll_count:6},{stat:'attack-flat',roll_count:3},{stat:'penetration-flat',roll_count:2}]},
      {slot:2,set_id:'31000',main_stat:'attack-flat',substats:[{stat:'attack-percent',roll_count:4}]}];
    const summary=effectiveStatCounts(discs,['attack-percent']);
    expect(summary.total).toBe(10);expect(summary.counts['attack-flat']).toBe(3);expect(summary.counts['penetration-flat']).toBe(2);
    expect(effectiveStatCounts(discs,[]).total).toBe(0);
  });
  it('uses official selections including a deliberately empty scheme and distinguishes missing metadata',()=>{
    expect(miyousheEffectiveStats({equip_plan_info:{effective_substats:['crit-rate','penetration-flat','attack-flat','attack-percent']}})).toEqual(['crit-rate','attack-percent']);
    expect(miyousheEffectiveStats({equip_plan_info:{effective_substats:[]}})).toEqual([]);
    expect(miyousheEffectiveStats({equip_plan_info:{valid_property_cnt:37}})).toBeNull();
    expect(validateEffectiveStats(['crit-rate','crit-rate'])).toBeNull();
    expect(validateEffectiveStats(['penetration-flat'])).toBeNull();
  });
  it('exports and reloads user effective selections while accepting earlier v2 files',()=>{
    const config=createCharacterConfig('character:1431',60,'equipment-build',{core_level:7,cinema_level:0},null,[],null,['attack-percent','crit-rate']);
    const result=parseCharacterConfig(serializeCharacterConfig(config),'character:1431',{wengines:[],driveDiscSets:[]});
    expect(result.ok && result.config.effective_substats).toEqual(['attack-percent','crit-rate']);
    delete config.effective_substats;
    expect(parseCharacterConfig(serializeCharacterConfig(config),'character:1431',{wengines:[],driveDiscSets:[]}).ok).toBe(true);
    expect(parseCharacterConfig(JSON.stringify({...config,effective_substats:['penetration-flat']}),'character:1431',{wengines:[],driveDiscSets:[]}).ok).toBe(false);
  });
});
