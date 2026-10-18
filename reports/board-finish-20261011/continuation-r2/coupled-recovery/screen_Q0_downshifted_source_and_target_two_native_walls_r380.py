"""Exact three ordinary-site nominees for a <=3-leg Q0/FLT coupled route."""
from pathlib import Path
import sys,pickle,json,hashlib,math
H=Path(__file__).resolve().parent;P=H.parent
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely import affinity
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());NET='/motherboard_do/DOA_Q0_READY_N';GND='/motherboard_motors/FIELD_GND';dom=h['domains_normalized'];deleted={next(t['uuid']for t in h['tracks']if t['uuid'].startswith('c76c0c67')),'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d'};oldpads=[p for p in h['pads']if p['ref']=='R10016'];pids={p['uuid']for p in oldpads};newpad=[]
for p in h['pads']:
 for layer,rs in p['layers'].items():
  for sh in K.L.poly(rs):newpad.append((p,layer,affinity.translate(sh,xoff=-.5,yoff=-.5)if p['uuid']in pids else sh))
smd=[(p,l,s)for p,l,s in newpad if p['smd']and l in('F.Cu','B.Cu')];st=STRtree([s for p,l,s in smd]);allholes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],s)for p in h['pads']for s in K.L.poly(p.get('hole')or[])];ht=STRtree([s for u,s in allholes]);rec,trees=K.F.build({**h,'zones':[]});reserve,exempt=K.A.reservations();sites=[('Q0-source',NET,[229.12,157.72]),('Q0-target',NET,[226.668448,163.130309])];rows=[]
for name,net,at in sites:
 point=Point(at);errors=[];checks=[]
 for layer in K.LAYERS:
  for j in trees[layer].query(point.buffer(1.1),predicate='intersects'):
   r=rec[layer][int(j)]
   if r['uuid']in pids or r['uuid']in deleted or K.L.norm(r['net'])==net:continue
   req=.15 if dom.get(K.L.norm(r['net']))==dom.get(net)else .6
   if r['kind']=='track'and not r['source'].get('m'):d=point.distance(LineString([r['source']['a'],r['source']['b']]))-.25-r['source']['w']/2
   elif r['kind']=='via':d=point.distance(Point(r['source']['x'],r['source']['y']))-.25-r['source']['d']/2
   else:d=point.distance(r['shape'])-.25
   row={'kind':'all6_actual_foreign_'+r['kind'],'other_UUID':r['uuid'],'raw_net':r['net'],'layer':layer,'gap_mm':d,'native_required_mm':req,'planner_required_mm':req+.025};checks.append(row)
   if d<req+.025:errors.append(row)
  for p,l,s in newpad:
   if l!=layer or K.L.norm(p['net'])==net:continue
   d=point.distance(s)-.25;req=.15 if dom.get(K.L.norm(p['net']))==dom.get(net)else .6
   if d<req+.025:errors.append({'kind':'all6_new_or_old_pad','other_UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'layer':layer,'gap_mm':d,'required_mm':req+.025})
  for z in q:
   if z['layer']!=layer or K.L.norm(z['net'])==net or K.L.norm(z['net'])==GND:continue
   d=point.distance(z['shape'])-.25;req=max(float(z['clearance_mm']),.15 if dom.get(K.L.norm(z['net']))==dom.get(net)else .6)+.025
   if d<req:errors.append({'kind':'current_power_owned_plane_hard','other_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'gap_mm':d,'required_mm':req})
 sm=smd[int(st.nearest(point))];smgap=point.distance(sm[2])-.1-.005
 if smgap<.275:errors.append({'kind':'ordinary_SMD_drill_aperture','nearest_pad':[sm[0]['ref'],sm[0]['num'],sm[0]['uuid']],'guarded_gap_mm':smgap,'required_mm':.275})
 hh=allholes[int(ht.nearest(point))];hgap=point.distance(hh[1])-.1-.005
 if hgap<.275:errors.append({'kind':'ordinary_every_drill_aperture','nearest_hole_UUID':hh[0],'guarded_gap_mm':hgap,'required_mm':.275})
 pitch=min((point.distance(Point(v['x'],v['y'])),v['uuid'])for v in h['vias'])
 if pitch[0]<.815:errors.append({'kind':'ordinary_pitch','nearest':pitch,'required_mm':.815})
 for oname,onet,oat in sites:
  if oname!=name and math.dist(at,oat)<.815:errors.append({'kind':'mutual_new_pitch','other':oname,'actual_mm':math.dist(at,oat),'required_mm':.815})
  for r in h['rule_areas']:
  if r.get('no_vias')and any(point.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'native_no_vias','uuid':r['uuid']})
 for r in reserve['keepouts']:
  if net not in exempt.get(r['name'],set())and any(point.distance(s)-.25<.025 for s in K.L.poly(r['outline'])):errors.append({'kind':'frozen_rule_disallow_via','name':r['name']})
 rows.append({'site':name,'raw_net':net,'at_mm':at,'via_diameter_drill_mm':[.5,.2],'all6_discrete_checks':checks,'guarded_SMD_drill_gap_mm':smgap,'guarded_every_drill_gap_mm':hgap,'nearest_original_via_pitch':pitch,'errors':errors,'original_ground_reference_planes_require_exact_prospective_antipads_and_source_graph':'OPEN; no generic plane credit'})
out=H/'Q0-FLT-four-coupled-blockers-two-port-preflight-r380';assert not out.exists();out.mkdir();r={'verdict':'CONCRETE_ORDINARY_PORT_PREFLIGHT_ONLY','model_sha256':sha(model),'exact_four_old_GATE_SENSE_owned_withdrawables':sorted(deleted),'all_seven_old_FLT_items_untouched_and_hard':True,'R10016_proposed_translation_mm':[-.5,-.5],'sites':rows,'total_errors':sum(len(r['errors'])for r in rows),'existing_protected_power_shapes_hard':True,'native_jobs':0,'board_written':False,'adopted':False};(out/'receipt.json').write_text(json.dumps(r,indent=1,allow_nan=False)+'\n');print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'rows':[{k:v for k,v in r.items()if k!='all6_discrete_checks'}for r in rows]}),flush=True)

