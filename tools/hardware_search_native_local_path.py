"""Finite native search for one literal same-side SOURCE pad pair.

This helper emits no copper and grants no electrical/routing qualification.
The caller supplies actual eligible native reference fill, exact ownership,
and must run full SOURCE, corridor, annulus and native DRC checks afterward.
"""
import heapq, math, time
import pcbnew
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy, mm, segment_distance
from hardware_check_return_corridors import covered, corridor_polygon


def find_local_pad_path(board, source_pad, target_pad, *, geometry,
                        eligible_reference_fill, layer=pcbnew.F_Cu,
                        width_mm=.20, clearance_mm=.20,
                        reference_margin_mm=.10, maximum_length_mm=8.0,
                        grid_mm=.125, maximum_states=14000, maximum_seconds=30):
    """Return a proposed path or a bounded failure; never modify ``board``.

    Both endpoints are actual same-net SOURCE pads. ``geometry`` is an actual
    hardware_route_owned_bypass_loops_wip_r03.Geometry(board), reusable across
    calls; update it after each independently accepted additive local route.
    Supply-loop callers should retain <=8 mm bounds and exact owner pins.
    """
    if layer not in (pcbnew.F_Cu, pcbnew.B_Cu):
        raise ValueError('Only an actual same-side F/B local pad pair is supported')
    if not (0 < maximum_length_mm <= 8 and .20 <= width_mm and .10 <= reference_margin_mm):
        raise ValueError('Local path length/width/reference bounds cannot be relaxed')
    name = source_pad.GetNetname()
    if not name or target_pad.GetNetname() != name or not source_pad.IsOnLayer(layer) or not target_pad.IsOnLayer(layer):
        raise ValueError('Actual same-net same-side SOURCE pad endpoints required')
    actual = {p.m_Uuid.AsString() for f in board.GetFootprints() for p in f.Pads()}
    if source_pad.m_Uuid.AsString() not in actual or target_pad.m_Uuid.AsString() not in actual:
        raise ValueError('Endpoint is not an actual numbered board SOURCE pad')
    start, end = mm(source_pad.GetPosition()), mm(target_pad.GetPosition())
    if math.dist(start, end) > maximum_length_mm:
        return dict(passed=False, reason='Actual source-pair span exceeds local bound')
    # Exact clipping removes possible reference coverage; it never expands it.
    margin = min(2., maximum_length_mm / 2)
    bounds = (min(start[0], end[0])-margin, min(start[1], end[1])-margin,
              max(start[0], end[0])+margin, max(start[1], end[1])+margin)
    box = pcbnew.SHAPE_POLY_SET(); box.NewOutline()
    for p in ((bounds[0], bounds[1]), (bounds[2], bounds[1]),
              (bounds[2], bounds[3]), (bounds[0], bounds[3])):
        box.Append(pcbnew.FromMM(p[0]), pcbnew.FromMM(p[1]))
    fill = pcbnew.SHAPE_POLY_SET(); fill.Append(eligible_reference_fill)
    fill.BooleanIntersection(box); fill.Simplify()

    def clear(points):
        for a, z in zip(points, points[1:]):
            seg = pcbnew.SEG(xy(a), xy(z))
            for pad, _ in geometry.pads.candidates(a, z, width_mm/2+clearance_mm+.1):
                if pad.IsOnLayer(layer) and pad.GetNetname() != name and pad.GetEffectiveShape(layer).Collide(
                        seg, pcbnew.FromMM(width_mm/2+clearance_mm-1e-6)):
                    return False
            for other, p, q, w in geometry.tracks[layer].candidates(a, z, width_mm/2+.5):
                if other != name and segment_distance(a, z, p, q) < width_mm/2+w/2+clearance_mm-1e-6:
                    return False
            copper = corridor_polygon(tuple(xy(a)), tuple(xy(z)), pcbnew.FromMM(width_mm/2))
            for zone in geometry.keepouts:
                if zone.IsOnLayer(layer) and zone.GetDoNotAllowTracks():
                    hit = pcbnew.SHAPE_POLY_SET(); hit.Append(copper); hit.BooleanIntersection(zone.Outline())
                    if hit.Area(): return False
            envelope = corridor_polygon(tuple(xy(a)), tuple(xy(z)), pcbnew.FromMM(width_mm/2+reference_margin_mm))
            if not covered(envelope, fill): return False
        return True

    def result(points, explored, method):
        length = sum(math.dist(a, z) for a, z in zip(points, points[1:]))
        if length > maximum_length_mm+1e-6 or not clear(points):
            raise ValueError('Final candidate violates exact local bound/native clearance/reference prefilter')
        return dict(passed=True, proposed_points_mm=points, actual_source_net=name,
                    actual_SOURCE_pad_UUIDs=[source_pad.m_Uuid.AsString(), target_pad.m_Uuid.AsString()],
                    layer=board.GetLayerName(layer), width_mm=width_mm, clearance_mm=clearance_mm,
                    reference_margin_mm=reference_margin_mm, path_length_mm=length,
                    explored_states=explored, grid_mm=grid_mm, method=method,
                    copper_added=0, exact_native_fill_clipping_only_removes_coverage=True,
                    final_native_SOURCE_DRC_and_full_return_validation_required=True,
                    manufacturing_ready=False)
    for points in paths(start, end):
        if sum(math.dist(a,z) for a,z in zip(points, points[1:])) <= maximum_length_mm and clear(points):
            return result(points, 0, 'Literal finite direct paths')
    lo = (math.floor(bounds[0]/grid_mm)*grid_mm, math.floor(bounds[1]/grid_mm)*grid_mm)
    def point(q): return (lo[0]+q[0]*grid_mm, lo[1]+q[1]*grid_mm)
    def index(p): return (round((p[0]-lo[0])/grid_mm), round((p[1]-lo[1])/grid_mm))
    def nearby(p):
        ix,iy=index(p)
        return [(ix+dx,iy+dy) for dx in range(-4,5) for dy in range(-4,5)
                if math.dist(point((ix+dx,iy+dy)),p)<.52 and clear([p,point((ix+dx,iy+dy))])]
    starts, ends = nearby(start), nearby(end)
    if not starts or not ends:
        return dict(passed=False, reason='Actual SOURCE pad lacks native-clear referenced local handoff',
                    start_choices=len(starts), end_choices=len(ends))
    heap=[]; costs={}; parents={}; edges={}; explored=0; t0=time.monotonic()
    maxq=index((bounds[2],bounds[3])); ends=set(ends)
    for q in starts:
        costs[q]=math.dist(point(q),start); parents[q]=None
        heapq.heappush(heap,(costs[q]+math.dist(point(q),end),costs[q],q))
    while heap:
        _, cost, q=heapq.heappop(heap)
        if cost != costs.get(q): continue
        explored += 1
        if q in ends and cost+math.dist(point(q),end) <= maximum_length_mm:
            chain=[]
            while q is not None: chain.append(point(q)); q=parents[q]
            raw=[start]+list(reversed(chain))+[end]
            raw=[v for i,v in enumerate(raw) if not i or math.dist(v,raw[i-1])>1e-6]
            simple=[raw[0]]; i=0
            while i<len(raw)-1:
                j=len(raw)-1
                while j>i+1 and not clear([raw[i],raw[j]]): j-=1
                simple.append(raw[j]); i=j
            return result(simple, explored, 'Finite native A*')
        if explored > maximum_states or time.monotonic()-t0 > maximum_seconds:
            return dict(passed=False, reason='Finite native A* budget exhausted', explored_states=explored)
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n=(q[0]+dx,q[1]+dy)
            if not (0<=n[0]<=maxq[0] and 0<=n[1]<=maxq[1]): continue
            nc=cost+grid_mm*math.hypot(dx,dy)
            if nc+math.dist(point(n),end)>maximum_length_mm or nc+1e-8>=costs.get(n,float('inf')): continue
            key=(q,n) if q<n else (n,q)
            if key not in edges: edges[key]=clear([point(q),point(n)])
            if not edges[key]: continue
            costs[n]=nc; parents[n]=q
            heapq.heappush(heap,(nc+math.dist(point(n),end),nc,n))
    return dict(passed=False, reason='No bounded native-clear referenced local path', explored_states=explored)
