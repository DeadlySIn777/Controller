"""Inventory exact discrete deltas before independent full preservation checks."""
import hashlib,json,pickle
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bp=H/'logic-two-reference-safe-return-restoration-r42/model.pkl';cp=H/'sbc-power/IO3-notch-ROOT42-SAFE-unprojected-r165/unprojected-model.pkl'
assert sha(bp)=='a4baedbfbccc92930a22c946b1e4e5262287d59b60b2a1e529bfddfa75c398ba'and sha(cp)=='b469400ca259d0085d1d0564a14f0ccab90f28c3e4a3389081110173ad4845cb'
g,h,b,z,current=pickle.loads(bp.read_bytes());ng,nh,nb,nz,ncurrent=pickle.loads(cp.read_bytes());rows={}
for k in ('tracks','vias','pads','footprints','zones'):
 identity='ref' if k=='footprints' else 'uuid';a={q[identity]:q for q in h[k]};n={q[identity]:q for q in nh[k]}
 rows[k]={'removed':[{key:q.get(key)for key in ('uuid','ref','num','net','layer')}for uid,q in a.items()if uid not in n],'added':[{key:q.get(key)for key in ('uuid','ref','num','net','layer')}for uid,q in n.items()if uid not in a],'changed':[]}
 for uid,q in a.items():
  if uid in n and q!=n[uid]:rows[k]['changed'].append({'uuid':uid,'ref':q.get('ref'),'num':q.get('num'),'changed_fields':[key for key in q.keys()|n[uid].keys()if q.get(key)!=n[uid].get(key)]})
out=H/'safe-root42-discrete-inventory-r49.json';assert not out.exists();out.write_text(json.dumps({'root42_model_sha256':sha(bp),'safe_unprojected_model_sha256':sha(cp),'rows':rows,'native_jobs':0,'adopted':False,'board_written':False},indent=1)+'\n');print(json.dumps({k:{f:len(xs)for f,xs in v.items()}for k,v in rows.items()}))
