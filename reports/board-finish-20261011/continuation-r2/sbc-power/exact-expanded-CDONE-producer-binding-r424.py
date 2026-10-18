"""Bind the original barrel's graph to the fresh open-collector producer."""
import sys,json,pickle,re,time
from pathlib import Path
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;sha=N.sha
OUT=P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424'
def balanced(s,a):
 level=0;quoted=False;escaped=False
 for i in range(a,len(s)):
  c=s[i]
  if quoted:
   if escaped:escaped=False
   elif c=='\\':escaped=True
   elif c=='"':quoted=False
  elif c=='"':quoted=True
  elif c=='(':level+=1
  elif c==')':
   level-=1
   if level==0:return s[a:i+1]
 raise AssertionError('unbalanced selected source expression')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();scope=P/'CM79-actual-CDONE-original-barrel-source-and-incident-scope-r422';r=json.loads((scope/'receipt.json').read_bytes());pf=scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl';assert sha(pf)==r['scope_packet_SHA256'];v=pickle.loads(pf.read_bytes());src=H/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net';assert sha(src)=='070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2';s=src.read_text(encoding='utf-8');name=s.index('(name "/fpga_core{slash}FPGA_CDONE")');block=balanced(s,s.rfind('(net',0,name));nodes=[]
 for m in re.finditer(r'\(node\b',block):
  n=balanced(block,m.start());row={key:re.search(r'\('+key+r' "([^"]*)"\)',n).group(1)for key in ('ref','pin','pintype')};row['pinfunction']=re.search(r'\(pinfunction "([^"]*)"\)',n).group(1)if '(pinfunction 'in n else None;nodes.append(row)
 producer=next(n for n in nodes if(n['ref'],n['pin'],n['pintype'])==('U1001','R1','open_collector'));groups=v['all_actual_before_groups'];root=K.root(groups,'U1001','R1');barrel=next(g for g in groups if any(q['kind']=='via'and q['uuid']==v['original_barrel']['uuid']for q in g));ri=next(i for i,g in enumerate(groups)if g is root);bi=next(i for i,g in enumerate(groups)if g is barrel);(OUT/'exact-fresh-CDONE-net-source-expression').write_text(block+'\n',encoding='utf-8');receipt={'status':'FRESH_OPEN_COLLECTOR_PRODUCER_ACTUAL_NATIVE_ROOT_BOUND','fresh_netlist_SHA256':sha(src),'net':'/fpga_core/FPGA_CDONE','producer':producer,'all_source_nodes':nodes,'actual_R157_geometry_SHA256':N.sha(N.R157/'actual-full-refill-geometry.json'),'actual_CDONE_group_count':len(groups),'actual_U1001_R1_source_group_index':ri,'actual_U1001_R1_source_layer_keys':len(K.keys(root)),'original_barrel_group_index':bi,'original_barrel_group_layer_keys':len(K.keys(barrel)),'original_barrel_group_is_producer_SOURCE':ri==bi,'source_repair_recovery14_contingency_REQUIRED':ri!=bi,'every_original_source_key_and_old_group_to_preserve':True,'R422_scope_packet_SHA256':sha(pf),'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1,allow_nan=False)+'\n',encoding='utf-8');print('R424_COMPLETE',sha(OUT/'receipt.json'),ri==bi,len(K.keys(root)),flush=True)
if __name__=='__main__':main()
