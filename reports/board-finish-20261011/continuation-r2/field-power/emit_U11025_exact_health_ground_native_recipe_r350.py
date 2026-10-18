"""Only original health-wall deletes, six tracks and one ordinary barrel."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely.geometry import LineString
import contact_layout as C
import fast_contacts as F
from inventory import sha
from verify_source import parse,atom,child
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
R=H/'U11025-joint-health-return-legal-face-construction-r344';M=H/'U11025-actual-current-fill-materialized-source-proof-r346';A=H/'U11025-independent-full-caps-aperture-current-r348';O=H/'U11025-exact-health-ground-native-owned-recipe-r350';B=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb'
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();mr=json.loads((M/'receipt.json').read_text());assert mr['verdict']=='U11025_COMPLETE_COUPLED_HEALTH_GROUND_SOURCE_CONTACT_OLDREF_PASS_FULL_NATIVE_CURRENT_OPEN';ar=json.loads((A/'receipt.json').read_text());assert ar['errors']==[];d=pickle.loads((R/'proposed-discrete.pkl').read_bytes());old=json.loads((R/'exact-owned-old-track-rows.json').read_text());assert len(old)==11 and len(d['tracks'])==6 and len(d['vias'])==1;assert sha(B)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';_,chunks,_=C.O.C.pcbtext.split(B.read_bytes());by={C.O.C.pcbtext.chunk_uuid(ch):ch for ch in chunks if C.O.C.pcbtext.chunk_uuid(ch)};deletes=[];adds=[]
 for t in old:
  ch=by[t['uuid']];ast=parse(ch.decode('utf-8'));assert C.O.C.pcbtext.chunk_kind(ch)=='segment' and atom(ast,'net')==t['net'] and atom(ast,'layer')==t['layer'] and float(atom(ast,'width'))==t['w'];assert [float(x) for x in child(ast,'start')[1:]]==t['a'] and [float(x) for x in child(ast,'end')[1:]]==t['b'];f=O/(t['uuid']+'.delete-original-segment-chunk');f.write_bytes(ch);deletes.append({'kind':'segment','uuid':t['uuid'],'raw_net':t['net'],'chunk_path':str(f.resolve()),'exact_original_chunk_sha256':sha(f),'expected_geometry':t})
 for kind,rows in [('segment',d['tracks']),('via',d['vias'])]:
  for q in rows:
   assert q['uuid'] not in by
   if kind=='segment':text='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.2f)\n\t\t(layer "%s")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(*q['a'],*q['b'],q['w'],q['layer'],q['net'],q['uuid'])
   else:text='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.2f)\n\t\t(drill %.2f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "%s")\n\t\t(uuid "%s")\n\t)\n'%(q['x'],q['y'],q['d'],q['drill'],q['net'],q['uuid'])
   ch=text.encode('utf-8');assert C.O.C.pcbtext.chunk_uuid(ch)==q['uuid'] and C.O.C.pcbtext.chunk_kind(ch)==kind and atom(parse(text),'net')==q['net'];f=O/(q['uuid']+'.'+kind+'-chunk');f.write_bytes(ch);adds.append({'kind':kind,'uuid':q['uuid'],'raw_net':q['net'],'geometry':q,'chunk_path':str(f.resolve()),'chunk_sha256':sha(f)})
 _,h,_,_,_=pickle.loads((H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl').read_bytes());records,trees=F.build({**h,'zones':[]},layers={'F.Cu'});ids={q['uuid'] for q in old};outside=[]
 for t in old:
  body=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);contacts=[]
  for i in trees['F.Cu'].query(body,predicate='intersects'):
   q=records['F.Cu'][int(i)]
   if q['uuid'] in ids or q['net']!=t['net']:continue
   contacts.append({'kind':q['kind'],'uuid':q['uuid'],'raw_net':q['net'],'ref':q.get('ref'),'pin':q.get('pin'),'exact_physical_body_overlap_mm2':body.intersection(q['shape']).area})
  outside.append({'deleted_original_UUID':t['uuid'],'mandatory_distinct_retained_contacts':contacts})
 write(O/'exact-outside-health-contact-ledger.json',outside);flash=[{'uuid':v['uuid'],'raw_net':v['net'],'via_kind':'ordinary_through_not_micro','diameter_drill_mm':[.5,.2],'required_span':['F.Cu','B.Cu'],'required_ordinary_actual_flash_layers':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],'required_source_connected_contacts':['F.Cu','In1.Cu','In4.Cu'],'physical_own_drill_void_separate_from_original_native_outline':True,'no_new_owned_zone_outline':True,'actual_J11003_2_and_U11025_2_native_group_join_required':True} for v in d['vias']];write(O/'native-flash-and-annular-source-obligations.json',flash);remove={'native_base_board':str(B.resolve()),'native_base_board_sha256':sha(B),'delete_rows':deletes,'add_rows':[],'scope':'ONLY eleven exact old FIELD_HEALTH_B_N right/bottom wall segments; every retained outside contact mandatory'};write(O/'remove-only-recipe.json',remove);source=H/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';(O/'proposed-discrete.pkl').write_bytes((R/'proposed-discrete.pkl').read_bytes());receipt={'verdict':'FROZEN_U11025_11_HEALTH_DELETE_6_TRACK_1_ORDINARY_VIA_NATIVE_REVIEW_PACKET','native_base_board':str(B.resolve()),'native_base_board_sha256':sha(B),'fresh_native_source_export_sha256':sha(source),'source_nodes_or_component_or_pad_assignments_changed':False,'R344_nomination_receipt_SHA256':sha(R/'receipt.json'),'R346_all77_contact_7source_3oldref_4newhealth_fullref_receipt_SHA256':sha(M/'receipt.json'),'R348_independent_true_Cu_aperture_local_current_receipt_SHA256':sha(A/'receipt.json'),'delete_rows':deletes,'add_rows':adds,'exact_old_health_segment_deletes':11,'new_tracks':6,'new_ordinary_vias':1,'new_or_changed_zone_chunks':0,'owned_zone_role_cuts':0,'only_current_original_native_filled_record_own_drill_void_updates':2,'no_monitor_shutdown_OTHER_original_Cu_ownership':True,'outside_contact_ledger_sha256':sha(O/'exact-outside-health-contact-ledger.json'),'remove_only_recipe_sha256':sha(O/'remove-only-recipe.json'),'native_flash_obligations_sha256':sha(O/'native-flash-and-annular-source-obligations.json'),'proposed_discrete_sha256':sha(O/'proposed-discrete.pkl'),'full_local_ground_branch_A':.001,'full_input_A_return_A_unchanged':4.584429372438923,'all16DO_all12motor_full_loads_limits_unchanged':True,'native_source_all_discrete_DRU_true_Cu_flash_annular_source_DRC_allseverity_current':'MANDATORY_OPEN','model_is_not_a_stale_geometry_overlay':True,'all_other_original_native_chunks_preserved_by_operations':True,'no_alias_introduced':True,'native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',receipt);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'remove_recipe_SHA256':sha(O/'remove-only-recipe.json'),'new_discrete_SHA256':sha(O/'proposed-discrete.pkl')}),flush=True)
if __name__=='__main__':main()
