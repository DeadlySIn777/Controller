"""Compose additive native segment/via donors; retain target bytes and UUIDs.

This is source reconciliation only. Refill, native DRC, pad-partition comparison,
drill/land, return/domain and power gates remain mandatory before acceptance.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import sys

sys.path.insert(0, "Z:/pcb-runs/claude-finish/tools/integrate")
import pcbtext


def sha(data):
    return hashlib.sha256(data).hexdigest()


def definition(chunk):
    """Ignore only serialized zone-fill caches, retaining every actual outline/rule."""
    normalized = chunk.replace(b"\r\n", b"\n")
    if pcbtext.chunk_kind(chunk) != "zone":
        return normalized
    result = re.sub(rb"(?ms)^\t\t\((?:filled_polygon|fill_segments)\b.*?^\t\t\)\n", b"", normalized)
    if re.search(rb"\t\t\((?:filled_polygon|fill_segments)\b", result):
        raise ValueError("unsupported stored zone-fill format")
    return result


def inventory(data):
    head, chunks, tail = pcbtext.split(data)
    if head + b"".join(chunks) + tail != data:
        raise ValueError("native file does not round-trip exactly")
    by_id = {}
    copper = {}
    other = []
    for chunk in chunks:
        kind, uuid = pcbtext.chunk_kind(chunk), pcbtext.chunk_uuid(chunk)
        if uuid:
            if uuid in by_id:
                raise ValueError(f"duplicate native item UUID {uuid}")
            by_id[uuid] = chunk
        if kind in ("segment", "via", "arc"):
            if not uuid:
                raise ValueError("copper item lacks UUID")
            copper[uuid] = chunk
        else:
            other.append(definition(chunk))
    return head, chunks, tail, by_id, copper, other


def compose(target, donor_base, donor):
    t = inventory(target)
    b = inventory(donor_base)
    d = inventory(donor)
    if b[0] != d[0] or b[2] != d[2] or b[5] != d[5]:
        raise ValueError("donor modifies non-copper source/native definitions")
    for uuid, chunk in b[4].items():
        if d[4].get(uuid) != chunk:
            raise ValueError(f"donor removes or changes original copper {uuid}")
        if t[4].get(uuid) != chunk:
            raise ValueError(f"target removes or changes donor baseline copper {uuid}")
    # Target may contain its own extra copper, but the donor shares identical
    # physical components, board setup, rules and zone definitions with target.
    if b[0] != t[0] or b[2] != t[2] or b[5] != t[5]:
        raise ValueError("target differs from donor physical/setup/zone definitions")
    additions = [(uuid, ch) for uuid, ch in d[4].items() if uuid not in b[4]]
    for uuid, chunk in additions:
        if pcbtext.chunk_kind(chunk) not in ("segment", "via"):
            raise ValueError("only ordinary segments and through-via donors supported")
        if uuid in t[3]:
            raise ValueError(f"donor UUID already exists in target {uuid}")
    result = t[0] + b"".join(t[1]) + b"".join(ch for _, ch in additions) + t[2]
    reconciled = inventory(result)
    if reconciled[5] != t[5] or any(reconciled[3].get(u) != ch for u, ch in t[3].items()):
        raise ValueError("composed candidate changed target items")
    return result, [{"uuid": u, "kind": pcbtext.chunk_kind(ch),
                     "sha256": sha(ch), "layer": pcbtext.chunk_layer(ch)} for u, ch in additions]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", type=Path)
    ap.add_argument("donor_base", type=Path)
    ap.add_argument("donor", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("receipt", type=Path)
    args = ap.parse_args()
    inputs = [p.resolve() for p in (args.target, args.donor_base, args.donor)]
    if args.out.resolve() in inputs or args.receipt.resolve() in inputs or args.out.resolve() == args.receipt.resolve():
        raise ValueError("output paths must be separate from inputs and one another")
    contents = [p.read_bytes() for p in inputs]
    candidate, added = compose(*contents)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists() or args.receipt.exists():
        raise ValueError("candidate or receipt already exists; use a fresh revision")
    args.out.write_bytes(candidate)
    if args.out.read_bytes() != candidate:
        raise ValueError("written candidate differs")
    receipt = {"evidence_class": "source/native byte reconciliation only", "adopted": False,
               "input_hashes": {str(p): sha(c) for p, c in zip(inputs, contents)},
               "candidate_sha256": sha(candidate), "added_items": added,
               "retained_target_items_exact": True,
               "required": ["fresh native refill/DRC", "uncapped connectivity with lost=0",
                            "actual return/domain/drill/land/power qualification"]}
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_sha256": sha(candidate), "additions": len(added), "adopted": False}))


if __name__ == "__main__":
    main()
