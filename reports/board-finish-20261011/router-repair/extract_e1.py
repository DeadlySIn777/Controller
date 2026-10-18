"""Read-only whole-net extraction from a frozen E1 checkpoint. No routing/native API."""
import argparse
import hashlib
import json
from pathlib import Path

from protected_net_selector import Selector, normalize


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def collect(jobs, checkpoint, partitions, selector):
    done = checkpoint.get("done")
    if isinstance(done, bool) or not isinstance(done, int) or not 0 <= done <= len(jobs):
        raise ValueError("invalid checkpoint done index")
    jobs_by_net, copper_by_net, successes, failures = {}, {}, set(), set()
    for index, job in enumerate(jobs, 1):
        if job.get("kind") != "power" or not isinstance(job.get("net"), str):
            raise ValueError("only current signal-producer power jobs are supported")
        jobs_by_net.setdefault(job["net"], []).append((index, job))
    for record in checkpoint["tracks"]:
        net = record["net"]
        if net not in jobs_by_net:
            raise ValueError("emitted copper net absent from source jobs")
        copper_by_net.setdefault(net, []).append(record)
        index = record.get("job_index")
        if index is not None:
            if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= done:
                raise ValueError("indexed copper exceeds completed checkpoint jobs")
            if jobs[index - 1]["net"] != net:
                raise ValueError("indexed copper net differs from source job")
            if record.get("kind") == "power":
                points = record.get("points", [])
                if len(points) < 2 or not any(a != b for a, b in zip(points, points[1:])):
                    raise ValueError("successful main route has no nonzero segment")
                successes.add(index)
    key = lambda j: (j["net"], tuple(j["from"]), tuple(j["to"]))
    index_by_key = {key(job): index for index, job in enumerate(jobs, 1)}
    if len(index_by_key) != len(jobs):
        raise ValueError("duplicate source job identities")
    for record in checkpoint["failures"]:
        index = index_by_key.get(key(record["job"]))
        if index is None or jobs[index - 1] != record["job"] or index > done or index in failures:
            raise ValueError("invalid or duplicate source failure")
        failures.add(index)
    if successes & failures:
        raise ValueError("source job has both success and failure")
    partition_nets = {normalize(net): islands for net, islands in partitions["nets"].items()}
    groups, withheld = [], []
    for net, records in sorted(copper_by_net.items()):
        decision = selector.select(net)
        own_jobs = jobs_by_net[net]
        indices = {index for index, job in own_jobs}
        reason = None
        if not decision["eligible"]:
            reason = decision["disposition"]
        elif any(index > done for index in indices):
            reason = "net_has_unattempted_jobs_in_partial_checkpoint"
        elif indices - successes - failures:
            reason = "net_has_unaccounted_completed_jobs"
        islands = partition_nets.get(normalize(net), [])
        identities = {}
        for island_index, island in enumerate(islands):
            for identity in island:
                identities.setdefault(identity.rsplit("#", 1)[0], set()).add(island_index)
        useful = []
        for index, job in own_jobs:
            if index not in successes:
                continue
            ends = [identities.get(".".join(job[end]), set()) for end in ("from", "to")]
            if all(len(end) == 1 for end in ends) and ends[0] != ends[1]:
                useful.append(index)
        if not reason and not useful:
            reason = "no_success_spans_distinct_exact_head_islands"
        entry = {"net": net, "decision": decision, "source_job_indices": sorted(indices),
                 "successful_job_indices": sorted(indices & successes), "failed_job_indices": sorted(indices & failures),
                 "useful_job_indices": useful, "items": records,
                 "source_jobs": [job for index, job in own_jobs]}
        if reason:
            entry["withheld_reason"] = reason
            withheld.append(entry)
        else:
            groups.append(entry)
    return groups, withheld


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-board", required=True)
    parser.add_argument("--partitions", required=True)
    parser.add_argument("--jobs", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    sources = {key: str(Path(getattr(args, key.replace("-", "_"))).resolve())
               for key in ("base-board", "partitions", "jobs", "checkpoint", "catalog")}
    hashes = {key: sha(path) for key, path in sources.items()}
    if checkpoint_hash := load(args.checkpoint).get("jobs_sha"):
        if checkpoint_hash != hashes["jobs"]:
            raise ValueError("checkpoint jobs fingerprint differs from frozen jobs")
    else:
        raise ValueError("checkpoint lacks source jobs fingerprint")
    partitions = load(args.partitions)
    if partitions.get("sha256") != hashes["base-board"]:
        raise ValueError("native partitions do not describe exact base board bytes")
    groups, withheld = collect(load(args.jobs), load(args.checkpoint), partitions, Selector(**load(args.catalog)))
    result = {"evidence_kind": "host extraction only; native preflight/after-cleanup proof required", "base_board_sha256": hashes["base-board"],
              "sources": sources, "source_hashes": hashes, "checkpoint_done": load(args.checkpoint)["done"],
              "source_total_jobs": len(load(args.jobs)), "checkpoint_is_complete": load(args.checkpoint)["done"] == len(load(args.jobs)),
              "groups": groups, "withheld": withheld, "catalog": load(args.catalog),
              "original_copper_deletion_authorized": False}
    for key, path in sources.items():
        if sha(path) != hashes[key]:
            raise ValueError("source changed during extraction")
    destination = Path(args.out).resolve()
    if destination in {Path(path) for path in sources.values()}:
        raise ValueError("manifest destination aliases source")
    destination.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"groups": len(groups), "items": sum(len(group["items"]) for group in groups),
                      "withheld_groups": len(withheld), "checkpoint_done": result["checkpoint_done"],
                      "checkpoint_is_complete": result["checkpoint_is_complete"]}))


if __name__ == "__main__":
    main()
