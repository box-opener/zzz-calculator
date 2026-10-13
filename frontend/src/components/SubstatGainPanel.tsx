export type StatGain = { stat:string; label:string; increment_label:string; issue?:string;
  modes:Record<string,{before:number|null; after:number|null;delta:number|null;gain_ratio:number|null;complete:boolean}> };
export type CharacterStatGains = {character_id:string; rows:StatGain[]};
type Props={results:CharacterStatGains[];names:Record<string,string>;effective:Record<string,string[]>; stale:boolean};
const fmt=(v:number|null|undefined)=>v==null?'—':new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2}).format(v);
export default function SubstatGainPanel({results,names,effective,stale}:Props) {
  return <section className="substat-gain-panel"><div className="section-heading compact"><div><p className="eyebrow">ONE MORE SUBSTAT</p><h2>新增一条副词条的伤害收益</h2><p className="control-section-hint">每次只增加一条 S 级副词条，其他装备、规则和目标保持本次计算的设置。下表以期望伤害比较，展开可查看不暴击与满暴击结果。</p></div></div>
    {stale && <p className="substat-gain-stale" role="status">配置已修改，重新计算后更新收益。</p>}
    {results.map(result=><details open className="substat-gain-character" key={result.character_id}><summary>{names[result.character_id]??result.character_id}</summary>
      <div className="substat-gain-table-wrap"><table><thead><tr><th>新增词条</th><th>分类</th><th>增加后伤害</th><th>伤害增加</th><th>增益</th></tr></thead><tbody>{result.rows.map(row=>{
        const mode=row.modes.expected;const small=['attack-flat','hp-flat','defense-flat','penetration-flat'].includes(row.stat);
        return <tr key={row.stat}><td><details><summary>{row.label} +{row.increment_label}</summary><div className="substat-gain-modes">{Object.entries(row.modes).map(([key,m])=><small key={key}>{({'expected':'期望','non-crit':'不暴击','full-crit':'满暴击'} as Record<string,string>)[key]??key}：{m.complete?`${fmt(m.before)} → ${fmt(m.after)}（${m.gain_ratio==null?'基准为零':`${fmt(m.gain_ratio*100)}%`}）`:'结果不完整'}</small>)}</div>{row.issue && <small>{row.issue}</small>}</details></td>
          <td>{small?'小词条':effective[result.character_id]?.includes(row.stat)?'有效词条':'未选词条'}</td><td>{mode?.complete?fmt(mode.after):'未完整结算'}</td><td>{mode?.complete?fmt(mode.delta):'—'}</td><td>{mode?.complete && mode.gain_ratio!=null?`${fmt(mode.gain_ratio*100)}%`:'—'}</td></tr>;
      })}</tbody></table></div></details>)}
  </section>;
}
