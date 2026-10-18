"""Freeze read-only source inventories; no native APIs or routing are invoked."""
import collections
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone

from protected_net_selector import Selector, normalize, select_jobs

BASE = Path("Z:/pcb-runs/claude-finish")
OUT = Path(__file__).resolve().parent
E1 = BASE / "agent-work/exp-fresh-signal"


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=1, allow_nan=False) + "\n", encoding="utf-8")


def lines(path):
    return {normalize(line.split("#", 1)[0].strip()) for line in path.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()}


def copper(path):
    """Read saved KiCad10 top-level copper UUID/net records, preserving board bytes."""
    records = {}
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"^\t\((segment|via)\b.*?^\t\)", text, re.M | re.S):
        node = match.group(0)
        uuid = re.search(r'\(uuid ("(?:[^"\\]|\\.)*")\)', node)
        net = re.search(r'\(net ("(?:[^"\\]|\\.)*")\)', node)
        if uuid is None or net is None:
            raise ValueError("unsupported copper identity in saved board")
        identity = json.loads(uuid[1])
        if identity in records:
            raise ValueError("duplicate copper UUID")
        records[identity] = {"item": match[1], "net": json.loads(net[1])}
    return records


def critical_family(decision):
    """Explicit name-based grouping; not an electrical qualification claim."""
    net = decision["net"]
    reasons = decision["reasons"]
    for reason in ("high_speed_pair", "plane_pour_return", "power_table", "owns_copper_zone"):
        if reason in reasons:
            return reason
    if re.search(r"(?:^|[/_])(?:STEP|DIR)\d*(?:[/_]|$)", net):
        return "step_dir"
    if "analog_" in net:
        return "analog"
    if re.search(r"(?:^|[/_])ENC\d|MPG|motherboard_fast_inputs", net):
        return "encoder_mpg_fast_input"
    if "fault_permission" in reasons:
        return "fault_permission_enable"
    return decision["disposition"] + "_other_scope"


