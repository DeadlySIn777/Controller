from pathlib import Path
p=Path(__file__).parent;src=p/'inspect_CCK_CORE_physical_delta_r04.py';text=src.read_text()
old="BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb')"
new="BASE=Path('reports/motherboard-critical-routing-20261001/CORE-literal-antipad-join-baseline-r02/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb')"
assert text.count(old)==1;text=text.replace(old,new)
old="pcbnew.LoadBoard(str(P/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'))";new="pcbnew.LoadBoard('reports/motherboard-critical-routing-20261001/CORE-literal-antipad-join-cck-r02/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb')"
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("OUT=P/'actual-CORE-physical-delta-r04'","OUT=P/'actual-CORE-cleaned-pair-delta-r05'")
(p/'inspect_CCK_CORE_cleaned_delta_r05.py').write_text(text)
