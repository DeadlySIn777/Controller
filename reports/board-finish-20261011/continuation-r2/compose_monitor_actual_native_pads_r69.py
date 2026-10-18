"""Compose exact monitor operation using newly attested native pads on current IO3 state."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.affinity import rotate
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import complete_geometry_r2 as G
import restore_SAFE_generated_precision_states_r168 as PS
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def main():
 out=H/'SAFE-native-monitor-rotation-composition-r69';assert not out.exists();out.mkdir()
 parent=H/'sbc-power/IO3-exact-unchanged-primitive-composition-r183/model.pkl';assert sha(parent)=='6e96338816a234e62afc309467c804c82d91785cfe0737b7b4a465f2b24b9fa5'
 packet=H/'sbc-power/IO3-minimal-validated-integration-packet-r190/receipt.json';assert sha(packet)=='4e6544cff59e0ebd16d8bd5b6ae7e9b43df0b74320c481d7febdeb141b53d63a'
 g,h,b,z,before=pickle.loads(parent.read_bytes());h=copy.deepcopy(h);replay=PS.restore_bound_generated_precision_states(b,z)
 lp=H/'SAFE-logic-four-return-restoration-r55/proposed-zones.pkl';assert sha(lp)=='b0e3766d17138741ae1f4ab6d2a574e55da6634734b03bec93d6a6abb891e065';logic=pickle.loads(lp.read_bytes());assert len(logic)==1 and logic[0]['uuid']=='ec99314b-c244-5748-bb67-de032c66ee3c'
 for q in logic:
  for role in ('shape','zone_outline_shape'):
   shape=q[role];oldhash=digest(shape);q[role]=set_precision(shape,1e-6,mode='pointwise');assert digest(q[role])==oldhash;replay.append({'UUID':q['uuid'],'role':role,'grid_mm':1e-6,'WKB_unchanged':oldhash,'constructor':'R55'})
 z+=logic;put(out/'precision-replay.json',replay)
 dp=H/'field-monitor-R9026-rotation-source-termination-r66/owned-delta.pkl';assert sha(dp)=='2669504846249102a6afe479c78f627b7729d0992c48bc64f79a330f431149c5';d=pickle.loads(dp.read_bytes())
 attdir=H/'field-monitor-native-R9026-rotation-r68';nr=json.loads((attdir/'receipt.json').read_bytes());assert sha(attdir/'receipt.json')=='3fbf5fa8c80a3bb9e03328108b677777482ae884786aef4d5ea2c09612a0baa4'and nr['verdict']=='PASS_NATIVE_SCOPED_R9026_ROTATION_ONLY_FULL_MONITOR_GATES_OPEN';att=nr['native_attestation'];assert att['verdict']=='PASS_NATIVE_EXACT_ROTATED_R9026_PAD_POSE';native={p['UUID']:p for p in att['native_pads']};nominal={p['uuid']:p for p in d['new_R9026_pads']};assert set(native)==set(nominal)
 currentpads={p['uuid']:p for p in h['pads']};assert all(currentpads[p['uuid']]==p for p in d['old_R9026_pads']),'Original monitor pads must match frozen operation exactly'
 for uid,p in native.items():
  q=currentpads[uid];expected=nominal[uid];assert [p['x'],p['y']]==[expected['x'],expected['y']]and p['net']==q['net']==expected['net']and p['num']==q['num']and p['ref']==q['ref']=='R9026'and p['smd']and p['hole']is None
  q.update(x=p['x'],y=p['y'],layers=p['layers'],smd=True,npth=False,hole=None)
 fp=next(q for q in h['footprints']if q['ref']=='R9026');origin=(fp['x'],fp['y']);assert list(origin)==d['unchanged_FP_center_mm']==att['FP_pose_mm_deg'][:2];assert fp['value']=='10000R 0.01% 5ppm'
 fp['courtyard']={l:G.records(rotate(unary_union(C.poly(rings)),180,origin=origin))for l,rings in fp.get('courtyard',{}).items()};fp['native_owned_rotation_pose_mm_deg']=att['FP_pose_mm_deg'];fp['native_owned_rotation_attestation_sha256']=sha(attdir/'receipt.json')
 removed=d['removed_old_track'];assert next(t for t in h['tracks']if t['uuid']==removed['uuid'])==removed;h['tracks']=[t for t in h['tracks']if t['uuid']!=removed['uuid']]
 assert len(d['tracks'])==5 and len(d['vias'])==1 and all(t['w']==.2 for t in d['tracks']);assert not({q['uuid']for q in d['tracks']} & {q['uuid']for q in h['tracks']})and not({q['uuid']for q in d['vias']}&{q['uuid']for q in h['vias']});h['tracks']+=d['tracks'];h['vias']+=d['vias']
 (out/'owned-operation.pkl').write_bytes(pickle.dumps({'original_parent_model_sha256':sha(parent),'exact_monitor_delta':d,'actual_native_pads':att['native_pads'],'native_rotation_receipt_sha256':sha(attdir/'receipt.json'),'logic_R55_exact_additive_zones':logic},protocol=5));(out/'unprojected-model.pkl').write_bytes(pickle.dumps((g,h,b,z,before),protocol=5))
 current,ledger=N.projected(g,h,z);put(out/'full-projection-ledger.json',ledger);model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,current),protocol=5));sources=[];groups={}
 for net,ref in [('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/IO_3V3','R18001'),('/CORE_1V2','L2001')]:
  prior=root(F.graph(before,net),ref);after=F.graph(current,net);groups[net]=after;rr=root(after,ref);lost=F.discrete_keys(prior)-F.discrete_keys(rr);sources.append({'net':net,'actual_source':ref+'.2','before_named_pads':len({q['uuid']for q in prior if q['kind']=='pad'and q['pin']}),'after_named_pads':len({q['uuid']for q in rr if q['kind']=='pad'and q['pin']}),'prior_source_keys_lost':[list(k)for k in sorted(lost)]});put(out/'source-checkpoint.json',sources);print('R69_SOURCE',net,sources[-1]['after_named_pads'],'losses',len(lost),flush=True)
 fg=root(groups['/motherboard_motors/FIELD_GND'],'J11003');joined=any(q['kind']=='pad'and q['uuid']==next(p['uuid']for p in nominal.values()if p['num']=='2')for q in fg);groundbody=unary_union([q['shape']for q in fg if q['kind']=='fill'and q['layer']=='In1.Cu']);uvbody=N.bounded_buffer(unary_union([C.body(t)for t in d['tracks']if C.norm(t['net'])!='/motherboard_motors/FIELD_GND']),.000001);gap=uvbody.difference(groundbody)
 (out/'new-UV-In1-source-reference-gap.wkb').write_bytes(gap.wkb);(out/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=joined and not any(q['prior_source_keys_lost']for q in sources)
 put(out/'receipt.json',{'verdict':'ACTUAL_NATIVE_MONITOR_SOURCE_PROJECTED_NO_PRIOR_SOURCE_LOSS_FULL_GATES_OPEN'if ok else'ACTUAL_NATIVE_MONITOR_SOURCE_CONTACT_REPAIR_REQUIRED','model_sha256':sha(model),'parent_sha256':sha(parent),'monitor_delta_sha256':sha(dp),'native_rotation_receipt_sha256':sha(attdir/'receipt.json'),'actual_new_R9026_ground_source_joined':joined,'source_checks':sources,'actual_J3_In1_new_UV_reference_gap_mm2':gap.area,'actual_J3_In1_new_UV_reference_gap_sha256':sha(out/'new-UV-In1-source-reference-gap.wkb'),'all_new_via_flashes':'PROSPECTIVE_ORDINARY_ALL6_NATIVE_OPEN','native_pad_polygons_replaced_nominal_host_mesh_before_projection':True,'source_geometrical_inside_polygon_error_mm':att['actual_native_polygon_inside_error_mm'],'full76_Cu_pad_source_reference_native_DRC_threshold_PDN_current':'OPEN','generated_precision_ledger_needs_extend_one_R55_owned_shape_before_replay':True,'native_jobs':0,'board_written':False,'adopted':False,'host_retained_relationships_pass':False})
 print('R69_COMPLETE',ok,joined,gap.area,sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
