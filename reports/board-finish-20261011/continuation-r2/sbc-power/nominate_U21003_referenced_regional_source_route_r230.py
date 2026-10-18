"""Preserved R229 ordinary sites; route in exact small reference-safe faces."""
from pathlib import Path
import hashlib
P=Path(__file__).resolve().parent;prior=P/'nominate_U21003_source_escape_at_real_return_r229.py';s=prior.read_text()
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,box')
s=s.replace("import restore_SAFE_generated_precision_states_r168 as PS","import restore_SAFE_generated_precision_states_r168 as PS\nimport tri_route as T")
s=s.replace('U21003-real-return-paired-source-escape-r229','U21003-referenced-regional-source-escape-r230').replace('U21003-R229:','U21003-R230:').replace('R229_','R230_')
marker=' attempts=[];accepted=[]\n'
assert marker in s
free=""" # The start/goal are exact ordinary pads/sites; no search radius is a
 # design requirement. This regional face merely speeds a literal route.
 window=box(329.5,142.5,336.5,149.5);query=window.buffer(2);obs=[]
 for j in trees['F.Cu'].query(query,predicate='intersects'):
  q=rec['F.Cu'][int(j)]
  if C.norm(q['net'])==RAW:continue
  rad=.1+GP.G.gap(h,RAW,q['net'])+.025+.000020
  if q['kind']=='track':tt=q['source'];cut=GP.bounded_buffer(LineString([tt['a'],tt['b']]),rad+tt['w']/2)
  elif q['kind']=='via':vv=q['source'];cut=GP.bounded_disk(vv,rad+vv['d']/2)
  else:cut=GP.bounded_buffer(q['shape'],rad)
  obs.append(cut.intersection(query))
 for hid,sh in holes:
  if sh.distance(query)>.3:continue
  if any(v['uuid']==hid and v['net']==RAW for v in h['vias']):continue
  obs.append(GP.bounded_buffer(sh,.1+.275+.005+.000020).intersection(query))
 for q in z:
  if q['layer']=='F.Cu'and C.norm(q['net'])!=RAW and GP.G.gap(h,RAW,q['net'])>.15 and q['shape'].intersects(query):obs.append(GP.bounded_buffer(q['shape'].intersection(query),.1+max(q['clearance_mm'],GP.G.gap(h,RAW,q['net']))+.025+.000020))
 for q,l,sh in native:
  if l=='F.Cu'and GP.G.gap(h,RAW,q['net'])>.15 and sh.intersects(query):obs.append(GP.bounded_buffer(sh.intersection(query),.1+max(q['clearance_mm'],GP.G.gap(h,RAW,q['net']))+.025+.000020))
 for q in h['rule_areas']:
  if 'F.Cu'in q['layers']and q.get('no_tracks'):
   for sh in C.poly(q['outline']):
    if sh.intersects(query):obs.append(GP.bounded_buffer(sh,.125+.000020))
 centers=oldref.intersection(window).buffer(-.100030,quad_segs=128).difference(unary_union(obs));parts=[centers]if centers.geom_type=='Polygon'else[q for q in getattr(centers,'geoms',[])if q.geom_type=='Polygon']
 (O/'exact-reference-and-old-Cu-free-center-regions.wkb').write_bytes(centers.wkb);print('R230_REFERENCE_SAFE_REGIONAL_FACES',len(parts),'actual_start_eligible',any(q.covers(Point(a))for q in parts),flush=True)
"""
s=s.replace(marker,free+marker)
marker="   for route in routes:\n"
assert marker in s
regional="""   for face in parts:
    if not(face.covers(Point(a))and face.covers(pos)):continue
    try:
     if face.covers(LineString([a,[x,y]])):points=[a,[x,y]]
     else:points,_=T.route(face,tuple(a),(x,y))
     routes.append(tuple([list(xy)for xy in points]))
    except (AssertionError,ValueError):continue
"""
s=s.replace(marker,regional+marker)
assert s!=prior.read_text()
exec(compile(s,str(__file__),'exec'))
