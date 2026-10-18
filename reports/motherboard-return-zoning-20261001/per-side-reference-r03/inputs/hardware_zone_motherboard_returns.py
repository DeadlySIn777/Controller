"""Add position-derived reference-plane polygons without replacing old copper.

Run with KiCad Python. This bounded prototype adds In1/In4 return polygons,
package barrier rule areas and exclusions beneath foreign domains. It retains
all old native objects, including zone definitions; their generated fills may
acquire necessary holes. No power-current capacity, finished stackup, safety
rating or complete signal routing follows from a plane-fill DRC result.
"""
from __future__ import annotations
import argparse
from array import array
import collections
import copy
import heapq
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import pcbnew

from hardware_build_assembly import parse,dump,children,child,value
from hardware_map_motherboard_domains import ROOT,SEEDS,RAW_RETURNS,sha,write
from hardware_route_selected_additive import immutable_objects,zone_definitions,corridor_polygon
from hardware_route_logic_return import identity

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
RAW_POWER={'/motherboard_comms/RS485_ISO_3V3_RAW':'/motherboard_comms/RS485_ISO_RETURN_RAW',
           '/motherboard_comms/CAN_ISO_5V_RAW':'/motherboard_comms/CAN_ISO_RETURN_RAW'}
LEGACY_SOURCE=ROOT/'reports/board-completion-20260930/local-signal-routing-v2/local-signal-routes-candidate.kicad_pcb'
LEGACY_ZONES={
    'c455b03f-4ee9-4ec3-b5ce-579d280664f2':('/LOGIC_GND','B.Cu'),
    '8f98a894-54ef-4ab0-8e2d-d91083a63719':('/LOGIC_GND','In1.Cu'),
    '2ad20bf7-6696-4e08-85d3-1f2d4c3caa40':('/IO_3V3','In2.Cu'),
    '9e763b2e-ae74-4ccb-9f62-ff551c9f1868':('/CORE_1V2','In3.Cu'),
    'feae3ab1-a47e-47c4-b3f6-00780881d2dc':('/LOGIC_GND','In4.Cu')}


def polygon(points):
    out=pcbnew.SHAPE_POLY_SET();out.NewOutline()
    for x,y in points:out.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
    return out


def dump_board(tree):
    #A real whole-board polygon expansion can exceed KiCad's text-line buffer
    #when the generic schematic dumper emits one17+MB line. Top-level newline
    #separation preserves the exact parsed native objects and avoids that
    #parser failure; no electrical/geometry simplification is performed.
    return '('+tree[0]+'\n'+'\n'.join(dump(n)if isinstance(n,list)else n for n in tree[1:])+')\n'


def rectangle(bounds,margin=0):
    a,b,c,d=bounds
    return polygon([(a-margin,b-margin),(c+margin,b-margin),(c+margin,d+margin),(a-margin,d+margin)])


def duplicate(poly):
    out=pcbnew.SHAPE_POLY_SET();out.Append(poly);return out


def inflation(poly,margin):
    out=duplicate(poly)
    out.Inflate(pcbnew.FromMM(margin),pcbnew.CORNER_STRATEGY_CHAMFER_ALL_CORNERS,pcbnew.FromMM(.01))
    return out


def return_net(pad):
    domain=pad['domain'];net=pad['net']
    if domain not in SEEDS or domain=='CHASSIS':return None
    if net in RAW_RETURNS:return net
    if net in RAW_POWER:return RAW_POWER[net]
    return SEEDS[domain]


def reference_envelopes(mapping,reference_layer=None):
    groups=collections.defaultdict(list)
    for pad in mapping['pads']:
        if reference_layer is not None and not pad_supports_reference(pad,reference_layer):continue
        net=return_net(pad)
        if net:groups[pad['reference'],net].append(pad)
    result=[]
    for (ref,net),pads in groups.items():
        result.append(dict(reference=ref,net=net,pins=sorted({p['pin'] for p in pads}),
            bounds=[min(p['copper_aabb_mm'][0] for p in pads),min(p['copper_aabb_mm'][1] for p in pads),
                    max(p['copper_aabb_mm'][2] for p in pads),max(p['copper_aabb_mm'][3] for p in pads)]))
    return result


def pad_supports_reference(pad,layer):
    """Use the actual copper side, never a mirrored all-component envelope."""
    allowed={'In1.Cu':{'F.Cu','In1.Cu','In2.Cu'},'In4.Cu':{'B.Cu','In3.Cu','In4.Cu'}}
    if layer not in allowed:raise ValueError('Unreviewed adjacent reference layer')
    return bool(set(pad['copper_layers']) & allowed[layer])


