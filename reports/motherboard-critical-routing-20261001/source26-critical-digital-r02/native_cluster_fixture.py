"""Real native copper-cluster control; never equate KIID proxy repr with UUID."""
from pathlib import Path
import json,uuid
import pcbnew as p
OUT=Path(__file__).resolve().parent
def fixture(joined,cut=False):
 b=p.BOARD();n=p.NETINFO_ITEM(b,'/REAL_CLOCK',1);b.Add(n);pads=[]
 for x in (10,20):
  f=p.FOOTPRINT(b);f.SetReference('U'+str(x));f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(10)));b.Add(f)
  q=p.PAD(f);q.SetNumber('1');q.SetAttribute(p.PAD_ATTRIB_SMD);q.SetShape(p.PAD_SHAPE_RECT);q.SetSize(p.VECTOR2I(p.FromMM(1),p.FromMM(1)));q.SetLayerSet(p.LSET.FrontMask());q.SetPosition(f.GetPosition());q.SetNet(n);f.Add(q);pads.append(q)
 if joined:
  t=p.PCB_TRACK(b);t.SetNet(n);t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.2));t.SetStart(pads[0].GetPosition());t.SetEnd(p.VECTOR2I(p.FromMM(19 if cut else 20),p.FromMM(10)));b.Add(t)
 b.BuildConnectivity();ids={q.m_Uuid.AsString():q for q in pads}
 assert len(ids)==2
 for u in ids:uuid.UUID(u)
 conn=b.GetConnectivity();pending=dict(ids);cs=[]
 while pending:
  u,q=next(iter(pending.items()));connected={x.m_Uuid.AsString()for x in conn.GetConnectedItems(q)if x.Type()==p.PCB_PAD_T}|{u}
  group=set(pending)&connected;cs.append(sorted(group));pending={k:v for k,v in pending.items()if k not in group}
 return len(cs),cs
results=[]
for name,joined,cut,want in [('actual_unrouted_two_pads',False,False,2),('actual_native_join',True,False,1),('actual_cut_one_mm_gap',True,True,2)]:
 got,groups=fixture(joined,cut);assert got==want,(name,got,want);results.append(dict(name=name,actual_clusters=got,expected=want,pad_groups=groups,passed=True))
(OUT/'native-cluster-control.json').write_text(json.dumps(dict(passed=True,cases=results),indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(results))))
