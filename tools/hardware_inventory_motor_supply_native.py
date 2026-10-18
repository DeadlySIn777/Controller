"""Read-only actual motor power/monitor endpoint positions and native nets."""
import json,sys
from pathlib import Path
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard(sys.argv[1]);fs={f.GetReference():f for f in b.GetFootprints()};out=[]
for ref in ['R18001','U11008','U11010','U11011','U11012','R9001','R9003','R9011','R9013','U9001','U9002']+[f'U600{i}'for i in range(1,7)]:
 f=fs[ref];out.append(dict(ref=ref,origin=mm(f.GetPosition()),angle=f.GetOrientationDegrees(),pads=[dict(pin=p.GetNumber(),uuid=p.m_Uuid.AsString(),net=p.GetNetname(),point=mm(p.GetPosition()))for p in f.Pads()if p.GetNumber()]))
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n');print([(r['ref'],r['origin'])for r in out])
