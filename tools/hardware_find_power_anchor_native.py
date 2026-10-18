"""Read-only filled-copper and clearance search for actual owner anchors."""
import sys,json,math
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm,xy
b=pcbnew.LoadBoard(sys.argv[1]);b.BuildConnectivity();co=b.GetConnectivity();g=Geometry(b);fs={f.GetReference():f for f in b.GetFootprints()};out=[]
for ref,pin in [v.split('.')for v in sys.argv[2:]]:
 p=next(v for v in fs[ref].Pads()if v.GetNumber()==pin);pos=mm(p.GetPosition());n=p.GetNetname();rows=[]
 for layer in [pcbnew.F_Cu,pcbnew.B_Cu]:
  zs=[t for t in co.GetConnectedItems(p)if isinstance(t,pcbnew.ZONE)and t.IsOnLayer(layer)and t.GetNetname()==n]
  pts=[]
  for dx in range(-20,21):
   for dy in range(-20,21):
    pt=(round(pos[0]+dx,4),round(pos[1]+dy,4))
    if any(z.GetFilledPolysList(layer).Contains(xy(pt))for z in zs)and g.clear([pt,pt],n,layer,6):pts.append(pt)
  rows.append(dict(layer=b.GetLayerName(layer),zone_count=len(zs),anchors=sorted(pts,key=lambda q:math.dist(q,pos))[:20]))
 out.append(dict(ref=ref,pin=pin,net=n,pad=pos,rows=rows))
print(json.dumps(out,indent=2))