def track_supports_reference(board,track,layer):
    if isinstance(track,pcbnew.PCB_VIA):return track.IsOnLayer(board.GetLayerID(layer))
    allowed={'In1.Cu':{'F.Cu','In1.Cu','In2.Cu'},'In4.Cu':{'B.Cu','In3.Cu','In4.Cu'}}
    return board.GetLayerName(track.GetLayer()) in allowed[layer]


def build_side_polygons(mapping,board,reference_layer):
    """Exact source/native per-side fields and adjacent reference resources.

    Raw ISOW secondary loops intentionally receive no global pour. Actual
    adopted all-Cu raw-loop and isolation rule areas remain authoritative.
    Floating SUB islands are not grounds and receive independent exclusions.
    """
    seed=collections.defaultdict(pcbnew.SHAPE_POLY_SET)
    for row in reference_envelopes(mapping,reference_layer):
        if row['net'] not in RAW_RETURNS:seed[row['net']].Append(rectangle(row['bounds'],.6))
    domains={p['net']:p['domain'] for p in mapping['pads']}
    for t in board.GetTracks():
        if not track_supports_reference(board,t,reference_layer):continue
        net=return_net(dict(domain=domains.get(t.GetNetname()),net=t.GetNetname()))
        if not net or net in RAW_RETURNS:continue
        if isinstance(t,pcbnew.PCB_VIA):
            seed[net].Append(corridor_polygon(tuple(t.GetPosition()),tuple(t.GetPosition()),t.GetWidth(pcbnew.F_Cu)/2+pcbnew.FromMM(.4)))
        elif isinstance(t,pcbnew.PCB_TRACK):
            seed[net].Append(corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4)))
        else:raise ValueError('Unreviewed retained arc in actual side reference map')
    for p in seed.values():p.Simplify()
    barriers=pcbnew.SHAPE_POLY_SET()
    for row in mapping['barriers']:barriers.Append(functional_barrier(row))
    barriers.Simplify();ungrounded=pcbnew.SHAPE_POLY_SET()
    for pad in mapping['pads']:
        if not pad_supports_reference(pad,reference_layer):continue
        if pad['domain'].startswith(('SUB:','CONTACT:')) or pad['domain']=='CHASSIS':
            ungrounded.Append(rectangle(pad['copper_aabb_mm'],.3))
    #Actual floating thermal zones reserve their extent on both inner layers
    #because the SUB stitch passes through them. This is never a GND pour.
    for z in board.Zones():
        if z.GetZoneName().startswith('FLOATING_SUB_'):ungrounded.Append(inflation(z.Outline(),.25))
        if z.GetIsRuleArea() and z.IsOnLayer(board.GetLayerID(reference_layer)):
            if z.GetDoNotAllowZoneFills():ungrounded.Append(duplicate(z.Outline()))
    ungrounded.Simplify();regions={}
    for net,poly in seed.items():
        if net=='/LOGIC_GND':continue
        obstacles=duplicate(barriers);obstacles.Append(ungrounded)
        for other,p in seed.items():
            if other!=net:obstacles.Append(inflation(p,.25))
        obstacles.Simplify();candidate=duplicate(poly);candidate.BooleanSubtract(obstacles);regions[net]=candidate
    return regions,barriers,ungrounded


def remaining_logic(regions,barriers,ungrounded):
    exclusion=duplicate(barriers);exclusion.Append(ungrounded)
    for net,p in regions.items():
        if net!='/LOGIC_GND':exclusion.Append(inflation(p,.25))
    exclusion.Simplify();logic=rectangle([.5,.5,459.5,339.5]);logic.BooleanSubtract(exclusion)
    return logic


