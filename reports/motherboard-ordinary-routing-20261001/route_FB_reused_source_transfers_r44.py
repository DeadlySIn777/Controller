"""Bounded real F/B dual-reference routing trial on the frozen ordinary112 scope.

Emit additive native copper only. No acceptance until native refill/DRC,
SOURCE clustering, full literal return-annulus checks and cut controls pass.
"""
from pathlib import Path
import sys,json,math,copy,shutil,itertools,time,heapq
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
BASE=Path(sys.argv[1])
MAP=Path(sys.argv[2])
OUT=Path(sys.argv[3]);OUT.mkdir(parents=True,exist_ok=False)
frozen={str(p):e.sha(p)for p in(BASE,MAP,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'),Path(__file__))}
review=e.read(e.ROOT/ordinary.SOURCE)
proof=pieces.qualify(Path(sys.argv[4]),MAP,BASE,{'/LOGIC_GND'},{'In1.Cu','In4.Cu'})
e.write(OUT/'piece-eligibility.json',proof)
m=binder.bind(BASE,OUT/'piece-eligibility.json',OUT/'manifest.json',set(review['nets']))
ordinary.INPUT_BOARD=BASE;ordinary.MAPPING=e.read(MAP)
ordinary.frozen_review_check(m,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity()
e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
check=ordinary.LiteralPieces(b,m['nets']);geo=Geometry(b)
fills={l:check.reference('/LOGIC_GND',r)for l,r in((pcbnew.F_Cu,pcbnew.In1_Cu),(pcbnew.B_Cu,pcbnew.In4_Cu))}
ps={p.m_Uuid.AsString():p for p in b.GetPads()}
existing_ground=[t for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='/LOGIC_GND' and all(physical_reference_contact(t,l,b.GetConnectivity())for l in(pcbnew.In1_Cu,pcbnew.In4_Cu))]
full_fills=fills;added=[];groups=[];blocked=[];prospective_signal_vias=[]
# CORE_1V2 remains an absolute filled-copper obstacle. The bounded IO3
# hole/slot must separately pass exact post-refill topology/feed screening.
# No candidate is eligible from this search alone.
power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.B_Cu,)}
critical_rows=e.read('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')['nets']
actual_reference_clearance=max([*check.zone_clearance.values(),*[z.GetLocalClearance()for z in b.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/LOGIC_GND'and any(z.IsOnLayer(l)for l in(pcbnew.In1_Cu,pcbnew.In4_Cu))]])
assert actual_reference_clearance>0
for z in b.Zones():
    if not z.GetIsRuleArea()and z.GetLayer()in power_fills:
        power_fills[z.GetLayer()].BooleanAdd(z.GetFilledPolysList(z.GetLayer()))
for poly in power_fills.values():poly.Simplify()


def prospective_reference_clear(points,signal_vias):
    # A non-endpoint segment must stay outside the future reference antipad.
    # Endpoint segments still require the unchanged post-refill annulus proof.
    radius=.3+actual_reference_clearance/1e6+.02
    for a,z in zip(points,points[1:]):
        for via in signal_vias:
            if tuple(xy(via))in(tuple(xy(a)),tuple(xy(z))):continue
            actual_corridor=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(.2))
            actual_corridor.BooleanIntersection(circle(tuple(xy(via)),pcbnew.FromMM(radius)))
            if actual_corridor.OutlineCount():return False
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

# A preexisting, exactly qualified endpoint via may have its own antipad.
# Invoke the original strict reference checker rather than require solid
# reference where the actual existing signal barrel physically passes.
actual_endpoint_vias={(v.GetNetname(),tuple(v.GetPosition())) for v in b.GetTracks() if v.Type()==pcbnew.PCB_VIA_T}
existing_endpoint_search_reviews=[]
def literal_existing_endpoint_corridor(a,z,name,layer,width):
    if not any((name,tuple(xy(pt))) in actual_endpoint_vias for pt in (a,z)):
        return False
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(layer);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(width))
    # A new proposed B leg requires a fresh dual-reference via audit;
    # an old F-only cached audit must not stand in for the future In4 side.
    cache=check.audits;check.audits={};check.tracks.append(t)
    try:
        actual=check.segment(t,m['nets'][name])
    except ValueError:
        return False
    finally:
        check.tracks.pop();check.audits=cache
    existing_endpoint_search_reviews.append(dict(start_mm=a,end_mm=z,net=name,layer=b.GetLayerName(layer),actual_reference_check=actual))
    return True

def clear(points,name,layer,width=.2,clearance=.20):
    if not prospective_reference_clear(points,prospective_signal_vias):return False
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
        if not covered(corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.10)),fills[layer]) and not literal_existing_endpoint_corridor(a,z,name,layer,width):return False
    return True

