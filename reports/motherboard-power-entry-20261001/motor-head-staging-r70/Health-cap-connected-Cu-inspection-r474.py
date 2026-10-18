import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity();out=[]
for p in b.GetPads():
 if p.GetParentFootprint().GetReference()not in ['C11078','C11080']:continue
 direct=list(b.GetConnectivity().GetConnectedTracks(p));near=[]
 for t in b.GetTracks():
  if t.GetNetname()!=p.GetNetname()or not p.IsOnLayer(t.GetLayer()):continue
  if p.GetEffectiveShape(t.GetLayer()).Collide(t.GetEffectiveShape(t.GetLayer()),0):near.append(dict(uuid=t.m_Uuid.AsString(),identity=identity(t)))
 out.append(dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),position_mm=mm(p.GetPosition()),net=p.GetNetname(),actual_native_direct_Cu=[dict(uuid=t.m_Uuid.AsString(),identity=identity(t))for t in direct],actual_same_layer_shape_Cu=near))
O=Path('reports/motherboard-power-entry-20261001/ROOT102-health-cap-Cu-inspection-r474');O.mkdir();(O/'inspection.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