def reconcile_legacy_zone_outlines(board,sides):
    """Subtract only foreign-domain geometry from the five exact old planes.

    A global keepout would also delete rightful field ground fills. This
    bounded change keeps each old UUID/net/rule, changes only its polygon,
    and creates same-rule extra fragments only if the subtraction splits it.
    The original327-copper source is the independent five-zone authority.
    """
    baseline=pcbnew.LoadBoard(str(LEGACY_SOURCE));expected={z.m_Uuid.AsString():z for z in baseline.Zones()}
    actual={z.m_Uuid.AsString():z for z in board.Zones()};ledger=[];newids=[]
    if set(expected)!=set(LEGACY_ZONES):raise ValueError('Five-zone original-source inventory changed')
    for uid,(net,layer)in LEGACY_ZONES.items():
        old=expected[uid];z=actual[uid]
        if z.GetNetname()!=net or board.GetLayerName(z.GetLayer())!=layer:
            raise ValueError('Exact old zone net/layer differs '+uid)
        difference=duplicate(z.Outline());difference.BooleanSubtract(old.Outline())
        reverse=duplicate(old.Outline());reverse.BooleanSubtract(z.Outline())
        if difference.Area()or reverse.Area():raise ValueError('Inherited five-zone outline differs from frozen source '+uid)
        reference='In1.Cu'if layer in ['F.Cu','In1.Cu','In2.Cu']else'In4.Cu'
        side=sides[reference];cut=duplicate(side['barriers']);cut.Append(side['ungrounded'])
        for other,p in side['regions'].items():
            if other!='/LOGIC_GND':cut.Append(inflation(p,.25))
        cut.Simplify();polygon=duplicate(z.Outline());before_area=polygon.Area()/1e12;polygon.BooleanSubtract(cut)
        sections=sorted(split_polygons(polygon),key=lambda p:p.Area(),reverse=True)
        if not sections:raise ValueError('A required legacy plane was entirely removed '+uid)
        z.Outline().RemoveAllContours();z.Outline().Append(sections[0]);extras=[]
        for p in sections[1:]:
            fragment=z.Duplicate();fragment.Outline().RemoveAllContours();fragment.Outline().Append(p)
            if fragment.m_Uuid.AsString()==uid:fragment.m_Uuid=pcbnew.KIID()
            board.Add(fragment);extras.append(fragment.m_Uuid.AsString());newids.append(fragment.m_Uuid.AsString())
        ledger.append(dict(uuid=uid,net=net,layer=layer,changed_keys=['polygon'],
            before_outline_area_mm2=before_area,after_combined_outline_area_mm2=sum(p.Area()for p in sections)/1e12,
            same_rule_extra_fragment_UUIDs=extras,frozen_original_source=str(LEGACY_SOURCE),frozen_original_source_sha256=sha(LEGACY_SOURCE)))
    return ledger,newids


def build_polygons(mapping,board=None):
    """Local same-reference islands plus a continuous remaining logic region.

    Multiple local field outlines remain explicit until legal spanning return
    corridors are added and native connectivity proves them joined. The
    current function cannot silently claim such fragments are continuous.
    """
    seed=collections.defaultdict(pcbnew.SHAPE_POLY_SET)
    for row in reference_envelopes(mapping):seed[row['net']].Append(rectangle(row['bounds'],.6))
    if board is not None:
        domains={p['net']:p['domain'] for p in mapping['pads']}
        for track in board.GetTracks():
            name=return_net(dict(domain=domains.get(track.GetNetname()),net=track.GetNetname()))
            if not name:continue
            if isinstance(track,pcbnew.PCB_VIA):
                radius=track.GetWidth(pcbnew.F_Cu)/2+pcbnew.FromMM(.4)
                seed[name].Append(corridor_polygon(tuple(track.GetPosition()),tuple(track.GetPosition()),radius))
            elif isinstance(track,pcbnew.PCB_TRACK):
                seed[name].Append(corridor_polygon(tuple(track.GetStart()),tuple(track.GetEnd()),track.GetWidth()/2+pcbnew.FromMM(.4)))
            else:raise ValueError('Unreviewed retained arc in reference envelope')
    for poly in seed.values():poly.Simplify()
    barriers=pcbnew.SHAPE_POLY_SET()
    for row in mapping['barriers']:barriers.Append(functional_barrier(row))
    barriers.Simplify()
    ungrounded=pcbnew.SHAPE_POLY_SET()
    for row in mapping['reference_seed_envelopes']:
        if row['domain'].startswith(('SUB:','CONTACT:')) or row['domain']=='CHASSIS':
            ungrounded.Append(rectangle(row['copper_aabb_mm'],.3))
    ungrounded.Simplify()
    all_foreign=pcbnew.SHAPE_POLY_SET()
    for name,poly in seed.items():
        if name!='/LOGIC_GND':all_foreign.Append(poly)
    all_foreign.Simplify()
    regions={}
    for name,poly in seed.items():
        if name=='/LOGIC_GND':continue
        obstacles=duplicate(barriers);obstacles.Append(ungrounded)
        for other,region in seed.items():
            if other!=name:obstacles.Append(inflation(region,.25))
        obstacles.Simplify();candidate=duplicate(poly);candidate.BooleanSubtract(obstacles)
        regions[name]=candidate
    logic=rectangle([.5,.5,459.5,339.5])
    exclusions=inflation(all_foreign,.25);exclusions.Append(barriers);exclusions.Append(ungrounded);exclusions.Simplify()
    logic.BooleanSubtract(exclusions);regions['/LOGIC_GND']=logic
    # Foreign-only pour exclusions on the former power/surface plane layers
    # retain old definitions yet prevent old logic/IO3/core fill beneath fields.
    old_layer_exclusions=inflation(all_foreign,.25);old_layer_exclusions.Append(ungrounded);old_layer_exclusions.Simplify()
    return regions,barriers,ungrounded,old_layer_exclusions


