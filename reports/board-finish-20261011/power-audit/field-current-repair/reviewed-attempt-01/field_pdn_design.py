"""field_pdn_design.py - field power distribution (FIELD_A / FIELD_B supply and return) on In3 with via arrays.

    C:/Python314/python.exe tools/field_pdn_design.py --geom GEOM.json --partitions PART.json --work DIR
        [--spec tools/field_pdn_spec.json] [--dru board.kicad_dru] [--only FAG,FA,FBG,FB]

GEOM.json is tools/field_pdn_dump.py output of the INPUT board (refilled). Writes into DIR:
    analysis.json  sources, clusters + current shares, copper islands, In3 occupancy, via-array legality per end
    design.json    per net: In3 tree (segments: width, current, IPC-2152 rise, resistance), via arrays (n vs n_req),
                   DC drop per cluster, territory crossed, blocked joins with the blocker and a rip-up proposal
    routes.json    tools/corridor_apply.py format (In3 tracks + through vias of the four nets) - nothing else
Method:
  * In3 free space per net from a 0.1 mm raster of the REFILLED copper (cv2 sub-pixel polygon fill) and Euclidean
    distance transforms: clearance 0.15 mm to other nets of the same galvanic domain, 0.6 mm to other domains
    (board.kicad_dru P1v2 rules, every layer), 0.25 mm to holes, 0.5 mm to the board edge, no copper inside rule
    areas (keepouts, TMR4WI areas), router reservations on In3 (tools/reserve_corridors.py differential-pair bands;
    an area whose exemption list contains the net is not an obstacle for it), the /CORE_1V2 region outline, and
    galvanic-barrier part courtyards + 0.6 mm (Z:/pcb-runs/domains/barriers.json parts). 0.1 mm raster margin;
    every segment and via is re-checked exactly with shapely before it is written.
  * Trees: scipy Dijkstra on a 0.2 mm grid; edge cost = length x territory factor / min(available width, target
    width) = the path of least DC resistance through the available In3 width. Territory = owner of the In1/In4 plane
    under the cell: own domain 1.0, no plane 1.2, LOGIC 1.5, the other field domain 2.5, any other isolated domain
    4.0. The highest-current cluster is routed first from the source; every other cluster joins the tree. The return
    net of a domain is routed first; its supply partner gets a 0.85 cost factor within 3.5 mm of it (side by side).
  * Via arrays: n_req = ceil(I / 0.5 A); 0.6/0.3 mm through vias where a via is legal on all six layers (clearances
    above, >= 0.10 mm from every SMD pad aperture, 0.25 mm hole-to-hole, edge 0.5 mm + radius, never within 0.6 mm
    of another domain's copper or fill on ANY layer = no piercing of another domain's In1/In2/In4 fill) and that
    land on the island's own copper (own-net zone fill, or the body of an own-net track); joined on In3.
  * Widths: IPC-2152 10 C rise at the segment current (Brooks & Adam fit of the IPC-2152 data, conservative for
    inner layers), then widened up to the available width while the DC drop at the design current exceeds 80 % of
    the DRAFT budget. Segment current = explicit downstream sum; inconsistent documented loads/design/source limits reject before routing.
  * Only the four nets' new In3 copper and through vias are written; existing copper is untouched (parallel paths).
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from field_current_guard import CurrentModelError, validate_spec, required_vias, array_status, modeled_route_status, route_output

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "4")
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import scipy.ndimage as ndi  # noqa: E402
import scipy.sparse as sp  # noqa: E402
import scipy.sparse.csgraph as csg  # noqa: E402
import shapely  # noqa: E402
from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from shapely.strtree import STRtree  # noqa: E402

T0 = time.time()
TOOL = "tools/field_pdn_design.py"
VERSION = "1.0 (2026-10-11)"
H = 0.1            # fine raster pitch, mm
K = 2              # routing grid = K * H
MARGIN = 0.1       # raster safety margin, mm
CL_SAME, CL_CROSS, CL_HOLE, CL_EDGE, CL_SMD, H2H = 0.15, 0.6, 0.25, 0.5, 0.10, 0.25
RHO20 = 1.7241e-8  # ohm m, IEC 60028
T_CU = 0.035e-3    # m, 1 oz on every layer
TJ = 60.0          # conductor temperature for the drop judgement, C (same as tools/verify/pdn_ir.py)
RHO_T = RHO20 * (1 + 0.00393 * (TJ - 20))
RS20 = RHO20 / T_CU
RST = RHO_T / T_CU
PLATING = 25e-6    # via barrel plating, m (IPC-6012 class 3 average)
W_MIN = 0.3        # narrowest trunk / branch, mm
W_STUB = 0.8       # via-array link cap, mm
TRACK_LAND_MM = 6.0  # vias may land on an island's thin tracks only this close to its terminal pads
ZERO_BRANCH_MM = 60.0  # a zero-current island (plane region, no load) is joined only by a branch up to this long
FILL_LAND_MM = 15.0  # terminal mode: vias may land on the terminal island's plane fill within this radius of its pads
END_KEEP = 0.05     # a new via keeps its pad this far from the end point of an existing own-net track
RIP_PENALTY = 60.0  # rip-up proposal mode: cost factor of cells next to a foreign In3 track
IN3 = "In3.Cu"
FIELD_DOMS = ("DOM_FIELD_A", "DOM_FIELD_B")


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def norm(n):
    return (n or "").replace("{slash}", "/")


MIL = 0.0254
TH_MIL = T_CU * 1e3 / MIL


def ipc_width_mm(amps, dt=10.0):
    """IPC-2152 width for a dt rise (Brooks & Adam fit, PCD&F 2015 Eq. 5: dT = 215.3 I^2 W^-1.15 Th^-1, mil)."""
    if amps <= 0:
        return 0.0
    return (215.3 * amps * amps / (dt * TH_MIL)) ** (1 / 1.15) * MIL


def ipc_rise(amps, w_mm):
    if amps <= 0 or w_mm <= 0:
        return 0.0
    return 215.3 * amps * amps * (w_mm / MIL) ** -1.15 / TH_MIL


def via_r(dz_m, drill_m=0.3e-3):
    return RHO_T * dz_m / (math.pi * PLATING * (drill_m + PLATING))


def rings_to_polys(pl):
    out = []
    for ring, holes in pl or []:
        if len(ring) < 3:
            continue
        try:
            p = Polygon(ring, [h for h in holes if len(h) >= 3])
            if not p.is_valid:
                p = p.buffer(0)
        except Exception:
            continue
        if not p.is_empty:
            out.append(p)
    return out


def arc_points(a, m, b, seg=0.2):
    (x1, y1), (x2, y2), (x3, y3) = a, m, b
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return [a, b]
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    t1, t2, t3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (a, m, b))
    tm, te = (t2 - t1) % (2 * math.pi), (t3 - t1) % (2 * math.pi)
    sweep = te if tm < te else -((t1 - t3) % (2 * math.pi))
    n = max(2, int(abs(sweep) * r / seg) + 1)
    return [(ux + r * math.cos(t1 + sweep * i / n), uy + r * math.sin(t1 + sweep * i / n)) for i in range(n + 1)]


def track_geom(t):
    pts = arc_points(t["a"], t["mid"], t["b"]) if t.get("mid") else [t["a"], t["b"]]
    if len(pts) == 2 and math.dist(pts[0], pts[1]) < 1e-6:
        return Point(pts[0]).buffer(t["w"] / 2, 8)
    return LineString(pts).buffer(t["w"] / 2, 8)


class Raster:
    def __init__(self, x0, y0, x1, y1, h):
        self.x0, self.y0, self.h = x0, y0, h
        self.nx = int(math.ceil((x1 - x0) / h)) + 1
        self.ny = int(math.ceil((y1 - y0) / h)) + 1
        self.n = self.nx * self.ny

    def empty(self):
        return np.zeros((self.ny, self.nx), np.uint8)

    def _pts(self, ring):
        a = np.asarray(ring, dtype=np.float64)
        return np.round(np.stack([(a[:, 0] - self.x0) / self.h, (a[:, 1] - self.y0) / self.h], 1) * 16).astype(np.int32)

    def fill_geom(self, img, g, val=1):
        if g is None or g.is_empty:
            return
        geoms = [g] if g.geom_type == "Polygon" else [x for x in getattr(g, "geoms", []) if x.geom_type == "Polygon"]
        for p in geoms:
            rings = [self._pts(p.exterior.coords)] + [self._pts(r.coords) for r in p.interiors]
            cv2.fillPoly(img, rings, val, lineType=cv2.LINE_8, shift=4)

    def to_cell(self, x, y):
        return int(round((y - self.y0) / self.h)), int(round((x - self.x0) / self.h))

    def pack(self, img):
        return np.packbits(img.ravel() > 0)

    def unpack(self, pk):
        return np.unpackbits(pk, count=self.n).reshape(self.ny, self.nx)


def edt_mm(mask, h):
    if not mask.any():
        return np.full(mask.shape, 1e3, np.float32)
    return ndi.distance_transform_edt(mask == 0, sampling=h).astype(np.float32)


def parse_dru_reservations(dru_path):
    ex = {}
    if not dru_path or not os.path.exists(dru_path):
        return ex
    for line in open(dru_path, encoding="utf-8"):
        m = re.match(r'\(rule "(RESERVE_KEEPOUT_[^"]+)" \(condition "(.*)"\) \(constraint disallow track via\)\)', line.strip())
        if m:
            ex[m.group(1)] = set(norm(n) for n in re.findall(r"A\.NetName != '([^']*)'", m.group(2)))
    return ex


class Designer:
    def __init__(self, G, PART, spec, args):
        self.current_preflight = validate_spec(spec, args.only)
        self.G, self.PART, self.spec, self.a = G, PART, spec, args
        self.layers = G["copper_layers"]
        self.cls = {norm(n): c for n, c in G["nets"].items()}
        self.board_name = {norm(n): n for n in G["nets"]}
        self.via_d = spec["via"]["d"]
        self.via_drill = spec["via"]["drill"]
        self.amps_per_via = spec["via"]["amps_per_via"]
        self.all_rails = spec["rails"]
        for r in self.all_rails:
            bn = self.board_name.get(norm(r["net"]))
            if bn is None:
                raise SystemExit(f"net not on board: {r['net']}")
            r["board_net"] = bn
        self.rid_of = {r["board_net"]: r["id"] for r in self.all_rails}
        self.rail = {r["id"]: r for r in self.all_rails}
        self.rails = [r for r in self.all_rails if not args.only or r["id"] in args.only.split(",")]
        self.terminal_mode = bool(getattr(args, "ripup_proposal", False)) or bool(getattr(args, "terminal_mode", False))
        tl = getattr(args, "track_land_mm", None)
        self.track_land = (TRACK_LAND_MM if getattr(args, "ripup_proposal", False) else 0.0) if tl is None else tl
        self.new_items = []
        self.out_tracks, self.out_vias = [], []
        self.analysis = {"tool": TOOL, "version": VERSION, "input": {"geom": args.geom, "board_sha256": G.get("sha256"),
                         "refilled": G.get("refilled"), "partitions": args.partitions,
                         "partitions_sha256": PART.get("sha256")}, "nets": {}}
        self.design = {"tool": TOOL, "version": VERSION, "method": __doc__, "nets": {}}

    def dom(self, net):
        if not net:
            return "NETLESS"
        return self.cls.get(norm(net), "") or "Default"

    def fkey(self, net):
        """raster group of a non-target net: its field domain or OTHER."""
        d = self.dom(net)
        return d if d in FIELD_DOMS else "OTHER"

    # ------------------------------------------------------------------ model
    def build(self):
        G = self.G
        self.board = unary_union(rings_to_polys(G["outline"]))
        if self.board.geom_type != "Polygon":
            self.board = max(self.board.geoms, key=lambda g: g.area)
        x0, y0, x1, y1 = self.board.bounds
        self.R = Raster(x0 - 1.0, y0 - 1.0, x1 + 1.0, y1 + 1.0, H)
        log("board", [round(v, 2) for v in self.board.bounds], "raster", self.R.nx, "x", self.R.ny)
        self.items = {L: [] for L in self.layers}
        self.holes = []
        for p in G["pads"]:
            for L, pl in p["layers"].items():
                for g in rings_to_polys(pl):
                    self.items[L].append((g, p["net"], "pad_smd" if p["smd"] else "pad_th", p["ref"] + "." + p["num"]))
            if p.get("hole"):
                for g in rings_to_polys(p["hole"]):
                    self.holes.append((g, p["net"]))
            elif p.get("hole_circle"):
                x, y, r = p["hole_circle"]
                self.holes.append((Point(x, y).buffer(r, 16), p["net"]))
        for t in G["tracks"]:
            if t["layer"] in self.items:
                self.items[t["layer"]].append((track_geom(t), t["net"], "track", t["uuid"]))
        for v in G["vias"]:
            g = Point(v["x"], v["y"]).buffer(v["d"] / 2, 16)
            for L in v["flashed"]:
                self.items[L].append((g, v["net"], "via", v["uuid"]))
            self.holes.append((Point(v["x"], v["y"]).buffer(v["drill"] / 2, 16), v["net"]))
        self.core12 = []
        for z in G["zones"]:
            for L, pl in z["fills"].items():
                for g in rings_to_polys(pl):
                    self.items[L].append((g, z["net"], "fill", z["uuid"]))
            if norm(z["net"]) == "/CORE_1V2" and IN3 in z["layers"]:
                self.core12 += rings_to_polys(z["outline"])
        for s in G["shapes"]:
            for g in rings_to_polys(s["poly"]):
                self.items[s["layer"]].append((g, s["net"], "shape", ""))
        self.hard = {L: [] for L in self.layers}   # (geom, exempt nets or None, name, blocks tracks, blocks vias)
        for ra in G["rule_areas"]:
            name = ra["name"]
            bt = bool(ra.get("no_tracks")) or "KEEPOUT" in name.upper()
            bv = bool(ra.get("no_vias")) or "KEEPOUT" in name.upper()
            if bt or bv:
                for L in ra["layers"]:
                    for g in rings_to_polys(ra["outline"]):
                        self.hard[L].append((g, None, name, bt, bv))
        try:
            bar = {b["refdes"] for b in json.load(open(self.a.barriers, encoding="utf-8"))["barriers"]}
        except Exception as ex:
            log("barriers.json not read:", ex)
            bar = set()
        nb = 0
        for f in G.get("footprints", []):
            if f["ref"] in bar:
                for side, pl in f["courtyard"].items():
                    for g in rings_to_polys(pl):
                        self.hard[IN3].append((g.buffer(CL_CROSS, 8), None, "BARRIER_" + f["ref"], True, False))
                        nb += 1
        self.n_barrier = nb
        log("barrier courtyards on In3:", nb, "| CORE_1V2 In3 outlines:", len(self.core12))
        self.pool = []
        if self.a.ripup_proposal:
            # WHAT-IF: every foreign In3 signal track may be ripped up (and re-routed elsewhere); they are removed from
            # the obstacles and charged a crossing penalty, and the ones the design hits are listed as the proposal
            keep = []
            for it in self.items[IN3]:
                (self.pool if it[2] == "track" and it[1] not in self.rid_of else keep).append(it)
            self.items[IN3] = keep
            log(f"RIP-UP PROPOSAL MODE: {len(self.pool)} foreign In3 tracks treated as removable (penalised)")
            if getattr(self.a, "ripup_vias", False):
                plane_nets = {z["net"] for z in G["zones"] if any(L in z["layers"] for L in ("In1.Cu", "In2.Cu", "In4.Cu"))}
                sig_vias = {v["uuid"]: v for v in G["vias"] if v["net"] not in self.rid_of and v["net"] not in plane_nets}
                for L in self.layers:
                    keep = []
                    for it in self.items[L]:
                        if it[2] == "via" and it[3] in sig_vias:
                            if L == IN3:
                                self.pool.append(it)
                        else:
                            keep.append(it)
                    self.items[L] = keep
                vx = {(round(v["x"], 4), round(v["y"], 4)) for v in sig_vias.values()}
                self.holes = [(g, n) for (g, n) in self.holes
                              if not (n in {v["net"] for v in sig_vias.values()} and (round(g.centroid.x, 4), round(g.centroid.y, 4)) in vx)]
                log(f"  + {len(sig_vias)} foreign signal vias (nets without inner-layer fills) treated as removable")
        self.reservations()
        self.island_model()
        self.build_base()
        self.territory()

    def reservations(self):
        G = self.G
        compat = {"pads": [], "tracks": [], "keepouts": [], "vias": [], "zones": []}
        for p in G["pads"]:
            lays = list(p["layers"])
            compat["pads"].append({"ref": p["ref"], "num": p["num"], "net": p["net"], "x": p["x"], "y": p["y"],
                                   "smd": p["smd"], "layers": lays, "poly": p["layers"][lays[0]] if lays else []})
        for t in G["tracks"]:
            compat["tracks"].append({"net": t["net"], "layer": t["layer"], "w": t["w"], "a": t["a"], "b": t["b"]})
        rdir = os.path.join(self.a.work, "reserve")
        os.makedirs(rdir, exist_ok=True)
        cg = os.path.join(rdir, "compat_geom.json")
        json.dump(compat, open(cg, "w", encoding="utf-8"))
        og = os.path.join(rdir, "geom_reserved.json")
        r = subprocess.run([sys.executable, self.a.reserve, cg, self.a.partitions, self.a.dru, og, rdir],
                           capture_output=True, text=True)
        open(os.path.join(rdir, "reserve.log"), "w").write(r.stdout + r.stderr)
        self.res_ok = r.returncode == 0 and os.path.exists(og)
        self.res_areas = []
        if not self.res_ok:
            log("reserve_corridors FAILED (rc", r.returncode, "): reservations NOT applied (reserve/reserve.log)")
            return
        ex = parse_dru_reservations(os.path.join(rdir, "board.kicad_dru"))
        soft_pref = [p for p in (getattr(self.a, "allow_reservations", "") or "").split(",") if p]
        self.soft_res = []
        for k in json.load(open(og, encoding="utf-8"))["keepouts"]:
            if k["name"].startswith("RESERVE_KEEPOUT_"):
                for L in k["layers"]:
                    for g in rings_to_polys(k["outline"]):
                        self.res_areas.append((L, k["name"], g))
                        if L == IN3 and any(k["name"][16:].startswith(p) for p in soft_pref):
                            self.soft_res.append((k["name"], g))   # what-if: crossable on In3 at a cost
                            continue
                        self.hard[L].append((g, ex.get(k["name"], set()), k["name"], True, True))
        for f in (cg, og):
            os.remove(f)
        log("reservations:", r.stdout.strip()[-220:])

    def island_model(self):
        """copper connectivity per target net (shapely): component of every own item, mapped to partition groups."""
        self.isl = {}
        for r in self.all_rails:
            net = r["board_net"]
            groups = self.PART["nets"].get(net)
            if groups is None:
                groups = next((g for n, g in self.PART["nets"].items() if norm(n) == norm(net)), [])
            pad_group = {}
            for gi, g in enumerate(groups):
                for nm in g:
                    pad_group[nm.split("#")[0]] = gi
            own = [(L, g, kind, ident) for L in self.layers for (g, n, kind, ident) in self.items[L] if n == net]
            parent = list(range(len(own)))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i

            def union(i, j):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
            by_layer = defaultdict(list)
            for i, it in enumerate(own):
                by_layer[it[0]].append(i)
            for L, ix in by_layer.items():
                geoms = [own[i][1] for i in ix]
                pr = STRtree(geoms).query(geoms, predicate="intersects")
                for u, v in zip(pr[0], pr[1]):
                    if u != v:
                        union(ix[u], ix[v])
            first = {}
            for i, (L, g, kind, ident) in enumerate(own):
                if kind in ("via", "pad_th", "pad_smd") and ident:
                    if ident in first:
                        union(i, first[ident])
                    else:
                        first[ident] = i
            comp_groups = defaultdict(set)
            for i, (L, g, kind, ident) in enumerate(own):
                if kind in ("pad_smd", "pad_th") and ident in pad_group:
                    comp_groups[find(i)].add(pad_group[ident])
            land = defaultdict(lambda: {"fill": [], "track": [], "fill_layers": set()})
            ambiguous = 0
            for i, (L, g, kind, ident) in enumerate(own):
                gs = comp_groups.get(find(i), set())
                if len(gs) != 1:
                    ambiguous += len(gs) > 1
                    continue
                gi = next(iter(gs))
                if kind == "fill":
                    land[gi]["fill"].append((L, g))
                    land[gi]["fill_layers"].add(L)
                elif kind == "track":
                    land[gi]["track"].append((L, g))
            pads_xy = {p["ref"] + "." + p["num"]: (p["x"], p["y"]) for p in self.G["pads"] if p["net"] == net}
            self.isl[r["id"]] = {"net": net, "groups": groups, "pad_group": pad_group, "land": land,
                                 "ambiguous_items": ambiguous, "pads_xy": pads_xy}
            log(r["id"], "islands", len(groups), "own items", len(own), "items in multi-group components", ambiguous)

    def build_base(self):
        """packed rasters per layer: non-fill / fill copper of FIELD_A, FIELD_B (target nets excluded) and OTHER,
        every SMD pad, each target net (non-fill / fill); holes."""
        t = time.time()
        self.base = {}
        rids = [r["id"] for r in self.all_rails]
        for L in self.layers:
            m = {k: self.R.empty() for k in ["nf_DOM_FIELD_A", "nf_DOM_FIELD_B", "nf_OTHER", "f_DOM_FIELD_A", "f_DOM_FIELD_B",
                                             "f_OTHER", "smd"] + [f"tnf_{x}" for x in rids] + [f"tf_{x}" for x in rids]}
            for (g, n, kind, ident) in self.items[L]:
                if kind == "pad_smd":
                    self.R.fill_geom(m["smd"], g)
                pre = "f_" if kind == "fill" else "nf_"
                if n in self.rid_of:
                    self.R.fill_geom(m["t" + pre + self.rid_of[n]], g)
                else:
                    self.R.fill_geom(m[pre + self.fkey(n)], g)
            if L == IN3:
                for g in self.core12:
                    self.R.fill_geom(m["f_OTHER"], g)
            self.base[L] = {k: self.R.pack(v) for k, v in m.items()}
        hm = {"h_excl": self.R.empty()}
        for x in rids:
            hm["h_" + x] = self.R.empty()
        for g, n in self.holes:
            self.R.fill_geom(hm["h_" + self.rid_of[n]] if n in self.rid_of else hm["h_excl"], g)
        self.base["holes"] = {k: self.R.pack(v) for k, v in hm.items()}
        o = self.R.empty()
        o[:] = 1
        self.R.fill_geom(o, self.board, 0)
        self.outside = o
        log(f"base rasters built in {time.time() - t:.0f}s")

    def territory(self):
        doms = sorted({self.dom(n) for n in self.G["nets"]} | {"NETLESS"})
        self.dom_ids = {d: i + 1 for i, d in enumerate(doms)}
        ter = np.zeros((self.R.ny, self.R.nx), np.int16)
        by = defaultdict(list)
        for L in ("In1.Cu", "In4.Cu"):
            for (g, n, kind, ident) in self.items[L]:
                if kind == "fill" and n:
                    by[self.dom(n)].append(g)
        for d, gs in by.items():
            img = self.R.empty()
            for g in gs:
                self.R.fill_geom(img, g)
            ter[img > 0] = self.dom_ids[d]
        self.ter = ter

    # ------------------------------------------------------------------ per-net masks
    def U(self, L, key):
        return self.R.unpack(self.base[L][key])

    def masks(self, rid, L, fills_same):
        """(same-domain other-net copper, cross-domain copper) on layer L for target rid, incl. new copper."""
        r = self.rail[rid]
        d = r["domain"]
        d2 = [x for x in FIELD_DOMS if x != d][0]
        same = self.U(L, "nf_" + d)
        if fills_same:
            same |= self.U(L, "f_" + d)
        cross = self.U(L, "nf_OTHER") | self.U(L, "f_OTHER") | self.U(L, "nf_" + d2) | self.U(L, "f_" + d2)
        for q in self.all_rails:
            if q["id"] == rid:
                continue
            if q["domain"] == d:
                same |= self.U(L, "tnf_" + q["id"])
                if fills_same:
                    same |= self.U(L, "tf_" + q["id"])
            else:
                cross |= self.U(L, "tnf_" + q["id"]) | self.U(L, "tf_" + q["id"])
        net = r["board_net"]
        for it in self.new_items:
            if it["net"] == net:
                continue
            tgt = same if self.dom(it["net"]) == d else cross
            for g in it["layers"].get(L, []):
                self.R.fill_geom(tgt, g)
        return same, cross

    def hole_masks(self, rid):
        net = self.rail[rid]["board_net"]
        oth = self.R.unpack(self.base["holes"]["h_excl"])
        own = self.R.unpack(self.base["holes"]["h_" + rid])
        for q in self.all_rails:
            if q["id"] != rid:
                oth |= self.R.unpack(self.base["holes"]["h_" + q["id"]])
        for it in self.new_items:
            for g in it.get("holes", []):
                self.R.fill_geom(own if it["net"] == net else oth, g)
        return oth, own

    def hard_mask(self, L, net, for_vias):
        img = self.R.empty()
        nn = norm(net)
        for (g, ex, name, bt, bv) in self.hard[L]:
            if ex is not None and nn in ex:
                continue
            if bv if for_vias else bt:
                self.R.fill_geom(img, g)
        return img

    def in3_hw(self, rid):
        net = self.rail[rid]["board_net"]
        same, cross = self.masks(rid, IN3, True)
        oth_h, own_h = self.hole_masks(rid)
        hw = edt_mm(same, H) - CL_SAME
        np.minimum(hw, edt_mm(cross, H) - CL_CROSS, out=hw)
        np.minimum(hw, edt_mm(oth_h, H) - CL_HOLE, out=hw)
        np.minimum(hw, edt_mm(self.hard_mask(IN3, net, False), H), out=hw)
        np.minimum(hw, edt_mm(self.outside, H) - CL_EDGE, out=hw)
        hw -= MARGIN
        return hw

    def via_slack(self, rid):
        net = self.rail[rid]["board_net"]
        r = self.via_d / 2
        slack = np.full((self.R.ny, self.R.nx), 1e3, np.float32)
        for L in self.layers:
            same, cross = self.masks(rid, L, False)
            np.minimum(slack, edt_mm(same, H) - (r + CL_SAME), out=slack)
            np.minimum(slack, edt_mm(cross, H) - (r + CL_CROSS), out=slack)
            del same, cross
            np.minimum(slack, edt_mm(self.U(L, "smd"), H) - (r + CL_SMD), out=slack)
            np.minimum(slack, edt_mm(self.hard_mask(L, net, True), H) - r, out=slack)
        oth_h, own_h = self.hole_masks(rid)
        np.minimum(slack, edt_mm(oth_h, H) - max(r + CL_HOLE, self.via_drill / 2 + H2H), out=slack)
        np.minimum(slack, edt_mm(own_h, H) - (self.via_drill / 2 + H2H), out=slack)
        ends = self.R.empty()
        for (x, y) in self.own_track_ends(net):
            cy, cx = self.R.to_cell(x, y)
            if 0 <= cy < self.R.ny and 0 <= cx < self.R.nx:
                ends[cy, cx] = 1
        np.minimum(slack, edt_mm(ends, H) - (r + END_KEEP), out=slack)
        np.minimum(slack, edt_mm(self.outside, H) - (r + CL_EDGE), out=slack)
        slack -= 0.07
        return slack

    # ------------------------------------------------------------------ exact checks
    def new_near(self, P, rr):
        for it in self.new_items:
            b = it["bbox"]
            if b[0] - rr <= P.x <= b[2] + rr and b[1] - rr <= P.y <= b[3] + rr:
                yield it

    def add_new(self, net, kind, layers, holes=()):
        allg = [g for gs in layers.values() for g in gs] + list(holes)
        bb = unary_union(allg).bounds
        self.new_items.append({"net": net, "kind": kind, "layers": layers, "holes": list(holes), "bbox": bb})

    def exact_index(self, net, layer):
        d = self.dom(net)
        geoms, clr, names = [], [], []
        for (g, n, kind, ident) in self.items[layer]:
            if n == net:
                continue
            if not n:
                geoms.append(g)
                clr.append(CL_CROSS)
                names.append(("", kind, ident))
                continue
            same = self.dom(n) == d
            geoms.append(g)
            clr.append(CL_SAME if same else CL_CROSS)
            names.append((n, kind, ident))
        if layer == IN3:
            for g in self.core12:
                geoms.append(g)
                clr.append(CL_CROSS)
                names.append(("/CORE_1V2", "zone_outline", ""))
        for it in self.new_items:
            if it["net"] != net:
                for g in it["layers"].get(layer, []):
                    geoms.append(g)
                    clr.append(CL_SAME if self.dom(it["net"]) == d else CL_CROSS)
                    names.append((it["net"], "new_" + it["kind"], ""))
                for g in it.get("holes", []):
                    geoms.append(g)
                    clr.append(CL_HOLE)
                    names.append((it["net"], "new_hole", ""))
        for g, n in self.holes:
            if n != net:
                geoms.append(g)
                clr.append(CL_HOLE)
                names.append((n, "hole", ""))
        nn = norm(net)
        for (g, ex, name, bt, bv) in self.hard[layer]:
            if (ex is None or nn not in ex) and bt:
                geoms.append(g)
                clr.append(0.0)
                names.append(("", "area", name))
        geoms.append(box(*self.board.buffer(5).bounds).difference(self.board))
        clr.append(CL_EDGE)
        names.append(("", "edge", ""))
        return {"tree": STRtree(geoms), "geoms": np.array(geoms, dtype=object), "clr": np.array(clr), "names": names}

    def seg_avail(self, idx, a, b, search=3.0):
        s = LineString([a, b]) if math.dist(a, b) > 1e-6 else Point(a)
        cand = idx["tree"].query(s.buffer(search + CL_CROSS))
        if len(cand) == 0:
            return search, None
        dist = shapely.distance(s, idx["geoms"][cand]) - idx["clr"][cand]
        k = int(np.argmin(dist))
        return float(min(dist[k], search)), idx["names"][cand[k]]

    def own_track_ends(self, net):
        if not hasattr(self, "_ends"):
            self._ends = defaultdict(list)
            for t in self.G["tracks"]:
                self._ends[t["net"]].append(tuple(t["a"]))
                self._ends[t["net"]].append(tuple(t["b"]))
        return self._ends.get(net, [])

    def _layer_tree(self, L):
        if not hasattr(self, "_ltrees"):
            self._ltrees = {}
        if L not in self._ltrees:
            self._ltrees[L] = STRtree([it[0] for it in self.items[L]])
        return self._ltrees[L]

    def via_ok_exact(self, net, x, y):
        d = self.dom(net)
        r = self.via_d / 2
        P = Point(x, y)
        worst, why = 1e9, None

        def upd(s, w):
            nonlocal worst, why
            if s < worst:
                worst, why = s, w
        for L in self.layers:
            for i in self._layer_tree(L).query(P.buffer(1.5)):
                g, n, kind, ident = self.items[L][i]
                if n == net:
                    if kind == "pad_smd":
                        upd(P.distance(g) - (r + CL_SMD), (L, n, kind, ident))
                    continue
                if not n:
                    upd(P.distance(g) - (r + CL_CROSS), (L, n, kind, ident))
                elif self.dom(n) == d:
                    if kind == "pad_smd":
                        upd(P.distance(g) - (r + max(CL_SAME, CL_SMD)), (L, n, kind, ident))
                    elif kind != "fill":
                        upd(P.distance(g) - (r + CL_SAME), (L, n, kind, ident))
                else:
                    upd(P.distance(g) - (r + CL_CROSS), (L, n, kind, ident))
            if L == IN3:
                for g in self.core12:
                    upd(P.distance(g) - (r + CL_CROSS), (L, "/CORE_1V2", "zone_outline", ""))
            nn = norm(net)
            for (g, ex, name, bt, bv) in self.hard[L]:
                if bv and (ex is None or nn not in ex):
                    upd(P.distance(g) - r, (L, "", "area", name))
        for it in self.new_near(P, 2.0):
            same_net = it["net"] == net
            for L, gs in it["layers"].items():
                if same_net:
                    continue
                for g in gs:
                    upd(P.distance(g) - (r + (CL_SAME if self.dom(it["net"]) == d else CL_CROSS)), (L, it["net"], "new_" + it["kind"], ""))
            for g in it.get("holes", []):
                upd(P.distance(g) - (self.via_drill / 2 + H2H if same_net else max(r + CL_HOLE, self.via_drill / 2 + H2H)),
                    ("hole", it["net"], "new_hole", ""))
        if not hasattr(self, "_htree"):
            self._htree = STRtree([g for g, n in self.holes])
        for i in self._htree.query(P.buffer(1.5)):
            g, n = self.holes[i]
            upd(P.distance(g) - (self.via_drill / 2 + H2H if n == net else max(r + CL_HOLE, self.via_drill / 2 + H2H)),
                ("hole", n, "hole", ""))
        for (ex_, ey_) in self.own_track_ends(net):
            if abs(ex_ - x) <= r + END_KEEP and abs(ey_ - y) <= r + END_KEEP:
                upd(math.hypot(ex_ - x, ey_ - y) - (r + END_KEEP), ("ends", net, "own_track_end", ""))
        se = self.board.exterior.distance(P) * (1 if self.board.contains(P) else -1)
        upd(se - (r + CL_EDGE), ("edge", "", "edge", ""))
        return worst >= 0.0, worst, why

    # ------------------------------------------------------------------ routing graph
    def coarse(self, a):
        ny, nx = a.shape[0] // K, a.shape[1] // K
        return a[:ny * K, :nx * K].reshape(ny, K, nx, K).min(axis=(1, 3))

    def cxy(self, cy, cx):
        """world point of coarse cell (cy, cx) = fine cell (cy*K, cx*K)."""
        return (self.R.x0 + cx * K * H, self.R.y0 + cy * K * H)

    def ccell(self, x, y):
        """coarse cell holding the fine cell nearest to (x, y) (same fine->coarse mapping as coarse())."""
        return (int(round((y - self.R.y0) / H)) // K, int(round((x - self.R.x0) / H)) // K)

    def build_graph(self, hwc, costc, wcap, wmin=W_MIN):
        ny, nx = hwc.shape
        ok = hwc >= wmin / 2
        idx = -np.ones((ny, nx), np.int64)
        nn = int(ok.sum())
        idx[ok] = np.arange(nn)
        c = np.where(ok, costc / np.maximum(np.minimum(2 * hwc, wcap), 1e-3), 0).astype(np.float64)
        rows, cols, data = [], [], []
        gstep = K * H
        for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
            ys1 = ny - dy
            xs0, xs1 = max(0, -dx), nx - max(0, dx)
            a_ = idx[0:ys1, xs0:xs1]
            b_ = idx[dy:ys1 + dy, xs0 + dx:xs1 + dx]
            m = (a_ >= 0) & (b_ >= 0)
            if dy and dx:
                m &= (idx[dy:ys1 + dy, xs0:xs1] >= 0) & (idx[0:ys1, xs0 + dx:xs1 + dx] >= 0)
            ca = c[0:ys1, xs0:xs1][m]
            cb = c[dy:ys1 + dy, xs0 + dx:xs1 + dx][m]
            rows.append(a_[m])
            cols.append(b_[m])
            data.append(gstep * math.hypot(dy, dx) * 0.5 * (ca + cb))
        A = sp.coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))), shape=(nn, nn)).tocsr()
        return A, idx, np.argwhere(ok)

    # ------------------------------------------------------------------ flow
    def run(self):
        self.build()
        order = {"return": 0, "supply": 1}
        rails = sorted(self.rails, key=lambda r: (r["domain"], order[r["role"]]))
        if getattr(self.a, "order", ""):
            want = [x for x in self.a.order.split(",") if x]
            rails = sorted(rails, key=lambda r: want.index(r["id"]) if r["id"] in want else 99)
        self.design["net_order"] = [r["id"] for r in rails]
        for r in rails:
            self.design_net(r)
        self.post_snap()
        self.write()

    def resolve(self, r, pads_spec):
        pg = self.isl[r["id"]]["pad_group"]
        out = []
        for ref, pin in pads_spec:
            for nm in pg:
                rr, pp = nm.split(".", 1)
                if rr == ref and (pin == "*" or pp == pin):
                    out.append(nm)
        return out

    def design_net(self, r):
        rid, net = r["id"], r["board_net"]
        I = self.isl[rid]
        groups = I["groups"]
        log(f"== {rid} {norm(net)}: {len(groups)} islands")
        clusters = [dict(c, pad_names=self.resolve(r, c["pads"])) for c in r["clusters"]]
        for c in clusters:
            c["groups"] = sorted({I["pad_group"][p] for p in c["pad_names"]})
        src_pads = self.resolve(r, r["source"]["pads"])
        src_groups = sorted({I["pad_group"][p] for p in src_pads})
        g_amps, g_names = defaultdict(float), defaultdict(list)
        for c in clusters:
            for gi in c["groups"]:
                g_amps[gi] += c["amps"] / len(c["groups"])
                g_names[gi].append(c["name"])
        an = {"net": net, "role": r["role"], "domain": r["domain"], "design_a": r["design_a"], "limit_a": r["limit_a"],
              "source": {"name": r["source"]["name"], "pads": src_pads, "islands": src_groups},
              "clusters": [{"name": c["name"], "amps": c["amps"], "basis": c["basis"], "cite": c["cite"],
                            "pads": c["pad_names"], "islands": c["groups"]} for c in clusters],
              "clusters_sum_a": math.fsum(c["amps"] for c in clusters),
              "share_rule": "cluster current = documented maximum (basis/cite); segment current = explicit downstream sum without caps", "islands": []}
        hw = self.in3_hw(rid)
        slack = self.via_slack(rid)
        # never under another isolated domain's plane (AI, AO0/1, CAN, RS485, CONTACT, CHASSIS): only own territory,
        # no plane, LOGIC and the other field domain may be crossed on In3
        allowed = {self.dom_ids.get(x, -9) for x in ("DOM_LOGIC", "DOM_FIELD_A", "DOM_FIELD_B")
                   + tuple(d for d in (getattr(self.a, "allow_domains", "") or "").split(",") if d)}
        forbid = (self.ter > 0) & ~np.isin(self.ter, list(allowed))
        hw[forbid] = -1.0
        an["forbidden_in3_territory_mm2"] = round(float(forbid.sum()) * H * H, 0)
        hwc = self.coarse(hw)
        feas_c = hwc >= W_MIN / 2
        feas_f = np.zeros(hw.shape, bool)
        feas_f[:feas_c.shape[0] * K, :feas_c.shape[1] * K] = np.repeat(np.repeat(feas_c, K, 0), K, 1)
        legal = (slack >= 0) & feas_f
        lab, ncomp = ndi.label(feas_c)
        csize = np.bincount(lab.ravel())
        info = {}
        members = defaultdict(set)
        for gi, g in enumerate(groups):
            land = I["land"].get(gi, {"fill": [], "track": [], "fill_layers": set()})
            lm = self.R.empty()
            for (L, gg) in land["fill"]:
                self.R.fill_geom(lm, gg.buffer(-0.05) if gg.area > 0.05 else gg)
            # a via on a thin track carries current well only near the island's terminal pads (source, cluster loads
            # or, for an island without a cluster, its own pads). --track-land-mm > 0 restricts track landings to that
            # radius (current-carrying design, default of the rip-up proposal); 0 lets a via land anywhere on the
            # island's tracks (completion join; the via picker still prefers the sites nearest the terminal pads and
            # each via group reports its landing distance)
            tl = self.R.empty()
            for (L, gg) in land["track"]:
                self.R.fill_geom(tl, gg.buffer(-0.03))
            if tl.any() and self.track_land > 0:
                term = [p.split("#")[0] for p in (src_pads if gi in src_groups else [])]
                term += [p.split("#")[0] for c in clusters if gi in c["groups"] for p in c["pad_names"]]
                term = term or [p.split("#")[0] for p in g]
                near = self.R.empty()
                for p in term:
                    if p in I["pads_xy"]:
                        x, y = I["pads_xy"][p]
                        cv2.circle(near, (int(round((x - self.R.x0) / H)), int(round((y - self.R.y0) / H))),
                                   int(self.track_land / H), 1, -1)
                lm |= tl & near
            elif tl.any():
                lm |= tl
            cand = (lm > 0) & legal
            ys, xs = np.nonzero(cand)
            comps = defaultdict(int)
            if len(ys):
                ll = lab[np.minimum(ys // K, lab.shape[0] - 1), np.minimum(xs // K, lab.shape[1] - 1)]
                for c_, n_ in zip(*np.unique(ll[ll > 0], return_counts=True)):
                    comps[int(c_)] = int(n_)
                    members[int(c_)].add(gi)
            xy = [I["pads_xy"][p.split("#")[0]] for p in g if p.split("#")[0] in I["pads_xy"]]
            c = (sum(x for x, y in xy) / max(1, len(xy)), sum(y for x, y in xy) / max(1, len(xy)))
            info[gi] = {"cand": cand, "n_cand": int(len(ys)), "centroid": c, "pads": [p.split("#")[0] for p in g], "comps": comps}
            an["islands"].append({"island": gi, "pads": len(g), "pad_examples": info[gi]["pads"][:6],
                                  "centroid": [round(c[0], 2), round(c[1], 2)], "amps": round(g_amps.get(gi, 0.0), 3),
                                  "clusters": g_names.get(gi, []), "is_source": gi in src_groups,
                                  "inner_fill_layers": sorted(land["fill_layers"]),
                                  "fill_area_mm2": round(sum(gg.area for L, gg in land["fill"]), 1),
                                  "track_landing_mm2": round(sum(gg.area for L, gg in land["track"]), 2),
                                  "legal_via_area_mm2": round(info[gi]["n_cand"] * H * H, 2),
                                  "in3_components": {str(k): {"via_cells": v, "area_mm2": round(float(csize[k]) * (K * H) ** 2, 1)}
                                                     for k, v in sorted(comps.items(), key=lambda kv: -csize[kv[0]])[:4]}})
        brd = self.outside == 0
        nb = float(brd.sum())
        an["in3_free_fraction_for_width_mm"] = {str(w): round(float(((hw >= w / 2) & brd).sum()) / nb, 3)
                                                for w in (0.3, 0.5, 1.0, 2.0, 3.0, 4.0)}
        an["in3_components_at_0p3mm"] = {"count": int(ncomp), "largest_mm2": [round(float(v) * (K * H) ** 2, 1)
                                                                              for v in sorted(csize[1:], reverse=True)[:5]]}
        self.analysis["nets"][rid] = an
        des = {"net": net, "role": r["role"], "domain": r["domain"], "design_a": r["design_a"], "segments": [],
               "via_groups": [], "unreached": [], "drops": [], "notes": [], "relay_islands": []}
        des["current_model"] = {"preflight": self.current_preflight["rails"][rid],
            "source_and_positive_load_pads_resolved": bool(src_pads) and all(c["pad_names"] for c in clusters if c["amps"] > 0),
            "source_local_load_a": 0.0, "full_rail_qualified": False}
        self.design["nets"][rid] = des
        if self.terminal_mode:
            # current-carrying design: every terminal (the source pads, and each load cluster on each island it touches)
            # is its own node with vias near ITS pads, so no current is left to the existing thin copper of an island
            info, members, g_amps, g_names, src_groups, groups, terms = self.terminal_nodes(r, I, clusters, src_pads, legal, lab)
            des["terminals"] = terms
            des["notes"].append(f"terminal mode: {len(terms)} terminals; vias within {self.track_land} mm (tracks) / "
                                f"{FILL_LAND_MM} mm (plane fill) of each terminal's pads; zero-current islands not joined")
        if not src_groups:
            des["notes"].append("source pads not found")
            return
        src_gi = src_groups[0]
        if len(src_groups) > 1:
            des["notes"].append(f"source pads span islands {src_groups}; island {src_gi} is the root")
        # ---- island <-> In3-component reachability (an island's own copper relays between components)
        reached = {src_gi: None}
        comp_entry, comp_targets = {}, defaultdict(list)
        queue = [src_gi]
        qi = 0
        while qi < len(queue):
            Ii = queue[qi]
            qi += 1
            for C in sorted(info[Ii]["comps"], key=lambda c_: -csize[c_]):
                if C in comp_entry:
                    continue
                comp_entry[C] = Ii
                for J in sorted(members[C], key=lambda j: (-g_amps.get(j, 0.0), math.dist(info[j]["centroid"], info[Ii]["centroid"]))):
                    if J not in reached:
                        reached[J] = (Ii, C)
                        comp_targets[C].append(J)
                        queue.append(J)
        children = defaultdict(list)
        for J, v in reached.items():
            if v:
                children[v[0]].append(J)
        down = {}
        for J in reversed(queue):
            down[J] = g_amps.get(J, 0.0) + sum(down[c_] for c_ in children[J])
        for J in range(len(groups)):
            if J in reached:
                continue
            rec = {"island": J, "amps": round(g_amps.get(J, 0.0), 3), "pads": info[J]["pads"][:8]}
            if info[J]["n_cand"] == 0:
                rec["reason"] = ("no legal via site on this island's own copper (single SMD pad without track/fill, or boxed): "
                                 "needs a stitch via / outer-layer join")
            else:
                rec["reason"] = "its legal via sites lie only in In3 free-space pockets that no reached island shares (In3 blocked)"
                rec["in3_components"] = {str(k): int(v) for k, v in info[J]["comps"].items()}
            des["unreached"].append(rec)
        # ---- cost map
        terc = self.ter[:hwc.shape[0] * K:K, :hwc.shape[1] * K:K]
        own_id, logic_id = self.dom_ids.get(r["domain"], -1), self.dom_ids.get("DOM_LOGIC", -1)
        other_field = self.dom_ids.get([x for x in FIELD_DOMS if x != r["domain"]][0], -2)
        cost = np.full(hwc.shape, 1.2)
        cost[terc > 0] = 4.0
        cost[terc == other_field] = 2.5
        cost[terc == logic_id] = 1.5
        cost[terc == own_id] = 1.0
        if self.pool:
            if not hasattr(self, "_pool_pen"):
                pm_ = self.R.empty()
                for (g, n, kind, ident) in self.pool:
                    self.R.fill_geom(pm_, g)
                self._pool_pen = self.coarse(edt_mm(pm_, H))
            cost[self._pool_pen < 0.75] *= RIP_PENALTY
            des["notes"].append(f"rip-up proposal mode: cells within 0.75 mm of a foreign In3 track cost x{RIP_PENALTY}")
        if getattr(self, "soft_res", None):
            sm = self.R.empty()
            for nm_, g in self.soft_res:
                self.R.fill_geom(sm, g)
            cost[self.coarse(sm.astype(np.float32)) > 0] *= 5.0
            des["notes"].append(f"what-if: {len(self.soft_res)} In3 reservation areas ({getattr(self.a, 'allow_reservations', '')}) crossable at x5 cost")
        pair_net = self.rail[r["pair"]]["board_net"] if r.get("pair") in self.rail else None
        pm = self.R.empty()
        npair = 0
        for it in self.new_items:
            if it["net"] == pair_net and it["kind"] == "track":
                for g in it["layers"].get(IN3, []):
                    self.R.fill_geom(pm, g)
                    npair += 1
        if npair:
            dpm = self.coarse(edt_mm(pm, H))
            cost[(dpm > 0) & (dpm <= 3.5)] *= 0.85
            des["notes"].append("side by side: cost x0.85 within 3.5 mm of the partner net's In3 copper")
        graphs = {}

        def graph_for(wcap, wmin=W_MIN):
            q = min((0.5, 1.0, 2.0, 3.0, 4.0, 5.0), key=lambda v: (v < wcap - 1e-9, abs(v - wcap)))
            wm = round(max(W_MIN, min(wmin, 5.0)), 2)
            if (q, wm) not in graphs:
                graphs[(q, wm)] = self.build_graph(hwc, cost, q, wmin=wm)
            return graphs[(q, wm)]
        # ---- one tree per In3 component, rooted at the island it was entered from
        cts = []
        connected = {src_gi}
        for C, E in comp_entry.items():
            tg = comp_targets.get(C, [])
            if not tg:
                continue
            if E not in connected:
                for J in tg:
                    des["unreached"].append({"island": J, "amps": round(down[J], 3), "pads": info[J]["pads"][:8],
                                             "reason": f"its In3 component {C} is entered from island {E}, which is not connected"})
                continue
            I_C = math.fsum(down[J] for J in tg)
            n_root = required_vias(I_C, self.amps_per_via)
            pads_E = [p.split("#")[0] for p in src_pads] if E == src_gi else info[E]["pads"]
            root = self.pick_vias(net, info[E], max(n_root, 2), I, pads_E, hw, lab, C, w_need=ipc_width_mm(I_C))
            root.update({"island": E, "component": C, "root": True, "amps": round(I_C, 3), "n_req": n_root,
                         "name": ("SOURCE " + r["source"]["name"] if E == src_gi else f"relay island {E} ({'; '.join(g_names.get(E, [])) or 'plane region'})")
                         + f" -> In3 component {C}"})
            ct = {"C": C, "entry": E, "root": root, "paths": [], "vgroups": [root]}
            cts.append(ct)
            if not root["vias"]:
                for J in tg:
                    des["unreached"].append({"island": J, "amps": round(down[J], 3), "pads": info[J]["pads"][:8],
                                             "reason": f"entry island {E} has no exact-legal via site in In3 component {C}",
                                             "blocker": root.get("blocker")})
                continue
            tree = {self.ccell(x, y) for (x, y) in root["vias"]}
            for J in sorted(tg, key=lambda j: (-down[j], math.dist(info[j]["centroid"], info[E]["centroid"]))):
                n_req = required_vias(down[J], self.amps_per_via)
                vg = self.pick_vias(net, info[J], max(n_req, 2), I, info[J]["pads"], hw, lab, C,
                                    w_need=ipc_width_mm(down[J]))
                vg.update({"island": J, "component": C, "amps": round(down[J], 3), "n_req": n_req,
                           "name": ("; ".join(g_names.get(J, [])) or f"island {J} (plane region, no current share)")
                           + (f" [relays {round(down[J] - g_amps.get(J, 0.0), 3)} A]" if children[J] else "")})
                if not vg["vias"]:
                    des["unreached"].append({"island": J, "amps": round(down[J], 3), "pads": info[J]["pads"][:8],
                                             "reason": f"every candidate via in component {C} failed the exact check",
                                             "blocker": vg.get("blocker")})
                    continue
                # width tiers: the IPC-2152 width of this branch's current first (no neck narrower than it), then
                # 80 % / 60 % of it, then the 0.3 mm floor; the first tier with a path wins and is recorded
                w_ipc = max(ipc_width_mm(down[J]), W_MIN)
                tiers = sorted({round(max(W_MIN, f * w_ipc), 2) for f in (1.0, 0.8, 0.6)} | {W_MIN}, reverse=True)
                best = None
                for wmin in tiers:
                    A, idx, rc = graph_for(w_ipc, wmin)
                    srcs = sorted({int(idx[c_]) for c_ in tree if self._in(idx, c_) and idx[c_] >= 0})
                    tn = sorted({int(idx[c_]) for c_ in (self.ccell(x, y) for x, y in vg["vias"]) if self._in(idx, c_) and idx[c_] >= 0})
                    if not srcs or not tn:
                        continue
                    dist, pred, _ = csg.dijkstra(A, directed=False, indices=np.array(srcs), min_only=True, return_predecessors=True)
                    b_ = min(tn, key=lambda n_: dist[n_])
                    if np.isfinite(dist[b_]):
                        best = b_
                        break
                if best is None:
                    des["unreached"].append({"island": J, "amps": round(down[J], 3), "pads": info[J]["pads"][:8],
                                             "reason": "tree or via cells off the In3 grid / no path at the 0.3 mm floor"})
                    continue
                vg["routed_min_width_mm"] = wmin
                vg["ipc_width_mm"] = round(w_ipc, 2)
                seq = [best]
                while pred[seq[-1]] >= 0:
                    seq.append(int(pred[seq[-1]]))
                cells = [tuple(int(v) for v in rc[n_]) for n_ in reversed(seq)]
                plen = sum(math.dist(self.cxy(*a_), self.cxy(*b_)) for a_, b_ in zip(cells, cells[1:]))
                if down[J] <= 0 and (plen > self.a.max_island_branch or self.a.ripup_proposal):
                    des["unreached"].append({"island": J, "amps": 0.0, "pads": info[J]["pads"][:8],
                                             "reason": (f"no current share and the In3 branch would be {plen:.0f} mm long (> {self.a.max_island_branch:.0f} mm): "
                                                        "In3 kept free; left for plane stitching or a later bridge") if not self.a.ripup_proposal else
                                                       "no current share: not part of the rip-up proposal (join after the trunks, by stitching or a short branch)"})
                    continue
                connected.add(J)
                ct["paths"].append({"cells": cells, "island": J, "amps": down[J]})
                ct["vgroups"].append(vg)
                tree |= set(cells) | {self.ccell(x, y) for (x, y) in vg["vias"]}
                log(f"  {rid} C{C} {E}->{J} ({down[J]:.3f} A, {len(vg['vias'])}/{n_req} vias): {len(cells)} cells")
        des["relay_islands"] = [{"island": J, "relays_a": round(down[J] - g_amps.get(J, 0.0), 3), "pads": info[J]["pads"][:6]}
                                for J in reached if children[J] and J != src_gi]
        # ---- blocked analysis for unreached islands that carry current (rip-up proposal)
        all_cells = set()
        for ct in cts:
            for p in ct["paths"]:
                all_cells |= set(p["cells"])
            for vg in ct["vgroups"]:
                all_cells |= {self.ccell(x, y) for (x, y) in vg["vias"]}
        if not all_cells:
            all_cells = {self.ccell(*xy) for xy in self.cells_xy(info[src_gi]["cand"], 400)}
        for u in des["unreached"]:
            if u.get("amps", 0) > 0 and info[u["island"]]["n_cand"] > 0:
                tc = {self.ccell(*xy) for xy in self.cells_xy(info[u["island"]]["cand"], 400)}
                u["blocked"] = self.blocked_analysis(rid, all_cells, tc, max(ipc_width_mm(u["amps"]), W_MIN))
                log(f"  {rid} island {u['island']} ({u['amps']} A) unreached: {u['blocked'].get('result')}, "
                    f"{u['blocked'].get('tracks')} In3 tracks on the cheapest path")
        # currents through the connected tree only (an unconnected descendant draws nothing through it)
        down_eff = {}
        for J in reversed(queue):
            if J in connected:
                down_eff[J] = g_amps.get(J, 0.0) + sum(down_eff.get(c_, 0.0) for c_ in children[J])
        for ct in cts:
            for p in ct["paths"]:
                p["amps"] = down_eff.get(p["island"], 0.0)
            for vg in ct["vgroups"][1:]:
                vg["amps"] = down_eff.get(vg["island"], 0.0)
                vg["n_req"] = required_vias(vg["amps"], self.amps_per_via)
            ct["root"]["amps"] = math.fsum(p["amps"] for p in ct["paths"])
            ct["root"]["n_req"] = required_vias(ct["root"]["amps"], self.amps_per_via)
        des["connected_islands"] = sorted(connected)
        des["current_reaching_source_a"] = down_eff.get(src_gi, 0.0) - g_amps.get(src_gi, 0.0)
        des["current_model"]["source_local_load_a"] = g_amps.get(src_gi, 0.0)
        self.finalize(r, des, cts, hw, down_eff, reached, src_gi)
        self.plot(rid, hwc, lab, cts, des, info, reached)

    def terminal_nodes(self, r, I, clusters, src_pads, legal, lab):
        terms = [("SOURCE " + r["source"]["name"], [p.split("#")[0] for p in src_pads], 0.0)]
        for c in clusters:
            if not c["pad_names"] or c["amps"] < getattr(self.a, "min_cluster_amps", 0.05):
                continue   # quiescent IC grounds etc.: joined by plane stitching, not by trunks
            by = defaultdict(list)
            for p in c["pad_names"]:
                by[I["pad_group"][p]].append(p.split("#")[0])
            for gi, ps in sorted(by.items()):
                terms.append((c["name"] + (f" [island {gi}]" if len(by) > 1 else ""), ps, c["amps"] * len(ps) / len(c["pad_names"])))
        info, members, g_amps, g_names, rec = {}, defaultdict(set), {}, defaultdict(list), []
        csz = np.bincount(lab.ravel())
        main_c = int(np.argmax(csz[1:]) + 1) if len(csz) > 1 else -1
        for k, (name, pads, amps) in enumerate(terms):
            gi = I["pad_group"].get(pads[0])
            land = I["land"].get(gi, {"fill": [], "track": [], "fill_layers": set()})
            fl = self.R.empty()
            for (L, gg) in land["fill"]:
                self.R.fill_geom(fl, gg.buffer(-0.05) if gg.area > 0.05 else gg)
            tl = self.R.empty()
            for (L, gg) in land["track"]:
                self.R.fill_geom(tl, gg.buffer(-0.03))
            # landing escalation: the terminal's own copper within 1x, 2x, 4x, 8x the landing radius, until a legal via
            # site reaches the main In3 free-space component (the copper between the pads and that site is the
            # EXISTING thin copper: the radius used is reported per terminal)
            for mult in (1, 2, 4, 8):
                nt, nf = self.R.empty(), self.R.empty()
                for p in pads:
                    if p in I["pads_xy"]:
                        x, y = I["pads_xy"][p]
                        c0 = (int(round((x - self.R.x0) / H)), int(round((y - self.R.y0) / H)))
                        cv2.circle(nt, c0, int(mult * self.track_land / H), 1, -1)
                        cv2.circle(nf, c0, int(mult * FILL_LAND_MM / H), 1, -1)
                lm = (fl & nf) | (tl & nt)
                cand = (lm > 0) & legal
                ys, xs = np.nonzero(cand)
                if len(ys) and main_c > 0 and (lab[np.minimum(ys // K, lab.shape[0] - 1), np.minimum(xs // K, lab.shape[1] - 1)] == main_c).any():
                    break
            land_r = mult * self.track_land
            comps = defaultdict(int)
            if len(ys):
                ll = lab[np.minimum(ys // K, lab.shape[0] - 1), np.minimum(xs // K, lab.shape[1] - 1)]
                for c_, n_ in zip(*np.unique(ll[ll > 0], return_counts=True)):
                    comps[int(c_)] = int(n_)
                    members[int(c_)].add(k)
            xy = [I["pads_xy"][p] for p in pads if p in I["pads_xy"]]
            cen = (sum(x for x, y in xy) / max(1, len(xy)), sum(y for x, y in xy) / max(1, len(xy)))
            info[k] = {"cand": cand, "n_cand": int(len(ys)), "centroid": cen, "pads": pads, "comps": comps, "island": gi}
            g_amps[k] = amps
            g_names[k].append(name)
            rec.append({"terminal": k, "name": name, "island": gi, "amps": round(amps, 3), "pads": pads[:8],
                        "legal_via_area_mm2": round(len(ys) * H * H, 2), "landing_radius_mm": land_r,
                        "landing_escalated": mult > 1})
        return info, members, g_amps, g_names, [0], [t[0] for t in terms], rec

    def _in(self, idx, c_):
        return 0 <= c_[0] < idx.shape[0] and 0 <= c_[1] < idx.shape[1]

    def cells_xy(self, mask, nmax):
        ys, xs = np.nonzero(mask)
        if len(ys) > nmax:
            sel = np.linspace(0, len(ys) - 1, nmax).astype(int)
            ys, xs = ys[sel], xs[sel]
        return [(self.R.x0 + x * H, self.R.y0 + y * H) for y, x in zip(ys, xs)]

    def pick_vias(self, net, info, n_want, I, pad_names, hw, lab=None, comp=None, w_need=0.0):
        cand = info["cand"]
        ys, xs = np.nonzero(cand)
        if lab is not None and comp is not None and len(ys):
            keep = lab[np.minimum(ys // K, lab.shape[0] - 1), np.minimum(xs // K, lab.shape[1] - 1)] == comp
            ys, xs = ys[keep], xs[keep]
        res = {"vias": [], "n_legal_cells": int(len(ys))}
        if len(ys) == 0:
            return res
        pts = np.stack([self.R.x0 + xs * H, self.R.y0 + ys * H], 1)
        tp = np.asarray([I["pads_xy"][p] for p in pad_names if p in I["pads_xy"]] or [info["centroid"]])
        if len(pts) * len(tp) < 3e7:
            dmin = np.min(np.hypot(pts[:, None, 0] - tp[None, :, 0], pts[:, None, 1] - tp[None, :, 1]), axis=1)
        else:
            dmin = np.hypot(pts[:, 0] - tp[:, 0].mean(), pts[:, 1] - tp[:, 1].mean())
        room = hw[ys, xs]
        score = dmin - 0.5 * np.minimum(room, 2.0) + 10.0 * np.maximum(0.0, w_need / 2 - room)
        order = np.argsort(score)
        chosen, tries = [], 0
        d0 = dmin[order[0]]
        reach = 25.0 if w_need > 1.0 else 12.0
        for k in order:
            x, y = float(pts[k, 0]), float(pts[k, 1])
            if dmin[k] > d0 + reach:
                break
            if any((x - cx) ** 2 + (y - cy) ** 2 < 0.81 for cx, cy in chosen):
                continue
            if chosen and min(math.hypot(x - cx, y - cy) for cx, cy in chosen) > 4.0:
                continue
            ok, s, why = self.via_ok_exact(net, x, y)
            tries += 1
            if not ok:
                res["rejected_exact"] = res.get("rejected_exact", 0) + 1
                res["blocker"] = [str(v) for v in why] if why else None
                if tries > 300:
                    break
                continue
            chosen.append((round(x, 4), round(y, 4)))
            if len(chosen) >= n_want:
                break
        res["vias"] = chosen
        if chosen:
            res["landing_to_terminal_mm"] = round(float(min(np.min(np.hypot(tp[:, 0] - x, tp[:, 1] - y)) for x, y in chosen)), 2)
        return res

    def blocked_analysis(self, rid, tree, tcells, w_req=1.0):
        """cheapest In3 path when every foreign In3 TRACK is passable at a penalty (pads, vias, fills, keepouts and
        reservations stay obstacles): the tracks within the trunk band of that path are the smallest rip-up proposal
        for this join. Tried at the required width first, then narrower (the result states the width achieved)."""
        r = self.rail[rid]
        net = r["board_net"]
        key = (rid, len(self.new_items))
        if getattr(self, "_blk_key", None) != key:
            tr = self.R.empty()
            uu = []
            for (g, n, kind, ident) in self.items[IN3]:
                if kind == "track" and n != net:
                    uu.append((g, n, ident))
                    self.R.fill_geom(tr, g)
            same, cross = self.masks(rid, IN3, True)
            same &= (tr == 0)
            cross &= (tr == 0)
            oth_h, own_h = self.hole_masks(rid)
            h2 = edt_mm(same, H) - CL_SAME
            np.minimum(h2, edt_mm(cross, H) - CL_CROSS, out=h2)
            np.minimum(h2, edt_mm(oth_h, H) - CL_HOLE, out=h2)
            np.minimum(h2, edt_mm(self.hard_mask(IN3, net, False), H), out=h2)
            np.minimum(h2, edt_mm(self.outside, H) - CL_EDGE, out=h2)
            h2 -= MARGIN
            self._blk_key = key
            self._blk = {"hwc": self.coarse(h2), "pen": self.coarse(edt_mm(tr, H)), "uu": uu, "graphs": {}}
        B = self._blk
        tried = []
        for wl in [w for w in (min(w_req, 4.0), 3.0, 2.0, 1.0, W_MIN) if w <= max(w_req, W_MIN) + 1e-9]:
            wl = round(wl, 2)
            if wl in tried:
                continue
            tried.append(wl)
            if wl not in B["graphs"]:
                cost = np.where(B["pen"] < wl / 2 + 0.3, 25.0, 1.0)
                B["graphs"][wl] = self.build_graph(B["hwc"], cost, max(wl, 1.0), wmin=wl)
            A, idx, rc = B["graphs"][wl]
            srcs = sorted({int(idx[c]) for c in tree if self._in(idx, c) and idx[c] >= 0})
            tn = sorted({int(idx[c]) for c in tcells if self._in(idx, c) and idx[c] >= 0})
            if not srcs or not tn:
                continue
            dist, pred, _ = csg.dijkstra(A, directed=False, indices=np.array(srcs), min_only=True, return_predecessors=True)
            best = min(tn, key=lambda n_: dist[n_])
            if not np.isfinite(dist[best]):
                continue
            seq = [best]
            while pred[seq[-1]] >= 0:
                seq.append(int(pred[seq[-1]]))
            pts = [self.cxy(*rc[n_]) for n_ in reversed(seq)]
            line = LineString(pts) if len(pts) > 1 else Point(pts[0])
            band = line.buffer(wl / 2 + CL_SAME)
            hit = [(n, ident) for (g, n, ident) in B["uu"] if g.intersects(band)]
            by = defaultdict(int)
            for n, ident in hit:
                by[norm(n)] += 1
            step = max(1, len(pts) // 150)
            return {"result": f"In3 path at {wl} mm exists if the listed In3 signal tracks are ripped up and re-routed",
                    "width_mm": wl, "width_required_mm": round(w_req, 2), "widths_tried": tried,
                    "path": [[round(x, 2), round(y, 2)] for x, y in pts[::step] + [pts[-1]]],
                    "path_len_mm": round(line.length, 1), "path_start": [round(v, 2) for v in pts[0]],
                    "path_end": [round(v, 2) for v in pts[-1]], "tracks": len(hit), "nets": len(by),
                    "by_net": dict(sorted(by.items(), key=lambda kv: -kv[1])), "uuids": [i for n, i in hit][:400]}
        return {"result": "no In3 path even with every foreign In3 track removed (pads, vias, fills, keepouts or "
                          "reservations block it) at any width tried", "widths_tried": tried}

    # ------------------------------------------------------------------ geometry + currents + widths
    def finalize(self, r, des, cts, hw, down, reached, src_gi):
        net = r["board_net"]
        idx = self.exact_index(net, IN3)
        segs = []
        for ci, ct in enumerate(cts):
            ct["seg_by_path"] = defaultdict(list)
            ct["join"] = []
            first = len(segs)
            for i, p in enumerate(ct["paths"]):
                pts = [self.cxy(*c) for c in p["cells"]]
                hwp = [float(hw[min(c[0] * K, hw.shape[0] - 1), min(c[1] * K, hw.shape[1] - 1)]) for c in p["cells"]]
                st = pts[0]
                best, att, par, pseg = 1e9, None, -1, None
                for v in ct["root"]["vias"]:
                    dd = math.dist(st, v)
                    if dd < best:
                        best, att, par, pseg = dd, v, -1, None
                for k in range(first, len(segs)):
                    s = segs[k]
                    L = LineString([s["a"], s["b"]]) if s["len"] > 1e-9 else Point(s["a"])
                    dd = L.distance(Point(st))
                    if dd < best - 1e-9:
                        q = L.interpolate(L.project(Point(st))) if s["len"] > 1e-9 else Point(s["a"])
                        best, att, par, pseg = dd, (q.x, q.y), s["path"], k
                if att is not None and best > 1e-6:
                    pts = [tuple(att)] + pts
                    hwp = [hwp[0]] + hwp
                vg = ct["vgroups"][i + 1]
                en = min(vg["vias"], key=lambda v: math.dist(v, pts[-1]))
                if math.dist(en, pts[-1]) > 1e-6:
                    pts = pts + [tuple(en)]
                    hwp = hwp + [hwp[-1]]
                ct["join"].append((par, pseg))
                for (a_, b_, av) in self.simplify(idx, pts, hwp):
                    k = len(segs)
                    segs.append({"a": a_, "b": b_, "avail": av, "path": i, "ct": ci, "len": math.dist(a_, b_)})
                    ct["seg_by_path"][i].append(k)
            amps = defaultdict(float)
            P = ct["paths"]
            for i in range(len(P) - 1, -1, -1):
                for k in ct["seg_by_path"][i]:
                    amps[k] += P[i]["amps"]
                j, kj = ct["join"][i]
                while j >= 0:
                    for k in ct["seg_by_path"][j]:
                        amps[k] += P[i]["amps"]
                        if k == kj:
                            break
                    j, kj = ct["join"][j]
            for k, v in amps.items():
                segs[k]["amps_raw"] = v
        for s in segs:
            s["amps"] = s.get("amps_raw", 0.0)
            s["w_ipc"] = ipc_width_mm(s["amps"])
            s["w_avail"] = max(0.0, 2 * s["avail"] - 0.02)
            # IPC width rounded UP to 0.01 mm (never below the IPC value through rounding), capped by the room
            s["w"] = min(s["w_avail"], max(math.ceil(s["w_ipc"] * 100 - 1e-9) / 100, W_MIN))
        budget = self.spec["drop_budget_v"]
        for _ in range(15):
            drops = self.drops(segs, cts, down, reached, src_gi)
            if max([d["drop_v"] for d in drops] or [0]) <= 0.8 * budget:
                break
            grew = False
            for s in segs:
                if s["w"] < s["w_avail"] - 0.01 and s["amps"] > 0.05:
                    s["w"] = min(s["w_avail"], s["w"] * 1.4 + 0.1)
                    grew = True
            if not grew:
                break
        for k, s in enumerate(segs):
            w = math.floor(s["w"] * 100 + 1e-6) / 100
            s["w"] = w
            if w < 0.2:
                s["skipped"] = True
                des["notes"].append(f"segment {k} NOT written: exact available width {s['w_avail']:.2f} mm")
                continue
            if s["len"] > 1e-6:
                self.out_tracks.append({"net": net, "layer": IN3, "width": w, "points": [list(s["a"]), list(s["b"])]})
                self.add_new(net, "track", {IN3: [LineString([s["a"], s["b"]]).buffer(w / 2, 8)]})
            ct = cts[s["ct"]]
            des["segments"].append({"component": ct["C"], "path": s["path"], "to_island": ct["paths"][s["path"]]["island"],
                                    "a": [round(v, 3) for v in s["a"]], "b": [round(v, 3) for v in s["b"]],
                                    "len_mm": round(s["len"], 2), "width_mm": w, "amps": s["amps"],
                                    "w_ipc10C_mm": round(s["w_ipc"], 2), "w_ipc10C_mm_raw": s["w_ipc"], "w_available_mm": round(s["w_avail"], 2),
                                    "rise_C": round(ipc_rise(s["amps"], w), 1),
                                    "R_mohm_60C": round(1e3 * RST * s["len"] / w, 3)})
        drops = self.drops(segs, cts, down, reached, src_gi)
        for ct in cts:
            csegs = [s for s in segs if cts[s["ct"]] is ct]
            for vg in ct["vgroups"]:
                self.write_vias(r, des, vg, csegs)
        des["drops"] = drops
        des["worst_drop_v"] = max([d["drop_v"] for d in drops] or [0])
        des["budget_v"] = budget
        des["territory_mm"] = self.territory_lengths(segs)
        if getattr(self, "soft_res", None):
            cr = defaultdict(float)
            for s_ in segs:
                if s_.get("skipped") or s_["len"] < 1e-6:
                    continue
                Ls = LineString([s_["a"], s_["b"]])
                for nm_, g in self.soft_res:
                    if Ls.intersects(g):
                        cr[nm_[16:]] += Ls.intersection(g).length
            des["reservation_crossings_mm"] = {k: round(v, 1) for k, v in sorted(cr.items(), key=lambda kv: -kv[1])}
        des["components_used"] = [{"component": ct["C"], "entry_island": ct["entry"], "targets": [p["island"] for p in ct["paths"]],
                                   "root_vias": len(ct["root"]["vias"])} for ct in cts]
        # necks: segments below their IPC-2152 width; the In3 signal tracks inside the band the IPC width needs are
        # the rip-up proposal that would let the segment reach it (pads, vias, keepouts there are listed as fixed)
        tr3 = [(g, n, ident) for (g, n, kind, ident) in self.items[IN3] if kind == "track" and n != net]
        fixed3 = [(g, n, kind) for (g, n, kind, ident) in self.items[IN3] if kind in ("pad_th", "via", "fill") and n != net]
        t_tree = STRtree([g for g, n, i in tr3]) if tr3 else None
        f_tree = STRtree([g for g, n, k in fixed3]) if fixed3 else None
        necks, rip = [], defaultdict(set)
        for s in segs:
            if s.get("skipped") or s["len"] < 1e-6 or s["w"] >= s["w_ipc"] - 1e-6:
                continue
            band = LineString([s["a"], s["b"]]).buffer(s["w_ipc"] / 2 + CL_SAME, 4)
            ht = [tr3[i] for i in (t_tree.query(band, predicate="intersects") if t_tree else [])]
            hf = [fixed3[i] for i in (f_tree.query(band, predicate="intersects") if f_tree else [])]
            for g, n, ident in ht:
                rip[norm(n)].add(ident)
            necks.append({"a": [round(v, 2) for v in s["a"]], "b": [round(v, 2) for v in s["b"]], "len_mm": round(s["len"], 2),
                          "amps": round(s["amps"], 3), "width_mm": s["w"], "w_ipc10C_mm": round(s["w_ipc"], 2),
                          "rise_C": round(ipc_rise(s["amps"], s["w"]), 1), "in3_tracks_in_band": len(ht),
                          "fixed_items_in_band": len(hf), "track_nets": sorted({norm(n) for g, n, i in ht})[:12]})
        des["necks_below_ipc"] = necks
        des["neck_ripup_proposal"] = {"tracks": sum(len(v) for v in rip.values()), "nets": len(rip),
                                      "by_net": {n: len(v) for n, v in sorted(rip.items(), key=lambda kv: -len(kv[1]))},
                                      "uuids": sorted({u for v in rip.values() for u in v})[:600],
                                      "note": "rip-up of these In3 signal tracks (and re-route elsewhere) frees the IPC-2152 width at "
                                              "every neck below it; necks whose band also holds pads, vias or fills need those moved too"}

    def simplify(self, idx, pts, hwp):
        out = []
        if len(pts) == 1:
            av, _ = self.seg_avail(idx, pts[0], pts[0])
            return [(pts[0], pts[0], av)]

        def rec(i, j):
            a_, b_ = pts[i], pts[j]
            need = 0.85 * min(hwp[i:j + 1])
            av, _ = self.seg_avail(idx, a_, b_)
            dev = 0.0
            if j - i > 1:
                L = LineString([a_, b_])
                dev = max(L.distance(Point(p)) for p in pts[i + 1:j])
            if j - i <= 1 or (av >= max(need, W_MIN / 2) and dev <= 0.6):
                out.append((a_, b_, av))
                return
            m = (i + j) // 2
            rec(i, m)
            rec(m, j)
        rec(0, len(pts) - 1)
        return out

    def drops(self, segs, cts, down, reached, src_gi):
        """DC drop (60 C, design current) from the source to every reached island: In3 tree drops + via barrels, chained
        through relay islands (the relay island's own plane copper between its two via groups is NOT modelled)."""
        res = []
        dz = self.dz_to_in3()
        rv = via_r(dz)
        drop_at = {src_gi: 0.0}
        for ct in cts:
            E = ct["entry"]
            base = drop_at.get(E, float("nan"))
            nroot = len(ct["root"]["vias"])
            I_C = ct["root"]["amps"]
            for i, p in enumerate(ct["paths"]):
                v = 0.0
                chain = [(i, None)]
                j, kj = ct["join"][i]
                while j >= 0:
                    chain.append((j, kj))
                    j, kj = ct["join"][j]
                for (pj, upto) in chain:
                    for k in ct["seg_by_path"][pj]:
                        s = segs[k]
                        if not s.get("skipped") and s["w"] > 0:
                            v += s["amps"] * RST * s["len"] / s["w"]
                        if upto is not None and k == upto:
                            break
                vg = ct["vgroups"][i + 1]
                vv = (I_C * rv / nroot if nroot else 0.0) + (p["amps"] * rv / len(vg["vias"]) if vg["vias"] else 0.0)
                drop_at[p["island"]] = base + v + vv
                res.append({"island": p["island"], "target": vg["name"], "component": ct["C"], "via_entry_island": E,
                            "amps_downstream": round(p["amps"], 3), "drop_this_tree_v": round(v + vv, 4),
                            "drop_v": round(base + v + vv, 4)})
        return res

    def plot(self, rid, hwc, lab, cts, des, info, reached):
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except Exception:
            return
        d = os.path.join(self.a.work, "maps")
        os.makedirs(d, exist_ok=True)
        ny, nx = hwc.shape
        ext = [self.R.x0, self.R.x0 + nx * K * H, self.R.y0 + ny * K * H, self.R.y0]
        img = np.ones((ny, nx, 3))
        w = 2 * hwc
        img[w >= W_MIN] = (0.86, 0.86, 0.86)
        img[w >= 1.0] = (0.75, 0.75, 0.75)
        img[w >= 3.0] = (0.62, 0.62, 0.62)
        used = [ct["C"] for ct in cts]
        if used:
            m = np.isin(lab, used) & (w >= W_MIN)
            img[m] = img[m] * np.array([0.85, 1.0, 0.85])
        fig, ax = plt.subplots(figsize=(26, 14))
        ax.imshow(img, extent=ext, interpolation="nearest")
        terc = self.ter[:ny * K:K, :nx * K:K]
        own = self.dom_ids.get(self.rail[rid]["domain"], -1)
        try:
            ax.contour(np.arange(nx) * K * H + self.R.x0, np.arange(ny) * K * H + self.R.y0, (terc == own).astype(float), [0.5],
                       colors=["green"], linewidths=0.6)
        except Exception:
            pass
        col = "blue" if self.rail[rid]["role"] == "return" else "red"
        for s in des["segments"]:
            ax.plot([s["a"][0], s["b"][0]], [s["a"][1], s["b"][1]], color=col, lw=max(0.6, s["width_mm"] * 1.6),
                    solid_capstyle="round")
        for vg in des["via_groups"]:
            if vg["vias"]:
                xs, ys = zip(*vg["vias"])
                ax.plot(xs, ys, "o", ms=3, mfc="yellow", mec="k", mew=0.4)
        for gi, ii in info.items():
            ax.plot(*ii["centroid"], "o" if gi in reached else "x", ms=5, color="darkgreen" if gi in reached else "red")
        for u in des["unreached"]:
            b = u.get("blocked") or {}
            if b.get("path"):
                xs, ys = zip(*b["path"])
                ax.plot(xs, ys, "--", color="red", lw=0.8)
            if u.get("amps", 0) > 0:
                c = info[u["island"]]["centroid"]
                ax.text(c[0], c[1], f"{u['island']}: {u['amps']} A", color="red", fontsize=8)
        ax.set_xlim(self.board.bounds[0], self.board.bounds[2])
        ax.set_ylim(self.board.bounds[3], self.board.bounds[1])
        ax.set_aspect("equal")
        ax.set_title(f"{rid} {norm(self.rail[rid]['board_net'])}: In3 free width (grey >= 0.3 / 1 / 3 mm; green tint = In3 "
                     f"components used), own-domain In1/In4 plane outline green, trunk {col}, vias yellow, reached islands "
                     "green dots, unreached red x, dashed red = cheapest path if In3 signal tracks are ripped up", fontsize=9)
        fig.savefig(os.path.join(d, f"{rid}.png"), dpi=60, bbox_inches="tight")
        plt.close(fig)

    def dz_to_in3(self):
        st = self.G.get("stackup", {})
        try:
            z, zs = 0.0, {}
            for k, v in st.items():
                t = v.get("thickness_mm", 0) or 0
                if v.get("type") == "copper":
                    zs[k] = z + t / 2
                if v.get("type") in ("copper", "core", "prepreg"):
                    z += t
            return abs(zs["In3.Cu"] - zs["F.Cu"]) * 1e-3
        except Exception:
            return 1.0e-3

    def write_vias(self, r, des, vg, segs):
        net = r["board_net"]
        idx = self.exact_index(net, IN3)
        placed, links = [], []
        lines = [LineString([s["a"], s["b"]]) for s in segs if not s.get("skipped") and s["len"] > 1e-6]
        # vias the trunk ends exactly on come first
        ends = {tuple(s["b"]) for s in segs if not s.get("skipped")} | {tuple(s["a"]) for s in segs if not s.get("skipped")}
        order = sorted(vg["vias"], key=lambda v: (tuple(v) not in ends,))
        for (x, y) in order:
            ok, sl, why = self.via_ok_exact(net, x, y)
            if not ok:
                vg.setdefault("dropped", []).append({"via": [x, y], "why": [str(v) for v in why] if why else None})
                continue
            P = Point(x, y)
            best, tgt = 1e9, None
            for L in lines:
                dd = L.distance(P)
                if dd < best:
                    best, tgt = dd, L.interpolate(L.project(P)).coords[0]
            for (px, py) in placed:
                dd = math.hypot(px - x, py - y)
                if dd < best:
                    best, tgt = dd, (px, py)
            if tgt is None:
                vg.setdefault("dropped", []).append({"via": [x, y], "why": "nothing to link to on In3"})
                continue
            if best > 1e-4:
                av, blk = self.seg_avail(idx, (x, y), tgt)
                w = math.floor(min(W_STUB, 2 * av - 0.02) * 100) / 100
                if w < 0.25 or best > 15.0:
                    vg.setdefault("dropped", []).append({"via": [x, y], "why": f"In3 link {best:.2f} mm, available width {2 * av:.2f} mm"})
                    continue
                links.append({"a": [x, y], "b": [round(tgt[0], 4), round(tgt[1], 4)], "width": w, "len": round(best, 2)})
                self.out_tracks.append({"net": net, "layer": IN3, "width": w, "points": [[x, y], [tgt[0], tgt[1]]]})
                g = LineString([(x, y), tgt]).buffer(w / 2, 8)
                self.add_new(net, "track", {IN3: [g]})
                lines.append(LineString([(x, y), tgt]))
            placed.append((x, y))
            self.out_vias.append({"kind": "via", "net": net, "x": x, "y": y, "d": self.via_d, "drill": self.via_drill})
            disk = Point(x, y).buffer(self.via_d / 2, 16)
            self.add_new(net, "via", {L: [disk] for L in self.layers}, [Point(x, y).buffer(self.via_drill / 2, 16)])
        rec = self.vg_record(dict(vg, vias=placed))
        rec["links"] = links
        rec["dropped"] = vg.get("dropped", [])
        des["via_groups"].append(rec)

    def vg_record(self, vg):
        n = len(vg.get("vias", []))
        qualification = array_status(vg.get("amps"), n, self.amps_per_via, vg.get("n_req"))
        return {"name": vg.get("name"), "island": vg.get("island"), "amps": vg.get("amps"), "n_req": vg.get("n_req"),
                "n": n, "ok": qualification["qualified_for_modeled_current"], "current_qualification": qualification, "full_rail_qualified": False, "vias": vg.get("vias", []),
                "legal_cells_on_island": vg.get("n_legal_cells"), "rejected_exact": vg.get("rejected_exact", 0),
                "amps_per_via": round((vg.get("amps") or 0) / n, 3) if n else None,
                "landing_to_terminal_mm": vg.get("landing_to_terminal_mm"), "routed_min_width_mm": vg.get("routed_min_width_mm"),
                "ipc_width_mm": vg.get("ipc_width_mm")}

    def territory_lengths(self, segs):
        out = defaultdict(float)
        inv = {v: k for k, v in self.dom_ids.items()}
        for s in segs:
            if s.get("skipped") or s["len"] < 1e-6:
                continue
            n = max(2, int(s["len"] / 0.5))
            for i in range(n):
                t = (i + 0.5) / n
                cy, cx = self.R.to_cell(s["a"][0] + t * (s["b"][0] - s["a"][0]), s["a"][1] + t * (s["b"][1] - s["a"][1]))
                d = int(self.ter[min(max(cy, 0), self.R.ny - 1), min(max(cx, 0), self.R.nx - 1)])
                out[inv.get(d, "no plane") if d else "no plane"] += s["len"] / n
        return {k: round(v, 1) for k, v in sorted(out.items(), key=lambda kv: -kv[1])}

    def ripup_list(self):
        """foreign In3 tracks that the proposal copper (In3 tracks and via pads) would violate: the rip-up list."""
        tree = STRtree([g for (g, n, k, i) in self.pool])
        hits = {}
        per_net = defaultdict(set)
        for it in self.new_items:
            d = self.dom(it["net"])
            for g in it["layers"].get(IN3, []):
                for k in tree.query(g.buffer(CL_CROSS)):
                    pg, pn, kind, ident = self.pool[k]
                    clr = CL_SAME if self.dom(pn) == d else CL_CROSS
                    if g.distance(pg) < clr - 1e-6:
                        hits[ident] = pn
                        per_net[it["net"]].add(ident)
        by = defaultdict(int)
        length = defaultdict(float)
        tl = {t["uuid"]: math.dist(t["a"], t["b"]) for t in self.G["tracks"] if t["layer"] == IN3}
        for ident, n in hits.items():
            by[norm(n)] += 1
            length[norm(n)] += tl.get(ident, 0.0)
        nv = sum(1 for i in hits if i in self._via_uuids())
        return {"tracks": len(hits) - nv, "vias": nv, "signal_nets": len(by), "track_length_mm": round(sum(length.values()), 1),
                "by_signal_net": {n: {"tracks": c, "mm": round(length[n], 1)} for n, c in sorted(by.items(), key=lambda kv: -kv[1])},
                "by_field_net": {norm(n): len(v) for n, v in per_net.items()},
                "uuids": sorted(hits),
                "note": "these In3 segments (of the listed signal nets) must be ripped up and the nets re-routed before this "
                        "proposal can be applied; every rip-up is a lost connection until re-routed"}

    def _via_uuids(self):
        if not hasattr(self, "_vu"):
            self._vu = {v["uuid"] for v in self.G["vias"]}
        return self._vu

    def post_snap(self):
        """a written track end that lies inside a via pad of its own net is moved to the via centre when the moved
        segment stays legal (avoids track_not_centered_on_via)."""
        vias = defaultdict(list)
        for v in self.out_vias:
            vias[v["net"]].append((v["x"], v["y"]))
        for v in self.G["vias"]:
            vias[v["net"]].append((v["x"], v["y"]))
        moved = 0
        idxs = {}
        for t in self.out_tracks:
            for e in (0, 1):
                p = t["points"][e]
                for (vx, vy) in vias[t["net"]]:
                    dd = math.hypot(p[0] - vx, p[1] - vy)
                    if 1e-6 < dd < self.via_d / 2:
                        if t["net"] not in idxs:
                            idxs[t["net"]] = self.exact_index(t["net"], IN3)
                        q = list(t["points"])
                        q[e] = [vx, vy]
                        av, _ = self.seg_avail(idxs[t["net"]], tuple(q[0]), tuple(q[1]))
                        if 2 * av >= t["width"] - 1e-6:
                            t["points"] = q
                            moved += 1
                        break
        # a segment that collapsed to a point (both ends snapped onto one via) carries nothing: drop it
        before = len(self.out_tracks)
        self.out_tracks = [t for t in self.out_tracks
                           if any(math.dist(a_, b_) > 1e-6 for a_, b_ in zip(t["points"], t["points"][1:]))]
        self.design["post_snap_moved_ends"] = moved
        self.design["post_snap_dropped_degenerate"] = before - len(self.out_tracks)

    def write(self):
        w = self.a.work
        if os.path.exists(os.path.join(w, "routes.json")):
            raise SystemExit("Existing applicable routes.json: use a fresh work directory to avoid stale route reuse")
        for rid, d in self.design["nets"].items():
            segs = d.get("segments", [])
            d["summary"] = {"segments": len(segs), "length_mm": round(sum(s["len_mm"] for s in segs), 1),
                            "min_width_mm": min([s["width_mm"] for s in segs] or [0]),
                            "max_width_mm": max([s["width_mm"] for s in segs] or [0]),
                            "segments_over_10C": sum(1 for s in segs if s["rise_C"] > 10.0),
                            "via_groups": len(d["via_groups"]), "vias": sum(v["n"] for v in d["via_groups"]),
                            "via_groups_below_n_req": sum(1 for v in d["via_groups"] if not v["ok"]),
                            "unreached_islands": len(d["unreached"]), "worst_drop_v": d.get("worst_drop_v")}
        self.design["constants"] = {
            "rho20_ohm_m": RHO20, "t_cu_mm": T_CU * 1e3, "conductor_C": TJ, "sheet_mohm_20C": round(RS20 * 1e3, 4),
            "sheet_mohm_TJ": round(RST * 1e3, 4), "via_barrel_F_to_In3_mohm": round(via_r(self.dz_to_in3()) * 1e3, 3),
            "clearances_mm": {"same_domain": CL_SAME, "cross_domain": CL_CROSS, "hole": CL_HOLE, "edge": CL_EDGE,
                              "smd_aperture": CL_SMD, "hole_to_hole": H2H},
            "via": {"d": self.via_d, "drill": self.via_drill, "amps_per_via": self.amps_per_via},
            "raster_mm": H, "routing_grid_mm": K * H, "raster_margin_mm": MARGIN,
            "reservations_applied": self.res_ok, "barrier_courtyards": self.n_barrier,
            "ipc2152": "Brooks & Adam fit of the IPC-2152 data, dT = 215.3 I^2 W^-1.15 Th^-1 (mil), Th = 1.378 mil (35 um)"}
        qualifications = {rid: modeled_route_status(self.rail[rid], d, self.spec) for rid, d in self.design["nets"].items()}
        self.design["current_qualification"] = qualifications
        self.design["full_rail_qualified"] = False
        route_failures = [{"net": rid, "reason": reason} for rid, q in qualifications.items() for reason in q["reasons"]]
        routes_name = route_output(qualifications, bool(self.pool))
        self.design["applicable_routes_emitted"] = routes_name == "routes.json"
        if self.pool:
            self.design["ripup_proposal"] = self.ripup_list()
            self.design["mode"] = ("RIP-UP PROPOSAL (what-if): NOT for application; the listed In3 signal tracks would have to be "
                                   "ripped up and re-routed first")
            routes_name = "routes_PROPOSAL_DO_NOT_APPLY.json"
        json.dump(self.analysis, open(os.path.join(w, "analysis.json"), "w", encoding="utf-8"), indent=1)
        json.dump(self.design, open(os.path.join(w, "design.json"), "w", encoding="utf-8"), indent=1)
        json.dump({"tracks": self.out_tracks + self.out_vias, "failures": route_failures,
                   "current_qualification": qualifications, "full_rail_qualified": False},
                  open(os.path.join(w, routes_name), "w", encoding="utf-8"), indent=0)
        log("wrote", len(self.out_tracks), "In3 tracks,", len(self.out_vias), "vias")
        print(json.dumps({rid: d["summary"] for rid, d in self.design["nets"].items()}))


def text_fallbacks(G):
    """board outline (Edge.Cuts lines/arcs) and stackup from the board file text when the dump could not get them."""
    need_o = not G.get("outline")
    need_s = not G.get("stackup") or "error" in G.get("stackup", {})
    if not (need_o or need_s) or not os.path.exists(G.get("board", "")):
        return
    txt = open(G["board"], encoding="utf-8").read()
    if need_s:
        st = {}
        i = txt.find("(stackup")
        for m in re.finditer(r'\(layer "([^"]+)"\s+\(type "([^"]+)"\)(?:\s+\(thickness ([0-9.]+)\))?', txt[i:i + 20000] if i >= 0 else ""):
            st[m.group(1)] = {"type": m.group(2), "thickness_mm": float(m.group(3)) if m.group(3) else 0.0}
        G["stackup"] = st
        log("stackup from the board text:", len(st), "layers")
    if need_o:
        from shapely.ops import polygonize
        lines = []
        for m in re.finditer(r'\n\t\(gr_(line|arc)\s*\n(.*?)\n\t\)', txt, re.S):
            body = m.group(2)
            if '(layer "Edge.Cuts")' not in body:
                continue
            P = {k: tuple(float(v) for v in re.search(r"\(" + k + r" ([-0-9.]+) ([-0-9.]+)\)", body).groups())
                 for k in ("start", "end", "mid") if re.search(r"\(" + k + r" ", body)}
            pts = arc_points(P["start"], P["mid"], P["end"], 0.05) if m.group(1) == "arc" else [P["start"], P["end"]]
            pts = [P["start"]] + [(round(x, 6), round(y, 6)) for x, y in pts[1:-1]] + [P["end"]]
            lines.append(LineString(pts))
        polys = list(polygonize(unary_union(lines)))
        if polys:
            g = max(polys, key=lambda p: p.area)
            G["outline"] = [[list(g.exterior.coords), []]]
            log(f"outline from {len(lines)} Edge.Cuts items: bounds {[round(v, 2) for v in g.bounds]}, area {g.area:.0f} mm2")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geom", required=True)
    ap.add_argument("--partitions", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--spec", default="Z:/pcb-runs/claude-finish/tools/field_pdn_spec.json")
    ap.add_argument("--dru", default="Z:/pcb-runs/claude-finish/integrate/board.kicad_dru")
    ap.add_argument("--barriers", default="Z:/pcb-runs/domains/barriers.json")
    ap.add_argument("--reserve", default="Z:/pcb-runs/claude-finish/tools/reserve_corridors.py")
    ap.add_argument("--only", default="")
    ap.add_argument("--max-island-branch", type=float, default=ZERO_BRANCH_MM,
                    help="a zero-current island is joined only by an In3 branch up to this long (mm)")
    ap.add_argument("--track-land-mm", type=float, default=None,
                    help="vias on an island's tracks only within this radius of its terminal pads (default: 0 = anywhere, "
                         "6 mm in --ripup-proposal mode)")
    ap.add_argument("--min-cluster-amps", type=float, default=0.05,
                    help="terminal mode: clusters below this current (quiescent IC grounds) get no trunk")
    ap.add_argument("--order", default="", help="routing order of the rail ids, e.g. FBG,FB,FAG,FA (default FIELD_A first, return first)")
    ap.add_argument("--allow-reservations", default="",
                    help="comma list of reservation prefixes (e.g. PAIR) that a trunk may cross on In3 at x5 cost (what-if only)")
    ap.add_argument("--allow-domains", default="",
                    help="comma list of extra galvanic domains whose In1/In4 territory a trunk may cross on In3 (what-if only)")
    ap.add_argument("--terminal-mode", action="store_true",
                    help="current-carrying design (default in --ripup-proposal): one node per source / load cluster, vias near its pads")
    ap.add_argument("--ripup-vias", action="store_true",
                    help="with --ripup-proposal: foreign SIGNAL vias (nets without inner-layer fills) are removable too")
    ap.add_argument("--ripup-proposal", action="store_true",
                    help="what-if design with every foreign In3 signal track removable (penalised); writes the rip-up list "
                         "and routes_PROPOSAL_DO_NOT_APPLY.json, never routes.json")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    if os.path.exists(os.path.join(a.work, "routes.json")):
        raise SystemExit("Existing applicable routes.json: use a fresh work directory to avoid stale route reuse")
    spec = json.load(open(a.spec, encoding="utf-8"))
    try:
        preflight = validate_spec(spec, a.only)
    except CurrentModelError as error:
        json.dump(error.report, open(os.path.join(a.work, "field-current-preflight.json"), "w", encoding="utf-8"), indent=1)
        log(str(error))
        raise SystemExit(3)
    json.dump(preflight, open(os.path.join(a.work, "field-current-preflight.json"), "w", encoding="utf-8"), indent=1)
    G = json.load(open(a.geom, encoding="utf-8"))
    PART = json.load(open(a.partitions, encoding="utf-8"))
    log("geom", G.get("sha256", "")[:16], "refilled", G.get("refilled"), "pads", len(G["pads"]), "tracks", len(G["tracks"]),
        "partitions", PART.get("sha256", "")[:16])
    if PART.get("sha256") and G.get("sha256") and PART["sha256"] != G["sha256"]:
        log("WARNING: partitions.json belongs to a different board revision than the geometry")
    text_fallbacks(G)
    Designer(G, PART, spec, a).run()


if __name__ == "__main__":
    main()
