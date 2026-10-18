"""Place only the frozen R10 field-B spine into corrected actual R106 source."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def root(d,net,ref):return next(xs for xs in F.graph(d,net)if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def pads(xs):return {q['uuid']for q in xs if q['kind']=='pad'and q['pin']}
mp=H/'field-power/corrected-regulated-joint-search-base-r106/model.pkl';mr=mp.with_name('receipt.json');sp=H/'fbg-lazy-existing-return-restoration-r10/proposed-zones.pkl';sr=sp.with_name('receipt.json')
assert sha(mp)=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39'
assert sha(mr)=='43561f7a10cb854563b7f585f03c104980a2165872f8f8cba1ebefd333d7dd20'
r=json.loads(sr.read_bytes());assert r['model_sha256']=='b84fefaed0fd708f859073fc6209663336f4fea29e88e60296ae7248af6c7184'and sha(sp)==r['proposed_zones_sha256']
old,h,b,zones,current=pickle.loads(mp.read_bytes());adds=pickle.loads(sp.read_bytes());assert len(adds)==1 and adds[0]['uuid']=='d480dd23-09f4-5c53-bc5b-0bee7c7536ff'
assert not {q['uuid']for q in adds}&{q['uuid']for q in zones}
out=H/'corrected-joint-ground-base-r11';assert not out.exists();out.mkdir()
candidate,retreat=N.projected(old,h,zones+adds);proofs=[]
for net,ref in[('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/LOGIC_GND','J11001')]:
 before=pads(root(current,net,ref));after=pads(root(candidate,net,ref));missing=sorted(before-after)
 proofs.append({'net':net,'source':ref+'.2','before_rooted_named_pads':len(before),'after_rooted_named_pads':len(after),'prior_actual_source_pad_losses':missing})
 assert not missing,('New FBG spine loses another actual source-rooted bank',net,missing)
 if ref=='J11005':assert set(r['rows'][0]['repair']['target_pad_UUIDs'])<=after
model=out/'model.pkl';model.write_bytes(pickle.dumps((old,h,b,zones+adds,candidate),protocol=5))
report={'verdict':'CORRECTED_R102_C_CORE91_ROOT4_R10_FULL_PROJECTED_GROUND_SEARCH_BASE_GATES_OPEN','model_sha256':sha(model),'actual_C_R102_R10_composed':True,'R106_model_sha256':sha(mp),'R10_proposed_zones_sha256':sha(sp),'R10_source_spine_exact':True,'all_other_R106_h_and_owned_planes_exact':True,'old_native_zone_outlines_changed':0,'new_holes':0,'old_Cu_deleted':0,'actual_source_retention':proofs,'full_projection_retreats':retreat,'script_sha256':sha(__file__),'input_sha256':{str(p.resolve()):sha(p)for p in(mp,mr,sp,sr,Path(N.__file__),Path(F.__file__))},'mutual_all_contacts_reference_current_native_DRC':'OPEN','native_jobs':0,'board_written':False,'adopted':False}
(out/'receipt.json').write_text(json.dumps(report,indent=1)+'\n');print(json.dumps({'verdict':report['verdict'],'model_sha256':sha(model),'roots':proofs}),flush=True)
