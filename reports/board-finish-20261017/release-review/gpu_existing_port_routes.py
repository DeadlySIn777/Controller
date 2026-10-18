"""Bounded CUDA reachability for previously unexplored old In3 port pairs.

Actual R299 filled copper and actual J1-connected In4 reference are immutable
hard obstacles/support. GPU output is only a proposal to exact vector checks.
"""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "2"
from pathlib import Path
import collections
import hashlib
import json
import math
import pickle
import sys
import time
import uuid
import psutil
proc = psutil.Process(); proc.cpu_affinity(list(range(16, 28))); proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import numpy as np
import shapely
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
from shapely import STRtree
import torch
import torch.nn.functional as F
torch.set_num_threads(2)

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / "reports/board-finish-20261011/continuation-r2"
CACHE = ROOT / "reports/board-finish-20261017/actual-full-audit-repaired-r1/r763"
OUT = HERE / "gpu-existing-In3-ports-r1"
LY = "In3.Cu"
for directory in (OLD / "field-power", OLD / "sbc-power", OLD / "coupled-recovery"):
    sys.path.insert(0, str(directory))
import R157_native_selected_actual_conversion_r673 as N
K = N.K; L = N.L
norm = L.norm
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def put(name, data):
    (OUT / name).write_text(json.dumps(data, indent=1, allow_nan=False) + "\n")

def bounded(shape, radius):
    return shapely.set_precision(shape.buffer((radius + .000002) / math.cos(math.pi / 256), quad_segs=64), .000001)

def summary(shape):
    return {"empty": shape.is_empty, "area_mm2": shape.area,
            "bounds": None if shape.is_empty else list(shape.bounds), "WKB_SHA256": hashlib.sha256(shape.wkb).hexdigest()}

def segments(path):
    return LineString(path) if len(path) > 1 else Point(path[0])

def simplify(path, free):
    answer = [path[0]]; index = 0
    while index < len(path) - 1:
        best = index + 1
        # Testing all later vertices is bounded by the grid path length and
        # never assumes that polygon coverage is monotone in path index.
        for j in range(len(path) - 1, index + 1, -1):
            if free.covers(LineString([path[index], path[j]])):
                best = j; break
        answer.append(path[best]); index = best
    return answer

def cuda_route(free, start, finish, window, requested_step):
    x0, y0, x1, y1 = window.bounds
    step = max(requested_step, math.sqrt((x1 - x0) * (y1 - y0) / 1800000))
    nx = int(math.ceil((x1 - x0) / step)) + 1; ny = int(math.ceil((y1 - y0) / step)) + 1
    xs = x0 + np.arange(nx) * step; ys = y0 + np.arange(ny) * step
    # A retained grid center's entire square, including every diagonal edge,
    # lies inside the exact centerline-free polygon. This prevents corner cuts.
    raster_safe = free.buffer(-(step / math.sqrt(2) + .000005))
    if raster_safe.is_empty:
        return None, {"status": "NO_CONSERVATIVE_RASTER_CELLS", "step_mm": step}
    mask = shapely.contains_xy(raster_safe, xs[None, :], ys[:, None])
    def terminals(point):
        ix = int(round((point[0] - x0) / step)); iy = int(round((point[1] - y0) / step)); found = []
        for yy in range(max(0, iy - 8), min(ny, iy + 9)):
            for xx in range(max(0, ix - 8), min(nx, ix + 9)):
                if mask[yy, xx] and math.dist(point, (xs[xx], ys[yy])) <= .45 and free.covers(LineString([point, (xs[xx], ys[yy])])):
                    found.append((yy, xx))
        return found
    starts, goals = terminals(start), terminals(finish)
    info = {"step_mm": step, "grid_shape": [ny, nx], "safe_cells": int(mask.sum()), "start_cells": len(starts), "goal_cells": len(goals)}
    if not starts or not goals:
        return None, info | {"status": "NO_CONSERVATIVE_GRID_TERMINAL"}
    device = torch.device("cuda:0")
    allowed = torch.as_tensor(mask, device=device, dtype=torch.float16)[None, None, :, :]
    reach = torch.zeros_like(allowed)
    distance = torch.full((ny, nx), -1, device=device, dtype=torch.int16)
    sy, sx = zip(*starts); reach[0, 0, list(sy), list(sx)] = 1; distance[list(sy), list(sx)] = 0
    gy, gx = zip(*goals); goals_y = torch.tensor(gy, device=device); goals_x = torch.tensor(gx, device=device)
    t0 = time.monotonic(); status = "GRID_ITERATION_BOUND"; iterations = 0
    for iteration in range(1, min(2 * (nx + ny), 20000)):
        grown = F.max_pool2d(reach, 3, stride=1, padding=1) * allowed
        new = (grown[0, 0] > 0) & (distance < 0)
        distance[new] = iteration
        reach = grown; iterations = iteration
        if iteration % 16 == 0:
            if bool((distance[goals_y, goals_x] >= 0).any().item()):
                status = "CUDA_PATH_FOUND"; break
            if not bool(new.any().item()):
                status = "CUDA_BOUNDED_GRID_DISCONNECTED"; break
            if time.monotonic() - t0 > 30:
                status = "CUDA_WINDOW_TIME_BOUND"; break
    values = distance.cpu().numpy()
    info.update(status=status, iterations=iterations, GPU_seconds=time.monotonic() - t0)
    reached = [(int(values[y, x]), y, x) for y, x in goals if values[y, x] >= 0]
    if not reached:
        del reach, allowed, distance
        return None, info
    _, yy, xx = min(reached); chain = [(yy, xx)]
    while values[yy, xx] > 0:
        target = int(values[yy, xx]) - 1
        options = [(y, x) for y in range(max(0, yy - 1), min(ny, yy + 2))
                   for x in range(max(0, xx - 1), min(nx, xx + 2)) if int(values[y, x]) == target]
        assert options
        yy, xx = min(options, key=lambda p: math.dist((xs[p[1]], ys[p[0]]), start)); chain.append((yy, xx))
    chain.reverse()
    path = [tuple(start)] + [(float(xs[x]), float(ys[y])) for y, x in chain] + [tuple(finish)]
    assert free.covers(LineString(path)), "Raster proposal failed exact vector coverage; never accept it"
    del reach, allowed, distance
    return simplify(path, free), info

