# ISOLATED CANDIDATE: 11 Oct 2026. Not adopted by the shared queue, and not native-tested.
# Restore step of the rip-up loop (KiCad 10 python, pcbnew API): after the re-route pass (c), every net with
# recorded removed copper gets its copper back, provided that copper is clear of
# everything the re-route pass added for other nets. The rip then costs nothing where it did not pay: a net whose
# old route can return keeps its old connectivity, and only the space that a freed job really used stays taken.
#   python.exe ripup_restore.py board.kicad_pcb rip-rR.json jobs-rR-c.json routes-rR-c.json out.kicad_pcb report.json
#        [--same-mm 0.20] [--cross-mm 0.65]
# board      the board after pass (c) was applied (the ripped board + routes-rR-c.json)
# rip        ripup_fence.py report of the round (removed items with geometry, ripped_nets)
# jobs/routes  pass (c) jobs and router output: complete one-failure-or-indexed-route accounting is required.
# Candidates include ALL removed/ripped nets, even those without jobs or reported failures. Router output is
# accounting evidence, not proof of connectivity. If any candidate cannot be restored, the WHOLE restore
# step refuses before adding copper or SaveBoard, reports saved=false and exits nonzero. The caller must
# retain its input revision. A final native partition diff with lost=0 remains required after cleanup.
# Conflict rule (pure geometry, mm): every removed item of the net is checked against every track/stub/via the
# router added in pass (c) for ANOTHER net (the only copper that did not coexist with it before the rip):
# copper-to-copper gap >= --same-mm (default 0.20 = board clearance 0.15 + margin) between nets of the same net
# class, >= --cross-mm (0.65 = galvanic 0.6 + margin) between different classes (DOM_* galvanic domains). A net
# is restored all-or-nothing: same geometry, net, width, layer, via size/drill and locked flag as recorded (KiCad
# gives the re-created items new uuids; the report maps old -> new). Copper the net got back in pass (c) stays
# (same-net overlap is legal). Zones are refilled by the DRC that follows; pads and rule areas did not change.
# Vias of the SAME net (fix of 11 Oct 2026: the round-2 DENSE proof restored 14 vias exactly on top of the vias
# pass (c) had placed for the same net = holes_co_located, and one 0.51 mm from one = hole_to_hole): a removed
# via whose centre coincides (<= 0.01 mm) is skipped ONLY when position, diameter and drill match in native
# units and a matching through via is present on the loaded board ("duplicate_skipped"). A non-equivalent
# near-colocated via refuses the restore; a removed via whose hole edge would come
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

GRID = 2.0


class InputError(ValueError):
    """Untrustworthy rip/job/route inputs must never reach SaveBoard."""


def job_key(job):
    if not isinstance(job, dict) or job.get("kind") != "power":
        raise InputError("restore accounting supports only the signal producer's power jobs")
    if not isinstance(job.get("net"), str) or not job["net"]:
        raise InputError("job has no net")
    for end in ("from", "to"):
        value = job.get(end)
        if not isinstance(value, list) or len(value) != 2 or not all(isinstance(x, str) and x for x in value):
            raise InputError(f"job has invalid {end} pad identity")
    return job["net"], tuple(job["from"]), tuple(job["to"])


