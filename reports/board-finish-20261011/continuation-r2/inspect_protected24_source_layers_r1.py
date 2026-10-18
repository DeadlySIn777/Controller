import json,pickle,collections
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'protected24-source-census-r2';r=json.loads((p/'receipt.json').read_bytes());g=pickle.loads((p/'groups.pkl').read_bytes());o=[]
for row in r['rows']:
 xs=g[row['normalized_net']][row['source_group']];by=collections.defaultdict(list)
 for q in xs:
  if q['kind']!='fill':by[q['layer']].append(q)
 poses=[{'uuid':q['uuid'],'pin':q['pin'],'layer':q['layer'],'bounds_mm':q['shape'].bounds} for q in xs if q['kind']=='pad' and q['ref']==row['actual_source']['ref']]
 o.append({'bank':row['bank'],'source_pads':poses,'physical_source_layer_counts':{l:len(x) for l,x in by.items()},'source_via_UUIDs':sorted({q['uuid'] for q in xs if q['kind']=='via'}),'source_outer_near_pads':[{'uuid':q['uuid'],'ref':q.get('ref'),'pin':q.get('pin'),'kind':q['kind'],'layer':q['layer'],'bounds_mm':q['shape'].bounds} for q in xs if q['kind']!='fill' and q['layer'] in ('F.Cu','B.Cu') and q['shape'].bounds[0]<210 and q['shape'].bounds[1]<180]})
out=h/'protected24-source-layer-inventory-r1';out.mkdir();(out/'receipt.json').write_text(json.dumps(o,indent=1));print(json.dumps(o,indent=1))
