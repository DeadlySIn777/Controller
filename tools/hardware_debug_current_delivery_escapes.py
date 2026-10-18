import sys,json,math
from pathlib import Path
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm,xy
b=pcbnew.LoadBoard(sys.argv[1]);b.BuildConnectivity();co=b.GetConnectivity();g=Geometry(b);fs={f.GetReference():f for f in b.GetFootprints()};rows=[]
for rr in json.loads(Path(sys.argv[2]).read_text())['routes']:
 if rr['name']!=sys.argv[3]:continue
 for side in ['from','to']:
  row=rr[side];ps=[p for p in fs[row['ref']].Pads()if p.GetNumber()==str(row['pin'])];p=ps[row.get('pin_occurrence',-1)];s=tuple(row.get('point_mm',mm(p.GetPosition())));n=p.GetNetname();l=pcbnew.B_Cu;esc=[]
  for d in [3,6,8,10]:
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(.707107,-.707107),(-.707107,.707107),(-.707107,-.707107)]:
    z=(s[0]+d*dx,s[1]+d*dy)
    esc.append(dict(point=z,neck_clear=g.clear([s,z],n,l,2),wide_end_clear=g.clear([z,z],n,l,6)))
  rows.append(dict(side=side,actual_pad=mm(p.GetPosition()),point=s,connected_objects=len(co.GetConnectedItems(p)),actual_anchor_hits=[dict(type=t.Type(),net=t.GetNetname(),uuid=t.m_Uuid.AsString())for t in co.GetConnectedItems(p)if t.IsOnLayer(l)and t.HitTest(xy(s))],escapes=esc))
print(json.dumps(rows,indent=2))
