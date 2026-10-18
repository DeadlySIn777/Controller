"""Bounded real F/In2 common-reference routing trial on the frozen ordinary112 scope.

Emit additive native copper only. No acceptance until native refill/DRC,
SOURCE clustering, full literal return-annulus checks and cut controls pass.
"""
from pathlib import Path
import sys,json,math,copy,shutil,itertools,time
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_bind_ordinary_route_manifest_r03 as binder
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_critical_digital_wip_r05 as authority
from hardware_route_owned_bypass_loops_wip_r03 import Geometry
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,distance,segment_distance,segment_hits_box
from hardware_check_return_corridors import covered,circle,corridor_polygon
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
e=ordinary.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r81-r01/domain-map.json')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
frozen={str(p):e.sha(p)for p in(BASE,MAP,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'),Path(__file__))}
review=e.read(e.ROOT/ordinary.SOURCE)
proof=pieces.qualify(BASE.parent/'literal-reference-resources.json',MAP,BASE,{'/LOGIC_GND'},{'In1.Cu','In4.Cu'})
e.write(OUT/'piece-eligibility.json',proof)
m=binder.bind(BASE,OUT/'piece-eligibility.json',OUT/'manifest.json',set(review['nets']))
ordinary.INPUT_BOARD=BASE;ordinary.MAPPING=e.read(MAP)
ordinary.frozen_review_check(m,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity()
e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
check=ordinary.LiteralPieces(b,m['nets']);geo=Geometry(b)
fills={l:check.reference('/LOGIC_GND',r)for l,r in((pcbnew.F_Cu,pcbnew.In1_Cu),(pcbnew.In2_Cu,pcbnew.In1_Cu))}
ps={p.m_Uuid.AsString():p for p in b.GetPads()}
existing_ground=[t for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='/LOGIC_GND' and all(physical_reference_contact(t,l,b.GetConnectivity())for l in(pcbnew.In1_Cu,))]
full_fills=fills;added=[];groups=[];blocked=[]
# CORE_1V2 remains an absolute filled-copper obstacle. The bounded IO3
# hole/slot must separately pass exact post-refill topology/feed screening.
# No candidate is eligible from this search alone.
power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.In3_Cu,)}
for z in b.Zones():
    if not z.GetIsRuleArea()and z.GetLayer()in power_fills:
        power_fills[z.GetLayer()].BooleanAdd(z.GetFilledPolysList(z.GetLayer()))
for poly in power_fills.values():poly.Simplify()


def clear(points,name,layer,width=.2,clearance=.20):
    for a,z in zip(points,points[1:]):
        seg=pcbnew.SEG(xy(a),xy(z))
        for p,_ in geo.pads.candidates(a,z,width/2+clearance+.1):
            if p.IsOnLayer(layer)and p.GetNetname()!=name and p.GetEffectiveShape(layer).Collide(seg,pcbnew.FromMM(width/2+clearance-1e-6)):return False
        for other,p,q,w in geo.tracks[layer].candidates(a,z,width/2+.5):
            if other!=name and segment_distance(a,z,p,q)<width/2+w/2+clearance-1e-6:return False
        cu=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2))
        for zone in geo.keepouts:
            if zone.IsOnLayer(layer)and zone.GetDoNotAllowTracks():
                hit=pcbnew.SHAPE_POLY_SET();hit.Append(cu);hit.BooleanIntersection(zone.Outline())
                if hit.OutlineCount():return False
        if layer in power_fills:
            hit=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+clearance))
            hit.BooleanIntersection(power_fills[layer])
            if hit.OutlineCount():return False
        if not covered(corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.10)),fills[layer]):return False
    return True

