import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_logic_return import mm
base='reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/motherboard-source26-return-bridges-candidate.kicad_pcb';b=pcbnew.LoadBoard(base);b.BuildConnectivity();items={t.m_Uuid.AsString():t for t in b.GetTracks()};rows=json.loads(Path('reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/unanchored-semantic-classification.json').read_text())['rows']
for row in rows:
 if row['exact_owned_pad_projections']:continue
 print('\nRESOURCE',row['net'],row['reference_layer'],row['filled_piece'],row['area_mm2'],flush=True)
 for uid in row['exact_owned_copper_projections']:
  t=items[uid];sources=[(p.GetParentFootprint().GetReference(),p.GetNumber())for p in b.GetConnectivity().GetConnectedItems(t)if isinstance(p,pcbnew.PAD)and p.GetNumber()and p.GetNetname()==t.GetNetname()]
  print(uid,'via'if isinstance(t,pcbnew.PCB_VIA)else b.GetLayerName(t.GetLayer()),t.GetNetname(),mm(t.GetStart()),mm(t.GetEnd()),'SOURCEcount',len(sources),'first',sources[:4],flush=True)
