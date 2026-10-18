"""Read-only inventory of the preserved coupled control routing authority."""
import sys,pickle,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def describe(v):
 if isinstance(v,dict):return {'type':'dict','keys':list(v),'counts':{k:len(v[k]) for k in ('tracks','vias','pads','zones','shapes') if k in v}}
 if isinstance(v,(list,tuple)):return {'type':type(v).__name__,'len':len(v),'members':[describe(q) for q in v[:8]]}
 return {'type':type(v).__name__}
for name,p in [('R47',HERE.parent/'sbc-power/io3-u15-logic-guarded-model-r47/model.pkl'),('CORE10',HERE.parent/'sbc-power/remaining-core-accepted-checkpoints-r50/stage-10/accepted-checkpoint-model.pkl')]:
 v=pickle.loads(p.read_bytes());print(json.dumps({'name':name,'sha256':sha(p),'description':describe(v)}),flush=True)
graph=json.loads((HERE/'conflict-graph.json').read_text())
for r in graph['lost_route_rows']:
 print(json.dumps({'net':r['net'],'keys':list(r),'blockers':r.get('blocking_nets'), 'missing_count':len(r.get('missing_original_items',[]))}),flush=True)