def finite(value, name, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{name} must be finite numeric data")
    if positive and value <= 0:
        raise InputError(f"{name} must be positive")
    return value


def point(value, name):
    if not isinstance(value, list) or len(value) != 2:
        raise InputError(f"{name} must be an xy point")
    for coord in value:
        finite(coord, name)


def validate_inputs(rip, jobs, routes):
    """Conservative coverage and accounting, not a claim that emitted routes join pads."""
    if not isinstance(rip, dict) or not isinstance(jobs, list) or not isinstance(routes, dict):
        raise InputError("rip/routes must be objects and jobs a list")
    for key in ("ripped_nets", "removed"):
        if not isinstance(rip.get(key), list):
            raise InputError(f"rip.{key} must be a list")
    for key in ("tracks", "failures"):
        if not isinstance(routes.get(key), list):
            raise InputError(f"routes.{key} must be a list")
    ripped = set()
    for net in rip["ripped_nets"]:
        if not isinstance(net, str) or not net or net in ripped:
            raise InputError("ripped net identities must be nonempty and unique")
        ripped.add(net)
    removed_by_net = defaultdict(list)
    uuids = set()
    for rec in rip["removed"]:
        if not isinstance(rec, dict) or not isinstance(rec.get("net"), str) or not rec["net"]:
            raise InputError("removed item has no net")
        if not isinstance(rec.get("uuid"), str) or not rec["uuid"] or rec["uuid"] in uuids:
            raise InputError("removed item uuids must be nonempty and unique")
        uuids.add(rec["uuid"])
        if rec.get("item") == "via":
            finite(rec.get("x"), "removed via x")
            finite(rec.get("y"), "removed via y")
            finite(rec.get("d"), "removed via diameter", True)
            finite(rec.get("drill"), "removed via drill", True)
            if rec["drill"] >= rec["d"]:
                raise InputError("removed via drill must be smaller than diameter")
        elif rec.get("item") == "track":
            point(rec.get("start"), "removed track start")
            point(rec.get("end"), "removed track end")
            finite(rec.get("width"), "removed track width", True)
            if not isinstance(rec.get("layer"), str) or not rec["layer"]:
                raise InputError("removed track has no layer")
        else:
            raise InputError("unsupported removed item")
        if "locked" in rec and not isinstance(rec["locked"], bool):
            raise InputError("removed locked flag must be boolean")
        removed_by_net[rec["net"]].append(rec)
    missing = ripped - removed_by_net.keys()
    if missing:
        raise InputError(f"ripped nets have no recorded removed geometry: {sorted(missing)}")
    candidates = ripped | removed_by_net.keys()

    keys = [job_key(job) for job in jobs]
    if len(set(keys)) != len(keys):
        raise InputError("duplicate job identity makes failure accounting ambiguous")
    index_for = {key: i + 1 for i, key in enumerate(keys)}
    failed_indices = set()
    failed_nets = defaultdict(int)
    for failure in routes["failures"]:
        if not isinstance(failure, dict) or not isinstance(failure.get("why"), str) or not failure["why"]:
            raise InputError("invalid failure record")
        key = job_key(failure.get("job"))
        index = index_for.get(key)
        if index is None or failure["job"] != jobs[index - 1]:
            raise InputError("failure does not match an input job")
        if index in failed_indices:
            raise InputError("duplicate failure for one job")
        failed_indices.add(index)
        failed_nets[key[0]] += 1
    successful_indices = set()
    auxiliary_indices = set()
    unindexed_nets = set()
    for rec in routes["tracks"]:
        if not isinstance(rec, dict) or not isinstance(rec.get("net"), str) or not rec["net"]:
            raise InputError("route copper has no net")
        if rec.get("kind") == "via":
            finite(rec.get("x"), "route via x")
            finite(rec.get("y"), "route via y")
            finite(rec.get("d"), "route via diameter", True)
            finite(rec.get("drill", 0.3), "route via drill", True)
            if rec.get("drill", 0.3) >= rec["d"]:
                raise InputError("route via drill must be smaller than diameter")
        else:
            finite(rec.get("width"), "route width", True)
            if not isinstance(rec.get("layer"), str) or not rec["layer"]:
                raise InputError("route track has no layer")
            if not isinstance(rec.get("points"), list) or len(rec["points"]) < 2:
                raise InputError("route track must have at least two points")
            for xy in rec["points"]:
                point(xy, "route track point")
        if "job_index" in rec:
            index = rec["job_index"]
            if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= len(jobs):
                raise InputError("route job_index outside the input jobs")
            if rec["net"] != jobs[index - 1]["net"]:
                raise InputError("route net does not match its indexed job")
            if rec.get("kind") == "power":
                if not any(math.hypot(xy[0] - rec["points"][0][0], xy[1] - rec["points"][0][1]) > 1e-6
                           for xy in rec["points"][1:]):
                    raise InputError("indexed job success requires a nonzero main power polyline")
                successful_indices.add(index)
            elif rec.get("kind") in ("via", "stub", "padstub", "neck"):
                auxiliary_indices.add(index)
            else:
                raise InputError("unsupported indexed route copper kind")
        else:
            if rec.get("kind") not in ("via", "stub", "padstub", "neck"):
                raise InputError("main route segment has no job_index")
            unindexed_nets.add(rec["net"])
    if failed_indices & successful_indices:
        raise InputError("job has both failure and route copper")
    if auxiliary_indices - successful_indices:
        raise InputError("indexed auxiliary copper has no successful main route for its job")
    unaccounted = set(range(1, len(jobs) + 1)) - failed_indices - successful_indices
    if unaccounted:
        raise InputError(f"router omitted outcomes for jobs {sorted(unaccounted)}")
    success_nets = {jobs[index - 1]["net"] for index in successful_indices}
    if unindexed_nets - success_nets:
        raise InputError("unindexed stub/via copper has no successful main route for its net")
    accounting = {"jobs": len(jobs), "failed_jobs": len(failed_indices),
                  "indexed_route_jobs": len(successful_indices), "complete": True,
                  "connectivity_proven": False}
    return candidates, removed_by_net, failed_nets, accounting


def write_report(path, report):
    temporary = path + ".part"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, allow_nan=False)
        handle.write("\n")
    os.replace(temporary, path)


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def aliases(first, second):
    first_path = os.path.normcase(os.path.realpath(os.path.abspath(first)))
    second_path = os.path.normcase(os.path.realpath(os.path.abspath(second)))
    if first_path == second_path:
        return True
    if os.path.exists(first) and os.path.exists(second):
        return os.path.samefile(first, second)
    return False