def via_clear(pt,name,diameter,drill):
    radius=diameter/2
    if not .8+radius<pt[0]<459.2-radius or not .8+radius<pt[1]<339.2-radius:return False
    for p,box in geo.pads.candidates(pt,pt,radius+.25):
        if segment_hits_box(pt,pt,box,radius+.20):return False
    for zone in geo.keepouts:
        if zone.GetDoNotAllowVias():
            hit=circle(tuple(xy(pt)),pcbnew.FromMM(radius));hit.BooleanIntersection(zone.Outline())
            if hit.OutlineCount():return False
    for power_poly in power_fills.values():
        hit=circle(tuple(xy(pt)),pcbnew.FromMM(radius+.205));hit.BooleanIntersection(power_poly)
        if hit.OutlineCount():return False
    for index in geo.tracks.values():
        for other,a,z,w in index.candidates(pt,pt,radius+.55):
            if other!=name and distance(pt,a,z)<radius+w/2+.205-1e-6:return False
    return not any(math.dist(pt,q)<drill/2+d/2+.25-1e-6 for q,d in geo.holes)

def ground_at(pt):
    for v in existing_ground:
        d=math.dist(pt,mm(v.GetPosition()))
        if .8<=d<=1 and all(covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.24)),fill)for fill in fills.values()):
            return dict(existing_uuid=v.m_Uuid.AsString(),position=mm(v.GetPosition()))
    for radius in(.8,.9,1.):
        for i in range(8):
            p=(round(pt[0]+radius*math.cos(i*math.pi/4),6),round(pt[1]+radius*math.sin(i*math.pi/4),6))
            if via_clear(p,'/LOGIC_GND',.5,.2)and all(covered(circle(tuple(xy(p)),pcbnew.FromMM(.26)),fill)for fill in fills.values()):return dict(new_position=p)
    return None

def escapes(p,row):
    center=mm(p.GetPosition());name=p.GetNetname();result=[]
    # Radius includes exact manifest .60 via, maximum actual pour clearance,
    # .02 discretization allowance, and the full .20 outer return annulus.
    radius=.3+max(check.zone_clearance['/LOGIC_GND',l]for l in(pcbnew.In1_Cu,))/1e6+.02+.20
    for d in(.75,1.,1.25,1.5,2.,2.5,3.):
        for i in range(16):
            pt=(round(center[0]+d*math.cos(i*math.pi/8),6),round(center[1]+d*math.sin(i*math.pi/8),6))
            if not via_clear(pt,name,.6,.3)or not clear([center,pt],name,pcbnew.F_Cu):continue
            if not all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(radius)),fill)for fill in fills.values()):continue
            ground=ground_at(pt)
            if ground:result.append(dict(position=pt,ground=ground))
            if len(result)>=8:return result
    return result

def add_segment(a,z,name,layer):
    if math.dist(a,z)<1e-6:return None
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(layer);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

def add_via(pt,name,diameter,drill):
    t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(name));t.SetPosition(xy(pt));t.SetWidth(pcbnew.FromMM(diameter));t.SetDrill(pcbnew.FromMM(drill));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

jobs=[]
for name,row in m['nets'].items():
    if row['via_diameter_mm']!=.6 or row['via_drill_mm']!=.3:raise ValueError('Unexpected literal ordinary via rule')
    candidates=[p for p in ps.values()if p.GetNetname()==name and p.IsOnLayer(pcbnew.F_Cu)and p.GetParentFootprint().GetReference()!='U1001']
    for p,q in itertools.combinations(candidates,2):
        length=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
        pair={p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()}
        if pair=={'U17003.6','U17004.5'}:
            assert name=='/motherboard_status/OBS8_INVERTED'
            jobs.append((length,name,p,q))
