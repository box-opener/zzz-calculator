import { useState } from 'react';
import ModalFrame from './ModalFrame';
import { rankedStatGains } from '../state/workbench';

export type StatGain = { stat:string; label:string; increment_label:string; issue?:string;
  modes:Record<string,{before:number|null; after:number|null;delta:number|null;gain_ratio:number|null;complete:boolean}> };
export type CharacterStatGains = {character_id:string; rows:StatGain[]};
type Props={results:CharacterStatGains[];names:Record<string,string>;effective:Record<string,string[]>;stale:boolean;operatorId?:string|null};
const fmt=(value:number|null|undefined)=>value==null?'—':new Intl.NumberFormat('zh-CN',{maximumFractionDigits:2}).format(value);
const labels:Record<string,string>={'expected':'期望伤害','non-crit':'不暴击','full-crit':'满暴击'};
const signed=(value:number|null|undefined)=>value==null?'—':`${value>0?'+':''}${fmt(value)}`;
const ratio=(row:StatGain,mode:string)=>{const value=row.modes[mode];return value?.complete&&value.gain_ratio!=null?`${signed(value.gain_ratio*100)}%`:'—';};

export default function SubstatGainPanel({results,names,effective,stale,operatorId}:Props) {
  const [selectedMode,setMode]=useState('expected');
  const [dialog,setDialog]=useState<{owner:string;stat?:string}|null>(null);
  const modes=['non-crit','expected','full-crit'].filter(key=>results.some(result=>result.rows.some(row=>key in row.modes)));
  const mode=modes.includes(selectedMode)?selectedMode:modes.includes('expected')?'expected':modes[0]??'expected';
  const category=(owner:string,row:StatGain)=>['attack-flat','hp-flat','defense-flat','penetration-flat'].includes(row.stat)?'小词条':effective[owner]?.includes(row.stat)?'有效词条':'未选词条';
  const active=results.find(result=>result.character_id===dialog?.owner);
  const modeControls=<div className="gain-mode-switch" role="group" aria-label="收益比较模式">{modes.map(key=><button type="button" key={key} aria-pressed={mode===key} onClick={()=>setMode(key)}>{labels[key]??key}</button>)}</div>;
  return <section className="substat-gain-panel">
    <div className="section-heading compact"><div><h2>新增一条，能提升多少？</h2><p className="control-section-hint">只给指定队员增加一条 S 级副词条，比较整次计算总伤害。</p></div></div>
    {stale&&<p className="substat-gain-stale" role="status">配置已修改，重新计算后更新收益。</p>}
    {modeControls}
    {results.map((result,index)=>{const ranked=rankedStatGains(result.rows,mode);return <details open={operatorId?result.character_id===operatorId:index===0} className="substat-gain-character" key={result.character_id}>
      <summary><strong>{names[result.character_id]??result.character_id}</strong><small>{result.character_id===operatorId?'主控':'支援'}</small><b>{ranked[0]?ratio(ranked[0],mode):'—'}</b></summary>
      <table className="gain-short-table"><thead><tr><th>新增词条</th><th>分类</th><th>伤害增加</th><th>增益</th></tr></thead><tbody>{ranked.slice(0,3).map(row=><tr key={row.stat}>
        <td><button type="button" onClick={()=>setDialog({owner:result.character_id,stat:row.stat})}>{row.label}<small>+{row.increment_label}</small></button></td>
        <td><span className={`gain-category ${category(result.character_id,row)==='有效词条'?'gain-effective':''}`}>{category(result.character_id,row)}</span></td>
        <td>{row.modes[mode]?.complete?signed(row.modes[mode].delta):'未完整'}</td><td className="gain-ratio">{ratio(row,mode)}</td>
      </tr>)}</tbody></table>
      <div className="gain-footer"><small>理论比较 · 不修改驱动盘</small><button type="button" className="text-button" onClick={()=>setDialog({owner:result.character_id})}>全部 {result.rows.length} 项 ↗</button></div>
    </details>;})}
    {active&&dialog&&<ModalFrame wide title={`${names[active.character_id]??active.character_id} · 词条收益`} subtitle="每次仅增加一条副词条；基准与增加后伤害均来自本次计算。" onClose={()=>setDialog(null)}>
      {stale&&<p className="incomplete">当前配置已变化，此处仍为上次计算的结果。</p>}
      {modeControls}
      <div className="substat-gain-table-wrap"><table><thead><tr><th>新增词条</th><th>分类</th><th>增加后伤害</th><th>伤害增加</th><th>增益</th></tr></thead><tbody>{rankedStatGains(active.rows,mode).map(row=><tr key={row.stat}>
        <td><details open={dialog.stat===row.stat}><summary>{row.label} +{row.increment_label}</summary><div className="substat-gain-modes">{Object.entries(row.modes).map(([key,value])=><small key={key}>{labels[key]??key}：{value.complete?`${fmt(value.before)} → ${fmt(value.after)}（${value.gain_ratio==null?'基准为零，比例不可计算':`${signed(value.gain_ratio*100)}%`}）`:'结果不完整'}</small>)}</div>{row.issue&&<small className="incomplete">{row.issue}</small>}</details></td>
        <td>{category(active.character_id,row)}</td><td>{row.modes[mode]?.complete?fmt(row.modes[mode].after):'未完整结算'}</td><td>{row.modes[mode]?.complete?signed(row.modes[mode].delta):'—'}</td><td>{ratio(row,mode)}</td>
      </tr>)}</tbody></table></div>
    </ModalFrame>}
  </section>;
}
