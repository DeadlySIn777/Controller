"""Pin exact prior/new foreign cutter causes of small reference losses."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision,from_wkb,get_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
import complete_geometry_r2 as G
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'REG-small-reference-primitive-delta-r221'

def load_baseline():
 g,h,b,z,_=pickle.loads((H/'U10017-wider-on-exact-IO3-audit-r195/model.pkl').read_bytes());restore_bound_generated_precision_states(b,z)
 W=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201';wr=json.loads((W/'receipt.json').read_text(encoding='utf-8'));r=wr['only_one_owned_host_group_replacement'][0];old=next(q for q in z if q['uuid']==r['old_UUID']);assert all(P.digest(old[k])==v['old_sha256'] for k,v in r['roles'].items());new=pickle.loads((W/'exact-owned-IO3-one-In3-group-replacement.pkl').read_bytes());new=new[0] if isinstance(new,list) else new
 for k in ('shape','zone_outline_shape'):new[k]=set_precision(new[k],1e-6,mode='pointwise')
 c=next(v for v in h['vias'] if v['uuid']=='c55416b9-e522-5cbf-9523-ddb093be9249');new,_=P.normalize_owned_via_guards({**h,'vias':[c]},[new]);z=[new[0] if q['uuid']==old['uuid'] else q for q in z]
 return g,h,b,z

def main():
 assert not O.exists();O.mkdir();g,h,b,z=load_baseline();bm={q['uuid']:q for q in z}
 R=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r212';ag,ah,ab,az,_=pickle.loads((R/'model.pkl').read_bytes());ab['restored_generated_grid_UUIDs']=sorted({q['uuid'] for q in az});restore_bound_generated_precision_states(ab,az)
 rows=[];lr=json.loads((H/'REG-B3-exact-IO3-and-LG-loss-attribution-r217/LOGIC-reference-loss-exact-proposal-attribution.json').read_text(encoding='utf-8'))
 for r in lr:
  sh=from_wkb(Path(r['exact_lost_shape_file']).read_bytes());inner='In1.Cu' if r['layer']=='F.Cu' else 'In4.Cu';causes=[]
  for q in az:
   if q['layer']!=inner or C.norm(q['net'])=='/LOGIC_GND':continue
   old=bm.get(q['uuid'])
   if old is None or q['shape'].wkb==old['shape'].wkb:continue
   added=q['shape'].difference(old['shape']);clear=max(G.gap(ah,q['net'],'/LOGIC_GND'),float(q.get('clearance_mm',.15)),.25)+.025
   current=P.bounded_buffer(q['shape'],clear);prior=P.bounded_buffer(old['shape'],clear);extra=current.difference(prior)
   if sh.distance(current)>.00001:continue
   row={'UUID':q['uuid'],'net':q['net'],'shape_before_sha256':P.digest(old['shape']),'shape_after_sha256':P.digest(q['shape']),'shape_added_mm2':added.area,'shape_removed_mm2':old['shape'].difference(q['shape']).area,'grid_before_mm':get_precision(old['shape']),'grid_after_mm':get_precision(q['shape']),'buffer_added_mm2':extra.area,'lost_intersection_current_buffer_mm2':sh.intersection(current).area,'lost_distance_to_current_buffer_mm':sh.distance(current),'lost_intersection_extra_buffer_mm2':sh.intersection(extra).area}
   causes.append(row)
  rows.append({'track_UUID':r['uuid'],'lost_area_mm2':sh.area,'changed_primitive_candidates':causes})
 (O/'reference-cutter-delta-rows.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 print(json.dumps(rows),flush=True)
 (O/'baseline-model.pkl').write_bytes(pickle.dumps((g,h,b,z,None),protocol=5))
 (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_DIAGNOSTIC_NO_WAIVER','rows_sha256':sha(O/'reference-cutter-delta-rows.json'),'baseline_model_sha256':sha(O/'baseline-model.pkl')},indent=1)+'\n',encoding='utf-8');print('R221 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
