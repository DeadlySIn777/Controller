"""Local owned-foreign-body replacement; preserve literal old return shadows.

This is a derived host proposal, not a native fill or an adopted projector.
Only d8/ed7 owned geometry is removed. Two native effective fill rows regain
tiny portions of their exact R214 copper once those owned obstacles withdraw.
Original native zone definitions, discrete copper and every policy stay exact.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,copy,hashlib
from pathlib import Path
from shapely import set_precision,from_wkb,get_precision
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from inventory import sha
H=Path(__file__).resolve().parent
for name in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/name))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
B=H/'R54-native-wider-IO3-monitor-joint-audit-r214'
N=H/'REG-seven-cached-exact-analytic-guard-audit-r262'
A=H/'R262-exact-residual-reference-attribution-r282'
E=H/'ed7-exact-local-cut-physical-reconstruction-r284'
O=H/'REG-exact-required-native-reference-mask-repair-r288'
ED='ed7b6af5-93e5-5f20-8977-d10ca721564d';D8='d8d8bdad-3845-5659-b172-4d0e231cdadc'
LG='/LOGIC_GND'
def write(path,value):path.write_text(json.dumps(value,indent=1)+'\n',encoding='utf-8')
def actual(q,layer):return unary_union(C.poly(q['fills'].get(layer,[])))
def native_role(old,cut):
 new=set_precision(set_precision(old,0).difference(set_precision(cut,0)),1e-6,mode='pointwise')
 for iteration in range(8):
  gain=set_precision(new,0).difference(set_precision(old,0))
  if gain.area<1e-12:break
  new=set_precision(set_precision(new,0).difference(set_precision(P.bounded_buffer(gain,.000003),0)),1e-6,mode='pointwise')
 assert set_precision(new,0).difference(set_precision(old,0)).area<1e-12
 return new
def main():
 assert not O.exists();O.mkdir()
 assert sha(N/'model.pkl')=='df45c8472f42fce952fb87afda55c4be10031bb4cc7dbfe18a24a553bb5d663d'
 assert sha(A/'receipt.json')=='1fca7adbeb328a9feb7c42c556a7895fd4ac243a2c02e730aa00b608f59717b4'
 assert sha(E/'corrected-owned-ed7-only.pkl')=='ddccee4c2744c92261e8245315445b1d364ea584d7dfd37e0584a7387df2271b'
 _,_,_,bz,bc=pickle.loads((B/'model.pkl').read_bytes())
 g,h,b,z,c=pickle.loads((N/'model.pkl').read_bytes());z=copy.deepcopy(z)
 replacement=pickle.loads((E/'corrected-owned-ed7-only.pkl').read_bytes())[0]
 z=[replacement if q['uuid']==ED else q for q in z];zm={q['uuid']:q for q in z}
 baseline_native={q['uuid']:q for q in bc['zones']};candidate_native={q['uuid']:q for q in c['zones']}
 attrib=json.loads((A/'receipt.json').read_text(encoding='utf-8'))['rows'];patches={};patch_rows=[]
 for row in attrib:
  if row['ground']!=LG:continue
  loss=from_wkb(Path(row['lost_reference_WKB_file']).read_bytes());assert P.digest(loss)==row['lost_reference_WKB_sha256']
  for contribution in row['atomic_effective_source_fill_removal_attribution']:
   assert not contribution['belongs_owned_NEW_plane'];uid=contribution['fill_UUID'];layer=row['reference_layer']
   old=actual(baseline_native[uid],layer);needed=old.intersection(set_precision(P.bounded_buffer(loss,.00005),0))
   assert loss.difference(needed).area<1e-12
   patches.setdefault((uid,layer),[]).append(needed)
   patch_rows.append({'old_track_UUID':row['uuid'],'native_fill_UUID':uid,'layer':layer,'exact_lost_reference_SHA256':P.digest(loss),'restore_support_patch_SHA256':P.digest(needed),'support_patch_mm2':needed.area,'patch_is_subset_of_exact_R214_actual_native_fill':needed.difference(old).area<1e-12,'extra_local_support_mm':.00005})
 patches={k:unary_union(v) for k,v in patches.items()};cuts={};restore={};native_rows=[]
 for (uid,layer),patch in patches.items():
  native=baseline_native[uid];old=actual(native,layer);prior=actual(candidate_native[uid],layer)
  assert C.norm(native['net'])==LG
  key=D8 if layer=='In1.Cu' else ED;owned=zm[key]
  required=max(G.gap(h,native['net'],owned['net']),float(native.get('clearance_mm',.15)),float(owned.get('clearance_mm',.15)))+.025
  assert abs(required-.625)<1e-10
  cutter=set_precision(P.bounded_buffer(patch,required+.0000001),0);cuts.setdefault(key,[]).append(cutter)
  sh=prior.union(patch);assert sh.difference(old).area<1e-12
  restore[(uid,layer)]=sh
  native_rows.append({'native_fill_UUID':uid,'layer':layer,'R214_native_actual_SHA256':P.digest(old),'R262_native_actual_SHA256':P.digest(prior),'restored_actual_SHA256':P.digest(sh),'regained_vs_failed_R262_mm2':sh.difference(prior).area,'never_added_outside_R214_actual_Cu_mm2':sh.difference(old).area,'restored_patch_SHA256':P.digest(patch),'foreign_owned_UUID':key,'unchanged_required_domain_gap_plus_guard_mm':required,'explicit_constructor_reserve_mm':.0000001,'owned_cutter_SHA256':P.digest(cutter)})
 delta=[]
 for uid,parts in cuts.items():
  q=zm[uid];cut=unary_union(parts);cutfile=O/(uid+'-required-reference-preserving-owned-cutter.wkb');cutfile.write_bytes(cut.wkb)
  for role in ('shape','zone_outline_shape'):
   old=q[role];new=set_precision(old,0).difference(cut) if role=='shape' else native_role(old,cut)
   assert new.difference(set_precision(old,0)).area<1e-12
   q[role]=new;delta.append({'owned_UUID':uid,'role':role,'before_WKB_SHA256':P.digest(old),'after_WKB_SHA256':P.digest(new),'old_precision_grid_mm':get_precision(old),'explicit_after_precision_grid_mm':get_precision(new),'only_removed_mm2':old.difference(new).area,'positive_gain_mm2':new.difference(old).area,'cutter_file':str(cutfile.resolve()),'cutter_file_SHA256':sha(cutfile)})
 # Rebuild only effective fill rows whose precise owned obstacle or restored
 # native boundary changed. No native zone definition or object is replaced.
 candidate=dict(c);candidate['zones']=[]
 for q in c['zones']:
  uid=q['uuid']
  if uid in (ED,D8):
   nq=copy.deepcopy(q);layer=zm[uid]['layer'];assert list(nq['fills'])==[layer];nq['fills'][layer]=G.records(zm[uid]['shape']);candidate['zones'].append(nq)
  elif any(k[0]==uid for k in restore):
   nq=copy.deepcopy(q)
   for (key,layer),sh in restore.items():
    if key==uid:nq['fills'][layer]=G.records(sh)
   candidate['zones'].append(nq)
  else:candidate['zones'].append(q)
 # Actual complete native fill guard scan for each changed owned body. Strict
 # nearest distances retain literal native floating Cu, never a snapped mask.
 nativeids={q['uuid'] for q in h['zones']};guards=[]
 for uid in (ED,D8):
  q=zm[uid];sh=q['shape'];layer=q['layer']
  for native in candidate['zones']:
   if native['uuid'] not in nativeids or C.norm(native['net'])==C.norm(q['net']):continue
   body=actual(native,layer)
   if body.is_empty:continue
   required=max(G.gap(h,native['net'],q['net']),float(native.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025
   gap=body.distance(sh)
   if gap<required+.001:guards.append({'kind':'changed_owned_to_actual_native_fill','owned_UUID':uid,'foreign_UUID':native['uuid'],'foreign_raw_net':native['net'],'layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})
  for other in z:
   if other['uuid']==uid or other['layer']!=layer or C.norm(other['net'])==C.norm(q['net']):continue
   required=max(G.gap(h,other['net'],q['net']),float(other.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025;gap=other['shape'].distance(sh)
   if gap<required+.001:guards.append({'kind':'changed_owned_to_foreign_owned','owned_UUID':uid,'foreign_UUID':other['uuid'],'layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})
 # Scan restored actual native patches against EVERY foreign owned plane.
 for (uid,layer),sh in restore.items():
  native=baseline_native[uid]
  for other in z:
   if other['layer']!=layer or C.norm(other['net'])==LG:continue
   required=max(G.gap(h,other['net'],native['net']),float(other.get('clearance_mm',.15)),float(native.get('clearance_mm',.15)))+.025;gap=other['shape'].distance(sh)
   if gap<required+.001:guards.append({'kind':'restored_actual_native_to_foreign_owned','owned_UUID':other['uuid'],'foreign_UUID':uid,'layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})
 write(O/'all-actual-native-and-owned-guard-checks.json',guards);write(O/'exact-local-reference-patches.json',patch_rows);write(O/'owned-remove-only-role-ledger.json',delta);write(O/'actual-native-effective-fill-restoration-ledger.json',native_rows)
 print('R288 geometry',len(guards),'guards',sum(not q['PASS'] for q in guards),flush=True)
 oldgroups=pickle.loads((B/'groups.pkl').read_bytes());groups={};refs=[];contacts=[];sources=[]
 for net,rootref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),(LG,'J11001')]:
  old=oldgroups[net];new=F.graph(candidate,net);groups[net]=new;root=lambda rows:next(xs for xs in rows if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));a,bb=root(old),root(new);bad=losses(old,new);missing=F.discrete_keys(a)-F.discrete_keys(bb)
  before_refs={outer:unary_union([q['shape'] for q in a if q['kind']=='fill' and q['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};after_refs={outer:unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};refbad,proof=REF.audit(bc,before_refs,after_refs,net)
  contacts.append({'net':net,'losses':bad});sources.append({'net':net,'prior_source_keys_lost':[list(k) for k in sorted(missing)]});refs.append({'net':net,'retained_outer_reference_losses':refbad,'full_formula_proof':proof});print('R288',net,'contacts',len(bad),'source',len(missing),'refs',len(refbad),flush=True);write(O/'contact-checkpoint.json',contacts);write(O/'reference-checkpoint.json',refs)
 b=copy.deepcopy(b);b['R288_scoped_alternative_host_reference_repair']={'baseline_model_sha256':sha(B/'model.pkl'),'failed_model_sha256':sha(N/'model.pkl'),'only_two_owned_physical_roles_grid0_intended_grid1nm':True,'native_effective_fill_regain_subset_of_exact_baseline_only':True,'original_native_definitions_unchanged':True,'strict_full_joint_projection_and_native_qualification_required':True}
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,candidate),protocol=5));(O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(O/'only-two-owned-replacements.pkl').write_bytes(pickle.dumps([zm[ED],zm[D8]],protocol=5));write(O/'contacts.json',contacts);write(O/'sources.json',sources);write(O/'references.json',refs)
 ok=not any(not q['PASS'] for q in guards) and not any(q['losses'] for q in contacts) and not any(q['prior_source_keys_lost'] for q in sources) and not any(q['retained_outer_reference_losses'] for q in refs)
 rec={'verdict':'SCOPED_OLD_REFERENCE_REPAIR_PASS_FULL_JOINT_NATIVE_REVIEW_OPEN' if ok else 'SCOPED_OLD_REFERENCE_REPAIR_REJECTED','input_rejected_R262_model_SHA256':sha(N/'model.pkl'),'R214_baseline_model_SHA256':sha(B/'model.pkl'),'R284_ed7_reconstruction_receipt_SHA256':sha(E/'receipt.json'),'only_changed_owned_UUIDs':[ED,D8],'actual_guard_errors':[q for q in guards if not q['PASS']],'ground_contact_losses':sum(len(q['losses']) for q in contacts),'prior_source_keys_lost':sum(len(q['prior_source_keys_lost']) for q in sources),'strict_old_reference_losses':sum(len(q['retained_outer_reference_losses']) for q in refs),'model_SHA256':sha(O/'model.pkl'),'owned_replacements_SHA256':sha(O/'only-two-owned-replacements.pkl'),'native_jobs':0,'board_written':False,'adopted':False,'physical_grid0_intended_grid1nm_requires_new_explicit_replay_adapter':True,'all_full_joint_current_and_native_gates_open':True};write(O/'receipt.json',rec);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'verdict':rec['verdict'],'guard_errors':len(rec['actual_guard_errors']),'contacts':rec['ground_contact_losses'],'source':rec['prior_source_keys_lost'],'refs':rec['strict_old_reference_losses']}),flush=True)
if __name__=='__main__':main()
