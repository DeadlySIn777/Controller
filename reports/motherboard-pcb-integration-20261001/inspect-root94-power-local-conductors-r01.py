"""Locate the actual new copper around three narrowed IO3 backbone regions."""
from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm,distance
from hardware_populate_motherboard_pcb import write
r=Path('reports/motherboard-pcb-integration-20261001')
base=pcbnew.LoadBoard(str(r/'source26-seven-path-larger-IO3-cleanup-trial-r87/motherboard-bounded-merged-candidate.kicad_pcb'))
p=r/'source26-BankA-health-DI7-merged-r94';b=pcbnew.LoadBoard(str(p/'motherboard-bounded-merged-candidate.kicad_pcb'))
old={t.m_Uuid.AsString():identity(t)for t in base.GetTracks()}
records=[]
for point in((345.16,178.85),(274.54,180.7),(274.72,178.89)):
 rows=[]
 for t in b.GetTracks():
  u=t.m_Uuid.AsString();s,e=mm(t.GetStart()),mm(t.GetEnd());d=distance(point,s,e)
  if d<=2.2 and(t.Type()==pcbnew.PCB_VIA_T or t.GetLayer()==pcbnew.In2_Cu):
   rows.append(dict(uuid=u,net=t.GetNetname(),kind='via'if t.Type()==pcbnew.PCB_VIA_T else'segment',start=s,end=e,width=pcbnew.ToMM(t.GetWidth(pcbnew.In2_Cu)),drill=pcbnew.ToMM(t.GetDrillValue())if t.Type()==pcbnew.PCB_VIA_T else None,new_or_changed=old.get(u)!=identity(t),distance_mm=d))
 pads=[dict(ref=x.GetParentFootprint().GetReference(),pin=x.GetNumber(),net=x.GetNetname(),position=mm(x.GetPosition()),layers=x.GetLayerSet().FmtBin())for x in b.GetPads()if math.dist(point,mm(x.GetPosition()))<=2.2]
 records.append(dict(center=point,conductors=sorted(rows,key=lambda x:x['distance_mm']),pads=pads))
write(p/'rejected-power-local-conductors.json',dict(regions=records))
print(json.dumps(records,indent=2))
