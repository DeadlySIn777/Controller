"""Real native polygon controls and complete actual unchanged-board positive."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent));import check_io3_backbone_preservation_r02 as h
import pcbnew
p=Path(__file__).parent/'io3-relative-power-screen-native-r02';p.mkdir(exist_ok=False)
controls=[]
before=h.box(0,0,10,10);after=h.subtract(before,h.circle((pcbnew.FromMM(5),pcbnew.FromMM(5)),pcbnew.FromMM(.35)))
positive=h.backbone(before,after);assert positive['passed'];controls.append(dict(name='literal central small hole keeps broad backbone',accepted=True))
cases=[]
cases.append(('cut actual whole broad backbone',before,h.subtract(before,h.box(4,-1,6,11))))
narrow=h.box(-4,-2,0,2);narrow.BooleanAdd(h.box(2,-2,6,2));narrow.BooleanAdd(h.box(0,-.4,2,.4));narrow.Simplify()
cases.append(('cut old sub1mm neck absent from erosion',narrow,h.subtract(narrow,h.box(.7,-.5,1.3,.5))))
separate=h.box(0,0,4,4);separate.BooleanAdd(h.box(6,0,10,4));separate.Simplify()
cases.append(('lose a whole old separate component',separate,h.box(0,0,4,4)))
cases.append(('empty erosion earns no power credit',h.box(0,0,5,.4),h.box(0,0,5,.4)))
cases.append(('empty after fill',before,pcbnew.SHAPE_POLY_SET()))
# Precision is bounded by distance, never total removed area. A2um-long,
# 32nm-deep real notch in a0.8mm neck has only6.4e-8mm2 area but must fail.
cases.append(('real tiny-area32nm notch in old thin neck',narrow,h.subtract(narrow,h.box(.8,.399968,.802,.401))))
cases.append(('real2um partial-width neck erosion',narrow,h.subtract(narrow,h.box(.8,.398,1.2,.401))))
for name,a,b in cases:
 try:h.backbone(a,b)
 except ValueError as ex:controls.append(dict(name=name,rejected=True,reason=str(ex)))
 else:raise AssertionError(name)
board=h.ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb'
before_board=pcbnew.LoadBoard(str(board));after_board=pcbnew.LoadBoard(str(board));actual=h.review(before_board,after_board)
(p/'receipt.json').write_text(json.dumps(dict(passed=True,helper_sha256=h.sha(h.__file__),test_sha256=h.sha(__file__),actual_board_sha256=h.sha(board),actual_unchanged_board_positive=actual,native_polygon_controls=controls,synthetic_polygon_controls_are_not_physical_hardware_tests=True,manufacturing_ready=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,actual_receivers=len(actual['actual44_receiver_endpoints']),actual_annuli=len(actual['actual22_receiving_annuli']),native_polygon_controls=len(controls),real_board_prior_1mm_components=actual['backbone']['prior_backbone_components'])))
