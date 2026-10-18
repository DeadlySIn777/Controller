# Exact (vector, not raster) audit of a stitch plan against geom.json, independent of the planner's raster code.
# For every planned via (d, drill) + stub (pad centre -> via, stub_w, on the pad layer) it measures:
#   - copper gap to every OTHER-net pad / track / via / copper shape (via: all six layers; stub: its layer),
#     required 0.15 mm (same galvanic domain = same first net-class component) or 0.6 mm (cross-domain, NC_ISOLATE,
#     net-less copper); domains come from the --classes geom.json (one dumped WITH the board's project file)
#   - via copper to board edge (rounded rectangle 0..450 x 0..235, required 0.5 mm)
#   - via annulus to every SMD/CONN pad copper on the outer layers (required >= 0.10 mm + mask expansion; expansions
#     from --pad-mask JSON {"REF.NUM": mm}, default 0)
#   - hole-to-hole to every existing drill (required 0.25 mm) and new-vs-new (same net or not)
#   - new-vs-new copper (via/via, via/stub, stub/stub on one layer) for different nets
#   - the via centre inside its own net's inner-layer fill (stored fills in geom.json), with the depth
#   python plan_exact_check.py geom.json plan.json out.json [--classes geom_with_classes.json] [--pad-mask m.json]
import json
import math
import sys
import hashlib
from pathlib import Path
from collections import defaultdict, Counter

# Pin every loaded Python module file, the interpreter and this executed helper.
# This is host runtime/source provenance, not an inventory of operating-system DLLs.
hashlib.sha256(b'').hexdigest()
def runtime_paths():
    paths = {str(Path(__file__).resolve()), str(Path(sys.executable).resolve())}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_file():
            paths.add(str(Path(filename).resolve()))
    return paths

def hashes(paths):
    return {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)}

runtime_before = hashes(runtime_paths())
input_paths = {str(Path(sys.argv[i]).resolve()) for i in (1, 2)}
for option in ('--classes', '--pad-mask'):
    if option in sys.argv:
        input_paths.add(str(Path(sys.argv[sys.argv.index(option)+1]).resolve()))
input_before = hashes(input_paths)
if str(Path(sys.argv[3]).resolve()) in input_paths | set(runtime_before):
    raise ValueError('Vector output aliases a protected input/runtime file')

G = json.load(open(sys.argv[1], encoding="utf-8"))
P = json.load(open(sys.argv[2], encoding="utf-8"))
OUT = sys.argv[3]


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


GC = json.load(open(arg("--classes"), encoding="utf-8")) if arg("--classes") else G
PM = json.load(open(arg("--pad-mask"), encoding="utf-8")) if arg("--pad-mask") else {}
CLR, XDOM, EDGE, H2H, GAP = 0.15, 0.6, 0.5, 0.25, 0.10
W, H = 450.0, 235.0
dom = {}
for p in GC["pads"]:
    if p["net"]:
        dom.setdefault(p["net"], p["cls"].split(",")[0])


def need(n1, n2):
    if not n2 or not n1:
        return XDOM
    d1, d2 = dom.get(n1, "UNKNOWN"), dom.get(n2, "UNKNOWN")
    if not (d1.startswith("DOM_") and d2.startswith("DOM_")):
        return XDOM
    if d1 == "NC_ISOLATE" or d2 == "NC_ISOLATE":
        return XDOM
    return CLR if d1 == d2 else XDOM


