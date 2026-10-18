"""Fix a reproduced group traversal defect while preserving the original audits."""
from pathlib import Path
import hashlib
import json

H = Path(__file__).resolve().parent
OLD = H.parent / "board-finish-20261011/continuation-r2/field-power"
OUT = H / "actual-full-audit-repaired-r1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quoted(path):
    return repr(path.as_posix())


def main():
    OUT.mkdir(exist_ok=False)
    first = OLD / "audit_combined_R753_actual_full_state_conn_scope_r763.generated.py"
    second = OLD / "audit_combined_actual_full_source_gains_and_CPP_partitions_r767.py"
    assert sha(first) == "1b7fabb30f39a5cb6329dd26a7bff3aa6f1a9c778b0a9d28efa19490a655cd8b"
    assert sha(second) == "dced8e7aa48f0217d798d1ede67f283a087a5fa2822d77ae7cbaee0ed0f58b4a"
    before = OLD / "R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763"
    after = OUT / "r763"
    after.mkdir()
    source = first.read_text(encoding="utf-8")
    original_context = "H = Path(__file__).resolve().parent; ROOT = H.parent"
    assert source.count(original_context) == 1
    source = source.replace(original_context, "H = Path(" + quoted(OLD) + "); ROOT = H.parent")
    oldout = "OUT = H / 'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'"
    assert source.count(oldout) == 1
    source = source.replace(oldout, "BEFORE = H / 'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'\nOUT = Path(" + quoted(after) + ")")
    for name in ("prepare-receipt.json", "actual-full-R157-before-model.pkl", "actual-full-R157-before-all-net-groups.pkl"):
        source = source.replace("(OUT / '" + name + "').read_bytes()", "(BEFORE / '" + name + "').read_bytes()")
        source = source.replace("sha(OUT / '" + name + "')", "sha(BEFORE / '" + name + "')")
    oldloop = """            for gr, dest in ((old, om), (now, nm)):
                for rr in gr:
                    if rr['kind'] != 'fill' and rr['layer'] == layer and rr['uuid'] not in removed:
                        dest[rr['kind'], rr['uuid'], layer].append(rr['shape'])"""
    newloop = """            for netgroups, dest in ((old, om), (now, nm)):
                for group in netgroups:
                    for rr in group:
                        if rr['kind'] != 'fill' and rr['layer'] == layer and rr['uuid'] not in removed:
                            dest[rr['kind'], rr['uuid'], layer].append(rr['shape'])"""
    assert source.count(oldloop) == 1
    source = source.replace(oldloop, newloop)
    marker = "    groups = all_physical(after, ctx, 'AFTER_ACTUAL_ALL_NET_CPP_FULL_GRAPH')"
    assert source.count(marker) == 1
    source = source.replace(marker, marker + """
    # Persist completed actual graph construction before downstream diagnostics.
    # This receipt certifies construction/identity only, never later audit gates.
    cached_model = OUT / 'actual-combined-full-after-model.pkl'
    cached_groups = OUT / 'actual-combined-full-after-all-net-groups.pkl'
    cached_model.write_bytes(pickle.dumps(after, protocol=5))
    cached_groups.write_bytes(pickle.dumps(groups, protocol=5))
    put('actual-graph-cache-receipt.json', {
        'status': 'ACTUAL_NATIVE_GRAPH_CONSTRUCTION_ONLY_LATER_GATES_PENDING',
        'native_candidate_SHA256': expected['board_sha256'],
        'actual_full_geometry_SHA256': sha(NF / 'actual-full-refill-geometry.json'),
        'after_actual_model_SHA256': sha(cached_model),
        'after_actual_groups_SHA256': sha(cached_groups),
        'all_actual_after_graph_nets': len(groups), 'native_jobs': 0,
        'later_contact_source_reference_guards': 'PENDING_NOT_A_PASS',
        'script_SHA256': sha(Path(__file__))})
    print('R763_ACTUAL_GRAPH_CACHE_READY', flush=True)
""")
    # Keep the provenance list bound to the untouched BEFORE prepare receipt.
    source = source.replace("OUT / 'prepare-receipt.json', STAGE", "BEFORE / 'prepare-receipt.json', STAGE")
    target1 = OUT / "audit_full_actual_repaired_r763.py"
    compile(source, str(target1), "exec")
    target1.write_text(source, encoding="utf-8")
    source2 = second.read_text(encoding="utf-8")
    marker2 = "H=Path(__file__).resolve().parent;ROOT=H.parent"
    assert source2.count(marker2) == 1
    source2 = source2.replace(marker2, "H=Path(" + quoted(OLD) + ");ROOT=H.parent")
    source2 = source2.replace("P=H/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763'",
        "P=Path(" + quoted(after) + "); BEFORE=Path(" + quoted(before) + ")")
    source2 = source2.replace("OUT=H/'R753-actual-FULL-source-gain-native-planner-guards-and-CPP-pad-partitions-r767'",
        "OUT=Path(" + quoted(OUT / "r767") + ")")
    for name in ("actual-full-R157-before-model.pkl", "actual-full-R157-before-all-net-groups.pkl"):
        source2 = source2.replace("(P/'" + name + "').read_bytes()", "(BEFORE/'" + name + "').read_bytes()")
    target2 = OUT / "audit_source_gains_rebound_r767.py"
    compile(source2, str(target2), "exec")
    target2.write_text(source2, encoding="utf-8")
    # Control reproduces the original TypeError on a two-component net and
    # demonstrates that distinct component membership is retained by traversal.
    fixture = [[{"kind": "track", "uuid": "a", "layer": "F.Cu"}],
               [{"kind": "pad", "uuid": "b", "layer": "B.Cu"}, {"kind": "fill", "uuid": "z", "layer": "B.Cu"}]]
    reproduced = False
    try:
        for row in fixture:
            row["kind"]
    except TypeError:
        reproduced = True
    observed = [(row["uuid"], row["layer"]) for group in fixture for row in group if row["kind"] != "fill"]
    assert reproduced and observed == [("a", "F.Cu"), ("b", "B.Cu")]
    (OUT / "derivation-receipt.json").write_text(json.dumps({
        "status": "REPRODUCED_NESTED_GROUP_TRAVERSAL_FIXED_IN_ISOLATED_DERIVATIVE",
        "original_failure_log": str(H / "resumed-full-native-host-audits/step-1.log"),
        "original_TypeError_reproduced": reproduced, "two_component_control_rows": observed,
        "input_original_scripts_SHA256": {str(p): sha(p) for p in (first, second)},
        "derived_scripts_SHA256": {str(p): sha(p) for p in (target1, target2)},
        "original_audit_and_partial_results_preserved": True,
        "BEFORE_cache_read_immutable_in_place": str(before),
        "physical_or_reference_threshold_changes": False,
        "native_board_or_fill_changes": False}, indent=2) + "\n", encoding="utf-8")
    guard = (H / "run_checks_guarded.py").read_text(encoding="utf-8")
    a = guard.index("JOBS = [")
    b = guard.index("\n\n\ndef utc()", a)
    replacement = "JOBS = [\n" + "\n".join("    (Path(" + quoted(p) + "), " + repr(sha(p)) + ", " + repr(args) + ")," for p, args in ((target1, ["--after"]), (target2, []))) + "\n]"
    guard = guard[:a] + replacement + guard[b:]
    guard = guard.replace('OUT = HERE / "resumed-full-native-host-audits"', 'OUT = HERE / "resumed-full-native-host-audits-repaired-r1"')
    (H / "run_repaired_checks_guarded.py").write_text(guard, encoding="utf-8")
    print("Repaired saved audits and guarded launcher created.")


if __name__ == "__main__":
    main()