for length,name,p,q in sorted(jobs,key=lambda x:x[0]):
    b.BuildConnectivity()
    if q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}:continue
    pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]
    # Exact native intersection can remove coverage, never add it. Final
    # acceptance recomputes complete actual filled reference and annuli.
    start,end=mm(p.GetPosition()),mm(q.GetPosition())
    bounds=(min(start[0],end[0])-10,min(start[1],end[1])-10,max(start[0],end[0])+10,max(start[1],end[1])+10)
    box=pcbnew.SHAPE_POLY_SET();box.NewOutline()
    for pt in((bounds[0],bounds[1]),(bounds[2],bounds[1]),(bounds[2],bounds[3]),(bounds[0],bounds[3])):box.Append(pcbnew.FromMM(pt[0]),pcbnew.FromMM(pt[1]))
    fills={}
    for layer,poly in full_fills.items():
        clipped=pcbnew.SHAPE_POLY_SET();clipped.Append(poly);clipped.BooleanIntersection(box);clipped.Simplify();fills[layer]=clipped
    row=m['nets'][name];starts=escapes(p,row);ends=escapes(q,row);chosen=None
    for a,z in sorted(itertools.product(starts,ends),key=lambda az:math.dist(az[0]['position'],az[1]['position'])):
        av,zv=a['position'],z['position']
        if math.dist(av,zv)<1.1:continue
        # Candidate vias/grounds are not in the cached index yet. Check all
        # same-group holes/copper against one another before committing.
        points=[(av,name,.6,.3),(zv,name,.6,.3)]
        for entry in(a,z):
            if 'new_position'in entry['ground']:points.append((entry['ground']['new_position'],'/LOGIC_GND',.5,.2))
        if any(math.dist(x[0],y[0])<max(x[3]/2+y[3]/2+.25,(x[2]+y[2])/2+.205 if x[1]!=y[1]else 0)-1e-6 for x,y in itertools.combinations(points,2)):continue
        path=next((line for line in paths(av,zv)if sum(math.dist(s,t)for s,t in zip(line,line[1:]))<=40 and clear(line,name,pcbnew.In2_Cu)),None)
        if path is None:continue
        all_segments=[(mm(p.GetPosition()),av,pcbnew.F_Cu),(mm(q.GetPosition()),zv,pcbnew.F_Cu)]+[(s,t,pcbnew.In2_Cu)for s,t in zip(path,path[1:])]
        if any(distance(gpt,s,t)<diam/2+.1+.20-1e-6 for gpt,gnet,diam,drill in points if gnet=='/LOGIC_GND'for s,t,l in all_segments):continue
        chosen=(a,z,path);break
    if chosen is None:
        blocked.append(dict(net=name,source_pair=pair,span_mm=length,start_choices=len(starts),end_choices=len(ends),reason='No conservative finite two-surface handoff/path'))
        print(json.dumps(blocked[-1]),flush=True);continue
    a,z,path=chosen;signal=[];grounds=[]
    for pad,entry in((p,a),(q,z)):
        signal.append(add_segment(mm(pad.GetPosition()),entry['position'],name,pcbnew.F_Cu))
        signal.append(add_via(entry['position'],name,.6,.3))
        if 'new_position'in entry['ground']:grounds.append(add_via(entry['ground']['new_position'],'/LOGIC_GND',.5,.2))
    signal.extend(add_segment(s,t,name,pcbnew.In2_Cu)for s,t in zip(path,path[1:]))
    groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],signal_UUIDs=[u for u in signal if u],ground_UUIDs=grounds,new_copper_UUIDs=[u for u in signal if u]+grounds,start=a,end=z,back_path_mm=path))
    print(json.dumps(dict(added_pair=pair,net=name,newCu=len(groups[-1]['new_copper_UUIDs']))),flush=True)
    if len(groups)>=12:break

dest=OUT/'motherboard-OBS8-common-In1-candidate.kicad_pcb'
pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
    if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
    elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'proposed-groups.json',dict(input_sha256=frozen,base_sha256=e.sha(BASE),groups=groups,blocked=blocked,new_copper_UUIDs=[t.m_Uuid.AsString()for t in added],actual_signal_layers=["F.Cu","In2.Cu"],actual_common_reference="In1.Cu",CORE1V2_preserved_as_actual_native_obstacle=True,IO3_1mm_backbone_and22_receiving_feed_preservation_pending=True,exact_native_fill_subset_clipping_search_only=True,native_refill_DRC_full_return_and_SOURCE_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
