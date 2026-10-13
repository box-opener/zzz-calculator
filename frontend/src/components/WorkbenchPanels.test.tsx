import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import DriveDiscTile from './DriveDiscTile';
import SubstatGainPanel, { type StatGain } from './SubstatGainPanel';
import { formatDriveStatValue } from '../state/buildPreview';

describe('compact drive disc overview',()=>{
  it('shows current roll counts and values before an asynchronous preview arrives',()=>{
    const html=renderToStaticMarkup(<DriveDiscTile ownerName="角色" schema={{slot:1,main_stat_options:[{stat_key:'hp-flat',label:'生命值',value_per_roll:2200}]}} disc={{slot:1,set_id:'set',main_stat:'hp-flat',substats:[{stat:'attack-percent',roll_count:4},{stat:'attack-flat',roll_count:2},{stat:'crit-rate',roll_count:1},{stat:'penetration-flat',roll_count:1}]}} sets={[{set_id:'set',display_name:'真实套装',icon_path:'/set.png',two_piece_text:'',four_piece_text:''}]} options={[{stat_key:'attack-percent',label:'攻击力%',value_per_roll:.03},{stat_key:'attack-flat',label:'攻击力',value_per_roll:19},{stat_key:'crit-rate',label:'暴击率',value_per_roll:.024},{stat_key:'penetration-flat',label:'穿透值',value_per_roll:9}]} formatValue={formatDriveStatValue} onEdit={()=>undefined}/>);
    expect(html).toContain('编辑角色的1号驱动盘，完整');
    expect(html).toContain('12%');
    expect(html).toContain('38');
    expect(html).toContain('副词条 8 次 · 4/4 种');
  });
  it('keeps an empty slot actionable without inventing attributes',()=>{
    const html=renderToStaticMarkup(<DriveDiscTile ownerName="角色" schema={{slot:4,main_stat_options:[]}} sets={[]} options={[]} formatValue={formatDriveStatValue} onEdit={()=>undefined}/>);
    expect(html).toContain('编辑角色的4号驱动盘，空槽');
    expect(html).toContain('装配驱动盘');
    expect(html).not.toContain('disc-tile-main');
  });
});
describe('compact gain panel',()=>{
  it('surfaces incomplete values as unknown while keeping all rows accessible',()=>{
    const row=(stat:string,complete:boolean,ratio:number|null):StatGain=>({stat,label:stat,increment_label:'3%',modes:{expected:{complete,before:100,after:110,delta:10,gain_ratio:ratio}}});
    const html=renderToStaticMarkup(<SubstatGainPanel results={[{character_id:'a',rows:[row('incomplete',false,.99),row('zero-baseline',true,null),row('known',true,.1),row('extra',true,.05)]}]} names={{a:'当前角色'}} effective={{a:['known']}} stale operatorId="a"/>);
    expect(html).toContain('全部 4 项');
    expect(html).toContain('配置已修改');
    expect(html).toContain('incomplete');
    expect(html).toContain('未完整');
    expect(html).not.toContain('zero-baseline');
    expect(html).not.toContain('99%');
    expect(html).toContain('aria-pressed="true"');
  });
});
