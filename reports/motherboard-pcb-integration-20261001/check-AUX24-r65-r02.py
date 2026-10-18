from pathlib import Path
import json,sys,subprocess
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_populate_motherboard_pcb import sha
P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-AUX24-field-r65'
DONOR=ROOT/'reports/motherboard-power-entry-20261001/aux24-field-cell-r68/receipt.json'
r=json.loads(DONOR.read_text())
keys=['exact_added_zones','exact_retired_private_copper','exact_added_copper','actual_local_endpoint_checks','external_feed_routing_pending']
intent={k:r[k]for k in keys};intent.update(board_sha256=sha(P/'motherboard-bounded-merged-candidate.kicad_pcb'),native_errors=0,
 original_donor_receipt=dict(path=str(DONOR),sha256=sha(DONOR)),passed=False,intent_only=True,
 scope='Literal AUX24 cell ledger rebased only for actual combined independent validation; donor observations not promoted.')
(P/'rebased-cell-intent-r02.json').write_text(json.dumps(intent,indent=2)+'\n')
run=subprocess.run([sys.executable,str(ROOT/'tools/hardware_validate_aux24_field_cell_native.py'),
 '--before',str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'),
 '--board',str(P/'motherboard-bounded-merged-candidate.kicad_pcb'),
 '--receipt',str(P/'rebased-cell-intent-r02.json'),'--out',str(P/'combined-cell-proof-r02')],capture_output=True,text=True)
(P/'combined-cell-command-r02.txt').write_text(run.stdout+run.stderr);print(run.stdout+run.stderr);raise SystemExit(run.returncode)
