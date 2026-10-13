import {useEffect,useRef,useState} from 'react';
import NumberField from './NumberField';
import {defaultSeason,parseSceneConfig,selectStage,type EndgameMode,type EndgameSelection,type EndgameSeason,type EndgameDetail,type EndgameEditor,type EnemyOverrides} from '../state/endgame';

async function request<T>(url:string, options:RequestInit={}):Promise<T> {
  const response=await fetch(url,{headers:{'Content-Type':'application/json'},...options});
  const value=await response.json();
  if (!response.ok) throw new Error(value.diagnostics?.[0]?.message ?? '终局数据读取失败');
  return value;
}
type Props={mode:EndgameMode;teamPayload:Record<string,unknown>;enemyOverrides:EnemyOverrides;
  onChange:(selection:EndgameSelection|null,editor:EndgameEditor|null)=>void};

export default function EndgamePanel({mode,teamPayload,enemyOverrides,onChange}:Props) {
  const [seasons,setSeasons]=useState<EndgameSeason[]>([]);
  const [seasonId,setSeasonId]=useState('');
  const [detail,setDetail]=useState<EndgameDetail|null>(null);
  const [selection,setSelection]=useState<EndgameSelection|null>(null);
  const [editor,setEditor]=useState<EndgameEditor|null>(null);
  const [issue,setIssue]=useState('');
  const [busy,setBusy]=useState(false);
  const imported=useRef<ReturnType<typeof parseSceneConfig>|null>(null);
  const inputRef=useRef<HTMLInputElement|null>(null);
  const notify=useRef(onChange);notify.current=onChange;
  const teamKey=JSON.stringify(teamPayload);
  const identityKey=JSON.stringify([...(teamPayload.team_character_ids as string[]??[])].sort());
  const oldTeam=useRef(identityKey);
  useEffect(()=>{
    if (oldTeam.current!==identityKey) {oldTeam.current=identityKey;setSelection(s=>s?{...s,states:{},disabled_rules:[]}:s);}
  },[identityKey]);
  useEffect(()=>{
    const controller=new AbortController();setIssue('');setSeasons([]);setSeasonId('');setDetail(null);setSelection(null);notify.current(null,null);
    request<{seasons:EndgameSeason[]}>(`/api/v1/endgame/seasons?mode=${mode}`,{signal:controller.signal})
      .then(data=>{setSeasons(data.seasons);setSeasonId(defaultSeason(data.seasons));})
      .catch(e=>{if(!controller.signal.aborted)setIssue(e.message);});
    return ()=>controller.abort();
  },[mode]);
  useEffect(()=>{
    if(!seasonId)return;
    const controller=new AbortController();setBusy(true);setIssue('');setDetail(null);setSelection(null);setEditor(null);notify.current(null,null);
    request<EndgameDetail>(`/api/v1/endgame/seasons/${mode}/${seasonId}`,{signal:controller.signal})
      .then(data=>{
        const pending=imported.current;
        if(pending && pending.selection.season_id===seasonId && pending.snapshot_sha256!==data.snapshot_sha256)throw new Error('场景快照摘要与当前数据不同，无法保证重现');
        setDetail(data);setSelection(pending?.selection.season_id===seasonId?pending.selection:selectStage(data));imported.current=null;
      }).catch(e=>{if(!controller.signal.aborted)setIssue(e.message);})
      .finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    return ()=>controller.abort();
  },[mode,seasonId]);
  useEffect(()=>{
    if(!selection || !teamPayload.primary_character_id){notify.current(null,null);return;}
    const controller=new AbortController();setBusy(true);setIssue('');notify.current(null,null);
    request<EndgameEditor>('/api/v1/endgame/editor',{method:'POST',body:JSON.stringify({...teamPayload,endgame_selection:selection}),signal:controller.signal})
      .then(data=>{setEditor(data);notify.current(selection,data);})
      .catch(e=>{if(!controller.signal.aborted){setIssue(e.message);}})
      .finally(()=>{if(!controller.signal.aborted)setBusy(false);});
    return ()=>controller.abort();
  },[selection,teamKey]);
  const stage=detail?.stages.find(s=>s.stage_id===selection?.stage_id);
  const room=stage?.rooms.find(r=>r.room_id===selection?.room_id);
  const patch=(values:Partial<EndgameSelection>)=>setSelection(s=>s?{...s,...values}:s);
  const selectRoom=(id:string)=>{
    const next=stage?.rooms.find(r=>r.room_id===id);if(next?.targets[0])patch({room_id:id,target_id:next.targets[0].target_id,states:{},disabled_rules:[],buff_ids:[],enemy_overrides:undefined});
  };
  const exportScene=()=>{
    if(!selection || !detail)return;
    const config={schema_version:'zzz-scene-config-v1',source_version:detail.source_version,snapshot_sha256:detail.snapshot_sha256,selection:{...selection,enemy_overrides:enemyOverrides}};
    const url=URL.createObjectURL(new Blob([JSON.stringify(config,null,2)],{type:'application/json'}));
    const anchor=document.createElement('a');anchor.href=url;anchor.download=`zzz-scene-${mode}-${seasonId}.json`;anchor.click();URL.revokeObjectURL(url);
  };
  const importScene=async(file:File)=>{
    try{
      const value=parseSceneConfig(await file.text());if(value.selection.mode!==mode)throw new Error('请先切换到文件对应的终局模式');
      if(!seasons.some(s=>s.season_id===value.selection.season_id))throw new Error('该期数未包含在本地正式数据中');
      if(value.selection.season_id===seasonId){if(value.snapshot_sha256!==detail?.snapshot_sha256)throw new Error('快照摘要不一致');setSelection(value.selection);}
      else {imported.current=value;setSeasonId(value.selection.season_id);}
      setIssue('');
    }catch(e){setIssue(e instanceof Error?e.message:'场景文件无效');}
  };
  return <div className="endgame-panel">
    <label><span>正式期数</span><select value={seasonId} onChange={e=>setSeasonId(e.target.value)}>{seasons.map(s=><option key={s.season_id} value={s.season_id}>{s.begin?s.begin.slice(0,10):s.name} · {s.season_id} · {s.status==='current'?'进行中':s.status==='future'?'即将开放':s.status==='permanent'?'常驻':'历史'}</option>)}</select></label>
    {detail && selection && <>
      <p className="control-section-hint">{detail.begin?`${detail.begin} — ${detail.end}（国服）`:'常驻节点'} · 正式版 {detail.source_version} · <a href={detail.page_url} target="_blank" rel="noreferrer">查看本期资料</a></p>
      <label><span>{mode==='boss'?'难度与试炼':'防线'}</span><select value={selection.stage_id} onChange={e=>{setSelection(selectStage(detail,e.target.value));}}>{detail.stages.map(s=><option key={s.stage_id} value={s.stage_id}>{s.difficulty} · {s.name}</option>)}</select></label>
      <label><span>房间</span><select value={selection.room_id} onChange={e=>selectRoom(e.target.value)}>{stage?.rooms.map((r,i)=><option key={r.room_id} value={r.room_id}>{r.name} · {i+1}</option>)}</select></label>
      <label><span>本次攻击目标</span><select value={selection.target_id} onChange={e=>patch({target_id:e.target.value,states:{},disabled_rules:[],enemy_overrides:undefined})}>{room?.targets.map(t=><option key={t.target_id} value={t.target_id}>{t.name} · 变体 {t.variant_id}</option>)}</select></label>
      <p className="control-section-hint">波次 ×{room?.waves} · 源提供房间合并目标，本次选择其中一个目标计算。</p>
      {!!stage?.hp_tiers.length && <NumberField label="生命档位" value={selection.hp_tier??stage.hp_tiers.length} integer min={1} max={stage.hp_tiers.length} helper="生命档位独立于战斗等级" onCommit={value=>patch({hp_tier:value})}/>}
      {!!room?.selectable_buffs.length && <label><span>可选场地增益</span><select value={selection.buff_ids?.[0]??''} onChange={e=>patch({buff_ids:e.target.value?[e.target.value]:[],states:{},disabled_rules:[]})}><option value="">不应用可选增益（对照）</option>{room.selectable_buffs.map(b=><option key={b.buff_id} value={b.buff_id}>{b.title}</option>)}</select></label>}
    </>}
    {busy && <p className="muted">读取场景与场地规则…</p>}
    {issue && <p role="alert" className="incomplete">{issue}</p>}
    {editor && !busy && <>
      <p className="control-section-hint">目标最大生命值 {editor.provenance.maximum_hp.toLocaleString()} · 等级 {editor.enemy.level} · 防御 {editor.enemy.initial_defense?.toFixed(2)??'未提供'}</p>
      {editor.controls.map(control=>control.maximum===1?<label className="check-field" key={control.key}><span>{control.label}</span><input type="checkbox" checked={(selection?.states?.[control.key]??0)>0} onChange={e=>patch({states:{...selection?.states,[control.key]:e.target.checked?1:0}})}/></label>:<NumberField key={control.key} label={control.label} value={selection?.states?.[control.key]??0} integer min={0} max={control.maximum} helper={`当前层数 0–${control.maximum}`} onCommit={value=>patch({states:{...selection?.states,[control.key]:value}})}/>)}
      <details><summary>场地原文与计算范围</summary>{editor.buffs.map(b=><div className="endgame-buff-text" key={b.buff_id}><strong>{b.title}</strong><p>{b.text}</p></div>)}
        {[...new Set(editor.clauses.filter(c=>c.status!=='implemented').map(c=>c.message))].map(message=><p className="control-section-hint" key={message}>{message}</p>)}
        <p className="control-section-hint">计分、回能、积蓄耗时与持续时间不模拟。未知条款只影响与其匹配的伤害；锐化条款不会代替贯穿伤害。</p>
      </details>
      <details><summary>场地规则开关（对照计算）</summary>{editor.rules.map(rule=><label className="check-field" key={rule.rule_id}><span>{rule.label}</span><input type="checkbox" checked={!selection?.disabled_rules?.includes(rule.rule_id)} onChange={e=>patch({disabled_rules:e.target.checked?(selection?.disabled_rules??[]).filter(id=>id!==rule.rule_id):[...selection?.disabled_rules??[],rule.rule_id]})}/></label>)}</details>
    </>}
    <div className="enemy-picker-actions"><button type="button" className="secondary-button" disabled={!editor||busy} onClick={exportScene}>导出场景</button><button type="button" className="secondary-button" onClick={()=>inputRef.current?.click()}>导入场景</button><input ref={inputRef} type="file" accept=".json,application/json" hidden onChange={e=>{const file=e.target.files?.[0];if(file)void importScene(file);e.target.value='';}}/></div>
    <p className="control-section-hint">场景文件保存目标、Buff、状态与属性覆写。队伍和装备沿用当前配置。</p>
  </div>;
}
