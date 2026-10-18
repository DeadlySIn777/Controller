"""Actual >=.20 manual local bends around the identified existing GND wall."""
from pathlib import Path
H=Path(__file__).resolve().parent;s=(H/'probe_core1v2_local_outer_joins_r105.py').read_text()
s=s.replace("O=L.OUT/'core1v2-local-outer-join-nominees-r105'","O=L.OUT/'core1v2-local-outer-join-nominees-r106'")
s=s.replace("('C1024','1',[('C1027','1'),('C1007','1'),('C1026','1')])", "('C1024','1',[('C1001','1')])")
a="""a,bp=nearest_points(body.buffer(-.03),gshape.buffer(-.03));coords=[list(map(lambda x:round(x,6),s)) for s in (a.coords[0],bp.coords[0])];line=LineString(coords);errors=[];region=line.buffer(2)"""
b="""a,bp=nearest_points(body.buffer(-.03),gshape.buffer(-.03));coords=[list(map(lambda x:round(x,6),s)) for s in (a.coords[0],bp.coords[0])]
            if (target_ref,target_pin,ref,pin)==('U1001','J7','U1001','J6'):coords=[[160.02,89.947],[159.36,89.947]]
            elif (target_ref,target_pin,ref,pin)==('C1024','1','C1001','1'):coords=[[158.19,80.3],[161.69,80.3],[161.69,81.127]]
            else:continue
            assert body.covers(Point(coords[0])) and gshape.covers(Point(coords[-1]))
            line=LineString(coords);errors=[];region=line.buffer(2)"""
assert s.count(a)==1;s=s.replace(a,b)
a="t=C.track('CORE1V2-local-r105-'+target_ref+'-'+target_pin,raw,'F.Cu',coords[0],coords[1],.20);accepted.append(t);answer=t;break"
b="ts=[C.track('CORE1V2-bent-local-r106-'+target_ref+'-'+target_pin+'-'+str(j),raw,'F.Cu',aa,bb,.20) for j,(aa,bb) in enumerate(zip(coords,coords[1:]))];accepted+=ts;answer=ts;break"
assert s.count(a)==1;s=s.replace(a,b)
out=H/'probe_core1v2_local_bent_joins_r106.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('CORE1V2_BOUND_LOCAL_BEND_DERIVED')
