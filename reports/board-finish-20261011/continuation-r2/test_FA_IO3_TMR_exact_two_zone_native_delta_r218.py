"""Native selected-fill diagnostic of the exact two-zone TMR repair on a clone."""
import hashlib,importlib.util,json,os,pickle,shutil,subprocess,sys,uuid
from pathlib import Path
from shapely.geometry import Polygon
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import native_pose_signal_contract as NC
import physical_reference_losses_r3_zero_r208 as RF
OUT=H/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_bytes())
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def dedup(ring):
 out=[]
 for p in ring:
  if not out or p!=out[-1]:out.append(p)
 if len(out)>1 and out[0]==out[-1]:out.pop()
 return out
def main():
 assert not OUT.exists();OUT.mkdir()
 contract=H/'field-power/FA-IO3-native-TMR-exact-two-zone-sparse-rebase-contract-r519/receipt.json';assert sha(contract)=='bf494afa1699ce52e1812b79efe3676d31cb9d25f4a9c6d0f79b55b65bf8440e';r=read(contract)
 assert r['all81_contact_loss_count']==r['nine_prior_source_key_loss_count']==r['direct_contact_loss_count']==0
 assert r['new_Cu_tracks_vias_holes_pad_source_design_rule_edits']==0 and r['three_ground_current_arrays_source_reference_roles_exact']
 for row in r['frozen_read_set']:assert sha(row['file'])==row['sha256']
 mp=Path(r['exact_host_head_file']);bp=Path(r['exact_before_model_file']);_,h,b,q,full=pickle.loads(mp.read_bytes());_,h0,b0,q0,oldfull=pickle.loads(bp.read_bytes());assert h==h0
 targets={row['UUID']for row in r['owned_q_rows']};assert targets=={'4f297f78-8d11-5be4-910e-9245f73fa249','7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19'}
 current={z['uuid']:z for z in q};prior={z['uuid']:z for z in q0};assert current.keys()==prior.keys()
 for uid in current:
  if uid not in targets:assert all(current[uid][key].wkb==prior[uid][key].wkb for key in('shape','zone_outline_shape'))
 for row in r['owned_q_rows']:
  for role in('shape','zone_outline_shape'):
   assert hashlib.sha256(prior[row['UUID']][role].wkb).hexdigest()==row['exact_before_roles'][role]
   assert hashlib.sha256(current[row['UUID']][role].wkb).hexdigest()==row['exact_after_roles'][role]
 stage=H/'R155-known-reference-native-diagnostic-r157';parent=stage/'copy/board.kicad_pcb';assert sha(parent)=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
 recipe=H/'coupled-recovery/R155-known-failed-reference-native-recipe-r306/receipt.json';rr=read(recipe);assert rr['frozen_host_model_sha256']==r['exact_before_model_sha256'];inv=NC.C.inventory(parent.read_bytes())
 oldrows=[row for row in rr['native_zone_rows']if row['proposal_uuid']in targets];removed={row['uuid']:Path(row['chunk_file']).read_bytes()for row in oldrows};assert all(inv[3][u]==ch for u,ch in removed.items())
 emitter=H/'sbc-power/emit_complete_power_recipe_r114.py';assert sha(emitter)=='5d252a7e19cacbe34ebc71021ad047209039438738183925124bbae9b569f2c5';spec=importlib.util.spec_from_file_location('TMR_exact_frozen_serializers',emitter);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
 chunks={};native_rows=[];zeroedges=[]
 for uid in sorted(targets):
  z=current[uid];assert all(z[k]==prior[uid][k]for k in('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm'));assert z['priority']==124 and z['pad_connect_mode']=='FULL_SOLID' and z['clearance_mm']==z['min_thickness_mm']==.15
  parts=sorted(RF.parts(z['zone_outline_shape']),key=lambda p:(-p.area,p.bounds));baseuid=E.native_uuid(uid)
  for i,part in enumerate(parts):
   nid=baseuid if i==0 else str(uuid.uuid5(uuid.UUID(baseuid),'separate-native-outer-'+str(i)));assert nid not in chunks and (nid not in inv[3]or nid in removed)
   text=E.render(nid,z['net'],z['layer'],part).replace('(priority 20)','(priority 124)');ast=E.parse(text);rawrings=[[[E.nm(float(p[1])),E.nm(float(p[2]))]for p in E.child(poly,'pts')[1:]]for poly in E.children(ast,'polygon')];assert rawrings==[E.exact_ring(part.exterior)]+[E.exact_ring(r)for r in part.interiors]
   rings=[dedup(ring)for ring in rawrings];assert Polygon([(x/1e6,y/1e6)for x,y in rings[0]],[[(x/1e6,y/1e6)for x,y in ring]for ring in rings[1:]]).equals(part)
   for j,(a,bb)in enumerate(zip(rawrings,rings)):
    if a!=bb:zeroedges.append({'native_UUID':nid,'ring':j,'removed_only_consecutive_identical_or_closure_vertices':True,'raw_ring_IU':a,'API_expected_ring_IU':bb})
   chunks[nid]=text.encode();(OUT/(nid+'.zone-chunk')).write_bytes(chunks[nid]);native_rows.append({'uuid':nid,'raw_net':z['net'],'layer':z['layer'],'rings_IU':rings,'declared_native_settings':{'priority':124,'local_clearance_IU':150000,'minimum_thickness_IU':150000,'thermal_gap_IU':150000,'thermal_spoke_IU':300000,'island_removal_mode':1}})
 data=inv[0]+b''.join(ch for ch in inv[1]if NC.C.pcbtext.chunk_uuid(ch)not in removed)+b''.join(chunks.values())+inv[2];after=NC.C.inventory(data);assert after[0]==inv[0]and after[2]==inv[2]
 assert all(after[3][u]==ch for u,ch in inv[3].items()if u not in removed);assert all(after[3][u]==ch for u,ch in chunks.items());assert after[4]==inv[4]
 copy=OUT/'copy';copy.mkdir();board=copy/'board.kicad_pcb';board.write_bytes(data)
 for ext in('.kicad_pro','.kicad_dru'):shutil.copy2(parent.with_suffix(ext),board.with_suffix(ext))
 assert sha(board.with_suffix('.kicad_dru'))==r['complete_native_rule_sha256']
 put(OUT/'two-zone-native-expected.json',{'candidate_sha256':sha(board),'zones':native_rows});put(OUT/'only-zero-edge-API-normalizations.json',zeroedges)
 expected=read(stage/'all-copper-expected.json');assert expected['board_sha256']==sha(parent);expected['board_sha256']=sha(board);expected['board_path']=str(board);put(OUT/'all-copper-expected.json',expected)
 helper=OUT/'native_FA_IO3_selected_fill.py';source=H/'native_core1v2_scoped_refill_r132.py';code=source.read_text();assert code.count("raw='/CORE_1V2'")==1;code=code.replace("raw='/CORE_1V2'","raws={'/IO_3V3','/motherboard_power_entry{slash}FIELD_A_24V_PROTECTED'};raw='exact FA plus IO3 raw nets'").replace('str(z.GetNetname())==raw:',"str(z.GetNetname())in raws:").replace('CORE1V2','FA_IO3').replace('FA_IO3 only','FA plus IO3 zones only');compile(code,str(helper),'exec');helper.write_text(code)
 wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');api=Path('C:/Program Files/KiCad/10.0/bin/python.exe');check=H/'native_declared_selected_zone_contract_r2.py';prefix=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api)]
 commands=[prefix+[str(check),str(OUT/'two-zone-native-expected.json'),str(board),str(OUT/'native-two-zone-API.json')],prefix+[str(helper),str(board),str(OUT/'all-copper-expected.json'),str(OUT/'scoped-fill')]]
 files=[Path(__file__),contract,mp,bp,parent,parent.with_suffix('.kicad_pro'),parent.with_suffix('.kicad_dru'),recipe,emitter,source,helper,wrapper,api,check,board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),OUT/'all-copper-expected.json',OUT/'two-zone-native-expected.json',OUT/'only-zero-edge-API-normalizations.json'];pins={str(p.resolve()):sha(p)for p in files};pins.update({row['file']:row['sha256']for row in r['frozen_read_set']})
 put(OUT/'inputs.json',{'pins':pins,'commands':commands,'exact_two_owned_proposal_UUIDs':sorted(targets),'removed_native_owned_zone_UUIDs':sorted(removed),'new_native_zone_UUIDs':sorted(chunks),'complete_Cu_FP_original_native_zones_source_rawdefs_project_rules_unchanged':True,'only_exact_two_new_owned_intended_zone_serializations_changed':True,'existing_slot':'test-only1','new_heavy_slots':0,'raw_inherited_R155_reference_planner_current_and_R157_full_native_gates_preserved':True,'adopted':False})
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH'];put(OUT/'status.json',{'phase':'TWO_OWNED_ZONE_API_AND_FA_IO3_SELECTED_NATIVE_FILL_RUNNING','candidate_sha256':sha(board),'adopted':False});print('R218_NATIVE_SELECTED_START',sha(board),len(native_rows),flush=True)
 for i,cmd in enumerate(commands):
  with(OUT/('native-'+str(i)+'.log')).open('w')as log:run=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert run.returncode==0,('Native selected diagnostic failed',i,run.returncode)
  assert all(sha(p)==v for p,v in pins.items())
 result={'verdict':'NATIVE_TWO_OWNED_ZONE_API_AND_SELECTED_FA_IO3_FILL_COMPLETE_INDEPENDENT_SOURCE_REVIEW_OPEN','candidate_sha256':sha(board),'parent_sha256':sha(parent),'host_delta_contract_sha256':sha(contract),'new_zone_chunks':len(native_rows),'all_discrete_Cu_FP_native_source_and_original_zones_project_rules_exact':True,'scope':'Only FA and IO3 zones refilled; other cache Cu and all-board source/reference/current/DRC not accepted','native_API_sha256':sha(OUT/'native-two-zone-API.json'),'native_fill_receipt_sha256':sha(OUT/'scoped-fill/receipt.json'),'inputs_sha256':sha(OUT/'inputs.json'),'native_copper_saved':False,'adopted':False,'manufacturing_ready':False};put(OUT/'receipt.json',result);put(OUT/'status.json',result);print('R218_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