def functional_barrier(row,width=.6):
    """An explicit SELV copper boundary, separate from the package kV rating.

    Same-domain PhotoMOS use needs no artificial galvanic boundary; its real
    contact/LED nets still have ordinary native spacing. Different reference
    sides receive a central .6 mm prototype no-copper strip. Existing pieces
    entering it are reviewed/corrected separately, not silently excused.
    """
    left=set(row['side_domains'][0]);right=set(row['side_domains'][1])
    if len(left)==len(right)==1 and left==right:return pcbnew.SHAPE_POLY_SET()
    ax,ay=row['package_axis'];cx,cy=row['cross_axis']
    points=row['polygon_mm'];a=[x*ax+y*ay for x,y in points];b=[x*cx+y*cy for x,y in points]
    middle=(min(a)+max(a))/2
    return polygon([(u*ax+v*cx,u*ay+v*cy) for u,v in
                    [(middle-width/2,min(b)),(middle+width/2,min(b)),(middle+width/2,max(b)),(middle-width/2,max(b))]])


def split_polygons(poly):
    # Native KiCad serializes one zone outline. Multiple disconnected
    # SHAPE_POLY_SET outlines appended to one ZONE lose all but outline 0.
    for index in range(poly.OutlineCount()):
        out=pcbnew.SHAPE_POLY_SET();out.AddPolygon(poly.CPolygon(index));yield out


def raster_box(grid,width,height,bounds,margin,step=.5):
    a,b,c,d=bounds
    x0=max(0,math.floor((a-margin)/step));x1=min(width-1,math.ceil((c+margin)/step))
    y0=max(0,math.floor((b-margin)/step));y1=min(height-1,math.ceil((d+margin)/step))
    fill=bytes([1])*(x1-x0+1)
    for y in range(y0,y1+1):grid[y*width+x0:y*width+x1+1]=fill


def outline_point(poly,index,grid,width,height,step=.5,labels=None,label_sizes=None):
    # A candidate must enter this exact fragment, including its holes. Testing
    # the whole multi-outline polygon could accidentally enter a neighbouring
    # fragment and falsely report an unreachable island as joined.
    piece=pcbnew.SHAPE_POLY_SET();piece.AddPolygon(poly.CPolygon(index))
    chain=poly.COutline(index)
    candidates=[]
    for i in range(chain.PointCount()):
        point=chain.CPoint(i);x=round(pcbnew.ToMM(point.x)/step);y=round(pcbnew.ToMM(point.y)/step)
        for radius in range(7):
            for dx in range(-radius,radius+1):
                for dy in range(-radius,radius+1):
                    nx,ny=x+dx,y+dy
                    if 0<=nx<width and 0<=ny<height and not grid[ny*width+nx]:
                        q=pcbnew.VECTOR2I(pcbnew.FromMM(nx*step),pcbnew.FromMM(ny*step))
                        if piece.Contains(q):
                            if labels is None:return nx,ny
                            label=labels[ny*width+nx]
                            candidates.append((label_sizes.get(label,0),nx,ny))
    #A first-corner choice may lie in a tiny dead-end enclosed by unrelated
    #component projections. Select a real entry in the largest physically
    #connected free region rather than falsely declaring the whole island
    #inaccessible. Every candidate is still inside this exact polygon.
    if candidates:
        _,x,y=max(candidates);return x,y
    return None


