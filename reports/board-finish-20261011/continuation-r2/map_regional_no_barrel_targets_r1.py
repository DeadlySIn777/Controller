"""Identify exact untouched source-ground pads with no existing inner-barrel port."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cp=H/'protected-field-return-restoration-r4/checkpoint.json';cb=cp.read_bytes();rows=json.loads(cb)['rows'];mp=H/'sbc-power/core-pocket-outward-round-guards-r69/model.pkl';assert sha(mp)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff'
_,h,_,_,_=pickle.loads(mp.read_bytes());pads={p['uuid']:p for p in h['pads']};result=[]
for r in rows:
 if r['repair']or r['existing_via_ports']:continue
 for u in r['target_pad_UUIDs']:
  p=pads[u];result.append({'net':r['net'],'physical_pad_uuid':u,'ref':p['ref'],'pin':p['num'],'raw_net':p['net'],'at_mm':[p.get('x'),p.get('y')],'pad_bounds_by_layer':{l:[list(q.bounds)for q in __import__('shapely').geometry.shape({'type':'MultiPolygon','coordinates':[]}).geoms]for l in []},'actual_copper_layers':list(p['layers']),'smd':p['smd'],'native_original_pad_record':p})
out=H/'regional-no-barrel-targets-r1.json';assert not out.exists();out.write_text(json.dumps({'verdict':'EXACT_ORIGINAL_GROUND_PAD_IDENTITIES_NEXT_DOGBONE_NOMINATIONS_REQUIRED','checkpoint_sha256':hashlib.sha256(cb).hexdigest(),'parent_model_sha256':sha(mp),'targets':result,'existing_copper_unchanged':True,'native_jobs':0,'adopted':False},indent=1)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='native_original_pad_record'}for r in result]))
