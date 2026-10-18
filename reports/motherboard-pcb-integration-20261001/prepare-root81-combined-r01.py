"""Keep every ROOT80 acceptance check and add exact ADC-cell evidence."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'verify-root80-combined.py').read_text()
s=s.replace('ROOT80','ROOT81').replace("P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-two-ground-contacts-r80'","P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81'")
s=s.replace("old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-critical7-r79/motherboard-bounded-merged-candidate.kicad_pcb'","old=ROOT/'reports/motherboard-pcb-integration-20261001/source26-two-ground-contacts-r80/motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace('source26-r80-r01/domain-map.json','source26-r81-r01/domain-map.json')
s=s.replace("assert len(resources['unanchored_components'])==2","assert len(resources['unanchored_components'])==1")
s=s.replace('remaining_real_reference_resources=2','remaining_real_reference_resources=1')
anchor='\nchecks=[]\n';assert s.count(anchor)==1
s=s.replace(anchor,"\nadc_proof=P/'combined-C19042-proof.json'\nadc=read(adc_proof)\nassert adc['passed'] and adc['board_sha256']==sha(board)\nassert any(Path(k).resolve()==mp.resolve() and v==sha(mp)for k,v in adc['input_sha256'].items())\nfrozen[str(adc_proof)]=sha(adc_proof)\n"+anchor)
s=s.replace('two_actual_inner_ground_contacts_checked=True,','two_actual_inner_ground_contacts_checked=True,exact_ADC_C19042_actual_loop_and_SOURCE_reference_proof=str(adc_proof),')
(p/'verify-root81-combined.py').write_text(s)
compile(s,str(p/'verify-root81-combined.py'),'exec')
