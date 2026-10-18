"""Alternate owned FIELD5 feeder; failed In2 wall frozen, no old Cu edits."""
import os
for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import copy,pickle,json,sys
from pathlib import Path
from inventory import sha
H=Path(__file__).resolve().parent
BASE=H/'field5-alternate-search-base-r149';O=H/'field5-IO3-preserving-In3-alternate-r149'
assert not BASE.exists();BASE.mkdir()
parent=H/'paired-regional-six-regulated-full-contact-audit-r142'
g,h,b,z,after=pickle.loads((parent/'REG_R130-regional-model.pkl').read_bytes())
root=pickle.loads((parent/'ROOT_R22-regional-model.pkl').read_bytes())
bad='8b448b65-d516-55ff-bd44-52dd5e298639';ded='ded2b949-0c87-5603-874b-a41f2f152e69'
z=[copy.deepcopy(q) for q in z if q['uuid']!=bad]
rm={q['uuid']:q for q in root[3]};z=[copy.deepcopy(rm[q['uuid']]) if q['uuid']==ded else q for q in z]
after=copy.deepcopy(after);after['zones']=[q for q in after['zones'] if q['uuid']!=bad]
peer=H.parent/'sbc-power/CORE1V2-source-native-outline-correction-r135/new-feed-zones.pkl'
assert peer.exists();pq=pickle.loads(peer.read_bytes());assert len(pq)==1 and pq[0]['uuid']=='2f346139-8f65-5990-b9e5-9d669e6c9438'
b=copy.deepcopy(b);b['field_regulated_search_hard_nominees']={'planes':pq,'discrete':{'tracks':[],'vias':[]},'source_qualified_peer_ROOT_spine_UUIDs_hard':[q['uuid'] for q in root[3] if q['uuid'].startswith(('f0ef','7b19','d03e','f0b2','5ac5'))]}
(BASE/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,after),protocol=5));(BASE/'receipt.json').write_text(json.dumps({'verdict':'SEARCH_ONLY_WITHDRAW_BAD_OWNED_IN2_FEED','model_sha256':sha(BASE/'model.pkl'),'R142_model_sha256':sha(parent/'REG_R130-regional-model.pkl'),'withdraw_only_bad_REG_uuid':bad,'restore_ded2_exact_ROOT_R22_shape_for_reconstruction':True,'R135_new_peer_shape_sha256':sha(peer),'candidate_foreign_oldfills_inherited_SEARCH_ONLY_no_fresh_contact_credit':True},indent=1)+'\n',encoding='utf-8')
s=(H/'construct_regulated_adaptive_feeds_r76.py').read_text(encoding='utf-8')
s=s.replace("OUT=HERE/'regulated-adaptive-source-feeds-r76';BASE=HERE/'c-u19008-actual-regulated-search-base-r84'", "OUT=HERE/'field5-IO3-preserving-In3-alternate-r149';BASE=HERE/'field5-alternate-search-base-r149'")
s=s.replace("INNER=['In1.Cu','In4.Cu','In3.Cu','In2.Cu']", "INNER=['In3.Cu']")
s=s.replace("for bank,net,ref,pin,policy in PORTS:", "for bank,net,ref,pin,policy in [x for x in PORTS if x[0]=='FIELD5']:")
s=s.replace("xs=gs[gi];print(bank,gi,'begin'", "xs=gs[gi];\n   if not any(q['kind']=='pad' and (q.get('ref'),q.get('pin'))==('R11071','1') for q in xs):continue\n   print(bank,gi,'begin'")
s=s.replace("and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93'", "and q['uuid']!='e852cf0c-fa5e-506c-9a4e-0e91a7593d93' and q['uuid'] not in hard.get('source_qualified_peer_ROOT_spine_UUIDs_hard',[])")
s=s.replace("for width in(.5,.35):\n    for margin in(8.,25.,60.,140.,None):", "for margin in(8.,25.,60.,140.,None):\n    for width in(.35,.5):")
s=s.replace("native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(free)) if q.intersection(core).area>1e-9]),1e-6)", "construction_free=set_precision(free.buffer(-.00002),1e-6);native=set_precision(unary_union([q for q in polys(line.buffer(max(.6,width),quad_segs=64).intersection(construction_free)) if q.intersection(core).area>1e-9]),1e-6)")
s=s.replace("   if not answer:\n    for a in sorted", "   if not answer:\n    for a in []: # existing plated ports only, no new-via fallback\n")
s=s.replace('controller-regulated-r76/', 'controller-regulated-IO3-preserving-r149/')
s=s.replace('.read_text()', ".read_text(encoding='utf-8')")
exec(compile(s,str(H/'construct_regulated_adaptive_feeds_r76.py'),'exec'))