def grid_path(start,goal,blocked,width,height,maximum_visited=100000):
    """A bounded plane-corridor search, not signal or high-current autorouting."""
    if len(blocked)!=width*height:raise ValueError('Grid dimensions do not match')
    if any(not(0<=p[0]<width and 0<=p[1]<height) for p in [start,goal]):return None
    initial=start[1]*width+start[0];target=goal[1]*width+goal[0]
    if blocked[initial] or blocked[target]:return None
    queue=[(abs(start[0]-goal[0])+abs(start[1]-goal[1]),0,initial)];cost={initial:0};parents={}
    while queue:
        if len(cost)>maximum_visited:return None
        _,g,n=heapq.heappop(queue)
        if cost.get(n)!=g:continue
        if n==target:
            result=[n]
            while n!=initial:n=parents[n];result.append(n)
            return [(n%width,n//width) for n in reversed(result)]
        x,y=n%width,n//width
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny=x+dx,y+dy
            if not (0<=nx<width and 0<=ny<height):continue
            nxt=ny*width+nx
            if blocked[nxt] or g+1>=cost.get(nxt,10**20):continue
            cost[nxt]=g+1;parents[nxt]=n
            heapq.heappush(queue,(g+1+abs(nx-goal[0])+abs(ny-goal[1]),g+1,nxt))
    return None


def connected_grid_labels(blocked,width,height):
    """Prove unreachable pieces once instead of repeating an exhaustive A*."""
    labels=array('i',[0])*len(blocked);label=0
    for initial in range(len(blocked)):
        if blocked[initial] or labels[initial]:continue
        label+=1;labels[initial]=label;queue=collections.deque([initial])
        while queue:
            n=queue.popleft();x=n%width
            for nxt in [n-width if n>=width else -1,n+width if n+width<len(blocked)else -1,
                        n-1 if x else -1,n+1 if x+1<width else -1]:
                if nxt>=0 and not blocked[nxt] and not labels[nxt]:labels[nxt]=label;queue.append(nxt)
    return labels,label


def spanning_regions(mapping,regions,reference_layer=None,additional_obstacles=None):
    """Connect legal field reference pieces through otherwise empty PCB area.

    All other component sides, substrates, chassis/contact groups and actual
    package boundaries are obstacles. Main/raw comm references cannot bypass
    their ferrites. Returned failures are exact unclosed geometry, not a
    disconnected polygon disguised as a continuous plane.
    """
    envelopes=reference_envelopes(mapping,reference_layer);width,height=921,681;step=.5
    occupied=[];result=dict(regions);receipts=[]
    names=sorted((n for n in regions if n!='/LOGIC_GND'),key=lambda n:regions[n].Area())
    for name in names:
        poly=duplicate(regions[name]);count=poly.OutlineCount()
        grid=bytearray(width*height)
        for row in envelopes:
            if row['net']!=name:raster_box(grid,width,height,row['bounds'],.9)
        for row in mapping['reference_seed_envelopes']:
            if row['domain'].startswith(('SUB:','CONTACT:')) or row['domain']=='CHASSIS':
                raster_box(grid,width,height,row['copper_aabb_mm'],.6)
        if additional_obstacles is not None:
            #Conservative per-outline boxes preserve actual thermal/EMI
            #exclusions; the route may not borrow a different fragment.
            for piece in split_polygons(additional_obstacles):
                box=piece.BBox();raster_box(grid,width,height,[pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),
                    pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())],.5)
        for row in mapping['barriers']:
            barrier=functional_barrier(row)
            if barrier.OutlineCount():
                box=barrier.BBox();raster_box(grid,width,height,
                    [pcbnew.ToMM(box.GetX()),pcbnew.ToMM(box.GetY()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())],.5)
        for path in occupied:
            for a,b in zip(path,path[1:]):raster_box(grid,width,height,[min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])],.9)
        # A one-cell perimeter remains clear of Edge.Cuts.
        raster_box(grid,width,height,[0,0,460,.5],0);raster_box(grid,width,height,[0,339.5,460,340],0)
        raster_box(grid,width,height,[0,0,.5,340],0);raster_box(grid,width,height,[459.5,0,460,340],0)
        labels,free_components=connected_grid_labels(grid,width,height)
        label_sizes=collections.Counter(labels)
        points={i:outline_point(poly,i,grid,width,height,labels=labels,label_sizes=label_sizes) for i in range(count)}
        failed=[];paths=[];available={i:p for i,p in points.items() if p is not None}
        failed.extend(dict(outline=i,reason='no unblocked conservative corridor entry') for i,p in points.items() if p is None)
        if available:
            first=max(available,key=lambda i:label_sizes[labels[available[i][1]*width+available[i][0]]])
            connected={first};pending=set(available)-connected
            while pending:
                distance,start,end=min((abs(available[a][0]-available[b][0])+abs(available[a][1]-available[b][1]),a,b)
                    for a in connected for b in pending)
                s,e=available[start],available[end]
                same_free_component=labels[s[1]*width+s[0]]==labels[e[1]*width+e[0]]
                path=grid_path(s,e,grid,width,height) if same_free_component else None
                if path:
                    # Compress collinear runs before generating native polygons.
                    compact=[path[0]]
                    for a,b,c in zip(path,path[1:],path[2:]):
                        if (b[0]-a[0],b[1]-a[1])!=(c[0]-b[0],c[1]-b[1]):compact.append(b)
                    compact.append(path[-1]);metric=[(x*step,y*step) for x,y in compact]
                    for a,b in zip(metric,metric[1:]):
                        poly.Append(corridor_polygon(tuple(pcbnew.FromMM(v) for v in a),tuple(pcbnew.FromMM(v) for v in b),pcbnew.FromMM(.35)))
                    paths.append(metric);connected.add(end)
                else:failed.append(dict(outline=end,reason='no conservative empty-area corridor to connected reference tree'))
                pending.remove(end)
        poly.Simplify();result[name]=poly;occupied.extend(paths)
        receipts.append(dict(net=name,original_disconnected_outline_count=count,
            resulting_outline_count=poly.OutlineCount(),native_reference_corridors_mm=paths,
            corridor_width_mm=.7,high_current_capacity_claim=False,failed_outlines=failed,
            free_space_connected_components=free_components,search_node_budget=100000))
        print(json.dumps(dict(net=name,original_outlines=count,resulting_outlines=poly.OutlineCount(),failed_outlines=len(failed))),flush=True)
    return result,receipts


