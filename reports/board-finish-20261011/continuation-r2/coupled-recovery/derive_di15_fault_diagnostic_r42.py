"""Preserve R40 failed JSON wrapper; retain exact shape by WKB hash."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'diagnose_di15_fault_transport_coupling_r40.py').read_text()
s=s.replace("'parsed':q}","'parsed':{k:v for k,v in q.items() if k!='shape'},'exact_shape_WKB_sha256':C.sha(q['shape'].wkb)}")
s=s.replace('di15-fault-transport-coupling-diagnostic-r40.json','di15-fault-transport-coupling-diagnostic-r42.json').replace('di15-r40-nine-removal-transport-checkpoint.pkl','di15-r42-nine-removal-transport-checkpoint.pkl')
out=HERE/'diagnose_di15_fault_transport_coupling_r42.py';assert not out.exists();out.write_text(s)
