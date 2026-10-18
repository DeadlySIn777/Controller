"""Reject lost pad connectivity even when the total unconnected count improves.

Read-only guard for refilled net_partitions.py receipts. This does not run DRC,
restore copper, or authorize adoption. Call again after every cleanup/refill.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def validate(receipt):
    if receipt.get("refilled") is not True:
        raise ValueError("partition receipt must come from a zone refill")
    if not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sha256", "")):
        raise ValueError("missing or invalid board hash")
    nets = receipt.get("nets")
    if not isinstance(nets, dict):
        raise ValueError("missing net partitions")
    missing = 0
    for net, groups in nets.items():
        if not isinstance(net, str) or not net or not isinstance(groups, list) or not groups:
            raise ValueError("invalid net partition")
        seen = set()
        for group in groups:
            if not isinstance(group, list) or not group:
                raise ValueError(f"empty or invalid group on {net}")
            for pad in group:
                if not isinstance(pad, str) or not pad or pad in seen:
                    raise ValueError(f"invalid or duplicate pad on {net}")
                seen.add(pad)
        if len(seen) < 2:
            raise ValueError(f"partition lacks multiple pads on {net}")
        missing += len(groups) - 1
    for key in ("pad_island_joins", "api_unconnected_count"):
        if type(receipt.get(key)) is not int or receipt[key] < 0:
            raise ValueError(f"invalid {key}")
    if missing != receipt["pad_island_joins"]:
        raise ValueError("partition groups disagree with reported missing joins")
    return nets


def common_groups(before, after):
    parent = {p: p for group in before for p in group}

    def find(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p

    for group in before + after:
        for pad in group[1:]:
            parent[find(pad)] = find(group[0])
    return len({find(p) for p in parent})


def compare(before, after):
    b, a = validate(before), validate(after)
    if set(b) != set(a):
        raise ValueError("net sets changed; loss comparison is unverifiable")
    completed = lost = 0
    changed = {}
    for net in sorted(b):
        if {p for g in b[net] for p in g} != {p for g in a[net] for p in g}:
            raise ValueError(f"pad identities changed on {net}")
        common = common_groups(b[net], a[net])
        c, l = len(b[net]) - common, len(a[net]) - common
        completed += c
        lost += l
        if c or l:
            changed[net] = {"completed": c, "lost": l}
    check = before["pad_island_joins"] - completed + lost == after["pad_island_joins"]
    api_ok = after["api_unconnected_count"] <= before["api_unconnected_count"]
    return {"verdict": "PASS" if check and not lost and api_ok else "FAIL",
            "before_sha256": before["sha256"], "after_sha256": after["sha256"],
            "completed": completed, "lost": lost, "partition_identity_check": check,
            "api_not_increased": api_ok, "missing_before": before["pad_island_joins"],
            "missing_after": after["pad_island_joins"], "per_net": changed,
            "scope": "saved, refilled connectivity receipts only; separate DRC and electrical gates required"}


def check_board(receipt, board):
    if hashlib.sha256(Path(board).read_bytes()).hexdigest() != receipt["sha256"]:
        raise ValueError(f"receipt is stale for board {board}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--before-board", required=True)
    ap.add_argument("--after-board", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    try:
        b = json.loads(Path(args.before).read_text(encoding="utf-8"))
        a = json.loads(Path(args.after).read_text(encoding="utf-8"))
        result = compare(b, a)
        check_board(b, args.before_board)
        check_board(a, args.after_board)
        code = 0 if result["verdict"] == "PASS" else 1
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result, code = {"verdict": "INVALID", "reason": str(exc)}, 2
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "per_net"}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