def via_clear(pt,name,diameter,drill):
    radius=diameter/2
    if not .8+radius<pt[0]<459.2-radius or not .8+radius<pt[1]<339.2-radius:return False
    # A signal barrel also removes reference copper. Preserve existing signal
    # corridors in both adjacent reference planes, beyond ordinary Cu DRC.
    # This conservative search screen grants no electrical/reference proof.
    if name!='/LOGIC_GND':
        antipad=radius+actual_reference_clearance/1e6+.02
        for layer,index in geo.tracks.items():
            if layer not in(pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.B_Cu):continue
            for other,a,z,w in index.candidates(pt,pt,antipad+1):
                if other in(name,'/LOGIC_GND','/IO_3V3','/CORE_1V2')or w>.5:continue
                margin=critical_rows.get(other,{}).get('reference_corridor_margin_mm',.1)
                if distance(pt,a,z)<antipad+w/2+margin:return False
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

def escapes_at_uncached(p,row,center):
    name=p.GetNetname();result=[];stages=dict(candidates=0,via_clear=0,front_path=0,reference_circle=0,ground=0)
    # Radius includes exact manifest .60 via, maximum actual pour clearance,
    # .02 discretization allowance, and the full .20 outer return annulus.
    radius=.3+max(actual_reference_clearance for l in(pcbnew.In1_Cu,pcbnew.In4_Cu))/1e6+.02+.20
    for d in(.75,1.,1.25,1.5,2.,2.5,3.):
        for i in range(16):
            pt=(round(center[0]+d*math.cos(i*math.pi/8),6),round(center[1]+d*math.sin(i*math.pi/8),6))
            stages['candidates']+=1
            if not via_clear(pt,name,.6,.3):continue
            if any(math.dist(pt,v)<1.34 for v in prospective_signal_vias):continue
            stages['via_clear']+=1
            front=next((path for path in enhanced_paths(center,pt)if prospective_reference_clear(path,[pt])and sum(math.dist(a,z)for a,z in zip(path,path[1:]))<=4.5 and clear(path,name,pcbnew.F_Cu)),None)
            if front is None:continue
            stages['front_path']+=1
            if not all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(radius)),fill)for fill in fills.values()):continue
            stages['reference_circle']+=1
            ground=ground_at(pt)
            if ground:stages['ground']+=1;result.append(dict(position=pt,ground=ground,front_path_mm=front))
            if len(result)>=8:return result
    print(json.dumps(dict(escape_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),stages=stages)),flush=True)
    return result

escape_cache={}
def escapes_at(p,row,center):
    global fills
    key=(p.m_Uuid.AsString(),tuple(center),len(added))
    if key not in escape_cache:
        previous=fills;fills={}
        local=pcbnew.SHAPE_POLY_SET();local.NewOutline()
        for q in((center[0]-6,center[1]-6),(center[0]+6,center[1]-6),(center[0]+6,center[1]+6),(center[0]-6,center[1]+6)):local.Append(pcbnew.FromMM(q[0]),pcbnew.FromMM(q[1]))
        for layer,poly in full_fills.items():
            clipped=pcbnew.SHAPE_POLY_SET();clipped.Append(poly);clipped.BooleanIntersection(local);clipped.Simplify();fills[layer]=clipped
        try:escape_cache[key]=escapes_at_uncached(p,row,center)
        finally:fills=previous
    return copy.deepcopy(escape_cache[key])

