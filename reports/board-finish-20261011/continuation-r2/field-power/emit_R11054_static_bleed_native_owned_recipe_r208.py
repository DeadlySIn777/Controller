"""Pin one FP root pose, two exact deletions, and the audited static/bleed feed."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,math,uuid
from pathlib import Path
from shapely.geometry import Polygon,Point
from shapely import set_precision
from inventory import sha
from verify_source import parse,atom,child,children
from emit_logic_zones_r1 import render
import contact_layout as C
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import freeze_owned_native_parts_r3 as F
O=H/'R11054-static-and-AUX-bleed-native-owned-recipe-r208'
def write(name,x):(O/name).write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();R=H/'R11054-static-and-bleed-full-contact-audit-r205';gate=json.loads((R/'receipt.json').read_text(encoding='utf-8'));assert gate['verdict']=='R11054_STATIC_AND_AUX_BLEED_SOURCE_CONTACT_REFERENCE_ANALYTIC_PASS'
 d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());assert len(d['vias'])==1 and len(d['tracks'])==3;zones=pickle.loads((R/'new-owned-zones.pkl').read_bytes());assert len(zones)==1
 board=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(board.read_bytes());byid={C.O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if C.O.C.pcbtext.chunk_uuid(ch)}
 old=next(ch for ch in chunks if C.O.C.pcbtext.chunk_kind(ch)=='footprint' and b'(property "Reference" "R11054"' in ch);a=parse(old.decode('utf-8'));uid=C.O.C.pcbtext.chunk_uuid(old);original_at=child(a,'at');assert [float(v) for v in original_at[1:]]==[221.,41.25,-90.]
 text=old.decode('utf-8');changed=[]
 for x,y in reversed(F.top_spans(text)):
  node=parse(text[x:y])
  if node[0]=='at':changed.append({'kind':'root_at_only','original_tokens':node,'replacement_tokens':['at','221','42.9','90']});text=text[:x]+'(at 221 42.9 90)'+text[y:]
 assert len(changed)==1;b=parse(text);assert [q for q in a if not isinstance(q,list) or q[0]!='at']==[q for q in b if not isinstance(q,list) or q[0]!='at']
 of=O/'R11054.original-exact-footprint-chunk';nf=O/'R11054.rotated-about-fault-pin-footprint-chunk';of.write_bytes(old);nf.write_text(text,encoding='utf-8',newline='');pads=[]
 for pad in children(b,'pad'):
  at=child(pad,'at');lx,ly=float(at[1]),float(at[2]);xy=[round(221+ly,6),round(42.9-lx,6)];pin=pad[1];expected={'1':[221,43.725],'2':[221,42.075]}[pin];assert xy==expected
  pads.append({'pin':pin,'pad_uuid':atom(pad,'uuid'),'raw_net':atom(pad,'net'),'absolute_center_mm':xy,'local_at_native':[float(v) for v in at[1:]],'local_shape':pad[3],'size_mm':[float(v) for v in child(pad,'size')[1:]],'declared_layers':child(pad,'layers')[1:],'native_local_AST_unchanged':True,'expected_actual_flashed_layers':['F.Cu'],'pin2_absolute_geometry_and_existing_fault_contacts_unchanged':pin=='2'})
 auth={'verdict':'EXACT_ROOT_POSE_ADAPTER_READY_NATIVE_POSE_AND_ALL_GATES_PENDING','ref':'R11054','uuid':uid,'native_parent_file':str(board.resolve()),'native_parent_sha256':sha(board),'source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','independent_host_gate_file':str((R/'receipt.json').resolve()),'independent_host_gate_sha256':sha(R/'receipt.json'),'exact_original_FP_chunk_sha256':sha(of),'exact_replacement_FP_chunk_sha256':sha(nf),'exact_changed_fields':changed,'all_other_native_AST_nodes_and_bytes_unchanged':True,'all_local_pad_UUID_raw_net_shape_size_mask_paste_and_angles_unchanged':True,'absolute_pad_coordinate_ledger':pads,'native_root_rotation_verification_required':True,'source_fault_timing_and_all_output_limits_unchanged':True,'board_written':False,'native_jobs':0};write('FP-authorization.json',auth)
 pose={'ref':'R11054','native_footprint_uuid':uid,'root_pose_mm_deg':[221,42.9,90],'layer':'F.Cu','schematic_path':atom(b,'path'),'chunk_path':str(nf.resolve()),'chunk_sha256':sha(nf),'pads':pads}
 fp={'uuid':uid,'ref':'R11054','original_chunk_file':str(of.resolve()),'original_chunk_sha256':sha(of),'replacement_chunk_file':str(nf.resolve()),'replacement_chunk_sha256':sha(nf),'authorizing_recipe_file':str((O/'FP-authorization.json').resolve()),'authorizing_recipe_sha256':sha(O/'FP-authorization.json'),'original_root_pose_mm_deg':[221,41.25,-90],'original_root_at_serialized_tokens':original_at[1:],'replacement_root_pose_mm_deg':[221,42.9,90],'native_pose_row':pose}
 oldledger=json.loads((R/'exact-moved-FP-pad-contact-ledger.json').read_text(encoding='utf-8'));deletes=[]
 for row in oldledger['old_2_tracks']:
  ch=byid[row['uuid']];ast=parse(ch.decode('utf-8'));assert C.O.C.pcbtext.chunk_kind(ch)=='segment' and atom(ast,'net')==row['net'] and atom(ast,'layer')==row['layer'];assert [float(v) for v in child(ast,'start')[1:]]==row['a'] and [float(v) for v in child(ast,'end')[1:]]==row['b'] and float(atom(ast,'width'))==row['w'];path=O/(row['uuid']+'.delete-original-segment-chunk');path.write_bytes(ch);deletes.append({'kind':'segment','uuid':row['uuid'],'raw_net':row['net'],'chunk_path':str(path.resolve()),'exact_original_chunk_sha256':sha(path),'expected_geometry':row})
 adds=[]
 for kind,rows in [('via',d['vias']),('segment',d['tracks'])]:
  for q in rows:
   assert q['uuid'] not in byid
   if kind=='via':txt='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],q['uuid'])
   else:assert q['w']>=.2;txt='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],q['uuid'])
   assert C.O.C.pcbtext.chunk_uuid(txt.encode())==q['uuid'] and atom(parse(txt),'net')==q['net'];path=O/(q['uuid']+'.'+kind+'-chunk');path.write_text(txt,encoding='utf-8',newline='');adds.append({'kind':kind,'uuid':q['uuid'],'raw_net':q['net'],'geometry':q,'chunk_path':str(path.resolve()),'chunk_sha256':sha(path)})
 zr=[]
 for q in zones:
  shape=q['zone_outline_shape'];assert set_precision(shape,1e-6).equals(shape);parts=[shape] if shape.geom_type=='Polygon' else [p for p in shape.geoms if p.geom_type=='Polygon']
  for i,part in enumerate(sorted(parts,key=lambda p:(-p.area,p.bounds))):
   uid=q['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(q['uuid']),'native-outer-'+str(i)));txt=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','R11055 retained AUX5 bleed source feed');ast=parse(txt);rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(ast,'polygon')];assert Polygon(rings[0],rings[1:]).symmetric_difference(part).area<1e-10 and atom(ast,'priority')=='124';path=O/(uid+'.zone-chunk');path.write_text(txt,encoding='utf-8',newline='');zr.append({'uuid':uid,'proposal_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'chunk_path':str(path.resolve()),'chunk_sha256':sha(path),'part_index':i,'holes':len(rings)-1})
 v=d['vias'][0];q=zones[0];assert q['zone_outline_shape'].covers(Point(v['x'],v['y']));flash={'uuid':v['uuid'],'raw_net':v['net'],'xy':[v['x'],v['y']],'NEW_ordinary_barrel_absent_original_eedf':True,'required_actual_native_flash_layers':['F.Cu','In1.Cu'],'every_SMD_and_hole_drill_gap_required_mm':.275,'all6_foreign_Cu_gate_required':True,'intended_outline_contains_own_barrel_center':True,'physical_shape_retains_actual_drill_void':not q['shape'].covers(Point(v['x'],v['y']))};write('native-flash-obligations.json',[flash]);write('remove-only-recipe.json',{'native_base_board':str(board.resolve()),'native_base_board_sha256':sha(board),'delete_rows':deletes,'add_rows':[],'scope':'Two exact AUX5 bleed-branch F wall tracks; full retained endpoint contacts preserved via separate source feed'})
 for name in ('proposed-discrete.pkl','new-owned-zones.pkl','exact-latest-owned-return-cutter-replay.json'):(O/name).write_bytes((R/name).read_bytes())
 write('receipt.json',{'verdict':'EXACT_NATIVE_OWNED_RECIPE_HOST_GATES_PASS_NATIVE_CURRENT_FAULT_PENDING','parent_native_board_sha256':sha(board),'fresh_native_source_export_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','independent_host_gate_file':str((R/'receipt.json').resolve()),'independent_host_gate_sha256':sha(R/'receipt.json'),'native_existing_owned_footprint_replacement_rows':[fp],'delete_rows':deletes,'add_rows':adds,'zone_rows':zr,'remove_only_recipe_sha256':sha(O/'remove-only-recipe.json'),'native_flash_obligations_sha256':sha(O/'native-flash-obligations.json'),'owned_return_cuts_replay_file':str((O/'exact-latest-owned-return-cutter-replay.json').resolve()),'original_byte_bound_deletes_only':True,'all_motor_AUX5_output_limits_and_fault_roles_unchanged':True,'full_sheet_barrel_upstream_thermal_transient_fault_and_native_gates':'OPEN','board_written':False,'native_jobs':0});assert sha(board)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';print('R208',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
