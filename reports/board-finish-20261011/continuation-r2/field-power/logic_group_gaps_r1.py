"""Exact same-layer distances for retained LOGIC_GND split repair."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
pr=psutil.Process();pr.cpu_affinity(list(range(16,28)));pr.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.ops import unary_union,nearest_points
from inventory import sha
HERE=Path(__file__).resolve().parent;OUT=HERE/'logic-group-gaps-r1'
def main():
    assert not OUT.exists();OUT.mkdir();base=HERE/'coupled-logic-base-r1';r=json.loads((base/'receipt.json').read_text());assert sha(base/'groups.pkl')==r['groups_sha256'];groups=pickle.loads((base/'groups.pkl').read_bytes())['new_groups'];parts=r['lost_retained_relationships'][0]['new_partitions'];main=max(map(int,parts),key=lambda i:len(parts[str(i)]));unions={layer:unary_union([q['shape'] for q in groups[main] if q['layer']==layer]) for layer in ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']};rows=[]
    for k,pads in sorted(parts.items(),key=lambda kv:(kv[0]!='69',-len(kv[1]))):
        i=int(k)
        if i==main:continue
        rr=[]
        for layer,goal in unions.items():
            source=unary_union([q['shape'] for q in groups[i] if q['layer']==layer])
            if source.is_empty or goal.is_empty:continue
            a,b=nearest_points(source,goal);rr.append({'layer':layer,'gap_mm':a.distance(b),'from_mm':list(a.coords[0]),'to_mm':list(b.coords[0]),'source_bounds_mm':source.bounds,'goal_bounds_mm':goal.bounds,'source_objects':[{'kind':q['kind'],'uuid':q['uuid'],'ref':q.get('ref'),'pin':q.get('pin')} for q in groups[i] if q['layer']==layer and q['shape'].distance(a)<.000002],'destination_objects':[{'kind':q['kind'],'uuid':q['uuid'],'ref':q.get('ref'),'pin':q.get('pin')} for q in groups[main] if q['layer']==layer and q['shape'].distance(b)<.000002]})
        row={'group':i,'pads':pads,'layer_gaps':sorted(rr,key=lambda q:q['gap_mm'])};rows.append(row);print(i,'pads',len(pads),[(q['layer'],round(q['gap_mm'],3)) for q in row['layer_gaps']],flush=True)
    (OUT/'receipt.json').write_text(json.dumps({'base_receipt_sha256':sha(base/'receipt.json'),'rows':rows,'native_jobs':0,'board_written':False},indent=1)+'\n');print('receipt',sha(OUT/'receipt.json'))
if __name__=='__main__':main()
