"""Independent analytic discrete/aperture/reservation and outside-contact audit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,re,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'u19008-independent-analytic-audit-r86'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'c-u19008-actual-regulated-search-base-r84';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'model.pkl')==br['model_sha256'];g,h,binding,zones,after=pickle.loads((bp/'model.pkl').read_bytes());assert sha(bp/'U19008-proposed-discrete.pkl')==br['U19008_proposed_discrete_sha256'];d=pickle.loads((bp/'U19008-proposed-discrete.pkl').read_bytes());ids={q['uuid'] for xs in d.values() for q in xs};old={t['uuid']:t for t in h['tracks']};vias={v['uuid']:v for v in h['vias']};rec,trees=F.build({**h,'zones':[]});fail=[];ann=[];minhole=1e9;minsmd=1e9;checks=0
 def gap(a,b,local=.15):return max(.15 if h['domains_normalized'].get(C.norm(a))==h['domains_normalized'].get(C.norm(b)) else .6,local)+.025
 def foreign_distance(test,q):
  if 'x' in test:
   xy=Point(test['x'],test['y']);radius=test['d']/2
   if q['kind']=='via':v=vias[q['uuid']];return xy.distance(Point(v['x'],v['y']))-radius-v['d']/2
   if q['kind']=='track':t=old[q['uuid']];return xy.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
   return xy.distance(q['shape'])-radius
  line=LineString([test['a'],test['b']]);radius=test['w']/2
  if q['kind']=='via':v=vias[q['uuid']];return line.distance(Point(v['x'],v['y']))-radius-v['d']/2
  if q['kind']=='track':t=old[q['uuid']];return line.distance(LineString([t['a'],t['b']]))-radius-t['w']/2
  return line.distance(q['shape'])-radius
 for kind,items in d.items():
  for test in items:
   layers=LAYERS if kind=='vias' else [test['layer']];shape=P.bounded_disk(test,test['d']/2) if kind=='vias' else P.bounded_buffer(LineString([test['a'],test['b']]),test['w']/2)
   for layer in layers:
    for j in trees[layer].query(shape.buffer(.627),predicate='intersects'):
     q=rec[layer][int(j)]
     if q['uuid']==test['uuid'] or q['net']==test['net']:continue
     actual=foreign_distance(test,q);required=gap(test['net'],q['net']);checks+=1
     if actual<required:fail.append({'kind':'analytic_discrete_Cu','uuid':test['uuid'],'foreign_uuid':q['uuid'],'foreign_kind':q['kind'],'layer':layer,'gap_mm':actual,'required_mm':required})
    for z in zones:
     if z['layer']!=layer or z['net']==test['net']:continue
     required=gap(test['net'],z['net'],float(z.get('clearance_mm',.15)))
     actual=Point(test['x'],test['y']).distance(z['shape'])-test['d']/2 if kind=='vias' else LineString([test['a'],test['b']]).distance(z['shape'])-test['w']/2
     if actual<required:fail.append({'kind':'analytic_owned_plane_Cu','uuid':test['uuid'],'foreign_uuid':z['uuid'],'layer':layer,'gap_mm':actual,'required_mm':required})
   if kind=='vias':
    point=Point(test['x'],test['y'])
    for pad in h['pads']:
     if pad['smd']:
      for layer in ('F.Cu','B.Cu'):
       for sh in C.poly(pad['layers'].get(layer,[])):
        actual=point.distance(sh)-test['drill']/2;minsmd=min(minsmd,actual)
        if actual<.275:fail.append({'kind':'every_SMD_hole_aperture','uuid':test['uuid'],'pad_uuid':pad['uuid'],'ref':pad['ref'],'pin':pad['num'],'layer':layer,'gap_mm':actual,'required_mm':.275})
     for sh in C.poly(pad.get('hole') or []):
      actual=point.distance(sh)-test['drill']/2;minhole=min(minhole,actual)
      if actual<.275:fail.append({'kind':'pad_hole_to_hole','uuid':test['uuid'],'foreign_uuid':pad['uuid'],'gap_mm':actual,'required_mm':.275})
    for v in h['vias']:
     if v['uuid']==test['uuid']:continue
     actual=math.hypot(test['x']-v['x'],test['y']-v['y'])-(test['drill']+v['drill'])/2;minhole=min(minhole,actual)
     if actual<.275:fail.append({'kind':'all_via_hole_to_hole','uuid':test['uuid'],'foreign_uuid':v['uuid'],'gap_mm':actual,'required_mm':.275})
 reserved=json.loads((C.BASE/'recovery-composite/c06/alternate-r07/reserved-r07.json').read_text());dru=(C.BASE/'recovery-composite/c06/alternate-r07/reserve/board.kicad_dru').read_text();exceptions={}
 for line in dru.splitlines():
  m=re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)',line.strip())
  if m:exceptions[m[1]]={C.norm(n) for n in re.findall(r"A\.NetName != '([^']*)'",m[2])}
 for kind,items in d.items():
  for test in items:
   layers=LAYERS if kind=='vias' else [test['layer']];sh=P.bounded_disk(test,test['d']/2) if kind=='vias' else P.bounded_buffer(LineString([test['a'],test['b']]),test['w']/2)
   for area in h['rule_areas']:
    if not set(layers)&set(area['layers']) or not area.get('no_vias' if kind=='vias' else 'no_tracks'):continue
    if any(sh.intersects(P.bounded_buffer(q,.025)) for q in C.poly(area['outline'])):fail.append({'kind':'actual_native_rule_area','uuid':test['uuid'],'area_uuid':area['uuid']})
   for area in reserved['keepouts']:
    if C.norm(test['net']) in exceptions.get(area['name'],set()) or not set(layers)&set(area['layers']):continue
    if any(sh.intersects(P.bounded_buffer(q,.025)) for q in C.poly(area['outline'])):fail.append({'kind':'frozen_D​RU_reservation','uuid':test['uuid'],'name':area['name']})
 nomination=json.loads((HERE/'u19008-coupled-power-wall-nomination-r82/receipt.json').read_text());power=[t for t in d['tracks'] if t['net']==nomination['owned_old_power_track']['net']];body=unary_union([P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2) for t in power]);outside=[]
 for row in nomination['answers'][0]['outside_contacts_preserved']:
  t=old[row['uuid']];area=body.intersection(C.body(t)).area;outside.append({**row,'replacement_contact_overlap_mm2':area})
  if area<.001:fail.append({'kind':'outside_power_contact_not_preserved','uuid':row['uuid'],'overlap_mm2':area})
 ng='/motherboard_do/FIELD_B_0V';gs=F.graph(after,ng);ri=next(i for i,xs in enumerate(gs) if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11005','2') for q in xs));root=gs[ri];rootref=unary_union([q['shape'] for q in root if q['layer']=='In4.Cu' and q['kind']=='fill']);missing=body.difference(rootref);(OUT/'new_power_B_body_without_source_rooted_In4_reference.wkb').write_bytes(missing.wkb)
 groundvia=next(v for v in d['vias'] if C.norm(v['net'])==ng)
 for v in d['vias']:
  for layer in LAYERS:
   disk=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64);hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64);copper=unary_union([q['shape'] for q in root if q['layer']==layer and q['kind']=='fill'])
   ann.append({'via_uuid':v['uuid'],'raw_net':v['net'],'layer':layer,'source_rooted_FBG_fill_annular_overlap_mm2':disk.difference(hole).intersection(copper).area,'via_is_ground':v['uuid']==groundvia['uuid'],'prospective_not_native_filled_flash':True})
 write(OUT/'analytic-errors.json',fail);write(OUT/'outside-contact-ledger.json',outside);write(OUT/'ground-fill-annular-ledger.json',ann)
 receipt={'verdict':'PASS_SCOPED_ANALYTIC_CU_DRILL_SMD_RESERVATION_AND_OUTSIDE_CONTACTS' if not fail else 'FAIL_SCOPED_GEOMETRY','input_R84_model_sha256':sha(bp/'model.pkl'),'input_U19008_discrete_sha256':sha(bp/'U19008-proposed-discrete.pkl'),'analytic_discrete_pairs_checked':checks,'errors':len(fail),'error_ledger_sha256':sha(OUT/'analytic-errors.json'),'minimum_all_via_and_pad_hole_gap_mm':minhole,'minimum_every_SMD_hole_aperture_gap_mm':minsmd,'outside_contact_ledger_sha256':sha(OUT/'outside-contact-ledger.json'),'source_ground_fill_annular_ledger_sha256':sha(OUT/'ground-fill-annular-ledger.json'),'source_rooted_In4_reference_missing_area_mm2':missing.area,'source_rooted_In4_reference_missing_WKB_sha256':sha(OUT/'new_power_B_body_without_source_rooted_In4_reference.wkb'),'reference_result':'FULL_NATIVE_OR_PROSPECTIVE_REFERENCE_ANALYSIS_OPEN' if not missing.is_empty else 'HOST_SOURCE_ROOTED_FILL_COVERS_FULL_NEW_B_POWER_BODY','all_supply_source_old_net_relationship_signed_current_drop_fault_thermal_native_flash_and_DRC_gates':'OPEN','board_written':False,'native_jobs':0};write(OUT/'receipt.json',receipt);print(receipt['verdict'],len(fail),'errors','reference missing',missing.area,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
