"""Bind the full seven-route check to the physically repaired, qualified baseline."""
from pathlib import Path
import hashlib
root=Path(__file__).parent
source=root/'verify_seven_pair_combined_r15.py'
out=root/'verify_seven_pair_combined_r18.py'
assert not out.exists()
s=source.read_text()
s=s.replace("donor=root/'actual-source26-root83-In2-batch-r12'", "donor=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86')\nassert e.sha(donor/'motherboard-bounded-merged-candidate.kicad_pcb')=='282e0e5b6cf7684ea844f693fd184d70ab18b72ac2c4a0b5a3c8064d4e817cb7'")
s=s.replace('IO3-literal-unused-tip-cleanup-r01/', 'IO3-literal-unused-tip-cleanup-r02/')
s=s.replace('motherboard-ordinary-In2-batch-candidate.kicad_pcb', 'motherboard-bounded-merged-candidate.kicad_pcb')
s=s.replace("ORIGINAL=Path(", "assert e.sha(BASE)=='e433fb8a669085dbef80a92e967d09170b16c5560e44c8cf2cdad61fc2e2dcd7'\nORIGINAL=Path(")
s=s.replace("powerproof=power.review(before,after);e.write", "powerproof=power.review(before,after);assert powerproof['passed'];e.write")
out.write_text(s)
print(out, hashlib.sha256(out.read_bytes()).hexdigest())
p=Path('reports/motherboard-pcb-integration-20261001')
t=(p/'run-root86-checks-r01.py').read_text()
t=t.replace('source26-seven-path-OBS29-repair-trial-r86','source26-seven-path-larger-IO3-cleanup-trial-r87').replace('source26-r86-r01','source26-r87-r01')
t=t.replace('seven-new-source-return-only','seven-new-full').replace('verify_seven_pair_source_return_r16.py','verify_seven_pair_combined_r18.py').replace('combined-seven-pair-source-return-proof','combined-seven-pair-full-proof')
dest=p/'run-root87-checks-r01.py'
assert not dest.exists()
dest.write_text(t)
