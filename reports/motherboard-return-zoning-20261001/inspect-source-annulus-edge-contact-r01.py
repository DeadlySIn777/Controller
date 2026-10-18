import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle
from hardware_zone_motherboard_returns import split_polygons
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/source26-r56-rebased-bridges-r01/motherboard-source26-return-bridges-candidate.kicad_pcb');b.BuildConnectivity();conn=b.GetConnectivity();net='/motherboard_do/FIELD_B_0V';fill=collect_native_reference_fills(b,{net},[pcbnew.In4_Cu])[net,pcbnew.In4_Cu];pieces=list(split_polygons(fill));ids={'7ae8ef08-d819-4e87-96f2-6713ef610599','7e5bc92a-f359-49b6-bb5a-fa36753b8545'}
for v in b.GetTracks():
 if v.m_Uuid.AsString()not in ids:continue
 q=circle(tuple(v.GetPosition()),v.GetWidth(pcbnew.F_Cu)/2);hit=pcbnew.SHAPE_POLY_SET();hit.Append(pieces[21]);hit.BooleanIntersection(q)
 peers=list(conn.GetConnectedItems(v));print(v.m_Uuid.AsString(),dict(actualFlash=v.FlashLayer(pcbnew.In4_Cu),nativeConnected=conn.IsConnectedOnLayer(v,pcbnew.In4_Cu),centreInside=pieces[21].Contains(v.GetPosition()),annulusFillIntersectionArea_mm2=hit.Area()/1e12,sourcePads=[(p.GetParentFootprint().GetReference(),p.GetNumber())for p in peers if isinstance(p,pcbnew.PAD)and p.GetNumber()and p.GetNetname()==net],zones=[z.m_Uuid.AsString()for z in peers if isinstance(z,pcbnew.ZONE)]),flush=True)
