"""Separate Source/return/cut proof from the still-open composed power review."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'verify_seven_pair_combined_r15.py').read_text()
s=s.replace('Recheck every literal ordinary path on the actual combined native board.','Source/return/cut proof only. Current-board power qualification is required separately.')
s=s.replace("root=Path(__file__).parent;donor=root/'actual-source26-root83-In2-batch-r12'", "root=Path(__file__).parent;donor=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-OBS29-repair-trial-r86')\nassert e.sha(donor/'motherboard-bounded-merged-candidate.kicad_pcb')=='282e0e5b6cf7684ea844f693fd184d70ab18b72ac2c4a0b5a3c8064d4e817cb7'")
s=s.replace("donor/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'", "donor/'motherboard-bounded-merged-candidate.kicad_pcb'")
s=s.replace("powerproof=power.review(before,after);e.write(a.out/'actual-IO3-power-geometry-proof.json',powerproof)", "# The full r15 guard failure is preserved. This checker proves only Source,\n# exact routed Cu, actual reference and cuts; adoption needs independent power.")
s=s.replace("actual_power_geometry_proof_sha256=e.sha(a.out/'actual-IO3-power-geometry-proof.json'),", "includes_power_verification=False,current_board_composed_power_proof_separately_required=True,")
s=s.replace("e.write(a.out/'review.json',dict(passed=True,", "e.write(a.out/'review.json',dict(passed=True,scope='Seven actual Source pairs, exact native Cu, own reference and physical cut controls only; no power qualification',")
dest=p/'verify_seven_pair_source_return_r16.py';assert not dest.exists();dest.write_text(s);compile(s,str(dest),'exec')
q=Path('reports/motherboard-pcb-integration-20261001');runner=(q/'run-root85-checks-r01.py').read_text().replace('source26-seven-path-IO3-tip-trial-r85','source26-seven-path-OBS29-repair-trial-r86').replace('source26-r85-r01','source26-r86-r01').replace('verify_seven_pair_combined_r15.py','verify_seven_pair_source_return_r16.py').replace("'seven-new-ordinary'", "'seven-new-source-return-only'").replace("p/'combined-seven-pair-proof'", "p/'combined-seven-pair-source-return-proof'")
start=runner.index("with(p/'map-command.log')");end=runner.index("common=['--board'",start);runner=runner[:start]+"assert mp.exists()\n"+runner[end:]
dest=q/'run-root86-checks-r01.py';assert not dest.exists();dest.write_text(runner);compile(runner,str(dest),'exec')
print(dest)
