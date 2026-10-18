"""Bind the new diagnostic to one genuine full-fill backend and a CPU guard."""
from pathlib import Path
import hashlib
import json

H = Path(__file__).resolve().parent
STAGE = H / "combined-route-stage-r1"
OLD = H.parent / "board-finish-20261011/continuation-r2"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    source = OLD / "native_combined_all_net_fill_and_real_saved_cache_r298.py"
    assert sha(source) == "e7a76e47acf7a0789d140b4ac47d7e22971e6d5cec5a5562fcb09c55cb0ca9bc"
    expected_path = STAGE / "all-copper-expected.json"
    expected = json.loads(expected_path.read_bytes())
    baseline = json.loads(Path(expected["baseline_full_native_mask_file"]).read_bytes())["vias"]
    retired = set(expected["authorized_removed_actual_full_R157_via_UUIDs"])
    assert retired == {"2193173a-497d-48d4-8833-92e9133ec64a", "67c69f6a-075b-465b-96c4-89a8aff35b02"}
    assert set(baseline) - set(expected["copper"]) == retired
    for lost, survivor in expected["exact_physical_retirement_survivors"].items():
        assert set(baseline[lost]) == set(baseline[survivor]) == {"F.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu", "B.Cu"}
        assert expected["copper"][survivor]["kind"] == "via"
    original = source.read_text(encoding="utf-8")
    old = "assert not e['authorized_removed_actual_full_R157_via_UUIDs']and set(oldmask)<=set(e['copper'])"
    new = """assert set(e['authorized_removed_actual_full_R157_via_UUIDs']) == {'2193173a-497d-48d4-8833-92e9133ec64a','67c69f6a-075b-465b-96c4-89a8aff35b02'}
assert set(oldmask)-set(e['copper']) == set(e['authorized_removed_actual_full_R157_via_UUIDs'])
assert set(e['exact_physical_retirement_survivors']) == set(e['authorized_removed_actual_full_R157_via_UUIDs'])
for retired,survivor in e['exact_physical_retirement_survivors'].items():
 assert set(oldmask[retired]) == set(oldmask[survivor]) == {'F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'}
 assert survivor in e['copper'] and e['copper'][survivor]['kind']=='via'
"""
    assert original.count(old) == 1
    changed = original.replace(old, new)
    backend = H / "native_combined_actual_full_fill_r1.py"
    assert not backend.exists()
    compile(changed, str(backend), "exec")
    backend.write_text(changed, encoding="utf-8")
    guard = (H / "run_checks_guarded.py").read_text(encoding="utf-8")
    a = guard.index("JOBS = [")
    b = guard.index("\n\n\ndef utc()", a)
    args = [str(STAGE / "native/board.kicad_pcb"), str(expected_path), str(STAGE / "native-full"), str(STAGE / "filled-copy/board.kicad_pcb")]
    guard = guard[:a] + "JOBS = [(Path(" + repr(backend.as_posix()) + "), " + repr(sha(backend)) + ", " + repr(args) + ")]" + guard[b:]
    guard = guard.replace('OUT = HERE / "resumed-full-native-host-audits"', 'OUT = HERE / "combined-native-resource-guard-r1"')
    guard = guard.replace('[sys.executable, "-X", "utf8", str(path), *args]', '["C:/Program Files/KiCad/10.0/bin/python.exe", "-X", "utf8", str(path), *args]')
    guard = guard.replace('"python": sys.executable, "affinity": ALLOWED', '"supervisor_python": sys.executable, "job_python": "C:/Program Files/KiCad/10.0/bin/python.exe", "affinity": ALLOWED')
    target = H / "run_combined_native_guarded.py"
    assert not target.exists()
    target.write_text(guard, encoding="utf-8")
    receipt = {"status": "EXACT_TWO_DECLARED_PHYSICAL_VIA_RETIREMENTS_FULL_NATIVE_SCOPE_BOUND",
        "original_backend_file": str(source), "original_backend_SHA256": sha(source),
        "derived_backend_file": str(backend), "derived_backend_SHA256": sha(backend),
        "only_backend_change": "Two exact retired vias explicitly bound to already proven retained all6 survivors; no mask forced or unlisted retirement accepted",
        "baseline_native_candidate": "R299 actual complete all-net fill", "retirement_survivors": expected["exact_physical_retirement_survivors"],
        "candidate_SHA256": sha(STAGE / "native/board.kicad_pcb"), "expected_Cu_SHA256": sha(expected_path),
        "guard_file": str(target), "guard_SHA256": sha(target), "full_fill_calls_planned": 1,
        "new_ordinary_all6_required": expected["required_NEW_ordinary_all6"],
        "affinity": list(range(16, 28)), "pause_total_CPU_percent": 70, "resume_below_percent": 62,
        "user_total_CPU_limit_percent": 80, "native_adoption_and_manufacturing": False}
    (STAGE / "native-run-derivation.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: receipt[k] for k in ("status", "candidate_SHA256", "full_fill_calls_planned")}))


if __name__ == "__main__":
    main()
