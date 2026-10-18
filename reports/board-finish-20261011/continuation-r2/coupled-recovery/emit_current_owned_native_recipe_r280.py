"""Parameterised exact-current recipe emitter; no board/native operation.

Only the supplied immutable model owns geometry. Supplemental native profiles
must be explicit, role/hash/receipt bound; legacy inventories never own q.
"""
import os,psutil
for env_name in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):os.environ[env_name]="2"
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,re,uuid,importlib.util
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'sbc-power',H.parent/'field-power',H.parent,H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import native_owned_root_pose_contract_r3 as FP
from shapely.geometry import Polygon
import physical_reference_losses_r3_zero_r208 as RF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
EFILE=H.parent/'sbc-power/emit_complete_power_recipe_r114.py'
spec=importlib.util.spec_from_file_location('frozen_r114_serializers',EFILE);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
PROFILE=('priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def exact_file(row,key):
 p=Path(row[key+'_file']).resolve();assert sha(p)==row[key+'_sha256'];return p
def main():
 assert len(sys.argv)==3,'immutable_emit_manifest.json fresh_recipe_directory';manifest=Path(sys.argv[1]).resolve();m=read(manifest);out=Path(sys.argv[2]).resolve();assert out.is_relative_to(H.parent)and not out.exists();assert m['schema']=='current-owned-native-emitter-manifest-r280';assert m['exploratory_diagnostic_only']is True and m['adopted']is False and m['manufacturing_ready']is False
 for row in m['frozen_read_set']:assert sha(row['file'])==row['sha256']
 assert sha(EFILE)=='5d252a7e19cacbe34ebc71021ad047209039438738183925124bbae9b569f2c5','Frozen exact serializers changed'
 model=exact_file(m,'current_model');audit=exact_file(m,'incremental_current_audit');failure=exact_file(m,'production_failure_ledger');inventory_receipt=exact_file(m,'complete_inventory_receipt');ir=read(inventory_receipt);assert ir['current_model_sha256']==sha(model)and ir['all_original_inventory_differences_bound']is True and ir['unbound_original_difference_count']==0;diff=Path(ir['diff_file']);assert sha(diff)==ir['diff_sha256'];d=read(diff);assert d['all_original_inventory_differences_bound']and not d['unbound_original_difference_rows']
 gate=read(audit);bound_gate=gate
 for part in m['incremental_current_audit_model_hash_pointer']:bound_gate=bound_gate[part]
 assert bound_gate==sha(model),'Incremental receipt must bind this exact current model, not only a named predecessor'
 assert m['fresh_actual_incremental_contact_source_strict_old_reference_native_effective_Cu_gate_pass']is True;assert m['all_current_sparse_operations_authorized_and_bound']is True;assert m['all_failed_or_open_current_native_reference_production_gates_recorded']is True
 g,h,b,q,current=pickle.loads(model.read_bytes());precision=restore_bound_generated_precision_states(b,q);native=Path(m['parent_native_board_file']);assert sha(native)==m['parent_native_board_sha256']==E.PARENT_SHA;source=Path(m['fresh_source_file']);assert sha(source)==m['fresh_source_sha256']==E.SOURCE_SHA;sourcebytes=native.read_bytes();source_inventory=A.C.inventory(sourcebytes);identity=A.N.SourceNets(sourcebytes)
 rotations=H.parent/'two-rotated-FP-native-collector-contract-r87/frozen-rotation-rows.json';assert sha(rotations)=='c79354f60f6fba0e38cd5f3df774876c4fc541ede3a2f27109d1a236f9c448d3';fprows=d['native_existing_owned_footprint_replacement_rows'];assert len(fprows)==3 and [r for r in fprows if r['ref']!='R17031']==read(rotations);fp_native,fp_pins,fp_poses,fp_masks=FP.collect(fprows,source_inventory)
 # Every current discrete record is tied to the complete original diff,
 # including unchanged-source full record hashes and exact additions.
 for kind in('tracks','vias','pads'):
  counts=d['counts'][kind];oldmap={r['uuid']:r for r in current[kind]};assert len(oldmap)==counts['current'];assert {r['uuid']:r for r in h[kind]}==oldmap;assert all(oldmap[r['uuid']]==r for r in counts['new_complete_native_rows']);assert not(kind=='pads'and counts['new_UUIDs'])
 supplement={r['proposal_UUID']:r for r in m.get('owned_zone_native_profile_completion_rows',[])};assert len(supplement)==len(m.get('owned_zone_native_profile_completion_rows',[]));profile_rows=[];zone_rows=[];cu_rows=[];mapping=[];newids=set();oldids=set(source_inventory[3]);assert len({z['uuid']for z in q})==len(q);out.mkdir();put(out/'bound-generated-role-precision-state.json',precision)
 for z in q:
  intended=z['zone_outline_shape'];physical=z['shape'];settings={k:z[k]for k in PROFILE if k in z};missing=set(PROFILE)-set(settings);authority=None
  if missing:
   authority=supplement.get(z['uuid']);assert authority is not None,('Missing explicit native profile',z['uuid'],sorted(missing));assert authority['physical_WKB_sha256']==hashlib.sha256(physical.wkb).hexdigest()and authority['intended_WKB_sha256']==hashlib.sha256(intended.wkb).hexdigest();assert sha(authority['authorizing_receipt_file'])==authority['authorizing_receipt_sha256'];assert set(authority['complete_native_settings'])==set(PROFILE);assert all(authority['complete_native_settings'][k]==v for k,v in settings.items());settings=dict(authority['complete_native_settings'])
  elif z['uuid']in supplement:assert supplement[z['uuid']]['complete_native_settings']==settings,'No profile override'
  assert settings['pad_connect_mode']=='FULL_SOLID'and settings['clearance_mm']>=.15 and settings['min_thickness_mm']>=.15;assert identity.raw(z['net'])==z['net'];uid=E.native_uuid(z['uuid']);assert uid not in oldids;pf=out/(uid+'.physical-Cu.wkb');nf=out/(uid+'.native-outline.wkb');pf.write_bytes(physical.wkb);nf.write_bytes(intended.wkb);parts=sorted(RF.parts(intended),key=lambda s:(-s.area,s.bounds));assert parts
  profile_rows.append({'proposal_UUID':z['uuid'],'exact_model_fields':{k:z[k]for k in PROFILE if k in z},'explicit_completion_only_for_missing_fields':authority,'effective_declared_native_settings':settings,'physical_WKB_sha256':sha(pf),'intended_WKB_sha256':sha(nf)})
  mapping.append({'proposal_uuid':z['uuid'],'native_parent_uuid':uid,'detached_native_outers':len(parts)})
  for i,part in enumerate(parts):
   nid=uid if i==0 else str(uuid.uuid5(uuid.UUID(uid),'separate-native-outer-'+str(i)));assert nid not in oldids and nid not in newids;newids.add(nid);rings=[E.exact_ring(part.exterior)]+[E.exact_ring(r)for r in part.interiors];chunk=E.render(nid,z['net'],z['layer'],part).replace('(priority 20)','(priority %d)'%settings['priority']).replace('(clearance 0.15)','(clearance %.6f)'%settings['clearance_mm']).replace('(min_thickness 0.15)','(min_thickness %.6f)'%settings['min_thickness_mm']).replace('(thermal_gap 0.15)','(thermal_gap %.6f)'%settings['thermal_gap_mm']).replace('(thermal_bridge_width 0.3)','(thermal_bridge_width %.6f)'%settings['thermal_bridge_width_mm']).replace('(island_removal_mode 1)','(island_removal_mode %d)'%settings['island_removal_mode']);path=out/(nid+'.zone-chunk');path.write_text(chunk,encoding='utf-8',newline='\n');ast=E.parse(chunk);rt=[[[E.nm(float(v[1])),E.nm(float(v[2]))]for v in E.child(poly,'pts')[1:]]for poly in E.children(ast,'polygon')];assert rt==rings;reconstructed=Polygon([(x/1e6,y/1e6)for x,y in rings[0]],[[(x/1e6,y/1e6)for x,y in r]for r in rings[1:]]);assert reconstructed.is_valid and reconstructed.equals(part)
   assert E.atom(ast,'uuid')==nid and E.atom(ast,'net')==z['net']and E.atom(ast,'layer')==z['layer'];assert int(E.atom(ast,'priority'))==settings['priority'];assert float(E.atom(E.child(ast,'connect_pads'),'clearance'))==settings['clearance_mm'];assert float(E.atom(ast,'min_thickness'))==settings['min_thickness_mm'];fill=E.child(ast,'fill');assert int(E.atom(fill,'island_removal_mode'))==settings['island_removal_mode'];assert float(E.atom(fill,'thermal_gap'))==settings['thermal_gap_mm']and float(E.atom(fill,'thermal_bridge_width'))==settings['thermal_bridge_width_mm'];assert E.child(ast,'connect_pads')[1]=='yes','Actual serialized FULL_SOLID required';assert not E.children(ast,'filled_polygon')and not E.children(ast,'fill_segments')
   zone_rows.append({'uuid':nid,'proposal_uuid':z['uuid'],'part_index':i,'raw_net':z['net'],'layer':z['layer'],'outer_integer_nm':rings[0],'hole_integer_nm':rings[1:],'chunk_file':str(path),'chunk_sha256':sha(path),'physical_Cu_wkb_sha256':sha(pf),'intended_native_outline_wkb_sha256':sha(nf),'declared_native_settings':{'priority':settings['priority'],'local_clearance_mm':settings['clearance_mm'],'min_thickness_mm':settings['min_thickness_mm'],'pad_connect_mode':settings['pad_connect_mode'],'island_removal_mode':settings['island_removal_mode'],'thermal_gap_mm':settings['thermal_gap_mm'],'thermal_bridge_width_mm':settings['thermal_bridge_width_mm']},'native_actual_fill_source_contact_and_reference':'OPEN'})
 frozen_additions={}
 for row in m.get('frozen_new_discrete_addition_rows',[]):
  uid=row['uuid'];assert uid not in frozen_additions and sha(row['chunk_path'])==row['chunk_sha256'];assert sha(row['authorizing_packet_file'])==row['authorizing_packet_sha256'];frozen_additions[uid]=row
 for kind,objects in(('segment',d['counts']['tracks']['new_complete_native_rows']),('via',d['counts']['vias']['new_complete_native_rows'])):
  for t in objects:
   uid=t['uuid'];assert str(uuid.UUID(uid))==uid and uid not in oldids and uid not in newids;newids.add(uid);assert identity.raw(t['net'])==t['net'];E.nm(t['d']if kind=='via'else t['w']);path=out/(uid+'.'+kind+'-chunk')
   if kind=='via':
    for v in(t['x'],t['y'],t['drill']):E.nm(v)
    chunk='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.6f)\n\t\t(drill %.6f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(t['x'],t['y'],t['d'],t['drill'],json.dumps(t['net']),json.dumps(uid))
   else:
    assert t.get('m')is None,'New arcs need a separate exact serializer'
    for point in(t['a'],t['b']):
     for v in point:E.nm(v)
    chunk='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*t['a'],*t['b'],t['w'],json.dumps(t['layer']),json.dumps(t['net']),json.dumps(uid))
   if uid in frozen_additions:
    chunk=Path(frozen_additions[uid]['chunk_path']).read_text();assert A.C.pcbtext.chunk_kind(chunk.encode())==kind;assert A.C.pcbtext.chunk_uuid(chunk.encode())==uid
   elif t.get('locked'):chunk=chunk.replace('\t\t(net ', '\t\t(locked yes)\n\t\t(net ',1)
   path.write_text(chunk,encoding='utf-8',newline='\n');ast=E.parse(chunk);assert E.atom(ast,'net')==t['net']and E.atom(ast,'uuid')==uid
   if kind=='via':
    assert not any(token in chunk for token in('remove_unused_layers','keep_end_layers','zone_connection')),'No newly emitted ordinary via may suppress unattested inner annuli'
    assert [E.nm(float(v))for v in E.child(ast,'at')[1:]]==[E.nm(t['x']),E.nm(t['y'])]and E.nm(float(E.atom(ast,'size')))==E.nm(t['d'])and E.nm(float(E.atom(ast,'drill')))==E.nm(t['drill'])
   else:assert [E.nm(float(v))for v in E.child(ast,'start')[1:]]==[E.nm(v)for v in t['a']]and [E.nm(float(v))for v in E.child(ast,'end')[1:]]==[E.nm(v)for v in t['b']]and E.nm(float(E.atom(ast,'width')))==E.nm(t['w'])and E.atom(ast,'layer')==t['layer']
   cu_rows.append({'kind':kind,'uuid':uid,'raw_net':t['net'],'geometry':t,'chunk_file':str(path),'chunk_sha256':sha(path),'native_all6_new_ordinary_flash_and_full_reference':'OPEN'})
 deletes=[]
 for old in d['native_existing_owned_Cu_delete_rows']:
  row=dict(old);src=Path(row['chunk_path']);assert sha(src)==row['exact_original_chunk_sha256'];dst=out/(row['uuid']+'.delete-original-'+row['kind']+'-chunk');dst.write_bytes(src.read_bytes());row['chunk_file']=str(dst);row['chunk_sha256']=sha(dst);deletes.append(row)
 put(out/'native-UUID-mapping.json',mapping);put(out/'current-owned-native-profile-ledger.json',profile_rows);(out/'proposed-zones.pkl').write_bytes(pickle.dumps(q,protocol=5));(out/'new-owned-discrete.pkl').write_bytes(pickle.dumps({'tracks':d['counts']['tracks']['new_complete_native_rows'],'vias':d['counts']['vias']['new_complete_native_rows'],'pads':[]},protocol=5))
 receipt={'verdict':'EXACT_CURRENT_OWNED_NATIVE_RECIPE_DIAGNOSTIC_INCREMENTAL_GATES_BOUND_FULL_PRODUCTION_FAIL_OPEN','parent_native_board_file':str(native),'parent_native_board_sha256':sha(native),'fresh_source_file':str(source),'fresh_source_sha256':sha(source),'frozen_host_model_file':str(model),'frozen_host_model_sha256':sha(model),'full_original198b_and_dc936_contact_audit_file':str(audit),'full_original198b_and_dc936_contact_audit_sha256':sha(audit),'host_retained_relationships_pass':False,'host_all_supply_pad_and_proposed_components_rooted':False,'native_zone_rows':zone_rows,'native_discrete_rows':cu_rows,'new_zone_chunks':len(zone_rows),'owned_proposal_shapes':len(q),'new_vias':len(d['counts']['vias']['new_UUIDs']),'new_segments':len(d['counts']['tracks']['new_UUIDs']),'native_existing_owned_Cu_delete_rows':deletes,'exact_existing_native_deleted_segments':sum(r['kind']=='segment'for r in deletes),'exact_existing_native_deleted_vias':sum(r['kind']=='via'for r in deletes),'existing_native_owned_Cu_removal_recipes':[{'file':r['authorizing_recipe_file'],'sha256':r['authorizing_recipe_sha256']}for r in deletes],'native_existing_owned_Cu_replacement_rows':d['native_existing_owned_Cu_replacement_rows'],'native_existing_owned_footprint_replacement_rows':fprows,'existing_via_prospective_new_flashes':d['existing_via_prospective_new_flashes'],'complete_inventory_receipt_file':str(inventory_receipt),'complete_inventory_receipt_sha256':sha(inventory_receipt),'complete_inventory_diff_file':str(diff),'complete_inventory_diff_sha256':sha(diff),'explicit_current_emit_manifest_file':str(manifest),'explicit_current_emit_manifest_sha256':sha(manifest),'production_failure_ledger_file':str(failure),'production_failure_ledger_sha256':sha(failure),'old_zone_removals':[],'old_zone_replacements':[],'raw_net_aliases':[],'all_current_q_physical_and_intended_WKB_from_actual_model':True,'no_old_R169_q_geometry_or_model_overlay':True,'all_new_coordinates_exact_integer_nm_AST_roundtrip':True,'supplemental_native_profile_completions_explicit':len(supplement),'frozen_R87_whole_file_sha256':sha(rotations),'native_FP_R3_collector_pins':fp_pins,'new_ordinary_via_UUIDs_requiring_actual_all6_annuli':[r['uuid']for r in cu_rows if r['kind']=='via'],'every_new_serialized_via_has_no_unused_layer_suppression':True,'native_postfill_all_new_and_retained_annuli_actual_source_and_reference_full_DRC_current_SI':'OPEN','board_written':False,'source_or_project_written':False,'board_adopted':False,'native_jobs':0,'emitter_sha256':sha(__file__),'reused_exact_R114_serializer_sha256':sha(EFILE)};put(out/'receipt.json',receipt);print(json.dumps({'receipt_file':str(out/'receipt.json'),'receipt_sha256':sha(out/'receipt.json'),'native_zones':len(zone_rows),'segments':receipt['new_segments'],'vias':receipt['new_vias']}),flush=True)
if __name__=='__main__':main()
