"""Preserve R50 failure; blank/NPTH copper is foreign hard geometry."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
src=P/'repair_logic_core_splits_r50.py';dst=P/'repair_logic_core_splits_r53.py';s=src.read_text(encoding='utf-8')
assert "OUT=HERE/'logic-core-split-repair-r50'" in s
s=s.replace("OUT=HERE/'logic-core-split-repair-r50'","OUT=HERE/'logic-core-split-repair-r53'")
s=s.replace("def gap(other):return .15 if h['domains_normalized'][C.norm(other)]=='DOM_LOGIC' else .6\n ","")
s=s.replace("h['domains_normalized'][C.norm(other)]==domain","h['domains_normalized'].get(C.norm(other))==domain")
needle="net='/LOGIC_GND';gg=F.graph(after,net)"
assert needle in s
s=s.replace(needle,"(OUT/'projected-base.pkl').write_bytes(pickle.dumps((g,h,binding,zones,after),protocol=5));net='/LOGIC_GND';gg=F.graph(after,net)")
s=s.replace('controller-logic-core-split-r50/','controller-logic-core-split-r53/').replace('LOGIC-retained-CORE-split-r50-','LOGIC-retained-CORE-split-r53-')
assert not dst.exists();dst.write_text(s,encoding='utf-8')
failure=P/'logic-core-split-repair-r50/failure-receipt.json';assert not failure.exists();failure.write_text(json.dumps({'verdict':'HOST_CONSTRUCTOR_FAILED_BEFORE_REPAIR_EMISSION','exit_code':1,'error':'KeyError empty raw net in obstacle domain lookup','correct_scope':'blank/NPTH or otherwise unassigned Cu is foreign hard geometry with .6mm domain gap; never a same-net exemption','failed_builder_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'superseding_builder_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'source_board_modified':False,'native_jobs':0},indent=1)+'\n',encoding='utf-8')
print(dst)
