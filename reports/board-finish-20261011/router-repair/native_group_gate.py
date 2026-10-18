"""Native staging/whole-new-group rejection on disposable copies only.

Run under a KiCad slot. Stage preserves all original copper. Filter removes only
UUIDs created by stage, and rejects the entire new net group for any DRC violation
with one of its new UUIDs. Final native measurement remains mandatory.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

from protected_net_selector import Selector, normalize


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=1, allow_nan=False) + "\n", encoding="utf-8")


def signature(item):
    common = (item.GetClass(), str(item.GetNetname()), int(item.GetWidth()), bool(item.IsLocked()))
    if item.GetClass() == "PCB_VIA":
        point = item.GetPosition()
        return common + (point.x, point.y, item.GetDrillValue(), int(item.GetViaType()))
    start, end = item.GetStart(), item.GetEnd()
    result = common + (start.x, start.y, end.x, end.y, item.GetLayer())
    if item.GetClass() == "PCB_ARC":
        mid = item.GetMid()
        result += (mid.x, mid.y)
    return result


def copper(board):
    return {item.m_Uuid.AsString(): signature(item) for item in board.GetTracks()}


def preserved(original, after):
    missing = original.keys() - after.keys()
    changed = [uuid for uuid in original.keys() & after.keys() if original[uuid] != after[uuid]]
    if missing or changed:
        raise ValueError(f"original copper preservation failed: {len(missing)} missing/{len(changed)} changed")


def checked_geometry(record):
    def numeric(value, positive=False):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("route geometry must be finite numeric data")
        if positive and value <= 0:
            raise ValueError("route copper size must be positive")
    if record.get("kind") == "via":
        for key in ("x", "y", "d", "drill"):
            numeric(record[key], key in ("d", "drill"))
        if record["drill"] >= record["d"]:
            raise ValueError("via drill must be smaller than copper diameter")
    elif record.get("kind") in ("power", "stub", "padstub", "neck"):
        numeric(record["width"], True)
        if not isinstance(record.get("layer"), str):
            raise ValueError("route track needs layer")
        if not isinstance(record.get("points"), list) or len(record["points"]) < 2:
            raise ValueError("route track needs points")
        for xy in record["points"]:
            if not isinstance(xy, list) or len(xy) != 2:
                raise ValueError("route point needs x/y")
            for coordinate in xy:
                numeric(coordinate)
    else:
        raise ValueError("unsupported emitted copper kind")


def stage(board, api, manifest):
    selector = Selector(**manifest["catalog"])
    original = copper(board)
    # Preflight source identities/layers for every group before mutating the in-memory copy.
    counts = {}
    for footprint in board.GetFootprints():
        reference = str(footprint.GetReference())
        for pad in footprint.Pads():
            key = (reference, str(pad.GetNumber()), normalize(str(pad.GetNetname()))) if pad.GetNetname() else None
            if key:
                counts[key] = counts.get(key, 0) + 1
    for group in manifest["groups"]:
        if not selector.select(group["net"])["eligible"] or board.FindNet(group["net"]) is None:
            raise ValueError("group is protected, unclassified, or absent from native board")
        for job in group["source_jobs"]:
            for endpoint in ("from", "to"):
                key = (*job[endpoint], normalize(group["net"]))
                if counts.get(key) != 1:
                    raise ValueError("source job endpoint is missing or physically ambiguous")
        for record in group["items"]:
            if record["net"] != group["net"]:
                raise ValueError("group contains another net's copper")
            checked_geometry(record)
            if record["kind"] != "via" and board.GetLayerID(record["layer"]) < 0:
                raise ValueError("native layer absent from candidate")
    mapping, groups = {}, []
    for group in manifest["groups"]:
        uuids = []
        net = board.FindNet(group["net"])
        for record in group["items"]:
            if record["kind"] == "via":
                item = api.PCB_VIA(board)
                item.SetPosition(api.VECTOR2I(api.FromMM(record["x"]), api.FromMM(record["y"])))
                item.SetViaType(api.VIATYPE_THROUGH)
                item.SetWidth(api.FromMM(record["d"]))
                item.SetDrill(api.FromMM(record["drill"]))
                pieces = [item]
            else:
                pieces = []
                for start, end in zip(record["points"], record["points"][1:]):
                    a = (api.FromMM(start[0]), api.FromMM(start[1]))
                    b = (api.FromMM(end[0]), api.FromMM(end[1]))
                    if a == b:
                        continue
                    item = api.PCB_TRACK(board)
                    item.SetStart(api.VECTOR2I(*a))
                    item.SetEnd(api.VECTOR2I(*b))
                    item.SetWidth(api.FromMM(record["width"]))
                    item.SetLayer(board.GetLayerID(record["layer"]))
                    pieces.append(item)
            for item in pieces:
                item.SetNet(net)
                item.SetLocked(True)
                board.Add(item)
                uuid = item.m_Uuid.AsString()
                if uuid in original or uuid in mapping:
                    raise ValueError("new copper UUID collision")
                mapping[uuid] = group["net"]
                uuids.append(uuid)
        groups.append({"net": group["net"], "new_uuids": uuids, "source_job_indices": group["source_job_indices"]})
    preserved(original, copper(board))
    return {"original_copper": {uuid: list(value) for uuid, value in original.items()},
            "new_uuid_group": mapping, "groups": groups, "original_copper_deletion_authorized": False}


def rejected_groups(drc, mapping):
    if not isinstance(drc, dict) or not isinstance(drc.get("violations"), list):
        raise ValueError("native DRC JSON lacks violation list")
    rejected, old_only = {}, []
    for violation in drc.get("violations", []):
        # Any listed new-copper rule warning or error rejects its whole group.
        affected = {mapping[item["uuid"]] for item in violation.get("items", []) if item.get("uuid") in mapping}
        for net in affected:
            rejected.setdefault(net, []).append({"type": violation.get("type"), "severity": violation.get("severity")})
        if not affected:
            old_only.append({"type": violation.get("type"), "severity": violation.get("severity")})
    return rejected, old_only


def filter_board(board, ledger, drc):
    original = {uuid: tuple(value) for uuid, value in ledger["original_copper"].items()}
    before = copper(board)
    preserved(original, before)
    mapping = ledger["new_uuid_group"]
    if before.keys() - original.keys() != mapping.keys():
        raise ValueError("native preflight board new-UUID set differs from staging ledger")
    rejected, old_only = rejected_groups(drc, mapping)
    held, removed = [], []
    for item in list(board.GetTracks()):
        uuid = item.m_Uuid.AsString()
        if uuid in mapping and mapping[uuid] in rejected:
            held.append(item)
            board.RemoveNative(item)
            removed.append(uuid)
    preserved(original, copper(board))
    return {"rejected_groups": rejected, "accepted_groups": [group["net"] for group in ledger["groups"] if group["net"] not in rejected],
            "new_items_removed": len(removed), "old_items_removed": 0,
            "old_only_violations": old_only, "native_after_cleanup_partition_lost_zero_required": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("stage", "filter"))
    parser.add_argument("--board", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--drc")
    parser.add_argument("--out", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    started = time.time()
    inputs = [args.board, args.manifest] + ([args.ledger, args.drc] if args.mode == "filter" else [])
    destinations = [args.out, args.out + ".part.kicad_pcb", args.receipt] + ([args.ledger] if args.mode == "stage" else [])
    resolved = lambda path: os.path.normcase(os.path.realpath(os.path.abspath(path)))
    for destination in destinations:
        for source in inputs:
            if resolved(destination) == resolved(source) or (os.path.exists(destination) and os.path.exists(source) and os.path.samefile(destination, source)):
                raise ValueError("output aliases protected source")
    if len({resolved(path) for path in destinations}) != len(destinations):
        raise ValueError("output destinations alias each other")
    import pcbnew
    manifest = load(args.manifest)
    board = pcbnew.LoadBoard(args.board)
    if args.mode == "stage":
        if sha(args.board) != manifest["base_board_sha256"]:
            raise ValueError("staging input differs from exact manifest head")
        if not manifest["groups"]:
            write(args.receipt, {"status": "no_eligible_complete_groups", "saved": False, "seconds": round(time.time() - started, 3)})
            return 4
        ledger = stage(board, pcbnew, manifest)
        ledger["manifest_sha256"] = sha(args.manifest)
        ledger["base_board_sha256"] = sha(args.board)
        write(args.ledger, ledger)
        result = {"status": "prospective_native_staged", "groups": len(ledger["groups"]), "new_items": len(ledger["new_uuid_group"])}
    else:
        if not args.drc:
            raise ValueError("filter requires native DRC JSON")
        ledger = load(args.ledger)
        if sha(args.manifest) != ledger["manifest_sha256"]:
            raise ValueError("manifest changed since native stage")
        result = filter_board(board, ledger, load(args.drc))
        result["native_preflight_drc_sha256"] = sha(args.drc)
        result["status"] = "whole_new_groups_filtered"
    temporary = args.out + ".part.kicad_pcb"
    if pcbnew.SaveBoard(temporary, board, True) is False:
        raise RuntimeError("native SaveBoard failed")
    os.replace(temporary, args.out)
    result.update(saved=True, seconds=round(time.time() - started, 3), output_sha256=sha(args.out),
                  project_settings_skipped=True, original_copper_preserved=True, manufacturing_ready=False)
    write(args.receipt, result)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
