"""Stronger copper-removal test for a local coupled FIELD_GND_In1 correction.

Remove entire immutable actual fill records instead of fabricating clipped fills.
If retained relationships pass, any strict local negative subset preserves them
with every other current actual conductor fixed. Current qualification is separate.
"""
import os,sys
sys.dont_write_bytecode=True
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,hashlib,time,gc
from pathlib import Path
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[3]
OLD=PROJECT/'reports/board-finish-20261011/continuation-r2';P=PROJECT/'reports/board-finish-20261017/actual-full-audit-repaired-r1/r763'
for d in(OLD,OLD/'field-power',OLD/'sbc-power',OLD/'coupled-recovery'):sys.path.insert(0,str(d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;L=N.L;NET='/motherboard_motors/FIELD_GND';OUT=HERE/'FG-In1-individual-immutable-record-retention-r2'
TARGETS=['ff5ffe1e-111b-5951-957a-dfd8894ca90c']
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,r):(OUT/n).write_text(json.dumps(r,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 st=time.monotonic();assert not OUT.exists();OUT.mkdir();mf=P/'actual-combined-full-after-model.pkl';gf=P/'actual-combined-full-after-all-net-groups.pkl'
 h=pickle.loads(mf.read_bytes());graphs=pickle.loads(gf.read_bytes());prior=graphs[NET];source=K.root(prior,'J11003','2');sourcekeys=K.keys(source);del graphs;gc.collect();ctx=K.hole_context(h);trials=[]
 for removed_index in(0,1):
  targets=TARGETS
  removed=[];zones=[]
  for z in h['zones']:
   if z['uuid']not in targets:zones.append(z);continue
   assert L.norm(z['net'])==NET
   for ly,rs in z['fills'].items():
    removed.extend({'UUID':z['uuid'],'layer':ly,'immutable_record':i,'WKB_SHA256':hashlib.sha256(sh.wkb).hexdigest(),'area_mm2':sh.area,'bounds_mm':list(sh.bounds)}for i,sh in enumerate(L.poly(rs))if i==removed_index)
   zones.append({**z,'fills':{ly:[record for i,record in enumerate(rs)if i!=removed_index]for ly,rs in z['fills'].items()}})
  after={**h,'zones':zones};_,now=K.physical(after,NET,ctx);newsource=K.root(now,'J11003','2');lost=sorted(sourcekeys-K.keys(newsource));allrows,bad=K.contact_losses(prior,now)
  direct=[]
  for ly in K.LAYERS:
   of=[r for g in prior for r in g if r['kind']=='fill'and r['layer']==ly];nf=[r for g in now for r in g if r['kind']=='fill'and r['layer']==ly];ot=STRtree([r['shape']for r in of]);nt=STRtree([r['shape']for r in nf]);metal={}
   for g in prior:
    for r in g:
     if r['kind']!='fill'and r['layer']==ly:metal.setdefault((r['kind'],r['uuid'],ly),[]).append(r['shape'])
   for key,shapes in metal.items():
    body=unary_union(shapes);oldhit=any(body.distance(of[int(i)]['shape'])<=.000002 for i in ot.query(body.buffer(.000002),predicate='intersects'))
    if not oldhit:continue
    newhit=any(body.distance(nf[int(i)]['shape'])<=.000002 for i in nt.query(body.buffer(.000002),predicate='intersects'))
    if not newhit:direct.append({'old_discrete_layer_key':list(key),'current_actual_any_same_net_fill_contact_lost':True})
  verdict=not(lost or bad or direct)
  result={'removed_immutable_fill_record_index':removed_index,'removed_native_zone_actual_fill_record_UUIDs':targets,'strict_copper_subset_by_unchanged_record_inventory':True,'all_other_current_native_actual_discrete_and_fill_records_immutable':True,'all_removed_records':removed,'old_FIELD_GND_In1_group_relationship_losses':bad,'old_FIELD_GND_In1_source_layer_key_losses':[list(k)for k in lost],'old_FIELD_GND_In1_direct_fill_contact_losses':direct,'FIELD_GND_In1_source_before_key_count':len(sourcekeys),'status':'STRONGER_WHOLE_RECORD_REMOVAL_HOST_RETENTION_PASS_LOCAL_NEGATIVE_SUBSET_CONDITIONALLY_MONOTONE'if verdict else'STRONGER_RECORD_REMOVAL_FAIL_LOCAL_CUT_NEEDS_SPECIFIC_PROOF','source_current_minwidth_thermal_barrel_voltage_drop':'SEPARATE_OPEN','native_CPP_after_and_all_reference_old_positive_pour_scopes':'SEPARATE_OPEN'}
  trials.append(result);put('trials-progress.json',trials);print('FIELD_GND_In1_DROP_TEST',len(targets),'source',len(lost),'relationships',len(bad),'direct',len(direct),flush=True)
 put('receipt.json',{'status':'CONSERVATIVE_EXACT_RECORD_INVENTORY_REMOVAL_DIAGNOSTIC_COMPLETE','trials':trials,'no_planned_fill_generated_as_actual_authority':True,'native_jobs':0,'candidate_or_source_changed':False,'all433_native_reference_losses_remain_held':True,'input_SHA256':{str(f):sha(f)for f in(Path(__file__),mf,gf,P/'actual-graph-cache-receipt.json')},'elapsed_seconds':time.monotonic()-st})
if __name__=='__main__':main()
