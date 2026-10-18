"""Read-only exact outcome census; checkpoint processed count is not success coverage."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "router-repair/e1-final-frozen"


def main():
    paths = {name: FROZEN / name for name in ("jobs.json", "checkpoint.json", "routes.json")}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    jobs, ckpt = json.loads(raw["jobs.json"]), json.loads(raw["checkpoint.json"])
    successes = {r["job_index"] for r in ckpt["tracks"] if r.get("kind") == "power"
                 and type(r.get("job_index")) is int and len(r.get("points", [])) >= 2
                 and any(a != b for a, b in zip(r["points"], r["points"][1:]))}
    key = lambda job: (job["net"], tuple(job["from"]), tuple(job["to"]))
    indices = {key(job): i for i, job in enumerate(jobs, 1)}
    if len(indices) != len(jobs):
        raise ValueError("Duplicate source job identity")
    failures = {indices[key(r["job"])] for r in ckpt["failures"]}
    if len(failures) != len(ckpt["failures"]) or successes & failures:
        raise ValueError("Duplicate/conflicting failure ledger")
    unknown = set(range(1, len(jobs) + 1)) - successes - failures
    nets = {"/motherboard_status/OBS27_K", "/motherboard_status/OBS34_K",
            "/motherboard_status/OUT5_R_MID", "/motherboard_status/RGB_DRIVER_19"}
    selected = {i for i, j in enumerate(jobs, 1) if j["net"] in nets}
    if selected & unknown:
        raise ValueError("Selected four-net group has unrepresented outcome")
    result = {"evidence_class": "host source outcome accounting only; no new routing/native job",
              "checkpoint_processed": ckpt["done"], "original_jobs": len(jobs),
              "explicit_main_success_indices": len(successes), "explicit_failure_indices": len(failures),
              "explicit_outcome_coverage": len(successes | failures),
              "unrepresented_indices": [{"job_index_one_based": i, "job": jobs[i-1]} for i in sorted(unknown)],
              "selected_four_net_indices": sorted(selected), "selected_success_indices": sorted(selected & successes),
              "selected_failure_indices": sorted(selected & failures), "selected_accounting_complete": True,
              "unrepresented_jobs_withheld": True, "checkpoint_done_is_not_full_outcome_coverage": True,
              "input_hashes": {str(paths[name]): hashlib.sha256(data).hexdigest() for name, data in raw.items()}}
    for name, path in paths.items():
        if path.read_bytes() != raw[name]:
            raise ValueError("Frozen source changed during census")
    out = HERE / "e1-final-accounting-note.json"
    if out.exists():
        raise ValueError("Refusing to overwrite census")
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"unrepresented_indices", "input_hashes"}}))


if __name__ == "__main__":
    main()
