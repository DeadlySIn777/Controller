"""Bind actual ROOT R11, exact owned DI6 additions and all latest hard Cu.

No old model overlay, native job, save, board emit or source qualification.
"""
import copy,pickle
import audit_aux_exact_raw as A
import contact_layout as L
import audit_di6_direct_latest_power_r8 as D
import guarded_power_projection_r44 as Z
import complete_geometry_r2 as GE
from shapely.geometry import LineString
from shapely.ops import unary_union
HERE=D.HERE;C=A.C
def bind(r11,cp):
 path=HERE.parent/'corrected-joint-ground-base-r11/model.pkl';old,h,binding,zones,before=pickle.loads(A.read(path));assert C.sha(A.read(path))=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8';assert before is not None;h=copy.deepcopy(h);zones=copy.deepcopy(zones)
 assert binding['exact_native_discrete_board_sha256']==r11['source_parent_sha256'];assert C.sha(A.read(binding['exact_native_discrete_board_file']))==r11['source_parent_sha256'];nt=cp['nt'];nv=cp['nv'];assert len(nt)==9 and len(nv)==2
 for k,added in(('tracks',nt),('vias',nv)):
  ids={q['uuid'] for q in h[k]};assert not ids&{q['uuid'] for q in added};h[k]+=copy.deepcopy(added)
 fillrows=[];afterzones=[]
 for z in before['zones']:
  nz={**z,'fills':{}};local=float(z.get('clearance_mm',.15));net=L.norm(z['net'])
  for l,rs in z['fills'].items():
   original=unary_union(L.poly(rs));cutters=[]
   for t in nt:
    n=L.norm(t['net'])
    if t['layer']!=l or n==net:continue
    domain=.15 if h['domains_normalized'].get(net)==h['domains_normalized'].get(n) else .6;cut=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+max(domain,local)+.025)
    if cut.intersects(original):cutters.append(cut)
   for v in nv:
    n=L.norm(v['net'])
    if n==net:radius=v['drill']/2
    else:domain=.15 if h['domains_normalized'].get(net)==h['domains_normalized'].get(n) else .6;radius=max(v['drill']/2+.275,v['d']/2+max(domain,local)+.025)
    cut=Z.bounded_disk(v,radius)
    if cut.intersects(original):cutters.append(cut)
   rem=original.difference(unary_union(cutters));nz['fills'][l]=GE.records(rem)
   if cutters:fillrows.append({'zone_UUID':z['uuid'],'layer':l,'net':z['net'],'native_or_proposed_local_mm':local,'before_WKB_sha256':C.sha(original.wkb),'after_WKB_sha256':C.sha(rem.wkb),'removed_mm2':original.difference(rem).area})
  afterzones.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':afterzones}
 print('DI15_JOINT_R11_OWN_DI6_DELTA_PROJECTED_DRILLED_SOURCE_ROOT_BEGIN',flush=True);refs,uf,groups,root=D.root_reference(after)
 receiptpath=path.with_name('receipt.json');receipt=__import__('json').loads(A.read(receiptpath));assert receipt['model_sha256']==C.sha(A.read(path));assert receipt['R10_source_spine_exact'] and receipt['all_other_R106_h_and_owned_planes_exact']
 for p,pin in receipt['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 result={'h':h,'old':old,'binding':binding,'before':before,'after':after,'zones':zones,'refs':refs,'groups':groups,'root':root,'joint_R11_model_sha256':C.sha(A.read(path)),'joint_R11_receipt_sha256':C.sha(A.read(receiptpath)),'R11_only_owned_additions_sha256':r11['saved_model_sha256'],'R10_spine_exact_sha256':receipt['R10_proposed_zones_sha256'],'exact_DI6_incremental_projection_ledger':fillrows,'all_source_roots_recomputed_after_actual_drills':True,'new_power_and_ground_planes_have_no_native_or_current_qualification':True}
 cache=HERE/'di15-current-joint-r11-projection-r34.pkl';assert not cache.exists();cache.write_bytes(pickle.dumps(result,protocol=5));print('DI15_JOINT_R11_EXACT_CURRENT_CHECKPOINT',C.sha(cache.read_bytes()),flush=True);result['checkpoint_sha256']=C.sha(cache.read_bytes());return result