def escapes(p,row,target):
    # Every alternate start is an endpoint of an actual existing F conductor
    # in this literal Source pad's native connected cluster. Final cut and
    # source-pair audits remain independent of this search-only optimization.
    center=mm(p.GetPosition()); cluster={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(p)}
    actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
    anchors={center:None}
    for u in cluster:
        t=actual.get(u)
        if t is None or t.Type()!=pcbnew.PCB_TRACE_T or t.GetLayer()!=pcbnew.F_Cu or t.GetNetname()!=p.GetNetname():continue
        for v in(t.GetStart(),t.GetEnd()):
            q=mm(v)
            if math.dist(center,q)>=.4:anchors.setdefault(q,u)
    result=[]
    # Reuse only actual Source-connected barrels that pass the same exact
    # .60/.30 geometry and full dual-reference/Source-stitch qualification.
    existing_vias=[actual[u] for u in cluster if u in actual and actual[u].Type()==pcbnew.PCB_VIA_T and actual[u].GetNetname()==p.GetNetname()]
    for v in sorted(existing_vias,key=lambda v:math.dist(mm(v.GetPosition()),target))[:8]:
        vp=mm(v.GetPosition());probe=pcbnew.PCB_TRACK(b);probe.SetNet(v.GetNet());probe.SetLayer(pcbnew.B_Cu);probe.SetStart(v.GetPosition());probe.SetEnd(xy((vp[0]+.001,vp[1])));probe.SetWidth(pcbnew.FromMM(.2))
        cache=check.audits;check.audits={};check.tracks.append(probe)
        try:
            audit=check.via(v,row)
            if set(audit['intended_reference_layers'])!={'In1.Cu','In4.Cu'}:continue
        except ValueError:
            continue
        finally:
            check.tracks.pop();check.audits=cache
        stitch=audit['return_stitches'][0];actual_ground=actual[stitch['uuid']]
        result.append(dict(position=vp,ground=dict(existing_uuid=stitch['uuid'],position=mm(actual_ground.GetPosition())),front_path_mm=[vp,vp],existing_signal_via_UUID=v.m_Uuid.AsString(),planned_dual_reference_audit=audit,actual_existing_source_cluster_anchor=dict(source=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),track_UUID=v.m_Uuid.AsString(),position_mm=vp,search_only=True)))
    selected=[center]+[q for q in sorted(anchors,key=lambda q:math.dist(q,target))if q!=center][:8]
    for q in selected:
        for entry in escapes_at(p,row,q):
            entry['actual_existing_source_cluster_anchor']=dict(source=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),track_UUID=anchors[q],position_mm=q,search_only=True)
            if entry['position']not in[e['position']for e in result]:result.append(entry)
        if len(result)>=12:break
    return result

def grid_inner(start,end,name,max_nodes=2800,step=.5):
    # Only a candidate search: all edges use actual native obstacles and
    # Source-owned reference; no new routing permission or tolerance.
    started=time.monotonic();limit=min(140.,1.8*math.dist(start,end)+15.)
    point=lambda k:(round(start[0]+step*k[0],6),round(start[1]+step*k[1],6))
    queue=[(math.dist(start,end),0.,(0,0))];cost={(0,0):0.};previous={};memo={}
    while queue and len(cost)<max_nodes and time.monotonic()-started<12:
        _,travelled,k=heapq.heappop(queue)
        if travelled>cost[k]+1e-8:continue
        at=point(k)
        if .8<=math.dist(at,end)<=1.6 and travelled+math.dist(at,end)<=limit and prospective_reference_clear([at,end],[start,end]) and clear([at,end],name,pcbnew.B_Cu):
            result=[end,at]
            while k!=(0,0):k=previous[k];result.append(point(k))
            result.reverse();simple=[]
            for pt in result:
                if simple and math.dist(simple[-1],pt)<1e-7:continue
                while len(simple)>1:
                    a,z=simple[-2:]
                    if abs((z[0]-a[0])*(pt[1]-z[1])-(z[1]-a[1])*(pt[0]-z[0]))>1e-8:break
                    simple.pop()
                simple.append(pt)
            if prospective_reference_clear(simple,[start,end]) and clear(simple,name,pcbnew.B_Cu):return simple
        scale=2 if k==(0,0)else 1
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            dx*=scale;dy*=scale;nxt=(k[0]+dx,k[1]+dy);dest=point(nxt);new=travelled+step*math.hypot(dx,dy)
            if new+math.dist(dest,end)>limit or new>=cost.get(nxt,float('inf'))-1e-8:continue
            if not(bounds[0]<=dest[0]<=bounds[2]and bounds[1]<=dest[1]<=bounds[3]):continue
            key=tuple(sorted((k,nxt)))
            if key not in memo:memo[key]=prospective_reference_clear([at,dest],[start,end]) and clear([at,dest],name,pcbnew.B_Cu)
            if not memo[key]:continue
            cost[nxt]=new;previous[nxt]=k;heapq.heappush(queue,(new+math.dist(dest,end),new,nxt))
    return None

def add_segment(a,z,name,layer):
    if math.dist(a,z)<1e-6:return None
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(layer);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

def add_via(pt,name,diameter,drill):
    t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(name));t.SetPosition(xy(pt));t.SetWidth(pcbnew.FromMM(diameter));t.SetDrill(pcbnew.FromMM(drill));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetIsFree(True);t.SetRemoveUnconnected(False);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

jobs=[]
for name,row in m['nets'].items():
    if 'B.Cu' not in row['layers'] or row['reference_layers'].get('B.Cu')!='In4.Cu':continue
    if row['via_diameter_mm']!=.6 or row['via_drill_mm']!=.3:raise ValueError('Unexpected literal ordinary via rule')
    candidates=[p for p in ps.values()if p.GetNetname()==name and p.IsOnLayer(pcbnew.F_Cu)and p.GetParentFootprint().GetReference()!='U1001']
    for p,q in itertools.combinations(candidates,2):
        length=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
        pair={p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()}
        if 0<length<=45:
            jobs.append((length,name,p,q))
