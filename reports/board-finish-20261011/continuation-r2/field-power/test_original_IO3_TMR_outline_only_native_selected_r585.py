"""Authorized original-zone outline-only exact API/selected native fill clone."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,shutil,subprocess,time,datetime
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(ROOT/d))
import native_pose_signal_contract as NC
from verify_source import P as SP
OUT=H/'original-IO3-TMR-outline-only-native-API-selected-FA-IO3-r585'
N=ROOT/'FA-IO3-TMR-exact-two-zone-native-selected-diagnostic-r218'
P=H/'original-IO3-TMR-exact-local-two-notch-negative-outline-nominee-r573'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();st=time.monotonic()
 attr=H/'R218-eight-native-zone-intersections-exact-input-attribution-r583/receipt.json';assert sha(attr)=='6c3083cdfdd8c9e8ab0aac83fbaf1ef6aa6fdc682a36a4289e19a8758c2027fc'
 ar=json.loads(attr.read_bytes());assert ar['pair_count']==8 and ar['introduced_by_R515_two_zone_serialization_count']==0 and ar['reported_inter_net_zone_pair_count']==0
 packet=P/'only-one-original-IO3-zone-outline-negative-replacement.pkl';assert sha(packet)=='f1d5b9c1550d996890ee8dba37c9fb19cd5337853df6778629541a82f2e252e6';x=pickle.loads(packet.read_bytes())
 parent=N/'copy/board.kicad_pcb';assert sha(parent)==x['R218_candidate_SHA256'];original=x['before_full_original_zone_chunk'];replacement=x['after_full_outline_only_original_zone_chunk'];uid=x['original_zone_UUID']
 old=NC.C.inventory(parent.read_bytes());assert old[3][uid]==original
 oa=SP['sexpr_parse'](original.decode());na=SP['sexpr_parse'](replacement.decode());assert [a for a in oa if not(isinstance(a,list)and a[0]=='polygon')]==[a for a in na if not(isinstance(a,list)and a[0]=='polygon')]
 assert SP['children'](oa,'polygon')[1:]==SP['children'](na,'polygon')[1:]
 rings=[[[int(round(float(xy[1])*1e6)),int(round(float(xy[2])*1e6))]for xy in SP['children'](SP['child'](poly,'pts'),'xy')]for poly in SP['children'](na,'polygon')];assert rings==x['after_integer_polygon_rings']
 data=old[0]+b''.join(replacement if NC.C.pcbtext.chunk_uuid(ch)==uid else ch for ch in old[1])+old[2];new=NC.C.inventory(data)
 assert new[0]==old[0]and new[2]==old[2]and new[4]==old[4]and new[3].keys()==old[3].keys()
 assert all(new[3][u]==ch for u,ch in old[3].items()if u!=uid)and new[3][uid]==replacement
 copy=OUT/'copy';copy.mkdir()
 for f in (N/'copy').iterdir():
  if f.is_file()and f.name!='board.kicad_pcb':shutil.copy2(f,copy/f.name)
 board=copy/'board.kicad_pcb';board.write_bytes(data)
 spec=json.loads((N/'two-zone-native-expected.json').read_bytes());assert spec['candidate_sha256']==sha(parent);spec['candidate_sha256']=sha(board)
 assert uid not in {z['uuid']for z in spec['zones']}
 spec['zones'].append({'uuid':uid,'raw_net':'/IO_3V3','layer':'In2.Cu','rings_IU':rings,'declared_native_settings':{'priority':3,'local_clearance_IU':150000,'minimum_thickness_IU':250000,'thermal_gap_IU':500000,'thermal_spoke_IU':500000,'island_removal_mode':0}})
 put(OUT/'exact-native-outline-shadow-expected.json',spec)
 copper=json.loads((N/'all-copper-expected.json').read_bytes());assert copper['board_sha256']==sha(parent);copper.update(board_sha256=sha(board),board_path=str(board));put(OUT/'all-copper-expected.json',copper)
 helper=OUT/'native_FA_IO3_selected_fill.py';shutil.copy2(N/'native_FA_IO3_selected_fill.py',helper)
 wrapper=Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh');api=Path('C:/Program Files/KiCad/10.0/bin/python.exe');check=ROOT/'native_declared_selected_zone_contract_r2.py'
 assert sha(helper)=='fea86c884dab0d8209a3c9db511c172e73ab60a7cd8ada0991bd9e58424aa193'
 assert sha(check)=='1e8d45846db6ca474bacd83045aec9bce05cd99127247da704a9e0d3ef8da58f'
 assert sha(wrapper)=='378b3d7d29b2bf6f0348cf89907fe67d7e0f7e128dddb095cd085fe4a7a1c4d1'
 source=H/'combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(source)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2'
 files=[Path(__file__),attr,packet,P/'receipt.json',parent,N/'receipt.json',N/'scoped-fill/receipt.json',N/'two-zone-native-expected.json',N/'all-copper-expected.json',wrapper,api,check,helper,source,OUT/'exact-native-outline-shadow-expected.json',OUT/'all-copper-expected.json']+[f for f in copy.iterdir()if f.is_file()]
 pins={str(f.resolve()):sha(f)for f in files};prefix=['C:/Program Files/Git/usr/bin/sh.exe',str(wrapper),'kicad',str(api)]
 commands=[prefix+[str(check),str(OUT/'exact-native-outline-shadow-expected.json'),str(board),str(OUT/'native-outline-API.json')],prefix+[str(helper),str(board),str(OUT/'all-copper-expected.json'),str(OUT/'scoped-fill')]]
 record={'phase':'EXACT_ORIGINAL_OUTLINE_API_THEN_SELECTED_FA_IO3_NATIVE_FILL_RUNNING','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pins':pins,'commands':commands,'original_zone_UUID':uid,'parent_sha256':sha(parent),'candidate_sha256':sha(board),'one_original_zone_outline_only_changed':True,'all_54_original_hole_AST_all_other_zone_AST_exact':True,'all_86396_segments_8006_vias_FP_source_project_rules_other_zones_exact':True,'original_full_before_bytes_archived_in_R573':True,'R515_two_owned_repairs_preserved_exact':True,'native_API_shadow_exact_9970_integer_points_54_holes_and_original_profile':True,'slot':'existing_test_only1','new_slots':0,'R567_eight_same_net_zone_errors_retained':sha(attr),'R575_R577_raw_virtual_clip_locality_FAILs_retained':True,'native_source_and_605_direct_contacts_after_fill':'OPEN: independent actual-drill source proof required','all_board_DRC_current_thermal_references':'OPEN/known failures preserved','no_native_save_or_manual_cachedfill_edit':True,'adopted':False}
 put(OUT/'inputs.json',record);put(OUT/'status.json',record);print('R585_START',sha(board),'zones',len(spec['zones']),flush=True)
 env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']
 for i,cmd in enumerate(commands):
  with(OUT/('native-'+str(i)+'.log')).open('w',encoding='utf-8')as log:r=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
  assert r.returncode==0,(i,r.returncode)
  assert all(sha(p)==v for p,v in pins.items())
  if i==0:
   v=json.loads((OUT/'native-outline-API.json').read_bytes());assert not v['errors'];assert v['native_zones_checked']==28
 put(OUT/'receipt.json',{'status':'ORIGINAL_ONE_OUTLINE_NATIVE_EXACT_API_SELECTED_FILL_COMPLETE_INDEPENDENT_SOURCE_CONTACT_RULE_REVIEW_OPEN','parent_sha256':sha(parent),'candidate_sha256':sha(board),'one_original_outline_only_and_all_other_native_bytes_exact':True,'inputs_sha256':sha(OUT/'inputs.json'),'native_API_sha256':sha(OUT/'native-outline-API.json'),'native_fill_receipt_sha256':sha(OUT/'scoped-fill/receipt.json'),'selected_geometry_sha256':sha(OUT/'scoped-fill/geometry.json'),'all_copper_postfill_exact':True,'native_source_605_direct_contacts_and_actual_nozone':'OPEN','eight_R567_same_net_overlap_ERRORS_and_inherited_R155_failures_preserved':True,'native_board_saved':False,'adopted':False,'elapsed_seconds':time.monotonic()-st});put(OUT/'status.json',json.loads((OUT/'receipt.json').read_bytes()));print('R585_COMPLETE',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
