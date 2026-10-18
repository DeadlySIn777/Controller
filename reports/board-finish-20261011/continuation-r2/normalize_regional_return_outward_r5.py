"""Trim only R4 return additions with full analytic guards, then repeat real-source proofs."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def main():
 mp=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.is_relative_to(H) and not out.exists()
 mr=mp.with_name('receipt.json');r=json.loads(mr.read_bytes());assert sha(mp)==r['model_sha256'] and r['script_sha256']=='8c96b3d5f85275027b0aed61b8570be8bad3efbb565ce43ffc1ec93d880e5b94'
 assert r['baseline_model_sha256']=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff' and r['new_holes']==r['old_Cu_deleted']==r['old_native_zone_outlines_changed']==0
 pp=mp.with_name('proposed-zones.pkl');assert sha(pp)==r['proposed_zones_sha256'];old,h,b,zones,current=pickle.loads(mp.read_bytes());adds=pickle.loads(pp.read_bytes());ids={z['uuid']for z in adds};assert len(ids)==len(adds)
 out.mkdir();records,trees=F.build({**h,'zones':[]});carves=[];corrected=[]
 # Twenty additional nanometres is an explicit outward construction guard,
 # not a clearance tolerance or waiver. The final independent audit retains
 # the unchanged full 0.025 mm planner requirement.
 for z in adds:
  cutters=[];outline=z.get('zone_outline_shape',z['shape'])
  for i in trees[z['layer']].query(outline.buffer(1.5),predicate='intersects'):
   q=records[z['layer']][int(i)]
   if q['net']==z['net']:continue
   need=max(.15 if h['domains_normalized'][C.norm(z['net'])]==h['domains_normalized'][C.norm(q['net'])] else .6,float(z.get('clearance_mm',.15)))+.025+.000020
   if q['kind']=='track':
    t=q['source'];cut=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+need)
   elif q['kind']=='via':
    v=q['source'];cut=N.bounded_disk(v,v['d']/2+need)
   else:cut=N.bounded_buffer(q['shape'],need)
   if cut.intersects(outline):
    cutters.append(cut);carves.append({'zone_uuid':z['uuid'],'foreign_uuid':q['uuid'],'kind':q['kind'],'layer':z['layer'],'clearance_plus_planner_and_explicit_outward_guard_mm':need})
  cut=unary_union(cutters);zz=copy.deepcopy(z);zz['shape']=set_precision(z['shape'].difference(cut),1e-6);zz['zone_outline_shape']=set_precision(outline.difference(cut),1e-6)
  assert not zz['shape'].is_empty and not zz['zone_outline_shape'].is_empty and zz['shape'].difference(z['shape']).area<1e-12
  corrected.append(zz)
 rz={q['uuid']:q for q in corrected};final=[rz.get(q['uuid'],q)for q in zones]
 (out/'proposed-zones.pkl').write_bytes(pickle.dumps(corrected,protocol=5));write(out/'explicit-analytic-carves.json',carves)
 print('RETURN_OUTWARD_FULL_SOURCE_PROJECTION',len(corrected),len(carves),flush=True)
 candidate,retreat=N.projected(old,h,final);proofs=[]
 for net,ref in[('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005')]:
  root=lambda gs:next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
  pads=lambda xs:{q['uuid']for q in xs if q['kind']=='pad'and q['pin']}
  before=pads(root(F.graph(current,net)));after=pads(root(F.graph(candidate,net)));assert before<=after,'Outward normalization lost prior actual-source pad contacts'
  accepted=[x['target_pad_UUIDs']for x in r['rows']if x['net']==net and x['repair']]
  assert all(set(xs)<=after for xs in accepted),'Accepted return target no longer source-rooted'
  proof={'net':net,'all_R4_prior_actual_source_contacts_retained':True,'all_R4_accepted_targets_actual_source_rooted':True,'source_rooted_named_pads':len(after)};proofs.append(proof);print('RETURN_OUTWARD_SOURCE_PASS',net,len(after),flush=True)
 model=out/'model.pkl';model.write_bytes(pickle.dumps((old,h,b,final,candidate),protocol=5));report={**r,'verdict':'RETURN_ADDITIONS_EXPLICIT_ANALYTIC_OUTWARD_TRIM_ACTUAL_SOURCE_PASS_INDEPENDENT_NATIVE_CURRENT_OPEN','model_sha256':sha(model),'proposed_zones_sha256':sha(out/'proposed-zones.pkl'),'parent_R4_model_sha256':sha(mp),'parent_R4_receipt_sha256':sha(mr),'script_sha256':sha(Path(__file__)),'explicit_additional_outward_guard_mm':.000020,'foreign_carve_ledger_sha256':sha(out/'explicit-analytic-carves.json'),'only_new_R4_return_shapes_changed':True,'all_parent_R69_owned_shapes_and_original_native_definitions_source_Cu_pads_exact':True,'outward_actual_source_proofs':proofs,'full_projection_retreats':retreat,'wholeboard_retained_other_net_contacts_current_native_refill_DRC':'OPEN','inputs':{str(p.resolve()):sha(p)for p in(mp,mr,pp,Path(__file__),Path(N.__file__),Path(F.__file__),Path(C.__file__))},'adopted':False};write(out/'receipt.json',report);print('RETURN_OUTWARD_R5_FROZEN',sha(model),flush=True)
if __name__=='__main__':main()