def validate_paths(args):
    """Report writes, including their temporary path, must not replace source inputs or board copper."""
    protected = (args.board, args.rip, args.jobs, args.routes, args.out)
    for destination in (args.report, args.report + ".part"):
        if any(aliases(destination, source) for source in protected):
            raise InputError("report/report.part path aliases board/output/input data")
    if aliases(args.report, args.report + ".part"):
        raise InputError("report and temporary report paths alias each other")
    if any(aliases(args.out, source) for source in (args.rip, args.jobs, args.routes)):
        raise InputError("output board path aliases JSON input data")


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


def main(argv, pcbnew_module=None):
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
    try:
        validate_paths(a)
    except InputError as error:
        raise SystemExit(f"unsafe destination paths: {error}")
    t0 = time.time()
    paths = {"board_in": os.path.abspath(a.board), "board_out": os.path.abspath(a.out),
             "rip": os.path.abspath(a.rip), "jobs": os.path.abspath(a.jobs), "routes": os.path.abspath(a.routes)}
    try:
        for name, value in (("same_mm", a.same_mm), ("cross_mm", a.cross_mm), ("hole_mm", a.hole_mm)):
            finite(value, name, True)
        rip = read_json(a.rip)
        jobs = read_json(a.jobs)
        routes = read_json(a.routes)
        candidates, removed_by_net, failed_nets, accounting = validate_inputs(rip, jobs, routes)
    except (InputError, ValueError, KeyError, TypeError, OSError) as error:
        summary = {"tool": "ripup_restore", "status": "rejected_input", "saved": False,
                   "strict": True, "seconds": round(time.time() - t0)}
        write_report(a.report, dict(paths, summary=summary, error=str(error)))
        print(json.dumps(summary))
        return 2
    if pcbnew_module is None:
        import pcbnew as pcbnew_module
    pcbnew = pcbnew_module

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

    # A JSON route is not proof that its via was applied. Exact duplicate suppression also requires a
    # physically present through via with the original recorded position, diameter and drill.
    actual_vias = set()
    for item in b.GetTracks():
        if item.GetClass() == "PCB_VIA" and item.GetViaType() == pcbnew.VIATYPE_THROUGH:
            position = item.GetPosition()
            actual_vias.add((str(item.GetNetname()), position.x, position.y, item.GetWidth(), item.GetDrillValue()))

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
                            original = (net, F(rec["x"]), F(rec["y"]), F(rec["d"]), F(rec["drill"]))
                            replacement = (net, F(qa[0]), F(qa[1]), F(qh * 2), F(qdr * 2))
                            if original != replacement or original not in actual_vias:
                                return {"other_net": qn, "layer": "via (same net, non-equivalent duplicate)",
                                        "at": [round(qa[0], 3), round(qa[1], 3)],
                                        "reason": "duplicate must match original native geometry and exist on loaded board"}
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
    # Preflight EVERY candidate before mutating the board. A conflict cannot silently leave old copper absent.
    for net in sorted(candidates):
        recs = removed_by_net.get(net, [])
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
        invalid_layers = sorted({rec["layer"] for rec in recs if rec["item"] == "track" and b.GetLayerID(rec["layer"]) < 0})
        if invalid_layers:
            decisions.append({"net": net, "restored": False, "conflict": f"unknown layers: {invalid_layers}"})
            continue
        decisions.append({"net": net, "failed_jobs": failed_nets[net], "removed_items": len(recs), "restored": True})
    refused = sum(not decision["restored"] for decision in decisions)
    if refused:
        for decision in decisions:
            decision["would_restore"] = decision.pop("restored")
            decision["restored"] = False
        summary = {"tool": "ripup_restore", "ripped_nets": len(rip["ripped_nets"]), "candidates": len(candidates),
                   "restored_nets": 0, "restored_items": 0, "duplicate_vias_skipped": 0,
                   "refused_conflict": refused, "status": "rejected_restore", "saved": False,
                   "strict": True, "seconds": round(time.time() - t0)}
        write_report(a.report, dict(paths, same_mm=a.same_mm, cross_mm=a.cross_mm, hole_mm=a.hole_mm,
                                   summary=summary, accounting=accounting, decisions=decisions))
        print(json.dumps(summary))
        return 3

    restored_items = 0
    restored_nets = 0
    dup_skipped = 0
    for decision in decisions:
        net = decision["net"]
        recs = removed_by_net[net]
        nb = b.FindNet(net)
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
        decision.update(uuid_map=made, duplicate_skipped=skipped_dup)
    saved = pcbnew.SaveBoard(a.out, b, True)
    if saved is False:
        raise RuntimeError("SaveBoard reported failure")
    summary = {"tool": "ripup_restore", "ripped_nets": len(rip["ripped_nets"]), "candidates": len(candidates),
               "restored_nets": restored_nets, "restored_items": restored_items, "duplicate_vias_skipped": dup_skipped,
               "refused_conflict": 0, "status": "restored_geometry", "saved": True, "strict": True,
               "connectivity_proven": False, "native_partition_diff_lost_zero_required": True,
               "seconds": round(time.time() - t0)}
    write_report(a.report, dict(paths, same_mm=a.same_mm, cross_mm=a.cross_mm, hole_mm=a.hole_mm,
                              summary=summary, accounting=accounting, decisions=decisions))
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
