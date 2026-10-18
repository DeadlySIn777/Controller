from pathlib import Path
p=Path('reports/motherboard-critical-routing-20261001/inspect_CCK_CORE_narrow_delta_r02.py');s=p.read_text().replace('actual-CORE-narrow-review-r02','unchanged-refill-CORE-review-r03')
s=s.replace("a=pcbnew.LoadBoard(str(P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'))","a=pcbnew.LoadBoard('reports/motherboard-critical-routing-20261001/source26-root84-unchanged-native-refill-control-r01/motherboard-bounded-merged-candidate.kicad_pcb')")
Path('reports/motherboard-critical-routing-20261001/inspect_ROOT84_refill_CORE_delta_r03.py').write_text(s)
