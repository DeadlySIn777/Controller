"""Preserve every prior combined circuit check and add literal FLASH_MISO."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'verify-root83-combined.py').read_text()
s=s.replace('ROOT83','ROOT84').replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84'")
s=s.replace("old=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root81-composed-r01/motherboard-bounded-merged-candidate.kicad_pcb'", "old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-r83-r01/domain-map.json','source26-r84-r01/domain-map.json')
s=s.replace("merger=read(old.parent/'receipt.json');frozen[str(old.parent/'receipt.json')]=sha(old.parent/'receipt.json');", "ao1_merger=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO1-SDO-root81-composed-r01/receipt.json';merger=read(ao1_merger);frozen[str(ao1_merger)]=sha(ao1_merger);")
needle='\nchecks=[]\n';assert s.count(needle)==1
s=s.replace(needle,"""
flash_proof=P/'combined-FLASH-MISO-proof/review.json';flash=read(flash_proof)
assert flash['passed'] and flash['board_sha256']==sha(board) and flash['map_sha256']==sha(mp)
assert len(flash['exact_12_signal_UUIDs'])==12 and flash['no_signal_vias']
assert len(flash['actual_twelve_physical_route_cut_negatives'])==12
frozen[str(flash_proof)]=sha(flash_proof)
"""+needle)
s=s.replace('full_power_or_reference_qualification=False,manufacturing_ready=False)', 'additional_complete_FPGA_FLASH_MISO_proof=str(flash_proof),full_power_or_reference_qualification=False,manufacturing_ready=False)')
s=s.replace('global_power_or_reference_qualification=False,manufacturing_ready=False)', 'additional_complete_FPGA_FLASH_MISO_proof=str(flash_proof),global_power_or_reference_qualification=False,manufacturing_ready=False)')
s=s.replace('one complete AO1 SDO SOURCE-pair routes rechecked.', 'one complete AO1 SDO and one FPGA FLASH MISO SOURCE-pair routes rechecked.')
(p/'verify-root84-combined.py').write_text(s);compile(s,str(p/'verify-root84-combined.py'),'exec')
