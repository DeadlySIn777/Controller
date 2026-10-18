"""Preserve exact old physical boundaries; replay only declared local cuts."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,hashlib,sys,copy
from pathlib import Path
import numpy as np
from shapely import set_precision,get_coordinates,get_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent
sys.path.insert(0,str(ROOT/'sbc-power'));sys.path.insert(0,str(ROOT/'coupled-recovery'))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
B=H/'R54-native-wider-IO3-monitor-joint-audit-r214';N=H/'REG-seven-cached-exact-analytic-guard-audit-r262';O=H/'ed7-exact-local-cut-physical-reconstruction-r284';UID='ed7b6af5-93e5-5f20-8977-d10ca721564d';NET='/motherboard_motors/FIELD_GND'
def write(p,v):p.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();assert sha(N/'receipt.json')=='683f426012983f3157ea59aee95edb394227c62d7c5d32acc46fb0078c38ae53';_,_,_,bz,bc=pickle.loads((B/'model.pkl').read_bytes());g,h,b,z,c=pickle.loads((N/'model.pkl').read_bytes());prior=next(q for q in bz if q['uuid']==UID);failed=next(q for q in z if q['uuid']==UID);fq=next(q for q in z if q['uuid']=='61cb8179-7754-5031-bbea-0da464bf816f');d=pickle.loads((N/'proposed-discrete.pkl').read_bytes());cutters=[]
 for v in d['vias']:
  req=max(G.gap(h,prior['net'],v['net']),float(prior.get('clearance_mm',.15)))+.025;cu=P.bounded_disk(v,v['d']/2+req);cutters.append({'kind':'new_actual_ordinary_barrel_clearance','UUID':v['uuid'],'raw_net':v['net'],'required_gap_mm':req,'radius_mm':v['d']/2+req,'shape':set_precision(cu,0)})
 req=max(G.gap(h,prior['net'],fq['net']),float(prior.get('clearance_mm',.15)),float(fq.get('clearance_mm',.15)))+.025;cu=P.bounded_buffer(fq['zone_outline_shape'],req);cutters.append({'kind':'new_owned_FIELD5_outline_clearance','UUID':fq['uuid'],'raw_net':fq['net'],'required_gap_mm':req,'shape':set_precision(cu,0)});cut=unary_union([r['shape'] for r in cutters]);replacement=copy.copy(prior);role_rows=[]
 for role in ('shape','zone_outline_shape'):
  old=prior[role];floating=set_precision(old,0);assert floating.wkb==old.wkb;new=floating.difference(cut);assert new.difference(old).area<1e-12
  # Effective physical Cu preserves native-derived floating boundary points.
  # The newly serialized intended outline keeps the old native integer grid.
  if role=='zone_outline_shape':
   native=set_precision(new,1e-6,mode='pointwise');gain=native.difference(old)
   for iteration in range(8):
    if gain.area<1e-12:break
    native=set_precision(set_precision(native,0).difference(set_precision(P.bounded_buffer(gain,.000003),0)),1e-6,mode='pointwise');gain=set_precision(native,0).difference(floating)
   assert gain.area<1e-12;new=native
  replacement[role]=new;coords=get_coordinates(old);frac=np.abs(coords*1e6-np.rint(coords*1e6));role_rows.append({'role':role,'old_WKB_sha256':P.digest(old),'failed_R262_WKB_sha256':P.digest(failed[role]),'corrected_WKB_sha256':P.digest(new),'old_GE0S_grid_mm':get_precision(old),'new_explicit_GE0S_grid_mm':get_precision(new),'old_max_fractional_nm':float(frac.max()),'old_noninteger_nm_coordinate_values':int((frac>1e-5).sum()),'only_declared_actual_cut_removed_mm2':old.difference(new).area,'added_Cu_vs_old_mm2':new.difference(old).area,'restored_vs_rejected_R262_mm2':new.difference(failed[role]).area,'remote_old_boundary_is_not_requantized':role=='shape'})
 # Update only this new owned filled geometry; every other candidate object
 # remains byte-identical. No native definition, settings or discrete changes.
 candidate=dict(c);candidate['zones']=[]
 for q in c['zones']:
  if q['uuid']!=UID:candidate['zones'].append(q);continue
  nq=copy.deepcopy(q);assert list(nq['fills'])==['In4.Cu'];nq['fills']['In4.Cu']=G.records(replacement['shape']);candidate['zones'].append(nq)
 gs=F.graph(candidate,NET);oldgs=pickle.loads((B/'groups.pkl').read_bytes())[NET];root=lambda groups:next(xs for xs in groups if any(x['kind']=='pad' and (x['ref'],x['pin'])==('J11003','2') for x in xs));a,bb=root(oldgs),root(gs);lost=losses(oldgs,gs);missing=F.discrete_keys(a)-F.discrete_keys(bb);oldref={out:unary_union([q['shape'] for q in a if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};newref={out:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for out,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};refbad,refproof=REF.audit(bc,oldref,newref,NET);guards=[]
 # Inspect every actual foreign native filled body against the corrected
 # physical Cu; inherited and newly introduced deficits are separate rows.
 nativeids={q['uuid'] for q in h['zones']}
 for q in candidate['zones']:
  if q['uuid'] not in nativeids or C.norm(q['net'])==NET:continue
  rs=q['fills'].get('In4.Cu',[])
  if not rs:continue
  sh=unary_union(C.poly(rs));req=max(G.gap(h,prior['net'],q['net']),float(q.get('clearance_mm',.15)),float(prior.get('clearance_mm',.15)))+.025;gap=sh.distance(replacement['shape'])
  if gap<req+.01:guards.append({'kind':'corrected_physical_plane_to_actual_native_fill','native_UUID':q['uuid'],'raw_net':q['net'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 for q in z:
  if q['uuid']==UID or q['layer']!='In4.Cu' or C.norm(q['net'])==NET:continue
  req=max(G.gap(h,prior['net'],q['net']),float(q.get('clearance_mm',.15)),float(prior.get('clearance_mm',.15)))+.025;gap=q['shape'].distance(replacement['shape'])
  if gap<req+.01:guards.append({'kind':'corrected_physical_plane_to_foreign_owned_plane','owned_UUID':q['uuid'],'raw_net':q['net'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
 for row in cutters:
  sh=row.pop('shape');row['cutter_WKB_sha256']=P.digest(sh);f=O/(row['UUID']+'-exact-cutter.wkb');f.write_bytes(sh.wkb);row['cutter_file']=str(f.resolve());row['cutter_file_sha256']=sha(f)
 (O/'corrected-owned-ed7-only.pkl').write_bytes(pickle.dumps([replacement],protocol=5));(O/'only-corrected-FAG-candidate.pkl').write_bytes(pickle.dumps(candidate,protocol=5));write(O/'corrected-role-ledger.json',role_rows);write(O/'exact-cut-primitives.json',cutters);write(O/'retained-FAG-reference-check.json',{'losses':refbad,'full_original_formula_proof':refproof});write(O/'actual-native-and-owned-guard-checks.json',guards);bad=[q for q in guards if not q['PASS']];rec={'verdict':'LOCAL_ED7_PHYSICAL_RECONSTRUCTION_FAG_REF_CONTACT_PASS_MUTUAL_GUARD_OPEN' if not refbad and not lost and not missing else 'LOCAL_ED7_RECONSTRUCTION_REJECTED','R214_model_sha256':sha(B/'model.pkl'),'rejected_R262_model_sha256':sha(N/'model.pkl'),'owned_UUID':UID,'role_ledger':role_rows,'old_FAG_contact_losses':lost,'old_FAG_source_keys_lost':[list(q) for q in sorted(missing)],'retained_FAG_outer_reference_losses':refbad,'required_actual_native_and_owned_guard_errors':bad,'corrected_owned_pickle_sha256':sha(O/'corrected-owned-ed7-only.pkl'),'explicit_physical_role_grid_zero_is_not_native_outline_grid':True,'all_unrelated_roles_settings_discrete_native_definitions_unchanged':True,'no_full_joint_projection_or_native_acceptance':True,'board_written':False,'native_jobs':0,'adopted':False};write(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'FG_refs':len(refbad),'FGcontacts':len(lost),'FGsource_missing':len(missing),'guard_errors':len(bad),'roles':role_rows}),flush=True)
if __name__=='__main__':main()
