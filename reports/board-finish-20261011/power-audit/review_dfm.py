"""Independent read-only source geometry audit of c02a DFM transfer.

This screen does not replace native/refilled connectivity or DRC.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from compose_additions import inventory, pcbtext
from reconcile_dfm import children, kind, pose, ref_of, validate
from test_dfm_contract import board


def parse_pair(chunk, token):
    match = re.search(rb"\(" + token + rb" ([-0-9.eE]+) ([-0-9.eE]+)(?: [-0-9.eE]+)?\)", chunk)
    if not match:
        raise ValueError("missing numeric coordinate " + token.decode())
    return tuple(float(v) for v in match.groups())


def value(chunk, token):
    match = re.search(rb"\(" + token + rb" ([-0-9.eE]+)\)", chunk)
    if not match:
        raise ValueError("missing value " + token.decode())
    return float(match.group(1))


def net_name(chunk):
    match = re.search(rb'\(net ("(?:\\.|[^"\\])*"|[-0-9]+)', chunk)
    if not match:
        raise ValueError("missing net")
    raw = match.group(1)
    return json.loads(raw.decode()) if raw.startswith(b'"') else int(raw)


def global_pad(local, position):
    angle = math.radians(position[2])
    x, y = local
    # KiCad board coordinates have downward-positive Y.
    return (position[0] + x * math.cos(angle) + y * math.sin(angle),
            position[1] - x * math.sin(angle) + y * math.cos(angle))


def pads(chunk):
    _, nodes = children(chunk)
    position = pose(nodes)
    return [{"number": re.match(rb'\(pad "([^"\\]+)"', node).group(1).decode(),
             "net": net_name(node),
             "local": parse_pair(node, b"at"),
             "world": global_pad(parse_pair(node, b"at"), position)}
            for node in nodes if kind(node) == b"pad" and b"(net " in node]


def segment(start, end, net=999, uid="unexpected-addition"):
    return (f'\t(segment\n\t\t(start {start[0]} {start[1]})\n\t\t(end {end[0]} {end[1]})\n'
            f'\t\t(width 2.0)\n\t\t(layer "In3.Cu")\n\t\t(net {net})\n'
            f'\t\t(uuid "{uid}")\n\t)\n').encode()


def main():
    target = Path("Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb")
    candidate = HERE.parent / "revisions/c02a-r06-dfm.kicad_pcb"
    source = target.read_bytes()
    result = candidate.read_bytes()
    actual = validate(source, result)
    before, after = inventory(source), inventory(result)
    retained_pad_centres = []
    for chunk in before[3].values():
        if pcbtext.chunk_kind(chunk) == "footprint":
            ref = ref_of(chunk)
            retained_pad_centres.extend({**pad, "ref": ref} for pad in pads(chunk))
    expected_ties = []
    for move in actual["moved_footprints"]:
        if not move["ref"].startswith("C"):
            continue
        old = next(chunk for chunk in before[3].values()
                   if pcbtext.chunk_kind(chunk) == "footprint" and ref_of(chunk) == move["ref"])
        new = next(chunk for chunk in after[3].values()
                   if pcbtext.chunk_kind(chunk) == "footprint" and ref_of(chunk) == move["ref"])
        old_pads, new_pads = pads(old), pads(new)
        for old_pad, new_pad in zip(old_pads, new_pads):
            expected_ties.append({"ref": move["ref"], "pad": old_pad["number"], "net": old_pad["net"],
                                  "start": old_pad["world"], "end": new_pad["world"]})
    ties, zones = [], []
    for add in actual["additions"]:
        chunk = after[3][add["uuid"]]
        if add["kind"] == "segment":
            start, end, net = parse_pair(chunk, b"start"), parse_pair(chunk, b"end"), net_name(chunk)
            matched = [tie for tie in expected_ties if tie["net"] == net and
                       (math.dist(start, tie["end"]) < 0.000002 or math.dist(end, tie["end"]) < 0.000002)]
            far_end = end if matched and math.dist(start, matched[0]["end"]) < 0.000002 else start
            existing_targets = [{"ref": pad["ref"], "pad": pad["number"], "net": pad["net"], "world": pad["world"]}
                                for pad in retained_pad_centres if pad["net"] == net and math.dist(far_end, pad["world"]) < 0.000002]
            ties.append({"uuid": add["uuid"], "net": net, "layer": pcbtext.chunk_layer(chunk),
                         "start": start, "end": end, "width_mm": value(chunk, b"width"),
                         "matches_expected_moved_pads": matched, "retained_same_net_target_pads": existing_targets})
        else:
            zones.append({"uuid": add["uuid"], "source": chunk.decode("utf-8")})

    defects = []
    fixture = board()
    arbitrary = fixture[:-2] + segment((100, 100), (150, 150)) + fixture[-2:]
    try:
        validate(fixture, arbitrary)
        defects.append({"kind": "unbounded_addition", "observed": "unrelated net999 width2mm In3 segment accepted",
                        "risk": "Structural DFM guard permits arbitrary new copper, beyond the reviewed eight capacitor ties"})
    except ValueError:
        pass
    copper_before = board().replace(b'"F.SilkS"', b'"F.Cu"').replace(
        b'(layer "F.Cu") (uuid "line-one")', b'(layer "F.Cu") (metadata (layer "F.SilkS")) (uuid "line-one")')
    copper_after = copper_before.replace(b'(stroke (width 0.1)', b'(stroke (width 0.9)')
    try:
        validate(copper_before, copper_after)
        defects.append({"kind": "nested_layer_silk_match", "observed": "nested F.SilkS token makes copper graphic editable",
                        "risk": "Silk detection searches descendants; direct child layer and valid children should be checked"})
    except ValueError:
        pass
    receipt = {"evidence_class": "independent host source geometry/guard audit, native gate still required",
               "files": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in (target, candidate, HERE.parent / "reconcile_dfm.py", HERE.parent / "test_dfm_contract.py")},
               "changed_footprints": len(actual["changed_footprints"]), "moves": actual["moved_footprints"],
               "expected_ties": expected_ties, "actual_ties": ties, "new_rule_areas": zones,
               "all_eight_ties_match_new_pad_to_retained_same_net_pad_centres": len(ties) == 8 and
                    all(len(tie["matches_expected_moved_pads"]) == 1 and tie["retained_same_net_target_pads"]
                        and tie["layer"] == "F.Cu" and abs(tie["width_mm"] - 0.448) < 1e-9 for tie in ties),
               "guard_defects": defects,
               "limits": ["Native partition guard must prove moved pads reconnect; all-errors refilled DRC required",
                          "Silk clipping/readability and capacitor bypass-loop/current effects need review",
                          "No manufacture claim or full electrical qualification from local-pad-byte preservation"]}
    (HERE / "dfm-independent-review.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"all_eight_ties_match_pad_moves": receipt["all_eight_ties_match_new_pad_to_retained_same_net_pad_centres"],
                      "guard_defects": defects, "changed_footprints": receipt["changed_footprints"]}))


if __name__ == "__main__":
    main()
