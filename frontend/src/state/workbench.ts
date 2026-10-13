import type { StatGain } from '../components/SubstatGainPanel';

export function editedTeamCharacter(team:string[],selected:string|null,operator:string|null):string|null {
  return selected&&team.includes(selected)?selected:operator&&team.includes(operator)?operator:team[0]??null;
}

/** Incomplete or zero-baseline comparisons have no rankable ratio. */
export function rankedStatGains(rows:StatGain[],mode:string):StatGain[] {
  return [...rows].sort((a,b)=>{
    const first=a.modes[mode],second=b.modes[mode];
    const x=first?.complete?first.gain_ratio:null,y=second?.complete?second.gain_ratio:null;
    return x==null?y==null?0:1:y==null?-1:y-x;
  });
}
