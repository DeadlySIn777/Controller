import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
P=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r300');b=pcbnew.LoadBoard(str(P/'motherboard-health-U19-facing-cell-candidate.kicad_pcb'));pads={p.m_Uuid.AsString():p for p in b.GetPads()};r=json.loads((P/'receipt.json').read_text());
for s in r['prior_Source_cluster_splits']:
 print('GROUP',[(pads[u].GetParentFootprint().GetReference(),pads[u].GetNumber(),mm(pads[u].GetPosition()))for u in [s['source']]+s['missing']])
for tr in b.GetTracks():
 if tr.GetNetname()=='/mc_local_power/CORE_5V' and not isinstance(tr,pcbnew.PCB_VIA)and any(345<=q[0]<=346 and 177.5<=q[1]<=178.8 for q in [mm(tr.GetStart()),mm(tr.GetEnd())]):print(tr.m_Uuid.AsString(),b.GetLayerName(tr.GetLayer()),mm(tr.GetStart()),mm(tr.GetEnd()))

