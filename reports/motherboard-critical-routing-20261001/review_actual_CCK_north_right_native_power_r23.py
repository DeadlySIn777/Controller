"""Exact candidate IO3 proof, with separately bound literal CORE proof.
Original general r07 remains byte-exact. Only its CORE-equality gate is
replaced in this report-local function by an actual independently reviewed
same-board CORE source/backbone/annulus proof; all IO3 guards stay verbatim.
"""
from pathlib import Path
import sys,types,json,hashlib
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_north_right_CORE_preservation_r22 as core
p=Path(__file__).parent;before=p/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb';after=p/'actual-source26-root84-CCK-north-right-restored-r20/motherboard-FPGA-flash-CCK-candidate.kicad_pcb';out=p/'CCK-north-right-native-power-review-r23';out.mkdir(exist_ok=False)
sha=core.sha;assert sha(core.FROZEN)=='c9068f6f9855e23e71bef433784119a85a6097e49252624b90020d1bc66a15ff'
old=" if not symmetric_equal(bf['/CORE_1V2',pcbnew.In3_Cu],af['/CORE_1V2',pcbnew.In3_Cu]):raise ValueError('CORE1V2 filled power copper changed')"
new=" literal_CORE_proof=exact_literal_CORE_review(before_board,after_board)\n if not literal_CORE_proof['passed']:raise ValueError('Literal separately reviewed CORE proof failed')"
text=core.FROZEN.read_text();assert text.count(old)==1;text=text.replace(old,new)
text=text.replace('CORE1V2_exact_filled_geometry_preserved=True,','CORE1V2_exact_filled_geometry_preserved=False,literal_separate_CORE_proof=literal_CORE_proof,')
module=types.ModuleType('same_board_literal_IO3_r04');module.__file__=str(core.FROZEN.resolve());module.exact_literal_CORE_review=core.review;exec(compile(text,str(core.FROZEN),'exec'),module.__dict__)
b,a=pcbnew.LoadBoard(str(before)),pcbnew.LoadBoard(str(after))
try:r=module.review(b,a)
except Exception as ex:r=dict(passed=False,error=str(ex),generic_frozen_power_helper_unchanged=True,manufacturing_ready=False)
r.update(before_board_sha256=sha(before),after_board_sha256=sha(after),same_IO3_body_all_guards_except_independently_proved_CORE_gate_verbatim=True,generic_original_power_helper_sha256=sha(core.FROZEN),scope='Only the literal12Cu/C1022 CCK donor against exact cleaned CORE baseline',loaded_capacity_not_proven=True,adopted=False)
(out/'review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=r['passed'],error=r.get('error'))))
