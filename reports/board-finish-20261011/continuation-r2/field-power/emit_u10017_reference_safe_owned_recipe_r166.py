"""Exact one-wall deletion and three-track/one-barrel supply bypass recipe."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,uuid
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely import set_precision
from inventory import sha
from verify_source import parse,atom,child,children
from emit_logic_zones_r1 import render
import contact_layout as C
H=Path(__file__).resolve().parent;O=H/'u10017-reference-safe-native-owned-recipe-r166'
def write(name,x):(O/name).write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();R=H/'u17-u10017-reference-safe-incremental-audit-r162';assert sha(R/'receipt.json')=='10bae09e7343683d918e333a19e43b90906b15fb794fcdd7be401ef7176b609a'
 d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());u17=pickle.loads((H/'u11017-dead-spur-native-owned-recipe-r138/proposed-tracks.pkl').read_bytes());u17ids={t['uuid'] for t in u17};d['tracks']=[t for t in d['tracks'] if t['uuid'] not in u17ids];assert len(d['tracks'])==3 and len(d['vias'])==1
 zones=pickle.loads((R/'new-owned-zones.pkl').read_bytes());assert len(zones)==1 and zones[0]['uuid']=='e8ec0287-e6d1-597d-8ad8-c4ab74280f6c'
 board=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(board.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if C.O.C.pcbtext.chunk_uuid(ch)}
 uid='5c6ebac9-c76a-41f1-8cb8-45e2321f2e89';ch=byid[uid];ast=parse(ch.decode('utf-8'));assert C.O.C.pcbtext.chunk_kind(ch)=='segment' and atom(ast,'net')=='/motherboard_power_entry{slash}FIELD_B_24V_PROTECTED' and atom(ast,'layer')=='F.Cu' and atom(ast,'width')=='0.3' and atom(ast,'locked')=='yes';assert [float(x) for x in child(ast,'start')[1:]]==[147.75,99.35] and [float(x) for x in child(ast,'end')[1:]]==[147.75,104.25]
 path=O/(uid+'.delete-original-segment-chunk');path.write_bytes(ch);deletes=[{'kind':'segment','uuid':uid,'raw_net':atom(ast,'net'),'chunk_path':str(path.resolve()),'exact_original_chunk_sha256':sha(path),'expected_geometry':{'a':[147.75,99.35],'b':[147.75,104.25],'width_mm':.3,'layer':'F.Cu','locked':True}}]
 adds=[];raws={}
 for kind,rows in [('via',d['vias']),('segment',d['tracks'])]:
  for q in rows:
   assert q['uuid'] not in byid;raws.setdefault(C.norm(q['net']),set()).add(q['net'])
   if kind=='via':text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],q['uuid'])
   else:
    assert q['w']>=.2;text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],q['uuid'])
   assert C.O.C.pcbtext.chunk_kind(text.encode())==kind and C.O.C.pcbtext.chunk_uuid(text.encode())==q['uuid'] and atom(parse(text),'net')==q['net'];path=O/(q['uuid']+'.'+kind+'-chunk');path.write_text(text,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':q['uuid'],'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 assert all(len(x)==1 for x in raws.values());zr=[]
 for q in zones:
  sh=q.get('zone_outline_shape',q['shape']);assert set_precision(sh,1e-6).equals(sh);parts=[sh] if sh.geom_type=='Polygon' else [p for p in sh.geoms if p.geom_type=='Polygon'];parts=sorted(parts,key=lambda p:(-p.area,p.bounds))
  for i,part in enumerate(parts):
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'native-outer-'+str(i)));txt=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','U10017 reference-safe protected source bypass');a=parse(txt);rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(a,'polygon')];assert Polygon(rings[0],rings[1:]).symmetric_difference(part).area<1e-10 and atom(a,'priority')=='124';path=O/(uid+'.zone-chunk');path.write_text(txt,encoding='utf-8',newline='');zr.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'part_index':i,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'intended_polygon_area_mm2':part.area,'holes':len(rings)-1,'survives_native_min015_interior_screen':not part.buffer(-.075).is_empty})
 centers=[('c55416b9-e522-5cbf-9523-ddb093be9249',[142.216942,106.397108],['F.Cu','In2.Cu']),('a7ee4fd8-200f-5a6e-968d-a2cd93a393b1',[143.820744,96.625855],['F.Cu','In1.Cu','In2.Cu'])]
 # Resolve the full root-owned barrel UUID from the frozen R160 nomination.
 nom=json.loads((H/'u10017-reference-safe-source-bypass-nominee-r160/receipt.json').read_text(encoding='utf-8'));source_uuid=next((r.get('source_via_uuid') for r in nom['rows'] if r.get('source_via_uuid')),None)
 root_d=pickle.loads((H.parent/'protected24-on-corrected-core-r9/proposed-discrete.pkl').read_bytes());source=next(v for v in root_d['vias'] if abs(v['x']-143.820744)<1e-7 and abs(v['y']-96.625855)<1e-7);centers[1]=(source['uuid'],[source['x'],source['y']],centers[1][2]);flashes=[]
 q=zones[0]
 for uid,xy,layers in centers:
  covered=q.get('zone_outline_shape',q['shape']).covers(Point(xy));assert covered,(uid,'intended own source landing center absent');flashes.append({'uuid':uid,'raw_net':q['net'],'xy':xy,'required_native_actual_flash_layers':layers,'new_plane_required_actual_source_contact_layer':'In2.Cu','intended_outline_contains_barrel_center':covered,'physical_shape_retains_actual_drill_void':not q['shape'].covers(Point(xy)),'old_root_via_required_F_In1_retained':uid==source['uuid'],'native_full_refill_annular_source_test_required':True})
 (O/'proposed-discrete.pkl').write_bytes(pickle.dumps(d,protocol=5));(O/'new-owned-zones.pkl').write_bytes((R/'new-owned-zones.pkl').read_bytes());write('native-flash-obligations.json',flashes);write('remove-only-recipe.json',{'native_base_board':str(board.resolve()),'native_base_board_sha256':sha(board),'delete_rows':deletes,'add_rows':[],'scope':'One exact U10017 protected F wall; bypass/new VDD and every retained outside source/contact mandatory'})
 write('receipt.json',{'verdict':'FROZEN_NATIVE_RECIPE_INCREMENTAL_HOST_PASS_FULL_JOINT_CURRENT_NATIVE_OPEN','native_base_board_sha256':sha(board),'fresh_native_source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','incremental_R162_receipt_sha256':sha(R/'receipt.json'),'delete_rows':deletes,'add_rows':adds,'zone_rows':zr,'remove_only_recipe_sha256':sha(O/'remove-only-recipe.json'),'proposed_discrete_sha256':sha(O/'proposed-discrete.pkl'),'new_owned_zones_sha256':sha(O/'new-owned-zones.pkl'),'native_flash_obligations_sha256':sha(O/'native-flash-obligations.json'),'separate_U17_recipe_preserved':str((H/'u11017-dead-spur-native-owned-recipe-r138/receipt.json').resolve()),'all_unowned_native_discrete_original_zone_definitions_unchanged':True,'actual_full_nine_pad_load_allocation_barrel_current_mesh_drop_thermal_fault_native_gates':'OPEN','R160_2_003_A_is_TPS274_diagnostic_reservation_not_complete_branch_capacity':True,'baseline_R142_IO3_split_and_precision_replay_OPEN':True,'native_jobs':0,'board_written':False})
 print('R166',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
