"""Transfer reviewed DFM edits only where original footprint bytes still match.

Preserves all target copper. This is construction/source validation, not native
proof of pad connectivity, clearances, electrical behavior or manufacture.
"""
import argparse
import json
import math
import re
from pathlib import Path
from compose_additions import inventory, definition, sha, pcbtext

CAPS = {"C14814", "C14818", "C14825", "C14829"}
FIDS = {"FIDF1", "FIDB1"}
KEEPOUT = b"FID_KEEPOUT_FIDB1_FIDF1"


def children(chunk):
    """Exact depth-two native expressions, respecting escaped quoted strings."""
    nodes = []
    depth = 0
    quoted = escaped = False
    start = None
    first = None
    for i, c in enumerate(chunk):
        if quoted:
            if escaped:
                escaped = False
            elif c == 92:
                escaped = True
            elif c == 34:
                quoted = False
        elif c == 34:
            quoted = True
        elif c == 40:
            if depth == 1:
                start = i
                first = i if first is None else first
            depth += 1
        elif c == 41:
            depth -= 1
            if depth == 1:
                nodes.append(chunk[start:i + 1].replace(b"\r", b""))
            if depth < 0:
                raise ValueError("unbalanced native expression")
    if depth or quoted or first is None:
        raise ValueError("invalid native expression")
    return chunk[:first].replace(b"\r", b""), nodes


def ref_of(chunk):
    match = re.search(rb'\(property "Reference" "([^"\\]+)"', chunk)
    if not match:
        raise ValueError("footprint lacks an unambiguous reference")
    return match.group(1).decode("utf-8")


def kind(node):
    return re.match(rb"\(([^\s()]+)", node).group(1)


def pose(nodes):
    ats = [n for n in nodes if kind(n) == b"at"]
    if len(ats) != 1:
        raise ValueError("footprint needs one pose")
    values = [float(x) for x in ats[0][4:-1].split()]
    if len(values) not in (2, 3) or not all(math.isfinite(x) for x in values):
        raise ValueError("invalid footprint pose")
    return values[:2] + [values[2] if len(values) == 3 else 0]


def is_silk(node):
    return (kind(node) in {b"fp_line", b"fp_arc", b"fp_circle", b"fp_rect", b"fp_poly", b"fp_text", b"property"}
            and re.search(rb'\(layer "[FB]\.SilkS"\)', node) is not None)


def protected_children(nodes):
    # Preserve all property names and text, including reference/value identity.
    # Silk graphic geometry may be clipped; copper, mask, paste, pads, models,
    # courtyard, fabrication and other attributes must remain exact.
    result = []
    for node in nodes:
        if kind(node) == b"at":
            continue
        if is_silk(node):
            if kind(node) == b"property":
                m = re.match(rb'\(property "((?:\\.|[^"\\])*)" "((?:\\.|[^"\\])*)"', node)
                if not m:
                    raise ValueError("invalid silk property")
                result.append((b"silk_property", m.groups()))
            continue
        result.append(node)
    return result


