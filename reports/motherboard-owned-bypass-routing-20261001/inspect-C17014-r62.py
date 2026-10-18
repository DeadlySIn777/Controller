from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_route_owned_bypass_loops_wip_r03 import Geometry,xy,mm
from hardware_route_local_signals import paths
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon
b=pcbnew.LoadBoard(str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'))
fp={f.GetReference():f for f in b.GetFootprints()}
owners=json.loads((ROOT/'reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json').read_text())
row=next(r for r in owners['capacitors']if r['ref']=='C17014')
pad=lambda ref,n:next(p for p in fp[ref].Pads()if p.GetNumber()==n)
cp=pad(row['ref'],row['cap_power']);cr=pad(row['ref'],row['cap_return'])
op=pad(row['power_nodes'][0]['ref'],row['power_nodes'][0]['pin'])
checker=NativeCollectedAnnulusCheck(b,{})
fill=checker.reference(cr.GetNetname(),pcbnew.In1_Cu);g=Geometry(b)
missing=corridor_polygon(tuple(cp.GetPosition()),tuple(op.GetPosition()),pcbnew.FromMM(.20));missing.BooleanSubtract(fill)
q=missing.BBox()
result=dict(owner=row['owner'],power_from=mm(cp.GetPosition()),power_to=mm(op.GetPosition()),
 cap_center_reference=fill.Contains(cp.GetPosition()),owner_center_reference=fill.Contains(op.GetPosition()),
 missing_area_mm2=missing.Area()/1e12,missing_bbox_mm=[pcbnew.ToMM(x)for x in(q.GetX(),q.GetY(),q.GetRight(),q.GetBottom())],legal_paths=[])
for points in paths(mm(cp.GetPosition()),mm(op.GetPosition())):
 if g.clear(points,cp.GetNetname(),pcbnew.F_Cu,width=.2)and all(covered(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.2)),fill)for s,e in zip(points,points[1:])):
  result['legal_paths'].append(points)
mapping=json.loads((ROOT/'reports/motherboard-domains-20261001/source26-r62-r01/domain-map.json').read_text())
result['nearby_source_pads']=[p for p in mapping['pads']if 370<p['position_mm'][0]<377 and 148<p['position_mm'][1]<154]
out=ROOT/'reports/motherboard-owned-bypass-routing-20261001/C17014-r62-native-inspection.json';out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k!='nearby_source_pads'},indent=2))
