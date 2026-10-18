"""Materialize only the bound sparse U10003 proposal on its isolated DIC head."""
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as C
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
import immutable_local_fill_subtraction_r254 as IM
OUT=H/'U10003-preserved-branch-exact-two-port-reference-construction-r174'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):p.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n')
def main():
 assert not OUT.exists();OUT.mkdir();mp=H/'U10003-sparse-current-ground-fault-construction-r153/model.pkl';assert sha(mp)=='2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8'
 g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);PS.restore_bound_generated_precision_states(b,q)
 parent=H/'U10003-exact-stub-source-seeded-ground-reference-nomination-r173';rp=parent/'receipt.json';assert sha(rp)=='2b76cfa2e66e614319f1e59778cc199e32d7a30b5100425b1f31317d2a55978e';r=json.loads(rp.read_bytes());packet=parent/'proposed-complete-sparse-delta.pkl';assert sha(packet)==r['proposed_sparse_delta_sha256'];d=pickle.loads(packet.read_bytes())
 newtracks=d['tracks'];newvias=[d['new_ordinary_signal_via'],d['new_ordinary_ground_return_via']];replace=d['replace_exact_two_unadopted_ground_roles'];delete={t['uuid']for t in d['delete_tracks']};replaceids={z['uuid']for z in replace}
 assert len(newtracks)==4 and len(newvias)==2 and len(delete)==2 and len(replaceids)==2
 oldtracks={t['uuid']:t for t in h['tracks']};assert all(oldtracks[t['uuid']]==t and t.get('prospective_not_native')for t in d['delete_tracks']);assert all(v['d']==.5 and v['drill']==.2 for v in newvias)
 h['tracks']=[t for t in h['tracks']if t['uuid']not in delete]+newtracks;h['vias']+=newvias;domains=h['domains_normalized'];gap=lambda a,bb:.15 if domains[C.norm(a)]==domains[C.norm(bb)]else.6
 # Every native old via, including the rejected relocation target, stays exact.
 assert all(next(n for n in h['vias']if n['uuid']==v['uuid'])==v for v in h0['vias'])
 roleledger=[]
 for z in q:
  if z['uuid']in replaceids:continue
  for role in ('shape','zone_outline_shape'):
   cuts=[]
   for v in newvias:
    same=C.norm(v['net'])==C.norm(z['net']);req=max(float(z['clearance_mm']),gap(v['net'],z['net']))+.025
    if same and role=='zone_outline_shape':continue
    radius=v['drill']/2 if same else max(v['drill']/2+.275,v['d']/2+req);cut=Z.bounded_disk(v,radius)
    if cut.intersects(z[role]):cuts.append(cut)
   for t in newtracks:
    if t['layer']==z['layer']and C.norm(t['net'])!=C.norm(z['net']):
     req=max(float(z['clearance_mm']),gap(t['net'],z['net']))+.025;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+req)
     if cut.intersects(z[role]):cuts.append(cut)
   if not cuts:continue
   assert z['uuid']in d['ground_roles_only_bound_local_negative_withdrawal_UUIDs'],'Every other existing owned role stays hard'
   old=z[role];literal=set_precision(old,0);cut=unary_union(cuts);new=set_precision(literal.difference(cut),1e-6,mode='pointwise');reserves=[]
   for i in range(16):
    gain=set_precision(new,0).difference(literal)
    if gain.is_empty:break
    reserve=Z.bounded_buffer(gain,.0001);(OUT/(z['uuid']+'-'+role+'-'+str(i)+'-gain.wkb')).write_bytes(gain.wkb);(OUT/(z['uuid']+'-'+role+'-'+str(i)+'-negative-reserve.wkb')).write_bytes(reserve.wkb)
    previous=new;new=set_precision(set_precision(new,0).difference(set_precision(reserve,0)).intersection(literal),1e-6,mode='pointwise');reserves.append({'raw_gain_area_mm2':gain.area,'actual_removed_mm2':set_precision(previous,0).difference(set_precision(new,0)).area,'explicit_local_negative_reserve_mm':.0001})
   assert set_precision(new,0).difference(literal).is_empty,('literal_owned_role_gain',z['uuid'],role)
   z[role]=new;roleledger.append({'UUID':z['uuid'],'role':role,'before_WKB_sha256':hashlib.sha256(old.wkb).hexdigest(),'after_WKB_sha256':hashlib.sha256(new.wkb).hexdigest(),'actual_removed_mm2':set_precision(old,0).difference(set_precision(new,0)).area,'only_bound_new_actual_antipads_and_tracks':True,'local_negative_reserves':reserves})
 q=[z for z in q if z['uuid']not in replaceids]+replace
 for z in q:assert set_precision(z['shape'],0).difference(set_precision(z['zone_outline_shape'],0)).is_empty,('physical_outside_intended',z['uuid'])
 zones=[];ledger=[]
 for old in before['zones']:
  if old['uuid']in replaceids:continue
  z={**old,'fills':{}};local=float(z['clearance_mm'])
  for layer,rs in old['fills'].items():
   original=unary_union(C.poly(rs));cuts=[]
   for item in newtracks+newvias:
    via='d'in item;same=C.norm(item['net'])==C.norm(z['net'])
    if not via and(item['layer']!=layer or same):continue
    req=max(local,gap(item['net'],z['net']))+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=Z.bounded_disk(item,radius)if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    if cut.intersects(original):cuts.append(cut)
   for n in replace:
    if n['layer']!=layer or C.norm(n['net'])==C.norm(z['net']):continue
    req=max(local,float(n['clearance_mm']),gap(n['net'],z['net']))+.025;cut=Z.bounded_buffer(n['shape'],req)
    if cut.intersects(original):cuts.append(cut)
   if cuts:z['fills'][layer],row=IM.subtract(rs,cuts,OUT,z['uuid']+'-'+layer);ledger.append({'UUID':z['uuid'],'net':z['net'],'layer':layer,'cuts':len(cuts),**row})
   else:z['fills'][layer]=copy.deepcopy(rs)
  zones.append(z)
 for z in replace:
  for role in ('shape','zone_outline_shape'):z[role]=set_precision(z[role],1e-6,mode='pointwise')
  zones.append({**{k:v for k,v in z.items()if k not in('shape','zone_outline_shape','layer')},'fills':{z['layer']:IM.records(z['shape'])},'prospective_not_native':True})
 b['restored_generated_grid_UUIDs']=[z['uuid']for z in q];b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(z[role].wkb).hexdigest()}for z in q for role in('shape','zone_outline_shape')]
 after={**h,'zones':zones};(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));put(OUT/'owned-local-negative-role-ledger.json',roleledger);put(OUT/'actual-filled-local-negative-ledger.json',ledger)
 result={'verdict':'SPARSE_U10003_TWO_PORT_PHYSICAL_CONSTRUCTION_ONLY_ALL_FRESH_CONTACT_REFERENCE_TRUE_CU_CURRENT_NATIVE_GATES_OPEN','base_model_file':str(mp),'base_model_sha256':sha(mp),'nominee_receipt_file':str(rp),'nominee_receipt_sha256':sha(rp),'model_file':str(OUT/'model.pkl'),'model_sha256':sha(OUT/'model.pkl'),'two_prior_prospective_tracks_replaced':sorted(delete),'new_tracks':len(newtracks),'new_ordinary_vias':len(newvias),'old_original_B_In3_all_native_via_shapes_positions_and_masks_exact':True,'two_new_ground_reference_roles_replaced':sorted(replaceids),'other_owned_changes':roleledger,'all_existing_actual_fills_literal_remove_only':True,'changed_filled_scopes':len(ledger),'old_three_native_B_fault_removals_inherited_from_exact_R153':'NO_ADDITIONAL_NATIVE_DELETES','all_native_design_FP_source_rule_and_project_defs_unchanged':True,'native_jobs':0,'board_written':False,'adopted':False,'manufacturing_ready':False};put(OUT/'receipt.json',result);print(json.dumps({'verdict':result['verdict'],'model_sha256':result['model_sha256'],'receipt_sha256':sha(OUT/'receipt.json'),'changed_fill_scopes':len(ledger),'old_roles_changed':len(roleledger)}),flush=True)
if __name__=='__main__':main()
