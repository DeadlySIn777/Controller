"""Hardened independent DFM source guard; does not alter the active native runner.

Only reviewed capacitor-pad ties, fiducial moves/keepout and silk edits are
accepted. A native refill, whole-board no-loss proof and DRC remain mandatory.
"""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from compose_additions import inventory, pcbtext, sha
from reconcile_dfm import CAPS, FIDS, children, kind, pose, ref_of, validate as legacy_validate

CAP_DELTAS = {"C14814": (-0.3, 0.0), "C14818": (0.3, 0.0),
              "C14825": (-0.1, -0.3), "C14829": (0.0, 0.3)}
TIE_WIDTH = 0.448
TOL = 0.000002


def direct_layer(node):
    _, nodes = children(node)
    layers = [item for item in nodes if kind(item) == b"layer"]
    if len(layers) != 1:
        return None
    match = re.fullmatch(rb'\(layer "([^"\\]+)"\)', layers[0])
    return match.group(1).decode() if match else None


def silk(node):
    return kind(node) in {b"fp_line", b"fp_arc", b"fp_circle", b"fp_rect", b"fp_poly", b"fp_text", b"property"} and direct_layer(node) in {"F.SilkS", "B.SilkS"}


def protected(nodes):
    result = []
    for node in nodes:
        token = kind(node)
        if token == b"at":
            continue
        if silk(node):
            if token in {b"property", b"fp_text"}:
                header, _ = children(node)
                result.append((token, header.strip()))
            continue
        result.append(node)
    return result


def coordinate(node, token):
    _, nodes = children(node)
    matches = [item for item in nodes if kind(item) == token]
    if len(matches) != 1:
        raise ValueError("one coordinate required: " + token.decode())
    values = matches[0][len(token) + 2:-1].split()
    if len(values) not in (2, 3):
        raise ValueError("invalid coordinate")
    values = [float(value) for value in values]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("non-finite coordinate")
    return tuple(values[:2])


def net(node):
    _, nodes = children(node)
    matches = [item for item in nodes if kind(item) == b"net"]
    if len(matches) != 1:
        raise ValueError("one net required")
    match = re.match(rb'\(net ("(?:\\.|[^"\\])*"|[-0-9]+)', matches[0])
    if not match:
        raise ValueError("invalid net")
    raw = match.group(1)
    return json.loads(raw.decode()) if raw.startswith(b'"') else int(raw)


def world_pad(local, location):
    angle = math.radians(location[2])
    x, y = local
    return (location[0] + x * math.cos(angle) + y * math.sin(angle),
            location[1] - x * math.sin(angle) + y * math.cos(angle))


def pad_inventory(chunk):
    _, nodes = children(chunk)
    location = pose(nodes)
    ref = ref_of(chunk)
    pads = []
    for index, node in enumerate(item for item in nodes if kind(item) == b"pad"):
        if b"(net " not in node:
            continue
        _, pn = children(node)
        layers = [item for item in pn if kind(item) == b"layers"]
        if len(layers) != 1 or b'"F.Cu"' not in layers[0]:
            continue
        number = re.match(rb'\(pad "([^"\\]+)"', node)
        if not number:
            raise ValueError("invalid pad number")
        pads.append({"ref": ref, "number": number.group(1).decode(), "index": index,
                     "net": net(node), "world": world_pad(coordinate(node, b"at"), location)})
    return pads


def near(first, second):
    return math.dist(first, second) <= TOL


def check_keepout(chunk):
    _, nodes = children(chunk)
    allowed = {b"locked", b"layers", b"uuid", b"name", b"hatch", b"connect_pads", b"min_thickness",
               b"keepout", b"placement", b"fill", b"polygon"}
    if {kind(item) for item in nodes} != allowed or any(count != 1 for count in Counter(kind(item) for item in nodes).values()):
        raise ValueError("unexpected fiducial keepout fields")
    polygon = next(item for item in nodes if kind(item) == b"polygon")
    _, polygon_nodes = children(polygon)
    if len(polygon_nodes) != 1 or kind(polygon_nodes[0]) != b"pts":
        raise ValueError("unexpected fiducial keepout polygon")
    _, point_nodes = children(polygon_nodes[0])
    if len(point_nodes) != 48 or any(kind(item) != b"xy" for item in point_nodes):
        raise ValueError("unexpected fiducial keepout polygon vertices")
    points = []
    for item in point_nodes:
        values = [float(value) for value in item[4:-1].split()]
        if len(values) != 2 or not all(math.isfinite(value) for value in values):
            raise ValueError("invalid fiducial keepout vertex")
        points.append(values)
    for index, point in enumerate(points):
        angle = math.radians(360 * index / 48)
        expected = [14.75 + 1.553326 * math.cos(angle), 229.5 + 1.553326 * math.sin(angle)]
        if not near(point, expected):
            raise ValueError("fiducial keepout outside reviewed polygon")


