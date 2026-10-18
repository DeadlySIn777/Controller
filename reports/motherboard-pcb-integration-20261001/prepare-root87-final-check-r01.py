"""Prepare, but do not execute, exact combined-board ROOT87 acceptance."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'verify-root84-combined.py').read_text()
def replace_once(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b)
replace_once('before adopting ROOT84','before adopting ROOT87')
replace_once("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84'", "P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87'")
replace_once("old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb'", "old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb'")
replace_once('source26-r84-r01/domain-map.json','source26-r87-r01/domain-map.json')
replace_once("P/'receipt.json'", "P/'route-assembly-proposal.json'")
replace_once("flash_proof=ROOT/'reports/motherboard-critical-routing-20261001/actual-source26-root83-FPGA-flash-MISO-F-only-r03/root84-combined-proof-r03/review.json'", "flash_proof=P/'combined-retained-FLASH-MISO-proof/review.json'")
replace_once("reports/motherboard-critical-routing-20261001/verify_FLASH_MISO_F12_combined_r03.py", "reports/motherboard-critical-routing-20261001/verify_FLASH_MISO_F12_composed_power_r05.py")
insert='''
seven_path=P/'combined-seven-pair-full-proof/review.json';seven=read(seven_path)
power_path=P/'combined-seven-pair-full-proof/actual-IO3-power-geometry-proof.json';power=read(power_path)
cleanup_path=R/'IO3-literal-tip-cleanup-independent-r08/receipt.json';cleanup=read(cleanup_path)
assert sha(cleanup_path)=='03cf0effbcc73f1190268c5c6007438ca3792b55cdf7e0550ca93e66ff0527ed'
assert cleanup['passed'] and cleanup['all_definite_old_thin_features_outside_exact_region_retained']
assert seven['passed'] and seven['board_sha256']==sha(board)
assert seven['all7_actual_pairs_closed'] and seven['actual_new_copper']==65
assert len(seven['actual_persisted_route_cuts'])==7 and all(row['disconnected']for row in seven['actual_persisted_route_cuts'])
assert seven['actual_power_geometry_proof_sha256']==sha(power_path) and power['passed']
assert power['CORE1V2_exact_filled_geometry_preserved'] and power['old_exact_rail_copper_preserved']
assert len(power['actual44_receiver_endpoints'])==44 and len(power['actual22_receiving_annuli'])==22
assert not seven['native_errors'] and not seven['native_warnings'] and not seven['ignored_checks']
for dependency,h in seven['input_sha256'].items():assert sha(Path(dependency))==h
for ep in(seven_path,power_path,cleanup_path,ROOT/'reports/motherboard-ordinary-routing-20261001/verify_seven_pair_combined_r18.py'):
 frozen[str(ep)]=sha(ep)
assert sha(board)=='0a9e4975b2d9cd90f7853884d626427fb089809c45ae5ed749472c68235e2d13'
'''
replace_once('checks=[]\n',insert+'\nchecks=[]\n')
s=s.replace('additional_complete_FPGA_FLASH_MISO_proof=str(flash_proof),', 'additional_complete_FPGA_FLASH_MISO_proof=str(flash_proof),additional_seven_complete_SOURCE_pair_proof=str(seven_path),current_unchanged_r07_power_proof=str(power_path),separate_literal_IO3_cleanup_proof=str(cleanup_path),')
replace_once('and one FPGA FLASH MISO SOURCE-pair routes rechecked.', 'and one FPGA FLASH MISO plus seven additional ordinary SOURCE-pair routes rechecked; literal unused IO3 tip cleanup independently qualified.')
dest=p/'verify-root87-combined.py'
assert not dest.exists()
dest.write_text(s)
print(dest)
