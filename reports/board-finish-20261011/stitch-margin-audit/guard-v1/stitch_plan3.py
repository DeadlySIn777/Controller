# Raster plane-stitching planner v3 (system Python: numpy, PIL, torch on GPU) = stitch_plan2.py plus the PCBWay
# via-in-pad rule: a new via is NEVER placed within GAP (default 0.10 mm, plus --mask-exp allowance for local mask
# expansion overrides, geom.json carries none) of any SMD/CONN pad aperture on either outer layer; the via sits at
# the end of a short lead (the stub from the pad centre). Everything else is identical to stitch_plan2.py:
# For every SMD pad of a plane net that is not yet in its plane's main cluster, place the nearest legal
# stub + through via that lands inside the net's own inner-layer copper. Legal = clear of every other net's
# copper on all six layers (0.15 mm inside a galvanic domain, 0.6 mm across domains or to net-less copper)
# with the via radius added, outside via keepouts, not inside any pad, >= 0.5 mm from the board edge; the stub
# (pad centre -> via, on the pad's layer) clear by the same rules. Placed copper becomes an obstacle for later
# nets; same-net vias keep >= 0.25 mm hole-to-hole. Output: plan JSON for stitch_apply.py.
#   python stitch_plan3.py geom.json plan.json [--via 0.6:0.3] [--stub 0.25] [--maxr 3.5] [--gap 0.10] [--mask-exp 0.05]
#        [--pad-mask pad-mask.json]      # per-pad expansions above --mask-exp (tools/fix/pad_mask_dump.py)
#        [--dru board.kicad_dru]         # default: board.kicad_dru next to geom.json, when present
#        [--stub-angle 35]               # min angle (deg) between a new stub and an existing same-pad track
#        [--allow-classless]             # accept a geom.json without DOM_* net classes (refused by default)
# .kicad_dru "disallow" rules on named rule areas (A.intersectsArea('NAME') ... (constraint disallow track via ...),
# with A.NetName != '...' exemptions; e.g. the TMR4WI converter keepouts, whose rule areas carry no keepout flags of
# their own) block vias (and stubs, when 'track' is disallowed) of every net that is not exempt (exact net spelling).
# CPU: the thread pools are capped at 4 (OMP/MKL/OPENBLAS env + torch.set_num_threads) - run it through heavy.sh gpu.
import os

for _k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_k, "4")
import json
import math
import re
import sys
from collections import defaultdict

import numpy as np
import torch
from PIL import Image, ImageDraw

torch.set_num_threads(int(os.environ.get("OMP_NUM_THREADS", "4")))

G = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]


def arg(name, default, conv=float):
    return conv(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


VD, VDR = (float(x) for x in arg("--via", "0.6:0.3", str).split(":"))
STUB = arg("--stub", 0.25)
MAXR = arg("--maxr", 3.5)
GAP = arg("--gap", 0.10)        # via annulus to SMD/CONN pad aperture (PCBWay mask web / via-in-pad rule)
MASKEXP = arg("--mask-exp", 0.05)  # allowance for per-pad solder-mask expansion overrides (not in geom.json)
PADMASK = arg("--pad-mask", "", str)  # optional {"REF.NUM": expansion_mm} for pads whose expansion exceeds --mask-exp
_dru_default = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), "board.kicad_dru")
DRU = arg("--dru", _dru_default if os.path.exists(_dru_default) else "", str)
RES = 0.05
CLR, XDOM, EDGE, HOLE2HOLE = 0.15, 0.6, 0.5, 0.25
SAFE = 0.06  # raster discretisation margin added to every clearance (0.05 mm grid)
LAYERS = ["F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"]
INNER = LAYERS[1:5]
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")

x0, y0, x1, y1 = G["bbox"]
NX, NY = int(math.ceil((x1 - x0) / RES)) + 1, int(math.ceil((y1 - y0) / RES)) + 1


def px(x, y):
    return ((x - x0) / RES, (y - y0) / RES)


net_dom = {}
for p in G["pads"]:
    if p["net"]:
        net_dom.setdefault(p["net"], p["cls"].split(",")[0])
