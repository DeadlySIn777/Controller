"""Exact F/In2/F transport with explicit actual In1 reference binding."""
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'construct_DIC_In2_actual_paired_CMD_r198.py';assert not p.exists();s=(H/'construct_DIC_In3_actual_paired_CMD_r190.py').read_text();s=s.replace('DIC-In3-actual-paired-CMD-construction-r190','DIC-In2-actual-paired-CMD-construction-r198').replace('DIC_R190_EXACT_ROUTE','DIC_R198_EXACT_ROUTE');s=s.replace("(NET,'In3.Cu',so['signal'],to['signal'])","(NET,'In2.Cu',so['signal'],to['signal'])");s=s.replace("'signal_layer_chain':['F.Cu','In3.Cu','F.Cu']","'signal_layer_chain':['F.Cu','In2.Cu','F.Cu'],'In2_actual_source_reference_layer':'In1.Cu'")
s=s.replace("plane='In1.Cu' if layer=='F.Cu' else'In4.Cu'","plane='In1.Cu' if layer in('F.Cu','In2.Cu') else'In4.Cu'")
s=s.replace("plane='In1.Cu' if t['layer']=='F.Cu' else'In4.Cu'","plane='In1.Cu' if t['layer'] in('F.Cu','In2.Cu') else'In4.Cu'")
s=s.replace("oref={'F.Cu':orefs['In1.Cu'],'B.Cu':orefs['In4.Cu'],'In3.Cu':orefs['In4.Cu']}","oref={'F.Cu':orefs['In1.Cu'],'B.Cu':orefs['In4.Cu'],'In3.Cu':orefs['In4.Cu'],'In2.Cu':orefs['In1.Cu']}")
s=s.replace("nref={'F.Cu':finalrefs['In1.Cu'],'B.Cu':finalrefs['In4.Cu'],'In3.Cu':finalrefs['In4.Cu']}","nref={'F.Cu':finalrefs['In1.Cu'],'B.Cu':finalrefs['In4.Cu'],'In3.Cu':finalrefs['In4.Cu'],'In2.Cu':finalrefs['In1.Cu']}")
# Exact repeated buffer cache, with identical inputs/parameters/WKB semantics.
s=s.replace("pairproof=[]\n  for signal,ret,isnew in pairs:","pairproof=[];pair_insets={l:sh.buffer(-.075,quad_segs=128) for l,sh in refs.items()}\n  for signal,ret,isnew in pairs:")
s=s.replace("{l:ann.intersection(sh.buffer(-.075,quad_segs=128)).area for l,sh in refs.items()}","{l:ann.intersection(sh).area for l,sh in pair_insets.items()}")
s=s.replace('DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN','DIC_IN2_ACTUAL_IN1_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN').replace('DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_INCOMPLETE','DIC_IN2_ACTUAL_IN1_PAIRED_CMD_CONSTRUCTION_INCOMPLETE')
assert "(NET,'In2.Cu',so['signal'],to['signal'])" in s and "'In2.Cu':finalrefs['In1.Cu']" in s and 'pair_insets' in s
compile(s,str(p),'exec');p.write_text(s);print(p)
