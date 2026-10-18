"""Bounded ordinary-indicator donor from genuine E1 native copper; source only."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import stat
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from compose_additions import inventory, pcbtext
from extract_e1 import collect
from protected_net_selector import Selector, normalize


def sha(data):
    return hashlib.sha256(data).hexdigest()


def net(chunk):
    m = re.search(rb'\n\t\t\(net "([^"\\]*)"\)', chunk)
    if not m:
        raise ValueError("Native copper lacks a supported exact named net")
    return m.group(1).decode("utf-8")


def potential_joins(group, islands):
    identity = {}
    for index, island in enumerate(islands):
        for pad in island:
            identity.setdefault(pad.rsplit("#", 1)[0], set()).add(index)
    parent = list(range(len(islands)))
    def find(index):
        while parent[index] != index:
            index = parent[index]
        return index
    count = 0
    successful = set(group["successful_job_indices"])
    for index, job in zip(group["source_job_indices"], group["source_jobs"]):
        if index not in successful:
            continue
        ends = [identity.get(".".join(job[end]), set()) for end in ("from", "to")]
        if any(len(end) != 1 for end in ends):
            raise ValueError("Eligible job endpoint has ambiguous physical partition identity")
        a, b = (find(next(iter(end))) for end in ends)
        if a != b:
            parent[b] = a; count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ["base", "partitions", "applied", "ripped", "manifest", "out"]:
        ap.add_argument("--" + name, required=True, type=Path)
    args = ap.parse_args()
    out = args.out.resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError("Output must be a new isolated router-repair child")
    paths = [args.base, args.partitions, args.applied, args.ripped, args.manifest]
    contents = {str(p.resolve()): p.read_bytes() for p in paths}
    original_hashes = {p: sha(data) for p, data in contents.items()}
    manifest = json.loads(args.manifest.read_text())
    parts = json.loads(args.partitions.read_text())
    if parts["sha256"] != sha(args.base.read_bytes()) or manifest["base_board_sha256"] != parts["sha256"]:
        raise ValueError("Base board, partitions and manifest differ")
    source_contents = {k: Path(v).read_bytes() for k, v in manifest["sources"].items()}
    if any(sha(data) != manifest["source_hashes"][k] for k, data in source_contents.items()):
        raise ValueError("Frozen extraction input changed")
    jobs, checkpoint = (json.loads(source_contents[k]) for k in ["jobs", "checkpoint"])
    if checkpoint["done"] != len(jobs) or checkpoint["jobs_sha"] != sha(source_contents["jobs"]):
        raise ValueError("Only an authentic fully completed checkpoint is supported")
    groups, withheld = collect(jobs, checkpoint, parts, Selector(**manifest["catalog"]))
    if groups != manifest["groups"] or withheld != manifest["withheld"]:
        raise ValueError("Manifest is not reproducible from its frozen source accounting")
    base, ripped, applied = (inventory(args.__dict__[k].read_bytes()) for k in ["base", "ripped", "applied"])
    if ripped[0] != applied[0] or ripped[2] != applied[2] or ripped[5] != applied[5]:
        raise ValueError("E1 application changed physical/source definitions")
    if base[0] != ripped[0] or base[2] != ripped[2] or base[5] != ripped[5]:
        raise ValueError("E1 and r06 physical/source definitions differ")
    if any(applied[4].get(u) != c for u, c in ripped[4].items()):
        raise ValueError("E1 application changed retained old copper")
    if any(base[4].get(u) != c for u, c in ripped[4].items()):
        raise ValueError("E1 retained copper differs from original r06")
    allowed = {g["net"] for g in groups}
    additions = [(u, c) for u, c in applied[4].items() if u not in ripped[4] and net(c) in allowed]
    if any(u in base[3] or pcbtext.chunk_kind(c) not in {"segment", "via"} for u, c in additions):
        raise ValueError("Selected E1 copper has UUID collisions or unsupported item kinds")
    per_net = {}
    norm_parts = {normalize(n): v for n, v in parts["nets"].items()}
    for g in groups:
        items = [(u, c) for u, c in additions if net(c) == g["net"]]
        counts = collections.Counter(pcbtext.chunk_kind(c) for u, c in items)
        expected = collections.Counter()
        for r in g["items"]:
            if r["kind"] == "via":
                expected["via"] += 1
            else:
                expected["segment"] += sum(a != b for a, b in zip(r["points"], r["points"][1:]))
        if counts != expected:
            raise ValueError("Applied E1 native delta disagrees with accounted router records on " + g["net"])
        per_net[g["net"]] = {"native_counts": dict(counts), "source_jobs": g["source_job_indices"],
                              "successes": g["successful_job_indices"], "failures": g["failed_job_indices"],
                              "potential_pad_island_joins": potential_joins(g, norm_parts[normalize(g["net"])]),
                              "layers": sorted({r["layer"] for r in g["items"] if "layer" in r}),
                              "widths_mm": sorted({r["width"] for r in g["items"] if "width" in r}),
                              "vias_mm": sorted({(r["d"], r["drill"]) for r in g["items"] if r["kind"] == "via"}),
                              "router_claimed_cross_ground_pour_records": sum(bool(r.get("crosses_ground_pour")) for r in g["items"]),
                              "router_claimed_cross_side_records": sum(bool(r.get("cross_side")) for r in g["items"]),
                              "new_native_uuids": [u for u, c in items]}
    candidate = base[0] + b"".join(base[1]) + b"".join(c for u, c in additions) + base[2]
    reconciled = inventory(candidate)
    if reconciled[5] != base[5] or any(reconciled[3].get(u) != c for u, c in base[3].items()):
        raise ValueError("Source donor changed or removed any original r06 item")
    if any(Path(p).read_bytes() != data for p, data in contents.items()):
        raise ValueError("External/source input changed while extracting")
    out.mkdir(exist_ok=False)
    donor = out / "r06-e1-ordinary-donor.kicad_pcb"
    donor.write_bytes(candidate); donor.chmod(stat.S_IREAD)
    receipt = {"evidence_class": "source-only native copper extraction/reconciliation; no native preflight or adoption",
               "baseline_path": str(args.base.resolve()), "baseline_sha256": parts["sha256"],
               "donor_path": str(donor), "donor_sha256": sha(candidate),
               "original_input_hashes": original_hashes, "original_inputs_unchanged": True,
               "checkpoint_done": checkpoint["done"], "source_total_jobs": len(jobs), "complete_checkpoint": True,
               "selected_whole_nets": len(groups), "native_counts": dict(collections.Counter(pcbtext.chunk_kind(c) for u, c in additions)),
               "added_native_items": len(additions), "per_net": per_net,
               "potential_joins_if_clear_and_connected": sum(n["potential_pad_island_joins"] for n in per_net.values()),
               "baseline_all_items_retained_exact": True, "baseline_critical_copper_retained_exact": True,
               "protected_crossings": "NOT QUALIFIED: E1 routed on ripped geometry; original r06 copper may obstruct these additions. Fresh native DRC and whole-new-net rollback are required; never remove old copper to fit these routes.",
               "routing_constraints": "Only explicit ordinary_indicator whole nets. Original jobs all accounted; failed job1679 retained in ledger. Actual E1 native segments/vias copied verbatim; no track width/clearance relaxation or re-router.",
               "adopted": False, "native_jobs_started": 0, "new_gpu_jobs": 0}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (out / "receipt.json").chmod(stat.S_IREAD)
    print(json.dumps({k: receipt[k] for k in ["donor_sha256", "selected_whole_nets", "native_counts", "added_native_items", "potential_joins_if_clear_and_connected"]}))


if __name__ == "__main__":
    main()
