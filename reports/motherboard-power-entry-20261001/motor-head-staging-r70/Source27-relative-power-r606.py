import sys,json,hashlib,importlib.util
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
H=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');B=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');A=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r596/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');S=Path('reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/candidate/motherboard/design.json');O=Path('reports/motherboard-power-entry-20261001/Source27-relative-power-r606');assert not O.exists();O.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[H,B,A,S,Path(__file__),Path('hardware/motherboard/design.json')]};spec=importlib.util.spec_from_file_location('frozen_power_guard',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.SOURCE=S.resolve();b=pcbnew.LoadBoard(str(B));a=pcbnew.LoadBoard(str(A))
try:result=m.review(b,a)
except Exception as e:result=dict(passed=False,rejection=repr(e))
assert all(sha(Path(p))==h for p,h in inputs.items());result.update(input_hashes=inputs,no_guard_geometric_threshold_or_hardware_mutation=True,actual_staged_Source27_model_used=True);(O/'review.json').write_text(json.dumps(result,indent=2));print('RELATIVE_POWER',result['passed'],result.get('rejection'),flush=True)
