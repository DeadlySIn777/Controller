"""Read-only native integer-coordinate differences; no tolerance or mutation."""
import hashlib,json,sys
from pathlib import Path
import pcbnew
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from native_declared_selected_zone_contract_r2 import canonical,points
S=H/'R155-known-reference-native-diagnostic-r157'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=json.loads((S/'expected-zones.json').read_bytes())
board=S/'copy/board.kicad_pcb'
assert sha(board)==spec['candidate_sha256']
b=pcbnew.LoadBoard(str(board));zs={str(z.m_Uuid.AsString()):z for z in b.Zones()}
rows=[]
for uid in ('0929ae75-1efc-5015-af08-223abac05c5e','61cb8179-7754-5031-bbea-0da464bf816f'):
 e=next(x for x in spec['zones'] if x['uuid']==uid);p=zs[uid].Outline()
 native=[points(p.COutline(0))]+[points(p.Hole(0,j)) for j in range(p.HoleCount(0))]
 er=[canonical(r) for r in e['rings_IU']];nr=[canonical(r) for r in native]
 diffs=[]
 for i,(a,c) in enumerate(zip(er,nr)):
  missing=set(a)-set(c);extra=set(c)-set(a)
  diffs.append({'ring':i,'expected_count':len(a),'native_count':len(c),'expected_only_count':len(missing),'native_only_count':len(extra),'expected_only':sorted(missing)[:30],'native_only':sorted(extra)[:30],'ordered_differences':[{'index':j,'expected':x,'native':y}for j,(x,y)in enumerate(zip(a,c))if x!=y][:30],'expected_duplicate_count':len(a)-len(set(a)),'native_duplicate_count':len(c)-len(set(c))})
 rows.append({'uuid':uid,'rings':diffs,'raw_native_rings_IU':native,'raw_expected_rings_IU':e['rings_IU']})
out=H/'R157-zone-coordinate-diagnosis-r158.json';assert not out.exists()
out.write_text(json.dumps({'candidate_sha256':sha(board),'native_version':pcbnew.Version(),'rows':rows,'no_save_or_refill':True,'adopted':False},indent=1)+'\n')
print(json.dumps({'candidate_sha256':sha(board),'rows':[{'uuid':r['uuid'],'rings':r['rings']}for r in rows],'receipt_sha256':sha(out)}),flush=True)
