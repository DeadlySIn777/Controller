"""Create frozen R198 independent checker with supported own-hole credit."""
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'freeze_DIC_In2_supported_independent_r202.py';assert not p.exists()
s=(H/'prepare_DIC_full_independent_r188.py').read_text()
s=s.replace('DIC-actual-paired-CMD-construction-r186.json','DIC-In2-actual-paired-CMD-construction-r198.json').replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN','DIC_IN2_ACTUAL_IN1_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN')
s=s.replace('audit_DIC_actual_paired_CMD_independent_r188.py','audit_DIC_In2_supported_independent_r202.py').replace('DIC-actual-paired-CMD-independent-r188','DIC-In2-supported-independent-r202').replace('DIC_R188','DIC_R202').replace('R186_receipt_sha256','R198_receipt_sha256')
delta='''
s=s.replace("q['layer'] in('F.Cu','B.Cu')","q['layer'] in('F.Cu','B.Cu','In2.Cu')")
s=s.replace("(('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu'))","(('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu'))")
s=s.replace("own_by_net={net:unary_union([shape for uid,n,shape in own if n==net]) for net in(NET,CMD)};reference=[];referrors=[]","import DIC_source_supported_own_apertures_r200 as OS;A.read(OS.__file__);supported,ownsupport=OS.scopes(before,h,oldroot,oldrefs,own,inv);reference=[];referrors=list(ownsupport['errors'])")
s=s.replace("own_by_net.get(net,Point())","supported.get((net,t['layer']),Point())")
s=s.replace("'actual_source_reference_layer':'In1.Cu' if t['layer']=='F.Cu' else'In4.Cu'","'actual_source_reference_layer':'In1.Cu' if t['layer'] in('F.Cu','In2.Cu') else'In4.Cu'")
s=s.replace("'actual_source_paired_returns':pairproof,","'actual_source_paired_returns':pairproof,'source_supported_actual_own_apertures':ownsupport,")
s=s.replace("'latest_R73_ROOT55_U10017_R195_IO3_R201_exact_mutual':latest","'latest_actual_R214_IO3_R201_C1022_R222_exact_mutual':latest")
s=s.replace("'DIC_PAIRED_CMD_INDEPENDENT_EXACT_HOST_AND_LATEST_MUTUAL_PASS_COMBINED_NATIVE_OPEN'","'DIC_IN2_SUPPORTED_OWN_INDEPENDENT_HOST_LATEST_R214_MUTUAL_PASS_COMBINED_NATIVE_OPEN'")
'''
tail="compile(s,str(p),'exec');p.write_text(s);print(p)";assert tail in s;s=s.replace(tail,delta+'\n'+tail)
compile(s,str(p),'exec');p.write_text(s);print(p)
