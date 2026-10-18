import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import identity,mm
b=pcbnew.LoadBoard(str(Path('reports/motherboard-pcb-integration-20261001/source26-ao-display-r50/motherboard-ao-display-reconciled-candidate.kicad_pcb').resolve()));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()}
for r in ['C14012','U14014','R14029','U14011']:
 f=fps[r];print(r,mm(f.GetPosition()),f.GetLayerName(),f.GetOrientationDegrees(),[(p.GetNumber(),p.GetNetname(),mm(p.GetPosition()))for p in f.Pads()])
f=fps['C14012'];items=[t for t in b.GetTracks()if any(t.GetNetname()==p.GetNetname()and(t.HitTest(p.GetPosition())or p.HitTest(t.GetStart())or p.HitTest(t.GetEnd()))for p in f.Pads())]
print('actual_touched_copper',[(t.m_Uuid.AsString(),identity(t))for t in items])
from hardware_route_owned_bypass_loops import Geometry
g=Geometry(b);op=next(p for p in fps['U14014'].Pads()if p.GetNumber()=='11');s=mm(op.GetPosition())
print('actual_input_escape',[(d,g.clear([s,(s[0]+d,s[1])],op.GetNetname(),pcbnew.F_Cu))for d in(.2,.5,1,1.5,2,3,4,5)])
print('actual_input_inward_escape',[(d,g.clear([s,(s[0]-d,s[1])],op.GetNetname(),pcbnew.F_Cu))for d in(.2,.5,1,1.5,2,3,4)])
from hardware_route_logic_return import segment_hits_box,segment_distance
end=(s[0]+1,s[1]);print('pin_escape_obstacles',[(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),box)for p,box in g.pads.candidates(s,end,.25)if p.IsOnLayer(pcbnew.F_Cu)and p.GetNetname()!=op.GetNetname()and segment_hits_box(s,end,box,.25)])
print('pin_escape_metal',[(name,a,z,w)for name,a,z,w in g.tracks[pcbnew.F_Cu].candidates(s,end,.6)if name!=op.GetNetname()and segment_distance(s,end,a,z)<.1+w/2+.15])
near=(125.6375,277.875)
print('exact_old_clock_junction',[(t.m_Uuid.AsString(),identity(t))for t in b.GetTracks()if t.GetNetname()=='/motherboard_operator/FAST_SR_CLK_BUFFER'and (mm(t.GetStart())==near or mm(t.GetEnd())==near)])
removed_items=[]
for t in list(b.GetTracks()):
 if t.m_Uuid.AsString()in {'a9ebc455-5dc9-4a45-9f70-5b45351e4560','fdd40b38-090e-4411-9fa4-5328aed881f3','5dfb8bb6-6990-4896-84f1-387ed5c4b5d1'}:removed_items.append(t);b.Remove(t)
g=Geometry(b)
print('same_line_clock_via_options',[(x,g.via((x,277.875),'/motherboard_operator/FAST_SR_CLK_BUFFER'))for x in (125.6375,125.7375,125.8375,125.9375,126.0375,126.1375,126.2375,126.3375,126.4375,126.5375,126.6375,126.7375,126.8375,126.9375)])
print('new_junction_pad_blocks',[(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),box)for p,box in g.pads.candidates((126.5,277.875),(126.5,277.875),.51)if segment_hits_box((126.5,277.875),(126.5,277.875),box,.4)])
pt=(125.9375,277.875)
print('alternate_junction_pad_blocks',[(p.GetParentFootprint().GetReference(),p.GetNumber(),p.GetNetname(),box)for p,box in g.pads.candidates(pt,pt,.51)if segment_hits_box(pt,pt,box,.4)])
print('alternate_junction_hole_blocks',[(q,d)for q,d in g.holes if __import__('math').dist(pt,q)<.1+d/2+.25-1e-6])
print('alternate_junction_keepouts',[(z.GetZoneName(),z.GetNetname())for z in g.keepouts if z.GetDoNotAllowVias()and z.Outline().Contains(pcbnew.VECTOR2I(round(pt[0]*1e6),round(pt[1]*1e6)))])
from hardware_route_logic_return import distance
print('alternate_junction_metal_blocks',[(b.GetLayerName(layer),name,a,z,w,distance(pt,a,z))for layer,index in g.tracks.items()for name,a,z,w in index.candidates(pt,pt,.51)if name!='/motherboard_operator/FAST_SR_CLK_BUFFER'and distance(pt,a,z)<.25+w/2+.205-1e-6])
