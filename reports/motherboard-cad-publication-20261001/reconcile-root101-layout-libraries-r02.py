"""Reconcile current actual graphics-only library overrides without relaxing lands."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_populate_motherboard_pcb import sha,write
from publish_full_motherboard_board_review_wip_r02 import library_land,copy_layout_resources
import pcbnew
root=Path('reports/motherboard-cad-publication-20261001')
stage=root/'ROOT101-self-contained-native-r01'
board=stage/'motherboard-bounded-merged-candidate.kicad_pcb'
base=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101')
old=Path('hardware/board_review/revisions/20260930-24/layout-graphics-review.json')
receipt=json.loads(old.read_text());overrides={r['FPID']:r for r in receipt['project_copied_library_overrides']}
isow=Path('reports/motherboard-chassis-20261001/isow-full-cells-r03')
parent=json.loads((isow/'receipt.json').read_text())
assert parent['all_lands_pin_nets_paste_mask_unchanged'] and parent['project_courtyard_only_override'] and parent['native_DRC_regular']==0
src=Path('hardware/motherboard/CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod')
current=stage/'CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod'
actual_historical=isow/'CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod'
assert sha(current)==sha(actual_historical)
assert library_land(pcbnew.FootprintLoad(str(src.parent),src.stem))==library_land(pcbnew.FootprintLoad(str(current.parent),current.stem))
overrides['CNC_MB_Comms:ISOW_DFM20_TI']=dict(FPID='CNC_MB_Comms:ISOW_DFM20_TI',original_sha256=sha(src),project_copy_sha256=sha(current),identical_land_pass=True,reason='Retain exact independently reviewed ISOW local capacitor courtyard outline; no new geometry edit.',original_proof=str(isow/'receipt.json'),original_proof_sha256=sha(isow/'receipt.json'))
assert sha(board)==sha(base/board.name)
drc=json.loads((base/'drc.json').read_text());assert not drc['violations'] and not drc['ignored_checks']
dest=root/'ROOT101-consolidated-layout-resource-review-r02.json';assert not dest.exists()
write(dest,dict(passed=True,scope='Read-only exact existing project-library reconciliation for WIP CAD publication',input_board_sha256=sha(board),candidate_board_sha256=sha(board),all_native_pad_geometry_pin_nets_piece_counts_and_poses_unchanged=True,native_DRC_regular_violations=0,native_DRC_ignored_checks=[],project_copied_library_overrides=list(overrides.values()),input_sha256={str(p.resolve()):sha(p)for p in [old,src,current,actual_historical,isow/'receipt.json',base/'adoption.json',base/'drc.json',Path(__file__)]},no_new_electrical_or_manufacturing_qualification=True,manufacturing_ready=False))
check=stage/'verified-current-copy-r02';assert not check.exists();check.mkdir()
result=copy_layout_resources(board,Path('hardware/motherboard'),check,pcbnew.LoadBoard(str(board)),dest)
write(stage/'completed-resource-review-r02.json',dict(passed=True,board_sha256=sha(board),resource_review=result,layout_receipt_sha256=sha(dest),native_board_source_rules_unchanged=True,manufacturing_ready=False))
print(dict(passed=True,used_FPIDs_checked=len(result['used_footprint_land_checks'])))
