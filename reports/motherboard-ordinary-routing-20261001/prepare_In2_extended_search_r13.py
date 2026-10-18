"""Extend the existing bounded search with prospective antipad avoidance.

Emits a report-local proposal generator only; source allowlist and all native
SOURCE/reference/DRC/power acceptance checks remain mandatory and unchanged.
"""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root83_In2_batch_r08.py').read_text()
s=s.replace("BASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')","BASE=Path(sys.argv[1])")
s=s.replace("MAP=Path('reports/motherboard-domains-20261001/source26-r83-r01/domain-map.json')","MAP=Path(sys.argv[2])")
s=s.replace('OUT=Path(sys.argv[1])','OUT=Path(sys.argv[3])')
s=s.replace("proof=pieces.qualify(BASE.parent/'literal-reference-resources.json',MAP,BASE", "proof=pieces.qualify(Path(sys.argv[4]),MAP,BASE")
s=s.replace('full_fills=fills;added=[];groups=[];blocked=[]','full_fills=fills;added=[];groups=[];blocked=[];prospective_signal_vias=[]')
needle='def clear(points,name,layer,width=.2,clearance=.20):'
insert='''def prospective_reference_clear(points,signal_vias):
    # A non-endpoint segment must stay outside the future reference antipad.
    # Endpoint segments still require the unchanged post-refill annulus proof.
    exclusion=.3+check.zone_clearance['/LOGIC_GND',pcbnew.In1_Cu]/1e6+.02+.20
    for a,z in zip(points,points[1:]):
        for via in signal_vias:
            if tuple(xy(via))in(tuple(xy(a)),tuple(xy(z))):continue
            if distance(via,a,z)<exclusion:return False
    return True

def enhanced_paths(start,end):
    for path in paths(start,end):
        yield path
        if len(path)>=3:
            first=path[1];d=math.dist(start,first)
            for length in(.25,.4,.6,.8,1.,1.2,1.5,2.,3.):
                if d<=length:continue
                bend=tuple(round(start[i]+length/d*(first[i]-start[i]),6)for i in(0,1))
                yield[start,bend,end]
        if len(path)>=4:
            prev,last=path[-3],path[-2];d=math.dist(prev,last)
            for retreat in(.4,.8,1.2,1.5,2,3,4):
                if d<=retreat:continue
                bend=tuple(round(last[i]+retreat/d*(prev[i]-last[i]),6)for i in(0,1))
                yield path[:-2]+[bend,end]

def clear(points,name,layer,width=.2,clearance=.20):
    if not prospective_reference_clear(points,prospective_signal_vias):return False'''
s=s.replace(needle,insert)
s=s.replace('for path in paths(center,pt)if sum','for path in enhanced_paths(center,pt)if prospective_reference_clear(path,[pt])and sum')
s=s.replace('t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair','t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetIsFree(True);t.SetRemoveUnconnected(False);t.SetLayerPair')
s=s.replace('if 0<length<=25:', 'if 0<length<=90:')
s=s.replace('for line in paths(av,zv)if sum','for line in enhanced_paths(av,zv)if prospective_reference_clear(line,[av,zv])and sum')
s=s.replace('zip(line,line[1:]))<=40','zip(line,line[1:]))<=140')
s=s.replace("if any(distance(gpt,s,t)<diam/2+.1+.20-1e-6", "if not all(prospective_reference_clear([s,t],[av,zv])for s,t,l in all_segments):continue\n        if any(distance(gpt,s,t)<diam/2+.1+.20-1e-6")
s=s.replace('chosen=(a,z,path);break','chosen=(a,z,path);break')
s=s.replace("if len(groups)>=8:break","prospective_signal_vias.extend([a['position'],z['position']])\n    if len(groups)>=24:break")
# New signal vias also require a full reference annulus clear of every previous
# proposed signal hole; otherwise a cached old fill can overstate its coverage.
s=s.replace("if not via_clear(pt,name,.6,.3):continue", "if not via_clear(pt,name,.6,.3):continue\n            if any(math.dist(pt,v)<1.34 for v in prospective_signal_vias):continue")
dest=p/'route_In2_extended_search_r13.py';assert not dest.exists();dest.write_text(s)
compile(s,str(dest),'exec')
print(dest)
