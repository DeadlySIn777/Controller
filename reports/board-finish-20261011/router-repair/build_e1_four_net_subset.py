"""Freeze the reviewed four-net subset; leave the full seven-net donor intact."""
import hashlib
import json
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from compose_additions import inventory, pcbtext
from build_e1_source_donor import potential_joins, net

NAMES = {"/motherboard_status/OBS27_K", "/motherboard_status/OBS34_K",
         "/motherboard_status/OUT5_R_MID", "/motherboard_status/RGB_DRIVER_19"}
BASE = Path("Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb")
RECOVERY = Path("Z:/pcb-runs/claude-finish/agent-work/codex-recovery-20261011")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parent = HERE / "e1-final-donor"
    donor_path, receipt_path = parent / "r06-e1-ordinary-donor.kicad_pcb", parent / "receipt.json"
    manifest_path = HERE / "e1-final-r06-manifest.json"
    inputs = {p: p.read_bytes() for p in [BASE, donor_path, receipt_path, manifest_path,
                                        RECOVERY / "measure/partitions.json", RECOVERY / "candidate.kicad_pcb"]}
    receipt, manifest = json.loads(inputs[receipt_path]), json.loads(inputs[manifest_path])
    if sha(inputs[BASE]) != receipt["baseline_sha256"] or sha(inputs[donor_path]) != receipt["donor_sha256"]:
        raise ValueError("Parent donor identity differs")
    recovery_parts = json.loads(inputs[RECOVERY / "measure/partitions.json"])
    if recovery_parts["sha256"] != sha(inputs[RECOVERY / "candidate.kicad_pcb"]):
        raise ValueError("Recovery partition receipt is stale")
    obs24 = recovery_parts["nets"]["/motherboard_status/OBS24_K"]
    if len(obs24) != 1:
        raise ValueError("OBS24_K redundancy has not been established by native recovery partitions")
    groups = {g["net"]: g for g in manifest["groups"] if g["net"] in NAMES}
    if set(groups) != NAMES:
        raise ValueError("Reviewed subset is absent from complete manifest")
    if any(receipt["per_net"][n]["router_claimed_cross_ground_pour_records"] for n in NAMES):
        raise ValueError("Reviewed subset unexpectedly claims ground-pour crossings")
    b, d = inventory(inputs[BASE]), inventory(inputs[donor_path])
    if b[0] != d[0] or b[2] != d[2] or b[5] != d[5] or any(d[3].get(u) != c for u, c in b[3].items()):
        raise ValueError("Full donor no longer retains every r06 item")
    uuids = {u for name in NAMES for u in receipt["per_net"][name]["new_native_uuids"]}
    additions = [(u, c) for u, c in d[4].items() if u in uuids]
    if len(additions) != len(uuids) or any(u in b[3] or net(c) not in NAMES for u, c in additions):
        raise ValueError("Subset UUID/net delta differs")
    per_net = {name: dict(receipt["per_net"][name],
                         potential_joins_beyond_measured_recovery=potential_joins(groups[name], recovery_parts["nets"][name]))
               for name in sorted(NAMES)}
    if any(n["potential_joins_beyond_measured_recovery"] != 1 for n in per_net.values()):
        raise ValueError("Expected four incremental recovery gaps are no longer present")
    candidate = b[0] + b"".join(b[1]) + b"".join(c for u, c in additions) + b[2]
    actual = inventory(candidate)
    if any(actual[3].get(u) != c for u, c in b[3].items()) or actual[5] != b[5]:
        raise ValueError("Subset changed original r06 items")
    if any(p.read_bytes() != data for p, data in inputs.items()):
        raise ValueError("Original inputs changed while subsetting")
    out = HERE / "e1-four-net-subset"
    out.mkdir(exist_ok=False)
    path = out / "r06-e1-four-net-donor.kicad_pcb"
    path.write_bytes(candidate); path.chmod(stat.S_IREAD)
    summary = {"evidence_class": "source-only exact whole-net subsetting; native proof required", "adopted": False,
               "baseline_path": str(BASE), "baseline_sha256": receipt["baseline_sha256"],
               "donor_path": str(path), "donor_sha256": sha(candidate),
               "seven_net_donor_sha256": receipt["donor_sha256"], "seven_net_donor_unchanged": True,
               "input_hashes": {str(p): sha(data) for p, data in inputs.items()}, "inputs_unchanged": True,
               "all_r06_original_items_retained_exact": True, "selected_whole_nets": sorted(NAMES),
               "native_counts": {kind: sum(pcbtext.chunk_kind(c) == kind for u, c in additions) for kind in ["segment", "via"]},
               "added_native_items": len(additions), "per_net": per_net,
               "potential_joins_beyond_measured_recovery": sum(v["potential_joins_beyond_measured_recovery"] for v in per_net.values()),
               "discarded_groups": {"/motherboard_status/OBS24_K": "Measured recovery5383 already has one connected island",
                                    "/motherboard_status/RGB_DRIVER_3": "Unreviewed claimed ground-pour crossings",
                                    "/motherboard_status/RGB_NETWORK_B_K": "Unreviewed claimed ground-pour crossings"},
               "partial_jobs_hidden": False, "source_failures_retained": {"/motherboard_status/OBS34_K": [1679]},
               "native_constraints": "0.2mm tracks,0.6/0.3mm through vias copied verbatim; ground-pour claimed crossings0 in selected groups. E1 was planned on ripped geometry, so source obstacle/domain clearance remains unqualified. Fresh DRC/no-loss and exact whole-new-net rollback mandatory.",
               "new_native_or_gpu_jobs": 0}
    (out / "receipt.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out / "receipt.json").chmod(stat.S_IREAD)
    manifest_path.chmod(stat.S_IREAD)
    print(json.dumps({k: summary[k] for k in ["donor_sha256", "native_counts", "added_native_items", "potential_joins_beyond_measured_recovery"]}))


if __name__ == "__main__":
    main()
