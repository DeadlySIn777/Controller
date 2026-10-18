"""Create exact three-leg DIC In3 alternative after the measured B wall."""
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'construct_DIC_In3_actual_paired_CMD_r190.py';assert not p.exists();s=(H/'construct_DIC_actual_paired_CMD_r186.py').read_text();s=s.replace('DIC-actual-paired-CMD-construction-r186','DIC-In3-actual-paired-CMD-construction-r190').replace('DIC_R186_EXACT_ROUTE','DIC_R190_EXACT_ROUTE')
s=s.replace("(NET,'B.Cu',so['signal'],to['signal'])", "(NET,'In3.Cu',so['signal'],to['signal'])")
s=s.replace("'signal_layer_chain':['F.Cu','B.Cu','F.Cu']", "'signal_layer_chain':['F.Cu','In3.Cu','F.Cu'],'transport_delta_only_from_saved_B_constructor':True")
s=s.replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN','DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN').replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_INCOMPLETE','DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_INCOMPLETE')
assert "(NET,'In3.Cu',so['signal'],to['signal'])" in s and "(CMD,'B.Cu',[123.05,95.05],[128.549999,100.55])" in s
compile(s,str(p),'exec');p.write_text(s);print(p)
