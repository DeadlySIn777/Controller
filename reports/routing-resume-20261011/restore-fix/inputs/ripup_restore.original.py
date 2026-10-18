# Restore step of the rip-up loop (KiCad 10 python, pcbnew API): after the re-route pass (c), every ripped net
# that did NOT get all of its island joins back gets its ripped copper back, provided that copper is clear of
# everything the re-route pass added for other nets. The rip then costs nothing where it did not pay: a net whose
# old route can return keeps its old connectivity, and only the space that a freed job really used stays taken.
#   python.exe ripup_restore.py board.kicad_pcb rip-rR.json jobs-rR-c.json routes-rR-c.json out.kicad_pcb report.json
#        [--same-mm 0.20] [--cross-mm 0.65]
# board      the board after pass (c) was applied (the ripped board + routes-rR-c.json)
# rip        ripup_fence.py report of the round (removed items with geometry, ripped_nets)
# jobs/routes  pass (c) jobs and router output: a ripped net is a restore candidate when one of its jobs failed
# Conflict rule (pure geometry, mm): every removed item of the net is checked against every track/stub/via the
# router added in pass (c) for ANOTHER net (the only copper that did not coexist with it before the rip):
# copper-to-copper gap >= --same-mm (default 0.20 = board clearance 0.15 + margin) between nets of the same net
# class, >= --cross-mm (0.65 = galvanic 0.6 + margin) between different classes (DOM_* galvanic domains). A net
# is restored all-or-nothing: same geometry, net, width, layer, via size/drill and locked flag as recorded (KiCad
# gives the re-created items new uuids; the report maps old -> new). Copper the net got back in pass (c) stays
# (same-net overlap is legal). Zones are refilled by the DRC that follows; pads and rule areas did not change.
# Vias of the SAME net (fix of 11 Oct 2026: the round-2 DENSE proof restored 14 vias exactly on top of the vias
# pass (c) had placed for the same net = holes_co_located, and one 0.51 mm from one = hole_to_hole): a removed
# via whose centre coincides (<= 0.01 mm) with a same-net via of pass (c) is NOT re-created (that via already
# joins the same layers; the report lists it as "duplicate_skipped"); a removed via whose hole edge would come
# closer than --hole-mm (default 0.25 = min_hole_to_hole of board.kicad_pro) to a same-net pass-(c) via hole is
# a conflict (the net is not restored).
# The board is written with SaveBoard(..., aSkipSettings=True): the project file is never written.
# Prints one JSON summary line; the report lists every candidate net with its decision, the restored items and,
# for a refused net, the first conflict (other net, layer, mm position, gap).
import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict

import pcbnew

GRID = 2.0


def pt_seg(p, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / l2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def seg_seg(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if ((o1 > 0) != (o2 > 0)) and ((o3 > 0) != (o4 > 0)) and o1 != 0 and o2 != 0 and o3 != 0 and o4 != 0:
        return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))


def cells(x0, y0, x1, y1, r):
    for gx in range(int(math.floor((min(x0, x1) - r) / GRID)), int(math.floor((max(x0, x1) + r) / GRID)) + 1):
        for gy in range(int(math.floor((min(y0, y1) - r) / GRID)), int(math.floor((max(y0, y1) + r) / GRID)) + 1):
            yield (gx, gy)


