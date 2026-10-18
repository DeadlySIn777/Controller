from pathlib import Path
import sys,json,importlib.util,hashlib
sys.path.insert(0,str(Path(__file__).parent))
import check_literal_CCK_CORE_preservation_r04 as core
import pcbnew
P=Path(__file__).parent;OUT=P/'CORE-cleaned-CCK-relative-review-r04';OUT.mkdir(exist_ok=False)
bp=P/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';ap=P/'CORE-literal-antipad-join-cck-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'
b,a=pcbnew.LoadBoard(str(bp)),pcbnew.LoadBoard(str(ap))
try:r=core.review(b,a)
except Exception as ex:r=dict(passed=False,error=str(ex),generic_frozen_CORE_guard_unchanged=True,failed_original_CCK_guard_retained=True,manufacturing_ready=False)
r.update(before_board_sha256=core.sha(bp),after_board_sha256=core.sha(ap),cleanup_adopted=False)
(OUT/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],error=r.get('error'))))