def main():
    assert torch.cuda.is_available(), "Use only the available local GPU"
    assert not OUT.exists(); OUT.mkdir()
    model_path = CACHE / "actual-combined-full-after-model.pkl"
    groups_path = CACHE / "actual-combined-full-after-all-net-groups.pkl"
    binding_path = CACHE / "actual-graph-cache-receipt.json"
    census_path = OLD / "actual-native-existing-In3-ports-across-current-logic-groups-r311/actual-unchanged-In3-port-pairs-not-routes.json"
    prior_path = OLD / "six-existing-old-port-In3-physical-batch-r313/receipt.json"
    expected_path = OLD / "combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json"
    paths = [model_path, groups_path, binding_path, census_path, prior_path, expected_path, Path(__file__)]
    pins = {str(p): sha(p) for p in paths}
    binding = json.loads(binding_path.read_text())
    assert pins[str(model_path)] == binding["after_actual_model_SHA256"] == "c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806"
    assert pins[str(groups_path)] == binding["after_actual_groups_SHA256"] == "c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd"
    assert binding["native_candidate_SHA256"] == "7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2"
    put("launch.json", {"input_sha256": pins, "CPU_affinity": proc.cpu_affinity(), "torch": torch.__version__, "GPU": torch.cuda.get_device_name(0), "candidate": binding["native_candidate_SHA256"], "new_vias": 0, "PCB_edits": 0})
    print("LOAD_ACTUAL_R299_MODEL_AND_GROUPS", flush=True)
    h = pickle.loads(model_path.read_bytes()); groups = pickle.loads(groups_path.read_bytes())
    lg = groups["/LOGIC_GND"]
    roots = [q for q in lg if any(r["kind"] == "pad" and r.get("ref") == "J11001" and str(r.get("pin")) == "2" for r in q)]
    assert len(roots) == 1
    ground = roots[0]
    ref_shapes = [r["shape"] for r in ground if r["kind"] == "fill" and r["layer"] == "In4.Cu"]
    ref_tree = STRtree(ref_shapes)
    ground_via_ids = {r["uuid"] for r in ground if r["kind"] == "via" and r["layer"] == "In3.Cu"}
    # Current native group membership, not the historical census group indices.
    membership = {}
    for net, gg in groups.items():
        for index, group in enumerate(gg):
            for r in group:
                if r["kind"] == "via" and r["layer"] == LY:
                    membership[norm(net), r["uuid"]] = index
    del groups, lg
    expected = json.loads(expected_path.read_text())
    vias = {v["uuid"]: v for v in h["vias"]}
    records = []
    def add(uid, raw, kind, shape, local=0., extra=0.):
        if not shape.is_empty:
            records.append({"uuid": uid, "net": norm(raw), "raw_net": raw, "kind": kind, "shape": shape, "local": local, "extra": extra})
    for p in h["pads"]:
        for shape in L.poly(p["layers"].get(LY, [])):
            add(p["uuid"], p["net"], "actual_native_pad", shape, extra=.005)
    for t in h["tracks"]:
        if t["layer"] == LY:
            assert "m" not in t, "Do not approximate an unhandled arc"
            add(t["uuid"], t["net"], "actual_native_segment", bounded(LineString([t["a"], t["b"]]), t["w"] / 2))
    holes = []
    for v in h["vias"]:
        center = Point(v["x"], v["y"])
        if LY in v["flashed"]: add(v["uuid"], v["net"], "actual_native_flashed_via", bounded(center, v["d"] / 2))
        holes.append((v["uuid"], bounded(center, v["drill"] / 2)))
    for p in h["pads"]:
        for shape in L.poly(p.get("hole") or []): holes.append((p["uuid"], shape))
    for z in h["zones"]:
        for shape in L.poly(z["fills"].get(LY, [])):
            add(z["uuid"], z["net"], "actual_R299_filled_Cu_hard", shape, float(z.get("clearance_mm", .15)))
    for s in h["shapes"]:
        if s["layer"] == LY:
            for shape in L.poly(s["poly"]): add(s["uuid"], s["net"], "retained_Cu_graphic", shape)
    tree = STRtree([r["shape"] for r in records]); hole_tree = STRtree([s for _, s in holes])
    board_axis = unary_union(L.poly(h["outline"])).buffer(-.625)
    reserve, exemptions = K.A.reservations()
    rules = []
    for rows, isreserve in ((h["rule_areas"], False), (reserve["keepouts"], True)):
        for r in rows:
            if LY in r["layers"] and (isreserve or r.get("no_tracks")):
                for shape in L.poly(r["outline"]): rules.append((r, isreserve, shape))
    pairs = json.loads(census_path.read_text()); prior = json.loads(prior_path.read_text())
    prior_exact = {frozenset((r["pair"]["left_port"]["UUID"], r["pair"]["right_port"]["UUID"])) for r in prior["pairs"]}
    pairs = [p for p in pairs if frozenset((p["left_port"]["UUID"], p["right_port"]["UUID"])) not in prior_exact]
    print("CUDA_READY", len(pairs), "pairs", len(records), "actual_In3_obstacles", flush=True)
    results = []; accepted = []; start_time = time.monotonic()
    for index, pair in enumerate(pairs):
        net = pair["normalized_net"]
        ids = {pair["left_port"]["UUID"], pair["right_port"]["UUID"]}
        if any((net, uid) not in membership for uid in ids):
            results.append({"pair": pair, "status": "CURRENT_PORT_NOT_IN_ACTUAL_IN3_GROUP"}); continue
        if len({membership[net, uid] for uid in ids}) == 1:
            results.append({"pair": pair, "status": "ALREADY_CONNECTED_IN_ACTUAL_R299"}); continue
        assert h["domains_normalized"][net] == "DOM_LOGIC"
        for port in (pair["left_port"], pair["right_port"]):
            v = vias[port["UUID"]]; e = expected["copper"][port["UUID"]]
            assert norm(v["net"]) == net and LY in v["flashed"] and e["chunk_sha256"] == port["unchanged_current_native_chunk_SHA256"]
            assert [v["x"], v["y"]] == port["at_mm"]
        a, b = pair["left_port"]["at_mm"], pair["right_port"]["at_mm"]
        roi = box(min(a[0], b[0]) - 24, min(a[1], b[1]) - 24, max(a[0], b[0]) + 24, max(a[1], b[1]) + 24)
        local_records = [records[int(j)] for j in tree.query(roi)]
        foreign = []
        for r in local_records:
            if r["net"] == net: continue
            clearance = max(.15 if h["domains_normalized"].get(r["net"]) == "DOM_LOGIC" else .6, r["local"]) + .025 + r["extra"]
            foreign.append((r, clearance, bounded(r["shape"].intersection(roi), .1 + clearance)))
        local_holes = [holes[int(j)] for j in hole_tree.query(roi)]
        cuts = [s for _, _, s in foreign] + [bounded(s, .380) for uid, s in local_holes if uid not in ids]
        for rule, isreserve, shape in rules:
            if isreserve and net in exemptions.get(rule["name"], set()): continue
            if shape.intersects(roi): cuts.append(bounded(shape.intersection(roi), .125))
        forbidden = unary_union(cuts)
        actual_reference = unary_union([ref_shapes[int(j)].intersection(roi) for j in ref_tree.query(roi)])
        caps = [Point(vias[u]["x"], vias[u]["y"]).buffer(vias[u]["d"] / 2 + .275, quad_segs=256) for u in ids]
        reference = unary_union([actual_reference, *caps])
        reference_axis = reference.buffer(-.10002)
        attempts = []; candidate = None
        print("PAIR", index, net, "span", pair["span_mm"], flush=True)
        for expansion, step in ((8., .1), (16., .075), (24., .05)):
            window = box(min(a[0], b[0]) - expansion, min(a[1], b[1]) - expansion, max(a[0], b[0]) + expansion, max(a[1], b[1]) + expansion)
            free = window.intersection(board_axis).difference(forbidden).intersection(reference_axis)
            if not free.covers(Point(a)) or not free.covers(Point(b)):
                attempts.append({"expansion_mm": expansion, "status": "ACTUAL_ENDPOINT_OUTSIDE_HARD_FREE_REFERENCE", "start_free": free.covers(Point(a)), "end_free": free.covers(Point(b))}); break
            path, gpu = cuda_route(free, a, b, window, step)
            attempt = {"expansion_mm": expansion, "GPU": gpu, "exact_free_polygon": summary(free)}
            attempts.append(attempt)
            print("CUDA_WINDOW", index, expansion, gpu["status"], flush=True)
            if path is None: continue
            path = [[round(x, 6), round(y, 6)] for x, y in path]
            body = bounded(LineString(path), .1); failures = []
            outside = body.difference(reference)
            if not outside.is_empty: failures.append({"kind": "literal_actual_J1_In4_reference_plus_two_owned_caps", "gap": summary(outside)})
            if not free.covers(LineString(path)): failures.append({"kind": "rounded_axis_not_exactly_in_free"})
            for r, clear, _ in foreign:
                d = body.distance(r["shape"])
                if d < clear: failures.append({"kind": r["kind"], "UUID": r["uuid"], "net": r["net"], "clear": clear, "actual": d})
            for uid, shape in local_holes:
                if uid not in ids and body.distance(shape) < .280: failures.append({"kind": "ordinary_drill", "UUID": uid, "actual": body.distance(shape)})
            attempt.update(path=path, length_mm=LineString(path).length, exact_vector_failures=failures)
            if failures: continue
            returns = []
            for uid in ids:
                v = vias[uid]
                near = sorted((math.dist((v["x"], v["y"]), (vias[u]["x"], vias[u]["y"])), u)
                              for u in ground_via_ids if "In4.Cu" in vias[u]["flashed"])
                returns.append({"signal_UUID": uid, "nearest_actual_J1_ground_via_In3_and_In4": near[:3]})
            tracks = [{"uuid": str(uuid.uuid5(uuid.NAMESPACE_URL, "R299-GPU-existing-In3/" + str(index) + "/" + str(i))),
                       "net": vias[pair["left_port"]["UUID"]]["net"], "layer": LY, "w": .2, "a": aa, "b": bb, "locked": False}
                      for i, (aa, bb) in enumerate(zip(path, path[1:]))]
            candidate = {"pair": pair, "tracks": tracks, "body_WKB_SHA256": hashlib.sha256(body.wkb).hexdigest(),
                         "full_actual_body_reference_plus_only_two_owned_caps": True, "exact_vector_clearance_and_drills_PASS": True,
                         "actual_existing_ground_return_neighbors": returns,
                         "finite_own_annular_transfer_return_current_SI_old_reference_native_AFTER": "OPEN_REQUIRED", "adopted": False}
            (OUT / ("pair" + str(index) + "-body.wkb")).write_bytes(body.wkb)
            accepted.append(candidate); break
        results.append({"pair": pair, "current_actual_groups": [membership[net, uid] for uid in ids], "attempts": attempts, "nominee": candidate is not None})
        put("progress.json", {"completed_pairs": len(results), "total_pairs": len(pairs), "nominees": len(accepted), "elapsed_seconds": time.monotonic() - start_time})
        put("bounded-attempts.json", results); put("source-bound-track-nominees.json", accepted)
    put("receipt.json", {"status": "BOUNDED_CUDA_SEARCH_WITH_EXACT_ACTUAL_SOURCE_GEOMETRY_RECHECK_COMPLETE", "candidate_SHA256": binding["native_candidate_SHA256"],
                         "port_pairs": len(pairs), "exact_rechecked_track_nominees": len(accepted), "new_vias": 0, "old_Cu_deletes": 0,
                         "all_current_foreign_native_fill_Cu_drills_rules_and_actual_J1_source_hard": True,
                         "CPU_affinity": proc.cpu_affinity(), "torch": torch.__version__, "GPU": torch.cuda.get_device_name(0),
                         "input_SHA256": pins, "inputs_unchanged": all(sha(Path(p)) == value for p, value in pins.items()),
                         "finite_terminal_return_current_SI_full_native_AFTER_no_loss": "OPEN_REQUIRED", "PCB_written": False,
                         "adopted": False, "manufacturing_ready": False, "elapsed_seconds": time.monotonic() - start_time})
    print("CUDA_EXISTING_PORT_SEARCH_COMPLETE", len(accepted), flush=True)

if __name__ == "__main__":
    main()
