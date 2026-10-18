"""Read-only exact R25 local wall/contact inventory; no native or board writes."""
import sys,json,pickle,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
FP=HERE.parent/'field-power'
sys.path.insert(0,str(FP))
import contact_layout as C
import fast_contacts as F
from shapely.geometry import box,Point
from shapely.ops import unary_union
R25=FP/'local-and-b5-return-audit-r25'
PINS={'receipt.json':'d5b593c9f678f7b3197057a8b06b4e86ec17fc061d7d69db607c112e4ee3bf42','geometry.pkl':'5f4bdebe6b30db9f184963b719ef8df454af213c471bf9132569248607f2fc6a','proposed-zones.pkl':'9bd2e4414ae4070962c73674040af254204b786ce7cdd1de570ca035d04e8e9d','groups.pkl':'5d61440389b9eeca10a153ecc13bc64f7ad14a3de669bf283bc8b285b384530e','discrete.pkl':'b5d9b9e5f7f8ca8171e9f7f84bdc28dcd5641e04f1c877c8cf8ef988ce6833b1'}
READS={}
def read(p):
 raw=p.read_bytes();READS[str(p.resolve())]=hashlib.sha256(raw).hexdigest();return raw
def clean(q):return {k:v for k,v in q.items() if k not in('shape','source')}
def main():
 out=HERE/'c10036-wall-diagnosis-r1.json';assert not out.exists()
 for name,pin in PINS.items():assert hashlib.sha256(read(R25/name)).hexdigest()==pin,name
 g=pickle.loads(read(R25/'geometry.pkl'));d=pickle.loads(read(R25/'discrete.pkl'))
 ids={'07fb2cff-c122-43b6-be05-2f6838607d30','7efa883d-9d3c-479a-8b49-da8226ea6968','a0e291b0-98d5-4b40-96af-4ea347d3b951','88b68b8b-d34f-4c14-81ac-2e866edd2542','cc9f1042-42d3-46a9-b317-165322c37753'}
 ts=[t for t in g['tracks'] if t['uuid'] in ids];assert len(ts)==5
 net=C.norm(ts[0]['net']);assert all(C.norm(t['net'])==net for t in ts)
 p=next(p for p in g['pads'] if p['ref']=='C10036' and p['num']=='2')
 rec,tr=F.build({**g,'zones':[]});window=box(64,92,76,105)
 own=[]
 for gs in F.graph(g,net):
  if any(q['uuid'] in ids for q in gs):own.append([clean(q) for q in gs if q['kind']!='fill'])
 local=[{**clean(q),'distance_to_pad_mm':q['shape'].distance(unary_union(C.poly(p['layers']['F.Cu'])))} for q in rec['F.Cu'] if q['shape'].intersects(window)]
 row={'verdict':'DIAGNOSIS_ONLY','input_hashes':READS,'ground_pad':p,'wall_tracks':ts,'wall_net':net,'wall_domain':g['domains_normalized'][net],'wall_group_discrete':own,'local_F_discrete':local,'same_source_discrete_tracks':all(t in d['tracks'] for t in ts),'no_native':True}
 out.write_text(json.dumps(row,indent=1)+'\n');print(json.dumps({'output':str(out),'wall_tracks':ts,'pad':{k:p[k] for k in('uuid','ref','num','net','x','y','layers')},'group_discrete_counts':[len(x) for x in own]},indent=1),flush=True)
if __name__=='__main__':main()
