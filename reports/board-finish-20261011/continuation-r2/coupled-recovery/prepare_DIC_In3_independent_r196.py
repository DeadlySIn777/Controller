"""Create independent reconstruction/final mutual auditor for frozen R190."""
from pathlib import Path
H=Path(__file__).resolve().parent;p=H/'freeze_DIC_In3_independent_r196.py';assert not p.exists()
s=(H/'prepare_DIC_full_independent_r188.py').read_text()
s=s.replace('DIC-actual-paired-CMD-construction-r186.json','DIC-In3-actual-paired-CMD-construction-r190.json').replace('DIC_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN','DIC_IN3_EXACT_REAL_PAIRED_CMD_CONSTRUCTION_POSITIVE_INDEPENDENT_OPEN')
s=s.replace('audit_DIC_actual_paired_CMD_independent_r188.py','audit_DIC_In3_CMD_independent_r196.py').replace('DIC-actual-paired-CMD-independent-r188','DIC-In3-CMD-independent-r196').replace('DIC_R188','DIC_R196').replace('R186_receipt_sha256','R190_receipt_sha256')
tail="compile(s,str(p),'exec');p.write_text(s);print(p)"
layer_delta="s=s.replace(\"q['layer'] in('F.Cu','B.Cu')\",\"q['layer'] in('F.Cu','B.Cu','In3.Cu')\")\n"
assert tail in s;s=s.replace(tail,layer_delta+tail)
compile(s,str(p),'exec');p.write_text(s);print(p)
