"""Frozen corrected U19008 recipe; no PCB/native execution or adoption."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,re,uuid
from pathlib import Path
from shapely.geometry import Polygon
from shapely import set_precision
from inventory import sha
from verify_source import parse,atom,children,child
from emit_logic_zones_r1 import render
import contact_layout as C
H=Path(__file__).resolve().parent;O=H/'u19008-corrected-native-owned-recipe-r102'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();dp=H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl';assert sha(dp)=='23c9a1f413da1723268203a6fe319a7b17505bba1df463136be671491c030a42';d=pickle.loads(dp.read_bytes());rp=H/'u19008-retained-logic-barrel-relocation-r95/owned-replacements.pkl';assert sha(rp)=='1d3052cb375c149f8243ea53b917ecdb0f014b9578446b9cf6a9396fc7a3fa81';replace=pickle.loads(rp.read_bytes());qp=H/'u19008-source-return-reference-r99/proposed-zones.pkl';assert sha(qp)=='728c56d5fc0ee145822e9d823883d6928cd65f80b1afd5696810e5aa281bded9';zones=pickle.loads(qp.read_bytes());assert len(d['vias'])==2 and len(d['tracks'])==7 and len(replace['vias'])==1 and len(replace['tracks'])==1
 board=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(board.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if C.O.C.pcbtext.chunk_uuid(ch)};nr=json.loads((H/'u19008-coupled-power-wall-nomination-r82/receipt.json').read_text());old=nr['owned_old_power_track'];ch=byid[old['uuid']];assert atom(parse(ch.decode()),'net')==old['net'] and atom(parse(ch.decode()),'locked')=='yes';path=O/(old['uuid']+'.delete-original-segment-chunk');path.write_bytes(ch);deletes=[{'kind':'segment','uuid':old['uuid'],'raw_net':old['net'],'geometry':old,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)}];repls=[]
 for kind,items in [('via',replace['vias']),('segment',replace['tracks'])]:
  for q in items:
   uid=q['uuid'];orig=byid[uid];assert C.O.C.pcbtext.chunk_kind(orig)==kind;ast=parse(orig.decode('utf-8'));assert atom(ast,'net')==q['net'];text=orig.decode('utf-8')
   if kind=='via':text,n=re.subn(r'\(at\s+[-\d.]+\s+[-\d.]+\)', '(at %.6f %.6f)'%(q['x'],q['y']),text);assert n==1 and float(atom(ast,'size'))==q['d'] and float(atom(ast,'drill'))==q['drill']
   else:text,n=re.subn(r'\(end\s+[-\d.]+\s+[-\d.]+\)', '(end %.6f %.6f)'%tuple(q['b']),text);assert n==1 and float(atom(ast,'width'))==q['w']
   a=parse(text);assert atom(a,'net')==q['net'] and atom(a,'uuid')==uid;op=O/(uid+'.original-'+kind+'-chunk');np=O/(uid+'.replacement-'+kind+'-chunk');op.write_bytes(orig);np.write_text(text,encoding='utf-8',newline='');repls.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'replacement_geometry':q,'original_chunk_path':str(op.resolve()),'original_chunk_sha256':sha(op),'replacement_chunk_path':str(np.resolve()),'replacement_chunk_sha256':sha(np),'only_owned_native_text_change':'at coordinates' if kind=='via' else 'end coordinates'})
 adds=[];raws={}
 for kind,items in [('via',d['vias']),('segment',d['tracks'])]:
  for q in items:
   uid=q['uuid'];assert uid not in byid;raws.setdefault(C.norm(q['net']),set()).add(q['net'])
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],uid)
   else:
    assert q['w']>=.20;lock='\t\t(locked yes)\n' if q['w']==.8 else '';text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n%s\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],lock,q['layer'],q['net'],uid)
   assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==uid;assert atom(parse(text),'net')==q['net'];path=O/(uid+'.'+kind+'-chunk');path.write_text(text,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':uid,'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 zr=[]
 for q in zones:
  sh=q.get('zone_outline_shape',q['shape']);assert set_precision(sh,1e-6).equals(sh);parts=[sh] if sh.geom_type=='Polygon' else [x for x in sh.geoms if x.geom_type=='Polygon'];parts=sorted(parts,key=lambda x:(-x.area,x.bounds))
  for i,part in enumerate(parts):
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'native-outer-'+str(i)));assert uid not in byid;txt=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','U19008 protected-power source return');ast=parse(txt);rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(ast,'polygon')];assert Polygon(rings[0],rings[1:]).symmetric_difference(part).area<1e-10;assert atom(ast,'net')==q['net'] and atom(ast,'priority')=='124';path=O/(uid+'.zone-chunk');path.write_text(txt,encoding='utf-8',newline='');zr.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'part_index':i,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'intended_polygon_area_mm2':part.area,'holes':len(rings)-1,'survives_min_015_interior_screen':not part.buffer(-.075).is_empty})
 assert all(len(v)==1 for v in raws.values());write(O/'outside-contact-ledger.json',json.loads((dp.parent/'outside-contact-ledger.json').read_text()));flash=[{'uuid':v['uuid'],'raw_net':v['net'],'required_outer':['B.Cu'],'required_inner_source_return_layers':'BOUND_BY_COMPLETE_JOINT_SOURCE_GRAPH'} for v in d['vias']]+[{'uuid':replace['vias'][0]['uuid'],'raw_net':replace['vias'][0]['net'],'retained_old_required_flash':['F.Cu','In1.Cu','In4.Cu'],'local_retained_annular_support_receipt_sha256':sha(H/'u19008-retained-logic-barrel-relocation-r95/receipt.json'),'J11001_source_join_unqualified':True}];write(O/'native-flash-obligations.json',flash)
 write(O/'receipt.json',{'verdict':'CORRECTED_SCOPED_NATIVE_RECIPE_FULL_JOINT_HOST_AND_NATIVE_CURRENT_GATES_OPEN','native_base_sha256':sha(board),'source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','exact_original_deletes':deletes,'exact_original_replacements':repls,'add_rows':adds,'zone_rows':zr,'new_vias':2,'new_segments':7,'new_zone_chunks':len(zr),'original_vias_moved':1,'original_stubs_replaced':1,'protected_power_width_preserved_mm':.8,'protected_power_lock_preserved':True,'R89_tree_receipt_sha256':sha(dp.parent/'receipt.json'),'R95_local_logic_move_receipt_sha256':sha(rp.parent/'receipt.json'),'R99_source_return_reference_receipt_sha256':sha(qp.parent/'receipt.json'),'outside_contact_ledger_sha256':sha(O/'outside-contact-ledger.json'),'native_flash_obligations_sha256':sha(O/'native-flash-obligations.json'),'supersedes_rejected_R85_recipe_not_adopted':True,'all_unowned_original_discrete_and_original_zone_definitions_remain_exact':True,'raw_aliases':0,'native_jobs':0,'board_written':False,'source_BOM_output_limits_control_rates_changed':False,'all_new_supply_source_return_root_no_loss_reference_aperture_current_drop_fault_native_fill_DRC_gates':'OPEN'});print(sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
