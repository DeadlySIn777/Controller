# Corridor router (system Python: numpy, PIL, torch on GPU).
# corridor_router_in3sv3.py = in3sv + CORR_STRICT_IN3 (tools/patch_strict_in3.py); in3sv = in3v + opt-in STRICT power mode (tools/patch_power_strict.py):
#   CORR_POWER_STRICT=1: power jobs carrying "amps" route their trunk only at the table width, with audited
#   necks (<= CORR_ENTRY_MM from the pad) and the via rule n_req = ceil(amps / CORR_I_VIA); unset = verified behaviour.
# Routes ordered jobs on the two outer layers (and, for boxed-in hops, through vias over the inner signal
# layer In3.Cu) of a KiCad board using a raster of all existing copper:
#   * "power" jobs: one wide track per connection, on F.Cu or B.Cu, straight-ish Manhattan/45 paths found
#     by a GPU BFS on the free raster (obstacles dilated by half width + clearance), joining the pad
#     clusters of a net in MST order; width per net from a table (IPC-2152 1 oz sizing done by the caller);
#   * "pair" jobs: a differential pair routed as ONE corridor of width 2w+s (+ clearance) along a BFS path
#     between the two pad pairs, then split into the P and N tracks at +-(w+s)/2; both end at their pads with
#     short straight stubs. Intra-pair skew is the stub difference only.
# Output: a JSON list of tracks (layer, net, width, polyline) for corridor_apply.py; the raster is updated as
# each job lands so later jobs see earlier results. Galvanic domains: other-domain copper is kept at 0.6 mm.
# Via legality (tools/patch_via_legality.py): vias keep EDGE from the board edge, respect via-only rule
# areas, and keep CLR/XDOM by domain to the plane-layer (In1/In2/In4) tracks and other-domain plane fills.
#   python corridor_router.py geom.json jobs.json out.json
import json
import math
import os
import re
import sys
from collections import defaultdict

import numpy as np
import torch
from PIL import Image, ImageDraw

G = json.load(open(sys.argv[1], encoding="utf-8"))
JOBS = json.load(open(sys.argv[2], encoding="utf-8"))
OUT = sys.argv[3]
import os as _os
import time as _time
import hashlib as _hashlib
DEBUG_DIR = _os.environ.get("CORR_DEBUG", "")
# --checkpoint <file>: the results are flushed to <file> every CKPT_SECONDS (atomic rename) and a run that
# finds a checkpoint for the same jobs file resumes after the jobs it already finished (power-loss safe)
CKPT = sys.argv[sys.argv.index("--checkpoint") + 1] if "--checkpoint" in sys.argv else ""
CKPT_SECONDS = 30.0
JOBS_SHA = _hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()


def ckpt_write(results_, failures_, done_):
    if not CKPT:
        return
    tmp = CKPT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"jobs_sha": JOBS_SHA, "done": done_, "tracks": results_, "failures": failures_}, f)
    _os.replace(tmp, CKPT)
SINGLE_FALLBACK = _os.environ.get("CORR_SINGLE_FALLBACK", "0") == "1"
RES = 0.1
CLR, XDOM, EDGE = 0.15, 0.6, 0.5
SAFE = float(__import__("os").environ.get("CORR_SAFE", "0.2"))
VIA_DETOUR = __import__("os").environ.get("CORR_VIA_DETOUR", "1") == "1"
POWER_STRICT = _os.environ.get("CORR_POWER_STRICT", "0") == "1"
ENTRY_MM = float(_os.environ.get("CORR_ENTRY_MM", "2.0"))     # strict: longest neck from a pad (geodesic)
I_VIA = float(_os.environ.get("CORR_I_VIA", "0.5"))           # strict: current per 0.6/0.3 mm via (A)
STRICT_IN3 = _os.environ.get("CORR_STRICT_IN3", "0") == "1"   # strict: In3 detours for n_req == 1 jobs
if POWER_STRICT:
    print(f"power-strict mode: trunk at the table width only, necks <= {ENTRY_MM} mm, {I_VIA} A per via", flush=True)
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
x0, y0, x1, y1 = G["bbox"]
NX, NY = int(math.ceil((x1 - x0) / RES)) + 1, int(math.ceil((y1 - y0) / RES)) + 1


def px(x, y):
    """mm -> raster coordinates in the nearest-cell convention: cell (ix, iy) is centred on to_mm(ix, iy);
    int(px()) is the nearest cell and Pillow (which truncates coordinates) draws at the nearest cell."""
    return ((x - x0) / RES + 0.5, (y - y0) / RES + 0.5)


def px_w(w):
    """Odd pixel width covering a track of width w (Pillow centres odd widths; even widths land one-sided)."""
    return 2 * int(w / (2 * RES) + 0.5 - 1e-9) + 1


def px_r(r):
    """Integer pixel radius covering a circle of radius r (conservative by at most half a cell)."""
    return int(r / RES + 0.5 - 1e-9)


def to_mm(ix, iy):
    return (x0 + ix * RES, y0 + iy * RES)


net_dom = {}
for p in G["pads"]:
    if p["net"]:
        net_dom.setdefault(p["net"], p["cls"].split(",")[0])
nets = sorted({p["net"] for p in G["pads"] if p["net"]} | {t["net"] for t in G["tracks"]} |
              {v["net"] for v in G["vias"]} | {z["net"] for z in G["zones"]} | {j["net"] for j in JOBS if "net" in j} |
              {n for j in JOBS for n in j.get("nets", [])})
NID = {n: i + 2 for i, n in enumerate(n for n in nets if n)}
DOMS = sorted(set(net_dom.values()) | {"DOM_LOGIC"})
DID = {d: i + 1 for i, d in enumerate(DOMS)}
dom_of_id = np.zeros(len(NID) + 2, dtype=np.int16)
for n, i in NID.items():
    dom_of_id[i] = DID[net_dom.get(n, "DOM_LOGIC")]
dom_t = torch.from_numpy(dom_of_id).to(DEV)

LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
RASTER_LAYERS = ("F.Cu", "In3.Cu", "B.Cu")   # In3-capable: the inner signal layer is routable through vias
labels = {L: Image.new("I", (NX, NY), 0) for L in RASTER_LAYERS}
draws = {L: ImageDraw.Draw(labels[L]) for L in labels}
holes = Image.new("I", (NX, NY), 0)
hd = ImageDraw.Draw(holes)


def ring_xy(ring):
    return [px(x, y) for x, y in ring]


def draw_poly(L, entry, val):
    ring, holes_ = entry
    if len(ring) >= 3:
        draws[L].polygon(ring_xy(ring), fill=val)


def draw_circle(d, x, y, r, val):
    cx, cy = (int(v) for v in px(x, y))
    rr = px_r(r)
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=val)


def draw_track(d, a, b, w, val):
    (ax, ay), (bx, by) = px(*a), px(*b)
    d.line([ax, ay, bx, by], fill=val, width=px_w(w))
    draw_circle(d, a[0], a[1], w / 2, val)
    draw_circle(d, b[0], b[1], w / 2, val)


for t in G["tracks"]:
    if t["layer"] in labels:
        draw_track(draws[t["layer"]], t["a"], t["b"], t["w"], NID.get(t["net"], 1))
for sh in G.get("shapes", []):
    if sh["layer"] in labels:
        for e in sh["poly"]:
            draw_poly(sh["layer"], e, NID.get(sh["net"], 1) if sh["net"] else 1)
for v in G["vias"]:
    for L in labels:
        draw_circle(draws[L], v["x"], v["y"], v["d"] / 2, NID.get(v["net"], 1))
    draw_circle(hd, v["x"], v["y"], v["drill"] / 2, 1)
pad_of = {}
for p in G["pads"]:
    val = NID.get(p["net"], 1) if p["net"] else 1
    for L in p["layers"]:
        if L in labels:
            for e in p["poly"]:
                draw_poly(L, e, val)
    if p["drill"] > 0 and not p["smd"]:
        for L in labels:
            if L not in p["layers"]:
                draw_circle(draws[L], p["x"], p["y"], p["drill"] / 2, val)
        draw_circle(hd, p["x"], p["y"], p["drill"] / 2, 1)
    pad_of[(p["ref"], p["num"])] = p
lab = {L: torch.from_numpy(np.array(labels[L], dtype=np.int32)).to(DEV) for L in labels}
# outer-layer zone fills (local pours): other nets' pours are obstacles so a corridor never cuts a pour that
# carries current; ground-type pours may be crossed as a last resort (they are also served by inner planes).
zimg = {L: Image.new("I", (NX, NY), 0) for L in labels}
zdraw = {L: ImageDraw.Draw(zimg[L]) for L in labels}
for zz in G["zones"]:
    for L, polys in zz.get("fills", {}).items():
        if L in labels:
            for poly in polys:
                if poly and len(poly[0]) >= 3:
                    zdraw[L].polygon(ring_xy(poly[0]), fill=NID.get(zz["net"], 1))
                    for hole in poly[1:]:
                        for ring in (hole if hole and isinstance(hole[0][0], (list, tuple)) else [hole]):
                            if len(ring) >= 3:
                                zdraw[L].polygon(ring_xy(ring), fill=0)
zfill = {L: torch.from_numpy(np.array(zimg[L], dtype=np.int32)).to(DEV) for L in labels}
GND_RE = re.compile(r"GND|_0V$|AGND|_COM$|CHASSIS", re.I)
gnd_ids = torch.zeros(len(NID) + 2, dtype=torch.bool)
for n, i in NID.items():
    gnd_ids[i] = bool(GND_RE.search(n.split("/")[-1].split("{slash}")[-1]))
gnd_t = gnd_ids.to(DEV)
# rule areas: flagged no-track areas block every net; areas named *KEEPOUT* are blocked for every net except
# those the project's .kicad_dru rule exempts for that area (its "A.NetName != 'x'" terms)
_exempt = {}
for _cand in (os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "..", "board.kicad_dru"),
              os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "board.kicad_dru")):
    if os.path.exists(_cand):
        _txt = open(_cand, encoding="utf-8").read()
        for m_ in re.finditer(r"intersectsArea\('([^']+)'\)([^\n]*)", _txt):
            _exempt.setdefault(m_.group(1), set()).update(
                x.replace("{slash}", "/") for x in re.findall(r"A\.NetName != '([^']+)'", m_.group(2)))
        break