def main():
    source_board = BASE / "integrate/revs/r06-stitch-plane-pads-2.kicad_pcb"
    ripped_board = E1 / "ripped.kicad_pcb"
    protected_files = [source_board, ripped_board, BASE / "tools/rip_signals.py",
                       BASE / "tools/corridor_router_in3v.py", BASE / "tools/signal_jobs.py"]
    hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in protected_files}
    geom = load(E1 / "p1/geom.json")
    plane = lines(BASE / "integrate/corridor-work/exclude.txt")
    all_excluded = lines(BASE / "integrate/corridor-work/exclude-pairs.txt")
    pair = all_excluded - plane
    pair |= {normalize(row[key]) for row in load(BASE / "tools/pairs.json") for key in ("p", "n")}
    power = set(load(BASE / "tools/power_widths.json"))
    zone = {row["net"] for row in geom["zones"] if row.get("net")}
    selector = Selector(plane, pair, power, zone)
    save("source-catalog.json", {"plane_nets": sorted(plane), "pair_nets": sorted(pair),
                                 "power_nets": sorted(power), "zone_nets": sorted(zone)})
    partitions = load(BASE / "integrate/measure/r06-stitch-plane-pads-2/partitions.json")
    all_nets = set(partitions["nets"]) | {p["net"] for p in geom["pads"] if p.get("net")}
    decisions = [dict(selector.select(net), source_net=net,
                      remaining_joins=max(0, len(partitions["nets"].get(net, [])) - 1)) for net in sorted(all_nets)]
    save("net-decisions.json", decisions)
    for disposition, name in (("protected", "protected-nets.txt"), ("ordinary_indicator", "ordinary-eligible-nets.txt"),
                              ("review_required", "review-required-nets.txt")):
        (OUT / name).write_text("".join(d["net"] + "\n" for d in decisions if d["disposition"] == disposition), encoding="utf-8")
    before, after = copper(source_board), copper(ripped_board)
    removed = {uid: rec for uid, rec in before.items() if uid not in after}
    if len(removed) != 58126 or len({rec["net"] for rec in removed.values()}) != 892:
        raise ValueError("E1 rip inventory no longer matches saved source experiment")
    if after.keys() - before.keys() or any(after[uid] != before[uid] for uid in after):
        raise ValueError("E1 ripped board changed retained copper identities")
    by_net = collections.defaultdict(collections.Counter)
    for rec in removed.values():
        by_net[rec["net"]][rec["item"]] += 1
    removed_rows = [dict(selector.select(net), source_net=net, removed_items=dict(counts),
                         removed_total=sum(counts.values())) for net, counts in sorted(by_net.items())]
    for row in removed_rows:
        row["name_based_family"] = critical_family(row)
    save("e1-removed-nets.json", removed_rows)
    jobs = load(E1 / "p1/jobs.json")
    eligible, withheld = select_jobs(jobs, selector)
    save("e1-eligible-job-inventory.json", eligible)
    save("e1-withheld-job-inventory.json", withheld)
    report = load(E1 / "p1/jobs-all.report.json")
    long, unaddressable = [], []
    for net, record in report["nets"].items():
        for edge in record.get("unjoined", []):
            long.append(dict(selector.select(net), source_net=net, omission=edge))
        for island in record.get("unaddressable_islands", []):
            unaddressable.append(dict(selector.select(net), source_net=net, pad_identity=island))
    if len(long) != 163 or len(unaddressable) != 8:
        raise ValueError("E1 source omission inventory changed")
    save("e1-omitted-long-joins.json", long)
    save("e1-unaddressable-islands.json", unaddressable)
    checkpoint = load(E1 / "p1/routes.ckpt.json")
    save("e1-checkpoint-snapshot.json", checkpoint)
    successes = {r["job_index"] for r in checkpoint["tracks"] if r.get("kind") == "power" and "job_index" in r}
    censuses = {}
    for name in ("relax40b-r07.json", "relax40b-ripped.json"):
        rows = load(BASE / "agent-work/diag-nopath" / name)
        reach, wall = collections.Counter(), collections.Counter()
        for row in rows:
            key = "ok_both_reach_via" if row["cross_side"] else "ok_reach_dst"
            for category in ("full", "no_tracks", "no_zones", "no_keepouts", "safe0", "all_relaxed", "rip_plane", "rip_power", "rip_plane_power"):
                reach[category] += bool(row[category][key])
            for net, cells in row.get("wall_by_net", {}).items():
                wall[selector.select(net)["disposition"]] += cells
        censuses[name] = {"sample_jobs": len(rows), "reachability": dict(reach), "wall_cells_by_selector_disposition": dict(wall)}
    summary = {
        "evidence_kind": "saved-source inspection and host selector tests; no native routing/DRC/connectivity",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "source_hashes": hashes,
        "current_r06_pad_island_joins": partitions["pad_island_joins"],
        "current_r06_api_unconnected": partitions["api_unconnected_count"],
        "selector_net_counts": dict(collections.Counter(d["disposition"] for d in decisions)),
        "selector_remaining_joins": dict(collections.Counter({category: sum(d["remaining_joins"] for d in decisions if d["disposition"] == category)
                                                              for category in ("protected", "ordinary_indicator", "review_required")})),
        "e1_removed_items": len(removed),
        "e1_removed_nets": len(by_net),
        "e1_removed_by_disposition": {category: {"nets": sum(d["disposition"] == category for d in removed_rows),
                                                  "items": sum(d["removed_total"] for d in removed_rows if d["disposition"] == category)}
                                       for category in ("protected", "ordinary_indicator", "review_required")},
        "e1_removed_by_name_based_family": {category: {"nets": sum(d["name_based_family"] == category for d in removed_rows),
                                                       "items": sum(d["removed_total"] for d in removed_rows if d["name_based_family"] == category)}
                                            for category in sorted({d["name_based_family"] for d in removed_rows})},
        "e1_routed_job_count": len(jobs), "e1_eligible_job_inventory": len(eligible),
        "e1_withheld_job_inventory": len(withheld),
        "e1_checkpoint_done": checkpoint["done"], "e1_checkpoint_main_successes": len(successes),
        "e1_checkpoint_failures": len(checkpoint["failures"]),
        "e1_omitted_long_joins": len(long), "e1_unaddressable_islands": len(unaddressable),
        "e1_unaddressable_by_net": dict(collections.Counter(d["net"] for d in unaddressable)),
        "diag_census": censuses,
        "inventory_is_router_input": False,
        "regenerate_jobs_from_exact_candidate_head_required": True,
        "eligibility_authorizes_copper_deletion": False,
        "native_after_cleanup_lost_zero_required": True,
    }
    for path in protected_files:
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[str(path)]:
            raise ValueError("source changed during read-only inventory")
    summary["protected_source_hashes_unchanged"] = True
    save("inventory-summary.json", summary)
    print(json.dumps(summary, separators=(",", ":")))


if __name__ == "__main__":
    main()
