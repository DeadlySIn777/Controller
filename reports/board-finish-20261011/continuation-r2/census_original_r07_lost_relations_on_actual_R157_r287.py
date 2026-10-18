"""Rebind all original r07 rip-up losses to pinned full native R157 partitions."""
import collections,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;OUT=H/'original-r07-seventeen-lost-joins-actual-native-R157-residual-r287'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
norm=lambda s:s.replace('{slash}','/')
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();beforefile=Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json');r07file=Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json');afterfile=H/'R155-known-reference-native-diagnostic-r157/measure/partitions.json'
 assert sha(beforefile)=='d431c16a5318cfcd438f73a9280d624d72ca233b0bf01aae636f827d21ea2bdf';assert sha(r07file)=='70adaa1e4f7047ae19f8d21b2303628d2ff4df30167858f73a45ad886eb22dda';assert sha(afterfile)=='2eed68ab73a817ba16110cda84e7cd8efc83355e55d582186e563499207efee9';before=json.loads(beforefile.read_bytes());r07=json.loads(r07file.read_bytes());after=json.loads(afterfile.read_bytes());assert before['sha256']=='0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53';assert r07['sha256']=='0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc';assert after['sha256']=='3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38'
 def normalized(data):
  result={}
  for raw,groups in data['nets'].items():assert norm(raw)not in result;result[norm(raw)]=(raw,groups)
  return result
 bn,seven,an=map(normalized,(before,r07,after));all_after_pad_nets={pad:(net,i)for net,(_,groups)in an.items()for i,gr in enumerate(groups)for pad in gr};rows=[];lost_original=0;remaining=0;source_review=[]
 for net,(raw,groups)in bn.items():
  raw7,g7=seven[net];m7={pad:i for i,gr in enumerate(g7)for pad in gr}
  for group in groups:
   oldsevens=collections.defaultdict(list)
   for pad in group:oldsevens[m7[pad]].append(pad)
   if len(oldsevens)<=1:continue
   oldloss=len(oldsevens)-1;lost_original+=oldloss;now=collections.defaultdict(list);missing=[];changed=[]
   for pad in group:
    if pad not in all_after_pad_nets:missing.append(pad);continue
    currentnet,i=all_after_pad_nets[pad]
    if currentnet!=net:changed.append({'pad':pad,'current_normalized_net':currentnet});continue
    now[i].append(pad)
   loss=max(0,len(now)-1)if not missing and not changed else None
   row={'normalized_original_net':net,'raw_R06_net':raw,'raw_R07_net':raw7,'raw_R157_net':an.get(net,(None,[]))[0],'original_R06_connected_pad_relationship':group,'original_R07_split_groups':list(oldsevens.values()),'original_R07_lost_joins':oldloss,'actual_R157_current_groups':list(now.values()),'actual_R157_missing_original_pads':missing,'actual_R157_changed_pad_net_assignments':changed,'actual_R157_remaining_required_joins':loss,'actual_R157_original_relation_recovered':loss==0 and not missing and not changed,'new_source_change_authority_review_required':bool(missing or changed)};rows.append(row)
   if loss is None:source_review.append(row)
   else:remaining+=loss
 assert lost_original==17;put('all-original-r07-lost-relationships-rebound-to-actual-R157.json',rows);put('actual-full-native-R157-unrestored-original-lost-relationships.json',[r for r in rows if not r['actual_R157_original_relation_recovered']]);put('receipt.json',{'status':'ORIGINAL_R07_LOSS_RESIDUAL_ACTUAL_FULL_NATIVE_R157_BOUND','original_R07_lost_joins':lost_original,'actual_R157_remaining_original_required_joins':remaining,'actual_R157_original_relationships_recovered':sum(r['actual_R157_original_relation_recovered']for r in rows),'original_relationship_count':len(rows),'native_pad_net_authority_reviews':len(source_review),'actual_full_R157_API_unconnected':after['api_unconnected_count'],'actual_full_R157_total_missing_pad_island_joins':after['pad_island_joins'],'full_native_partition_input_SHA256':{str(p.resolve()):sha(p)for p in(beforefile,r07file,afterfile)},'lookup_normalization_ONLY_native_raw_tokens_retained':True,'actual_native_connectivity_scope_NOT_all_drilled_geometry_SI_current_DRC':True,'new_DIC_Q0_ROOT_SBC_packets_NOT_automatically_credited_before_actual_refill':True,'all_original_failures_retained':True,'native_jobs':0,'board_emitted':False,'adopted':False});print('R287_COMPLETE',sha(OUT/'receipt.json'),'original17','current_remaining',remaining,'source_reviews',len(source_review),flush=True)
 for r in rows:
  if r['actual_R157_remaining_required_joins']:print('R287_REMAINING',r['normalized_original_net'],r['actual_R157_remaining_required_joins'],flush=True)
if __name__=='__main__':main()
