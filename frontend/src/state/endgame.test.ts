import {describe,it,expect} from 'vitest';
import {defaultSeason,parseSceneConfig,selectStage,type EndgameDetail,type EndgameSeason} from './endgame';
describe('endgame saved scenes and current season',()=>{
  const seasons:EndgameSeason[]=[
    {season_id:'future',name:'',begin:'2026-10-16',end:'2026-10-30',status:'future'},
    {season_id:'current',name:'',begin:'2026-10-02',end:'2026-10-16',status:'current'},
    {season_id:'past',name:'',begin:'2026-09-18',end:'2026-10-02',status:'history'},
  ];
  it('selects active formal season even when a future season is first',()=>{
    expect(defaultSeason(seasons)).toBe('current');expect(defaultSeason(seasons.filter(s=>s.status!=='current'))).toBe('past');
  });
  it('stage changes clear trigger facts and excluded clauses from the previous room',()=>{
    const room={room_id:'room-3',name:'第三房间',waves:2,buffs:[],selectable_buffs:[],targets:[{target_id:'target',enemy_id:'enemy:1',variant_id:'2',name:'boss',level:70,stats:{}}]};
    const detail:EndgameDetail={mode:'shiyu',season_id:'62058',source_version:'3.2',begin:'',end:'',page_url:'',snapshot_sha256:'a'.repeat(64),stages:[{stage_id:'fifth',name:'第五防线',difficulty:'防线',rooms:[room],hp_tiers:[]}]};
    expect(selectStage(detail)).toEqual({mode:'shiyu',season_id:'62058',stage_id:'fifth',room_id:'room-3',target_id:'target',buff_ids:[],states:{},disabled_rules:[],hp_tier:1});
  });
  it('retains named overrides and trigger states without changing character config format',()=>{
    const selection={mode:'boss',season_id:'690471',stage_id:'stage',room_id:'room',target_id:'target',states:{'buff:trigger:character:1431':1},hp_tier:24,enemy_overrides:{damage_resistance:{luminance:0}}};
    const config={schema_version:'zzz-scene-config-v1',source_version:'3.2',snapshot_sha256:'a'.repeat(64),selection};
    expect(parseSceneConfig(JSON.stringify(config)).selection).toEqual(selection);
    expect(()=>parseSceneConfig(JSON.stringify({...config,source_version:'3.3.12'}))).toThrow();
    expect(()=>parseSceneConfig(JSON.stringify({...config,snapshot_sha256:'changed'}))).toThrow();
    expect(()=>parseSceneConfig(JSON.stringify({schema_version:'zzz-character-config-v2'}))).toThrow();
  });
});
