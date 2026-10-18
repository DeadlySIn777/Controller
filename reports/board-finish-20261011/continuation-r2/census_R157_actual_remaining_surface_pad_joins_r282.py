"""Rank real native missing pad joins; no routes or electrical role assumptions."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import collections,hashlib,json,math,time
from pathlib import Path
H=Path(__file__).resolve().parent;M=H/'R155-known-reference-native-diagnostic-r157/measure';OUT=H/'R157-actual-native-remaining-pad-joins-same-surface-census-r282'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();started=time.monotonic();pf=M/'partitions.json';gf=M/'actual-full-refill-geometry.json';assert sha(pf)=='2eed68ab73a817ba16110cda84e7cd8efc83355e55d582186e563499207efee9';assert sha(gf)=='421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b';part=json.loads(pf.read_bytes());geom=json.loads(gf.read_bytes());assert part['sha256']=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38';seen=collections.Counter();pads={}
 for p in geom['pads']:
  key=p['ref'],str(p['num']);name=p['ref']+'.'+str(p['num'])+'#'+str(seen[key]);seen[key]+=1;assert name not in pads;pads[name]=p
 domains=collections.defaultdict(lambda:{'split_nets':0,'missing_pad_island_joins':0});nets=[];pairs=[]
 for raw,groups in part['nets'].items():
  if len(groups)<=1:continue
  info=geom['nets'][raw];dom=info['domain'];domains[dom]['split_nets']+=1;domains[dom]['missing_pad_island_joins']+=len(groups)-1
  for group in groups:
   for name in group:assert name in pads and pads[name]['net']==raw,(raw,name)
  nearest=None;all_near=[]
  for i,left in enumerate(groups):
   for j in range(i+1,len(groups)):
    best=None
    for a in left:
     pa=pads[a];la=set(pa['layers'])&{'F.Cu','B.Cu'}
     if not la:continue
     for b in groups[j]:
      pb=pads[b];common=la&set(pb['layers'])
      if not common:continue
      distance=math.dist(pa['at'],pb['at'])
      if best is None or distance<best['centre_span_mm']:
       best={'raw_net':raw,'normalized_net':info['norm'],'native_netclass':info['netclass'],'native_domain':dom,'left_group':i,'right_group':j,'native_left_pad':a,'native_right_pad':b,'left_actual_at_mm':pa['at'],'right_actual_at_mm':pb['at'],'common_native_surfaces':sorted(common),'centre_span_mm':distance,'left_actual_kind':pa['attr'],'right_actual_kind':pb['attr'],'not_a_clearance_or_body_or_current_qualification':True}
    if best:
     if nearest is None or best['centre_span_mm']<nearest['centre_span_mm']:nearest=best
     if best['centre_span_mm']<=5:all_near.append(best)
  all_near.sort(key=lambda r:r['centre_span_mm']);pairs.extend(all_near[:12]);nets.append({'raw_net':raw,'normalized_net':info['norm'],'native_domain':dom,'native_netclass':info['netclass'],'native_pad_island_groups':len(groups),'joins_missing':len(groups)-1,'total_named_pads':sum(len(gr)for gr in groups),'nearest_common_surface_pad_pair':nearest,'short_common_surface_group_pairs_le5mm':len(all_near)})
  if len(nets)%100==0:print('R282_CENSUS',len(nets),'split_nets',len(pairs),'bounded_short_pairs',flush=True)
 pairs.sort(key=lambda r:r['centre_span_mm']);nets.sort(key=lambda r:(-r['joins_missing'],r['raw_net']));put('all-745-native-split-net-census.json',nets);put('actual-short-common-surface-pad-group-pairs-not-routes.json',pairs);put('native-domain-missing-join-counts.json',dict(domains));assert len(nets)==745 and sum(r['joins_missing']for r in nets)==1177
 put('receipt.json',{'status':'ACTUAL_FULL_NATIVE_REMAINING_PAD_JOIN_CENSUS_BOUND_NOT_ROUTING_QUALIFICATION','native_partition_SHA256':sha(pf),'actual_full_native_geometry_SHA256':sha(gf),'native_board_SHA256':part['sha256'],'API_unconnected_items':part['api_unconnected_count'],'actual_native_pad_island_joins_missing':part['pad_island_joins'],'split_nets':len(nets),'one_join_nets':sum(r['joins_missing']==1 for r in nets),'native_domain_census':dict(domains),'short_common_surface_pad_pairs_le5mm':len(pairs),'actual_native_pad_names_resolved_exact':True,'centre_spans_are_candidate_ordering_ONLY':True,'all_newbody_foreign_Cu_ground_source_reference_holes_courtyards_current_rules':'OPEN_BEFORE_ANY_ROUTE','power_ground_supply_roles_not_inferred_from_names':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R282_COMPLETE',sha(OUT/'receipt.json'),'split_nets',len(nets),'joins1177','short_pairs',len(pairs),'domain_counts',dict(domains),flush=True)
if __name__=='__main__':main()
