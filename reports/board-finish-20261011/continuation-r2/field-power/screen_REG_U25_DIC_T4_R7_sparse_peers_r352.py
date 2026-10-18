"""Exact sparse peer nomination screen; no full-model/source credit."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,time
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely import set_precision
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import contact_layout as C
import complete_geometry_r2 as G
from inventory import sha
O=H/'REG-U25-DIC-T4-R7-exact-sparse-mutual-screen-r352'
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 sources=[('REG',H/'REG7-native-support-minimal-current-delta-r312/new-REG-discrete.pkl','5bbbf453c738829774d4b5964ebdf42622e0e0466685bb1ccde83672452cad0f'),('U25',H/'U11025-exact-health-ground-native-owned-recipe-r350/proposed-discrete.pkl','438d1f9b5adc8b8255870a531107d96cbc55faa11bfca1d2500bae8202871fa5'),('DIC_C1022',H.parent/'coupled-recovery/DIC-C1022-exact-R250-current-construction-r256/new-owned-discrete.pkl','bb1e5159bd82b520150b0b40834b6cff7714458ba5a0356f826c9fef28ea36c3'),('T4',H.parent/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256/proposed-discrete.pkl','9b8150b8daa7bff3b51e3381a1654d0629294dcdef41d2919555f63313fb9c8d'),('R7',H.parent/'sbc-power/R7-NW-fullwidth-two-B-trunk-detour-nominations-r259/first-nominee-discrete.pkl','008bbcd1380e45a115bcbe4076eb1cad35f302b3fcda5ef19bbb13238aafd094')]
 _,h,_,_,_=pickle.loads((H.parent/'coupled-recovery/DIC-C1022-exact-R250-current-construction-r256/model.pkl').read_bytes());ds={};files=[]
 for name,path,digest in sources:
  assert sha(path)==digest;(ds.setdefault(name,pickle.loads(path.read_bytes())));files.append({'owner':name,'path':str(path.resolve()),'SHA256':digest})
 qp=H/'REG7-native-support-minimal-current-delta-r312/new-REG7-zones.pkl';assert sha(qp)=='8f79fddbf190943b7c1c40fe80aaadef630fb06775af20e64aaa87130f0c8d84';zones=pickle.loads(qp.read_bytes());checks=[]
 def add(row):
  row['PASS']=row['actual_mm']+1e-10>=row['required_mm'];checks.append(row)
 for our in ('REG','U25'):
  for peer in ('DIC_C1022','T4','R7'):
   for a in ds[our]['tracks']+ds[our]['vias']:
    av='d'in a;ap=Point(a['x'],a['y']) if av else LineString([a['a'],a['b']]);ar=a['d']/2 if av else a['w']/2
    for b in ds[peer]['tracks']+ds[peer]['vias']:
     bv='d'in b;bp=Point(b['x'],b['y']) if bv else LineString([b['a'],b['b']]);br=b['d']/2 if bv else b['w']/2
     if av and bv:
      gap=ap.distance(bp)-(a['drill']+b['drill'])/2
      if gap<1:add({'owner':our,'new_UUID':a['uuid'],'peer_owner':peer,'peer_UUID':b['uuid'],'kind':'dynamic_new_new_drilled_gap_including_same_raw','actual_mm':gap,'required_mm':.275})
     if not av and not bv and a['layer']!=b['layer']:continue
     if C.norm(a['net'])==C.norm(b['net']):continue
     gap=ap.distance(bp)-ar-br;req=G.gap(h,a['net'],b['net'])+.025
     if gap<req+.01:add({'owner':our,'new_UUID':a['uuid'],'peer_owner':peer,'peer_UUID':b['uuid'],'kind':'true_caps_barrel_peer_clearance','actual_mm':gap,'required_mm':req})
   if our=='REG':
    for q in zones:
     for b in ds[peer]['tracks']+ds[peer]['vias']:
      bv='d'in b
      if not bv and q['layer']!=b['layer']:continue
      if C.norm(q['net'])==C.norm(b['net']):continue
      bp=Point(b['x'],b['y']) if bv else LineString([b['a'],b['b']]);br=b['d']/2 if bv else b['w']/2;req=max(G.gap(h,q['net'],b['net']),q.get('clearance_mm',.15))+.025
      for role in ('shape','zone_outline_shape'):
       gap=set_precision(q[role],0).distance(bp)-br
       if gap<req+.01:add({'owner':our,'new_UUID':q['uuid'],'role':role,'peer_owner':peer,'peer_UUID':b['uuid'],'kind':'new_REG_role_to_true_peer_Cu','actual_mm':gap,'required_mm':req})
 errors=[r for r in checks if not r['PASS']];(O/'all-exact-sparse-peer-checks.json').write_text(json.dumps(checks,indent=1)+'\n',encoding='utf-8');receipt={'verdict':'SCOPED_EXACT_SPARSE_PEER_CU_AND_DRILL_PASS_SOURCE_CURRENT_NATIVE_OPEN' if not errors else 'SPARSE_PEER_NOMINATION_REJECTED','source_files':files,'REG7_zone_file':str(qp.resolve()),'REG7_zone_SHA256':sha(qp),'checks':len(checks),'errors':errors,'no_peer_fullmodel_or_copper_source_credit':True,'inherited_CORE_body_reference_gap_mm2':93.04195929171794,'all_full_source_relationship_reference_current_native_gates':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'checks':len(checks),'errors':len(errors)}),flush=True)
if __name__=='__main__':main()
