import json,hashlib
from pathlib import Path
root=Path('reports/motherboard-power-entry-20261001/health-supply-r99')
files=[root/'motor-health-supply-candidate.kicad_pcb',root/'motor-health-supply-candidate.kicad_pro',root/'motor-health-supply-candidate.kicad_dru',root/'receipt.json',root/'bounded-scope.json',root/'independent-proof.json',Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-supply-builder-r95.py'),Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-source-barrel-r99.py'),Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-supply-independent-r105.py')]
(root/'freeze-receipt.json').write_text(json.dumps(dict(immutable_candidate=True,manufacturing_ready=False,input_output_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}),indent=2))
