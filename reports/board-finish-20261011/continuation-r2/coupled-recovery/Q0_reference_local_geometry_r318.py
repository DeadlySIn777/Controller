"""Exact foreign bodies/holes at saved R10016 terminal, no change or native job."""
from pathlib import Path
import sys,pickle,json,hashlib
H=Path(__file__).resolve().parent;P=H.parent
for p in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(p))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point
from shapely.ops import unary_union
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
model=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(model)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,current=pickle.loads(model.read_bytes());pad=next(p for p in current['pads']if(p['ref'],str(p['num']))==('R10016','1'));shape=unary_union(K.L.poly(pad['layers']['F.Cu']));ground='/motherboard_motors/FIELD_GND';records,trees=K.F.build(current,layers={'In1.Cu'});rows=[]
for j in trees['In1.Cu'].query(shape.buffer(1),predicate='intersects'):
 r=records['In1.Cu'][int(j)]
 if K.L.norm(r['net'])==ground:continue
 d=shape.distance(r['shape']);intersection=shape.intersection(r['shape']);rows.append({'kind':r['kind'],'uuid':r['uuid'],'raw_net':r['net'],'distance_to_R10016_F_projected_body_mm':d,'projected_overlap_mm2':intersection.area,'source_record':r.get('source'),'ref':r.get('ref'),'pin':r.get('pin'),'shape_bounds_mm':r['shape'].bounds})
rows.sort(key=lambda r:r['distance_to_R10016_F_projected_body_mm']);holes=[]
for v in current['vias']:
 d=shape.distance(Point(v['x'],v['y']))-v['drill']/2
 if d<1:holes.append({'uuid':v['uuid'],'raw_net':v['net'],'at_mm':[v['x'],v['y']],'diameter_drill_mm':[v['d'],v['drill']],'nearest_projected_pad_to_drill_edge_mm':d,'actual_or_prospective_flashes':v.get('flashed')})
holes.sort(key=lambda r:r['nearest_projected_pad_to_drill_edge_mm']);rules=[]
for r in current['rule_areas']:
 if 'In1.Cu'in r['layers']and r.get('no_zones'):
  for sh in K.L.poly(r['outline']):
   if sh.distance(shape)<1:rules.append({'uuid':r['uuid'],'no_zones':True,'distance_mm':sh.distance(shape),'overlap_mm2':sh.intersection(shape).area})
out=H/'Q0-R10016-local-reference-geometry-r318';assert not out.exists();out.mkdir();receipt={'verdict':'EXACT_LOCAL_REFERENCE_FOREIGN_GEOMETRY_NO_ACCEPTANCE','model_sha256':sha(model),'pad':{k:v for k,v in pad.items()if k not in('layers','poly','hole')},'pad_bounds_mm':shape.bounds,'foreign_In1_Cu':rows,'every_near_drilled_via':holes,'actual_native_no_zones_areas':rules,'full_current_and_native_checks':'OPEN','native_jobs':0,'board_written':False,'adopted':False};(out/'receipt.json').write_text(json.dumps(receipt,indent=1,allow_nan=False)+'\n');print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'pad_bounds':shape.bounds,'first_foreign':rows[:10],'holes':holes[:10],'rules':rules}),flush=True)