# Guard (11 Oct 2026): geom_dump.py records the classes pcbnew loaded from <board basename>.kicad_pro. A board copy
# named e.g. source.kicad_pcb next to board.kicad_pro loads CLASS-LESS (every net "Default"): every net would share
# one domain and cross-domain vias/stubs would get 0.15 mm instead of 0.6 mm (agent-work/verify-stitch3 measured 47
# such stitches). Refuse such a geom.json unless --allow-classless is given.
_n_dom = sum(1 for d in net_dom.values() if d.startswith("DOM_") or d == "NC_ISOLATE")
print(f"nets with a DOM_*/NC_ISOLATE class in geom.json: {_n_dom} of {len(net_dom)}", flush=True)
if _n_dom == 0 and "--allow-classless" not in sys.argv:
    print("stitch_plan3: geom.json carries no DOM_* net classes (board dumped without its <basename>.kicad_pro?); "
          "galvanic clearances unknown - refusing to plan (--allow-classless overrides)", file=sys.stderr, flush=True)
    sys.exit(2)
nets = sorted({p["net"] for p in G["pads"] if p["net"]} | {t["net"] for t in G["tracks"]} |
              {v["net"] for v in G["vias"]} | {z["net"] for z in G["zones"]})
NID = {n: i + 2 for i, n in enumerate(n for n in nets if n)}  # 0 empty, 1 net-less copper
DOMS = sorted(set(net_dom.values()) | {"DOM_LOGIC"})
DID = {d: i + 1 for i, d in enumerate(DOMS)}
dom_of_id = np.zeros(len(NID) + 2, dtype=np.int16)
dom_of_id[1] = 0  # net-less: its own "domain" 0, always the cross-domain distance
for n, i in NID.items():
    dom_of_id[i] = DID[net_dom.get(n, "DOM_LOGIC")]


def new_label():
    return Image.new("I", (NX, NY), 0)


labels = {L: new_label() for L in LAYERS}
draws = {L: ImageDraw.Draw(labels[L]) for L in LAYERS}


def ring_xy(ring):
    return [px(x, y) for x, y in ring]


def draw_poly(L, entry, val):
    ring, holes = entry
    if len(ring) >= 3:
        draws[L].polygon(ring_xy(ring), fill=val)


def draw_circle(L, x, y, r, val):
    cx, cy = px(x, y)
    rr = r / RES
    draws[L].ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=val)


def draw_track(L, a, b, w, val):
    (ax, ay), (bx, by) = px(*a), px(*b)
    draws[L].line([ax, ay, bx, by], fill=val, width=max(1, int(round(w / RES))))
    draw_circle(L, a[0], a[1], w / 2, val)
    draw_circle(L, b[0], b[1], w / 2, val)


# Zone fills go into a separate raster: they only decide where a via lands in its own plane. Other nets'
# pours are not obstacles (they refill around a new via with the zone clearance), so they are not drawn
# into the copper label raster.
fills_img = {L: new_label() for L in LAYERS}
fills_draw = {L: ImageDraw.Draw(fills_img[L]) for L in LAYERS}
for z in G["zones"]:
    val = NID.get(z["net"], 1)
    for L, fills in z["fills"].items():
        for e in fills:
            ring, holes = e
            if len(ring) >= 3:
                fills_draw[L].polygon(ring_xy(ring), fill=val)
            for h in holes:
                if len(h) >= 3:
                    fills_draw[L].polygon(ring_xy(h), fill=0)
for t in G["tracks"]:
    draw_track(t["layer"], t["a"], t["b"], t["w"], NID.get(t["net"], 1))
for sh in G.get("shapes", []):
    for e in sh["poly"]:
        draw_poly(sh["layer"], e, NID.get(sh["net"], 1) if sh["net"] else 1)
# Every existing drill hole (vias, PTH, NPTH) keeps the hole-to-hole distance to a new via hole.
holes_img = Image.new("F", (NX, NY), 0.0)
hd = ImageDraw.Draw(holes_img)
hole_list = [(v["x"], v["y"], v["drill"]) for v in G["vias"]] +             [(p["x"], p["y"], p["drill"]) for p in G["pads"] if p["drill"] > 0]
for v in G["vias"]:
    for L in LAYERS:
        draw_circle(L, v["x"], v["y"], v["d"] / 2, NID.get(v["net"], 1))
