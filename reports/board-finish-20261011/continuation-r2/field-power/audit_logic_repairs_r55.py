"""Independent R53 repair proof with complete R25 retained-contact comparison."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from u11015_projection_r49 import correct_original_fills
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
OUT=HERE/'logic-r53-full-contact-audit-r55'

def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();rp=HERE/'logic-core-split-repair-r53';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'base-model.pkl')==rr['base_model_sha256'];g,h,binding,zones,_=pickle.loads((rp/'base-model.pkl').read_bytes());assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256'];adds=pickle.loads((rp/'proposed-zones.pkl').read_bytes());zones+=adds;pids={z['uuid'] for z in zones if z.get('label')=='CORE-main-In2' or z.get('label','').startswith('IO3-r15-field-crossing-') or z.get('field_return_proposal') and z['layer']=='In2.Cu'};assert len(pids)==9;zones=[{**z,'shape':set_precision(z['shape'],1e-6)} if z['uuid'] in pids else z for z in zones];r44p=HERE/'u11015-reverse-companion-repair-r44';r44=json.loads((r44p/'receipt.json').read_text());assert sha(r44p/'proposed-discrete.pkl')==r44['proposed_discrete_sha256'];d=pickle.loads((r44p/'proposed-discrete.pkl').read_bytes());removed={q['uuid'] for q in r44['owned_original_track_removals']};print('project independent R53',len(zones),flush=True);after,cuts=N.projected(g,h,zones);after,roundcuts=correct_original_fills(after,d['vias']);bp=HERE/'local-and-b5-return-audit-r25';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'groups.pkl')==br['groups_sha256'];prior=pickle.loads((bp/'groups.pkl').read_bytes());before=pickle.loads((bp/'geometry.pkl').read_bytes());rows=[];groups={};rec,trees=F.build({**h,'zones':[]});Cu=[];foreign=[]
 for z in adds:
  for i in trees[z['layer']].query(z['shape'].buffer(.626),predicate='intersects'):
   q=rec[z['layer']][int(i)]
   if q['net']==z['net']:continue
   req=.15 if q['domain']==h['domains_normalized'][C.norm(z['net'])] else .6;dist=z['shape'].distance(q['shape'])
   if dist<req+.025-2e-6:Cu.append({'zone_UUID':z['uuid'],'other_UUID':q['uuid'],'other_raw_net':q['net'],'layer':z['layer'],'gap_mm':dist,'required_mm':req+.025})
  for q in zones:
   if q['layer']!=z['layer'] or q['net']==z['net']:continue
   req=.15 if h['domains_normalized'][C.norm(q['net'])]==h['domains_normalized'][C.norm(z['net'])] else .6;dist=z['shape'].distance(q['shape'])
   if dist<req+.025-2e-6:foreign.append({'zone_UUID':z['uuid'],'other_zone_UUID':q['uuid'],'layer':z['layer'],'gap_mm':dist,'required_mm':req+.025})
 write(OUT/'new-zone-clearance-receipt.json',{'verdict':'PASS' if not Cu and not foreign else 'REJECT','Cu_failures':Cu,'foreign_zone_failures':foreign});print('new-plane guards',len(Cu),len(foreign),flush=True)
 for net in sorted(set(prior)|{C.norm(q['net']) for q in d['tracks']}):
  a=prior.get(net) or F.graph(before,net);a=[[q for q in xs if not(q['kind']=='track' and q['uuid'] in removed)] for xs in a];b=F.graph(after,net);groups[net]=b;lost=losses(a,b);row={'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','lost_retained_relationships':lost};rows.append(row);write(OUT/'checkpoint.json',rows);print(net,row['verdict'],len(lost),flush=True)
 roots=[]
 for net,ref in[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/motherboard_safety_sensor/FIELD_B_5V_PRE','L19001')]:
  ri=next(i for i,xs in enumerate(groups[net]) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));oi=next(i for i,xs in enumerate(prior[net]) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));missing=F.discrete_keys(prior[net][oi])-F.discrete_keys(groups[net][ri]);roots.append({'net':net,'source':ref+'.2','prior_source_contacts_not_rooted':[list(x) for x in sorted(missing)],'rooted_named_physical_pads':len({q['uuid'] for q in groups[net][ri] if q['kind']=='pad' and q['pin']}),'unrooted_named_groups':[i for i,xs in enumerate(groups[net]) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
 # Check every new U11015 annulus/trace against corrected prospective fills.
 zone_rows={l:[] for l in trees}
 for z in after['zones']:
  for l,rs in z['fills'].items():
   for sh in C.poly(rs):zone_rows[l].append({'shape':sh,'uuid':z['uuid'],'net':z['net'],'local':z['clearance_mm']})
 zt={l:STRtree([q['shape'] for q in xs]) for l,xs in zone_rows.items()};plane_fail=[]
 for kind,objects in [('via',d['vias']),('track',d['tracks'])]:
  for q in objects:
   sh=Point(q['x'],q['y']).buffer(q['d']/2,quad_segs=32) if kind=='via' else C.body(q)
   for l in q['flashed'] if kind=='via' else [q['layer']]:
    for i in zt[l].query(sh.buffer(.626),predicate='intersects'):
     z=zone_rows[l][int(i)]
     if z['net']==q['net']:continue
     req=max(.15 if h['domains_normalized'][C.norm(z['net'])]==h['domains_normalized'][C.norm(q['net'])] else .6,z['local'])+.025;dist=sh.distance(z['shape'])
     if dist<req-1e-7:plane_fail.append({'kind':kind,'uuid':q['uuid'],'other_zone_UUID':z['uuid'],'layer':l,'distance_mm':dist,'required_mm':req})
 (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(OUT/'discrete.pkl').write_bytes(pickle.dumps(h,protocol=5));(OUT/'proposed-zones.pkl').write_bytes(pickle.dumps(zones,protocol=5));(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));write(OUT/'outward-circular-cut-ledger.json',roundcuts)
 passed=not Cu and not foreign and not plane_fail and all(q['verdict']=='PASS' for q in rows) and all(not q['prior_source_contacts_not_rooted'] for q in roots)
 receipt={'verdict':'PASS_RESTORED_LOGIC_AND_RETAINED_FIELD_RELATIONSHIPS_PROSPECTIVE_PLANES_CURRENT_NATIVE_PENDING' if passed else 'JOINT_CONTACT_OR_PLANE_REPAIR_REQUIRED','rows':rows,'source_root_status':roots,'U11015_new_Cu_foreign_plane_failures':plane_fail,'new_zone_clearance_sha256':sha(OUT/'new-zone-clearance-receipt.json'),'input_R53_receipt_sha256':sha(rp/'receipt.json'),'input_R25_receipt_sha256':sha(bp/'receipt.json'),'input_R44_receipt_sha256':sha(r44p/'receipt.json'),'outward_round_cutter_helper_sha256':sha(HERE/'u11015_projection_r49.py'),'outward_round_cutter_ledger_sha256':sha(OUT/'outward-circular-cut-ledger.json'),'model_sha256':sha(OUT/'model.pkl'),'geometry_sha256':sha(OUT/'geometry.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'discrete_sha256':sha(OUT/'discrete.pkl'),'proposed_zones_sha256':sha(OUT/'proposed-zones.pkl'),'precise_six_explicit_old_ILIM_DVDT_removals_filtered':sorted(removed),'comparison_scope':'all exact R25 physical relationships; original198b/r06/r07 and later corrected CORE/protected/regulated models remain separate','protected_R7_R9_and_regulated_R41_not_composed':True,'native_jobs':0,'board_written':False,'full_signed_current_mesh_drop_thermal_fault_native_refill_flash_min_thickness_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(receipt['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