def add_zone(board,net,poly,layer,priority,name):
    if not poly.OutlineCount():return None
    zone=pcbnew.ZONE(board);zone.SetLayer(layer);zone.SetNet(board.FindNet(net))
    zone.SetAssignedPriority(priority);zone.SetZoneName(name)
    zone.SetLocalClearance(pcbnew.FromMM(.25));zone.SetMinThickness(pcbnew.FromMM(.2))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    #Unanchored generated islands are not electrical return resources. Keep
    #required unrouted source pads visible; do not retain meaningless floating
    #fill or hide the missing actual local ground route behind its net name.
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.Outline().Append(poly);board.Add(zone);return zone


def spanning_complete(receipts):
    """No disconnected native polygon can earn a continuous-reference claim."""
    return all(not row['failed_outlines'] and row['resulting_outline_count']==1
               for row in receipts)


def add_keepout(board,poly,layers,name,tracks=False,vias=False):
    if not poly.OutlineCount():return None
    zone=pcbnew.ZONE(board);mask=pcbnew.LSET()
    for layer in layers:mask.AddLayer(layer)
    zone.SetLayerSet(mask);zone.SetIsRuleArea(True);zone.SetZoneName(name)
    zone.SetDoNotAllowZoneFills(True);zone.SetDoNotAllowTracks(tracks);zone.SetDoNotAllowVias(vias)
    zone.SetDoNotAllowPads(False);zone.SetDoNotAllowFootprints(False)
    zone.Outline().Append(poly);board.Add(zone);return zone


