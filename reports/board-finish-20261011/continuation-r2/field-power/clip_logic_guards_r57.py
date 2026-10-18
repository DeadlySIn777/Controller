"""Outward-bound the two R53 new outlines; recheck the complete LOGIC graph."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,hashlib
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
from inventory import sha
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from u11015_projection_r49 import records
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-outward-guard-repair-r57'

def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def bounded_buffer(sh,d):return set_precision(sh.buffer((d+.000002)/math.cos(math.pi/256),quad_segs=64),1e-6)
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'logic-r53-full-contact-audit-r55';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];g,h,binding,zones,prior=pickle.loads((bp/'model.pkl').read_bytes());assert sha(bp/'groups.pkl')==br['groups_sha256'];oldgroups=pickle.loads((bp/'groups.pkl').read_bytes());rp=HERE/'logic-core-split-repair-r53';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256'];owned=pickle.loads((rp/'proposed-zones.pkl').read_bytes());ids={q['uuid'] for q in owned};assert len(ids)==2;rec,trees=F.build({**h,'zones':[]},layers={'F.Cu','B.Cu'});updated=[];deltas=[];fail=[];byid={}
 for z in owned:
  dom=h['domains_normalized'][C.norm(z['net'])];cuts=[]
  for i in trees[z['layer']].query(z['zone_outline_shape'].buffer(.627),predicate='intersects'):
   q=rec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   req=(.15 if q['domain']==dom else .6)+.025;cuts.append(bounded_buffer(q['shape'],req))
  for q in zones:
   if q['layer']!=z['layer'] or q['net']==z['net']:continue
   if q['shape'].distance(z['zone_outline_shape'])>.627:continue
   req=(.15 if h['domains_normalized'][C.norm(q['net'])]==dom else .6)+.025;cuts.append(bounded_buffer(q['shape'],req))
  cutter=unary_union(cuts);physical=set_precision(z['shape'].difference(cutter),1e-6);outline=set_precision(z['zone_outline_shape'].difference(cutter),1e-6);new={**z,'shape':physical,'zone_outline_shape':outline,'R53_outward_guard_corrected':True};updated.append(new);byid[z['uuid']]=new;removed=z['shape'].difference(physical);added=physical.difference(z['shape']);rf=OUT/(z['uuid']+'.removed.wkb');af=OUT/(z['uuid']+'.quantization-added.wkb');rf.write_bytes(removed.wkb);af.write_bytes(added.wkb);deltas.append({'uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'old_physical_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),'new_physical_WKB_sha256':hashlib.sha256(physical.wkb).hexdigest(),'old_intended_WKB_sha256':hashlib.sha256(z['zone_outline_shape'].wkb).hexdigest(),'new_intended_WKB_sha256':hashlib.sha256(outline.wkb).hexdigest(),'removed_area_mm2':removed.area,'positive_quantization_area_mm2':added.area,'removed_file_sha256':sha(rf),'positive_delta_file_sha256':sha(af)})
  for i in trees[z['layer']].query(physical.buffer(.627),predicate='intersects'):
   q=rec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   req=(.15 if q['domain']==dom else .6)+.025;d=physical.distance(q['shape'])
   if d<req-1e-7:fail.append({'kind':'Cu','zone_UUID':z['uuid'],'other_UUID':q['uuid'],'distance_mm':d,'required_mm':req})
  for q in zones:
   if q['layer']!=z['layer'] or q['net']==z['net']:continue
   req=(.15 if h['domains_normalized'][C.norm(q['net'])]==dom else .6)+.025;d=physical.distance(q['shape'])
   if d<req-1e-7:fail.append({'kind':'plane','zone_UUID':z['uuid'],'other_UUID':q['uuid'],'distance_mm':d,'required_mm':req})
 zones=[byid.get(z['uuid'],z) for z in zones];newfills=[]
 for z in prior['zones']:
  if z['uuid'] not in byid:newfills.append(z);continue
  q=byid[z['uuid']];newfills.append({**z,'fills':{q['layer']:records(q['shape'])}})
 after={**prior,'zones':newfills};gs=F.graph(after,'/LOGIC_GND');lost=losses(oldgroups['/LOGIC_GND'],gs);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));oi=next(i for i,xs in enumerate(oldgroups['/LOGIC_GND']) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));missing=F.discrete_keys(oldgroups['/LOGIC_GND'][oi])-F.discrete_keys(gs[ri]);physicalcontacts=[]
 for z in updated:
  hits=[C.identity(q)|{'physical_annular_or_pad_contact_mm2':q['shape'].intersection(z['shape']).area} for q in gs[ri] if q['kind']!='fill' and q['layer']==z['layer'] and q['shape'].intersection(z['shape']).area>.001];physicalcontacts.append({'uuid':z['uuid'],'layer':z['layer'],'source_root':'J11001.2','contacts':hits})
 (OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(updated,protocol=5));(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));(OUT/'logic-groups.pkl').write_bytes(pickle.dumps(gs,protocol=5));write(OUT/'shape-delta-ledger.json',deltas);write(OUT/'physical-source-contact-ledger.json',physicalcontacts)
 receipt={'verdict':'PASS_OUTWARD_GUARDS_ALL_LOGIC_RELATIONSHIPS_AND_SOURCE_CONTACTS_FINAL_COMPOSITION_PENDING' if not fail and not lost and not missing else 'OUTWARD_GUARD_OR_LOGIC_REPAIR_REQUIRED','clearance_failures':fail,'LOGIC_retained_relationship_losses':lost,'prior_J11001_source_contacts_not_rooted':[list(k) for k in sorted(missing)],'input_R55_receipt_sha256':sha(bp/'receipt.json'),'input_R53_receipt_sha256':sha(rp/'receipt.json'),'new_vias':0,'new_segments':0,'new_zones':2,'supersedes_only_R53_two_proposal_shapes':sorted(ids),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'model_sha256':sha(OUT/'model.pkl'),'logic_groups_sha256':sha(OUT/'logic-groups.pkl'),'shape_delta_ledger_sha256':sha(OUT/'shape-delta-ledger.json'),'source_contact_ledger_sha256':sha(OUT/'physical-source-contact-ledger.json'),'all_non_LOGIC_physical_Cu_in_this_local_candidate_unchanged_from_R55':True,'all18_R25_relationships_remain_by_transitive_R55_proof_and_complete_LOGIC_recheck':not lost and not missing and all(r['verdict']=='PASS' for r in br['rows']),'final_global_foreign_original_fill_restoration_projection_and_new_guard_normalization':'MANDATORY_OPEN; candidate retains older foreign fills conservatively','native_jobs':0,'board_written':False,'native_refill_min_thickness_flash_signed_mesh_drop_transient_fault_thermal_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(receipt['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
