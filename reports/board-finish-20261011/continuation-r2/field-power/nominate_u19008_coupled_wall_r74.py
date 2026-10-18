"""Scoped real protected-power wall detour with paired regulator/return sites.

This stages geometry and exact retained outside contacts only. Native source,
full supply/return continuity, mesh and fault-current gates remain mandatory.
"""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,math,sys,uuid
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
from inventory import sha
import contact_layout as C
import tri_route as T
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'sbc-power'))
import guarded_power_projection_r44 as P
OUT=HERE/'u19008-coupled-power-wall-nomination-r74'
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def write(p,x):p.write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
def polys(s):return [s] if s.geom_type=='Polygon' else [q for q in getattr(s,'geoms',[]) if q.geom_type=='Polygon']
def main():
 assert not OUT.exists();OUT.mkdir();mp=HERE/'regulated-final-power-search-base-r70/model.pkl';assert sha(mp)=='1368cee2cc2e18bc670a2875f31c4148b6d8792bbc67e89e65289107d923b73d'
 g,h,binding,zones,after=pickle.loads(mp.read_bytes());uid='e4ba8462-8a7d-4860-b7bb-cccfdb246ddd';old=next(t for t in h['tracks'] if t['uuid']==uid);assert old['w']==.8 and old['layer']=='B.Cu';win=box(57,105,68,115)
 rec={l:[] for l in LAYERS};holes=[];smd=[]
 for q in h['pads']:
  for l,rs in q['layers'].items():
   if l not in rec:continue
   for sh in C.poly(rs):
    if sh.intersects(win.buffer(.7)):rec[l].append({'kind':'pad','uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'net':q['net'],'shape':sh})
    if q['smd'] and l in ('F.Cu','B.Cu') and sh.intersects(win.buffer(.7)):smd.append(sh)
  for sh in C.poly(q.get('hole') or []):
   if sh.intersects(win.buffer(.7)):holes.append(sh)
 for t in h['tracks']:
  if t['uuid']==uid or t['layer'] not in rec:continue
  if max(t['a'][0],t['b'][0])+t['w']/2<56.3 or min(t['a'][0],t['b'][0])-t['w']/2>68.7 or max(t['a'][1],t['b'][1])+t['w']/2<104.3 or min(t['a'][1],t['b'][1])-t['w']/2>115.7:continue
  rec[t['layer']].append({'kind':'track',**t,'shape':C.body(t)})
 for v in h['vias']:
  if not (56.3<v['x']<68.7 and 104.3<v['y']<115.7):continue
  holes.append(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64))
  for l in v['flashed']:rec[l].append({'kind':'via',**v,'shape':Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=64)})
 def gap(a,b):return .175 if h['domains_normalized'].get(C.norm(a))==h['domains_normalized'].get(C.norm(b)) else .625
 def legal(net,extra):
  walls=[P.bounded_buffer(q['shape'],gap(net,q['net'])) for q in rec['B.Cu'] if q['net']!=net]
  walls += [P.bounded_buffer(z['shape'],max(gap(net,z['net']),float(z.get('clearance_mm',.15))+.025)) for z in zones if z['layer']=='B.Cu' and z['net']!=net and z['shape'].intersects(win.buffer(.627))]
  walls += [P.bounded_buffer(s,.275) for s in holes]
  walls += [P.bounded_buffer(q['shape'],gap(net,q['net'])) for q in extra if q['net']!=net]
  for area in h['rule_areas']:
   if area.get('no_tracks') and 'B.Cu' in area['layers']:walls.extend(P.bounded_buffer(sh,.025) for sh in C.poly(area['outline']) if sh.intersects(win.buffer(.025)))
  return set_precision(win.difference(unary_union(walls)),1e-6)
 pads={q['num']:q for q in h['pads'] if q['ref']=='U19008'};targetnet=pads['10']['net'];groundnet=pads['11']['net'];newvias=[];failures=[]
 def ordinary_site(net,xy):
  point=Point(xy);disk=P.bounded_buffer(point,.25)
  if any(point.distance(sh)-.1<.275+.000002 for sh in smd+holes):return False
  for l in LAYERS:
   if any(q['net']!=net and disk.distance(q['shape'])<gap(net,q['net'])+.000002 for q in rec[l]):return False
   for z in zones:
    if z['layer']!=l or z['net']==net:continue
    if C.norm(z['net']) in ('/motherboard_do/FIELD_B_0V','/motherboard_motors/FIELD_GND') and h['domains_normalized'].get(C.norm(z['net']))==h['domains_normalized'].get(C.norm(net)):continue
    if disk.distance(z['shape'])<gap(net,z['net'])+.000002:return False
  for area in h['rule_areas']:
   if area.get('no_vias') and any(disk.intersects(P.bounded_buffer(sh,.025)) for sh in C.poly(area['outline'])):return False
  return True
 def options(net,pin):
  pad=unary_union(C.poly(pads[pin]['layers']['B.Cu']));out=[]
  for ix in range(626,670):
   for iy in range(1085,1140):
    xy=[round(ix/10,6),round(iy/10,6)]
    if ordinary_site(net,xy):out.append((Point(xy).distance(pad),xy))
  return sorted(out,key=lambda q:q[0])
 a=options(targetnet,'10');b=options(groundnet,'11');print('R74 legal sites',len(a),len(b),flush=True);chosen=None
 for _,aa in a:
  for _,bb in b:
   if math.dist(aa,bb)<.675+.000002:continue
   chosen=(aa,bb);break
  if chosen:break
 if not chosen:
  write(OUT/'receipt.json',{'verdict':'NO_ALL6_PAIRED_ORDINARY_SITES','regulator_legal_sites':len(a),'ground_legal_sites':len(b),'R70_model_sha256':sha(mp),'native_jobs':0,'board_written':False});return
 sites=[{'net':targetnet,'xy':chosen[0]},{'net':groundnet,'xy':chosen[1]}]

 for i,s in enumerate(sites):
  xy=s['xy'];point=Point(xy);disk=P.bounded_buffer(point,.25);net=s['net'];v={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u19008-r74/via/{i}')),'net':net,'x':xy[0],'y':xy[1],'d':.5,'drill':.2,'flashed':LAYERS,'prospective_not_native':True};newvias.append(v)
  if any(point.distance(sh)-.1<.275+.000002 for sh in smd):failures.append({'kind':'SMD_hole_gap','site':s})
  if any(point.distance(sh)-.1<.275+.000002 for sh in holes):failures.append({'kind':'existing_hole_gap','site':s})
  for l in LAYERS:
   for q in rec[l]:
    if q['net']!=net and disk.distance(q['shape'])<gap(net,q['net']):failures.append({'kind':'all_layer_discrete_Cu','site':s,'layer':l,'foreign_kind':q['kind'],'foreign_uuid':q['uuid'],'foreign_raw_net':q['net'],'gap_mm':disk.distance(q['shape'])})
   for z in zones:
    if z['layer']!=l or z['net']==net:continue
    # New same-domain ground planes may be ledgered and carved by final owner.
    if C.norm(z['net']) in ('/motherboard_do/FIELD_B_0V','/motherboard_motors/FIELD_GND') and h['domains_normalized'].get(C.norm(z['net']))==h['domains_normalized'].get(C.norm(net)):continue
    if disk.distance(z['shape'])<gap(net,z['net']):failures.append({'kind':'foreign_power_plane','site':s,'layer':l,'foreign_uuid':z['uuid'],'foreign_raw_net':z['net']})
 for a,b in zip(newvias,newvias[1:]):
  if math.hypot(a['x']-b['x'],a['y']-b['y'])-(a['drill']+b['drill'])/2<.275:failures.append({'kind':'new_new_drill'})
 extra=[{'net':v['net'],'shape':P.bounded_disk(v,v['d']/2)} for v in newvias]
 outside=[{k:q[k] for k in ('kind','uuid','net') if k in q} | {'ref':q.get('ref'),'pin':q.get('pin'),'original_contact_overlap_mm2':q['shape'].intersection(C.body(old)).area} for q in rec['B.Cu'] if q['net']==old['net'] and q['shape'].intersects(C.body(old))]
 answers=[];tracks=[]
 free=legal(old['net'],extra)
 for part in polys(free.buffer(-.4-.002)):
  if not part.covers(Point(old['a'])) or not part.covers(Point(old['b'])):continue
  try:points,search=T.route(part,tuple(old['a']),tuple(old['b']))
  except(AssertionError,ValueError):continue
  points=[[round(x,6),round(y,6)] for x,y in points];body=P.bounded_buffer(LineString(points),.4)
  if not free.covers(body):continue
  missing=[r for r in outside if not any(q['uuid']==r['uuid'] and q['shape'].intersection(body).area>=.001 for q in rec['B.Cu'])]
  if missing:failures.append({'kind':'retained_outside_contact_not_restored','contacts':missing});continue
  answers.append({'kind':'protected_power_wall_detour','width_mm':.8,'points_mm':points,'length_mm':LineString(points).length,'outside_contacts_preserved':outside,'search':search})
  extra.append({'net':old['net'],'shape':body})
  for i,(a,b) in enumerate(zip(points,points[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u19008-r74/power/{i}')),'net':old['net'],'layer':'B.Cu','a':a,'b':b,'w':.8,'prospective_not_native':True})
  break
 for pin,v in [('10',newvias[0]),('11',newvias[1])]:
  pad=unary_union(C.poly(pads[pin]['layers']['B.Cu']));free=legal(v['net'],extra);answer=None
  for part in polys(free.buffer(-.1-.002)):
   start=part.buffer(-.00002).intersection(pad)
   if start.is_empty or not part.covers(Point(v['x'],v['y'])):continue
   try:points,search=T.route(part,tuple(start.representative_point().coords[0]),(v['x'],v['y']))
   except(AssertionError,ValueError):continue
   points=[[round(x,6),round(y,6)] for x,y in points];body=P.bounded_buffer(LineString(points),.1)
   if not free.covers(body) or body.intersection(pad).area<.001:continue
   answer={'kind':'paired_supply_or_return_stub','pin':pin,'native_pad_uuid':pads[pin]['uuid'],'raw_net':v['net'],'via_uuid':v['uuid'],'width_mm':.2,'points_mm':points,'length_mm':LineString(points).length,'search':search};extra.append({'net':v['net'],'shape':body})
   for i,(a,b) in enumerate(zip(points,points[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,f'controller-u19008-r74/stub/{pin}/{i}')),'net':v['net'],'layer':'B.Cu','a':a,'b':b,'w':.2,'prospective_not_native':True})
   break
  if answer:answers.append(answer)
  else:failures.append({'kind':'no_paired_stub','pin':pin})
 if not any(a['kind']=='protected_power_wall_detour' for a in answers):failures.append({'kind':'no_protected_power_detour'})
 (OUT/'proposed-discrete.pkl').write_bytes(pickle.dumps({'vias':newvias,'tracks':tracks},protocol=5));write(OUT/'outside-contact-ledger.json',outside)
 write(OUT/'receipt.json',{'verdict':'NOMINATION_GEOMETRY_COMPLETE_ALL_SOURCE_CURRENT_NATIVE_GATES_OPEN' if not failures else 'COUPLED_WALL_NOMINATION_INCOMPLETE','R70_model_sha256':sha(mp),'owned_old_power_track':old,'answers':answers,'failures':failures,'proposed_discrete_sha256':sha(OUT/'proposed-discrete.pkl'),'outside_contact_ledger_sha256':sha(OUT/'outside-contact-ledger.json'),'original_items_modified':0,'board_written':False,'native_jobs':0,'source_new_ground_carves_reference_full_drill_reserved_areas_current_fault_native_gates':'MANDATORY_OPEN'})
 print('R74',len(answers),'answers',len(failures),'failures',sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
