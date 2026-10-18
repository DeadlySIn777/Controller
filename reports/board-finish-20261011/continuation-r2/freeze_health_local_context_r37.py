"""Read only the actual saved native-bound field-health local inventory."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H/'field-power'));sys.path.insert(0,str(H/'sbc-power'))
import contact_layout as C
import fast_contacts as F
from shapely.geometry import box
from shapely.ops import unary_union
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
mp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';g,h,b,z,full=pickle.loads(mp.read_bytes());win=box(308,151,316,158);out=H/'field-health-local-context-r37';assert not out.exists();out.mkdir();rows={'tracks':[t for t in h['tracks']if t['layer']=='F.Cu'and C.body(t).intersects(win)],'vias':[v for v in h['vias']if win.covers(C.Point(v['x'],v['y']))],'pads':[dict(p,layers={l:r for l,r in p['layers'].items()if l=='F.Cu'})for p in h['pads']if any(s.intersects(win)for s in C.poly(p['layers'].get('F.Cu',[])))]};(out/'inventory.json').write_text(json.dumps(rows,indent=1)+'\n');rr=next(xs for xs in F.graph(full,'/motherboard_motors/FIELD_GND')if any(q['kind']=='pad'and(q['ref'],q['pin'])==('J11003','2')for q in xs))
for l in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu'):(out/(l+'-actual-J3-source-local.wkb')).write_bytes(unary_union([q['shape']for q in rr if q['layer']==l]).intersection(win).wkb)
(out/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_NATIVE_BOUND_LOCAL_INVENTORY_AND_ACTUAL_J3_SOURCE','model_sha256':sha(mp),'inventory_sha256':sha(out/'inventory.json'),'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n');print('R37_NEAR_WALL',[(t['uuid'],t['net'],t['a'],t['b'])for t in rows['tracks']if t['uuid']in ['e4373f43-4bf8-4252-afdf-b11a56a2c998','7215d6b8-7cd0-477d-97f4-090c49c0e08a']],flush=True)
