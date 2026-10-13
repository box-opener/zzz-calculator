import { describe, expect, it } from 'vitest';
import { editedTeamCharacter, rankedStatGains } from './workbench';
import type { StatGain } from '../components/SubstatGainPanel';

describe('independent equipment editing',()=>{
  it('keeps the edited support when the operator changes or the team reorders',()=>{
    expect(editedTeamCharacter(['a','b','c'],'b','a')).toBe('b');
    expect(editedTeamCharacter(['c','a','b'],'b','c')).toBe('b');
  });
  it('falls back to a surviving operator when the edited character is removed',()=>{
    expect(editedTeamCharacter(['a','c'],'b','c')).toBe('c');
    expect(editedTeamCharacter(['a'],'b','c')).toBe('a');
    expect(editedTeamCharacter([],'b','c')).toBeNull();
  });
});
const row=(stat:string,gain:number|null,complete=true,fullCrit=gain):StatGain=>({stat,label:stat,increment_label:'1',modes:{expected:{before:100,after:110,delta:10,gain_ratio:gain,complete},'full-crit':{before:100,after:110,delta:10,gain_ratio:fullCrit,complete}}});
describe('stat gain ranking',()=>{
  it('ranks by selected calculation mode, without mutating the response',()=>{
    const rows=[row('attack',.01,true,.03),row('crit',.03,true,.01),row('flat',.005)];
    expect(rankedStatGains(rows,'expected').map(item=>item.stat)).toEqual(['crit','attack','flat']);
    expect(rankedStatGains(rows,'full-crit').map(item=>item.stat)).toEqual(['attack','crit','flat']);
    expect(rows.map(item=>item.stat)).toEqual(['attack','crit','flat']);
  });
  it('retains incomplete and zero-baseline rows after known results, including zero or negative gains',()=>{
    const rows=[row('incomplete',.99,false),row('zero-base',null),row('negative',-.01),row('zero',0)];
    expect(rankedStatGains(rows,'expected').map(item=>item.stat)).toEqual(['zero','negative','incomplete','zero-base']);
    expect(rankedStatGains(rows,'missing').map(item=>item.stat)).toEqual(rows.map(item=>item.stat));
  });
});
