"""Independent corrected U19008 local geometry, actual reference and ports.

This gate deliberately does not grant whole LOGIC ground source closure,
regulated source closure or board acceptance from a local physical pass.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,math,re
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import STRtree
import contact_layout as C
import fast_contacts as F
from inventory import sha
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'u19008-corrected-independent-audit-r109';LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();bp=H/'corrected-regulated-joint-search-base-r106';assert sha(bp/'model.pkl')=='3f9086799fb85283714126d51b1e7cc8dc477ffe8a3ed0b1c06edd91071dcf39';g,h,b,z,after=pickle.loads((bp/'model.pkl').read_bytes())
 up=H/'u19008-outside-reservation-branch-tree-r89/proposed-discrete.pkl';rp=H/'u19008-retained-logic-barrel-relocation-r95/owned-replacements.pkl';ud=pickle.loads(up.read_bytes());replacement=pickle.loads(rp.read_bytes());d={k:ud[k]+replacement[k] for k in ('tracks','vias')};tracks={q['uuid']:q for q in h['tracks']};vias={q['uuid']:q for q in h['vias']};assert all(tracks[q['uuid']]==q for q in d['tracks']) and all(vias[q['uuid']]==q for q in d['vias']);rec,trees=F.build({**h,'zones':[]});fail=[];checks=0;mh=1e9;ms=1e9
 def gap(a,b,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(a))==h['domains_normalized'].get(C.norm(b)) else .6,local)+.025
 def discrete_gap(s,kind,q):
  center=Point(s['x'],s['y']) if kind=='vias' else LineString([s['a'],s['b']]);radius=s['d']/2 if kind=='vias' else s['w']/2
  if q['kind']=='via':v=vias[q['uuid']];return center.distance(Point(v['x'],v['y']))-radius-v['d']/2
  if q['kind']=='track':t=tracks[q['uuid']];return center.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
  return center.distance(q['shape'])-radius
 for kind,items in d.items():
  for test in items:
   layers=LAYERS if kind=='vias' else [test['layer']];sh=P.bounded_disk(test,test['d']/2) if kind=='vias' else P.bounded_buffer(LineString([test['a'],test['b']]),test['w']/2)
   for layer in layers:
    for j in trees[layer].query(sh.buffer(.627),predicate='intersects'):
     q=rec[layer][int(j)]
     if q['uuid']==test['uuid'] or q['net']==test['net']:continue
     actual=discrete_gap(test,kind,q);required=gap(test['net'],q['net']);checks+=1
     if actual<required:fail.append({'kind':'analytic_discrete_Cu','uuid':test['uuid'],'foreign_uuid':q['uuid'],'foreign_kind':q['kind'],'layer':layer,'gap_mm':actual,'required_mm':required})
    for q in z:
     if q['layer']!=layer or q['net']==test['net']:continue
     center=Point(test['x'],test['y']) if kind=='vias' else LineString([test['a'],test['b']]);radius=test['d']/2 if kind=='vias' else test['w']/2;actual=center.distance(q['shape'])-radius;required=gap(test['net'],q['net'],float(q.get('clearance_mm',.15)))
     if actual<required:fail.append({'kind':'analytic_mutual_plane_Cu','uuid':test['uuid'],'foreign_uuid':q['uuid'],'layer':layer,'gap_mm':actual,'required_mm':required})
   if kind=='vias':
    point=Point(test['x'],test['y'])
    for pad in h['pads']:
     if pad['smd']:
      for layer in ('F.Cu','B.Cu'):
       for q in C.poly(pad['layers'].get(layer,[])):
        actual=point.distance(q)-test['drill']/2;ms=min(ms,actual)
        if actual<.275:fail.append({'kind':'every_SMD_drill_aperture','uuid':test['uuid'],'pad_uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num'],'layer':layer,'gap_mm':actual,'required_mm':.275})
     for q in C.poly(pad.get('hole') or []):
      actual=point.distance(q)-test['drill']/2;mh=min(mh,actual)
      if actual<.275:fail.append({'kind':'pad_hole_to_hole','uuid':test['uuid'],'foreign_uuid':pad['uuid'],'gap_mm':actual,'required_mm':.275})
    for v in h['vias']:
     if v['uuid']==test['uuid']:continue
     actual=math.hypot(test['x']-v['x'],test['y']-v['y'])-(test['drill']+v['drill'])/2;mh=min(mh,actual)
     if actual<.275:fail.append({'kind':'all_via_hole_to_hole','uuid':test['uuid'],'foreign_uuid':v['uuid'],'gap_mm':actual,'required_mm':.275})
 reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 for kind,items in d.items():
  for test in items:
   layers=LAYERS if kind=='vias' else [test['layer']];sh=P.bounded_disk(test,test['d']/2) if kind=='vias' else P.bounded_buffer(LineString([test['a'],test['b']]),test['w']/2)
   for area in h['rule_areas']:
    if set(layers)&set(area['layers']) and area.get('no_vias' if kind=='vias' else 'no_tracks') and any(sh.intersects(P.bounded_buffer(q,.025)) for q in C.poly(area['outline'])):fail.append({'kind':'native_rule_area','uuid':test['uuid'],'area_uuid':area['uuid']})
   for area in reserved['keepouts']:
    if C.norm(test['net']) not in exceptions.get(area['name'],set()) and set(layers)&set(area['layers']) and any(sh.intersects(P.bounded_buffer(q,.025)) for q in C.poly(area['outline'])):fail.append({'kind':'frozen_DRU_reservation','uuid':test['uuid'],'name':area['name']})
 # Independently test actual final local return against analytic copper, not
 # the inscribed disk polygons used by broad-phase contact graph geometry.
 refq=next(q for q in z if q['uuid'] in {x['uuid'] for x in pickle.loads((H/'u19008-source-return-reference-r99/proposed-zones.pkl').read_bytes())});body=refq['shape'];refchecks=0
 for j in trees['In4.Cu'].query(body.buffer(.627),predicate='intersects'):
  q=rec['In4.Cu'][int(j)]
  if q['net']==refq['net']:continue
  if q['kind']=='via':v=vias[q['uuid']];actual=Point(v['x'],v['y']).distance(body)-v['d']/2
  elif q['kind']=='track':t=tracks[q['uuid']];actual=LineString([t['a'],t['b']]).distance(body)-t['w']/2
  else:actual=body.distance(q['shape'])
  required=gap(refq['net'],q['net'],float(refq.get('clearance_mm',.15)));refchecks+=1
  if actual<required:fail.append({'kind':'new_return_analytic_Cu','uuid':refq['uuid'],'foreign_uuid':q['uuid'],'foreign_kind':q['kind'],'gap_mm':actual,'required_mm':required})
 for q in z:
  if q['uuid']==refq['uuid'] or q['layer']!='In4.Cu' or q['net']==refq['net']:continue
  required=gap(refq['net'],q['net'],max(float(refq.get('clearance_mm',.15)),float(q.get('clearance_mm',.15))));actual=body.distance(q['shape'])
  if actual<required:fail.append({'kind':'new_return_mutual_plane_Cu','uuid':refq['uuid'],'foreign_uuid':q['uuid'],'gap_mm':actual,'required_mm':required})
 for area in h['rule_areas']:
  if 'In4.Cu' in area['layers'] and area.get('no_zones') and any(body.intersects(P.bounded_buffer(q,.025)) for q in C.poly(area['outline'])):fail.append({'kind':'new_return_native_no_zones','uuid':refq['uuid'],'area_uuid':area['uuid']})
 nomination=json.loads((H/'u19008-outside-reservation-branch-tree-r89/receipt.json').read_text());power=[t for t in ud['tracks'] if C.norm(t['net'])=='/motherboard_power_entry/FIELD_B_24V_PROTECTED'];powerbody=unary_union([P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2) for t in power]);outside=[]
 for q in nomination['answer']['all_six_outside_contacts']:
  t=tracks[q['uuid']];area=powerbody.intersection(C.body(t)).area;outside.append({'uuid':q['uuid'],'raw_net':t['net'],'positive_overlap_mm2':area})
  if area<.001:fail.append({'kind':'outside_power_contact','uuid':q['uuid'],'overlap_mm2':area})
 groups={};source=[]
 for net,ref,pin in [('/motherboard_do/FIELD_B_0V','J11005','2'),('/motherboard_do/DOB_FIELD_3V3','U11018','1'),('/motherboard_power_entry/FIELD_B_24V_PROTECTED','U11006','17')]:
  gs=F.graph(after,net);groups[net]=gs;ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,pin) for q in xs));keys=F.discrete_keys(gs[ri]);source.append({'net':net,'source':ref+'.'+pin,'source_group':ri,'rooted_named_physical_pads':len({q['uuid'] for q in gs[ri] if q['kind']=='pad' and q['pin']}),'owned_via_source_membership':{v['uuid']:any(q['uuid']==v['uuid'] for q in gs[ri]) for v in ud['vias'] if C.norm(v['net'])==net},'U19008_pin_source_membership':{q['pin']:q['uuid'] in {x['uuid'] for x in gs[ri] if x['kind']=='pad'} for xs in gs for q in xs if q['kind']=='pad' and q['ref']=='U19008'},'all_unrooted_named_groups':[{'group':i,'pads':[C.identity(q) for q in xs if q['kind']=='pad' and q['pin']]} for i,xs in enumerate(gs) if i!=ri and any(q['kind']=='pad' and q['pin'] for q in xs)]});print(net,'source groups frozen',flush=True)
 fg=groups['/motherboard_do/FIELD_B_0V'];ri=next(i for i,xs in enumerate(fg) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));rootref=unary_union([q['shape'] for q in fg[ri] if q['layer']=='In4.Cu' and q['kind']=='fill']);missing=powerbody.difference(rootref);(O/'new_power_without_actual_source_rooted_reference.wkb').write_bytes(missing.wkb)
 groundvia=next(v for v in ud['vias'] if C.norm(v['net'])=='/motherboard_do/FIELD_B_0V');ann=[]
 for layer in groundvia['flashed']:
  disk=Point(groundvia['x'],groundvia['y']).buffer(groundvia['d']/2,quad_segs=64);hole=Point(groundvia['x'],groundvia['y']).buffer(groundvia['drill']/2,quad_segs=64);cu=unary_union([q['shape'] for q in fg[ri] if q['layer']==layer and q['kind']=='fill']);ann.append({'via_uuid':groundvia['uuid'],'layer':layer,'actual_source_rooted_annular_overlap_mm2':disk.difference(hole).intersection(cu).area,'native_flash_required_not_proven':True})
 write(O/'errors.json',fail);write(O/'outside-contact-ledger.json',outside);write(O/'source-port-ledger.json',source);write(O/'ground-annular-ledger.json',ann);(O/'groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 write(O/'receipt.json',{'verdict':'PASS_SCOPED_GEOMETRY_REFERENCE_GROUND_PORTS' if not fail and missing.area<1e-10 else 'REPAIR_REQUIRED','input_R106_model_sha256':sha(bp/'model.pkl'),'corrected_native_recipe_sha256':sha(H/'u19008-corrected-native-owned-recipe-r102/receipt.json'),'analytic_discrete_pairs':checks,'analytic_local_return_pairs':refchecks,'geometry_errors':len(fail),'error_ledger_sha256':sha(O/'errors.json'),'min_all_hole_gap_mm':mh,'min_every_SMD_drill_aperture_mm':ms,'full_new_B_power_reference_gap_mm2':missing.area,'outside_contacts_sha256':sha(O/'outside-contact-ledger.json'),'source_ports_sha256':sha(O/'source-port-ledger.json'),'annular_ledger_sha256':sha(O/'ground-annular-ledger.json'),'groups_sha256':sha(O/'groups.pkl'),'LOGIC_moved_barrel_whole_source_relationships':'ROOT_CONTINUATION_PENDING','B3V3_complete_source_feed':'REG_CONSTRUCTOR_PENDING','full_ordinary_native_FLASH_old_group_reference_current_thermal_gates':'OPEN','board_written':False,'native_jobs':0});print('R109 done',len(fail),'errors',missing.area,'reference gap',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
