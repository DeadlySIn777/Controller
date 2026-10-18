"""Locate the real R393 IO3 split; diagnostic only, no geometry mutation."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,time
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import contact_layout as L
import audit_aux_exact_raw as A
from inventory import sha
R=H/'FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393'
P=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155'
O=H/'FIELD5-R393-exact-IO3-split-diagnosis-r403'
NET='/IO_3V3';UID='8d0d8533-168b-59d0-b231-cdd89cb7bd4e'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(R/'model.pkl')=='df3e75059ea013087ddd8481e1f5bfe79e7915c2c3b4f34e2eaf1de9864acc13'
 g,h,b,q,c=pickle.loads((R/'model.pkl').read_bytes())
 loss=next(x for x in json.loads((H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395/all-net-drilled-contact-checkpoint.json').read_text())if x['net']==NET)['old_layer_key_partition_losses'][0]
 keys={tuple(k)for k in loss['all_exact_retained_layer_keys']}
 _,groups=K.physical(c,NET,K.hole_context(c));root=K.root(groups,'R18001','2');rootkeys=K.keys(root)
 rows=[];detached=[]
 for i,xs in enumerate(groups):
  retained=keys&K.keys(xs)
  if not retained:continue
  pads=[{'UUID':r['uuid'],'ref':r['ref'],'pin':str(r['pin']),'layer':r['layer'],'bounds':r['shape'].bounds}for r in xs if r['kind']=='pad']
  row={'group':i,'source_rooted':bool(retained&rootkeys),'retained_keys':len(retained),'physical_key_count':len(K.keys(xs)),'pads':pads,'all_retained_keys':[list(k)for k in sorted(retained)],'layer_bounds':{ly:unary_union([r['shape']for r in xs if r['layer']==ly]).bounds for ly in K.LAYERS if any(r['layer']==ly for r in xs)}}
  rows.append(row)
  if not row['source_rooted']:detached.append((i,xs))
 put(O/'exact-detached-key-membership.json',rows);(O/'actual-IO3-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5))
 pg,ph,pb,pq,pc=pickle.loads((P/'model.pkl').read_bytes());orig={z['uuid']:z for z in pc['zones']};new={z['uuid']:z for z in c['zones']};plane=next(z for z in q if z['uuid']==UID);attribution=[]
 for zid,z in orig.items():
  if L.norm(z['net'])!=NET:continue
  for layer,rr in z['fills'].items():
   if new[zid]['fills'][layer]==rr:continue
   before=unary_union(L.poly(rr));after=unary_union(L.poly(new[zid]['fills'][layer]));removed=before.difference(after);f=O/(zid+'-'+layer+'-actual-removed.wkb');f.write_bytes(removed.wkb)
   for idx,xs in detached:
    target=unary_union([r['shape']for r in xs if r['layer']==layer]);source=unary_union([r['shape']for r in root if r['layer']==layer])
    if target.is_empty or source.is_empty:continue
    a,bb=nearest_points(target,source);attribution.append({'old_native_fill_UUID':zid,'layer':layer,'removed_mm2':removed.area,'removed_file':str(f.resolve()),'removed_sha256':sha(f),'detached_group':idx,'nearest_gap_mm':a.distance(bb),'nearest_target':list(a.coords[0]),'nearest_source':list(bb.coords[0]),'target_distance_to_removed_mm':target.distance(removed),'source_distance_to_removed_mm':source.distance(removed),'removed_intersects_NEW_FIELD5_guard_region':removed.distance(plane['zone_outline_shape'])<.626})
 put(O/'actual-fill-removal-split-attribution.json',attribution)
 rec={'verdict':'EXACT_REAL_IO3_SPLIT_DIAGNOSIS_NO_CHANGES','R393_model_sha256':sha(R/'model.pkl'),'parent_R155_model_sha256':sha(P/'model.pkl'),'IO3_prior_group_keys':len(keys),'rooted_retained_keys':len(keys&rootkeys),'detached_retained_keys':len(keys-rootkeys),'membership_file_sha256':sha(O/'exact-detached-key-membership.json'),'groups_file_sha256':sha(O/'actual-IO3-groups.pkl'),'attribution':attribution,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'rooted':rec['rooted_retained_keys'],'detached':rec['detached_retained_keys'],'elapsed':rec['elapsed_seconds']}),flush=True)
if __name__=='__main__':main()
