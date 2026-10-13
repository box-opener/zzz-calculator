import { isDriveDiscComplete, type DriveDiscConfig, type DriveDiscSlotSchema, type DriveDiscStatOption } from '../state/driveDiscState';
import type { DriveDiscPreview, DriveDiscSetInfo } from './DriveDiscCard';

type Props={ownerName:string;schema:DriveDiscSlotSchema;disc?:DriveDiscConfig;preview?:DriveDiscPreview;sets:readonly DriveDiscSetInfo[];options:readonly DriveDiscStatOption[];formatValue:(stat:string,value:number)=>string;onEdit:()=>void};
export default function DriveDiscTile({ownerName,schema,disc,preview,sets,options,formatValue,onEdit}:Props) {
  const set=sets.find(item=>item.set_id===disc?.set_id);
  const complete=Boolean(disc&&isDriveDiscComplete(disc));
  const status=complete?'完整':disc?'未完成':'空槽';
  const main=schema.main_stat_options.find(item=>item.stat_key===disc?.main_stat);
  const rolls=disc?.substats.reduce((total,row)=>total+row.roll_count,0)??0;
  return <button type="button" className={`disc-tile ${disc?'disc-tile-equipped':'disc-tile-empty'}`} aria-label={`编辑${ownerName}的${schema.slot}号驱动盘，${status}`} onClick={onEdit}>
    <span className="disc-tile-top"><span>SLOT {String(schema.slot).padStart(2,'0')}</span><small className={complete?'complete':disc?'incomplete':'muted'}>{status}</small></span>
    {disc?<><span className="disc-tile-set">{set&&<img src={set.icon_path} alt=""/>}<span><strong>{set?.display_name??disc.set_id}</strong><small>S 级 · 15 级</small></span></span>
      <span className="disc-tile-main"><span>{main?.label??'未选择主词条'}</span><strong>{main?formatValue(main.stat_key,main.value_per_roll):'—'}</strong></span>
      <span className="disc-tile-substats">{disc.substats.map(row=>{const option=options.find(item=>item.stat_key===row.stat);const value=preview?.substats.find(item=>item.stat_key===row.stat)?.value_per_roll??option?.value_per_roll;return <span key={row.stat}><span>{option?.label??row.stat}</span><b>{value===undefined?'—':formatValue(row.stat,value*row.roll_count)}</b><small>×{row.roll_count}</small></span>;})}</span>
      <span className="disc-tile-footer">副词条 {rolls} 次 · {disc.substats.length}/4 种 <span aria-hidden="true">↗</span></span>
    </>:<span className="disc-tile-empty-copy"><b aria-hidden="true">＋</b><strong>装配驱动盘</strong><small>选择套装与词条</small></span>}
  </button>;
}