def main(argv):
    ap = argparse.ArgumentParser(description="give ripped nets their copper back where pass (c) did not reconnect them")
    ap.add_argument("board")
    ap.add_argument("rip")
    ap.add_argument("jobs")
    ap.add_argument("routes")
    ap.add_argument("out")
    ap.add_argument("report")
    ap.add_argument("--same-mm", type=float, default=0.20)
    ap.add_argument("--cross-mm", type=float, default=0.65)
    ap.add_argument("--hole-mm", type=float, default=0.25, help="min hole-to-hole edge gap to a same-net pass-(c) via")
    a = ap.parse_args(argv)
    t0 = time.time()
    rip = json.load(open(a.rip, encoding="utf-8"))
    jobs = json.load(open(a.jobs, encoding="utf-8"))
    routes = json.load(open(a.routes, encoding="utf-8"))
    ripped = set(rip.get("ripped_nets", []))
    failed_nets = defaultdict(int)
    for f in routes.get("failures", []):
        n = f["job"].get("net")
        if n in ripped:
            failed_nets[n] += 1
    removed_by_net = defaultdict(list)
    for r in rip.get("removed", []):
        removed_by_net[r["net"]].append(r)

    b = pcbnew.LoadBoard(a.board)
    F = pcbnew.FromMM
    cls_of = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            n = str(p.GetNetname())
            if n and n not in cls_of:
                cls_of[n] = str(p.GetNetClassName()).split(",")[0]

    def cls(n):
        if n not in cls_of:
            net = b.FindNet(n)
            cls_of[n] = str(net.GetNetClassName()).split(",")[0] if net else ""
        return cls_of[n]

    # index of the copper pass (c) added: ("seg", layer, a, b, half width, net) / ("via", None, c, c, radius, net)
    grid = defaultdict(list)
    new_items = []
    for r in routes.get("tracks", []):
        if r.get("kind") == "via":
            it = ("via", None, (r["x"], r["y"]), (r["x"], r["y"]), r["d"] / 2, r["net"], r.get("drill", 0.3) / 2)
            new_items.append(it)
            for c in cells(r["x"], r["y"], r["x"], r["y"], it[4]):
                grid[c].append(len(new_items) - 1)
            continue
        pts = r.get("points", [])
        for p, q in zip(pts, pts[1:]):
            it = ("seg", r["layer"], tuple(p), tuple(q), r["width"] / 2, r["net"], 0.0)
            new_items.append(it)
            for c in cells(p[0], p[1], q[0], q[1], it[4]):
                grid[c].append(len(new_items) - 1)
    reach = max([it[4] for it in new_items] + [0.0]) + max(a.same_mm, a.cross_mm) + 1.0

    dup_vias = set()          # uuids of removed vias that coincide with a same-net pass-(c) via (not re-created)

    def conflict(rec):
        """first conflict of a removed item with pass-(c) copper of another net (or, for a via, with the hole of a
        same-net pass-(c) via), or None"""
        net = rec["net"]
        if rec["item"] == "via":
            pa = pb = (rec["x"], rec["y"])
            hw, lay = rec["d"] / 2, None
        else:
            pa, pb = tuple(rec["start"]), tuple(rec["end"])
            hw, lay = rec["width"] / 2, rec["layer"]
        seen = set()
        for c in cells(pa[0], pa[1], pb[0], pb[1], hw + reach):
            for k in grid.get(c, ()):
                if k in seen:
                    continue
                seen.add(k)
                kind, L, qa, qb, qh, qn, qdr = new_items[k]
                if qn == net:
                    if rec["item"] == "via" and kind == "via":
                        dc = math.hypot(pa[0] - qa[0], pa[1] - qa[1])
                        if dc <= 0.01:
                            dup_vias.add(rec["uuid"])
                            continue
                        gap_h = dc - rec.get("drill", 0.3) / 2 - qdr
                        if gap_h < a.hole_mm:
                            return {"other_net": qn, "layer": "via (same net, hole to hole)", "at": [round(qa[0], 3), round(qa[1], 3)],
                                    "gap_mm": round(gap_h, 3), "required_mm": a.hole_mm}
                    continue
                if lay is not None and L is not None and L != lay:
                    continue          # two tracks on different layers never touch; a via is on every layer
                req = a.same_mm if cls(qn) == cls(net) else a.cross_mm
                gap = seg_seg(pa, pb, qa, qb) - hw - qh
                if gap < req:
                    return {"other_net": qn, "layer": L or lay or "via", "at": [round(qa[0], 3), round(qa[1], 3)],
                            "gap_mm": round(gap, 3), "required_mm": req}
        return None

    decisions = []
    restored_items = 0
    restored_nets = 0
    dup_skipped = 0
    for net in sorted(failed_nets):
        recs = removed_by_net.get(net, [])
        if not recs:
            continue
        first = None
        for rec in recs:
            first = conflict(rec)
            if first:
                break
        if first:
            decisions.append({"net": net, "failed_jobs": failed_nets[net], "removed_items": len(recs), "restored": False,
                              "conflict": first, "blocking_item": {k: rec.get(k) for k in ("item", "layer", "start", "end", "x", "y")}})
            continue
        nb = b.FindNet(net)
        if nb is None:
            decisions.append({"net": net, "restored": False, "conflict": "net not on board"})
            continue
        made = []
        skipped_dup = []
        for rec in recs:
            if rec["item"] == "via" and rec["uuid"] in dup_vias:
                skipped_dup.append({"old": rec["uuid"], "at": [rec["x"], rec["y"]]})
                continue
            if rec["item"] == "via":
                v = pcbnew.PCB_VIA(b)
                v.SetPosition(pcbnew.VECTOR2I(F(rec["x"]), F(rec["y"])))
                v.SetViaType(pcbnew.VIATYPE_THROUGH)
                v.SetWidth(F(rec["d"]))
                v.SetDrill(F(rec["drill"]))
                v.SetNet(nb)
                v.SetLocked(bool(rec.get("locked")))
                b.Add(v)
                made.append({"old": rec["uuid"], "new": v.m_Uuid.AsString()})
            else:
                t = pcbnew.PCB_TRACK(b)
                t.SetStart(pcbnew.VECTOR2I(F(rec["start"][0]), F(rec["start"][1])))
                t.SetEnd(pcbnew.VECTOR2I(F(rec["end"][0]), F(rec["end"][1])))
                t.SetWidth(F(rec["width"]))
                t.SetLayer(b.GetLayerID(rec["layer"]))
                t.SetNet(nb)
                t.SetLocked(bool(rec.get("locked")))
                b.Add(t)
                made.append({"old": rec["uuid"], "new": t.m_Uuid.AsString()})
        restored_items += len(made)
        restored_nets += 1
        dup_skipped += len(skipped_dup)
        decisions.append({"net": net, "failed_jobs": failed_nets[net], "removed_items": len(recs), "restored": True, "uuid_map": made,
                          "duplicate_skipped": skipped_dup})
    pcbnew.SaveBoard(a.out, b, True)
    summary = {"tool": "ripup_restore", "ripped_nets": len(ripped), "candidates": len(failed_nets),
               "restored_nets": restored_nets, "restored_items": restored_items, "duplicate_vias_skipped": dup_skipped,
               "refused_conflict": sum(1 for d in decisions if not d["restored"]), "seconds": round(time.time() - t0)}
    json.dump({"board_in": os.path.abspath(a.board), "board_out": os.path.abspath(a.out), "rip": os.path.abspath(a.rip),
               "routes": os.path.abspath(a.routes), "same_mm": a.same_mm, "cross_mm": a.cross_mm, "summary": summary,
               "decisions": decisions}, open(a.report, "w", encoding="utf-8"), indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main(sys.argv[1:])
