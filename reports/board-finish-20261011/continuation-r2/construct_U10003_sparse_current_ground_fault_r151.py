"""Apply one nominated sparse repair to the exact current R359 diagnostic.

Physical construction is separate from all contact/reference/native/current
qualification. Every previous filled record is explicitly remove-only.
"""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
import immutable_local_fill_subtraction_r254 as IM
OUT=H/'U10003-sparse-current-ground-fault-construction-r151'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'field-power/REG-U25-corrected-DIC262-sparse-current-composition-r359/model.pkl';assert sha(mp)=='52076bd44490e66b73dbd06994eea58a13f80152abdb7643cf2c3ae05e055739';g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);PS.restore_bound_generated_precision_states(b,q)
 parent=H/'U10003-fault-ground-source-barrel-reference-bridge-nominee-r150';rp=parent/'receipt.json';assert sha(rp)=='7f3538a6d8abad28ed6a468a27d2629df5647e98c641e3e2157e7b2ba5f23698';r=json.loads(rp.read_bytes());d=pickle.loads((parent/'proposed-discrete.pkl').read_bytes());nz=pickle.loads((parent/'proposed-zones.pkl').read_bytes());assert sha(parent/'proposed-discrete.pkl')==r['new_discrete_sha256']and sha(parent/'proposed-zones.pkl')==r['new_zones_sha256'];assert not r['B_ground_stub_true_Cu_errors'];assert all(row['fault_outside_caps_gap_empty']and not row['foreign_effective_fill_overlap_obligations']for row in r['rows']);assert len(d['tracks'])==3 and len(d['vias'])==1 and len(nz)==2;delete=set(r['exact_original_fault_delete_UUIDs']);oldtracks={t['uuid']:t for t in h['tracks']};assert delete<=set(oldtracks)
 reference=pickle.loads((H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl').read_bytes())[1];assert all(oldtracks[u]==next(t for t in reference['tracks']if t['uuid']==u)for u in delete);assert not({t['uuid']for t in d['tracks']}&set(oldtracks));assert not({v['uuid']for v in d['vias']}&{v['uuid']for v in h['vias']});h['tracks']=[t for t in h['tracks']if t['uuid']not in delete]+d['tracks'];h['vias']+=d['vias'];domains=h['domains_normalized'];gap=lambda a,bb:.15 if domains[C.norm(a)]==domains[C.norm(bb)]else.6;roleledger=[]
 for z in q:
  cuts=[]
  for v in d['vias']:
   same=C.norm(v['net'])==C.norm(z['net']);req=max(float(z['clearance_mm']),gap(v['net'],z['net']))+.025;radius=v['drill']/2 if same else max(v['drill']/2+.275,v['d']/2+req);cut=Z.bounded_disk(v,radius)
   if cut.intersects(z['shape']):
    assert same,'Foreign owned-role collision needs a separate exact joint correction';cuts.append(cut)
  if not cuts:continue
  old=z['shape'];cut=unary_union(cuts);physical=set_precision(old.difference(cut),1e-6);gain=set_precision(physical,0).difference(set_precision(old,0));assert gain.is_empty,('owned-role gain',z['uuid'],gain.area);assert set_precision(physical,0).difference(set_precision(z['zone_outline_shape'],0)).is_empty;z['shape']=physical;roleledger.append({'UUID':z['uuid'],'role':'shape','before_WKB_sha256':hashlib.sha256(old.wkb).hexdigest(),'after_WKB_sha256':hashlib.sha256(physical.wkb).hexdigest(),'only_own_new_physical_drill':True,'exact_intended_unchanged':True,'removed_mm2':old.difference(physical).area})
 # Hold every other old proposal role against the new copper and bands.
 errors=[]
 for z in q:
  for item in d['tracks']+d['vias']:
   via='d'in item;same=C.norm(item['net'])==C.norm(z['net'])
   if same or(not via and item['layer']!=z['layer']):continue
   req=max(float(z['clearance_mm']),gap(item['net'],z['net']))+.025;radius=max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=Z.bounded_disk(item,radius)if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
   if cut.intersects(z['shape']):errors.append({'new_UUID':item['uuid'],'owned_UUID':z['uuid'],'intersection_mm2':cut.intersection(z['shape']).area})
  for n in nz:
   if n['layer']==z['layer']and C.norm(n['net'])!=C.norm(z['net']):
    req=max(float(n['clearance_mm']),float(z['clearance_mm']),gap(n['net'],z['net']))+.025;cut=Z.bounded_buffer(n['shape'],req)
    if cut.intersects(z['shape']):errors.append({'new_UUID':n['uuid'],'owned_UUID':z['uuid'],'intersection_mm2':cut.intersection(z['shape']).area})
 put(OUT/'held-owned-role-guard-errors.json',errors);assert not errors,'Frozen current owned roles remain hard'
 zones=[];ledger=[]
 for old in before['zones']:
  z={**old,'fills':{}};local=float(old['clearance_mm'])
  for layer,rs in old['fills'].items():
   original=unary_union(C.poly(rs));cuts=[]
   for item in d['tracks']+d['vias']:
    via='d'in item;same=C.norm(item['net'])==C.norm(z['net'])
    if not via and(item['layer']!=layer or same):continue
    req=max(local,gap(item['net'],z['net']))+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=Z.bounded_disk(item,radius)if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    if cut.intersects(original):cuts.append(cut)
   for n in nz:
    if n['layer']!=layer or C.norm(n['net'])==C.norm(z['net']):continue
    req=max(local,float(n['clearance_mm']),gap(n['net'],z['net']))+.025;cut=Z.bounded_buffer(n['shape'],req)
    if cut.intersects(original):cuts.append(cut)
   if cuts:
    z['fills'][layer],row=IM.subtract(rs,cuts,OUT,z['uuid']+'-'+layer);ledger.append({'UUID':z['uuid'],'net':z['net'],'layer':layer,'cuts':len(cuts),**row})
   else:z['fills'][layer]=copy.deepcopy(rs)
  zones.append(z)
 for n in nz:
  for role in('shape','zone_outline_shape'):
   p=set_precision(n[role],1e-6,mode='pointwise');assert p.wkb==n[role].wkb;n[role]=p
  q.append(n);zones.append({'uuid':n['uuid'],'net':n['net'],'priority':n['priority'],'clearance_mm':n['clearance_mm'],'min_thickness_mm':n['min_thickness_mm'],'pad_connect_mode':n['pad_connect_mode'],'island_removal_mode':n['island_removal_mode'],'thermal_gap_mm':n['thermal_gap_mm'],'thermal_bridge_width_mm':n['thermal_bridge_width_mm'],'fills':{n['layer']:IM.records(n['shape'])},'prospective_not_native':True})
 b['restored_generated_grid_UUIDs']=[z['uuid']for z in q];b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(z[role].wkb).hexdigest()}for z in q for role in('shape','zone_outline_shape')];b['U10003_r151_exact_sparse_authority']={'nominee_receipt_file':str(rp),'nominee_receipt_sha256':sha(rp),'old_deleted_UUIDs':sorted(delete),'old_signal_aperture_reference_current_native_qualification':'OPEN; no automatic aperture or readiness credit'};after={**h,'zones':zones};put(OUT/'actual-filled-remove-only-ledger.json',ledger);put(OUT/'owned-own-physical-drill-only-ledger.json',roleledger);(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));put(OUT/'receipt.json',{'verdict':'SPARSE_PHYSICAL_CONSTRUCTION_ONLY_ALL_CONTACT_STRICT_REFERENCE_TRUE_GEOMETRY_SOURCE_CURRENT_NATIVE_OPEN','base_model_file':str(mp),'base_model_sha256':sha(mp),'nominee_receipt_sha256':sha(rp),'model_file':str(OUT/'model.pkl'),'model_sha256':sha(OUT/'model.pkl'),'three_exact_old_fault_deletes':sorted(delete),'new_tracks':3,'new_ordinary_vias':1,'new_FG_reference_roles':2,'existing_owned_only_own_new_drill_changes':roleledger,'existing_actual_filled_layer_cut_count':len(ledger),'every_existing_fill_strict_subset':True,'every_native_design_pad_FP_rule_source_unchanged':True,'old_signal_apertures_fullbody_reference_all_current_source_and_qualification':'OPEN','inherited_CORE_ROOT42_current_native_production_flags_unchanged':True,'board_written':False,'native_jobs':0,'adopted':False});print('R151_CONSTRUCTED',sha(OUT/'receipt.json'),sha(OUT/'model.pkl'),len(ledger),flush=True)
if __name__=='__main__':main()