pad_mask = Image.new("1", (NX, NY), 0)
pmd = ImageDraw.Draw(pad_mask)
smd_mask = Image.new("1", (NX, NY), 0)  # SMD/CONN pad copper on either outer layer (aperture ~ copper + mask expansion)
smd_draw = ImageDraw.Draw(smd_mask)
# Pads whose resolved mask expansion exceeds the flat --mask-exp allowance (fiducials +0.5 mm, local overrides) come
# from --pad-mask (tools/fix/pad_mask_dump.py: {"REF.NUM": expansion_mm}); they get their own, wider guard ring.
PAD_MASK = json.load(open(PADMASK, encoding="utf-8")) if PADMASK else {}
smd_wide = defaultdict(lambda: Image.new("1", (NX, NY), 0))  # expansion (mm, rounded) -> pad copper mask
smd_wide_n = defaultdict(int)
for p in G["pads"]:
    val = NID.get(p["net"], 1) if p["net"] else 1
    for L in p["layers"]:
        for e in p["poly"]:
            draw_poly(L, e, val)
    is_outer_smd = p["smd"] and any(L in ("F.Cu", "B.Cu") for L in p["layers"])
    exp = PAD_MASK.get(f"{p['ref']}.{p['num']}", 0.0) if is_outer_smd else 0.0
    for e in p["poly"]:
        if len(e[0]) >= 3:
            pmd.polygon(ring_xy(e[0]), fill=1)
            if is_outer_smd:
                smd_draw.polygon(ring_xy(e[0]), fill=1)
                if exp > MASKEXP:
                    key = round(exp, 3)
                    ImageDraw.Draw(smd_wide[key]).polygon(ring_xy(e[0]), fill=1)
                    smd_wide_n[key] += 1
    if p["drill"] > 0 and not p["smd"]:
        for L in LAYERS:
            if L not in p["layers"]:
                draw_circle(L, p["x"], p["y"], p["drill"] / 2, val)
lab = {L: torch.from_numpy(np.array(labels[L], dtype=np.int32)).to(DEV) for L in LAYERS}
hole_bad = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
for hx, hy, hdr in hole_list:
    r = (hdr / 2 + HOLE2HOLE + VDR / 2 + SAFE) / RES
    cx, cy = (hx - x0) / RES, (hy - y0) / RES
    ya, yb = max(0, int(cy - r) - 1), min(NY, int(cy + r) + 2)
    xa, xb = max(0, int(cx - r) - 1), min(NX, int(cx + r) + 2)
    if ya >= yb or xa >= xb:
        continue
    gy, gx = torch.meshgrid(torch.arange(ya, yb, device=DEV), torch.arange(xa, xb, device=DEV), indexing="ij")
    hole_bad[ya:yb, xa:xb] |= ((gx - cx) ** 2 + (gy - cy) ** 2) <= r * r
fill = {L: torch.from_numpy(np.array(fills_img[L], dtype=np.int32)).to(DEV) for L in INNER}
padm = torch.from_numpy(np.array(pad_mask, dtype=np.uint8)).to(DEV).bool()
smdm = torch.from_numpy(np.array(smd_mask, dtype=np.uint8)).to(DEV).bool()
dom_t = torch.from_numpy(dom_of_id).to(DEV)
print("rasters", NX, "x", NY, "on", DEV, flush=True)

# Keepouts and board edge.
novia = Image.new("1", (NX, NY), 0)
nvd = ImageDraw.Draw(novia)
for k in G["keepouts"]:
    if k["no_vias"]:
        for e in k["outline"]:
            if len(e[0]) >= 3:
                nvd.polygon(ring_xy(e[0]), fill=1)
