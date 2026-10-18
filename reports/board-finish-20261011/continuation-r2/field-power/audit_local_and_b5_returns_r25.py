"""Independent complete corrected local aperture/contact/source-root audit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,sys
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from shapely import set_precision
from inventory import sha
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'local-and-b5-return-audit-r25'
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();rp=HERE.parent/'sbc-power/io3-field-crossings-r15';old,discrete,binding,zones,saved=pickle.loads((rp/'model.pkl').read_bytes());precids={q['uuid'] for q in zones if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'};assert len(precids)==9;zones=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precids else q for q in zones];inputs={}
 for name,key in [('source-rooted-local-field-returns-r6','proposal_sha256'),('bridged-field-ground-dogbones-r8','proposed_zones_sha256'),('logic-island-repair-r18','proposal_sha256')]:
  path=HERE/name;rr=json.loads((path/'receipt.json').read_text());assert sha(path/'proposed-zones.pkl')==rr[key];zones+=pickle.loads((path/'proposed-zones.pkl').read_bytes());inputs[name]=sha(path/'receipt.json')
 r8p=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((r8p/'receipt.json').read_text());assert sha(r8p/'proposed-discrete.pkl')==r8['proposed_discrete_sha256'];ds=pickle.loads((r8p/'proposed-discrete.pkl').read_bytes());repairp=HERE/'ordinary-field-via-repair-r17';repair=json.loads((repairp/'receipt.json').read_text());assert sha(repairp/'proposed-discrete.pkl')==repair['proposed_discrete_sha256'];rd=pickle.loads((repairp/'proposed-discrete.pkl').read_bytes());bad=set(repair['remove_rejected_via_UUIDs']);badstub=repair['remove_rejected_stub_UUID'];nv=[q for q in ds['vias'] if q['uuid'] not in bad]+rd['vias'];nt=[q for q in ds['tracks'] if q['uuid']!=badstub]+rd['tracks'];inputs[repairp.name]=sha(repairp/'receipt.json')
 for name in('fine-outer-field-ground-joins-r9','extended-outer-field-ground-joins-r11'):
  path=HERE/name;rr=json.loads((path/'receipt.json').read_text());assert sha(path/'proposed-tracks.pkl')==rr['proposal_sha256'];nt+=pickle.loads((path/'proposed-tracks.pkl').read_bytes());inputs[name]=sha(path/'receipt.json')
 logicp=HERE/'logic-island-repair-r18';logic=json.loads((logicp/'receipt.json').read_text());viaid=logic['existing_via_UUID'];oldvia=next(q for q in discrete['vias'] if q['uuid']==viaid);assert sorted(oldvia['flashed'])==sorted(logic['existing_native_flash_mask']);newvia={**oldvia,'flashed':sorted(set(oldvia['flashed'])|{logic['prospective_additional_flash_layer']}),'prospective_extra_flash_native_required':True};h={**discrete,'tracks':discrete['tracks']+nt,'vias':[newvia if q['uuid']==viaid else q for q in discrete['vias']]+nv}
 for label in('remaining-field-ground-feeds-r23','b5-source-rooted-feeds-r4'):
  extra=HERE/label;er=json.loads((extra/'receipt.json').read_text());assert sha(extra/'proposed-discrete.pkl')==er['proposed_discrete_sha256'];ed=pickle.loads((extra/'proposed-discrete.pkl').read_bytes());assert sha(extra/'proposed-zones.pkl')==er['proposed_zones_sha256'];ez=pickle.loads((extra/'proposed-zones.pkl').read_bytes());nv+=ed['vias'];nt+=ed['tracks'];zones+=ez;inputs[label]=sha(extra/'receipt.json');h={**h,'tracks':h['tracks']+ed['tracks'],'vias':h['vias']+ed['vias']}
 assert len(nv)==25 and len(nt)==108
 smd=[{'uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'raw_net':q['net'],'layer':l,'shape':unary_union(C.poly(ps))} for q in h['pads'] if q['smd'] for l,ps in q['layers'].items() if l in('F.Cu','B.Cu')];tree=STRtree([q['shape'] for q in smd]);ph=[{'uuid':q['uuid'],'shape':s} for q in h['pads'] for s in C.poly(q.get('hole') or [])];ht=STRtree([q['shape'] for q in ph]);aprows=[]
 for v in nv:
  p0=Point(v['x'],v['y']);errors=[];minsmd=math.inf;mindrill=math.inf
  for i in tree.query(p0.buffer(v['drill']/2+.7),predicate='intersects'):
   q=smd[int(i)];d=p0.distance(q['shape'])-v['drill']/2;minsmd=min(minsmd,d)
   if d<.275-1e-9:errors.append({k:x for k,x in q.items() if k!='shape'}|{'kind':'SMD_COPPER_APERTURE','hole_edge_gap_mm':d})
  for w in h['vias']:
   if w['uuid']==v['uuid']:continue
   d=math.hypot(v['x']-w['x'],v['y']-w['y'])-(v['drill']+w['drill'])/2;mindrill=min(mindrill,d)
   if d<.275-1e-9:errors.append({'kind':'OTHER_VIA_DRILL','uuid':w['uuid'],'hole_edge_gap_mm':d})
  for i in ht.query(p0.buffer(v['drill']/2+.7),predicate='intersects'):
   q=ph[int(i)];d=p0.distance(q['shape'])-v['drill']/2;mindrill=min(mindrill,d)
   if d<.275-1e-9:errors.append({'kind':'PAD_DRILL','uuid':q['uuid'],'hole_edge_gap_mm':d})
  aprows.append({'via_UUID':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'nearest_SMD_hole_edge_gap_mm':None if math.isinf(minsmd) else minsmd,'nearest_other_drill_edge_gap_mm':mindrill,'verdict':'PASS' if not errors else 'REJECT','violations':errors})
 widthfail=[q for q in nt if q['w']<.2-1e-9];apreceipt={'verdict':'PASS' if not widthfail and all(q['verdict']=='PASS' for q in aprows) else 'REJECT','rows':aprows,'native_min_track_width_mm':.2,'track_width_failures':widthfail,'all_SMD_including_same_net_guard_mm':.275,'all_new_retained_added_and_native_drill_guard_mm':.275,'input_receipt_SHA256s':inputs,'all_19_failed_vias_removed':True,'native_jobs':0};write(OUT/'aperture-receipt.json',apreceipt);print('aperture',apreceipt['verdict'],'vias',len(nv),'tracks',len(nt),flush=True)
 collisions=[]
 for i,a in enumerate(zones):
  for b in zones[i+1:]:
   if a['layer']!=b['layer'] or C.norm(a['net'])==C.norm(b['net']):continue
   gap=.15 if h['domains_normalized'][C.norm(a['net'])]==h['domains_normalized'][C.norm(b['net'])] else .6;d=a['shape'].distance(b['shape'])
   if d<gap+.024:collisions.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':d,'required_mm':gap+.024})
 records,trees=F.build({**h,'zones':[]});cufail=[]
 for v in nv:
  net=C.norm(v['net']);dom=h['domains_normalized'][net];disk=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=32)
  for l in v['flashed']:
   for j in trees[l].query(disk.buffer(.65),predicate='intersects'):
    q=records[l][int(j)]
    if C.norm(q['net'])==net:continue
    required=(.15 if q['domain']==dom else .6)+.025;d=disk.distance(q['shape'])
    if d<required-1e-7:cufail.append({'kind':'via','uuid':v['uuid'],'layer':l,'other_UUID':q['uuid'],'other_raw_net':q['net'],'distance_mm':d,'required_mm':required})
 for t in nt:
  net=C.norm(t['net']);dom=h['domains_normalized'][net];body=C.body(t);l=t['layer']
  for j in trees[l].query(body.buffer(.65),predicate='intersects'):
   q=records[l][int(j)]
   if C.norm(q['net'])==net:continue
   required=(.15 if q['domain']==dom else .6)+.025;d=body.distance(q['shape'])
   if d<required-1e-7:cufail.append({'kind':'segment','uuid':t['uuid'],'layer':l,'other_UUID':q['uuid'],'other_raw_net':q['net'],'distance_mm':d,'required_mm':required})
 write(OUT/'ordinary-Cu-clearance-receipt.json',{'verdict':'PASS' if not cufail else 'REJECT','failures':cufail,'all25_vias_all_screened_layers':True,'all108_segment_exact_body_checks':True,'native_domain_receipt':str((HERE.parent/'native-raw-domain-contract-r1/receipt.json').resolve())});print('ordinary-Cu',len(cufail),'foreign-zone-collisions',len(collisions),flush=True)
 print('projecting',len(zones),'planes',flush=True);after,cuts=N.projected(old,h,zones);bp=HERE/'field-io3-crossing-contact-audit-r15e';br=json.loads((bp/'receipt.json').read_text());prior=pickle.loads((bp/'groups.pkl').read_bytes());before=pickle.loads((bp/'geometry.pkl').read_bytes());nets=sorted(set(prior)|{C.norm(q['net']) for q in zones});rows=[];gg={}
 for net in nets:
  a=prior.get(net)
  if a is None:a=F.graph(before,net)
  b=F.graph(after,net);gg[net]=b;lost=losses(a,b);row={'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','lost_old_discrete_relationships':lost,'prior_groups':len(a),'new_groups':len(b)};rows.append(row);print(net,row['verdict'],len(lost),flush=True);write(OUT/'checkpoint.json',rows)
 sources=[]
 for bank,net,rootref in [('FA','/motherboard_motors/FIELD_GND','J11003'),('FB','/motherboard_do/FIELD_B_0V','J11005')]:
  groups=gg[net];ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(rootref,'2') for q in xs));rooted={q['uuid'] for q in groups[ri] if q['kind']=='pad' and q['pin']};bare=[]
  for i,xs in enumerate(groups):
   if i==ri:continue
   pads=[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]
   if pads:bare.append({'group':i,'physical_pads':pads})
  sources.append({'domain':bank,'net':net,'source_root':rootref+'.2','source_group':ri,'rooted_named_physical_pads':len(rooted),'unrooted_named_groups':bare})
 b5net='/motherboard_safety_sensor/FIELD_B_5V_PRE';bg=gg[b5net];bri=next(i for i,xs in enumerate(bg) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('L19001','2') for q in xs));b5bare=[{'group':i,'physical_pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(bg) if i!=bri and any(q['kind']=='pad' and q['pin'] for q in xs)];sources.append({'domain':'FB_B5PRE','net':b5net,'local_converter_output_root':'L19001.2','external_source':'J11005.1 via U11006 and U19028; upstream protected24 still separate root obligation','source_group':bri,'rooted_named_physical_pads':len({q['uuid'] for q in bg[bri] if q['kind']=='pad' and q['pin']}),'unrooted_named_groups':b5bare})
 (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'discrete.pkl').write_bytes(pickle.dumps(h,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(gg,protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5));(OUT/'local-owned-discrete.pkl').write_bytes(pickle.dumps({'vias':nv,'tracks':nt},protocol=5));receipt={'verdict':'PASS_RETAINED_CONTACTS_AND_ORDINARY_APERTURES_CURRENT_NATIVE_PENDING' if apreceipt['verdict']=='PASS' and not collisions and not cufail and not b5bare and all(q['verdict']=='PASS' for q in rows) else 'REPAIRED_LOCAL_MUTUAL_GATE_FAILED','rows':rows,'source_root_status':sources,'foreign_new_zone_collisions':collisions,'aperture_receipt_sha256':sha(OUT/'aperture-receipt.json'),'ordinary_Cu_clearance_receipt_sha256':sha(OUT/'ordinary-Cu-clearance-receipt.json'),'input_receipt_SHA256s':inputs,'complete_original_fill_retreat_ledger':cuts,'geometry_sha256':sha(OUT/'geometry.pkl'),'discrete_sha256':sha(OUT/'discrete.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'local_owned_discrete_sha256':sha(OUT/'local-owned-discrete.pkl'),'new_vias':len(nv),'new_segments':len(nt),'existing_LOGIC_via_extra_flash_required':{'uuid':viaid,'old_native':oldvia['flashed'],'new_layer':logic['prospective_additional_flash_layer']},'native_discrete_base_sha256':br['native_discrete_sha256'],'comparison_baseline':'r15e composed native geometry; original198b CORE and native r06/r07 remain independent obligations','B5_source_complete_but_native_refill_current_still_pending':True,'root_positive24_and_new_CORE_feeds_not_composed':True,'U11015_companion_wall_and_other5_ground_groups_not_composed':True,'full_signed_current_mesh_drop_thermal_and_native_refill_flash_gates':'OPEN','native_jobs':0,'board_written':False};write(OUT/'receipt.json',receipt);print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
