"""Freeze exact add-only native fragments and reject redundant/conflicting paths."""
import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "2"
from pathlib import Path
import hashlib
import json
import math
import pickle
import sys
from decimal import Decimal
import psutil
p = psutil.Process(); p.cpu_affinity(list(range(16, 28))); p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from shapely.geometry import Point, LineString
from shapely import from_wkb

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RUN = HERE / "gpu-existing-In3-ports-r1"
OUT = HERE / "gpu-existing-In3-native-packet-r1"
OLD = ROOT / "reports/board-finish-20261011/continuation-r2"
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
norm = lambda s: s.replace("{slash}", "/")

def decimal(value):
    number = Decimal(str(value))
    assert number * 1000000 == (number * 1000000).to_integral_value()
    return format(number, "f").rstrip("0").rstrip(".") if "." in format(number, "f") else format(number, "f")

def key(pair):
    return frozenset((pair["left_port"]["UUID"], pair["right_port"]["UUID"]))

def main():
    assert not OUT.exists(); OUT.mkdir()
    receipt_path = RUN / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    assert receipt["inputs_unchanged"] and receipt["new_vias"] == 0 and not receipt["adopted"]
    assert receipt["candidate_SHA256"] == "7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2"
    paths = [receipt_path, RUN / "source-bound-track-nominees.json", RUN / "bounded-attempts.json", Path(__file__)]
    pins = {str(f): sha(f) for f in paths}
    candidates = json.loads(paths[1].read_text()); attempts = json.loads(paths[2].read_text())
    bypair = {key(r["pair"]): r for r in attempts}
    expected_file = OLD / "combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json"
    pins[str(expected_file)] = sha(expected_file)
    e = json.loads(expected_file.read_text())["copper"]
    actual_groups_file = ROOT / "reports/board-finish-20261017/actual-full-audit-repaired-r1/r763/actual-combined-full-after-all-net-groups.pkl"
    pins[str(actual_groups_file)] = sha(actual_groups_file)
    assert pins[str(actual_groups_file)] == "c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd"
    actual_groups = pickle.loads(actual_groups_file.read_bytes())
    decorated = []
    for index, c in enumerate(candidates):
        row = bypair[key(c["pair"])]
        passing = [a for a in row["attempts"] if a.get("path") and not a["exact_vector_failures"]]
        assert len(passing) == 1
        body_file = RUN / ("pair" + str(attempts.index(row)) + "-body.wkb")
        pins[str(body_file)] = sha(body_file)
        body = from_wkb(body_file.read_bytes())
        assert hashlib.sha256(body.wkb).hexdigest() == c["body_WKB_SHA256"]
        decorated.append((passing[0]["length_mm"], index, c, row, body, body_file))
    decorated.sort(key=lambda v: v[0])
    selected = []; rejected = []; parents = {}
    def find(n):
        parents.setdefault(n, n)
        while parents[n] != n:
            parents[n] = parents[parents[n]]; n = parents[n]
        return n
    for length, index, c, row, body, body_file in decorated:
        net = c["pair"]["normalized_net"]
        aa, bb = row["current_actual_groups"]
        a, b = (net, aa), (net, bb)
        if find(a) == find(b):
            rejected.append({"candidate_index": index, "reason": "Redundant actual R299 group join; shorter same-net edge selected", "net": net, "length_mm": length}); continue
        conflicts = [{"other_candidate_index": old[1], "gap_mm": body.distance(old[4])}
                     for old in selected if old[2]["pair"]["normalized_net"] != net and body.distance(old[4]) < .175]
        if conflicts:
            rejected.append({"candidate_index": index, "reason": "Prospective new-new peer clearance", "conflicts": conflicts}); continue
        parents[find(a)] = find(b); selected.append((length, index, c, row, body, body_file))
    packets = []; endpoint_context = []
    for length, index, c, row, body, body_file in selected:
        tracks = c["tracks"]
        assert len({t["uuid"] for t in tracks}) == len(tracks)
        assert all(t["uuid"] not in e for t in tracks)
        chunks = []
        for t in tracks:
            assert t["layer"] == "In3.Cu" and t["w"] == .2 and not t["locked"]
            text = ('\t(segment\n\t\t(start ' + ' '.join(decimal(v) for v in t["a"]) + ')\n\t\t(end ' + ' '.join(decimal(v) for v in t["b"]) + ')\n\t\t(width 0.2)\n\t\t(layer "In3.Cu")\n\t\t(net ' + json.dumps(t["net"]) + ')\n\t\t(uuid ' + json.dumps(t["uuid"]) + ')\n\t)\n')
            f = OUT / (t["uuid"] + ".add-segment-fragment")
            f.write_bytes(text.encode())
            chunks.append({"action": "add_exact_segment", "UUID": t["uuid"], "file": str(f), "SHA256": sha(f), "expected_native_integer_coordinates": True})
        for port in (c["pair"]["left_port"], c["pair"]["right_port"]):
            uid = port["UUID"]; via = e[uid]; center = [v / 1e6 for v in via["at_IU"]]
            assert set(via["diameters_IU"].values()) == {600000} and via["drill_IU"] == 300000
            ring = Point(center).buffer(.3, quad_segs=256).difference(Point(center).buffer(.15 / math.cos(math.pi / 1024), quad_segs=256))
            contacts = []
            for tid, t in e.items():
                if t["kind"] != "segment" or t["layer"] != "In3.Cu" or norm(t["raw_net"]) != c["pair"]["normalized_net"]: continue
                a = [v / 1e6 for v in t["start_IU"]]; b = [v / 1e6 for v in t["end_IU"]]
                shape = LineString([a, b]).buffer(t["width_IU"] / 2e6, quad_segs=128)
                area = ring.intersection(shape).area
                if area > .000001: contacts.append({"UUID": tid, "finite_In3_annulus_overlap_mm2": area})
            endpoint_context.append({"candidate_index": index, "signal_via_UUID": uid, "existing_actual_In3_segment_contacts": contacts,
                                     "new_In3_layer_entry_if_no_contacts": not contacts,
                                     "ordinary_return_transfer_current_and_SI": "OPEN_REQUIRED"})
        pad_groups = []
        for gi in row["current_actual_groups"]:
            group = actual_groups[c["pair"]["normalized_net"]][gi]
            pads = sorted({(r["ref"], str(r["pin"])) for r in group if r["kind"] == "pad"})
            assert pads, "Do not credit an orphan-Cu join as a required-pad join"
            pad_groups.append({"actual_group": gi, "named_pads": pads})
        packets.append({"candidate_index": index, "net": c["pair"]["normalized_net"], "length_mm": length,
                        "actual_R299_group_join": row["current_actual_groups"], "existing_terminal_ports": [c["pair"]["left_port"], c["pair"]["right_port"]],
                        "current_actual_named_pad_groups": pad_groups,
                        "operations": chunks, "full_source_body_WKB_file": str(body_file), "full_source_body_WKB_SHA256": pins[str(body_file)],
                        "exact_actual_J1_In4_plus_two_owned_caps_and_foreign_Cu_hole_guards": True,
                        "source_current_return_SI_native_AFTER": "OPEN_REQUIRED"})
    # Additional provenance is a CURRENT snapshot for subsequent independent
    # replay, never a retroactive imported-helper certificate for the GPU run.
    for directory in (OLD / "field-power", OLD / "sbc-power", OLD / "coupled-recovery"):
        sys.path.insert(0, str(directory))
    import R157_native_selected_actual_conversion_r673 as N
    N.K.A.reservations()
    closure = dict(N.K.A.READS)
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if path:
            f = Path(path)
            if f.is_file() and (str(ROOT).lower() in str(f).lower() or "pcb-runs" in str(f).lower()) and f.suffix == ".py": closure[str(f)] = sha(f)
    pins.update(closure)
    report = {"status": "EXACT_ADDITIVE_NATIVE_FRAGMENTS_FROZEN_RETURN_SI_NATIVE_GATES_OPEN",
              "actual_parent_unfilled_SHA256": receipt["candidate_SHA256"],
              "actual_parent_full_filled_SHA256": "6d7719335455a1941c28de1ebd750e862915d483049dd90226e054bd559e1632",
              "GPU_pairs_screened": receipt["port_pairs"], "GPU_vector_PASS_nominees": len(candidates),
              "selected_nonredundant_peer_clear_candidates": len(selected), "prospective_group_joins": len(selected),
              "packets": packets, "not_selected": rejected, "endpoint_existing_In3_context": endpoint_context,
              "new_vias": 0, "old_Cu_deletes": 0, "new_or_changed_ground_or_power_planes": 0,
              "helper_source_snapshot_is_for_current_replay_not_retroactive_GPU_run_provenance": True,
              "all_input_SHA256": pins, "inputs_unchanged": all(sha(Path(f)) == h for f, h in pins.items()),
              "required_before_adoption": ["Exact source-anchored endpoint annular transfers and existing/new reference transitions", "Return/current/SI and all current peer proposal checks", "One joint full native refill, uncapped joins, all old relationships, source/geometry/masks/DRC/parity"],
              "PCB_written": False, "adopted": False, "manufacturing_ready": False}
    (OUT / "exact-additive-native-track-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"selected": len(selected), "new_segments": sum(len(x["operations"]) for x in packets), "rejected_redundant_or_conflicting": len(rejected), "inputs_unchanged": report["inputs_unchanged"], "endpoint_context": endpoint_context}))

if __name__ == "__main__": main()
