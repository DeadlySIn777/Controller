"""Exact U11015 pad-wall inventory; no board mutation or routing work."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import Point
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;OUT=HERE/'u11015-wall-diagnosis-r28'
def main():
 assert not OUT.exists();OUT.mkdir();bp=HERE/'local-and-b5-return-audit-r25';r=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==r['geometry_sha256'];g=pickle.loads((bp/'geometry.pkl').read_bytes());rec,tr=F.build({**g,'zones':[]});pad=next(q for q in rec['B.Cu'] if q['kind']=='pad' and(q['ref'],q['pin'])==('U11015','6'));rows=[]
 for layer in('F.Cu','B.Cu'):
  for ii in tr[layer].query(pad['shape'].buffer(2.),predicate='intersects'):
   q=rec[layer][int(ii)];d=q['shape'].distance(pad['shape']);entry=C.identity(q)|{'gap_to_ground_pad_mm':d,'Cu_bounds_mm':q['shape'].bounds};original=next((t for t in g['tracks'] if t['uuid']==q['uuid']),None)
   if original:entry['track_geometry']=original
   rows.append(entry)
 rows=sorted(rows,key=lambda q:(q['layer'],q['gap_to_ground_pad_mm'],q['uuid']));(OUT/'receipt.json').write_text(json.dumps({'parent_r25_receipt_sha256':sha(bp/'receipt.json'),'target':C.identity(pad),'neighbors':rows,'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
 print(json.dumps([q for q in rows if q['layer']=='B.Cu' and q['gap_to_ground_pad_mm']<.8],indent=1),flush=True)
if __name__=='__main__':main()