search_started=time.monotonic()
known_pairs={frozenset(v)for v in [['U13001.12','R8207.1'],['R13007.1','U19022.4'],['U13001.19','U8005.5']]}
for length,name,p,q in sorted(jobs,key=lambda x:x[0]):
    if name not in {'/mc_permission/OUT_PERMIT','/motherboard_status/STATUS_HW_GOOD'}:continue
    if time.monotonic()-search_started>600:break
    if frozenset([p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()])in known_pairs:continue
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
    row=m['nets'][name];starts=escapes(p,row,end);ends=escapes(q,row,start);chosen=None;grid_tries=0
    for a,z in sorted(itertools.product(starts,ends),key=lambda az:math.dist(az[0]['position'],az[1]['position'])):
        av,zv=a['position'],z['position']
        if math.dist(av,zv)<1.1:continue
        # Candidate vias/grounds are not in the cached index yet. Check all
        # same-group holes/copper against one another before committing.
        points=[(av,name,.6,.3),(zv,name,.6,.3)]
        for entry in(a,z):
            if 'new_position'in entry['ground']:points.append((entry['ground']['new_position'],'/LOGIC_GND',.5,.2))
        if any(math.dist(x[0],y[0])<max(x[3]/2+y[3]/2+.25,(x[2]+y[2])/2+.205 if x[1]!=y[1]else 0)-1e-6 for x,y in itertools.combinations(points,2)):continue
        path=next((line for line in enhanced_paths(av,zv)if prospective_reference_clear(line,[av,zv])and sum(math.dist(s,t)for s,t in zip(line,line[1:]))<=140 and clear(line,name,pcbnew.B_Cu)),None)
        if path is None and grid_tries<3:
            grid_tries+=1;path=grid_inner(av,zv,name)
        if path is None:continue
        all_segments=[(s,t,pcbnew.F_Cu)for entry in(a,z)for s,t in zip(entry['front_path_mm'],entry['front_path_mm'][1:])]+[(s,t,pcbnew.B_Cu)for s,t in zip(path,path[1:])]
        if not all(prospective_reference_clear([s,t],[av,zv])for s,t,l in all_segments):continue
        if any(distance(gpt,s,t)<diam/2+.1+.20-1e-6 for gpt,gnet,diam,drill in points if gnet=='/LOGIC_GND'for s,t,l in all_segments):continue
        chosen=(a,z,path);break
    if chosen is None:
        blocked.append(dict(net=name,source_pair=pair,span_mm=length,start_choices=len(starts),end_choices=len(ends),reason='No conservative finite two-surface handoff/path'))
        print(json.dumps(blocked[-1]),flush=True);continue
    a,z,path=chosen;signal=[];grounds=[]
    for pad,entry in((p,a),(q,z)):
        signal.extend(add_segment(s,t,name,pcbnew.F_Cu)for s,t in zip(entry['front_path_mm'],entry['front_path_mm'][1:]))
        if 'existing_signal_via_UUID'not in entry:signal.append(add_via(entry['position'],name,.6,.3))
        if 'new_position'in entry['ground']:grounds.append(add_via(entry['ground']['new_position'],'/LOGIC_GND',.5,.2))
    signal.extend(add_segment(s,t,name,pcbnew.B_Cu)for s,t in zip(path,path[1:]))
    groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],signal_UUIDs=[u for u in signal if u],ground_UUIDs=grounds,new_copper_UUIDs=[u for u in signal if u]+grounds,start=a,end=z,back_path_mm=path))
    print(json.dumps(dict(added_pair=pair,net=name,newCu=len(groups[-1]['new_copper_UUIDs']))),flush=True)
    prospective_signal_vias.extend([a['position'],z['position']])
    if len(groups)>=8:break

dest=OUT/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'
pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
    if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
    elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'proposed-groups.json',dict(input_sha256=frozen,base_sha256=e.sha(BASE),groups=groups,blocked=blocked,new_copper_UUIDs=[t.m_Uuid.AsString()for t in added],actual_signal_layers=["F.Cu","B.Cu"],actual_common_reference=None,actual_transfer_references=["In1.Cu","In4.Cu"],all_existing_B_fills_preserved_as_actual_native_obstacles=True,IO3_1mm_backbone_and22_receiving_feed_preservation_pending=True,exact_native_fill_subset_clipping_search_only=True,actual_existing_endpoint_antipad_search_reviews=existing_endpoint_search_reviews,native_refill_DRC_full_return_and_SOURCE_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
