"""Independent complete R41 proposal audit against R38/R44/corrected R57.

This preserves the historical R41 and R51 files and gives no native or
current-capacity credit to a proposed all-layer barrel.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
from audit_field_io3_crossings_r15e import losses
from u11015_projection_r49 import records
from regulated_outer_joins_r51 import PORTS
HERE=Path(__file__).resolve().parent;OUT=HERE/'regulated-joint-independent-audit-r59'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir()
 bp=HERE/'regulated-outer-source-joins-r51';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'base-model.pkl')==br['base_model_sha256'];g,h,binding,zones,after=pickle.loads((bp/'base-model.pkl').read_bytes())
 rp=HERE/'regulated-field-source-feeds-r41';rr=json.loads((rp/'receipt.json').read_text());assert sha(rp/'proposed-discrete.pkl')==rr['proposed_discrete_sha256'];d=pickle.loads((rp/'proposed-discrete.pkl').read_bytes());assert sha(rp/'proposed-zones.pkl')==rr['proposed_zones_sha256'];owned=pickle.loads((rp/'proposed-zones.pkl').read_bytes())
 lp=HERE/'logic-outward-guard-repair-r57';lr=json.loads((lp/'receipt.json').read_text());assert sha(lp/'proposed-zones.pkl')==lr['proposed_zones_sha256'];newlogic={z['uuid']:z for z in pickle.loads((lp/'proposed-zones.pkl').read_bytes())};zones=[newlogic.get(z['uuid'],z) for z in zones];after={**after,'zones':[{**z,'fills':{newlogic[z['uuid']]['layer']:records(newlogic[z['uuid']]['shape'])}} if z['uuid'] in newlogic else z for z in after['zones']]}
 rec,trees=F.build({**h,'zones':[]});dom=h['domains_normalized'];holes=[]
 for q in h['pads']:
  for sh in C.poly(q.get('hole') or []):holes.append({'uuid':q['uuid'],'shape':sh})
 for q in h['vias']:holes.append({'uuid':q['uuid'],'shape':Point(q['x'],q['y']).buffer(q['drill']/2,quad_segs=64)})
 ht=STRtree([q['shape'] for q in holes]);smd=[{'uuid':q['uuid'],'shape':unary_union(C.poly(rs))} for q in h['pads'] if q['smd'] for l,rs in q['layers'].items() if l in ('F.Cu','B.Cu')];st=STRtree([q['shape'] for q in smd]);fails=[]
 def gap(a,b):return (.15 if dom.get(C.norm(a))==dom.get(C.norm(b)) else .6)+.025
 for kind,objects in [('via',d['vias']),('track',d['tracks'])]:
  for q in objects:
   if kind=='via':
    point=Point(q['x'],q['y']);sh=point.buffer(q['d']/2,quad_segs=64);ls=LAYERS
    for i in st.query(point.buffer(q['drill']/2+.276),predicate='intersects'):
     other=smd[int(i)];dist=point.distance(other['shape'])-q['drill']/2
     if dist<.275-1e-7:fails.append({'kind':'via_SMD_aperture','uuid':q['uuid'],'other_uuid':other['uuid'],'gap_mm':dist,'required_mm':.275})
    for i in ht.query(point.buffer(q['drill']/2+.276),predicate='intersects'):
     other=holes[int(i)]
     if other['uuid']==q['uuid']:continue
     dist=point.distance(other['shape'])-q['drill']/2
     if dist<.275-1e-7:fails.append({'kind':'via_drill_edge','uuid':q['uuid'],'other_uuid':other['uuid'],'gap_mm':dist,'required_mm':.275})
   else:
    sh=C.body(q);ls=[q['layer']]
    if q['w']<.2:fails.append({'kind':'track_min_width','uuid':q['uuid'],'width_mm':q['w'],'required_mm':.2})
   for l in ls:
    for i in trees[l].query(sh.buffer(.627),predicate='intersects'):
     other=rec[l][int(i)]
     if other['net']==q['net']:continue
     dist=sh.distance(other['shape']);req=gap(q['net'],other['net'])
     if dist<req-1e-7:fails.append({'kind':kind+'_physical_Cu','uuid':q['uuid'],'other_uuid':other['uuid'],'other_raw_net':other['net'],'layer':l,'gap_mm':dist,'required_mm':req})
    for other in zones:
     if other['layer']!=l or other['net']==q['net']:continue
     dist=sh.distance(other['shape']);req=gap(q['net'],other['net'])
     if dist<req-1e-7:fails.append({'kind':kind+'_new_plane','uuid':q['uuid'],'other_uuid':other['uuid'],'other_raw_net':other['net'],'layer':l,'gap_mm':dist,'required_mm':req})
 print('R41 discrete violations',len(fails),flush=True)
 for z in owned:
  for i in trees[z['layer']].query(z['shape'].buffer(.627),predicate='intersects'):
   other=rec[z['layer']][int(i)]
   if other['net']==z['net']:continue
   dist=z['shape'].distance(other['shape']);req=gap(z['net'],other['net'])
   if dist<req-1e-7:fails.append({'kind':'plane_physical_Cu','uuid':z['uuid'],'other_uuid':other['uuid'],'other_raw_net':other['net'],'layer':z['layer'],'gap_mm':dist,'required_mm':req})
  for other in zones:
   if other['layer']!=z['layer'] or other['net']==z['net']:continue
   dist=z['shape'].distance(other['shape']);req=gap(z['net'],other['net'])
   if dist<req-1e-7:fails.append({'kind':'plane_foreign_plane','uuid':z['uuid'],'other_uuid':other['uuid'],'other_raw_net':other['net'],'layer':z['layer'],'gap_mm':dist,'required_mm':req})
 write(OUT/'physical-guard-check.json',fails);print('R41 full guard violations',len(fails),flush=True)
 prior=pickle.loads((HERE/'local-and-b5-return-audit-r25/groups.pkl').read_bytes());before=pickle.loads((HERE/'local-and-b5-return-audit-r25/geometry.pkl').read_bytes());removed={q['uuid'] for q in json.loads((HERE/'u11015-reverse-companion-repair-r44/receipt.json').read_text())['owned_original_track_removals']};groups={};rows=[]
 for net in sorted(set(prior)|{net for _,net,_,_,_ in PORTS}):
  old=prior.get(net) or F.graph(before,net);old=[[q for q in xs if not(q['kind']=='track' and q['uuid'] in removed)] for xs in old];new=F.graph(after,net);groups[net]=new;lost=losses(old,new);rows.append({'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','lost_retained_relationships':lost});write(OUT/'contact-checkpoint.json',rows);print(net,rows[-1]['verdict'],len(lost),flush=True)
 roots=[]
 for bank,net,ref,pin,policy in PORTS:
  gs=groups[net];ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));roots.append({'bank':bank,'source':ref+'.'+pin,'source_group':ri,'unrooted_named_groups':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]})
 (OUT/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));(OUT/'model.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5))
 receipt={'verdict':'PASS_R41_ALL_GUARDS_AND_RETAINED_CONTACTS_INCOMPLETE_SOURCE_FEEDS' if not fails and all(q['verdict']=='PASS' for q in rows) else 'REGULATED_JOINT_REPAIR_REQUIRED','physical_guard_failures':fails,'retained_contact_rows':rows,'source_roots':roots,'input_R41_receipt_sha256':sha(rp/'receipt.json'),'input_R51_receipt_sha256':sha(bp/'receipt.json'),'input_R57_receipt_sha256':sha(lp/'receipt.json'),'groups_sha256':sha(OUT/'groups.pkl'),'model_sha256':sha(OUT/'model.pkl'),'current_scope':'exact R38 + R44 + R41 + corrected R57, older projection preserved; latest R42/R47/R9 and final bounded global projection excluded','original_native_zone_configs_unchanged':True,'native_jobs':0,'board_written':False,'native_flash_refill_current_mesh_drop_thermal_fault_gates':'OPEN'};write(OUT/'receipt.json',receipt);print(receipt['verdict'],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
