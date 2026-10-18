"""Freeze actual six-layer native fixture evidence for the separate return gate."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'tests'))
import hardware_check_return_corridors as h
import test_motherboard_return_corridors as test
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[ROOT/'tools/hardware_check_return_corridors.py',ROOT/'tools/hardware_route_selected_additive.py',ROOT/'tests/test_motherboard_return_corridors.py',ROOT/'reports/motherboard-return-zoning-20260930/return-corridor-native-tests-r02.txt']
hashes={str(p):sha(p)for p in inputs};snapshot=OUT/'inputs';snapshot.mkdir()
for p in inputs:shutil.copy2(p,snapshot/p.name)
cases=[]
for kind in ['healthy','name_only','one_side_open','slot','large_hole','wrong_domain','wrong_reference','too_far']:
 folder=OUT/kind;folder.mkdir()
 b,added,rows,drc=test.fixture(folder,kind)
 try:r=h.return_corridor_check(b,added,rows);rejection=None
 except ValueError as exc:r=None;rejection=str(exc)
 expected=kind=='healthy'
 if bool(r)!=expected:raise ValueError('Unexpected native acceptance: '+kind)
 row=dict(kind=kind,expected_acceptance=expected,accepted=bool(r),rejection=rejection,
  board_sha256=sha(folder/'native.kicad_pcb'),project_sha256=sha(folder/'native.kicad_pro'),rules_sha256=sha(folder/'native.kicad_dru'),
  actual_native_drc_regular=len(drc.get('violations',[])),actual_native_ignored=drc.get('ignored_checks',[]),
  native_unconnected_items=len(drc.get('unconnected_items',[])),gate_receipt=r)
 (folder/'return-check.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8');cases.append(row)
 if expected and(row['actual_native_drc_regular']or row['actual_native_ignored']):raise ValueError('Healthy fixture native DRC does not pass fully')
for p,expected in hashes.items():
 if sha(Path(p))!=expected:raise ValueError('Frozen gate/test input changed')
receipt=dict(schema_version=1,tool_sha256=hashes[str(inputs[0])],input_sha256=hashes,
 fixture_scope='actual standalone six-layer native geometry; not a manufactured controller or a full-board route',
 focused_native_tests=dict(reported=9,passed=9,evidence='inputs/return-corridor-native-tests-r02.txt'),
 native_cases=cases,all_cases_as_expected=True,healthy_native_DRC_regular=0,healthy_native_DRC_ignored=[],
 original_router_unchanged=True,live_source_or_pcb_changed=False,
 bounded_exception='only exact same-net signal through-via endpoints with connected own-return stitch<=1mm and filled own-reference annulus/polygon proof',
 conservative_requirement='full0.20mm annulus and full ground-stitch copper projection are required; partial-plane edge contact is deliberately insufficient for this selected router',
 source_pad_evidence='native physically connected numbered copper pads; complete source reconciliation remains mandatory at integration',
 full_board_CLI_merge_DRC_and_uncapped_connectivity_not_executed_by_this_fixture=True,
 measured_return_impedance=False,physical_SI_EMC_qualification=False,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(tool_sha256=receipt['tool_sha256'],receipt_sha256=sha(OUT/'receipt.json'),native_cases=len(cases),healthy_native_DRC_regular=0,healthy_native_DRC_ignored=[])))
