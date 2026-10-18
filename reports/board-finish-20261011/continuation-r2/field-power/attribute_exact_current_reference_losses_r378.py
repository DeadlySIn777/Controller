"""Attribute every R368 strict reference remainder to actual changed fills."""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_aux_exact_raw as A
import contact_layout as L
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import guarded_declared_settings_projection_r58 as N
from inventory import sha
O=H/'R368-exact-local-reference-loss-new-owner-attribution-r378'
R=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
M=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364/model.pkl'
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl'
def dg(s):return A.C.sha(s.wkb)
def main():
 assert not O.exists();O.mkdir();assert sha(R/'receipt.json')=='e4a9373b5816de6926cc3b3cea82d1751e5db6cb70d9f150443dff577afff29e'
 g,h,b,q,current=pickle.loads(M.read_bytes());_,bh,_,bq,before=pickle.loads(B.read_bytes());old=pickle.loads((R/'actual-drilled-before-groups.pkl').read_bytes());new=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes())
 tm={t['uuid']:t for t in h['tracks']};bm={t['uuid']:t for t in bh['tracks']};currentzones={z['uuid']:z for z in current['zones']};priorzones={z['uuid']:z for z in before['zones']};changed=[]
 for z in before['zones']:
  for layer,rs in z['fills'].items():
   if rs==currentzones[z['uuid']]['fills'][layer]:continue
   a=unary_union(L.poly(rs));n=unary_union(L.poly(currentzones[z['uuid']]['fills'][layer]));delta=a.difference(n);assert n.difference(a).is_empty
   changed.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'delta':delta})
 newqs=[z for z in q if z['uuid']not in{z['uuid']for z in bq}];newvias=[v for v in h['vias']if v['uuid']not in{v['uuid']for v in bh['vias']}];rows=[]
 refrows=json.loads((R/'three-bank-strict-zero-reference-rows.json').read_bytes());rootpairs={'/LOGIC_GND':('J11001','2'),'/motherboard_motors/FIELD_GND':('J11003','2'),'/motherboard_do/FIELD_B_0V':('J11005','2')}
 for bank in refrows:
  net=bank['net'];ref,pin=rootpairs[net];oldref=K.source_refs(K.root(old[net],ref,pin));newref=K.source_refs(K.root(new[net],ref,pin))
  for loss in bank['strict_ZERO_retained_old_reference_losses']:
   t=bm[loss['uuid']];body=A.shape({'kind':'segment',**t});layer=t['layer'];inner=K.MAP[layer];gap=body.intersection(oldref[layer]).difference(newref[layer]);f=O/(loss['uuid']+'-exact-local-remainder.wkb');f.write_bytes(gap.wkb);matches=[]
   for z in changed:
    if z['layer']!=inner or L.norm(z['raw_net'])!=net:continue
    hit=gap.intersection(z['delta'])
    if not hit.is_empty:matches.append({'filled_UUID':z['UUID'],'layer':inner,'exact_removed_fill_bounds_mm':list(z['delta'].bounds),'exact_removed_fill_WKB_SHA256':dg(z['delta']),'remainder_intersection_mm2':hit.area,'remainder_intersection_empty':False})
   guards=[]
   for z in newqs:
    if z['layer']!=inner or L.norm(z['net'])==net:continue
    guard=N.bounded_buffer(z['shape'],.625);hit=gap.intersection(guard)
    if not hit.is_empty:guards.append({'kind':'NEW_REG_PLANE','UUID':z['uuid'],'raw_net':z['net'],'layer':inner,'guard_overlap_mm2':hit.area,'physical_body_bounds_mm':list(z['shape'].bounds)})
   for v in newvias:
    if L.norm(v['net'])==net:continue
    guard=N.bounded_disk(v,v['d']/2+.625);hit=gap.intersection(guard)
    if not hit.is_empty:guards.append({'kind':'NEW_ORDINARY_VIA_FOREIGN_GUARD','UUID':v['uuid'],'raw_net':v['net'],'centre_mm':[v['x'],v['y']],'guard_overlap_mm2':hit.area})
   rows.append({'source_ground_net':net,'old_track_UUID':t['uuid'],'old_raw_signal_net':t['net'],'outer_or_route_layer':layer,'reference_layer':inner,'exact_old_track':t,'strict_remainder_mm2':gap.area,'strict_remainder_empty':gap.is_empty,'strict_remainder_bounds_mm':list(gap.bounds),'strict_remainder_WKB_SHA256':sha(f),'actual_changed_fill_matches':matches,'new_owner_primitive_guard_matches':guards})
 put={'verdict':'EXACT_CURRENT_NEW_OWNER_REFERENCE_LOSS_ATTRIBUTION_ONLY_NO_WAIVER_OR_EDIT','current_model_sha256':sha(M),'baseline_model_sha256':sha(B),'source_audit_receipt_sha256':sha(R/'receipt.json'),'source_groups_sha256':sha(R/'actual-drilled-current-groups.pkl'),'rows':rows,'strict_nonempty_remainders':sum(not r['strict_remainder_empty']for r in rows),'native_jobs':0,'geometry_or_source_changed':False,'adopted':False}
 (O/'receipt.json').write_text(json.dumps(put,indent=1,allow_nan=False)+'\n',encoding='utf-8');print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'source_groups_sha256':put['source_groups_sha256'],'rows':[{'track':r['old_track_UUID'],'signal':r['old_raw_signal_net'],'gap':r['strict_remainder_mm2'],'bounds':r['strict_remainder_bounds_mm'],'guard_matches':r['new_owner_primitive_guard_matches']}for r in rows]}),flush=True)
if __name__=='__main__':main()