def seg_pt(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def seg_seg(a, b, c, d):
    def ccw(p, q, r):
        return (r[1] - p[1]) * (q[0] - p[0]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2, d3, d4 = ccw(a, b, c), ccw(a, b, d), ccw(c, d, a), ccw(c, d, b)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return 0.0
    return min(seg_pt(*a, *c, *d), seg_pt(*b, *c, *d), seg_pt(*c, *a, *b), seg_pt(*d, *a, *b))


def inside(px, py, ring):
    c = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > py) != (y2 > py) and px < (x2 - x1) * (py - y1) / (y2 - y1) + x1:
            c = not c
    return c


def poly_pt(px, py, ring):
    if inside(px, py, ring):
        return 0.0
    n = len(ring)
    return min(seg_pt(px, py, *ring[i], *ring[(i + 1) % n]) for i in range(n))


def poly_seg(a, b, ring):
    if inside(*a, ring) or inside(*b, ring):
        return 0.0
    n = len(ring)
    return min(seg_seg(a, b, ring[i], ring[(i + 1) % n]) for i in range(n))


# spatial index of obstacles: (kind, net, layers(set or None=all), geometry)
CELL = 1.0
grid = defaultdict(list)
objs = []


def add(o, xa, ya, xb, yb):
    i = len(objs)
    objs.append(o)
    for gx in range(int(math.floor(xa / CELL)), int(math.floor(xb / CELL)) + 1):
        for gy in range(int(math.floor(ya / CELL)), int(math.floor(yb / CELL)) + 1):
            grid[(gx, gy)].append(i)


for p in G["pads"]:
    for e in p["poly"]:
        ring = e[0]
        if len(ring) < 3:
            continue
        xs, ys = [q[0] for q in ring], [q[1] for q in ring]
        add({"k": "pad", "net": p["net"], "layers": set(p["layers"]), "ring": ring, "id": f"{p['ref']}.{p['num']}",
             "smd": p["smd"] and any(L in ("F.Cu", "B.Cu") for L in p["layers"]),
             "exp": PM.get(f"{p['ref']}.{p['num']}", 0.0)}, min(xs), min(ys), max(xs), max(ys))
    if p["drill"] > 0:
        add({"k": "hole", "net": p["net"], "x": p["x"], "y": p["y"], "dr": p["drill"], "id": f"{p['ref']}.{p['num']}",
             "npth": not p["layers"] or p["net"] == ""}, p["x"] - 1, p["y"] - 1, p["x"] + 1, p["y"] + 1)
for t in G["tracks"]:
    (ax, ay), (bx, by) = t["a"], t["b"]
    r = t["w"] / 2
    add({"k": "track", "net": t["net"], "layers": {t["layer"]}, "a": (ax, ay), "b": (bx, by), "r": r},
        min(ax, bx) - r, min(ay, by) - r, max(ax, bx) + r, max(ay, by) + r)
for v in G["vias"]:
    add({"k": "via", "net": v["net"], "layers": None, "x": v["x"], "y": v["y"], "r": v["d"] / 2, "dr": v["drill"]},
        v["x"] - v["d"] / 2, v["y"] - v["d"] / 2, v["x"] + v["d"] / 2, v["y"] + v["d"] / 2)
for sh in G.get("shapes", []):
    for e in sh["poly"]:
        ring = e[0]
        if len(ring) < 3:
            continue
        xs, ys = [q[0] for q in ring], [q[1] for q in ring]
        add({"k": "shape", "net": sh["net"], "layers": {sh["layer"]}, "ring": ring}, min(xs), min(ys), max(xs), max(ys))


def near(xa, ya, xb, yb):
    seen = set()
    for gx in range(int(math.floor(xa / CELL)), int(math.floor(xb / CELL)) + 1):
        for gy in range(int(math.floor(ya / CELL)), int(math.floor(yb / CELL)) + 1):
            for i in grid.get((gx, gy), ()):
                if i not in seen:
                    seen.add(i)
                    yield objs[i]


fills = defaultdict(list)  # net -> [(layer, ring, holes)]
for z in G["zones"]:
    for L, fl in z["fills"].items():
        if L in ("F.Cu", "B.Cu"):
            continue
        for ring, holes in fl:
            if len(ring) >= 3:
                fills[z["net"]].append((L, ring, holes))

res = []
plan = P["plan"]
for s in plan:
    vx, vy = s["via"]
    rv, rd = s["d"] / 2, s["drill"] / 2
    net, L = s["net"], s["layer"]
    a, b = tuple(s["pad_xy"]), (vx, vy)
    sw = s["stub_w"] / 2
    viol = []
    worst = {"via_cu": 9, "stub_cu": 9, "smd_gap": 9, "h2h": 9, "edge": 9}
    R = 1.6
    for o in near(vx - R, vy - R, vx + R, vy + R):
        k = o["k"]
        if k == "hole":
            dd = math.hypot(vx - o["x"], vy - o["y"]) - o["dr"] / 2 - rd
            worst["h2h"] = min(worst["h2h"], dd)
            if dd < H2H - 1e-6:
                viol.append(("hole_to_hole", o["id"], round(dd, 3)))
            if o["npth"]:
                dc = math.hypot(vx - o["x"], vy - o["y"]) - o["dr"] / 2 - rv
                if dc < 0.25 - 1e-6:
                    viol.append(("via_to_npth_hole", o["id"], round(dc, 3)))
            continue
        if o["net"] == net:
            if k == "pad" and o["smd"]:
                g = poly_pt(vx, vy, o["ring"]) - rv - o["exp"]
                worst["smd_gap"] = min(worst["smd_gap"], g)
                if g < GAP - 1e-6:
                    viol.append(("via_in_pad_gap(own net)", o["id"], round(g, 3)))
            if k == "via":
                dd = math.hypot(vx - o["x"], vy - o["y"]) - o["dr"] / 2 - rd
                worst["h2h"] = min(worst["h2h"], dd)
                if dd < H2H - 1e-6:
                    viol.append(("hole_to_hole(own via)", "", round(dd, 3)))
            continue
        req = need(net, o["net"])
        if k == "pad":
            dcu = poly_pt(vx, vy, o["ring"]) - rv
            if o["smd"]:
                g = dcu - o["exp"]
                worst["smd_gap"] = min(worst["smd_gap"], g)
                if g < GAP - 1e-6:
                    viol.append(("via_in_pad_gap", o["id"], round(g, 3)))
        elif k == "track":
            dcu = seg_pt(vx, vy, *o["a"], *o["b"]) - o["r"] - rv
        elif k == "via":
            dcu = math.hypot(vx - o["x"], vy - o["y"]) - o["r"] - rv
            dd = math.hypot(vx - o["x"], vy - o["y"]) - o["dr"] / 2 - rd
            worst["h2h"] = min(worst["h2h"], dd)
            if dd < H2H - 1e-6:
                viol.append(("hole_to_hole", "via " + o["net"], round(dd, 3)))
        else:
            dcu = poly_pt(vx, vy, o["ring"]) - rv
        worst["via_cu"] = min(worst["via_cu"], dcu - req)
        if dcu < req - 1e-6:
            viol.append(("via_clearance", f"{k} {o.get('id', '')} {o['net']} req {req}", round(dcu, 3)))
    # stub on its layer
    xa, xb = min(a[0], b[0]) - 1, max(a[0], b[0]) + 1
    ya, yb = min(a[1], b[1]) - 1, max(a[1], b[1]) + 1
    for o in near(xa, ya, xb, yb):
        k = o["k"]
        if k == "hole" or o["net"] == net:
            continue
        if o["layers"] is not None and L not in o["layers"]:
            continue
        req = need(net, o["net"])
        if k in ("pad", "shape"):
            dcu = poly_seg(a, b, o["ring"]) - sw
        elif k == "track":
            dcu = seg_seg(a, b, o["a"], o["b"]) - o["r"] - sw
        else:
            dcu = seg_pt(o["x"], o["y"], *a, *b) - o["r"] - sw
        worst["stub_cu"] = min(worst["stub_cu"], dcu - req)
        if dcu < req - 1e-6:
            viol.append(("stub_clearance", f"{k} {o.get('id', '')} {o['net']} req {req}", round(dcu, 3)))
    e = min(vx, W - vx, vy, H - vy) - rv
    worst["edge"] = e
    if e < EDGE - 1e-6:
        viol.append(("via_edge_clearance", "", round(e, 3)))
    # own-plane landing (stored fills)
    land = []
    for Lf, ring, holes in fills.get(net, []):
        xs = [q[0] for q in ring]
        if not (min(xs) <= vx <= max(xs)):
            continue
        if inside(vx, vy, ring) and not any(len(h) >= 3 and inside(vx, vy, h) for h in holes):
            n = len(ring)
            depth = min(seg_pt(vx, vy, *ring[i], *ring[(i + 1) % n]) for i in range(n))
            land.append((Lf, round(depth, 3)))
    if not land:
        viol.append(("no_own_fill_under_via", "", 0))
    res.append({"ref": s["ref"], "pad": s["pad"], "net": net, "layer": L, "via": s["via"], "dist": s["dist"],
                "land": land, "worst_margin": {k: round(v, 3) for k, v in worst.items()}, "viol": viol})
# new vs new
for i in range(len(plan)):
    si = plan[i]
    for j in range(i + 1, len(plan)):
        sj = plan[j]
        if abs(si["via"][0] - sj["via"][0]) > 6 or abs(si["via"][1] - sj["via"][1]) > 6:
            continue
        dvv = math.hypot(si["via"][0] - sj["via"][0], si["via"][1] - sj["via"][1])
        h = dvv - si["drill"] / 2 - sj["drill"] / 2
        if h < H2H - 1e-6:
            res[i]["viol"].append(("new_hole_to_hole", f"{sj['ref']}.{sj['pad']}", round(h, 3)))
        if si["net"] == sj["net"]:
            continue
        req = need(si["net"], sj["net"])
        c = dvv - si["d"] / 2 - sj["d"] / 2
        if c < req - 1e-6:
            res[i]["viol"].append(("new_via_via", f"{sj['ref']}.{sj['pad']} {sj['net']}", round(c, 3)))
        for (s1, s2) in ((si, sj), (sj, si)):
            c2 = seg_pt(s2["via"][0], s2["via"][1], *s1["pad_xy"], *s1["via"]) - s1["stub_w"] / 2 - s2["d"] / 2
            if c2 < req - 1e-6:
                res[i]["viol"].append(("new_stub_via", f"{s1['ref']}.{s1['pad']} vs via {s2['ref']}.{s2['pad']}", round(c2, 3)))
        if si["layer"] == sj["layer"]:
            c3 = seg_seg(tuple(si["pad_xy"]), tuple(si["via"]), tuple(sj["pad_xy"]), tuple(sj["via"])) - \
                si["stub_w"] / 2 - sj["stub_w"] / 2
            if c3 < req - 1e-6:
                res[i]["viol"].append(("new_stub_stub", f"{sj['ref']}.{sj['pad']}", round(c3, 3)))
cnt = Counter(v[0] for r in res for v in r["viol"])
nbad = sum(1 for r in res if r["viol"])
mins = {k: min(r["worst_margin"][k] for r in res) for k in res[0]["worst_margin"]} if res else {}
runtime_after = hashes(runtime_paths())
input_after = hashes(input_paths)
if runtime_before != runtime_after or input_before != input_after:
    raise ValueError('Vector helper/runtime/input files changed during checking')
provenance = {'before': runtime_before, 'after': runtime_after, 'unchanged': True,
              'inputs_before': input_before, 'inputs_after': input_after,
              'scope': 'Every loaded Python module file plus interpreter/helper; OS DLL dependencies not inventoried'}
json.dump({"plan": sys.argv[2], "planned": len(plan), "stitches_with_violations": nbad, "by_type": cnt,
           "min_margins": mins, "rows": res, "runtime_provenance": provenance}, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps({"plan": sys.argv[2], "planned": len(plan), "stitches_with_violations": nbad, "by_type": cnt,
                  "min_margins": mins}))
for r in res:
    if r["viol"]:
        print(" ", r["ref"], r["pad"], r["net"][-22:], r["via"], r["viol"][:3])
