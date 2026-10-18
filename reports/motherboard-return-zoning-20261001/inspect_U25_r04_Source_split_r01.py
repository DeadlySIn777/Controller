"""Record every exact native Source split from the U25 WIP correction."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_map_motherboard_domains import write,sha
from hardware_route_logic_return import mm
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');A=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/motherboard-U25-two-local-barrels-candidate.kicad_pcb');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r04-Source-split-diagnostic-r01');assert not O.exists();O.mkdir()
b=pcbnew.LoadBoard(str(B));a=pcbnew.LoadBoard(str(A));nets={p.GetNetname()for p in b.GetPads()if p.GetNumber()};old=native_pad_clusters(b,nets);new=native_pad_clusters(a,nets);where={p:(r['net'],set(r['pad_UUIDs']))for r in new for p in r['pad_UUIDs']};pads={p.m_Uuid.AsString():dict(reference=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),position_mm=mm(p.GetPosition()))for p in a.GetPads()};fail=[]
for row in old:
 current=where[row['pad_UUIDs'][0]]
 if row['net']!=current[0]or not set(row['pad_UUIDs'])<=current[1]:fail.append(dict(literal_net=row['net'],before_source_pads=[pads[u]for u in row['pad_UUIDs']],lost_from_representative=[pads[u]for u in set(row['pad_UUIDs'])-current[1]]))
write(O/'Source-split.json',dict(passed=not fail,before_board_sha256=sha(B),after_board_sha256=sha(A),before_native_clusters=len(old),after_native_clusters=len(new),failures=fail));print(json.dumps(dict(passed=not fail,failures=fail)),flush=True)
