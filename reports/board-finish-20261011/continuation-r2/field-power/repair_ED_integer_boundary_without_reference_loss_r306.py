"""Explicit local intended-only lattice change; keep native fill immutable."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Polygon,MultiPolygon,LineString,Point
from shapely.ops import unary_union
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from inventory import sha
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import regional_guarded_declared_projection_r140 as P
import complete_geometry_r2 as G
import physical_reference_losses_r1 as REF
R=H/'REG-two-native-intents-literal-gain-correction-r302';B=H/'R54-native-wider-IO3-monitor-joint-audit-r214';O=H/'REG-explicit-local-integer-boundary-reference-repair-r306';ED='ed7b6af5-93e5-5f20-8977-d10ca721564d';D8='d8d8bdad-3845-5659-b172-4d0e231cdadc';IDS={ED,D8}
def write(f,v):f.write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def moved(sh,target):
 ps=[sh] if sh.geom_type=='Polygon' else list(sh.geoms);out=[];changed=0
 for p in ps:
  rings=[]
  for r in [p.exterior,*p.interiors]:
   cs=[]
   for xy in r.coords:
    if tuple(xy)==(284.272346,178.402939):cs.append(target);changed+=1
    else:cs.append(xy)
   rings.append(cs)
  out.append(Polygon(rings[0],rings[1:]))
 assert changed==1,changed
 return set_precision(out[0] if len(out)==1 else MultiPolygon(out),1e-6,mode='pointwise')
def main():
 assert not O.exists();O.mkdir();rr=json.loads((R/'receipt.json').read_text());assert sha(R/'model.pkl')==rr['model_SHA256'];g,h,b,z,c=pickle.loads((R/'model.pkl').read_bytes());_,_,_,bz,bc=pickle.loads((B/'model.pkl').read_bytes());zm={q['uuid']:q for q in z};oldm={q['uuid']:q for q in bz};q=zm[ED];original=set_precision(q['zone_outline_shape'],0);checks=[];chosen=None
 # Restore reference along the original diagonal with an explicit outward
 # integer endpoint, moving away from the actual new cutter intersection.
 rec,trees=F.build({**h,'zones':[]});tm={t['uuid']:t for t in h['tracks']};vm={v['uuid']:v for v in h['vias']}
 for rise_nm in (10,30,100,300,1000):
  target=(284.272345,round(178.402939+rise_nm*1e-6,6));intent=moved(original,target);gain=set_precision(intent,0).difference(original);trial=[]
  for other in z:
   if other['uuid']==ED or other['layer']!='In4.Cu' or C.norm(other['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],other['net']),q.get('clearance_mm',.15),other.get('clearance_mm',.15))+.025;gap=set_precision(intent,0).distance(set_precision(other['zone_outline_shape'],0))
   if gap<req+.01:trial.append({'kind':'changed_intended_to_foreign_intended','UUID':other['uuid'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
  for i in trees['In4.Cu'].query(gain.buffer(.627),predicate='intersects'):
   item=rec['In4.Cu'][int(i)]
   if C.norm(item['net'])==C.norm(q['net']):continue
   req=max(G.gap(h,q['net'],item['net']),q.get('clearance_mm',.15))+.025;gap=gain.distance(item['shape'])
   if item['kind']=='track':t=tm[item['uuid']];gap=gain.distance(LineString([t['a'],t['b']]))-t['w']/2
   elif item['kind']=='via':v=vm[item['uuid']];gap=gain.distance(Point(v['x'],v['y']))-v['d']/2
   trial.append({'kind':'positive_intended_sliver_to_actual_'+item['kind'],'UUID':item['uuid'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
  for n in c['zones']:
   if n['uuid'] not in {x['uuid'] for x in h['zones']} or C.norm(n['net'])==C.norm(q['net']):continue
   records=n['fills'].get('In4.Cu',[])
   if not records:continue
   sh=unary_union(C.poly(records));req=max(G.gap(h,q['net'],n['net']),q.get('clearance_mm',.15),n.get('clearance_mm',.15))+.025;gap=gain.distance(sh)
   if gap<req+.01:trial.append({'kind':'positive_intended_sliver_to_actual_native_filled_Cu','UUID':n['uuid'],'required_mm':req,'actual_mm':gap,'PASS':gap+1e-10>=req})
  checks.append({'endpoint_mm':target,'rise_nm':rise_nm,'positive_intended_delta_mm2':gain.area,'checks':trial});print('R306 endpoint',target,'gain',gain.area,'errors',sum(not t['PASS'] for t in trial),flush=True)
  if not any(not t['PASS'] for t in trial):chosen=(intent,target,gain);break
 assert chosen is not None,'no integer endpoint clears exact foreign guards'
 intent,target,gain=chosen;q['zone_outline_shape']=intent;gainfile=O/'ED-explicit-new-native-intended-sliver.wkb';gainfile.write_bytes(gain.wkb);(O/'ED-native-intended-local-replacement.pkl').write_bytes(pickle.dumps({'UUID':ED,'old_R302_SHA256':P.digest(original),'new_intended':intent,'explicit_old_vertex_mm':[284.272346,178.402939],'explicit_new_vertex_mm':list(target),'physical_gain_credit':False},protocol=5));role_rows=[]
 for uid in IDS:
  nq=zm[uid];prior=set_precision(nq['shape'],0);outline=set_precision(nq['zone_outline_shape'],0);physical=prior.intersection(outline);nq['shape']=physical;role_rows.append({'UUID':uid,'physical_before_SHA256':P.digest(prior),'physical_after_SHA256':P.digest(physical),'intended_after_SHA256':P.digest(outline),'physical_only_removed_mm2':prior.difference(physical).area,'physical_added_mm2':physical.difference(prior).area,'physical_unsupported_mm2':physical.difference(outline).area,'intended_added_vs_R214_mm2':outline.difference(set_precision(oldm[uid]['zone_outline_shape'],0)).area})
 candidate=dict(c);candidate['zones']=[]
 for native in c['zones']:
  if native['uuid'] not in IDS:candidate['zones'].append(native);continue
  nq=copy.deepcopy(native);owned=zm[native['uuid']];nq['fills'][owned['layer']]=G.records(owned['shape']);candidate['zones'].append(nq)
 oldgroups=pickle.loads((B/'groups.pkl').read_bytes());groups={};tests=[]
 for net,ref in [('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('LOGIC_GND','J11001')]:
  old=oldgroups[net];new=F.graph(candidate,net);groups[net]=new;root=lambda gs:next(xs for xs in gs if any(i['kind']=='pad' and(i['ref'],i['pin'])==(ref,'2') for i in xs));a,bb=root(old),root(new);a_refs={outer:unary_union([i['shape'] for i in a if i['kind']=='fill' and i['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};b_refs={outer:unary_union([i['shape'] for i in bb if i['kind']=='fill' and i['layer']==inner]) for outer,inner in [('F.Cu','In1.Cu'),('B.Cu','In4.Cu')]};bad,proof=REF.audit(bc,a_refs,b_refs,net);contactbad=losses(old,new);missing=F.discrete_keys(a)-F.discrete_keys(bb);tests.append({'net':net,'old_contact_losses':contactbad,'prior_source_keys_lost':[list(k) for k in sorted(missing)],'strict_old_ref_losses':bad,'full_formula_proof':proof});write(O/'fresh-ground-checkpoint.json',tests);print('R306',net,'contact',len(contactbad),'source',len(missing),'refs',len(bad),flush=True)
 states=[]
 for owned in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if owned['uuid'] in IDS and role=='shape' else 1e-6;raw=owned[role].wkb;owned[role]=set_precision(owned[role],grid,mode='pointwise');assert raw==owned[role].wkb;states.append({'new_generated_UUID':owned['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':P.digest(owned[role]),'exact_WKB_unchanged':True,'explicit_effective_physical_float_role':grid==0})
 b=copy.deepcopy(b);b['generated_precision_state_ledger']=states;b['R306_explicit_native_intended_positive_sliver']={'owned_UUID':ED,'file':str(gainfile.resolve()),'SHA256':sha(gainfile),'area_mm2':gain.area,'physical_added_Cu_credit_mm2':0,'native_fill_required':True};write(O/'exact-scoped-generated-precision-states.json',states);write(O/'two-physical-support-role-ledger.json',role_rows);write(O/'explicit-integer-endpoint-and-positive-sliver-guards.json',checks);(O/'only-two-owned-replacements.pkl').write_bytes(pickle.dumps([zm[x] for x in sorted(IDS)],protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,candidate),protocol=5));(O/'ground-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));ok=not any(t['old_contact_losses'] or t['prior_source_keys_lost'] or t['strict_old_ref_losses'] for t in tests)
 out={'verdict':'EXPLICIT_NATIVE_INTEGER_BOUNDARY_LOCAL_GUARD_SUPPORT_CONTACT_REF_PASS_NATIVE_OPEN' if ok else 'EXPLICIT_NATIVE_INTEGER_BOUNDARY_REJECTED_REFERENCE_OR_CONTACT','parent_R302_receipt_SHA256':sha(R/'receipt.json'),'parent_R292_receipt_SHA256':sha(H/'REG-local-reference-true-copper-and-state-contract-r292/receipt.json'),'model_SHA256':sha(O/'model.pkl'),'owned_replacements_SHA256':sha(O/'only-two-owned-replacements.pkl'),'physical_support_role_ledger_SHA256':sha(O/'two-physical-support-role-ledger.json'),'explicit_positive_native_intended_sliver_SHA256':sha(gainfile),'explicit_positive_native_intended_sliver_mm2':gain.area,'endpoint_mm':target,'positive_native_intended_is_declared_owned_delta_not_remove_only':True,'actual_old_native_effective_fill_rows_unchanged_from_R302':True,'original_source_discrete_definitions_unrelated_owned_roles_unchanged':True,'new_physical_Cu_credit_mm2':0,'new_fresh_ground_tests':tests,'eleven_inherited_full_row_margin_failures_open':True,'native_jobs':0,'board_written':False,'adopted':False};write(O/'receipt.json',out);print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'PASS':ok,'model_SHA256':out['model_SHA256']}),flush=True)
if __name__=='__main__':main()
