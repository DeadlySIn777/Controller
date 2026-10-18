"""Read-only, conservative F configuration-space diagnostic; never route proof.

r01's SWIG parent lookup failure is retained. Resolve pad owners by the actual
footprint inventory, rather than calling GetReference on a proxy parent.
"""
from pathlib import Path
import json, sys

ROOT = Path.cwd()
sys.path[:0] = [str(ROOT / 'tools'), str(ROOT / 'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import pcbnew
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import hardware_route_selected_additive_r02 as e

R = ROOT / 'reports/freerouting-evaluation-20261002'
PRE = R / 'ROOT103-visual-local-window-DSN-r06'
OUT = R / 'ROOT103-local-F-configuration-space-r02'
OUT.mkdir(exist_ok=False)
inputs = {str(p.relative_to(ROOT)): e.sha(p) for p in [PRE/'selected.dsn', PRE/'base.kicad_pcb', PRE/'manifest.json']}
t = e.parse((PRE/'selected.dsn').read_text())
b = pcbnew.LoadBoard(str(PRE/'base.kicad_pcb'))
m = e.read(PRE/'manifest.json')
window = box(300_000_000, 120_000_000, 330_000_000, 150_000_000)
margin = 250_000  # .10-mm trace radius plus .15-mm exported clearance

def parts(g):
    if isinstance(g, Polygon):
        return [g]
    if hasattr(g, 'geoms'):
        return [p for c in g.geoms for p in parts(c)]
    return []

def geom(poly):
    def points(chain):
        return [(chain.CPoint(i).x, chain.CPoint(i).y) for i in range(chain.PointCount())]
    result = []
    for i in range(poly.OutlineCount()):
        p = Polygon(points(poly.COutline(i)), [points(poly.CHole(i,j)) for j in range(poly.HoleCount(i))])
        assert p.is_valid, 'Native transformed obstacle requires separate literal reconstruction'
        result.append(p)
    return unary_union(result)

obstacles = []
fixed_rows = []
for k in e.children(e.child(t, 'structure'), 'keepout'):
    raw = e.child(k, 'polygon')
    if raw is None or e.value(raw[1]) != 'F.Cu':
        continue
    def coords(r):
        return [(round(float(r[i])*1000), -round(float(r[i+1])*1000)) for i in range(3,len(r),2)]
    g = Polygon(coords(raw), [coords(e.child(w, 'polygon')) for w in e.children(k, 'window')])
    assert g.is_valid
    if g.intersects(window):
        # Extra 1 um exceeds circular chord underapproximation at 32 segments
        # per quadrant; this is deliberately conservative, not an exact router.
        obstacles.append(g.buffer(margin+1000, quad_segs=32, join_style='round'))
        fixed_rows.append(dict(name=e.value(k[1]), bounds_mm=[v/1e6 for v in g.bounds]))
fixed = unary_union(obstacles)
pad_rows = [(f.GetReference(), p) for f in b.GetFootprints() for p in f.Pads()]
pads = {(ref,p.GetNumber()):p for ref,p in pad_rows}

def memberships(pieces, endpoints):
    result = []
    for ref, pin in endpoints:
        p = pads[(ref,pin)].GetPosition()
        result.append([i for i,g in enumerate(pieces) if g.covers(Point(p.x,p.y))])
    common = set(result[0])
    for ids in result[1:]:
        common.intersection_update(ids)
    return result, sorted(common)

dsn_pieces = parts(window.buffer(-margin).difference(fixed))
rows = []
for name, row in m['nets'].items():
    metal = []
    identities = []
    for ref,p in pad_rows:
        if p.GetNetname() == name or not p.IsOnLayer(pcbnew.F_Cu):
            continue
        bb = p.GetBoundingBox()
        region = box(bb.GetLeft()-margin, bb.GetTop()-margin, bb.GetRight()+margin, bb.GetBottom()+margin)
        if not region.intersects(window):
            continue
        poly = pcbnew.SHAPE_POLY_SET()
        p.TransformShapeToPolygon(poly, pcbnew.F_Cu, margin, 1000, pcbnew.ERROR_OUTSIDE)
        g = geom(poly)
        if g.intersects(window):
            metal.append(g)
            identities.append(dict(kind='pad', uuid=str(p.m_Uuid), reference=ref, pin=p.GetNumber(), net=p.GetNetname()))
    for v in b.GetTracks():
        if v.GetNetname() == name or not v.IsOnLayer(pcbnew.F_Cu):
            continue
        bb = v.GetBoundingBox()
        region = box(bb.GetLeft()-margin, bb.GetTop()-margin, bb.GetRight()+margin, bb.GetBottom()+margin)
        if not region.intersects(window):
            continue
        poly = pcbnew.SHAPE_POLY_SET()
        v.TransformShapeToPolygon(poly, pcbnew.F_Cu, margin, 1000, pcbnew.ERROR_OUTSIDE)
        g = geom(poly)
        if g.intersects(window):
            metal.append(g)
            identities.append(dict(kind='via' if v.Type()==pcbnew.PCB_VIA_T else 'track', uuid=str(v.m_Uuid), net=v.GetNetname()))
    native_metal = unary_union(metal)
    blocked = unary_union([fixed, native_metal])
    free = window.buffer(-margin).difference(blocked)
    assert free.is_valid
    pieces = parts(free)
    ep_ids, common = memberships(pieces, row['source_pins'])
    dsn_ep_ids, dsn_common = memberships(dsn_pieces, row['source_pins'])
    endpoints = []
    for (ref,pin), ids, dsn_ids in zip(row['source_pins'], ep_ids, dsn_ep_ids):
        pad = pads[(ref,pin)]
        p = pad.GetPosition()
        point = Point(p.x,p.y)
        endpoints.append(dict(reference=ref, pin=pin, xy_mm=[p.x/1e6,p.y/1e6], free_components=ids, DSN_only_free_components=dsn_ids, blocked_by_DSN_polygon_or_void=fixed.covers(point), blocked_by_native_foreign_metal=native_metal.covers(point)))
    rows.append(dict(net=name, endpoints=endpoints, conservative_F_free_component_count=len(pieces), common_endpoint_components=common, common_component_bounds_mm=[[v/1e6 for v in pieces[i].bounds] for i in common], DSN_only_common_endpoint_components=dsn_common, native_foreign_metal_count=len(metal), native_foreign_metal_identities=identities, actual_accepted_route=False))
    # Preserve the literal diagnostic operands and derived free components.
    e.write(OUT/(name.rsplit('/',1)[-1]+'-geometry.json'), dict(native_IU_per_mm=1_000_000, fixed_DSN_WKT=fixed.wkt, native_foreign_metal_WKT=native_metal.wkt, conservative_F_free_space_WKT=free.wkt))
    print(json.dumps(dict(net=name, endpoints=endpoints, common_components=common, DSN_only_common_components=dsn_common), indent=2), flush=True)

assert all(e.sha(ROOT/path)==sha for path,sha in inputs.items())
e.write(OUT/'review.json', dict(passed=True, diagnostic_only=True, inputs=inputs, script_sha256=e.sha(Path(__file__)), source_board_sha256=e.sha(PRE/'base.kicad_pcb'), selected_DSN_sha256=e.sha(PRE/'selected.dsn'), native_window_mm=[300,120,330,150], trace_width_mm=.20, clearance_mm=.15, configuration_space_radius_mm=.25, conservative_native_polygon_max_error_mm=.001, DSN_round_buffer_extra_mm=.001, via_layer_span_may_overblock_unflashed_annuli=True, no_geometric_impossibility_or_route_acceptance_claim=True, all_endpoint_rows=rows, fixed_DSN_obstacle_count=len(obstacles), fixed_DSN_obstacle_rows=fixed_rows, no_source_or_board_writes=True, no_router_trial_started=True, hold_for_user_Argus_routing=True, retained_r01_failure='AttributeError: BOARD_ITEM_CONTAINER has no GetReference; footprint-owned pad lookup replaces only that proxy assumption'))
