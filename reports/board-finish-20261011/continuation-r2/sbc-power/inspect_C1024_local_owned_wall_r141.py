"""Saved exact local copper/footprint context for a constructive cap escape."""
from pathlib import Path
import pickle,json,hashlib,sys
from shapely.geometry import LineString,box,Point
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import contact_layout as C
mp=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl';old,h,b,z,current=pickle.loads(mp.read_bytes());win=box(152,76,166,86)
pads=[q for q in h['pads'] if abs(q['x']-159)<7 and abs(q['y']-81)<5]
tracks=[q for q in h['tracks'] if q['layer']=='F.Cu' and LineString([q['a'],q['b']]).intersects(win)]
vias=[q for q in h['vias'] if win.covers(Point(q['x'],q['y']))]
fp=[q for q in h.get('footprints',[]) if q.get('ref')=='C1024']
result={'parent_model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'window_mm':list(win.bounds),'pads':pads,'tracks_F':tracks,'vias_all_layers':vias,'footprint_metadata':fp,'candidate_C1024':next(q for q in pads if (q['ref'],q['num'])==('C1024','1')),'rules':[q for q in h['rule_areas'] if any(win.intersects(s) for s in C.poly(q['outline']))]}
f=H/'sbc-power/C1024-local-native-bound-context-r141.json';assert not f.exists();f.write_text(json.dumps(result,indent=1)+'\n');print('C1024_EXACT_LOCAL_CONTEXT',len(pads),len(tracks),len(vias),hashlib.sha256(f.read_bytes()).hexdigest());print(json.dumps({'C1024pads':[{k:q[k] for k in ('uuid','ref','num','net','x','y')} for q in pads if q['ref']=='C1024'],'named_GND_walls':[q for q in tracks if q['uuid'].startswith(('090b18c2','575cc','74dc41c5'))],'1V2_vias':[{k:v[k] for k in ('uuid','x','y','d','drill','flashed')} for v in vias if v['net']=='/CORE_1V2']},indent=1))
