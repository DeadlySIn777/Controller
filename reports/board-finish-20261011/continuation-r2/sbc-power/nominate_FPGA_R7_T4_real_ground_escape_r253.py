"""Preserved R252 successor; pad inventory uses its explicit ref field."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_FPGA_R7_T4_real_ground_escape_r252.py').read_text()
assert s.count("q['kind']=='pad'and q['source']['ref']=='U1001'")==1
s=s.replace("q['kind']=='pad'and q['source']['ref']=='U1001'","q['kind']=='pad'and q.get('ref')=='U1001'").replace('r252','r253').replace('R252','R253')
exec(compile(s,str(__file__),'exec'))