def validate(before, after):
    b, a = inventory(before), inventory(after)
    if b[0] != a[0] or b[2] != a[2]:
        raise ValueError("native header/tail changed")
    if any(a[4].get(u) != ch for u, ch in b[4].items()):
        raise ValueError("DFM patch changed or removed old copper")
    changed = []
    moved = []
    for u, ch in b[3].items():
        new = a[3].get(u)
        if new is None:
            raise ValueError("DFM patch removed existing item")
        if definition(ch) == definition(new):
            continue
        if pcbtext.chunk_kind(ch) != "footprint" or pcbtext.chunk_kind(new) != "footprint":
            raise ValueError("DFM patch changed a non-footprint definition")
        old_ref, new_ref = ref_of(ch), ref_of(new)
        if old_ref != new_ref:
            raise ValueError("reference changed")
        hp, bn = children(ch)
        hq, an = children(new)
        if hp != hq or protected_children(bn) != protected_children(an):
            raise ValueError("DFM patch changed protected footprint/pad data: " + old_ref)
        p, q = pose(bn), pose(an)
        if p != q:
            if p[2] != q[2] or old_ref not in CAPS | FIDS:
                raise ValueError("unapproved footprint movement: " + old_ref)
            if old_ref in CAPS and math.dist(p[:2], q[:2]) > 3:
                raise ValueError("capacitor exceeds bounded relocation")
            if old_ref in FIDS and q[:2] != [14.75, 229.5]:
                raise ValueError("unapproved fiducial position")
            moved.append({"ref": old_ref, "before": p, "after": q})
        changed.append({"uuid": u, "ref": old_ref, "before_sha256": sha(ch), "after_sha256": sha(new)})
    # Anonymous setup/property expressions may not change either.
    ba = [definition(c) for c in b[1] if not pcbtext.chunk_uuid(c)]
    aa = [definition(c) for c in a[1] if not pcbtext.chunk_uuid(c)]
    if ba != aa:
        raise ValueError("anonymous native setup changed")
    additions = []
    for u, ch in a[3].items():
        if u in b[3]:
            continue
        k = pcbtext.chunk_kind(ch)
        if k == "zone":
            h, ns = children(ch)
            expected = {b'(tracks not_allowed)', b'(vias not_allowed)', b'(pads allowed)',
                        b'(copperpour not_allowed)', b'(footprints allowed)'}
            keepouts = [n for n in ns if kind(n) == b"keepout"]
            if (b'(name "' + KEEPOUT + b'")' not in ns or len(keepouts) != 1
                    or set(children(keepouts[0])[1]) != expected
                    or b'(locked yes)' not in ns
                    or b'(layers "F.Cu" "B.Cu" "In1.Cu" "In2.Cu" "In3.Cu" "In4.Cu")' not in ns
                    or len([n for n in ns if kind(n) == b"polygon"]) != 1
                    or any(kind(n) in {b"net", b"net_name", b"filled_polygon"} for n in ns)):
                raise ValueError("unapproved new zone")
        elif k != "segment":
            raise ValueError("unapproved DFM addition")
        additions.append({"uuid": u, "kind": k, "sha256": sha(ch)})
    if len([x for x in additions if x["kind"] == "zone"]) > 1:
        raise ValueError("multiple new fiducial keepouts")
    return {"changed_footprints": changed, "moved_footprints": moved, "additions": additions,
            "all_original_copper_retained_exact": True,
            "all_pad_local_geometry_uuid_and_net_assignments_retained_exact": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("target", "donor-base", "donor", "out", "receipt"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    target, base, donor = [p.read_bytes() for p in (args.target, args.donor_base, args.donor)]
    validated = validate(base, donor)
    t, b, d = [inventory(x) for x in (target, base, donor)]
    if t[0] != b[0] or t[2] != b[2] or t[5] != b[5]:
        raise ValueError("target physical source differs from DFM donor base")
    replacements = {x["uuid"]: d[3][x["uuid"]] for x in validated["changed_footprints"]}
    for u in replacements:
        if t[3].get(u) != b[3][u]:
            raise ValueError("target footprint changed since DFM donor: " + u)
    additions = [d[3][x["uuid"]] for x in validated["additions"]]
    if any(x["uuid"] in t[3] for x in validated["additions"]):
        raise ValueError("DFM UUID collision")
    candidate = t[0] + b"".join(replacements.get(pcbtext.chunk_uuid(c), c) for c in t[1]) + b"".join(additions) + t[2]
    actual = validate(target, candidate)
    inputs = (args.target, args.donor_base, args.donor)
    if any(p.resolve() in [q.resolve() for q in inputs] for p in (args.out, args.receipt)):
        raise ValueError("outputs alias inputs")
    if args.out.resolve() == args.receipt.resolve() or args.out.exists() or args.receipt.exists():
        raise ValueError("outputs must be distinct and fresh")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(candidate)
    receipt = {"evidence_class": "source/native structural DFM reconciliation only", "adopted": False,
               "before_sha256": sha(target), "candidate_sha256": sha(candidate),
               "inputs": {str(p.resolve()): sha(v) for p, v in zip(inputs, (target, base, donor))}, **actual,
               "limits": ["Fresh native refill, no-loss connectivity, all-errors DRC and DFM checks required",
                          "Fiducial clear area and bypass-loop electrical quality need independent review"]}
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_sha256": receipt["candidate_sha256"], "changed_footprints": len(actual["changed_footprints"]),
                      "moved_footprints": actual["moved_footprints"], "additions": len(additions), "adopted": False}))


if __name__ == "__main__":
    main()