def validate(before, after):
    legacy = legacy_validate(before, after)
    b, a = inventory(before), inventory(after)
    expected, retained = [], []
    changed_poses = {item["ref"] for item in legacy["moved_footprints"]}
    for uid, old in b[3].items():
        if pcbtext.chunk_kind(old) != "footprint":
            continue
        new = a[3][uid]
        _, old_nodes = children(old)
        _, new_nodes = children(new)
        if protected(old_nodes) != protected(new_nodes):
            raise ValueError("direct-layer protected footprint data changed: " + ref_of(old))
        ref = ref_of(old)
        if ref not in changed_poses:
            retained.extend(pad_inventory(old))
            continue
        if ref in CAPS:
            first, second = pose(old_nodes), pose(new_nodes)
            delta = (second[0] - first[0], second[1] - first[1])
            if not near(delta, CAP_DELTAS[ref]):
                raise ValueError("capacitor displacement differs from reviewed recipe")
            new_pads = pad_inventory(new)
            if len(new_pads) != 2:
                raise ValueError("reviewed capacitor needs two F.Cu pads")
            expected.extend(new_pads)
    matched, ties, zones = Counter(), [], []
    for item in legacy["additions"]:
        chunk = a[3][item["uuid"]]
        if item["kind"] == "zone":
            check_keepout(chunk)
            zones.append(item["uuid"])
            continue
        _, nodes = children(chunk)
        token_counts = Counter(kind(node) for node in nodes)
        if (set(token_counts) - {b"start", b"end", b"width", b"layer", b"net", b"uuid", b"locked"}
                or any(count != 1 for count in token_counts.values())):
            raise ValueError("unexpected capacitor tie fields")
        widths = [node for node in nodes if kind(node) == b"width"]
        if len(widths) != 1 or not math.isclose(float(widths[0][7:-1]), TIE_WIDTH, abs_tol=1e-9):
            raise ValueError("capacitor tie width differs from reviewed recipe")
        if direct_layer(chunk) != "F.Cu":
            raise ValueError("capacitor tie must remain on F.Cu")
        start, end, name = coordinate(chunk, b"start"), coordinate(chunk, b"end"), net(chunk)
        owners = [pad for pad in expected if pad["net"] == name and (near(start, pad["world"]) or near(end, pad["world"]))]
        if len(owners) != 1:
            raise ValueError("new segment lacks one reviewed moved-capacitor pad owner")
        owner = owners[0]
        far = end if near(start, owner["world"]) else start
        targets = [pad for pad in retained if pad["net"] == name and near(far, pad["world"])]
        if not targets or math.dist(start, end) > 2:
            raise ValueError("capacitor tie lacks a bounded retained same-net pad endpoint")
        identity = (owner["ref"], owner["number"], owner["index"])
        matched[identity] += 1
        ties.append({"uuid": item["uuid"], "owner": owner, "retained_targets": targets,
                     "width_mm": TIE_WIDTH, "length_mm": math.dist(start, end), "net": name})
    identities = {(pad["ref"], pad["number"], pad["index"]) for pad in expected}
    if set(matched) != identities or any(count != 1 for count in matched.values()) or len(ties) != len(expected):
        raise ValueError("each moved-capacitor pad needs exactly one reviewed tie")
    fid_moves = changed_poses & FIDS
    if fid_moves and (fid_moves != FIDS or len(zones) != 1):
        raise ValueError("both fiducials and exactly one reviewed keepout are required")
    if not fid_moves and zones:
        raise ValueError("fiducial keepout without reviewed fiducial moves")
    return {**legacy, "guard_version": 2, "capacitor_ties": ties,
            "direct_child_layer_validation": True, "bounded_tie_ownership": True,
            "reviewed_fiducial_polygon": True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("receipt", type=Path)
    args = ap.parse_args()
    if args.receipt.exists() or args.receipt.resolve() in {args.before.resolve(), args.after.resolve()}:
        raise ValueError("receipt must be a fresh separate file")
    contents = [path.read_bytes() for path in (args.before, args.after)]
    guarded = validate(*contents)
    receipt = {"evidence_class": "hardened source DFM contract only", "adopted": False,
               "files": {str(path.resolve()): sha(content) for path, content in zip((args.before, args.after), contents)},
               "checker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               **guarded, "limits": ["Fresh native refill/no-loss/DRC still required on these exact board hashes",
                                      "Bypass/current/SI, silk readability and manufacturing process qualification remain open"]}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"guard_version": 2, "ties": len(guarded["capacitor_ties"]),
                      "changed_footprints": len(guarded["changed_footprints"]), "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
