"""Qualify the composed stage against actual R299 geometry, never planned fills.

This prepares a deterministic successor to the current full native job. A
preflight is not a qualification result; --run refuses incomplete native output.
Inherited R157-to-R299 failures remain independent, even if incremental gates pass.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import pickle
import sys
import time
sys.dont_write_bytecode = True

H = Path(__file__).resolve().parent
STAGE = H / "combined-route-stage-r1"
NF = STAGE / "native-full"
OUT = STAGE / "actual-after-audit-r1"
PARENT = H / "actual-full-audit-repaired-r1/r763"
OLDNF = H.parent / "board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/native-full"
MODEL_SHA = "c71985a7bce58538be801c092a3dc92f8ae4f2766a6e43fc1d8a42b910a91806"
GROUP_SHA = "c89a4df063cf1a817763a7298f7f511f88fbddbc55471e2b2b8786544aec24cd"
BOARD_SHA = "758f3968589948ce6550d30586818a5ffaa673d8dad7fe8c9a7e402598cff1ad"
EXPECTED_SHA = "053a5edc92f6134f7dc9589d2fa3adf9f9f0bd664f12c01e617d0fd7feb4be8e"
HELPER = H / "actual-full-audit-repaired-r1/audit_full_actual_repaired_r763.py"
HELPER_SHA = "763bda36b8fa22d444f99e4964ca417b82a560ee17d0e3a5c098ecfdb30978d7"
POSE_SHA = "a63c0360854f9a8b57a523f12553c134341c39edd96a3bf4f312d8d3d5c0b4f7"
REMOVED_TRACKS = {"16ac4bda-32bd-47a3-8cc4-404758a78d41", "6b5d7465-3e16-4492-82be-cd9ae2fb2ad5",
                  "b17752d1-3aeb-4b37-8ae4-7fbf8502584e", "e0c09d60-50a7-411e-9a56-ce39e23f1bff"}


def sha(p):
    with Path(p).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def put(name, data):
    (OUT / name).write_text(json.dumps(data, indent=1, allow_nan=False) + "\n", encoding="utf-8")


def preflight():
    assert sha(HELPER) == HELPER_SHA
    assert sha(NF / "before-native-all-FP-pad-pose.json") == POSE_SHA
    assert sha(STAGE / "all-copper-expected.json") == EXPECTED_SHA
    expected = json.loads((STAGE / "all-copper-expected.json").read_bytes())
    assert sha(STAGE / "native/board.kicad_pcb") == expected["board_sha256"] == BOARD_SHA
    assert sha(PARENT / "actual-combined-full-after-model.pkl") == MODEL_SHA
    assert sha(PARENT / "actual-combined-full-after-all-net-groups.pkl") == GROUP_SHA
    cache = json.loads((PARENT / "actual-graph-cache-receipt.json").read_bytes())
    assert cache["after_actual_model_SHA256"] == MODEL_SHA
    assert cache["after_actual_groups_SHA256"] == GROUP_SHA
    assert cache["actual_full_geometry_SHA256"] == sha(OLDNF / "actual-full-refill-geometry.json")
    return expected


def partitions(before, after):
    """Compare whole old pad islands, including complete pad inventories."""
    rows = []
    for net in sorted(set(before["nets"]) | set(after["nets"])):
        old = before["nets"].get(net, [])
        now = after["nets"].get(net, [])
        oi = set().union(*(set(g) for g in old)) if old else set()
        ni = set().union(*(set(g) for g in now)) if now else set()
        missing = sorted(oi - ni)
        extra = sorted(ni - oi)
        owner = {pad: i for i, group in enumerate(now) for pad in group}
        split = [g for g in old if len({owner.get(p, "MISSING") for p in g}) != 1]
        if missing or extra or split or len(old) != len(now):
            rows.append({"net": net, "before_islands": len(old), "after_islands": len(now),
                         "missing_pads": missing, "extra_pads": extra, "old_islands_split": split})
    return rows


def physical_relationships(old, new, removed_tracks, retired_vias, K):
    """A retired via is replaced by its individually attested survivor, not ignored."""
    def canonical(key):
        kind, uid, layer = key
        return kind, retired_vias.get(uid, uid) if kind == "via" else uid, layer
    mapping = collections.defaultdict(set)
    for i, group in enumerate(new):
        for key in K.keys(group):
            mapping[canonical(key)].add(i)
    rows = []
    for i, group in enumerate(old):
        keys = {canonical(k) for k in K.keys(group) if not (k[0] == "track" and k[1] in removed_tracks)}
        owners = set().union(*(mapping.get(k, {"MISSING"}) for k in keys)) if keys else set()
        if "MISSING" in owners or len(owners) > 1:
            rows.append({"old_group": i, "after_groups": sorted(owners, key=str),
                         "retained_canonical_layer_keys": [list(k) for k in sorted(keys)]})
    return rows


def main():
    expected = preflight()
    if sys.argv[1:] == ["--preflight"]:
        print(json.dumps({"status": "INPUT_PREFLIGHT_ONLY_NATIVE_AFTER_REQUIRED", "board_SHA256": BOARD_SHA,
                          "actual_R299_cache_hashes_match": True, "native_receipt_present": (NF / "receipt.json").is_file()}))
        return
    assert sys.argv[1:] == ["--run"]
    assert not OUT.exists(), "Preserve any prior attempt; never overwrite its evidence"
    receipt = json.loads((NF / "receipt.json").read_bytes())
    assert receipt["candidate_SHA256"] == BOARD_SHA
    assert receipt["full_native_CPP_Fill_calls"] == 1 and not receipt["discrete_Cu_errors"]
    assert receipt["same_loaded_board_for_all_zones_partitions_Cu_geometry_flash"]
    assert receipt["native_saved_reload_Cu_pose_match"]
    for key, name in (("actual_full_geometry_SHA256", "actual-full-refill-geometry.json"),
                      ("actual_full_flash_SHA256", "actual-full-refill-via-flashes.json"),
                      ("partitions_SHA256", "partitions.json")):
        assert receipt[key] == sha(NF / name)
    assert sha(receipt["genuine_CPP_filled_diagnostic_copy_file"]) == receipt["genuine_CPP_filled_diagnostic_copy_SHA256"]
    pinned_files = [Path(__file__), HELPER, STAGE / "all-copper-expected.json", STAGE / "native/board.kicad_pcb",
                    NF / "receipt.json", NF / "actual-full-refill-geometry.json", NF / "actual-full-refill-via-flashes.json",
                    NF / "partitions.json", NF / "before-native-all-FP-pad-pose.json",
                    PARENT / "actual-combined-full-after-model.pkl", PARENT / "actual-combined-full-after-all-net-groups.pkl",
                    OLDNF / "actual-full-refill-via-flashes.json", OLDNF / "partitions.json",
                    Path(receipt["genuine_CPP_filled_diagnostic_copy_file"])]
    pins = {str(p): sha(p) for p in pinned_files}
    spec = importlib.util.spec_from_file_location("actual_native_audit_helpers", HELPER)
    A = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(A)
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    OUT.mkdir()
    A.OUT = OUT
    started = time.monotonic()
    before = pickle.loads((PARENT / "actual-combined-full-after-model.pkl").read_bytes())
    oldgroups = pickle.loads((PARENT / "actual-combined-full-after-all-net-groups.pkl").read_bytes())
    geometry = json.loads((NF / "actual-full-refill-geometry.json").read_bytes())
    masks = json.loads((NF / "actual-full-refill-via-flashes.json").read_bytes())["vias"]
    pose = json.loads((NF / "before-native-all-FP-pad-pose.json").read_bytes())
    after, context, pads, duplicates = A.native_header(before, geometry, masks, pose, expected)
    for p, q in zip(before["pads"], after["pads"]):
        assert (p["uuid"], p["x"], p["y"], p["net"], set(p["layers"])) == (q["uuid"], q["x"], q["y"], q["net"], set(q["layers"]))
        for layer in p["layers"]:
            # Canonical 180-degree metadata can rotate the start vertex of an
            # identical pad contour. Exact topological equality uses no buffer
            # or area tolerance and rejects any changed physical pad polygon.
            assert unary_union(A.L.poly(p["layers"][layer])).equals(unary_union(A.L.poly(q["layers"][layer])))
    put("all-9971-native-pad-bindings.json", pads)
    put("indistinguishable-paste-identities.json", duplicates)
    groups = A.all_physical(after, context, "COMPOSED_ACTUAL_FULL_GRAPH")
    mp = OUT / "actual-after-model.pkl"
    gp = OUT / "actual-after-all-net-groups.pkl"
    mp.write_bytes(pickle.dumps(after, protocol=5))
    gp.write_bytes(pickle.dumps(groups, protocol=5))
    put("graph-cache-receipt.json", {"status": "GRAPH_ONLY_DOWNSTREAM_GATES_PENDING", "model_SHA256": sha(mp),
                                    "groups_SHA256": sha(gp), "candidate_SHA256": BOARD_SHA})
    K, L = A.K, A.L
    oldtracks = {t["uuid"]: t for t in before["tracks"]}
    newtracks = {t["uuid"]: t for t in after["tracks"]}
    removed = set(oldtracks) - set(newtracks)
    added = set(newtracks) - set(oldtracks)
    changed = {u for u in oldtracks.keys() & newtracks.keys() if oldtracks[u] != newtracks[u]}
    assert removed == REMOVED_TRACKS and len(added) == 25 and not changed
    retire = expected["exact_physical_retirement_survivors"]
    oldmasks = json.loads((OLDNF / "actual-full-refill-via-flashes.json").read_bytes())["vias"]
    maskloss = []
    for uid, layers in oldmasks.items():
        survivor = retire.get(uid, uid)
        lost = set(layers) - set(masks.get(survivor, []))
        if lost:
            maskloss.append({"old_UUID": uid, "retained_or_explicit_survivor_UUID": survivor,
                             "actual_R299_layers_lost": sorted(lost)})
    put("all-actual-R299-mask-losses.json", maskloss)
    relationships, direct, sources = [], [], []
    for index, (net, old) in enumerate(sorted(oldgroups.items())):
        now = groups.get(net, [])
        losses = physical_relationships(old, now, removed, retire, K)
        if losses:
            relationships.append({"net": net, "losses": losses})
        for layer in K.LAYERS:
            of = [r for gr in old for r in gr if r["kind"] == "fill" and r["layer"] == layer]
            nf = [r for gr in now for r in gr if r["kind"] == "fill" and r["layer"] == layer]
            ot, nt = STRtree([r["shape"] for r in of]), STRtree([r["shape"] for r in nf])
            om, nm = collections.defaultdict(list), collections.defaultdict(list)
            for netgroups, dest in ((old, om), (now, nm)):
                for group in netgroups:
                    for r in group:
                        if r["kind"] != "fill" and r["layer"] == layer and r["uuid"] not in removed:
                            uid = retire.get(r["uuid"], r["uuid"]) if r["kind"] == "via" else r["uuid"]
                            dest[r["kind"], uid, layer].append(r["shape"])
            for key, shapes in om.items():
                body = unary_union(shapes)
                oldhit = [of[int(i)] for i in ot.query(body.buffer(A.CONTACT), predicate="intersects")
                          if body.distance(of[int(i)]["shape"]) <= A.CONTACT]
                if not oldhit:
                    continue
                newbody = unary_union(nm.get(key, []))
                newhit = [] if newbody.is_empty else [nf[int(i)] for i in nt.query(newbody.buffer(A.CONTACT), predicate="intersects")
                                                    if newbody.distance(nf[int(i)]["shape"]) <= A.CONTACT]
                if not newhit:
                    direct.append({"net": net, "canonical_key": list(key),
                                   "old_touching_zone_UUIDs": sorted({r["uuid"] for r in oldhit})})
        if index % 50 == 0:
            put("status.json", {"phase": "ALL_OLD_RELATIONSHIP_AND_DIRECT_CONTACTS", "completed_nets": index})
    put("old-physical-relationship-losses.json", relationships)
    put("old-direct-fill-contact-losses.json", direct)
    indices = {}
    for net, ref, pin in A.ROOTS:
        old, now = K.root(oldgroups[net], ref, pin), K.root(groups[net], ref, pin)
        def canon(keys):
            return {(k, retire.get(u, u) if k == "via" else u, ly) for k, u, ly in keys
                    if not (k == "track" and u in removed)}
        lost = canon(K.keys(old)) - canon(K.keys(now))
        sources.append({"net": net, "actual_source": ref + "." + pin,
                        "before_source_pads": A.R.countpad(old), "after_source_pads": A.R.countpad(now),
                        "retained_source_key_losses": [list(k) for k in sorted(lost)]})
        indices[net] = A.source_fill_index(old), A.source_fill_index(now)
    put("nine-source-keys.json", sources)
    oldrefs, newrefs, positive = [], [], []
    domains = {before["domains_normalized"][g]: g for g, _, _ in A.ROOTS[:3]}
    for ground, _, _ in A.ROOTS[:3]:
        oi, ni = indices[ground]
        for t in before["tracks"]:
            net, layer = L.norm(t["net"]), t["layer"]
            if t["uuid"] in removed or layer not in K.MAP or net == ground or before["domains_normalized"].get(net) != before["domains_normalized"][ground]:
                continue
            body = K.A.shape({"kind": "segment", **t}) if not t.get("m") else L.body(t)
            gap = A.local_reference_loss(body, oi, ni, K.MAP[layer])
            if not gap.is_empty:
                oldrefs.append({"ground": ground, "UUID": t["uuid"], "raw_net": t["net"], "layer": layer,
                                "literal_loss": A.witness("oldref-" + t["uuid"], gap)})
        print("COMPOSED_OLDREF", ground, len(oldrefs), flush=True)
    for uid in sorted(added):
        t = newtracks[uid]
        ground, layer = domains.get(after["domains_normalized"].get(L.norm(t["net"]))), t["layer"]
        if ground is None or layer not in K.MAP:
            continue
        body = K.A.shape({"kind": "segment", **t})
        holes = unary_union([context[0][int(i)] for i in context[1].query(body, predicate="intersects")])
        physical = body.difference(holes)
        gap = physical.difference(A.local_supported(physical, indices[ground][1], K.MAP[layer]))
        newrefs.append({"UUID": uid, "raw_net": t["net"], "ground": ground, "layer": layer,
                        "raw_gap_no_own_caps": A.witness("newbody-" + uid, gap),
                        "original_ground_power_signal_scope_and_own_aperture_current_checks": "SEPARATE_REQUIRED"})
    for zone in before["zones"]:
        net = L.norm(zone["net"])
        ground = domains.get(before["domains_normalized"].get(net))
        if ground is None or net == ground:
            continue
        for layer, rings in zone["fills"].items():
            if layer not in K.MAP:
                continue
            for i, body in enumerate(L.poly(rings)):
                gap = A.local_reference_loss(body, indices[ground][0], indices[ground][1], K.MAP[layer])
                if not gap.is_empty:
                    positive.append({"UUID": zone["uuid"], "raw_net": zone["net"], "layer": layer, "contour": i,
                                     "literal_loss": A.witness("oldpositive-" + zone["uuid"] + "-" + layer + "-" + str(i), gap)})
    put("strict-old-reference-losses.json", oldrefs)
    put("new-body-raw-reference-gaps.json", newrefs)
    put("old-positive-pour-reference-losses.json", positive)
    beforeparts = json.loads((OLDNF / "partitions.json").read_bytes())
    afterparts = json.loads((NF / "partitions.json").read_bytes())
    padchanges = partitions(beforeparts, afterparts)
    put("native-pad-partition-changes.json", padchanges)
    counts = {"old_physical_relationship_losses": sum(len(r["losses"]) for r in relationships),
              "old_direct_fill_contact_losses": len(direct), "source_key_losses": sum(len(r["retained_source_key_losses"]) for r in sources),
              "old_reference_losses": len(oldrefs), "old_positive_pour_reference_losses": len(positive),
              "raw_new_body_reference_gaps": sum(not r["raw_gap_no_own_caps"]["EMPTY"] for r in newrefs),
              "native_pad_inventory_or_old_island_losses": sum(bool(r["missing_pads"] or r["extra_pads"] or r["old_islands_split"]) for r in padchanges),
              "actual_R299_retained_or_survivor_mask_losses": len(maskloss),
              "native_mask_failures": len(receipt["old_actual_or_NEW_ordinary_mask_errors"])}
    assert all(sha(Path(path)) == digest for path, digest in pins.items()), "Frozen audit input changed"
    put("receipt.json", {"status": "ACTUAL_NATIVE_INCREMENTAL_DIAGNOSTIC_REVIEW_REQUIRED", "counts": counts,
                         "candidate_SHA256": BOARD_SHA, "filled_board_SHA256": receipt["genuine_CPP_filled_diagnostic_copy_SHA256"],
                         "native_joins_before": beforeparts["pad_island_joins"], "native_joins_after": afterparts["pad_island_joins"],
                         "native_API_after": afterparts["api_unconnected_count"],
                         "actual_model_SHA256": sha(mp), "actual_groups_SHA256": sha(gp),
                         "inherited_R157_to_R299_failures": "RETAINED_SEPARATE_NOT_WAIVED_BY_INCREMENTAL_CHECK",
                         "actual_fill_gain_foreign_geometry_rules_and_no_fill": "OPEN_SEPARATE_REQUIRED",
                         "signal_return_transition_and_power_current_scopes": "OPEN_SEPARATE_REQUIRED",
                         "cached_native_DRC_parity_circuit_ERC": "OPEN_SEPARATE_REQUIRED",
                         "physical_thermal_SI_assembly_manufacturing": "OPEN", "native_jobs": 0,
                         "script_SHA256": sha(Path(__file__)), "elapsed_seconds": time.monotonic() - started,
                         "helper_SHA256": sha(HELPER), "before_native_pad_pose_SHA256": sha(NF / "before-native-all-FP-pad-pose.json"),
                         "input_SHA256": pins, "frozen_inputs_unchanged": True,
                         "adopted": False, "manufacturing_ready": False})
    put("status.json", {"phase": "COMPLETE_REVIEW_REQUIRED", "counts": counts})
    print("COMPOSED_ACTUAL_INCREMENTAL_COMPLETE", counts, flush=True)


if __name__ == "__main__":
    main()
