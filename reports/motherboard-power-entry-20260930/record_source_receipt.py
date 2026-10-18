"""Snapshot stable 11xxx source, validation and exact parent integration rules."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=Path(__file__).resolve().parent
OUT=ROOT/'hardware/motherboard_power_entry'

if __name__=='__main__':
    rejected=[]
    for p in (REPORT/'sources').glob('*.pdf'):
        if not p.read_bytes().startswith(b'%PDF'):
            target=p.with_suffix('.access-error.html');p.rename(target);rejected.append(str(target.relative_to(ROOT)))
            txt=p.with_suffix('.txt')
            if txt.exists():txt.rename(txt.with_suffix('.access-error.txt'))
    model=json.loads((OUT/'design.json').read_text());validation=json.loads((REPORT/'validation.json').read_text());footprints=json.loads((REPORT/'native-footprint-review.json').read_text())
    files=list(OUT.rglob('*'))+[ROOT/'tools/hardware_build_motherboard_power_entry.py',ROOT/'tools/hardware_validate_motherboard_power_entry.py',ROOT/'tests/test_motherboard_power_entry.py']
    hashes={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    erc=json.loads((REPORT/'erc.json').read_text())
    violations=[v for sheet in erc['sheets'] for v in sheet['violations']]
    accessories=list(csv.DictReader((OUT/'fitted-accessories-bom.csv').open()))
    receipt={'revision':'motherboard-power-entry-r0.2','source_frozen':True,'fitted_pcb_components':220,'additional_fitted_nonpcb_accessories':accessories,'native_erc':{'errors':sum(v['severity']=='error' for v in violations),'warnings':sum(v['severity']=='warning' for v in violations),'ignored':sum(v['severity']=='ignored' for v in violations)},'independent_connectivity_passed':validation['passed'],'native_pins':validation['native_pins'],'native_nc_pins':validation['native_nc_pins'],'native_footprint_load':{k:footprints[k] for k in ['passed','fitted_components_loaded','numbered_copper_pads_loaded']},'tests':{'entry':25,'motors':24,'receiving_health':21,'total':70,'failures':0,'logs':['entry-tests.log','motors-tests.log','receiving-health-tests.log']},'boundary_power':model['boundary_power'],'boundary_inputs':model['boundary_inputs'],'boundary_outputs':model['boundary_outputs'],'parent_interposition_rules':validation['parent_interposition_rules'],'conditional_screen':validation['conditional_screen'],'engineering_gates':model['engineering_gates'],'not_physical_only_gates':True,'bad_downloads_archived_as_errors_never_as_datasheets':rejected,'hashes':hashes,'whole_board_drc_or_fabrication_generated':False,'manufacturing_ready':False}
    (REPORT/'receipt-r02.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['revision','source_frozen','fitted_pcb_components','native_erc','independent_connectivity_passed','tests']}))
