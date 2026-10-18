"""Bind CM ground necessity to the full R157 actual cached source groups."""
import sys,json,time
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K
OUT=P/'CORE5-retained-trunk-CM79-full-R157-actual-source-necessity-r416'
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before();saved,missing=N.bound_R663_before_groups({'/LOGIC_GND'});assert not missing
 groups=saved['/LOGIC_GND'];root=K.root(groups,'J11001','2');rootIndex=next(i for i,g in enumerate(groups)if g is root)
 rows=[]
 for i,g in enumerate(groups):
  for r in g:
   if r['kind']=='pad'and r['ref']=='J15002':
    rows.append({'ref':r['ref'],'pin':str(r['pin']),'UUID':r['uuid'],'layer':r['layer'],'group_index':i,'actual_J11001_2_SOURCE':i==rootIndex,'actual_Cu_area_mm2':r['shape'].area})
 rows.sort(key=lambda r:(int(r['pin']),r['layer']));pins={p:sorted({r['group_index']for r in rows if r['pin']==p})for p in sorted({r['pin']for r in rows},key=int)}
 receipt={'status':'FULL_ACTUAL_R157_CM_GROUND_SOURCE_NECESSITY_CACHE_AUDIT','actual_R157_geometry_SHA256':N.sha(N.R157/'actual-full-refill-geometry.json'),'R663_receipt_SHA256':N.sha(N.R663/'receipt.json'),'R663_source_groups_SHA256':N.sha(N.R663/'actual-R157-native-three-ground-all-drilled-groups.pkl'),'LG_group_count':len(groups),'J1_SOURCE_group_index':rootIndex,'J1_SOURCE_layer_key_count':len(K.keys(root)),'J15002_ground_pin_group_indices':pins,'pin79_actual_SOURCE':any(r['pin']=='79'and r['actual_J11001_2_SOURCE']for r in rows),'pin73_actual_SOURCE':any(r['pin']=='73'and r['actual_J11001_2_SOURCE']for r in rows),'no_historical_R371_equivalence_or_route_restart':True,'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started}
 for n,v in [('all-actual-J15002-ground-pad-layer-source-groups.json',rows),('receipt.json',receipt)]:(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
 print('R416_COMPLETE',N.sha(OUT/'receipt.json'),receipt['pin79_actual_SOURCE'],receipt['pin73_actual_SOURCE'],flush=True)
if __name__=='__main__':main()