def filled_return_coverage(board,mapping):
    fills={};rows=[]
    for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
        for zone in board.Zones():
            if zone.GetIsRuleArea() or not zone.IsOnLayer(layer) or not zone.HasFilledPolysForLayer(layer):continue
            key=zone.GetNetname(),layer
            fills.setdefault(key,pcbnew.SHAPE_POLY_SET()).Append(zone.GetFilledPolysList(layer))
    for fill in fills.values():fill.Simplify()
    for pad in mapping['pads']:
        net=return_net(pad)
        if not net:continue
        p=pcbnew.VECTOR2I(pcbnew.FromMM(pad['position_mm'][0]),pcbnew.FromMM(pad['position_mm'][1]))
        for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
            if not pad_supports_reference(pad,board.GetLayerName(layer)):continue
            actual=fills.get((net,layer))
            # Copper antipads under through-hole signal contacts are expected;
            # this report is explicit projection, not an electrical pad join.
            rows.append(dict(reference=pad['reference'],pin=pad['pin'],pad_uuid=pad['uuid'],
                reference_net=net,layer=board.GetLayerName(layer),
                projected_pad_center_has_own_reference=bool(actual and actual.Contains(p)),
                through_hole_projection_antipad_expected=len(pad['copper_layers'])>1))
    continuity=[]
    for (net,layer),fill in fills.items():
        continuity.append(dict(net=net,layer=board.GetLayerName(layer),
            filled_connected_outline_count=fill.OutlineCount(),filled_area_mm2=fill.Area()/1e12,
            single_continuous_reference=fill.OutlineCount()==1))
    return dict(pad_projection_rows=rows,filled_reference_regions=continuity,
        all_pad_projection_requirement_qualified=False,
        note='Projection only; native zone copper connectivity and legal local stitching remain distinct from this geometric necessary condition. Through-hole signal antipads cannot be interpreted as an error or as adequate return proof.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--map',type=Path,required=True);p.add_argument('--board',type=Path,required=True)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--correct-legacy-five-zone-outlines',action='store_true',
        help='Reviewed net-aware correction of only the frozen five original zone polygons')
    a=p.parse_args();base=a.board.resolve();out=a.out.resolve();source=a.source.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'reports'):raise ValueError('New immutable report directory required')
    mapping=json.loads(a.map.read_text(encoding='utf-8'))
    if mapping['input_sha256'].get(str(base))!=sha(base):raise ValueError('Domain map does not describe this exact board')
    for name in ['design.json','netlist.xml','assembly-map.json']:
        if mapping['input_sha256'].get(str(source/name))!=sha(source/name):raise ValueError('Source hash differs '+name)
    if not mapping['source_physical_population_complete'] or mapping['errors']:raise ValueError('Source population/net mapping is incomplete')
    out.mkdir(parents=True)
    inputs=out/'inputs';inputs.mkdir()
    for file in [base,a.map.resolve(),source/'design.json',source/'netlist.xml',source/'assembly-map.json',Path(__file__)]:
        shutil.copy2(file,inputs/file.name)
    candidate=out/'motherboard-return-zones-candidate.kicad_pcb'
    for suffix in ['.kicad_pro','.kicad_dru']:
        shutil.copy2(base.with_suffix(suffix),candidate.with_suffix(suffix))
    for file in base.parent.iterdir():
        if file.is_dir() and (file.name.endswith('.pretty') or file.name=='3dmodels'):shutil.copytree(file,out/file.name)
    if (base.parent/'fp-lib-table').exists():shutil.copy2(base.parent/'fp-lib-table',out/'fp-lib-table')
    files=[base,a.map.resolve(),source/'design.json',source/'netlist.xml',source/'assembly-map.json',base.with_suffix('.kicad_pro'),base.with_suffix('.kicad_dru')]
    if a.correct_legacy_five_zone_outlines:
        files.append(LEGACY_SOURCE);shutil.copy2(LEGACY_SOURCE,inputs/'original-five-zone-source.kicad_pcb')
    hashes={str(v):sha(v) for v in files}
    tree=parse(base.read_text(encoding='utf-8'));before=immutable_objects(tree)
    board=pcbnew.LoadBoard(str(base));old_copper={t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}
    oldzones={z.m_Uuid.AsString() for z in board.Zones()}
    if a.correct_legacy_five_zone_outlines:
        from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
        old_clusters=native_pad_clusters(board,{net for net,layer in LEGACY_ZONES.values()})
    sides={};spanning=[]
    for layer in ['In1.Cu','In4.Cu']:
        regions,barriers,ungrounded=build_side_polygons(mapping,board,layer)
        regions,receipts=spanning_regions(mapping,regions,layer,ungrounded)
        for row in receipts:row['reference_layer']=layer
        spanning.extend(receipts);regions['/LOGIC_GND']=remaining_logic(regions,barriers,ungrounded)
        sides[layer]=dict(regions=regions,barriers=barriers,ungrounded=ungrounded)
    all_layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]
    old_zone_names={z.GetZoneName()for z in board.Zones()}
    for row in mapping['barriers']:
        name='ISO_FUNCTIONAL_BOUNDARY_'+row['reference']
        if name not in old_zone_names:add_keepout(board,functional_barrier(row),all_layers,name,tracks=True,vias=True)
    for layer,side in sides.items():
        for net,poly in side['regions'].items():
            for index,section in enumerate(split_polygons(poly)):
                add_zone(board,net,section,board.GetLayerID(layer),10 if net=='/LOGIC_GND' else 20,'REFERENCE_'+net.replace('/','_')+'_'+layer+'_'+str(index))
    legacy_ledger=[]
    if a.correct_legacy_five_zone_outlines:legacy_ledger,_=reconcile_legacy_zone_outlines(board,sides)
    temporary=out/'zone-donor.kicad_pcb';pcbnew.SaveBoard(str(temporary),board)
    donor=parse(temporary.read_text(encoding='utf-8'))
    additions=[z for z in children(donor,'zone') if value(child(z,'uuid')[1]) not in oldzones]
    final=copy.deepcopy(tree);final.extend(copy.deepcopy(additions));candidate.write_text(dump_board(final),encoding='utf-8')
    if legacy_ledger:
        changed={r['uuid']for r in legacy_ledger};replace={value(child(z,'uuid')[1]):z for z in children(donor,'zone')if value(child(z,'uuid')[1])in changed}
        for i,n in enumerate(final):
            if isinstance(n,list)and n and n[0]=='zone'and value(child(n,'uuid')[1])in changed:
                final[i]=copy.deepcopy(replace[value(child(n,'uuid')[1])])
        candidate.write_text(dump_board(final),encoding='utf-8')
    if immutable_objects(final)[0]!=before[0] or immutable_objects(final)[2]!=before[2]:raise ValueError('Zone addition altered old native objects')
    if any(zone_definitions(final).get(k)!=v for k,v in before[1].items()if k not in {r['uuid']for r in legacy_ledger}):raise ValueError('Unreviewed old zone definition changed')
    cmd=[str(CLI),'pcb','drc','--all-track-errors','--severity-all','--refill-zones','--save-board','--format','json','-o',str(out/'drc.json'),str(candidate)]
    (out/'drc-command.json').write_text(json.dumps(cmd,indent=2)+'\n')
    run=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    (out/'drc-command.txt').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
    drc=json.loads((out/'drc.json').read_text(encoding='utf-8'))
    board=pcbnew.LoadBoard(str(candidate));board.BuildConnectivity()
    if {t.m_Uuid.AsString():identity(t) for t in board.GetTracks()}!=old_copper:raise ValueError('Retained copper changed')
    after=immutable_objects(parse(candidate.read_text(encoding='utf-8')))
    if after[0]!=before[0] or after[2]!=before[2]:raise ValueError('Native refill changed old footprints/pad pieces/other objects')
    if any(after[1].get(k)!=v for k,v in before[1].items()if k not in {r['uuid']for r in legacy_ledger}):raise ValueError('Native refill changed unreviewed old zone definitions')
    for row in legacy_ledger:
        original=parse(before[1][row['uuid']]);revised=parse(after[1][row['uuid']])
        original_rules=copy.deepcopy(original);revised_rules=copy.deepcopy(revised)
        for node in list(children(original_rules,'polygon')):original_rules.remove(node)
        for node in list(children(revised_rules,'polygon')):revised_rules.remove(node)
        if dump(original_rules)!=dump(revised_rules):raise ValueError('Legacy zone rules/net/UUID changed outside exact polygons '+row['uuid'])
        row['before_raw_definition']=before[1][row['uuid']];row['after_raw_definition']=after[1][row['uuid']]
        import hashlib
        row['before_polygon_definition_sha256']=hashlib.sha256(before[1][row['uuid']].encode()).hexdigest()
        row['after_polygon_definition_sha256']=hashlib.sha256(after[1][row['uuid']].encode()).hexdigest()
    if legacy_ledger:
        new_clusters=native_pad_clusters(board,{net for net,layer in LEGACY_ZONES.values()})
        if any(not any(old['net']==new['net']and set(old['pad_UUIDs'])<=set(new['pad_UUIDs'])for new in new_clusters)for old in old_clusters):
            raise ValueError('Net-aware plane correction disconnected a prior actual source-pad cluster')
        write(out/'old-five-zone-source-pad-cluster-proof.json',dict(before=old_clusters,after=new_clusters,passed=True))
        write(out/'old-five-zone-outline-ledger.json',legacy_ledger)
    write(out/'reference-coverage.json',filled_return_coverage(board,mapping))
    write(out/'spanning-corridors.json',spanning)
    for path,h in hashes.items():
        if sha(path)!=h:raise ValueError('Immutable input changed '+path)
    receipt=dict(input_sha256=hashes,board_sha256=sha(candidate),footprints=len(board.GetFootprints()),
        old_copper_geometry_UUIDs_preserved=True,old_zone_definitions_preserved=not legacy_ledger,
        old_zone_rules_UUIDs_nets_preserved=True,exact_five_legacy_zone_outline_correction=bool(legacy_ledger),old_all_pad_pieces_preserved=True,
        track_via_count=len(board.GetTracks()),old_zone_count=len(oldzones),new_zone_rule_area_objects=len(additions),
        native_DRC_regular=len(drc.get('violations',[])),native_DRC_ignored=drc.get('ignored_checks',[]),
        uncapped_unconnected=board.GetConnectivity().GetUnconnectedCount(False),
        new_reference_plan_nets={layer:list(side['regions'])for layer,side in sides.items()},
        SUB_nets_accounted=44,SUB_thermal_2x2_copper_implemented=sum(z.GetZoneName().startswith('FLOATING_SUB_')for z in board.Zones())==44,
        field_spanning_reference_corridors_implemented=spanning_complete(spanning),
        status='native_position_derived_partial_return_prototype_not_manufacturing_ready',
        manufacturing_ready=False,physical_qualification=False)
    write(out/'receipt.json',receipt);print(json.dumps(receipt,indent=2))
    raise SystemExit(bool(receipt['native_DRC_regular'] or receipt['native_DRC_ignored']))


if __name__=='__main__':main()
