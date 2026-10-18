"""Pin unchanged primitive geometry/settings/grid operators before union; diagnostic only."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
import fast_contacts as F
import physical_reference_losses_r1 as REF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from diagnose_reference_cutter_union_precision_r229 import primitive_rows
from inventory import sha
O=H/'B3-residual-unchanged-primitive-grid-diagnostic-r235'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def root(groups):return next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs))
def main():
 assert not O.exists();O.mkdir();base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';n=H/'B3-envelope-scoped-LOGIC-projection-r233'
 g,bh,bb,bz,bc=pickle.loads((base/'model.pkl').read_bytes());ag,ah,ab,az,_=pickle.loads((n/'derived-full-input-model.pkl').read_bytes())
 prior_state={q['uuid']:{role:get_precision(q[role]) for role in ('shape','zone_outline_shape')} for q in bz};candidate_state={q['uuid']:{role:get_precision(q[role]) for role in ('shape','zone_outline_shape')} for q in az}
 restore_bound_generated_precision_states(bb,bz);restore_bound_generated_precision_states(ab,az)
 bg=pickle.loads((base/'groups.pkl').read_bytes())['/LOGIC_GND'];ng=pickle.loads((n/'scoped-groups.pkl').read_bytes());oldroot=root(bg);newroot=root(ng)
 oldref=unary_union([q['shape'] for q in oldroot if q['kind']=='fill' and q['layer']=='In1.Cu']);newref=unary_union([q['shape'] for q in newroot if q['kind']=='fill' and q['layer']=='In1.Cu']);tmap={t['uuid']:t for t in bh['tracks']};losses=json.loads((n/'reference-losses.json').read_text(encoding='utf-8'));lost=unary_union([REF.A.shape({'kind':'segment',**tmap[r['uuid']]}).intersection(oldref).difference(newref) for r in losses]);(O/'exact-residual-reference-loss.wkb').write_bytes(lost.wkb)
 bmap={q['uuid']:q for q in bz};nmap={q['uuid']:q for q in az};paired=[]
 for uid in sorted(bmap.keys()&nmap.keys()):
  q,qq=bmap[uid],nmap[uid];settings=lambda r:{k:r.get(k) for k in ('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')}
  roles={role:{'old_sha256':P.digest(q[role]),'new_sha256':P.digest(qq[role]),'exact_WKB_equal':q[role].wkb==qq[role].wkb,'old_pickle_grid_mm':prior_state[uid][role],'new_pickle_grid_mm':candidate_state[uid][role],'old_restored_grid_mm':get_precision(q[role]),'new_restored_grid_mm':get_precision(qq[role])} for role in ('shape','zone_outline_shape')}
  if all(row['exact_WKB_equal'] for row in roles.values()) and settings(q)==settings(qq):paired.append({'UUID':uid,'exact_nine_settings_equal':True,'roles':roles})
 write(O/'exact-unchanged-owned-primitive-input-states.json',paired)
 reports=[]
 for local in sorted({float(q['clearance_mm']) for q in bh['zones'] if C.norm(q['net'])=='/LOGIC_GND' and 'In1.Cu' in q['fills']}):
  old=primitive_rows(g,bh,bz,'/LOGIC_GND','In1.Cu',local);new=primitive_rows(ag,ah,az,'/LOGIC_GND','In1.Cu',local);rows=[]
  for key in sorted(set(old)|set(new)):
   a=old.get(key);b=new.get(key);same=a is not None and b is not None and a.wkb==b.wkb;extra=b.difference(a) if a is not None and b is not None else b
   if a is not None:zero=set_precision(a,0);assert zero.wkb==a.wkb
   if b is not None:zero=set_precision(b,0);assert zero.wkb==b.wkb
   rows.append({'key':list(key),'old_sha256':P.digest(a) if a is not None else None,'new_sha256':P.digest(b) if b is not None else None,'exact_WKB_equal':same,'old_grid_mm':get_precision(a) if a is not None else None,'new_grid_mm':get_precision(b) if b is not None else None,'extra_cut_intersects_residual_mm2':extra.intersection(lost).area if extra is not None else 0})
  (O/('primitive-pairs-'+str(local)+'.json')).write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
  for q in bh['zones']:
   if C.norm(q['net'])!='/LOGIC_GND' or 'In1.Cu' not in q['fills'] or float(q['clearance_mm'])!=local:continue
   original=unary_union(C.poly(q['fills']['In1.Cu']))
   if original.intersection(lost).area<1e-14:continue
   op={k:a for k,a in old.items() if a.intersects(original)};np={k:a for k,a in new.items() if a.intersects(original)}
   oc=unary_union(list(op.values()));nc=unary_union(list(np.values()));oz=unary_union([set_precision(a,0) for a in op.values()]);nz=unary_union([set_precision(a,0) for a in np.values()])
   unchanged={k:a for k,a in op.items() if k in np and a.wkb==np[k].wkb};extra=[a.difference(op[k]) if k in op else a for k,a in np.items() if k not in unchanged]
   # Diagnostic immutable baseline operation: preserve the exact already-projected
   # native physical polygon and subtract only exact new/extra primitives in
   # floating precision. Every primitive WKB/required guard remains unchanged.
   baseline_native=next(r for r in bc['zones'] if r['uuid']==q['uuid']);prior=unary_union(C.poly(baseline_native['fills']['In1.Cu']));candidate=prior
   for a in extra:candidate=candidate.difference(set_precision(a,0))
   report={'native_zone_UUID':q['uuid'],'local_clearance_mm':local,'old_rows':len(op),'new_rows':len(np),'exact_unchanged_primitive_rows':len(unchanged),'exact_changed_rows':[list(k) for k in op if k in np and k not in unchanged],'exact_added_rows':[list(k) for k in np if k not in op],'all_unchanged_WKB_and_grid_equal':all(get_precision(a)==get_precision(np[k]) for k,a in unchanged.items()),'current_union_extra_intersects_residual_mm2':nc.difference(oc).intersection(lost).area,'current_original_difference_lost_mm2':original.difference(oc).intersection(lost).difference(original.difference(nc)).area,'zero_tag_union_extra_intersects_residual_mm2':nz.difference(oz).intersection(lost).area,'zero_tag_original_difference_lost_mm2':original.difference(oz).intersection(lost).difference(original.difference(nz)).area,'immutable_baseline_extra_cut_diagnostic_lost_mm2':prior.intersection(lost).difference(candidate).area,'immutable_baseline_added_Cu_mm2':candidate.difference(prior).area,'alternative_operator_not_applied_to_model':True}
   reports.append(report);print('R235',json.dumps(report),flush=True)
 write(O/'operator-paired-attribution.json',reports);receipt={'verdict':'DIAGNOSTIC_ONLY_UNCHANGED_PRIMITIVES_PINNED_NO_ADOPTION','baseline_model_sha256':sha(base/'model.pkl'),'candidate_model_sha256':sha(n/'derived-full-input-model.pkl'),'literal_failed_reference_union_mm2':lost.area,'unchanged_owned_q_count':len(paired),'per_primitive_geometry_and_required_guards_unchanged_for_operator_comparison':True,'precision_operators_hypotheses_only':True,'reports_sha256':sha(O/'operator-paired-attribution.json'),'no_model_or_native_adoption':True,'native_jobs':0,'board_written':False}
 write(O/'receipt.json',receipt);print('R235 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