notrk = {}
area_masks = {L: [] for L in labels}
for L in labels:
    im = Image.new("1", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    for k in G["keepouts"]:
        name = str(k.get("name", ""))
        if L not in k["layers"]:
            continue
        if k["no_tracks"]:
            for e in k["outline"]:
                if len(e[0]) >= 3:
                    d.polygon(ring_xy(e[0]), fill=1)
        elif "KEEPOUT" in name.upper():
            im2 = Image.new("1", (NX, NY), 0)
            d2 = ImageDraw.Draw(im2)
            for e in k["outline"]:
                if len(e[0]) >= 3:
                    d2.polygon(ring_xy(e[0]), fill=1)
            area_masks[L].append((name, torch.from_numpy(np.array(im2, dtype=np.uint8)).to(DEV).bool(), _exempt.get(name, set())))
    notrk[L] = torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()


def notrk_for(layer, net_ids):
    """No-track raster for a job: flagged areas plus the named keepouts that do not exempt the job's nets."""
    inv = {v: k for k, v in NID.items()}
    names = {inv.get(n, "").replace("{slash}", "/") for n in net_ids}
    m = notrk[layer]
    for name, mask, ex in area_masks[layer]:
        if not (names & ex):
            m = m | mask
    return m


# V2: rule areas with no_vias block every via (all router vias are through vias, so an area on ANY copper
# layer applies) for every net except the .kicad_dru exemptions of the area's name, as for the named
# *KEEPOUT* areas above; one raster per area name (unnamed footprint rule areas share the name "")
_vk_img = {}
for _vk_k in G["keepouts"]:
    if not _vk_k.get("no_vias") or not any(_vk_L in LAYERS for _vk_L in _vk_k["layers"]):
        continue
    _vk_name = str(_vk_k.get("name", ""))
    if _vk_name not in _vk_img:
        _vk_img[_vk_name] = Image.new("1", (NX, NY), 0)
    _vk_d = ImageDraw.Draw(_vk_img[_vk_name])
    for _vk_e in _vk_k["outline"]:
        if len(_vk_e[0]) >= 3:
            _vk_d.polygon(ring_xy(_vk_e[0]), fill=1)
via_keepouts = [(_vk_name, torch.from_numpy(np.array(_vk_im, dtype=np.uint8)).to(DEV).bool(), _exempt.get(_vk_name, set()))
                for _vk_name, _vk_im in sorted(_vk_img.items())]
del _vk_img


def novia_for(net_ids):
    """Via keepout raster for a job: every no_vias rule area that does not exempt the job's nets."""
    inv = {v: k for k, v in NID.items()}
    names = {inv.get(n, "").replace("{slash}", "/") for n in net_ids}
    m = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
    for name, mask, ex in via_keepouts:
        if not (names & ex):
            m = m | mask
    return m
e = int(round(EDGE / RES))
edge_t = torch.ones((NY, NX), dtype=torch.bool, device=DEV)
edge_t[e:NY - e, e:NX - e] = False
print("rasters", NX, "x", NY, "on", DEV, flush=True)


def dilate(mask, r_mm):
    r = int(math.ceil(r_mm / RES))
    if r <= 0:
        return mask.clone()
    yy, xx = torch.meshgrid(torch.arange(-r, r + 1, device=DEV), torch.arange(-r, r + 1, device=DEV), indexing="ij")
    k = ((xx * xx + yy * yy) <= (r_mm / RES) ** 2).half()[None, None]
    out = torch.nn.functional.conv2d(mask.half()[None, None], k, padding=r)[0, 0]
    return out > 0.5


def blocked(layer, net_ids, dom_id, half_w, safe=None, cross_gnd=False, ignore=None):
    """Cells where a track centre of this width may NOT go: other copper dilated, keepouts, edge.
    Other nets' zone fills count as copper; with cross_gnd ground-type pours are ignored (last resort)."""
    SAFE_ = SAFE if safe is None else safe
    if half_w <= 0.13:          # signal widths: the quantisation margin of 0.12 mm is enough (clean-up catches the rest)
        SAFE_ = min(SAFE_, 0.12)
    L = lab[layer]
    own = torch.zeros_like(L, dtype=torch.bool)
    for nid in net_ids:
        own |= L == nid
    Z = zfill[layer]
    zown = torch.zeros_like(Z, dtype=torch.bool)
    for nid in net_ids:
        zown |= Z == nid
    zother = (Z > 0) & ~zown
    if cross_gnd:
        zother &= ~gnd_t[Z.long()]
    L = torch.where(zother & (L == 0), Z, L)
    other = (L > 0) & ~own
    if ignore is not None:
        other &= ~ignore
    same_dom = other & (dom_t[L.long()] == dom_id)
    cross = other & ~same_dom
    return dilate(same_dom, CLR + SAFE_ + half_w) | dilate(cross, XDOM + SAFE_ + half_w) | dilate(notrk_for(layer, net_ids), half_w + SAFE_) | dilate(edge_t, half_w + SAFE_)


def bfs(free, src, dst_mask):
    """Multi-source BFS with 8-neighbour moves on a boolean free raster (GPU, wavefront). Returns path cells."""
    H, W = free.shape
    dist = torch.full((H, W), -1, dtype=torch.int32, device=DEV)
    front = torch.zeros((H, W), dtype=torch.bool, device=DEV)
    for (iy, ix) in src:
        if 0 <= iy < H and 0 <= ix < W:
            front[iy, ix] = True
    front &= free
    dist[front] = 0
    k = torch.ones((1, 1, 3, 3), dtype=torch.half, device=DEV)
    step = 0
    reached = (front & dst_mask).any()
    while not reached and front.any() and step < 20000:
        step += 1
        nxt = torch.nn.functional.conv2d(front.half()[None, None], k, padding=1)[0, 0] > 0.5
        nxt &= free & (dist < 0)
        if not nxt.any():
            break
        dist[nxt] = step
        front = nxt
        reached = (front & dst_mask).any()
    if not reached:
        return None
    # backtrack from the nearest reached destination cell
    hit = torch.nonzero(front & dst_mask)[0]
    iy, ix = int(hit[0]), int(hit[1])
    path = [(iy, ix)]
    d = int(dist[iy, ix])
    dist_cpu = None
    while d > 0:
        d -= 1
        found = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny_, nx_ = iy + dy, ix + dx
                if 0 <= ny_ < H and 0 <= nx_ < W and int(dist[ny_, nx_]) == d:
                    iy, ix = ny_, nx_
                    found = True
                    break
            if found:
                break
        if not found:
            return None
        path.append((iy, ix))
    path.reverse()
    return path

STUB_OUT, STUB_W, SPLAY, FAN = 1.0, 0.2, 0.8, 1.6   # lead beyond the pad end, fine-pitch lead width, splay run, fan-out pitch
VIA_D, VIA_DRILL, VIA_PAIR_SPACING = 0.6, 0.3, 0.9
RUNWAY, RUNV = 1.0, 0.8   # straight full-width run beyond the lead ends / after a via pair
_via_ok_cache = {}
_via_static_cache = {}   # (nets, domain, R, margin) -> static via block raster (V1-V3); bounded below


def inner_copper():
    """Net-id rasters of the copper on the NON-rasterised inner layers (the plane layers In1/In2/In4; In3
    is rasterised and tested per layer) for a through via (V3): {layer: (tracks, zone fills)}. Tracks are
    drawn like the routed layers' tracks (line + round end caps) with their net id; every fill polygon
    (outline minus its holes) is composited on its own so a later polygon's hole never erases another
    zone's copper."""
    out = {}
    for L in LAYERS:
        if L in labels:
            continue
        ti = Image.new("I", (NX, NY), 0)
        td = ImageDraw.Draw(ti)
        for t in G["tracks"]:
            if t["layer"] == L:
                draw_track(td, t["a"], t["b"], t["w"], NID.get(t["net"], 1))
        fa = np.zeros((NY, NX), dtype=np.int32)
        for zz in G["zones"]:
            for poly in zz.get("fills", {}).get(L, []):
                if not poly or len(poly[0]) < 3:
                    continue
                outer = ring_xy(poly[0])
                bx0 = max(0, int(min(q[0] for q in outer)) - 1)
                by0 = max(0, int(min(q[1] for q in outer)) - 1)
                bx1 = min(NX, int(max(q[0] for q in outer)) + 2)
                by1 = min(NY, int(max(q[1] for q in outer)) + 2)
                if bx1 <= bx0 or by1 <= by0:
                    continue
                pm = Image.new("1", (bx1 - bx0, by1 - by0), 0)
                pd_ = ImageDraw.Draw(pm)
                pd_.polygon([(qx - bx0, qy - by0) for qx, qy in outer], fill=1)
                for hole in poly[1:]:
                    for ring in (hole if hole and isinstance(hole[0][0], (list, tuple)) else [hole]):
                        if len(ring) >= 3:
                            pd_.polygon([(qx - bx0, qy - by0) for qx, qy in ring_xy(ring)], fill=0)
                sub = fa[by0:by1, bx0:bx1]
                sub[np.array(pm, dtype=bool)] = NID.get(zz["net"], 1)
        out[L] = (torch.from_numpy(np.array(ti, dtype=np.int32)).to(DEV), torch.from_numpy(fa).to(DEV))
    return out


def via_pair_ok(LA, LB, net_ids, dom_id, R=None):
    """Cells where a via pair (two vias VIA_PAIR_SPACING apart, any orientation) can be placed: EVERY
    rasterised layer (F, In3, B; a through via crosses them all) free of other copper within the pair
    envelope, plane-layer copper kept at CLR (same domain) / XDOM (other domains, incl. their plane
    fills), via-only rule areas and the board edge (EDGE + envelope) respected, existing holes kept at
    hole-to-hole distance. R overrides the envelope radius (single via: VIA_D/2). LA/LB only key the
    cache."""
    R = VIA_PAIR_SPACING / 2 + VIA_D / 2 if R is None else R   # envelope radius around the centre
    key = (LA, LB, tuple(sorted(net_ids)), dom_id, round(R, 3))
    if key in _via_ok_cache:
        return _via_ok_cache[key]
    blk = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
    SAFE_V = min(SAFE, 0.12) if R <= VIA_D / 2 + 1e-9 else SAFE   # F3: single via: quantisation margin only
    for L in labels:   # through vias cross every layer: test every rasterised layer, not just LA/LB
        Lb = lab[L]
        own = torch.zeros_like(Lb, dtype=torch.bool)
        for nid in net_ids:
            own |= Lb == nid
        other = (Lb > 0) & ~own
        same_dom = other & (dom_t[Lb.long()] == dom_id)
        cross = other & ~same_dom
        blk |= dilate(same_dom, CLR + SAFE_V + R) | dilate(cross, XDOM + SAFE_V + R) | dilate(notrk_for(L, net_ids), R)
    global _inner
    if "_inner" not in globals():
        _inner = inner_copper()
    skey = (tuple(sorted(net_ids)), dom_id, round(R, 3), SAFE_V)
    if skey not in _via_static_cache:
        if len(_via_static_cache) >= 8:   # one full-board mask per entry: keep the GPU footprint bounded
            _via_static_cache.clear()
        # V3: plane-layer copper by domain: own net allowed, same-domain tracks at CLR, other-domain tracks
        # and other-domain zone fills at XDOM (a same-domain fill is knocked out around the via on refill)
        same_i = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
        cross_i = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
        for Ti, Fi in _inner.values():
            own = torch.zeros_like(Ti, dtype=torch.bool)
            for nid in net_ids:
                own |= Ti == nid
            other = (Ti > 0) & ~own
            sd = other & (dom_t[Ti.long()] == dom_id)
            same_i |= sd
            cross_i |= (other & ~sd) | ((Fi > 0) & (dom_t[Fi.long()] != dom_id))
        st = dilate(same_i, CLR + SAFE_V + R) | dilate(cross_i, XDOM + SAFE_V + R)
        # V2: via-only rule areas (all copper layers, .kicad_dru exemptions honoured)
        st |= dilate(novia_for(net_ids), R + SAFE_V)
        # V1: the via envelope keeps EDGE from the board edge: the track-centre band dilated by R + SAFE_V,
        # as blocked() dilates it by half_w + SAFE_ (its inner cell centre is 0.35 mm from the edge line)
        st |= dilate(edge_t, R + SAFE_V)
        _via_static_cache[skey] = st
    blk |= _via_static_cache[skey]
    hole_t = torch.from_numpy(np.array(holes, dtype=np.int32)).to(DEV) > 0
    blk |= dilate(hole_t, 0.25 + R)
    ok = ~blk & ~edge_t
    _via_ok_cache[key] = ok
    return ok


def bfs2(free_a, free_b, via_ok, src, dst_mask, dst_on="B"):
    """Two-layer wavefront BFS: 8-neighbour moves within a layer, layer change at via_ok cells.
    Returns a path of (layer, iy, ix) from a source cell on layer A to a destination cell on layer
    dst_on ("B" for a cross-side hop, "A" for a same-layer hop that may detour over the other layer)."""
    H, W = free_a.shape
    distA = torch.full((H, W), -1, dtype=torch.int32, device=DEV)
    distB = torch.full((H, W), -1, dtype=torch.int32, device=DEV)
    frontA = torch.zeros((H, W), dtype=torch.bool, device=DEV)
    frontB = torch.zeros((H, W), dtype=torch.bool, device=DEV)
    for (iy, ix) in src:
        if 0 <= iy < H and 0 <= ix < W:
            frontA[iy, ix] = True
    frontA &= free_a
    distA[frontA] = 0
    k = torch.ones((1, 1, 3, 3), dtype=torch.half, device=DEV)
    step = 0
    while step < 20000:
        if ((frontB if dst_on == "B" else frontA) & dst_mask).any():
            break
        if not (frontA.any() or frontB.any()):
            return None
        step += 1
        nA = (torch.nn.functional.conv2d(frontA.half()[None, None], k, padding=1)[0, 0] > 0.5) & free_a & (distA < 0)
        nB = (torch.nn.functional.conv2d(frontB.half()[None, None], k, padding=1)[0, 0] > 0.5) & free_b & (distB < 0)
        nB |= frontA & via_ok & free_b & (distB < 0)
        nA |= frontB & via_ok & free_a & (distA < 0)
        distA[nA] = step
        distB[nB] = step
        frontA, frontB = nA, nB
    else:
        return None
    hit = torch.nonzero((frontB if dst_on == "B" else frontA) & dst_mask)[0]
    L, iy, ix = dst_on, int(hit[0]), int(hit[1])
    d = int((distB if dst_on == "B" else distA)[iy, ix])
    path = [(L, iy, ix)]
    while d > 0:
        d -= 1
        cur, oth = (distA, distB) if L == "A" else (distB, distA)
        # prefer staying on the layer; a layer change only where the other layer holds d at the same cell
        found = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny_, nx_ = iy + dy, ix + dx
                if 0 <= ny_ < H and 0 <= nx_ < W and int(cur[ny_, nx_]) == d:
                    iy, ix = ny_, nx_
                    found = True
                    break
            if found:
                break
        if not found:
            if int(oth[iy, ix]) == d and bool(via_ok[iy, ix]):
                L = "B" if L == "A" else "A"
            else:
                return None
        path.append((L, iy, ix))
    path.reverse()
    return path


def single_escape(nid, did, Pd):
    return _escape(nid, did, Pd)


def route_single(net, nid, did, A, B, w, ladder=(0.25, 0.2), escapes=None):
    """Single track from pad A to pad B (any outer layers; one via if they differ), width w then necks.
    Returns (tracks, vias) in result format or None."""
    LA_ = next((L for L in A["layers"] if L in labels), None)
    LB_ = next((L for L in B["layers"] if L in labels), None)
    if LA_ is None or LB_ is None:
        return None
    if len([L for L in A["layers"] if L in labels]) >= 2 and LB_:   # through-hole pad: on every raster
        LA_ = LB_
    if len([L for L in B["layers"] if L in labels]) >= 2:
        LB_ = LA_
    def escape(Pd):
        return _escape(nid, did, Pd)

    eA, eB = escapes if escapes is not None else (escape(A), escape(B))
    return _route_single_body(net, nid, did, A, B, w, ladder, eA, eB)


def _escape(nid, did, Pd):
    if True:
        """Straight escape stub out of a fine-pitch row (pitch < 0.6 mm): returns (end point, cells mask)."""
        fpp = [q for q in G["pads"] if q["ref"] == Pd["ref"]]
        cxf, cyf = sum(q["x"] for q in fpp) / len(fpp), sum(q["y"] for q in fpp) / len(fpp)
        # F5: row detection for any footprint rotation: the row direction is taken from the nearest pads of
        # the footprint; a row needs >= 2 other pads on that line, the nearest within 1.0 mm; the stub leaves
        # the row perpendicularly, away from the footprint centroid
        others = sorted((q for q in fpp if q is not Pd), key=lambda q: math.hypot(q["x"] - Pd["x"], q["y"] - Pd["y"]))
        ox = oy = None
        row_pads = [Pd]
        for q1 in others[:2]:
            dq = math.hypot(q1["x"] - Pd["x"], q1["y"] - Pd["y"])
            if dq < 1e-6 or dq >= 1.0:
                continue
            rx_, ry_ = (q1["x"] - Pd["x"]) / dq, (q1["y"] - Pd["y"]) / dq
            on_line = [q for q in others if abs((q["x"] - Pd["x"]) * ry_ - (q["y"] - Pd["y"]) * rx_) < 0.05]
            if len(on_line) >= 2:
                nx_, ny_ = -ry_, rx_
                s_ = 1.0 if (Pd["x"] - cxf) * nx_ + (Pd["y"] - cyf) * ny_ >= 0 else -1.0
                ox, oy = s_ * nx_, s_ * ny_
                row_pads = [Pd] + on_line
                break
        if ox is None:
            return None
        ring = Pd["poly"][0][0]
        vals = [(x - Pd["x"]) * ox + (y - Pd["y"]) * oy for x, y in ring]
        ext = (max(vals) - min(vals)) / 2
        Lp = next((L for L in Pd["layers"] if L in labels), None)
        if Lp is None:
            return None
        # F1: the end is preferred free at the routing margin too, and the straight run from the pad end to
        # the escape end must not cross foreign copper (the row's own pads are ignored: a centred stub
        # between them is legal by construction when the pitch allows STUB_W)
        im_fp = Image.new("1", (NX, NY), 0)
        d_fp = ImageDraw.Draw(im_fp)
        for q in row_pads:
            for e in q["poly"]:
                if len(e[0]) >= 3:
                    d_fp.polygon(ring_xy(e[0]), fill=1)
        fp_mask = torch.from_numpy(np.array(im_fp, dtype=np.uint8)).to(DEV).bool()
        blk_ = blocked(Lp, {nid}, did, STUB_W / 2, safe=0.0, cross_gnd=True)
        blk_m = blocked(Lp, {nid}, did, STUB_W / 2, cross_gnd=True)
        # the run is checked WITH the raster margin (two independent cell roundings can hide 0.1 mm of a
        # true gap; DRC test 10 Oct: a stub 0.105 mm from a via passed a safe-0 check)
        blk_r = blocked(Lp, {nid}, did, STUB_W / 2, cross_gnd=True, ignore=fp_mask)

        def hit(blk, X, Y):
            cx_, cy_ = px(X, Y)
            iy_, ix_ = int(cy_), int(cx_)
            return not (0 <= iy_ < NY and 0 <= ix_ < NX) or bool(blk[iy_, ix_])

        for need_margin in (True, False):
            for extra in (0.6, 0.4, 0.25, 0.15):
                end = (Pd["x"] + ox * (ext + extra), Pd["y"] + oy * (ext + extra))
                if hit(blk_, *end) or (need_margin and hit(blk_m, *end)):
                    continue
                n_ = max(2, int((extra + 0.05) / RES) + 1)
                if any(hit(blk_r, Pd["x"] + ox * (ext - 0.05 + (extra + 0.05) * i / n_),
                           Pd["y"] + oy * (ext - 0.05 + (extra + 0.05) * i / n_)) for i in range(n_ + 1)):
                    continue
                cx_, cy_ = px(*end)
                im = Image.new("1", (NX, NY), 0)
                ImageDraw.Draw(im).ellipse([cx_ - 1, cy_ - 1, cx_ + 1, cy_ + 1], fill=1)
                return end, torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()
        return None



def _route_single_body(net, nid, did, A, B, w, ladder, eA, eB):
    LA_ = next((L for L in A["layers"] if L in labels), None)
    LB_ = next((L for L in B["layers"] if L in labels), None)
    if len([L for L in A["layers"] if L in labels]) >= 2 and LB_:   # through-hole pad: on every raster
        LA_ = LB_
    if len([L for L in B["layers"] if L in labels]) >= 2:
        LB_ = LA_
    src_m = eA[1] if eA else pad_cells(A)
    dst_m = eB[1] if eB else pad_cells(B)
    headA = [(A["x"], A["y"]), eA[0]] if eA else [(A["x"], A["y"])]
    tailB = [eB[0], (B["x"], B["y"])] if eB else [(B["x"], B["y"])]
    src = [tuple(int(v) for v in c) for c in torch.nonzero(src_m).tolist()]
    if DEBUG_DIR:
        print(f"debug single {net.split('/')[-1]} {A['ref']}.{A['num']}({LA_})->{B['ref']}.{B['num']}({LB_}) escapes {bool(eA)}/{bool(eB)} src {int(src_m.sum())} dst {int(dst_m.sum())}", flush=True)
    for cg in (False, True):
        for wt in [w] + [x for x in ladder if x < w]:
            freeA = ~blocked(LA_, {nid}, did, wt / 2, cross_gnd=cg) | dilate(src_m, wt / 2)
            if DEBUG_DIR:
                print(f"debug single   try w{wt} cg{cg}: src free {int((freeA & src_m).sum())}", flush=True)
            if LA_ == LB_:
                free = freeA | dilate(dst_m, wt / 2)
                path = bfs_win(free, src, dst_m)
                if path is None:
                    continue
                pts = [headA[-1]] + smooth_path([to_mm(ix, iy) for iy, ix in simplify(path)]) + [tailB[0]]
                out_ = [{"kind": "single", "net": net, "layer": LA_, "width": wt, "points": pts}]
                if eA:
                    out_.append({"kind": "stub", "net": net, "layer": LA_, "width": STUB_W, "points": headA})
                if eB:
                    out_.append({"kind": "stub", "net": net, "layer": LB_, "width": STUB_W, "points": tailB})
                return out_, []
            freeB = ~blocked(LB_, {nid}, did, wt / 2, cross_gnd=cg) | dilate(dst_m, wt / 2)
            via_ok = via_pair_ok(LA_, LB_, {nid}, did, R=VIA_D / 2)
            path3 = bfs2_win(freeA, freeB, via_ok, src, dst_m)
            if path3 is None:
                continue
            path3 = [(LA_ if L == "A" else LB_, iy, ix) for L, iy, ix in path3]
            legs = []
            for L, iy, ix in path3:
                if not legs or legs[-1][0] != L:
                    legs.append([L, []])
                legs[-1][1].append((iy, ix))
            tracks, vias = [], []
            for li, (L, cells) in enumerate(legs):
                pts = [to_mm(ix, iy) for iy, ix in (simplify(cells) if len(cells) >= 3 else cells)]
                pts = smooth_path(pts) if len(pts) >= 3 else pts
                if li == 0:
                    pts = [headA[-1]] + pts
                if li == len(legs) - 1:
                    pts = pts + [tailB[0]]
                if li > 0:
                    pts = [(vias[-1]["x"], vias[-1]["y"])] + pts
                if li < len(legs) - 1:
                    vx, vy = pts[-1]
                    vias.append({"kind": "via", "net": net, "x": vx, "y": vy, "d": VIA_D, "drill": VIA_DRILL})
                tracks.append({"kind": "single", "net": net, "layer": L, "width": wt, "points": pts})
            if eA:
                tracks.append({"kind": "stub", "net": net, "layer": LA_, "width": STUB_W, "points": headA})
            if eB:
                tracks.append({"kind": "stub", "net": net, "layer": LB_, "width": STUB_W, "points": tailB})
            return tracks, vias
    return None


def douglas_peucker(pts, tol):
    if len(pts) < 3:
        return list(pts)
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    best, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        x, y = pts[i]
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L if L > 1e-9 else math.hypot(x - x1, y - y1)
        if d > best:
            best, idx = d, i
    if best > tol:
        return douglas_peucker(pts[:idx + 1], tol)[:-1] + douglas_peucker(pts[idx:], tol)
    return [pts[0], pts[-1]]


def smooth_path(pts, tol=0.06, min_seg=0.3, chamfer=0.0):
    """Polyline clean-up for offsetting: Douglas-Peucker on the raster staircase, merge short segments,
    chamfer turns sharper than 90 degrees into two gentler ones. End points are kept exactly."""
    pts = douglas_peucker([tuple(q) for q in pts], tol)
    out = [pts[0]]
    for q in pts[1:-1]:
        if math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) >= min_seg:
            out.append(q)
    if len(pts) > 1:
        if len(out) > 1 and math.hypot(pts[-1][0] - out[-1][0], pts[-1][1] - out[-1][1]) < min_seg:
            out.pop()
        out.append(pts[-1])
    pts = out
    res = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        v1 = (b[0] - a[0], b[1] - a[1])
        v2 = (c[0] - b[0], c[1] - b[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        if l1 < 1e-9 or l2 < 1e-9:
            continue
        cosang = (v1[0] * v2[0] + v1[1] * v2[1]) / (l1 * l2)
        if chamfer > 0 and cosang < 0.05:  # turn > ~87 degrees: chamfer (off by default)
            t = min(chamfer, l1 / 2, l2 / 2)
            res.append((b[0] - v1[0] / l1 * t, b[1] - v1[1] / l1 * t))
            res.append((b[0] + v2[0] / l2 * t, b[1] + v2[1] / l2 * t))
        else:
            res.append(b)
    res.append(pts[-1])
    return res


def offset_poly(line, d):
    """Parallel offset of a polyline by signed distance d (left of travel for d > 0): per-segment
    parallel lines joined by their intersections (mitre), capped at 2|d| and bevelled beyond."""
    if len(line) < 2:
        return list(line)
    segs = []
    for (x1, y1), (x2, y2) in zip(line, line[1:]):
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-9:
            continue
        nx_, ny_ = -dy / L, dx / L
        segs.append(((x1 + d * nx_, y1 + d * ny_), (x2 + d * nx_, y2 + d * ny_)))
    if not segs:
        return [line[0], line[-1]]
    out = [segs[0][0]]
    for (a1, a2), (b1, b2) in zip(segs, segs[1:]):
        dax, day = a2[0] - a1[0], a2[1] - a1[1]
        dbx, dby = b2[0] - b1[0], b2[1] - b1[1]
        den = dax * dby - day * dbx
        if abs(den) < 1e-9:
            out.append(a2)
            continue
        t = ((b1[0] - a1[0]) * dby - (b1[1] - a1[1]) * dbx) / den
        ix, iy = a1[0] + dax * t, a1[1] + day * t
        if math.hypot(ix - a2[0], iy - a2[1]) <= 2 * abs(d):
            out.append((ix, iy))
        else:
            out.append(a2)
            out.append(b1)
    out.append(segs[-1][1])
    return out


def _window(masks, src, dst_mask, margin_mm):
    """Crop rasters to the bounding box of src cells and dst cells plus a margin."""
    ys = [iy for iy, ix in src]
    xs = [ix for iy, ix in src]
    nz = torch.nonzero(dst_mask)
    if len(nz) == 0 or not src:
        return None
    ys += [int(nz[:, 0].min()), int(nz[:, 0].max())]
    xs += [int(nz[:, 1].min()), int(nz[:, 1].max())]
    m = int(margin_mm / RES)
    y0, y1 = max(0, min(ys) - m), min(NY, max(ys) + m + 1)
    x0, x1 = max(0, min(xs) - m), min(NX, max(xs) + m + 1)
    return y0, y1, x0, x1


def bfs_win(free, src, dst_mask, margins=(12.0, 40.0, None)):
    """Windowed BFS: a window around the end points first (fast), the whole board as a last resort."""
    for margin in margins:
        if margin is None:
            return bfs(free, src, dst_mask)
        w = _window([], src, dst_mask, margin)
        if w is None:
            return None
        y0, y1, x0, x1 = w
        if (y1 - y0) * (x1 - x0) >= 0.6 * NY * NX:
            return bfs(free, src, dst_mask)
        sub = [(iy - y0, ix - x0) for iy, ix in src if y0 <= iy < y1 and x0 <= ix < x1]
        path = bfs(free[y0:y1, x0:x1], sub, dst_mask[y0:y1, x0:x1])
        if path is not None:
            return [(iy + y0, ix + x0) for iy, ix in path]
    return None


def bfs2_win(free_a, free_b, via_ok, src, dst_mask, dst_on="B", margins=(12.0, 40.0, None)):
    for margin in margins:
        if margin is None:
            return bfs2(free_a, free_b, via_ok, src, dst_mask, dst_on)
        w = _window([], src, dst_mask, margin)
        if w is None:
            return None
        y0, y1, x0, x1 = w
        if (y1 - y0) * (x1 - x0) >= 0.6 * NY * NX:
            return bfs2(free_a, free_b, via_ok, src, dst_mask, dst_on)
        sub = [(iy - y0, ix - x0) for iy, ix in src if y0 <= iy < y1 and x0 <= ix < x1]
        path = bfs2(free_a[y0:y1, x0:x1], free_b[y0:y1, x0:x1], via_ok[y0:y1, x0:x1], sub, dst_mask[y0:y1, x0:x1], dst_on)
        if path is not None:
            return [(L, iy + y0, ix + x0) for L, iy, ix in path]
    return None


def bfsN(frees, via_ok, src, dst_mask, dst_i):
    """N-layer wavefront BFS (generalises bfs2): 8-neighbour moves within a layer; at a via_ok cell the
    wave jumps from any layer to any other (a through via spans them all). Source cells are on layer 0,
    the destination mask applies on layer dst_i. Returns a path of (layer index, iy, ix) or None."""
    H, W = frees[0].shape
    n = len(frees)
    dist = [torch.full((H, W), -1, dtype=torch.int32, device=DEV) for _ in range(n)]
    front = [torch.zeros((H, W), dtype=torch.bool, device=DEV) for _ in range(n)]
    for (iy, ix) in src:
        if 0 <= iy < H and 0 <= ix < W:
            front[0][iy, ix] = True
    front[0] &= frees[0]
    dist[0][front[0]] = 0
    k = torch.ones((1, 1, 3, 3), dtype=torch.half, device=DEV)
    step = 0
    while step < 20000:
        if (front[dst_i] & dst_mask).any():
            break
        if not any(f.any() for f in front):
            return None
        step += 1
        via_from = torch.zeros((H, W), dtype=torch.bool, device=DEV)
        for f in front:
            via_from |= f
        via_from &= via_ok
        nxt = []
        for i in range(n):
            ni = (torch.nn.functional.conv2d(front[i].half()[None, None], k, padding=1)[0, 0] > 0.5)
            ni |= via_from & ~front[i]
            ni &= frees[i] & (dist[i] < 0)
            nxt.append(ni)
        for i in range(n):
            dist[i][nxt[i]] = step
        front = nxt
    else:
        return None
    hit = torch.nonzero(front[dst_i] & dst_mask)[0]
    L, iy, ix = dst_i, int(hit[0]), int(hit[1])
    d = int(dist[L][iy, ix])
    path = [(L, iy, ix)]
    while d > 0:
        d -= 1
        found = False
        for dy in (-1, 0, 1):   # prefer staying on the layer
            for dx in (-1, 0, 1):
                ny_, nx_ = iy + dy, ix + dx
                if 0 <= ny_ < H and 0 <= nx_ < W and int(dist[L][ny_, nx_]) == d:
                    iy, ix = ny_, nx_
                    found = True
                    break
            if found:
                break
        if not found:
            if not bool(via_ok[iy, ix]):
                return None
            for j in range(n):   # a layer change at this cell: the layer that holds d here
                if j != L and int(dist[j][iy, ix]) == d:
                    L = j
                    found = True
                    break
            if not found:
                return None
        path.append((L, iy, ix))
    path.reverse()
    return path


def bfsN_win(frees, via_ok, src, dst_mask, dst_i, margins=(12.0, 40.0, None)):
    for margin in margins:
        if margin is None:
            return bfsN(frees, via_ok, src, dst_mask, dst_i)
        w = _window([], src, dst_mask, margin)
        if w is None:
            return None
        y0, y1, x0, x1 = w
        if (y1 - y0) * (x1 - x0) >= 0.6 * NY * NX:
            return bfsN(frees, via_ok, src, dst_mask, dst_i)
        sub = [(iy - y0, ix - x0) for iy, ix in src if y0 <= iy < y1 and x0 <= ix < x1]
        path = bfsN([f[y0:y1, x0:x1] for f in frees], via_ok[y0:y1, x0:x1], sub, dst_mask[y0:y1, x0:x1], dst_i)
        if path is not None:
            return [(L, iy + y0, ix + x0) for L, iy, ix in path]
    return None


def pad_extent_xy(p):
    ring = p["poly"][0][0] if p["poly"] and p["poly"][0] else []
    if len(ring) < 3:
        return (0.5, 0.5)
    xs = [x for x, y in ring]
    ys = [y for x, y in ring]
    return (max(xs) - min(xs), max(ys) - min(ys))


def simplify(path):
    """Collapse collinear raster steps into segments (keeps 0/45/90 degree turns)."""
    if len(path) < 3:
        return path
    out = [path[0]]
    d_prev = (path[1][0] - path[0][0], path[1][1] - path[0][1])
    for i in range(1, len(path) - 1):
        d = (path[i + 1][0] - path[i][0], path[i + 1][1] - path[i][1])
        if d != d_prev:
            out.append(path[i])
            d_prev = d
    out.append(path[-1])
    return out


def paint(layer, pts_mm, w, nid):
    _via_ok_cache.clear()   # the via masks depend on lab[] and the holes image, which change here
    im = Image.new("I", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    for a, b in zip(pts_mm, pts_mm[1:]):
        draw_track(d, a, b, w, 1)
    m = torch.from_numpy(np.array(im, dtype=np.int32)).to(DEV) > 0
    m = m & (lab[layer] == 0)
    lab[layer][m] = nid
    return (layer, m)


def pad_cells(p):
    """Raster cells inside a pad polygon (on the pad's layer)."""
    im = Image.new("1", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    for e in p["poly"]:
        if len(e[0]) >= 3:
            d.polygon(ring_xy(e[0]), fill=1)
    return torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()


# ---- strict power mode (CORR_POWER_STRICT=1), added by tools/patch_power_strict.py ----------------------------
STRICT_COUNT = {"strict_jobs": 0, "routed": 0, "failed": 0, "jobs_without_amps": 0}
_R2 = math.sqrt(2.0)
OUTER = ("F.Cu", "B.Cu")


def _pad_short(p):
    """Smallest width of the pad polygon: minimum over the edge normals of the projected extent (exact for convex
    pads; the bounding-box short side for axis-aligned rectangles)."""
    ring = p["poly"][0][0] if p["poly"] and p["poly"][0] else []
    if len(ring) < 3:
        return min(pad_extent_xy(p))
    best = None
    n = len(ring)
    for i in range(n):
        (ax, ay), (bx, by) = ring[i], ring[(i + 1) % n]
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        nx_, ny_ = -(by - ay) / L, (bx - ax) / L
        vals = [(x - ax) * nx_ + (y - ay) * ny_ for x, y in ring]
        wd = max(vals) - min(vals)
        if best is None or wd < best:
            best = wd
    return best if best is not None else min(pad_extent_xy(p))


_SMD_VIA_EXCL = []


def _smd_via_excl():
    """Cells where a strict power via would touch an SMD pad of ANY net (own net included): via-in-pad is only for
    intentional, filled and capped vias, so the router never creates one by accident. Via disc + 0.1 mm mask web."""
    if not _SMD_VIA_EXCL:
        im = Image.new("1", (NX, NY), 0)
        d_ = ImageDraw.Draw(im)
        for p in G["pads"]:
            if p["smd"]:
                for e in p["poly"]:
                    if len(e[0]) >= 3:
                        d_.polygon(ring_xy(e[0]), fill=1)
        m_ = torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()
        _SMD_VIA_EXCL.append(dilate(m_, VIA_D / 2 + 0.1))
    return _SMD_VIA_EXCL[0]


def _neck_width(p, w):
    return round(max(0.2, min(w, 0.8 * _pad_short(p))), 3)


def _escape_w(nid, did, Pd, sw):
    """The verified straight escape (_escape) at width sw instead of STUB_W: out of a fine-pitch row, perpendicular,
    away from the footprint centroid. The row's own pads are ignored by the raster run check (as in _escape), so a
    lateral check is added: the stub, centred on its pad, must clear every row neighbour by the clearance (0.6 mm
    across domains) + 0.02 mm. Returns (end point, layer, run length beyond the pad end) or None."""
    fpp = [q for q in G["pads"] if q["ref"] == Pd["ref"]]
    cxf, cyf = sum(q["x"] for q in fpp) / len(fpp), sum(q["y"] for q in fpp) / len(fpp)
    others = sorted((q for q in fpp if q is not Pd), key=lambda q: math.hypot(q["x"] - Pd["x"], q["y"] - Pd["y"]))
    ox = oy = rx_ = ry_ = None
    row_pads = [Pd]
    for q1 in others[:2]:
        dq = math.hypot(q1["x"] - Pd["x"], q1["y"] - Pd["y"])
        if dq < 1e-6 or dq >= 1.0:
            continue
        rx_, ry_ = (q1["x"] - Pd["x"]) / dq, (q1["y"] - Pd["y"]) / dq
        on_line = [q for q in others if abs((q["x"] - Pd["x"]) * ry_ - (q["y"] - Pd["y"]) * rx_) < 0.05]
        if len(on_line) >= 2:
            nx_, ny_ = -ry_, rx_
            s_ = 1.0 if (Pd["x"] - cxf) * nx_ + (Pd["y"] - cyf) * ny_ >= 0 else -1.0
            ox, oy = s_ * nx_, s_ * ny_
            row_pads = [Pd] + on_line
            break
    if ox is None:
        return None
    for q in row_pads[1:]:
        if q["net"] and q["net"] == Pd["net"]:
            continue
        ring_q = q["poly"][0][0] if q["poly"] and q["poly"][0] and q["poly"][0][0] else None
        if not ring_q:
            return None
        lat = [(x - Pd["x"]) * rx_ + (y - Pd["y"]) * ry_ for x, y in ring_q]
        gap = min(abs(v) for v in lat) if (min(lat) > 0 or max(lat) < 0) else 0.0
        need = XDOM if (q["net"] and net_dom.get(q["net"], "DOM_LOGIC") != net_dom.get(Pd["net"], "DOM_LOGIC")) else CLR
        if gap - sw / 2 < need + 0.02:
            return None
    ring = Pd["poly"][0][0]
    vals = [(x - Pd["x"]) * ox + (y - Pd["y"]) * oy for x, y in ring]
    ext = (max(vals) - min(vals)) / 2
    Lp = next((L for L in Pd["layers"] if L in labels), None)
    if Lp is None:
        return None
    im_fp = Image.new("1", (NX, NY), 0)
    d_fp = ImageDraw.Draw(im_fp)
    for q in row_pads:
        for e in q["poly"]:
            if len(e[0]) >= 3:
                d_fp.polygon(ring_xy(e[0]), fill=1)
    fp_mask = torch.from_numpy(np.array(im_fp, dtype=np.uint8)).to(DEV).bool()
    blk_ = blocked(Lp, {nid}, did, sw / 2, safe=0.0, cross_gnd=True)
    blk_m = blocked(Lp, {nid}, did, sw / 2, cross_gnd=True)
    blk_r = blocked(Lp, {nid}, did, sw / 2, cross_gnd=True, ignore=fp_mask)

    def hit(blk, X, Y):
        cx_, cy_ = px(X, Y)
        iy_, ix_ = int(cy_), int(cx_)
        return not (0 <= iy_ < NY and 0 <= ix_ < NX) or bool(blk[iy_, ix_])

    for need_margin in (True, False):
        for extra in (0.6, 0.4, 0.25, 0.15):
            end = (Pd["x"] + ox * (ext + extra), Pd["y"] + oy * (ext + extra))
            if hit(blk_, *end) or (need_margin and hit(blk_m, *end)):
                continue
            n_ = max(2, int((extra + 0.05) / RES) + 1)
            if any(hit(blk_r, Pd["x"] + ox * (ext - 0.05 + (extra + 0.05) * i / n_),
                       Pd["y"] + oy * (ext - 0.05 + (extra + 0.05) * i / n_)) for i in range(n_ + 1)):
                continue
            return end, Lp, extra
    return None


def _neck_field(free_s, seeds, max_cells, fw):
    """Octile geodesic distance (in cells; orthogonal step 1, diagonal sqrt 2) over the free raster free_s from the
    seed cells {(iy, ix): d0}, cut at max_cells. Seeds are passable even when not free (an escape end is legal by
    construction). Cells legal at the trunk width (fw) are TERMINAL: a neck stops at the first wide-legal cell it
    meets and never runs on through wide-legal copper. Returns (distance window tensor with inf beyond reach,
    (y0, x0) window offset, terminal window mask)."""
    ys = [c[0] for c in seeds]
    xs = [c[1] for c in seeds]
    m = int(math.ceil(max_cells)) + 3
    wy0, wy1 = max(0, min(ys) - m), min(NY, max(ys) + m + 1)
    wx0, wx1 = max(0, min(xs) - m), min(NX, max(xs) + m + 1)
    term = fw[wy0:wy1, wx0:wx1]
    pas = free_s[wy0:wy1, wx0:wx1].clone()
    INF = float("inf")
    D = torch.full(pas.shape, INF, dtype=torch.float32, device=DEV)
    keys = list(seeds)
    sy = torch.tensor([k_[0] - wy0 for k_ in keys], dtype=torch.long, device=DEV)
    sx = torch.tensor([k_[1] - wx0 for k_ in keys], dtype=torch.long, device=DEV)
    D[sy, sx] = torch.tensor([float(seeds[k_]) for k_ in keys], dtype=torch.float32, device=DEV)
    pas[sy, sx] = True
    H_, W_ = D.shape
    lim = float(max_cells) + 1e-4
    for _ in range(4 * m + 8):
        Dp = torch.nn.functional.pad(torch.where(term, torch.full_like(D, INF), D)[None, None], (1, 1, 1, 1), value=INF)[0, 0]
        Dn = D.clone()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    Dn = torch.minimum(Dn, Dp[1 + dy:1 + dy + H_, 1 + dx:1 + dx + W_] + (_R2 if (dy and dx) else 1.0))
        Dn = torch.where(pas & (Dn <= lim), Dn, torch.full_like(Dn, INF))
        if torch.equal(Dn, D):
            break
        D = Dn
    return D, (wy0, wx0), term


def _neck_back(D, off, cell, seeds, term):
    """Cells of the octile geodesic from a seed to `cell` (seed first), or None. Terminal (wide-legal) cells are
    never intermediate cells of a neck."""
    wy0, wx0 = off
    Dc = D.cpu().numpy()
    Tc = term.cpu().numpy()
    H_, W_ = Dc.shape
    iy, ix = cell[0] - wy0, cell[1] - wx0
    if not (0 <= iy < H_ and 0 <= ix < W_) or not np.isfinite(Dc[iy, ix]):
        return None
    path = [(iy, ix)]
    for _ in range(100000):
        g = (iy + wy0, ix + wx0)
        if g in seeds and abs(float(Dc[iy, ix]) - seeds[g]) < 1e-3:
            break
        nxt = None
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if not (dy or dx):
                    continue
                ny_, nx_ = iy + dy, ix + dx
                if 0 <= ny_ < H_ and 0 <= nx_ < W_ and np.isfinite(Dc[ny_, nx_]) and not Tc[ny_, nx_]:
                    c = _R2 if (dy and dx) else 1.0
                    if abs(float(Dc[ny_, nx_]) + c - float(Dc[iy, ix])) < 1e-3:
                        nxt = (ny_, nx_)
                        break
            if nxt:
                break
        if nxt is None:
            return None
        iy, ix = nxt
        path.append((iy, ix))
    else:
        return None
    path.reverse()
    return [(a + wy0, b + wx0) for a, b in path]


def _pull(cells, free):
    """Line-of-sight shortening (string pulling) of a raster path on its free raster: the 8-neighbour BFS returns a
    Chebyshev-shortest staircase (long 45-degree doglegs); a shortcut between two path cells is taken only when every
    point sampled along it (4 samples per cell) falls in a free cell, i.e. it is as legal as the BFS moves themselves.
    End cells are kept. Returns the corner cells."""
    if len(cells) < 3:
        return list(cells)
    ys = [c[0] for c in cells]
    xs = [c[1] for c in cells]
    py0, px0 = min(ys), min(xs)
    Fm = free[py0:max(ys) + 1, px0:max(xs) + 1].cpu().numpy()

    def vis(a, b):
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 4) + 1
        t = np.linspace(0.0, 1.0, n + 1)
        yy = np.rint(a[0] + (b[0] - a[0]) * t).astype(int) - py0
        xx = np.rint(a[1] + (b[1] - a[1]) * t).astype(int) - px0
        return bool(Fm[yy, xx].all())

    out, i = [cells[0]], 0
    while i < len(cells) - 1:
        k = i + 1
        while k + 1 < len(cells) and vis(cells[i], cells[k + 1]):
            k += 1
        out.append(cells[k])
        i = k
    return out


def bfs2_oneway(free_a, free_b, via_ok, src, dst_mask):
    """bfs2 restricted to ONE layer change (A -> B, never back): the path carries exactly one via. Sources on layer A,
    destination mask on layer B. Returns [(layer "A"/"B", iy, ix), ...] or None."""
    H, W = free_a.shape
    distA = torch.full((H, W), -1, dtype=torch.int32, device=DEV)
    distB = torch.full((H, W), -1, dtype=torch.int32, device=DEV)
    frontA = torch.zeros((H, W), dtype=torch.bool, device=DEV)
    frontB = torch.zeros((H, W), dtype=torch.bool, device=DEV)
    for (iy, ix) in src:
        if 0 <= iy < H and 0 <= ix < W:
            frontA[iy, ix] = True
    frontA &= free_a
    distA[frontA] = 0
    k = torch.ones((1, 1, 3, 3), dtype=torch.half, device=DEV)
    step = 0
    while step < 20000:
        if (frontB & dst_mask).any():
            break
        if not (frontA.any() or frontB.any()):
            return None
        step += 1
        nA = (torch.nn.functional.conv2d(frontA.half()[None, None], k, padding=1)[0, 0] > 0.5) & free_a & (distA < 0)
        nB = (torch.nn.functional.conv2d(frontB.half()[None, None], k, padding=1)[0, 0] > 0.5) & free_b & (distB < 0)
        nB |= frontA & via_ok & free_b & (distB < 0)
        distA[nA] = step
        distB[nB] = step
        frontA, frontB = nA, nB
    else:
        return None
    hit = torch.nonzero(frontB & dst_mask)[0]
    L, iy, ix = "B", int(hit[0]), int(hit[1])
    d = int(distB[iy, ix])
    path = [(L, iy, ix)]
    while d > 0:
        d -= 1
        cur = distA if L == "A" else distB
        found = False
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny_, nx_ = iy + dy, ix + dx
                if 0 <= ny_ < H and 0 <= nx_ < W and int(cur[ny_, nx_]) == d:
                    iy, ix = ny_, nx_
                    found = True
                    break
            if found:
                break
        if not found:
            if L == "B" and int(distA[iy, ix]) == d and bool(via_ok[iy, ix]):
                L = "A"
            else:
                return None
        path.append((L, iy, ix))
    path.reverse()
    return path


def bfs2_oneway_win(free_a, free_b, via_ok, src, dst_mask, margins=(12.0, 40.0, None)):
    for margin in margins:
        if margin is None:
            return bfs2_oneway(free_a, free_b, via_ok, src, dst_mask)
        w_ = _window([], src, dst_mask, margin)
        if w_ is None:
            return None
        wy0, wy1, wx0, wx1 = w_
        if (wy1 - wy0) * (wx1 - wx0) >= 0.6 * NY * NX:
            return bfs2_oneway(free_a, free_b, via_ok, src, dst_mask)
        sub = [(iy - wy0, ix - wx0) for iy, ix in src if wy0 <= iy < wy1 and wx0 <= ix < wx1]
        path = bfs2_oneway(free_a[wy0:wy1, wx0:wx1], free_b[wy0:wy1, wx0:wx1], via_ok[wy0:wy1, wx0:wx1], sub,
                           dst_mask[wy0:wy1, wx0:wx1])
        if path is not None:
            return [(L, iy + wy0, ix + wx0) for L, iy, ix in path]
    return None


def _strict_end(P, L, nid, did, sw, cg, pad_m, fw, esc):
    """Neck field of one job end on layer L: seeds = pad cells legal at sw (distance 0) plus the escape end (distance
    = escape run beyond the pad end); wide = cells legal at the trunk width reachable within ENTRY_MM.
    Returns (end record or None, reason)."""
    free_s = ~blocked(L, {nid}, did, sw / 2, cross_gnd=cg)
    seeds = {}
    for c in torch.nonzero(pad_m & free_s).tolist():
        seeds[(int(c[0]), int(c[1]))] = 0.0
    esc_rec = None
    if esc and esc[1] == L:
        cx_, cy_ = px(*esc[0])
        cell = (int(cy_), int(cx_))
        if 0 <= cell[0] < NY and 0 <= cell[1] < NX:
            d0 = esc[2] / RES
            if cell not in seeds or seeds[cell] > d0:
                seeds[cell] = d0
            esc_rec = (esc[0], cell)
    if not seeds:
        return None, f"no start legal at the neck width {sw} mm on {L} at pad {P['ref']}.{P['num']}"
    D, off, term = _neck_field(free_s, seeds, ENTRY_MM / RES, fw)
    wy0, wx0 = off
    front = torch.isfinite(D) & term          # first wide-legal cells (in-pad wide-legal seeds included, distance 0)
    if not bool(front.any()):
        return None, (f"no cell legal at the trunk width within {ENTRY_MM} mm of pad {P['ref']}.{P['num']} on {L} "
                      f"(neck width {sw} mm)")
    # trunk start tiers: the shortest necks first (in-pad start when the pad allows the trunk width), then necks up to
    # 1 mm longer than the shortest, then every first wide-legal cell within ENTRY_MM (multi-source)
    dmin = float(D[front].min())
    tiers, last = [], -1
    for thr in (dmin + 1e-3, dmin + 1.0 / RES + 1e-3, float("inf")):
        mw = front & (D <= thr)
        k_ = int(mw.sum())
        if k_ != last:
            g_ = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
            g_[wy0:wy0 + D.shape[0], wx0:wx0 + D.shape[1]] = mw
            tiers.append(g_)
            last = k_
    return {"pad": P, "layer": L, "sw": sw, "seeds": seeds, "D": D, "off": off, "term": term, "tiers": tiers,
            "esc": esc_rec, "dmin_mm": round(dmin * RES, 3)}, ""


def _emit_end(E, cell, net, nid, info, end_name):
    """Neck (or, for a trunk end inside the pad, the verified in-pad pad stub) from the pad to the trunk end cell."""
    P, L, sw = E["pad"], E["layer"], E["sw"]
    cells = _neck_back(E["D"], E["off"], cell, E["seeds"], E["term"])
    if cells is None:
        raise RuntimeError(f"neck backtrack failed at {P['ref']}.{P['num']}")
    wy0, wx0 = E["off"]
    dlen = float(E["D"][cell[0] - wy0, cell[1] - wx0]) * RES
    seed = cells[0]
    via_esc = E["esc"] is not None and seed == E["esc"][1] and E["seeds"].get(seed, 0.0) > 0.0
    # pad centre -> (escape end) -> neck cells from the seed cell to the trunk end cell (the trunk starts exactly there)
    pts = [(P["x"], P["y"])] + ([tuple(E["esc"][0])] if via_esc else [])
    pts += [to_mm(ix, iy) for iy, ix in (simplify(cells) if len(cells) >= 3 else cells)]
    dd = []
    for q in pts:
        if not dd or math.hypot(q[0] - dd[-1][0], q[1] - dd[-1][1]) > 1e-6:
            dd.append(q)
    pts = dd
    total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    kind = "neck" if (via_esc or dlen > 1e-6) else "padstub"
    if len(pts) < 2 or (kind == "padstub" and total <= 0.01):
        return None
    item = {"kind": kind, "net": net, "layer": L, "width": sw, "points": pts, "end": end_name, "pad": [P["ref"], P["num"]]}
    item.update(info)
    if kind == "neck":
        item.update({"length": round(dlen, 3), "length_total": round(total, 3), "escape": via_esc})
    results.append(item)
    paint(L, pts, sw, nid)
    return item


def route_power_strict(job, job_index):
    net, w, layer = job["net"], float(job["width"]), job["layer"]
    amps = float(job["amps"])
    n_req = max(1, int(math.ceil(amps / I_VIA - 1e-9)))
    nid, did = NID[net], DID[net_dom.get(net, "DOM_LOGIC")]
    A = pad_of[tuple(job["from"])]
    B = pad_of[tuple(job["to"])]
    STRICT_COUNT["strict_jobs"] += 1
    swA, swB = _neck_width(A, w), _neck_width(B, w)

    def fail(why):
        STRICT_COUNT["failed"] += 1
        failures.append({"job": job, "why": why, "strict": True, "n_req": n_req, "amps": amps, "width_requested": w,
                         "neck_widths": [swA, swB], "job_index": job_index})
        print(f"power-strict {net} {A['ref']}.{A['num']}->{B['ref']}.{B['num']} w{w} n_req {n_req}: FAILED ({why})", flush=True)

    LA_ = [L for L in A["layers"] if L in OUTER]
    LB_ = [L for L in B["layers"] if L in OUTER]
    if not LA_ or not LB_:
        fail("pad not on an outer layer")
        return
    shared = [L for L in OUTER if L in LA_ and L in LB_]
    cross_side = not shared
    if cross_side and n_req >= 2:
        fail(f"needs {n_req} vias per transition: left for the power via-array tool")
        return
    if cross_side:
        plans = [(layer if layer in LA_ else LA_[0], LB_[0])]
    else:
        plans = [(L, L) for L in ([layer] if layer in shared else []) + [L for L in shared if L != layer]]
    pmA, pmB = pad_cells(A), pad_cells(B)
    escA = _escape_w(nid, did, A, swA)
    escB = _escape_w(nid, did, B, swB)
    reasons = []
    info = {"job_index": job_index, "n_req": n_req, "amps": amps, "width_requested": w, "strict": True}
    for cg in (False, True):
        for LA, LB in plans:
            fwA = ~blocked(LA, {nid}, did, w / 2, cross_gnd=cg)
            fwB = fwA if LB == LA else ~blocked(LB, {nid}, did, w / 2, cross_gnd=cg)
            EA, why = _strict_end(A, LA, nid, did, swA, cg, pmA, fwA, escA)
            if EA is None:
                reasons.append((1, why))
                continue
            EB, why = _strict_end(B, LB, nid, did, swB, cg, pmB, fwB, escB)
            if EB is None:
                reasons.append((1, why))
                continue
            path3 = None
            via_ok_ = (via_pair_ok(LA, LB, {nid}, did, R=VIA_D / 2) & ~_smd_via_excl()) if LA != LB else None
            nt = max(len(EA["tiers"]), len(EB["tiers"]))
            for k in range(nt):
                mA, mB = EA["tiers"][min(k, len(EA["tiers"]) - 1)], EB["tiers"][min(k, len(EB["tiers"]) - 1)]
                src = [tuple(int(v) for v in c) for c in torch.nonzero(mA).tolist()]
                mg = (12.0, 40.0, None) if k == nt - 1 else (12.0, 40.0)   # whole-board search only for the last tier
                if LA == LB:
                    path = bfs_win(fwA, src, mB, margins=mg)
                    path3 = [(LA, iy, ix) for iy, ix in path] if path is not None else None
                else:
                    p3 = bfs2_oneway_win(fwA, fwB, via_ok_, src, mB, margins=mg)
                    path3 = [(LA if L == "A" else LB, iy, ix) for L, iy, ix in p3] if p3 is not None else None
                if path3 is not None:
                    break
            free3 = None
            if path3 is None and STRICT_IN3 and n_req == 1:
                free3 = ~blocked("In3.Cu", {nid}, did, w / 2, cross_gnd=cg)
                srcs = [tuple(int(v) for v in c) for c in torch.nonzero(EA["tiers"][-1]).tolist()]
                mB_ = EB["tiers"][-1]
                if LA == LB:
                    v3 = via_pair_ok(LA, "In3.Cu", {nid}, did, R=VIA_D / 2) & ~_smd_via_excl()
                    p3 = bfs2_win(fwA, free3, v3, srcs, mB_, dst_on="A", margins=(12.0, 40.0))
                    path3 = [(LA if L == "A" else "In3.Cu", iy, ix) for L, iy, ix in p3] if p3 is not None else None
                else:
                    v3 = via_pair_ok(LA, LB, {nid}, did, R=VIA_D / 2) & ~_smd_via_excl()
                    p3 = bfsN_win([fwA, free3, fwB], v3, srcs, mB_, 2, margins=(12.0, 40.0))
                    path3 = [((LA, "In3.Cu", LB)[li], iy, ix) for li, iy, ix in p3] if p3 is not None else None
                if path3 is not None:
                    # the two-layer wavefront may change layer more than once: only one dive to In3 and one return
                    # (three legs at most) keeps one via per transition, anything else is rejected as no path
                    _nl = 1 + sum(1 for i_ in range(1, len(path3)) if path3[i_][0] != path3[i_ - 1][0])
                    if _nl > 3:
                        path3 = None
            if path3 is None:
                reasons.append((2, f"no path at the table width {w} mm on {LA}{'->' + LB if LB != LA else ''}"
                                   f"{' (ground pours crossable)' if cg else ''}"))
                continue
            legs = []
            for L, iy, ix in path3:
                if not legs or legs[-1][0] != L:
                    legs.append([L, []])
                legs[-1][1].append((iy, ix))
            nvias = len(legs) - 1
            in3_legs = sum(1 for L_, _c in legs if L_ == "In3.Cu")
            if in3_legs and not (STRICT_IN3 and n_req == 1):
                raise RuntimeError("strict invariant broken: In3 leg without CORR_STRICT_IN3 / n_req 1")
            if nvias > (1 if cross_side else 0) + (2 if in3_legs and not cross_side else 1 if in3_legs else 0):
                raise RuntimeError(f"strict invariant broken: {nvias} vias on a {'cross-side' if cross_side else 'same-layer'} job")
            info_j = dict(info, vias=nvias, vias_per_transition=1 if nvias else 0, cross_side=cross_side, in3_legs=in3_legs)
            trunk_mm = 0.0
            for li, (L, cells) in enumerate(legs):
                pts = [to_mm(ix, iy) for iy, ix in _pull(cells, fwA if L == LA else (fwB if L == LB else free3))]
                if len(pts) >= 2:
                    it = {"kind": "power", "net": net, "layer": L, "width": w, "points": pts, "crosses_ground_pour": cg}
                    it.update(info_j)
                    results.append(it)
                    paint(L, pts, w, nid)
                    trunk_mm += sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
                if li < len(legs) - 1:
                    vx, vy = pts[-1]
                    v_ = {"kind": "via", "net": net, "x": vx, "y": vy, "d": VIA_D, "drill": VIA_DRILL, "power_via": True}
                    v_.update(info_j)
                    results.append(v_)
                    for L2_ in labels:
                        paint(L2_, [(vx, vy), (vx, vy)], VIA_D, nid)
                    draw_circle(hd, vx, vy, VIA_DRILL / 2, 1)
            nA_ = _emit_end(EA, (path3[0][1], path3[0][2]), net, nid, info_j, "from")
            nB_ = _emit_end(EB, (path3[-1][1], path3[-1][2]), net, nid, info_j, "to")
            STRICT_COUNT["routed"] += 1
            necks = [n_ for n_ in (nA_, nB_) if n_ and n_["kind"] == "neck"]
            print(f"power-strict {net} {A['ref']}.{A['num']}->{B['ref']}.{B['num']} {LA}{'->' + LB if LB != LA else ''} "
                  f"w{w} trunk {trunk_mm:.1f} mm, vias {nvias} (n_req {n_req}), necks "
                  f"{[(n_['width'], n_['length']) for n_ in necks]}", flush=True)
            return
    fail(max(reasons, key=lambda r: r[0])[1] if reasons else "no attempt")


results, failures = [], []
LEADS = {}
LEAD_CELLS = {}
PASS_THROUGH = set()
DONE_JOBS = 0
if CKPT and _os.path.exists(CKPT):
    try:
        _ck = json.load(open(CKPT, encoding="utf-8"))
    except Exception:
        _ck = None
    if _ck and _ck.get("jobs_sha") == JOBS_SHA:
        results, failures, DONE_JOBS = _ck["tracks"], _ck["failures"], int(_ck["done"])
        for t_ in results:
            if t_.get("kind") == "via":
                for L_ in labels:
                    paint(L_, [(t_["x"], t_["y"]), (t_["x"], t_["y"])], t_["d"], NID.get(t_["net"], 1))
                draw_circle(hd, t_["x"], t_["y"], t_["drill"] / 2, 1)
            elif t_.get("layer") in labels:
                paint(t_["layer"], t_["points"], t_["width"], NID.get(t_["net"], 1))
        print(f"resumed from checkpoint: {DONE_JOBS} jobs done, {len(results)} items, {len(failures)} failures", flush=True)
_last_flush = _time.time()
_job_index = 0
# phase 0 prepares and paints every pair job's leads (reserving the escape lanes); phase 1 routes all jobs
for PREPARE_ONLY, job in [(True, j) for j in JOBS if j["kind"] == "pair"] + [(False, j) for j in JOBS]:
    kind = job["kind"]
    if not PREPARE_ONLY:
        _job_index += 1
        if _job_index <= DONE_JOBS:
            continue
        if _time.time() - _last_flush >= CKPT_SECONDS:
            ckpt_write(results, failures, _job_index - 1)
            _last_flush = _time.time()
    if kind == "power" and POWER_STRICT:
        if "amps" in job:
            route_power_strict(job, _job_index)
            continue
        STRICT_COUNT["jobs_without_amps"] += 1
    if kind == "power":
        net, w, layer = job["net"], job["width"], job["layer"]
        nid, did = NID[net], DID[net_dom.get(net, "DOM_LOGIC")]
        A = pad_of[tuple(job["from"])]
        B = pad_of[tuple(job["to"])]
        src_m = pad_cells(A)
        dst_m = pad_cells(B)
        src = [tuple(int(v) for v in c) for c in torch.nonzero(src_m).tolist()]
        # Width ladder: the requested width first, then neck-down steps (a hop between small pads cannot take
        # the trunk width); the width actually used is recorded so the caller can audit current capacity.
        ladder = [w] + [x for x in (2.0, 1.2, 0.8, 0.5, 0.3, 0.2) if x < w]   # neck-down steps; the audit flags trunk necks
        path, used, crossed = None, None, False
        # the attempted width is capped by the smaller end pad (a trunk never attaches to a 0603 at 3.5 mm;
        # the audit reports necks between large pads)
        ext_a = max(pad_extent_xy(A))
        ext_b = max(pad_extent_xy(B))
        cap = max(0.2, round(1.3 * min(ext_a, ext_b) * 20) / 20)
        ladder = sorted({min(x, cap) for x in ladder}, reverse=True)
        LA_ = [L for L in A["layers"] if L in labels]
        LB_ = [L for L in B["layers"] if L in labels]
        cross_side = bool(LA_) and bool(LB_) and not (set(LA_) & set(LB_))
        layerA = layer if layer in LA_ or not LA_ else LA_[0]
        layerB = layerA if not cross_side else LB_[0]
        path3 = None
        escA = escB = None
        for cg in (False, True):
            for i_w, wt in enumerate(ladder):
                free = ~blocked(layerA, {nid}, did, wt / 2, cross_gnd=cg)
                # no halo: the start/end cells are the pad cells that are legal for this width, so a track of
                # this width never overlaps a neighbouring pad or via; too narrow a lane means the next width
                src_w = [c for c in src if free[c[0], c[1]]]
                if wt <= 0.25:
                    # F2: fine-pitch pad: a straight escape stub (legal by construction between the row's own
                    # pads) is an EXTRA source even when the pad has free cells: at <= 0.8 mm pitch the legal
                    # pad cells are a thin strip that the neighbours' dilation closes at both ends
                    if escA is None:
                        escA = _escape(nid, did, A) or False
                    if escA:
                        src_w = src_w + [tuple(int(v) for v in c) for c in torch.nonzero(escA[1] & free & ~src_m).tolist()]
                if not src_w:
                    continue
                dst_use = dst_m
                if not cross_side:
                    if wt <= 0.25:
                        if escB is None:
                            escB = _escape(nid, did, B) or False
                        if escB:
                            dst_use = dst_m | escB[1]
                    if not bool((dst_use & free).any()):
                        continue
                    path = bfs_win(free, src_w, dst_use & free, margins=(12.0, 40.0, None) if i_w == 0 else (12.0, 40.0))
                    if path is not None:
                        path3 = [(layerA, iy, ix) for iy, ix in path]
                    elif wt <= 0.3 and VIA_DETOUR:
                        # blocked on this layer: drop to the inner signal layer In3 with two vias, run there
                        # and come back up; the opposite outer layer is the second choice
                        otherL = "B.Cu" if layerA == "F.Cu" else "F.Cu"
                        for detL in ("In3.Cu", otherL):
                            freeO = ~blocked(detL, {nid}, did, wt / 2, cross_gnd=cg)
                            via_ok_ = via_pair_ok(layerA, detL, {nid}, did, R=VIA_D / 2)
                            # windowed only: a whole-board two-layer search per failing hop costs minutes
                            p3 = bfs2_win(free, freeO, via_ok_, src_w, dst_use & free, dst_on="A", margins=(12.0, 40.0))
                            if p3 is not None:
                                path3 = [(layerA if L == "A" else detL, iy, ix) for L, iy, ix in p3]
                                break
                else:
                    freeB_ = ~blocked(layerB, {nid}, did, wt / 2, cross_gnd=cg)
                    dst_use = dst_m
                    if wt <= 0.25:
                        if escB is None:
                            escB = _escape(nid, did, B) or False
                        if escB:
                            dst_use = dst_m | escB[1]
                    if not bool((dst_use & freeB_).any()):
                        continue
                    via_ok_ = via_pair_ok(layerA, layerB, {nid}, did, R=VIA_D / 2)
                    path3 = bfs2_win(free, freeB_, via_ok_, src_w, dst_use & freeB_)
                    if path3 is not None:
                        path3 = [(layerA if L == "A" else layerB, iy, ix) for L, iy, ix in path3]
                    elif wt <= 0.3 and VIA_DETOUR:
                        # boxed in on both outer layers: F -> In3 -> B with two vias (three-layer wavefront)
                        free3_ = ~blocked("In3.Cu", {nid}, did, wt / 2, cross_gnd=cg)
                        p3 = bfsN_win([free, free3_, freeB_], via_ok_, src_w, dst_use & freeB_, 2, margins=(12.0, 40.0))
                        if p3 is not None:
                            path3 = [((layerA, "In3.Cu", layerB)[li], iy, ix) for li, iy, ix in p3]
                if path3 is not None:
                    used, crossed = wt, cg
                    path = [(iy, ix) for L, iy, ix in path3]
                    break
            if path3 is not None:
                break
        if path3 is None:
            failures.append({"job": job, "why": "no path"})
            if DEBUG_DIR:  # crop of the free raster at the smallest width around both pads, src/dst marked
                import os
                wt = ladder[-1]
                free = ~blocked(layer, {nid}, did, wt / 2)
                free |= dilate(src_m, wt / 2) | dilate(dst_m, wt / 2)
                x0c, x1c = int(px(min(A["x"], B["x"]) - 4, 0)[0]), int(px(max(A["x"], B["x"]) + 4, 0)[0])
                y0c, y1c = int(px(0, min(A["y"], B["y"]) - 4)[1]), int(px(0, max(A["y"], B["y"]) + 4)[1])
                crop = free[max(y0c, 0):y1c, max(x0c, 0):x1c].cpu().numpy().astype(np.uint8) * 200
                img = np.stack([crop, crop, crop], axis=-1)
                for m, col in ((src_m, (255, 0, 0)), (dst_m, (0, 0, 255))):
                    cm = m[max(y0c, 0):y1c, max(x0c, 0):x1c].cpu().numpy()
                    img[cm] = col
                Image.fromarray(img).save(os.path.join(DEBUG_DIR, f"fail_{A['ref']}_{A['num']}_{B['ref']}_{B['num']}.png"))
                inv = {v: k for k, v in NID.items()}
                vals, cnts = torch.unique(lab[layer][max(y0c, 0):y1c, max(x0c, 0):x1c], return_counts=True)
                print("debug labels in crop:", {inv.get(int(v), "<unnamed>" if int(v) == 1 else int(v)): int(c) for v, c in zip(vals, cnts)}, flush=True)
                nk = notrk[layer][max(y0c, 0):y1c, max(x0c, 0):x1c]
                print("debug no-track keepout cells in crop:", int(nk.sum()), flush=True)
                print(f"debug: src free cells {int((free & src_m).sum())} of {int(src_m.sum())}, dst free {int((free & dst_m).sum())}, "
                      f"free in crop {int(crop.astype(bool).sum())} / {crop.size}", flush=True)
            continue
        # legs per layer; the track starts/ends on the legal pad cells (never extended to the pad centre, so
        # a wide track cannot overlap the neighbouring pad); a layer change places one via
        legs = []
        for L, iy, ix in path3:
            if not legs or legs[-1][0] != L:
                legs.append([L, []])
            legs[-1][1].append((iy, ix))
        nvias = 0
        for li, (L, cells) in enumerate(legs):
            pts = [to_mm(ix, iy) for iy, ix in (simplify(cells) if len(cells) >= 3 else cells)]
            if len(pts) >= 2:   # a one-cell leg is just the via position: the via and the pad stub connect it
                results.append({"kind": "power", "net": net, "layer": L, "width": used, "width_requested": w, "points": pts,
                                "crosses_ground_pour": crossed, "cross_side": cross_side, "job_index": _job_index})
                paint(L, pts, used, nid)
            # narrow stubs (no wider than the pad) from the end cells to the pad centres keep the end points
            # inside the pads (KiCad flags a cell centre just outside the outline as dangling); an escape stub
            # (fine-pitch row) runs pad centre -> escape end -> first path point at STUB_W
            # the escape stub is emitted when the path starts/ends on the escape cell rather than on a pad cell
            for is_first, pad_, esc_ in ((li == 0, A, escA if escA and not bool(src_m[path3[0][1], path3[0][2]]) else None),
                                         (li == len(legs) - 1, B, escB if escB and not bool(dst_m[path3[-1][1], path3[-1][2]]) else None)):
                if is_first:
                    endp = pts[0] if pad_ is A else pts[-1]
                    if esc_:
                        stub_ = [(pad_["x"], pad_["y"]), esc_[0], endp]
                        results.append({"kind": "stub", "net": net, "layer": L, "width": STUB_W, "points": stub_})
                        paint(L, stub_, STUB_W, nid)
                        continue
                    ex_, ey_ = pad_extent_xy(pad_)
                    sw_ = max(0.2, min(used, 0.8 * min(ex_, ey_)))   # the board rule keeps every track >= 0.20 mm
                    stub_ = [endp, (pad_["x"], pad_["y"])]
                    if math.hypot(stub_[0][0] - stub_[1][0], stub_[0][1] - stub_[1][1]) > 0.01:
                        results.append({"kind": "padstub", "net": net, "layer": L, "width": sw_, "points": stub_})
                        paint(L, stub_, sw_, nid)
            if li < len(legs) - 1:
                vx, vy = pts[-1]
                v_ = {"kind": "via", "net": net, "x": vx, "y": vy, "d": VIA_D, "drill": VIA_DRILL, "power_via": True}
                results.append(v_)
                for L2_ in labels:
                    paint(L2_, [(vx, vy), (vx, vy)], VIA_D, nid)
                draw_circle(hd, vx, vy, VIA_DRILL / 2, 1)
                nvias += 1
        print(f"power {net} {layerA}{'->' + layerB if cross_side else ''} w{used}{'' if used == w else f' (req {w})'}: "
              f"{len(path)} cells, {len(path) * RES:.1f} mm, vias {nvias}"
              f"{' via In3' if any(L == 'In3.Cu' for L, _ in legs) else ''}", flush=True)
    elif kind == "pair":
        netP, netN, w, s = job["nets"][0], job["nets"][1], job["width"], job["gap"]
        nidP, nidN = NID[netP], NID[netN]
        did = DID[net_dom.get(netP, "DOM_LOGIC")]
        corridor = 2 * w + s
        AP, AN = pad_of[tuple(job["from"][0])], pad_of[tuple(job["from"][1])]
        BP, BN = pad_of[tuple(job["to"][0])], pad_of[tuple(job["to"][1])]

        def end_layer(p, fallback):
            Ls = [L for L in p["layers"] if L in labels]
            return Ls[0] if len(Ls) == 1 else fallback

        LA = end_layer(AP, job["layer"])
        LB = end_layer(BP, LA)

        def pad_extent(p, ux, uy):
            ring = p["poly"][0][0]
            vals = [(x - p["x"]) * ux + (y - p["y"]) * uy for x, y in ring]
            return max(vals) - min(vals)

        def prepare_end(P, N, L):
            """Leads from the two pads to a clean start point outside the pin field, on layer L:
            * outward direction = from the footprint centroid to the pad pair, snapped to the nearest axis;
            * both leads end at the same outward depth (ext + STUB_OUT beyond the outermost pad of the two);
            * then a splay/converge run of SPLAY so the centres end (w+s) apart, with a fan-out shift when
              several pair jobs leave the same pad row (FAN per rank), so neighbouring pairs do not collide;
            * lead width = pair width when the pad pitch allows it, else STUB_W (fine pitch);
            * a lead that would cross other copper is dropped (plain pad-centre start as before).
            Returns (corridor centre, lead points P, lead points N, lead width or None)."""
            pitch = math.hypot(P["x"] - N["x"], P["y"] - N["y"]) or 1e-6
            fpp = [q for q in G["pads"] if q["ref"] == P["ref"]]
            cxf, cyf = sum(q["x"] for q in fpp) / len(fpp), sum(q["y"] for q in fpp) / len(fpp)
            mx, my = (P["x"] + N["x"]) / 2 - cxf, (P["y"] + N["y"]) / 2 - cyf
            same_y = sum(1 for q in fpp if abs(q["y"] - P["y"]) < 0.05)
            same_x = sum(1 for q in fpp if abs(q["x"] - P["x"]) < 0.05)
            if same_y >= 3 and same_y >= same_x:      # pads form a row along x: leave along y
                ox, oy = 0.0, (1.0 if my >= 0 else -1.0)
            elif same_x >= 3:                          # row along y: leave along x
                ox, oy = (1.0 if mx >= 0 else -1.0), 0.0
            elif abs(mx) >= abs(my):
                ox, oy = (1.0 if mx >= 0 else -1.0), 0.0
            else:
                ox, oy = 0.0, (1.0 if my >= 0 else -1.0)
            rx, ry = -oy, ox                      # row direction (lateral)
            # pads of this footprint in the same row as the pair (same outward depth within 0.3 mm)
            depthP = (P["x"] - cxf) * ox + (P["y"] - cyf) * oy
            depthN = (N["x"] - cxf) * ox + (N["y"] - cyf) * oy
            top = max(depthP, depthN)
            ext = max(pad_extent(P, ox, oy), pad_extent(N, ox, oy)) / 2
            # fan-out rank among the pair jobs leaving this row
            lat_pair = ((P["x"] + N["x"]) / 2 - cxf) * rx + ((P["y"] + N["y"]) / 2 - cyf) * ry
            row_pairs = []
            for j2 in JOBS:
                if j2.get("kind") != "pair":
                    continue
                for end in ("from", "to"):
                    q1, q2 = pad_of.get(tuple(j2[end][0])), pad_of.get(tuple(j2[end][1]))
                    if not q1 or not q2 or q1["ref"] != P["ref"]:
                        continue
                    d1 = (q1["x"] - cxf) * ox + (q1["y"] - cyf) * oy
                    if abs(d1 - top) <= max(0.3, abs(depthP - depthN) + 0.05):
                        row_pairs.append(((q1["x"] + q2["x"]) / 2 - cxf) * rx + ((q1["y"] + q2["y"]) / 2 - cyf) * ry)
            row_pairs = sorted(set(round(v, 3) for v in row_pairs))
            K = len(row_pairs)
            rank = row_pairs.index(round(lat_pair, 3)) if round(lat_pair, 3) in row_pairs else (K - 1) / 2
            shift = (rank - (K - 1) / 2) * FAN if K > 1 else 0.0
            pitch_lat = abs((P["x"] - N["x"]) * rx + (P["y"] - N["y"]) * ry)
            lead_w = w if pitch_lat >= (w + s) else STUB_W
            if pitch_lat < 0.4 + lead_w - 0.001 and lead_w == w:
                lead_w = STUB_W
            lat = (w + s) / 2 - pitch_lat / 2      # >0 splay, <0 converge (lateral distance along the row)
            if pitch_lat >= 0.7:                   # coarse rows (THT connectors) need no fan-out
                shift = 0.0
            sP = -1.0 if ((P["x"] - N["x"]) * rx + (P["y"] - N["y"]) * ry) < 0 else 1.0   # P side along r
            # exact DRC clearance (no raster safety margin); the straight escape is checked with the pads of
            # the footprint itself ignored (parallel, centred leads between same-row pads are legal by
            # construction when the pitch allows the lead width), the splay is checked against everything
            fp_mask = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
            for q in fpp:
                for e in q["poly"]:
                    if len(e[0]) >= 3:
                        im_ = Image.new("1", (NX, NY), 0)
                        ImageDraw.Draw(im_).polygon(ring_xy(e[0]), fill=1)
                        fp_mask |= torch.from_numpy(np.array(im_, dtype=np.uint8)).to(DEV).bool()
            blk_straight = blocked(L, {nidP, nidN}, did, lead_w / 2, safe=0.0, ignore=fp_mask)
            blk_all = blocked(L, {nidP, nidN}, did, lead_w / 2, safe=0.0)

            def seg_clear(x1, y1, x2, y2, blk, skip_r):
                n = max(2, int(math.hypot(x2 - x1, y2 - y1) / RES))
                for i in range(n + 1):
                    t = i / n
                    X, Y = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
                    if math.hypot(X - x1, Y - y1) <= skip_r:
                        continue
                    cx_, cy_ = px(X, Y)
                    iy_, ix_ = int(cy_), int(cx_)
                    if 0 <= iy_ < NY and 0 <= ix_ < NX and bool(blk[iy_, ix_]):
                        return (X, Y)
                return None

            reason = None
            for out_len in (STUB_OUT, 0.6, 0.35):
                run = SPLAY + (abs(shift) * 0.8)
                pe = (P["x"] + ox * (top - depthP + ext + out_len), P["y"] + oy * (top - depthP + ext + out_len))
                ne = (N["x"] + ox * (top - depthN + ext + out_len), N["y"] + oy * (top - depthN + ext + out_len))
                ps_ = (pe[0] + ox * run + rx * (sP * lat + shift), pe[1] + oy * run + ry * (sP * lat + shift))
                ns_ = (ne[0] + ox * run + rx * (-sP * lat + shift), ne[1] + oy * run + ry * (-sP * lat + shift))
                leadP, leadN = [(P["x"], P["y"]), pe, ps_], [(N["x"], N["y"]), ne, ns_]
                bad = None
                for lead in (leadP, leadN):
                    bad = seg_clear(*lead[0], *lead[1], blk_straight, ext) or seg_clear(*lead[1], *lead[2], blk_all, 0.0)
                    if bad:
                        break
                if not bad:
                    centre = ((ps_[0] + ns_[0]) / 2, (ps_[1] + ns_[1]) / 2)
                    return centre, leadP, leadN, lead_w, (ox, oy), sP
                reason = bad
            if DEBUG_DIR and reason:
                cx_, cy_ = px(*reason)
                iy_, ix_ = int(cy_), int(cx_)
                inv = {v: k for k, v in NID.items()}
                win = lab[L][max(iy_ - 4, 0):iy_ + 5, max(ix_ - 4, 0):ix_ + 5]
                near = {inv.get(int(v), int(v)) for v in torch.unique(win).tolist() if int(v) > 0}
                print(f"debug lead rejected {P['ref']}.{P['num']}/{N['num']} on {L} at ({reason[0]:.2f},{reason[1]:.2f}) "
                      f"lead_w {lead_w} shift {shift:.2f}: nearby {near or 'keepout/edge/pour'}", flush=True)
            return ((P["x"] + N["x"]) / 2, (P["y"] + N["y"]) / 2), [(P["x"], P["y"])], [(N["x"], N["y"])], None, (ox, oy), sP

        jkey = json.dumps(job, sort_keys=True)
        if jkey in LEADS:
            endA, endB = LEADS[jkey]
        else:
            endA = prepare_end(AP, AN, LA)
            endB = prepare_end(BP, BN, LB)
            LEADS[jkey] = (endA, endB)
            if PREPARE_ONLY:
                LEAD_CELLS[jkey] = []
                for L, pts, nid_, sw in ((LA, endA[1], nidP, endA[3]), (LA, endA[2], nidN, endA[3]),
                                         (LB, endB[1], nidP, endB[3]), (LB, endB[2], nidN, endB[3])):
                    if sw:
                        before_ = lab[L].clone()
                        paint(L, pts, sw, nid_)
                        LEAD_CELLS[jkey].append((L, (lab[L] != before_)))
                continue
        a_c, leadAP, leadAN, stubA, outA, sPA = endA
        b_c, leadBP, leadBN, stubB, outB, sPB = endB
        corridor = 2 * w + s
        from_key = (tuple(job["from"][0]), tuple(job["from"][1]))
        if from_key in PASS_THROUGH:
            single_fallback_pt = True
        else:
            single_fallback_pt = False
        PASS_THROUGH.add((tuple(job["to"][0]), tuple(job["to"][1])))
        # handedness: P's side along the row at A must be the mirror of its side at B (the pair travels
        # out of A and into B); otherwise the two tracks would have to cross

        def single_fallback(why):
            """Route P then N as plain tracks (coupling lost on this hop); the result is flagged. Both nets'
            escape stubs are reserved before either is routed; everything is reverted on failure.
            With SINGLE_FALLBACK off the hop is simply left to the autorouter (its net stays unrouted)."""
            out_t, out_v, painted = [], [], []
            if not SINGLE_FALLBACK:
                for L, m_ in LEAD_CELLS.get(jkey, []):
                    lab[L][m_] = 0
                failures.append({"job": job, "why": why + " (left to the autorouter)"})
                print(f"pair {netP}/{netN}: left to the autorouter ({why})", flush=True)
                return False
            for L, m_ in LEAD_CELLS.get(jkey, []):   # the reserved pair leads of this job are released first
                lab[L][m_] = 0
            esc = {}
            for net_, nid_, A_, B_ in ((netP, nidP, AP, BP), (netN, nidN, AN, BN)):
                esc[net_] = (single_escape(nid_, did, A_), single_escape(nid_, did, B_))
                for e_, Pd in ((esc[net_][0], A_), (esc[net_][1], B_)):
                    if e_:
                        Lp = next(L for L in Pd["layers"] if L in labels)
                        painted.append(paint(Lp, [(Pd["x"], Pd["y"]), e_[0]], STUB_W, nid_))
            for net_, nid_, A_, B_ in ((netP, nidP, AP, BP), (netN, nidN, AN, BN)):
                r_ = route_single(net_, nid_, did, A_, B_, w, escapes=esc[net_])
                if r_ is None:
                    failures.append({"job": job, "why": why + "; single-ended fallback failed for " + net_})
                    for L, m_ in painted:
                        lab[L][m_] = 0
                    return False
                tr, vi = r_
                for t_ in tr:
                    t_["uncoupled"] = why
                    painted.append(paint(t_["layer"], t_["points"], t_["width"], nid_))
                for v_ in vi:
                    for L in labels:
                        painted.append(paint(L, [(v_["x"], v_["y"]), (v_["x"], v_["y"])], v_["d"], nid_))
                    draw_circle(hd, v_["x"], v_["y"], v_["drill"] / 2, 1)
                out_t += tr
                out_v += vi
            results.extend(out_t + out_v)
            print(f"pair {netP}/{netN}: single-ended fallback ({why}), {len(out_t)} tracks {len(out_v)} vias", flush=True)
            return True

        swap_tracks, swap_vias, swap_stubs = [], [], []
        leadsA_ok, leadsB_ok = bool(stubA), bool(stubB)
        if single_fallback_pt:
            single_fallback("pass-through pads: branch from the existing copper")
            continue
        if stubA and stubB and sPA != -sPB:
            # inline via swap on the A runway: both tracks change layer through two vias placed one behind
            # the other on the centreline, which exchanges their sides (P leaves on the other lane)
            L2 = "B.Cu" if LA == "F.Cu" else "F.Cu"
            ox_, oy_ = outA
            rx_, ry_ = -oy_, ox_                      # left normal of the travel direction
            off_ = (w + s) / 2
            D1, WIDE = 0.9, 0.65
            D2, DEND = D1 + VIA_PAIR_SPACING, D1 + VIA_PAIR_SPACING + 1.0
            v1 = (a_c[0] + ox_ * D1, a_c[1] + oy_ * D1)
            v2 = (a_c[0] + ox_ * D2, a_c[1] + oy_ * D2)
            via_ok_sw = via_pair_ok(LA, L2, {nidP, nidN}, did, R=VIA_D / 2)
            ok = True
            for vx_, vy_ in (v1, v2):
                cx_, cy_ = px(vx_, vy_)
                iy_, ix_ = int(cy_), int(cx_)
                if not (0 <= iy_ < NY and 0 <= ix_ < NX and bool(via_ok_sw[iy_, ix_])):
                    ok = False
            # the swap region must be clear on both layers for a WIDE + track corridor
            for L_ in (LA, L2):
                blk_ = blocked(L_, {nidP, nidN}, did, WIDE + w / 2, safe=0.0, cross_gnd=True)
                for i in range(0, int(DEND / RES) + 1):
                    X, Y = a_c[0] + ox_ * i * RES, a_c[1] + oy_ * i * RES
                    cx_, cy_ = px(X, Y)
                    iy_, ix_ = int(cy_), int(cx_)
                    if 0 <= iy_ < NY and 0 <= ix_ < NX and bool(blk_[iy_, ix_]):
                        ok = False
                        break
            if not ok:
                single_fallback("handedness mismatch, no room for an inline via swap")
                continue
            sideP = sPA           # P's lane side along r at the lead ends (+1 = +r)
            pA = (a_c[0] + rx_ * sideP * off_, a_c[1] + ry_ * sideP * off_)          # P lead end
            nA = (a_c[0] - rx_ * sideP * off_, a_c[1] - ry_ * sideP * off_)          # N lead end

            def pt(d, lat):
                return (a_c[0] + ox_ * d + rx_ * lat, a_c[1] + oy_ * d + ry_ * lat)

            # layer LA: P -> near via straight in; N detours around the near via to the far via
            P_LA = [pA, pt(D1 - 0.4, sideP * off_), v1]
            N_LA = [nA, pt(0.4, -sideP * WIDE), pt(D2 - 0.5, -sideP * WIDE), v2]
            # layer L2: P detours around the far via onto the opposite lane; N goes straight to its lane
            P_L2 = [v1, pt(D1 + 0.3, -sideP * WIDE), pt(D2 + 0.5, -sideP * WIDE), pt(DEND, -sideP * off_)]
            N_L2 = [v2, pt(D2 + 0.4, sideP * off_), pt(DEND, sideP * off_)]
            for L_, pts_, net_, nid_ in ((LA, P_LA, netP, nidP), (LA, N_LA, netN, nidN), (L2, P_L2, netP, nidP), (L2, N_L2, netN, nidN)):
                swap_tracks.append({"kind": "swap", "net": net_, "layer": L_, "width": w, "points": pts_})
            swap_vias = [{"kind": "via", "net": netP, "x": v1[0], "y": v1[1], "d": VIA_D, "drill": VIA_DRILL},
                         {"kind": "via", "net": netN, "x": v2[0], "y": v2[1], "d": VIA_D, "drill": VIA_DRILL}]
            # the corridor now starts on L2 at DEND with P on the opposite lane (lead points first: pt()
            # refers to the lead-end centre a_c, which is moved afterwards)
            swap_stubs = [(LA, leadAP, netP, nidP, stubA), (LA, leadAN, netN, nidN, stubA)]
            newP, newN, new_c = [pt(DEND, -sideP * off_)], [pt(DEND, sideP * off_)], pt(DEND, 0.0)
            LA = L2
            a_c = new_c
            leadAP, leadAN = newP, newN
            stubA = 0.0           # the original leads are emitted via swap_stubs; no lead emission from leadAP
            sPA = -sPA
            print(f"pair {netP}/{netN}: inline via swap at A ({LA})", flush=True)

        def runway(L, c, o, nets):
            """Longest straight full-width run out of the lead ends that is clear on layer L."""
            blk = blocked(L, nets, did, corridor / 2, safe=0.0, cross_gnd=True)
            for run in (RUNWAY, 0.6, 0.3):
                ok = True
                n = max(2, int(run / RES) + 1)
                for i in range(n + 1):
                    X, Y = c[0] + o[0] * run * i / n, c[1] + o[1] * run * i / n
                    cx_, cy_ = px(X, Y)
                    iy_, ix_ = int(cy_), int(cx_)
                    if 0 <= iy_ < NY and 0 <= ix_ < NX and bool(blk[iy_, ix_]) and i > 0:
                        ok = False
                        break
                if ok:
                    return run
            return 0.0

        runA = runway(LA, a_c, outA, {nidP, nidN}) if leadsA_ok else 0.0
        runB = runway(LB, b_c, outB, {nidP, nidN}) if leadsB_ok else 0.0
        # an end whose leads cannot be followed by even a 0.3 mm straight run is treated as lead-less:
        # the corridor stops short there and the autorouter finishes from the dangling ends
        if leadsA_ok and runA == 0.0:
            leadsA_ok, stubA = False, None
            a_c = ((AP["x"] + AN["x"]) / 2, (AP["y"] + AN["y"]) / 2)
        if leadsB_ok and runB == 0.0:
            leadsB_ok, stubB = False, None
            b_c = ((BP["x"] + BN["x"]) / 2, (BP["y"] + BN["y"]) / 2)
        a_run = (a_c[0] + outA[0] * runA, a_c[1] + outA[1] * runA)
        b_run = (b_c[0] + outB[0] * runB, b_c[1] + outB[1] * runB)
        path3 = None
        for cg in (False, True):
            freeA = ~blocked(LA, {nidP, nidN}, did, corridor / 2, cross_gnd=cg)
            freeB = freeA if LB == LA else ~blocked(LB, {nidP, nidN}, did, corridor / 2, cross_gnd=cg)
            src_m = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
            dst_m = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
            for m_, c in ((src_m, a_run), (dst_m, b_run)):
                cx, cy = px(*c)
                r = int(math.ceil((corridor / 2 + 0.3) / RES))
                m_[max(0, int(cy) - r):min(NY, int(cy) + r + 1), max(0, int(cx) - r):min(NX, int(cx) + r + 1)] = True
            freeA = freeA | src_m
            if LB == LA:
                freeA = freeA | dst_m
            else:
                freeB = freeB | dst_m
            src = [tuple(int(v) for v in c) for c in torch.nonzero(src_m).tolist()]
            if LA == LB:
                path = bfs_win(freeA, src, dst_m)
                path3 = [(LA, iy, ix) for iy, ix in path] if path else None
            else:
                via_ok = via_pair_ok(LA, LB, {nidP, nidN}, did)
                path3 = bfs2_win(freeA, freeB, via_ok, src, dst_m)
                if path3 is not None:
                    path3 = [(LA if L == "A" else LB, iy, ix) for L, iy, ix in path3]
            if path3 is not None:
                break
        if path3 is None:
            if DEBUG_DIR:
                import os
                for tag, fr, cpt, m_ in (("A", freeA, a_run, src_m), ("B", freeB, b_run, dst_m)):
                    cx, cy = px(*cpt)
                    x0c, x1c, y0c, y1c = int(cx) - 60, int(cx) + 60, int(cy) - 60, int(cy) + 60
                    crop = fr[max(y0c, 0):y1c, max(x0c, 0):x1c].cpu().numpy().astype(np.uint8) * 200
                    img = np.stack([crop, crop, crop], axis=-1)
                    cm = m_[max(y0c, 0):y1c, max(x0c, 0):x1c].cpu().numpy()
                    img[cm] = (255, 0, 0) if tag == "A" else (0, 0, 255)
                    Image.fromarray(img).save(os.path.join(DEBUG_DIR, f"pairfail_{job['nets'][0].split('/')[-1]}_{job['from'][0][0]}_{tag}.png"))
                print(f"debug pair: leads A {stubA} B {stubB}, runs {runA}/{runB}, layers {LA}->{LB}", flush=True)
            single_fallback("no corridor")
            continue
        # per-layer legs; a layer change is a via pair placed on the straight-through direction of the arrival
        legs = []
        for L, iy, ix in path3:
            if not legs or legs[-1][0] != L:
                legs.append([L, []])
            legs[-1][1].append((iy, ix))
        off = (w + s) / 2
        VOFF = VIA_PAIR_SPACING / 2

        def offset(line, sign, d):
            return offset_poly(line, sign * d)

        def dedup(pts):
            out = []
            for q in pts:
                if not out or math.hypot(q[0] - out[-1][0], q[1] - out[-1][1]) > 1e-6:
                    out.append(q)
            return out

        centres = []
        for li, (L, cells) in enumerate(legs):
            pts = [to_mm(ix, iy) for iy, ix in (simplify(cells) if len(cells) >= 3 else cells)]
            if li == 0:
                pts = [a_c, a_run] + pts if runA > 0 else [a_c] + pts
            if li == len(legs) - 1:
                pts = pts + ([b_run, b_c] if runB > 0 else [b_c])
            pts = dedup(smooth_path(dedup(pts)))
            if len(pts) < 2:
                pts = pts + [(pts[-1][0] + 0.01, pts[-1][1])]
            centres.append(pts)
        # P side: along the normal of the first direction (the A runway when present)
        plus0 = offset(centres[0], 1, off)
        signP = 1 if math.hypot(plus0[0][0] - leadAP[-1][0], plus0[0][1] - leadAP[-1][1]) <= \
            math.hypot(plus0[0][0] - leadAN[-1][0], plus0[0][1] - leadAN[-1][1]) else -1
        # straight-through via transitions: leg i ends at v, leg i+1 starts v -> v + d0*RUNV
        for li in range(len(centres) - 1):
            pts0, pts1 = centres[li], centres[li + 1]
            v = pts0[-1]
            d0 = (v[0] - pts0[-2][0], v[1] - pts0[-2][1])
            Lx = math.hypot(*d0) or 1.0
            d0 = (d0[0] / Lx, d0[1] / Lx)
            centres[li + 1] = dedup([v, (v[0] + d0[0] * RUNV, v[1] + d0[1] * RUNV)] + pts1[1:])
        vias_out = []
        trackP, trackN = [], []
        for li, pts in enumerate(centres):
            L = legs[li][0]
            P = offset(pts, signP, off)
            N = offset(pts, -signP, off)
            if li > 0:  # starts at the via pair of the previous leg
                pv, nv = vias_out[-2], vias_out[-1]
                P = [(pv["x"], pv["y"])] + P[1:]
                N = [(nv["x"], nv["y"])] + N[1:]
            if li < len(centres) - 1:  # ends at a via pair, normal to the arrival direction
                vx, vy = pts[-1]
                dx, dy = vx - pts[-2][0], vy - pts[-2][1]
                Lx = math.hypot(dx, dy) or 1.0
                nx_, ny_ = -dy / Lx, dx / Lx
                pv = (vx + signP * VOFF * nx_, vy + signP * VOFF * ny_)
                nv = (vx - signP * VOFF * nx_, vy - signP * VOFF * ny_)
                P = P[:-1] + [pv]
                N = N[:-1] + [nv]
                vias_out.append({"kind": "via", "net": netP, "x": pv[0], "y": pv[1], "d": VIA_D, "drill": VIA_DRILL})
                vias_out.append({"kind": "via", "net": netN, "x": nv[0], "y": nv[1], "d": VIA_D, "drill": VIA_DRILL})
            # lead-less ends (no legal lead could be built): the corridor stops short of the pads and the
            # autorouter finishes the last stretch from the dangling ends; with leads the tracks join them
            if li == 0 and leadsA_ok:
                P = [leadAP[-1]] + P
                N = [leadAN[-1]] + N
            if li == len(centres) - 1 and leadsB_ok:
                P = P + [leadBP[-1]]
                N = N + [leadBN[-1]]
            trackP.append((L, dedup(P)))
            trackN.append((L, dedup(N)))
        def seg_int(a, b, c, d):
            def orient(p_, q_, r_):
                return (q_[0] - p_[0]) * (r_[1] - p_[1]) - (q_[1] - p_[1]) * (r_[0] - p_[0])
            o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
            return (o1 * o2 < 0) and (o3 * o4 < 0)

        def seg_dist(a, b, c, d):
            def pd(pt_, u, v):
                ux, uy = v[0] - u[0], v[1] - u[1]
                L2 = ux * ux + uy * uy
                t = 0 if L2 == 0 else max(0.0, min(1.0, ((pt_[0] - u[0]) * ux + (pt_[1] - u[1]) * uy) / L2))
                return math.hypot(pt_[0] - (u[0] + ux * t), pt_[1] - (u[1] + uy * t))
            return min(pd(a, c, d), pd(b, c, d), pd(c, a, b), pd(d, a, b))

        bad_geom = None
        per_layer = {}
        for L, pts in trackP:
            per_layer.setdefault(L, [[], []])[0].append(pts)
        for L, pts in trackN:
            per_layer.setdefault(L, [[], []])[1].append(pts)
        for L, (Ps, Ns) in per_layer.items():
            for pp in Ps:
                for nn in Ns:
                    for a, b in zip(pp, pp[1:]):
                        for c, d in zip(nn, nn[1:]):
                            if seg_int(a, b, c, d):
                                bad_geom = f"P/N cross on {L} near ({a[0]:.2f},{a[1]:.2f})"
                            elif seg_dist(a, b, c, d) < w + s - 0.02:
                                bad_geom = f"P/N gap {seg_dist(a, b, c, d) - w:.3f} on {L} near ({a[0]:.2f},{a[1]:.2f})"
                            if bad_geom:
                                break
                        if bad_geom:
                            break
                    if bad_geom:
                        break
                if bad_geom:
                    break
            if bad_geom:
                break
        if bad_geom:
            for L, m_ in LEAD_CELLS.get(jkey, []):
                lab[L][m_] = 0
            single_fallback("corridor geometry rejected: " + bad_geom)
            continue
        stubs = list(swap_stubs)
        if stubA:
            stubs += [(LA, leadAP, netP, nidP, stubA), (LA, leadAN, netN, nidN, stubA)]
        if stubB:
            stubs += [(LB, leadBP, netP, nidP, stubB), (LB, leadBN, netN, nidN, stubB)]
        for L, pts, net_, nid_, sw in stubs:
            results.append({"kind": "stub", "net": net_, "layer": L, "width": sw, "points": pts})
            paint(L, pts, sw, nid_)
        for t_ in swap_tracks:
            results.append(t_)
            paint(t_["layer"], t_["points"], t_["width"], NID[t_["net"]])
        for v_ in swap_vias:
            results.append(v_)
            for L in labels:
                paint(L, [(v_["x"], v_["y"]), (v_["x"], v_["y"])], v_["d"], NID[v_["net"]])
            draw_circle(hd, v_["x"], v_["y"], v_["drill"] / 2, 1)
        for L, pts in trackP:
            results.append({"kind": "pair", "net": netP, "layer": L, "width": w, "points": pts})
            paint(L, pts, w, nidP)
        for L, pts in trackN:
            results.append({"kind": "pair", "net": netN, "layer": L, "width": w, "points": pts})
            paint(L, pts, w, nidN)
        for v in vias_out:
            results.append(v)
            for L in labels:
                paint(L, [(v["x"], v["y"]), (v["x"], v["y"])], v["d"], NID[v["net"]])
            draw_circle(hd, v["x"], v["y"], v["drill"] / 2, 1)
        print(f"pair {netP}/{netN} {LA}->{LB} w{w} s{s}: {sum(len(c) for c in centres)} points, "
              f"{len(path3) * RES:.1f} mm, vias {len(vias_out)}, runs {runA}/{runB}", flush=True)
json.dump({"tracks": results, "failures": failures} | ({"power_strict": {"entry_mm": ENTRY_MM, "i_via": I_VIA, "counts": STRICT_COUNT}} if POWER_STRICT else {}), open(OUT, "w", encoding="utf-8"), indent=1)
ckpt_write(results, failures, len(JOBS))
print("done:", len(results), "tracks,", len(failures), "failures")
if POWER_STRICT:
    print("power-strict counts (this run; a resumed run counts only the jobs after the checkpoint):", json.dumps(STRICT_COUNT))
