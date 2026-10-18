"""Exact fresh constraint attribution; do not replace or waive old copper."""
import hashlib,json,pickle,sys,traceback
from pathlib import Path
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent.parent
for d in('sbc-power','field-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as GP
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/FPGA-ground-escape-literal-wall-attribution-r254'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();mp=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(mp)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,z,c=pickle.loads(mp.read_bytes());replay=PS.restore_bound_generated_precision_states(b,z);tp=H/'sbc-power/FPGA-R7-T4-full-width-real-ground-nominees-r253/receipt.json';assert sha(tp)=='c08aef0bc842066169f81c83f552900f3605f0bf9869db31e7f8e52283d3b178';uids={'c161da3b-e8ef-42cc-b51e-f7e2f2df45ff','7a7efa56-f9f9-4efa-b31d-3ceed21fa937'};objects=[]
 for kind in('tracks','vias','pads'):
  for q in h[kind]:
   if q['uuid']not in uids:continue
   body=LineString([q['a'],q['b']])if kind=='tracks'else Point(q['x'],q['y']);near=[{'ref':p['ref'],'pin':p['num'],'UUID':p['uuid'],'raw_net':p['net'],'at':[p['x'],p['y']],'distance_to_axis_mm':body.distance(Point(p['x'],p['y']))}for p in h['pads']if body.distance(Point(p['x'],p['y']))<1.5];old=next((p for p in g[kind]if p['uuid']==q['uuid']),None);objects.append({'kind':kind,'object':q,'original198b_same_UUID_record':old,'nearby_actual_pad_roles':near,'current_source_quiet_VOS_feedback_role_must_be_reconciled_before_any_reroute':True})
 assert len(objects)==2;rec,trees=F.build({**h,'zones':[]});rows=[]
 for pin,start,ends in [('T4',[157.69,95.677],[[157.69,96.477],[157.69,97.177],[157.29,96.077],[158.09,96.077]]),('R7',[160.09,94.877],[[159.69,94.477],[159.69,95.277]])]:
  for end in ends:
   axis=LineString([start,end]);errs=[]
   for j in trees['F.Cu'].query(axis.buffer(.85),predicate='intersects'):
    q=rec['F.Cu'][int(j)]
    if C.norm(q['net'])=='/LOGIC_GND':continue
    if q['kind']=='track':t=q['source'];gap=axis.distance(LineString([t['a'],t['b']]))-.1-t['w']/2
    elif q['kind']=='via':v=q['source'];gap=axis.distance(Point(v['x'],v['y']))-.1-v['d']/2
    else:gap=axis.distance(q['shape'])-.1
    req=GP.G.gap(h,'/LOGIC_GND',q['net'])+.025
    if gap<req:errs.append({'kind':'literal_old_F_Cu','UUID':q['uuid'],'object_kind':q['kind'],'raw_net':q['net'],'gap_mm':gap,'required_mm':req,'source_record':q.get('source')or{a:q[a]for a in('ref','pin','uuid','net')if a in q}})
   for q in z:
    if q['layer']!='F.Cu'or C.norm(q['net'])=='/LOGIC_GND':continue
    req=max(q['clearance_mm'],GP.G.gap(h,'/LOGIC_GND',q['net']))+.025;gap=axis.distance(q['shape'])-.1
    if gap<req:errs.append({'kind':'owned_NEW_F_plane_only_nominatable_bounded_notch','UUID':q['uuid'],'raw_net':q['net'],'gap_mm':gap,'required_mm':req,'physical_WKB_sha256':hashlib.sha256(q['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(q['zone_outline_shape'].wkb).hexdigest()})
   rows.append({'pin':pin,'literal_fullwidth_0p2_F_axis':[start,end],'blockers':errs})
 put(O/'literal-B-under-R7-blocker-roles.json',objects);put(O/'literal-F-escape-wall-rows.json',rows);put(O/'precision-restoration.json',replay);put(O/'receipt.json',{'verdict':'EXACT_LITERAL_TRACK_PAD_VIA_AND_OWNED_F_PLANE_WALL_ATTRIBUTION_NO_CU_CHANGE','model_sha256':sha(mp),'R253_failed_search_sha256':sha(tp),'B_blocker_roles_sha256':sha(O/'literal-B-under-R7-blocker-roles.json'),'F_escape_attribution_sha256':sha(O/'literal-F-escape-wall-rows.json'),'no_original_actual_pads_source_signal_current_rules_or_geometry_replaced':True,'all_gate_failures_retained_no_nominal_rule_or_private_barrel_workaround':True,'native_jobs':0,'board_written':False,'script_sha256':sha(__file__)});print('R254_COMPLETE',sha(O/'receipt.json'),[(q['object']['net'],q['object'].get('w'))for q in objects],flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