novia_t = torch.from_numpy(np.array(novia, dtype=np.uint8)).to(DEV).bool()
e = int(round(EDGE / RES))
edge_t = torch.ones((NY, NX), dtype=torch.bool, device=DEV)
edge_t[e:NY - e, e:NX - e] = False
notrk = {}
for L in ("F.Cu", "B.Cu"):
    im = Image.new("1", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    for k in G["keepouts"]:
        if k["no_tracks"] and L in k["layers"]:
            for e2 in k["outline"]:
                if len(e2[0]) >= 3:
                    d.polygon(ring_xy(e2[0]), fill=1)
    notrk[L] = torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()


# .kicad_dru disallow rules on named rule areas: [(area name, disallow set, exempt net names)]
def parse_dru_disallow(path):
    out = []
    if not path:
        return out
    txt = open(path, encoding="utf-8", errors="replace").read()
    starts = [m.start() for m in re.finditer(r"\(rule\s+\"", txt)] + [len(txt)]
    for a, c in zip(starts, starts[1:]):
        block = txt[a:c]
        dm = re.search(r"\(constraint\s+disallow([^)]*)\)", block)
        cm = re.search(r"\(condition\s+\"(.*?)\"\)", block, re.S)
        if not dm or not cm:
            continue
        areas = re.findall(r"intersectsArea\('([^']+)'\)", cm.group(1))
        if len(areas) != 1 or "||" in cm.group(1):
            if areas:
                print(f"DRU rule with {len(areas)} areas / '||' not modelled, areas blocked for every net: {areas}",
                      flush=True)
            for ar in areas:
                out.append((ar, set(dm.group(1).split()), set()))
            continue
        out.append((areas[0], set(dm.group(1).split()), set(re.findall(r"A\.NetName != '([^']*)'", cm.group(1)))))
    return out


DRU_AREAS = parse_dru_disallow(DRU)
dru_masks = []  # (disallow set, exempt nets, layers, raster of the area outline)
for name, dis, exempt in DRU_AREAS:
    ks = [k for k in G["keepouts"] if k["name"] == name]
    if not ks:
        print(f"DRU area {name}: no rule area of that name in geom.json", flush=True)
        continue
    im = Image.new("1", (NX, NY), 0)
    d = ImageDraw.Draw(im)
    lays = set()
    for k in ks:
        lays |= set(k["layers"])
        for e2 in k["outline"]:
            if len(e2[0]) >= 3:
                d.polygon(ring_xy(e2[0]), fill=1)
    dru_masks.append((dis, exempt, lays, torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool(), name))
print(f"DRU disallow areas: {[(n, sorted(dis)) for dis, ex, ly, m, n in dru_masks]}", flush=True)


def dilate(mask, r_mm):
    r = int(math.ceil(r_mm / RES))
    yy, xx = torch.meshgrid(torch.arange(-r, r + 1, device=DEV), torch.arange(-r, r + 1, device=DEV), indexing="ij")
    k = ((xx * xx + yy * yy) <= (r_mm / RES) ** 2).half()[None, None]
    out = torch.nn.functional.conv2d(mask.half()[None, None], k, padding=r)[0, 0]
    return out > 0.5


def forbidden(layer, net_id, dom_id, extra_r):
    L = lab[layer]
    other = (L > 0) & (L != net_id)
    same_dom = other & (dom_t[L.long()] == dom_id)
    cross = other & ~same_dom
    return dilate(same_dom, CLR + SAFE + extra_r) | dilate(cross, XDOM + SAFE + extra_r)


# v3: the via centre must stay >= via radius + GAP + mask-expansion allowance from every SMD/CONN pad's copper
targets = defaultdict(list)
for p in G["pads"]:
    if p["plane_net"] and not p["on_plane"] and p["smd"] and len(p["layers"]) == 1 and p["layers"][0] in ("F.Cu", "B.Cu"):
        targets[p["net"]].append(p)
# v3.1 (11 Oct 2026) copper-sliver / acid-trap guard: KiCad's copper_sliver test flags the narrow V between two
# same-net tracks that leave one pad at a small angle (via-dogbone proof r3: 3 B.Cu slivers between the stubs of
# C11069.2 / C11066.2 and an existing lead / stub of the same pad). A stub whose direction from the pad centre is
# closer than --stub-angle (default 35 deg) to an existing same-net track leaving the same pad (one endpoint inside
# the pad copper on the pad's layer, the other outside) is rejected; the next candidate cell is tried.
STUB_ANG = math.radians(arg("--stub-angle", 35.0))


def _pip(x, y, ring):
    c = False
    n = len(ring)
    for i in range(n):
        xa, ya = ring[i]
        xb, yb = ring[(i + 1) % n]
        if (ya > y) != (yb > y) and x < (xb - xa) * (y - ya) / (yb - ya) + xa:
            c = not c
    return c


_tracks_nl = defaultdict(list)
for _t in G["tracks"]:
    _tracks_nl[(_t["net"], _t["layer"])].append(_t)
pad_dirs = {}
for _net, _pads in targets.items():
    for _p in _pads:
        _L = _p["layers"][0]
        _rings = [e[0] for e in _p["poly"] if len(e[0]) >= 3]
        if not _rings:
            continue
        _xs = [q[0] for r in _rings for q in r]
        _ys = [q[1] for r in _rings for q in r]
        _bb = (min(_xs), min(_ys), max(_xs), max(_ys))
        _dirs = []
        for _t in _tracks_nl.get((_net, _L), ()):
            for _a, _b in ((_t["a"], _t["b"]), (_t["b"], _t["a"])):
                if _bb[0] <= _a[0] <= _bb[2] and _bb[1] <= _a[1] <= _bb[3] and any(_pip(_a[0], _a[1], r) for r in _rings):
                    if not any(_pip(_b[0], _b[1], r) for r in _rings):
                        _dirs.append(math.atan2(_b[1] - _p["y"], _b[0] - _p["x"]))
                    break
        if _dirs:
            pad_dirs[(_p["ref"], _p["num"])] = _dirs
print(f"stub-angle guard: {math.degrees(STUB_ANG):.0f} deg to {sum(len(v) for v in pad_dirs.values())} existing same-pad "
      f"tracks of {len(pad_dirs)} target pads", flush=True)
n_angle_rej = 0
plan, failed = [], []
rv = VD / 2
smd_bad = dilate(smdm, rv + GAP + MASKEXP + SAFE)
print(f"via-in-pad guard: via centre >= {rv + GAP + MASKEXP + SAFE:.3f} mm from SMD/CONN pad copper", flush=True)
for exp_key, im in smd_wide.items():
    wide = torch.from_numpy(np.array(im, dtype=np.uint8)).to(DEV).bool()
    smd_bad |= dilate(wide, rv + GAP + exp_key + SAFE)
    print(f"via-in-pad guard: {smd_wide_n[exp_key]} pads with mask expansion {exp_key} mm -> centre >= "
          f"{rv + GAP + exp_key + SAFE:.3f} mm", flush=True)
for net in sorted(targets, key=lambda n: -len(targets[n])):
    nid, did = NID[net], DID[net_dom.get(net, "DOM_LOGIC")]
    land = torch.zeros((NY, NX), dtype=torch.bool, device=DEV)
    for Lp in INNER:
        own = fill[Lp] == nid
        land |= ~dilate(~own, rv * 0.5) & own  # comfortably inside own copper
    via_bad = novia_t | edge_t | padm | hole_bad | smd_bad
    for Lx in LAYERS:
        via_bad |= forbidden(Lx, nid, did, rv)
    stub_bad = {Lx: forbidden(Lx, nid, did, STUB / 2) | notrk[Lx] for Lx in ("F.Cu", "B.Cu")}
    for dis, exempt, lays, amask, aname in dru_masks:
        if net in exempt:
            continue
        if "via" in dis:
            via_bad |= dilate(amask, rv + SAFE)
        if "track" in dis:
            for Lx in ("F.Cu", "B.Cu"):
                if Lx in lays:
                    stub_bad[Lx] |= dilate(amask, STUB / 2 + SAFE)
    valid = land & ~via_bad
    placed = []
    for p in targets[net]:
        L = p["layers"][0]
        cx, cy = px(p["x"], p["y"])
        R = int(MAXR / RES)
        ia, ib = max(0, int(cy) - R), min(NY, int(cy) + R + 1)
        ja, jb = max(0, int(cx) - R), min(NX, int(cx) + R + 1)
        win = valid[ia:ib, ja:jb]
        ys, xs = torch.nonzero(win, as_tuple=True)
        if len(ys) == 0:
            failed.append({"pad": f"{p['ref']}.{p['num']}", "net": net, "why": "no legal via cell within reach"})
            continue
        dy = (ys + ia).float() - cy
        dx = (xs + ja).float() - cx
        dist = torch.sqrt(dx * dx + dy * dy)
        order = torch.argsort(dist)
        chosen = None
        sb = stub_bad[L]
        dirs = pad_dirs.get((p["ref"], p["num"]), ())
        for k in order[:400].tolist():
            vy, vx = int(ys[k]) + ia, int(xs[k]) + ja
            if dirs:  # pixel axes have the orientation of the mm axes
                ang = math.atan2(vy - cy, vx - cx)
                if any(abs((ang - d + math.pi) % (2 * math.pi) - math.pi) < STUB_ANG for d in dirs):
                    n_angle_rej += 1
                    continue
            n = int(dist[k].item()) + 2
            t = torch.linspace(0, 1, n * 2, device=DEV)
            sy = (cy + (vy - cy) * t).round().long().clamp(0, NY - 1)
            sx = (cx + (vx - cx) * t).round().long().clamp(0, NX - 1)
            if bool(sb[sy, sx].any()):
                continue
            chosen = (vx, vy, float(dist[k]) * RES)
            break
        if not chosen:
            failed.append({"pad": f"{p['ref']}.{p['num']}", "net": net, "why": "no via with a clear stub"})
            continue
        vx, vy, dmm = chosen
        X, Y = x0 + vx * RES, y0 + vy * RES
        plan.append({"ref": p["ref"], "pad": p["num"], "net": net, "layer": L, "via": [round(X, 3), round(Y, 3)],
                     "pad_xy": [p["x"], p["y"]],
                     "d": VD, "drill": VDR, "stub_w": STUB, "dist": round(dmm, 3)})
        # Same-net spacing: block hole-to-hole < 0.25 mm around this via for later vias of this net.
        r_block = (VDR + HOLE2HOLE) / RES
        yy0, yy1 = max(0, int(vy - r_block) - 1), min(NY, int(vy + r_block) + 2)
        xx0, xx1 = max(0, int(vx - r_block) - 1), min(NX, int(vx + r_block) + 2)
        gy, gx = torch.meshgrid(torch.arange(yy0, yy1, device=DEV), torch.arange(xx0, xx1, device=DEV), indexing="ij")
        valid[yy0:yy1, xx0:xx1] &= ((gx - vx) ** 2 + (gy - vy) ** 2) > r_block ** 2
        placed.append((X, Y, L, p))
    # Placed copper becomes an obstacle (labelled with this net) for the nets processed afterwards.
    for X, Y, L, p in placed:
        cxp, cyp = px(X, Y)
        r = rv / RES
        yy0, yy1 = max(0, int(cyp - r) - 1), min(NY, int(cyp + r) + 2)
        xx0, xx1 = max(0, int(cxp - r) - 1), min(NX, int(cxp + r) + 2)
        gy, gx = torch.meshgrid(torch.arange(yy0, yy1, device=DEV), torch.arange(xx0, xx1, device=DEV), indexing="ij")
        disk = ((gx - cxp) ** 2 + (gy - cyp) ** 2) <= r * r
        for Lx in LAYERS:
            sub = lab[Lx][yy0:yy1, xx0:xx1]
            sub[disk & (sub == 0)] = nid
        # stub on its layer
        sx0, sy0 = px(p["x"], p["y"])
        n = int(math.hypot(cxp - sx0, cyp - sy0)) + 2
        t = torch.linspace(0, 1, n * 2, device=DEV)
        sy = (sy0 + (cyp - sy0) * t).round().long().clamp(0, NY - 1)
        sx = (sx0 + (cxp - sx0) * t).round().long().clamp(0, NX - 1)
        w = int(math.ceil(STUB / 2 / RES))
        for oy in range(-w, w + 1):
            for ox in range(-w, w + 1):
                yy = (sy + oy).clamp(0, NY - 1)
                xx = (sx + ox).clamp(0, NX - 1)
                cur = lab[L][yy, xx]
                lab[L][yy, xx] = torch.where(cur == 0, torch.full_like(cur, nid), cur)
    print(f"{net}: targets {len(targets[net])}, placed {len(placed)}", flush=True)
from stitch_exact_guard import validate_plan
plan = validate_plan(sys.argv[1], plan, OUT, PADMASK)
json.dump({"plan": plan, "failed": failed, "targets": sum(len(v) for v in targets.values()),
           "via": [VD, VDR], "stub": STUB, "gap": GAP, "mask_exp": MASKEXP, "pad_mask": PADMASK,
           "pad_mask_wide": {str(k): v for k, v in smd_wide_n.items()}, "planner": "stitch_plan3",
           "dru": DRU, "dru_areas": [n for dis, ex, ly, m, n in dru_masks],
           "stub_angle_deg": round(math.degrees(STUB_ANG), 1), "stub_angle_rejections": n_angle_rej,
           "stub_angle_pads": len(pad_dirs)},
          open(OUT, "w", encoding="utf-8"), indent=1)
print("TOTAL targets", sum(len(v) for v in targets.values()), "planned", len(plan), "failed", len(failed))
print(json.dumps({"tool": "stitch_plan3", "geom": sys.argv[1], "plan": OUT, "targets": sum(len(v) for v in targets.values()),
                  "planned": len(plan), "failed": len(failed), "gap_mm": GAP, "mask_exp_mm": MASKEXP,
                  "dru_areas_applied": len(dru_masks), "stub_angle_deg": round(math.degrees(STUB_ANG), 1),
                  "stub_angle_rejections": n_angle_rej}))
