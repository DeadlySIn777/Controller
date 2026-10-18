import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
A=Path('reports/motherboard-power-entry-20261001/ROOT101-bankB-output-cap-registration-r384/motor-bank-B-registration-candidate.kicad_pcb');B=Path('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r490/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-CORE-fill-inspection-r494');assert not O.exists();O.mkdir()
a=pcbnew.LoadBoard(str(A));b=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString()for t in a.GetTracks()};rows=[]
for name,q in [('before',a),('candidate',b)]:
 fills=[]
 for z in q.Zones():
  if z.GetNetname()!='/mc_local_power/CORE_5V':continue
  for layer in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:
   if not z.IsOnLayer(layer):continue
   p=z.GetFilledPolysList(layer)
   for k in range(p.OutlineCount()):
    outline=[mm(p.COutline(k).CPoint(i))for i in range(p.COutline(k).PointCount())];holes=[[mm(p.CHole(k,h).CPoint(i))for i in range(p.CHole(k,h).PointCount())]for h in range(p.HoleCount(k))]
    fills.append(dict(zone=z.m_Uuid.AsString(),layer=q.GetLayerName(layer),outer=outline,holes=holes))
 rows.append(dict(name=name,fills=fills))
new=[dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),position_mm=mm(t.GetPosition()),identity=identity(t))for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.m_Uuid.AsString()not in old and 250<mm(t.GetPosition())[0]<280 and 140<mm(t.GetPosition())[1]<170]
(O/'geometry.json').write_text(json.dumps(dict(Core5_fills=rows,new_actual_barrels=new),indent=2));print('FILLS',[(r['name'],len(r['fills']))for r in rows],'NEWBARRELS',len(new),flush=True)
