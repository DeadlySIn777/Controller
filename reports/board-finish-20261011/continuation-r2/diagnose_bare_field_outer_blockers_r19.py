"""Attribute exact ordinary outer-pad exclusions to bound physical/owned masks."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
import guarded_declared_settings_projection_r58 as N
import core_inner_feed_r18 as I
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'corrected-joint-ground-base-r11/model.pkl';assert sha(mp)=='24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8'
old,h,b,z,current=pickle.loads(mp.read_bytes());records,trees=F.build({**h,'zones':[]});net='/motherboard_motors/FIELD_GND';domain=h['domains_normalized'][net]
areas=I.L.live.reservations();hardmodel={**h,'zones':[dict(q,layers=[l for l in q['layers']if l!='In3.Cu'])if C.norm(q['net'])=='/CORE_1V2'else q for q in h['zones']]}
rows=[]
for uid in['d64c464d-de71-4c7e-9d98-b870e2ad977f','6d65e765-0689-4977-98aa-e5c00d7c8922','4021795d-90df-4df0-a1b4-13cdcbdd91ac']:
 p=next(q for q in h['pads']if q['uuid']==uid);layer=next(iter(p['layers']));body=unary_union(C.poly(p['layers'][layer]));raw=p['net'];blockers=[]
 def add(kind,ident,cut,**data):
  overlap=cut.intersection(body).area
  if overlap>0:blockers.append({'kind':kind,'identity':ident,'covered_pad_area_mm2':overlap,'covers_whole_pad':cut.covers(body),**data})
 for i in trees[layer].query(body.buffer(1.5),predicate='intersects'):
  q=records[layer][int(i)]
  if q['net']==raw:continue
  gap=.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6;need=gap+.025+.000020
  if q['kind']=='track':t=q['source'];cut=N.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+need)
  elif q['kind']=='via':v=q['source'];cut=N.bounded_disk(v,v['d']/2+need)
  else:cut=N.bounded_buffer(q['shape'],need)
  add('actual_'+q['kind'],q['uuid'],cut,raw_net=q['net'],required_full_gap_mm=need,ref=q.get('ref'),pin=q.get('pin'))
 for q in z:
  if q['layer']!=layer or q['net']==raw:continue
  need=max(.15 if h['domains_normalized'][C.norm(q['net'])]==domain else .6,float(q.get('clearance_mm',.15)))+.025+.000020
  add('foreign_NEW_owned_zone',q['uuid'],N.bounded_buffer(q['shape'],need),raw_net=q['net'],required_full_gap_mm=need,label=q.get('label'))
 for i,s in enumerate(I.p.hard_shapes(hardmodel,areas,net,layer)):
  add('native_area_or_planning_source_reservation_or_isolation_courtyard',i,N.bounded_buffer(s,.025+.000020),hard_mask_bounds_mm=list(s.bounds))
 for q in h['pads']:
  for s in C.poly(q.get('hole')or[]):add('actual_pad_hole',q['uuid'],N.bounded_buffer(s,.275+.000020),ref=q['ref'],pin=q['num'])
 for v in h['vias']:add('actual_via_hole',v['uuid'],N.bounded_disk(v,v['drill']/2+.275+.000020),raw_net=v['net'])
 rows.append({'pad_uuid':uid,'ref':p['ref'],'pin':p['num'],'raw_net':raw,'layer':layer,'pad_bounds_mm':list(body.bounds),'pad_area_mm2':body.area,'exclusions':sorted(blockers,key=lambda q:-q['covered_pad_area_mm2'])})
out=H/'bare-field-pad-outer-blockers-r19.json';assert not out.exists();r={'verdict':'BOUND_ORDINARY_OUTER_PAD_EXCLUSION_DIAGNOSIS_NOT_NO_PATH_PROOF','model_sha256':sha(mp),'rows':rows,'script_sha256':sha(__file__),'no_native_Cu_or_rule_changes':True,'native_jobs':0,'adopted':False};out.write_text(json.dumps(r,indent=1)+'\n');print(json.dumps({'receipt_sha256':sha(out),'rows':rows}),flush=True)
