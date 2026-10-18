from pathlib import Path
p=Path(__file__).parent
s=(p/'inspect_ROOT85_power_cut_vs_cleanup.py').read_text()
s=s.replace("out=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85')", "out=p/'actual-source26-root87-In2-extended-r20'")
s=s.replace('reports/motherboard-ordinary-routing-20261001/IO3-literal-unused-tip-cleanup-r01/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb','reports/motherboard-pcb-integration-20261001/source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb')
s=s.replace("out/'motherboard-bounded-merged-candidate.kicad_pcb'", "out/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'")
s=s.replace("p/'actual-source26-root83-In2-batch-r12/proposed-groups.json'", "out/'proposed-groups.json'")
out=p/'inspect_DI7_power_cut_r23.py';assert not out.exists();out.write_text(s)
