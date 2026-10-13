export type EndgameMode = 'shiyu' | 'boss';
export type TargetMode = 'normal' | EndgameMode;
export type EnemyOverrides = {
  level?:number; initial_defense?:number; damage_resistance?:Record<string,number>;
  stun_vulnerability_bonus?:number; damage_reduction?:number; is_stunned?:boolean;
};
export type EndgameSelection = {
  mode:EndgameMode; season_id:string; stage_id:string; room_id:string; target_id:string;
  buff_ids?:string[]; states?:Record<string,number>; disabled_rules?:string[]; hp_tier?:number;
  enemy_overrides?:EnemyOverrides;
};
export type EndgameSeason = {season_id:string; name:string; begin:string; end:string; status:'current'|'history'|'future'|'permanent'};
export type EndgameBuff = {buff_id:string; title:string; text:string; selectable:boolean};
export type EndgameTarget = {target_id:string; enemy_id:string; variant_id:string; name:string; level:number; stats:Record<string,number>};
export type EndgameRoom = {room_id:string; name:string; waves:number; targets:EndgameTarget[]; buffs:EndgameBuff[]; selectable_buffs:EndgameBuff[]};
export type EndgameStage = {stage_id:string; name:string; difficulty:string; rooms:EndgameRoom[]; hp_tiers:{tier:number;hp_rate:number;points:number}[]};
export type EndgameDetail = {mode:EndgameMode;season_id:string;source_version:string;begin:string;end:string;page_url:string;snapshot_sha256:string;stages:EndgameStage[]};
export type EndgameEditor = {
  defaults:EndgameEditor['enemy'];
  buffs:EndgameBuff[];
  enemy:{enemy_id:string;variant_id:string;level:number;initial_defense:number|null;damage_resistance:Record<string,number>;stun_vulnerability_bonus:number|null;damage_reduction:number;is_stunned:boolean};
  provenance:{mode:string;season_id:string;source_version:string;maximum_hp:number;hp_tier:number;snapshot_sha256:string;target_name:string;missing_fields:string[];room_id:string;room_name:string;stage_name:string;buff_ids:string[]};
  controls:{key:string;label:string;maximum:number;value:number}[];
  clauses:{rule_id?:string;buff_id:string;status:string;message:string}[];
  rules:{rule_id:string;label:string;source_label:string;source_type:string;enabled:boolean}[];
};

export function selectStage(detail:EndgameDetail, stageId?:string):EndgameSelection {
  const stage=detail.stages.find(s=>s.stage_id===stageId) ?? detail.stages.at(-1);
  const room=stage?.rooms[0],target=room?.targets[0];
  if (!stage || !room || !target) throw new Error('该期数没有可计算的目标');
  return {mode:detail.mode,season_id:detail.season_id,stage_id:stage.stage_id,room_id:room.room_id,
    target_id:target.target_id,buff_ids:[],states:{},disabled_rules:[],hp_tier:stage.hp_tiers.length||1};
}
export function defaultSeason(rows:EndgameSeason[]):string {
  return (rows.find(r=>r.status==='current') ?? rows.find(r=>r.status==='history') ?? rows[0])?.season_id ?? '';
}
export function parseSceneConfig(text:string):{selection:EndgameSelection;snapshot_sha256:string} {
  const value=JSON.parse(text);
  if (value?.schema_version!=='zzz-scene-config-v1' || value?.source_version!=='3.2') throw new Error('场景文件版本不支持');
  const s=value.selection;
  if (!s || !['shiyu','boss'].includes(s.mode) || ['season_id','stage_id','room_id','target_id'].some(k=>typeof s[k]!=='string')
    || typeof value.snapshot_sha256!=='string' || !/^[a-f0-9]{64}$/.test(value.snapshot_sha256)) throw new Error('场景文件缺少合法的期数、目标或数据摘要');
  return {selection:s,snapshot_sha256:value.snapshot_sha256};
}
