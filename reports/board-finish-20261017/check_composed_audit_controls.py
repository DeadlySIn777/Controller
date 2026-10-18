"""Executed controls for native pad loss and explicit via-retirement checking."""
import hashlib
import importlib.util
import json
from pathlib import Path

H = Path(__file__).resolve().parent
SCRIPT = H / "audit_composed_actual_after.py"
spec = importlib.util.spec_from_file_location("composed_audit_controls", SCRIPT)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


class Keys:
    @staticmethod
    def keys(group):
        return set(group)


def main():
    tests = []
    def check(name, result):
        assert result, name
        tests.append({"name": name, "PASS": True})
    old = {"nets": {"/a": [["A.1#0", "B.1#0"], ["C.1#0"]]}}
    joined = {"nets": {"/a": [["A.1#0", "B.1#0", "C.1#0"]]}}
    split = {"nets": {"/a": [["A.1#0"], ["B.1#0", "C.1#0"]]}}
    check("merge retains all old islands", not A.partitions(old, joined)[0]["old_islands_split"])
    check("split old island rejected", bool(A.partitions(old, split)[0]["old_islands_split"]))
    missing = {"nets": {"/a": [["A.1#0", "B.1#0"]]}}
    check("missing pad rejected", A.partitions(old, missing)[0]["missing_pads"] == ["C.1#0"])
    extra = {"nets": {"/a": [["A.1#0", "B.1#0", "C.1#0", "D.1#0"]]}}
    check("unexpected physical pad rejected", A.partitions(old, extra)[0]["extra_pads"] == ["D.1#0"])
    renamed = {"nets": {"/alias": [["A.1#0", "B.1#0", "C.1#0"]]}}
    check("raw net rename is not normalized away", len(A.partitions(old, renamed)) == 2)
    check("unchanged island inventory accepted", A.partitions(old, old) == [])
    before = [[("pad", "p", "F.Cu"), ("via", "retired", "F.Cu"), ("via", "retired", "In1.Cu")]]
    after = [[("pad", "p", "F.Cu"), ("via", "survivor", "F.Cu"), ("via", "survivor", "In1.Cu")]]
    check("explicit survivor preserves each actual layer", not A.physical_relationships(before, after, set(), {"retired": "survivor"}, Keys))
    check("retired via not silently ignored", bool(A.physical_relationships(before, after, set(), {}, Keys)))
    after_lost = [[("pad", "p", "F.Cu"), ("via", "survivor", "F.Cu")]]
    check("missing survivor layer rejected", bool(A.physical_relationships(before, after_lost, set(), {"retired": "survivor"}, Keys)))
    after_split = [[("pad", "p", "F.Cu")], [("via", "survivor", "F.Cu"), ("via", "survivor", "In1.Cu")]]
    check("survivor detached from old pad rejected", bool(A.physical_relationships(before, after_split, set(), {"retired": "survivor"}, Keys)))
    with_track = [before[0] + [("track", "oldtrack", "F.Cu")]]
    check("explicit replaced track exempted only by UUID", not A.physical_relationships(with_track, after, {"oldtrack"}, {"retired": "survivor"}, Keys))
    check("unlisted old track loss rejected", bool(A.physical_relationships(with_track, after, set(), {"retired": "survivor"}, Keys)))
    A.preflight()
    check("actual current parent and candidate preflight pass", True)
    A.EXPECTED_SHA = "0" * 64
    rejected = False
    try:
        A.preflight()
    except AssertionError:
        rejected = True
    check("changed expected ledger hash rejected", rejected)
    result = {"status": "EXECUTED_HOST_GUARD_CONTROLS_PASS_NATIVE_AFTER_NOT_EXECUTED",
              "cases": tests, "script_SHA256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
              "board_modified": False, "native_jobs": 0, "native_after_qualification": "PENDING"}
    (H / "composed-audit-controls-r1.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"PASS {len(tests)} composed-audit controls; native AFTER still pending")


if __name__ == "__main__":
    main()
