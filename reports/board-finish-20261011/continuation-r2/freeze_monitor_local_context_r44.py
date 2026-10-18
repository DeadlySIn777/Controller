"""Read-only exact monitor-ground inventory on all copper layers."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely.geometry import box,Point
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power'):sys.path.insert(0,str(H/d))
import contact_layout as C
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl'
assert sha(mp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'
g,h,b,z,full=pickle.loads(mp.read_bytes());win=box(342,55,351,64)
out=H/'field-monitor-local-context-r44';assert not out.exists();out.mkdir()
rows={'tracks':[t for t in h['tracks']if C.body(t).intersects(win)],'vias':[v for v in h['vias']if win.covers(Point(v['x'],v['y']))],'pads':[p for p in h['pads']if any(s.intersects(win)for l,r in p['layers'].items()for s in C.poly(r))]}
(out/'inventory.json').write_text(json.dumps(rows,indent=1)+'\n')
rr=next(xs for xs in F.graph(full,'/motherboard_motors/FIELD_GND')if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))
for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):(out/(l+'-actual-J3-source-local.wkb')).write_bytes(unary_union([q['shape']for q in rr if q['layer']==l]).intersection(win).wkb)
qrows=json.loads((H/'field-ground-outer-wall-diagnosis-r31/receipt.json').read_bytes())['rows'];wall=next(q for q in qrows if q['ref']=='R9026')
(out/'wall-attribution.json').write_text(json.dumps(wall,indent=1)+'\n')
(out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_ALL6_NATIVE_BOUND_LOCAL_INVENTORY_AND_ACTUAL_J3_SOURCE','model_sha256':sha(mp),'inventory_sha256':sha(out/'inventory.json'),'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n')
print('R44',len(rows['tracks']),len(rows['vias']),len(rows['pads']))
print('R44_WALL',[(q['kind'],q.get('uuid'),q.get('net_raw'),q.get('start_mm'),q.get('end_mm'))for q in wall['walls']])
