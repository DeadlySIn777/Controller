"""Independent root pose and all absolute pad centers for six new+13 net moves."""
import json,math
from pathlib import Path
from inventory import HERE,PARSER,sha
from contact_layout import load,norm,O,S,BOARD
from verify_source import parse,children,child,atom
from export_ab_native import load_parser
OUT=HERE/'board-delta-r4-c92-pose/native-pose-ledger.json'
def pose(a):
 p=list(map(float,child(a,'at')[1:]));return p+[0.] if len(p)==2 else p
def absolute(a,p):
 x,y,deg=pose(a);v=list(map(float,child(p,'at')[1:3]));r=math.radians(deg)
 return [x+v[0]*math.cos(r)+v[1]*math.sin(r),y-v[0]*math.sin(r)+v[1]*math.cos(r)]
def main():
 assert not OUT.exists();g,b=load();r=json.loads((HERE/'board-delta-r3/receipt.json').read_text(encoding='utf-8'));native=O.C.inventory(BOARD.read_bytes())[3];olds={S.overlay_tool.base.ref_of(c):parse(c.decode('utf-8')) for c in native.values() if O.C.pcbtext.chunk_kind(c)=='footprint'}
 parser=load_parser(PARSER);net=HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net';fresh=parser['read_netlist'](net)
 rows=[];pairs=[(x['ref'],Path(x['path']),x['ref'],False) for x in r['existing_footprint_chunks']]
 pairs += [(x['ref'],HERE/('board-delta-r4-c92-pose' if x['ref']=='C11092' else 'board-delta-r3')/(x['ref']+'.footprint-chunk'),x['clone'],True) for x in r['new_footprint_chunks']]
 sbc=HERE.parent/'sbc-power/source-native-frozen-r2/receipt.json';s=json.loads(sbc.read_text(encoding='utf-8'));x=s['new_C11094'];pairs.append(('C11094',Path(x['new_native_chunk_path']),'C11088',True));assert len(pairs)==19
 for ref,path,clone,isnew in pairs:
  a=parse(path.read_text(encoding='utf-8'));old=olds[clone];p=pose(a);op=pose(old);padrows=[]
  oldpadlist=children(old,'pad');newpadlist=children(a,'pad');assert len(oldpadlist)==len(newpadlist)
  for oldp,np in zip(oldpadlist,newpadlist):
   uid=atom(oldp,'uuid');nativepad=next(q for q in g['pads'] if q['uuid']==uid);ap=absolute(a,np)
   # Native original absolute center transformed only by the intended rigid
   # pose must equal the independently evaluated new text pad coordinates.
   delta=math.radians(p[2]-op[2]);dx=nativepad['x']-op[0];dy=nativepad['y']-op[1];transform=[p[0]+dx*math.cos(delta)+dy*math.sin(delta),p[1]-dx*math.sin(delta)+dy*math.cos(delta)]
   assert math.dist(ap,transform)<.000003,(ref,np[1],ap,transform)
   raw=atom(np,'net') or ''
   if np[1]:assert norm(raw)==fresh['node_net'][(ref,np[1])],(ref,np[1],raw)
   padrows.append({'pin':np[1],'pad_uuid':atom(np,'uuid'),'raw_net':raw,'absolute_center_mm':[round(v,9) for v in ap],'local_at':child(np,'at')[1:],'actual_original_clone_native_flashes':sorted(nativepad['layers']),'source_named_pin':bool(np[1])})
  if not isnew:assert p==op and all(math.dist(q['absolute_center_mm'],[pp['x'],pp['y']])<.000003 for q,pp in zip(padrows,[next(x for x in g['pads'] if x['uuid']==atom(k,'uuid')) for k in oldpadlist]))
  rows.append({'ref':ref,'new':isnew,'clone':clone if isnew else None,'native_footprint_uuid':atom(a,'uuid'),'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'root_pose_mm_deg':p,'layer':atom(a,'layer'),'schematic_path':atom(a,'path'),'pads':padrows,'existing_pose_unchanged':not isnew})
 c92=next(r for r in rows if r['ref']=='C11092');assert c92['root_pose_mm_deg']==[80.5,210.5,0.];assert {p['pin']:p['absolute_center_mm'] for p in c92['pads']}=={'1':[79.025,210.5],'2':[81.975,210.5]}
 c94=next(r for r in rows if r['ref']=='C11094');assert {p['pin']:p['absolute_center_mm'] for p in c94['pads']}=={'1':[252.3,102.],'2':[246.7,102.]}
 result={'verdict':'PASS_HOST_ABSOLUTE_PAD_AND_SOURCE_LEDGER','new_part_count':6,'existing_net_move_footprint_count':13,'native_original_geometry_binding':b,'fresh_native_source_sha256':sha(net),'SBC_source_chunk_receipt_sha256':sha(sbc),'rows':rows,'coordinate_evaluation':'Exact text root/local pad coordinates; independently cross-checked against original native clone pad centers rigidly transformed with KiCad clockwise board coordinates. Omitting 0 rotation is explicitly interpreted as 0.','native_position_gate':'PENDING_ROOT_NATIVE_LOAD_COMPARE','native_jobs':0,'whole_board_written':False}
 OUT.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'ledger':str(OUT.resolve()),'sha256':sha(OUT),'new6':[(r['ref'],r['root_pose_mm_deg']) for r in rows if r['new']],'existing13_pose_unchanged':True}))
if __name__=='__main__':main()
