"""Independent exact whole-group FAG+E1 rollback audit; source/host only."""
import argparse
import json
from collections import Counter
from pathlib import Path
from audit_fag_rollback import BASE, DONOR, SOURCE, EXPECTED, sha, require, inventory, pcbtext, children, kind, validate_rollback

HERE = Path(__file__).resolve().parent
SUBSET = HERE.parent / "recovery-composite/e1/inputs/subset_donor.kicad_pcb"
SUBSET_SHA = "ebdf6b1da6d19ea46d25b31b29429a1ffca2df8d1b7c97fce752ba6377f853dc"
E1_NETS = {"/motherboard_status/OBS27_K", "/motherboard_status/OBS34_K",
           "/motherboard_status/OUT5_R_MID", "/motherboard_status/RGB_DRIVER_19"}
DEFAULT_CANDIDATE = HERE.parent / "recovery-composite/c05/c05-fag-e1-rollback-dfm.kicad_pcb"
EXPECTED_ERRORS = {"FAG": 14, "/motherboard_status/OBS27_K": 138, "/motherboard_status/OBS34_K": 74,
                   "/motherboard_status/OUT5_R_MID": 124, "/motherboard_status/RGB_DRIVER_19": 121}


def item_net(chunk):
    fields = {kind(node): node for node in children(chunk)[1]}
    return json.loads(fields[b"net"][5:-1])


def validate_attribution(attribution, drc, owners, source_uuids, expected_counts=EXPECTED_ERRORS):
    require(attribution["verdict"] == "PASS_EXACT_ERROR_ATTRIBUTION"
            and attribution["all_errors_have_exact_single_donor_owner"] is True, "Root attribution did not pass")
    counts, records = Counter(), []
    for error in drc["violations"]:
        if error["severity"] != "error":
            continue
        item_uuids = [item["uuid"] for item in error["items"]]
        require(set(item_uuids) <= source_uuids, "Raw DRC error names an item outside c04 source")
        matched = {owners[uid] for uid in item_uuids if uid in owners}
        require(len(matched) == 1, "Raw DRC error is not attributable to one removed donor group")
        owner = next(iter(matched))
        counts[owner] += 1
        records.append({"owner": owner, "type": error["type"], "description": error["description"], "item_uuids": item_uuids})
    require(dict(counts) == expected_counts and dict(counts) == attribution["counts_by_new_donor_group"], "Root attribution error counts differ")
    require(records == attribution["records"] and len(records) == attribution["errors"], "Root attribution does not reproduce raw DRC")
    return {"all_errors_attributed_to_removed_groups": True, "raw_drc_errors": len(records), "counts_by_removed_group": dict(counts)}


def validate_composite(base_data, fag_data, subset_data, source_data, candidate_data, fag_count=261, e1_count=201):
    base, fag, subset, source, candidate = [inventory(data) for data in (base_data, fag_data, subset_data, source_data, candidate_data)]
    fag_owned = set(fag[3]) - set(base[3])
    fag_only_rollback = source[0] + b"".join(chunk for chunk in source[1] if pcbtext.chunk_uuid(chunk) not in fag_owned) + source[2]
    fag_proof = validate_rollback(base_data, fag_data, source_data, fag_only_rollback, expected_count=fag_count)
    require(base[0] == subset[0] and base[2] == subset[2] and base[5] == subset[5], "E1 subset changed non-copper definitions")
    require(all(subset[3].get(uid) == chunk for uid, chunk in base[3].items()), "E1 subset changed/removed older items")
    e1_owned = {uid: chunk for uid, chunk in subset[3].items() if uid not in base[3]}
    require(len(e1_owned) == e1_count, "Unexpected whole E1 subset count")
    require(not (fag_owned & set(e1_owned)), "FAG and E1 ownership overlap")
    by_net, kinds = {}, Counter()
    for uid, chunk in e1_owned.items():
        net, item_kind = item_net(chunk), pcbtext.chunk_kind(chunk)
        require(net in E1_NETS and item_kind in {"segment", "via"}, "E1 rollback owns a foreign/non-copper item")
        require(source[3].get(uid) == chunk, "c04 E1 source addition differs from exact donor subset")
        by_net.setdefault(net, []).append({"uuid": uid, "sha256": sha(chunk), "kind": item_kind})
        kinds[item_kind] += 1
    require(set(by_net) == E1_NETS, "Whole E1 net group selection differs")
    if e1_count == 201:
        require(kinds == {"segment": 178, "via": 23}, "Unexpected E1 kind inventory")
    owned = fag_owned | set(e1_owned)
    expected = source[0] + b"".join(chunk for chunk in source[1] if pcbtext.chunk_uuid(chunk) not in owned) + source[2]
    require(candidate_data == expected, "c05 differs from deleting all and only complete FAG+four E1 donor groups")
    require(set(source[3]) - set(candidate[3]) == owned and not (set(candidate[3]) - set(source[3])), "Removed/added UUIDs differ")
    require(all(candidate[3].get(uid) == chunk for uid, chunk in source[3].items() if uid not in owned), "Protected c04 item changed")
    require(candidate[0] == source[0] and candidate[2] == source[2] and candidate[5] == source[5], "Header/tail/non-copper definitions changed")
    return {"FAG": fag_proof, "E1": {"removed_items": len(e1_owned), "removed_tracks": kinds["segment"],
            "removed_vias": kinds["via"], "whole_net_groups": {net: sorted(rows, key=lambda row: row["uuid"]) for net, rows in sorted(by_net.items())}},
            "removed_total": len(owned), "added_items": 0, "changed_retained_items": 0,
            "all_non_owned_source_bytes_retained": True, "protected_c04_items_retained": len(candidate[3])}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", nargs="?", type=Path, default=DEFAULT_CANDIDATE)
    ap.add_argument("--out", type=Path, default=HERE / "c05-rollback-audit.json")
    args = ap.parse_args()
    paths = {"base": BASE, "donor": DONOR, "source": SOURCE, "subset": SUBSET, "candidate": args.candidate.resolve()}
    blobs = {name: path.read_bytes() for name, path in paths.items()}
    for name, expected in {**EXPECTED, "subset": SUBSET_SHA}.items():
        require(sha(blobs[name]) == expected, "Frozen " + name + " changed")
    audit = validate_composite(blobs["base"], blobs["donor"], blobs["subset"], blobs["source"], blobs["candidate"])
    construction = HERE.parent / "recovery-composite/e1/construction.json"
    construction_data = construction.read_bytes()
    receipt = json.loads(construction_data)
    declared = {row["uuid"]: row["sha256"] for row in receipt["stages"]["e1_native_subset_items"]}
    actual = {row["uuid"]: row["sha256"] for rows in audit["E1"]["whole_net_groups"].values() for row in rows}
    require(declared == actual, "E1 c04 construction UUID/chunk-hash ownership differs")
    owners = {uid: "FAG" for uid in audit["FAG"]["removed_item_uuids"]}
    for net, rows in audit["E1"]["whole_net_groups"].items():
        owners.update({row["uuid"]: net for row in rows})
    require(len(owners) == 462, "Total rollback ownership count differs")
    attribution_path = HERE.parent / "c04-error-attribution.json"
    attribution_data = attribution_path.read_bytes()
    attribution = json.loads(attribution_data)
    drc_path = HERE.parent / "measure/c04-main/drc.json"
    drc_data = drc_path.read_bytes()
    drc = json.loads(drc_data)
    require(attribution["candidate_sha256"] == EXPECTED["source"] and attribution["construction_sha256"] == sha(construction_data)
            and attribution["drc_sha256"] == sha(drc_data), "Root attribution is stale/unbound")
    require(drc["kicad_version"] == "10.0.4", "Unexpected raw DRC version")
    attribution_proof = validate_attribution(attribution, drc, owners, set(inventory(blobs["source"])[3]))
    read_set = {str(path): sha(blobs[name]) for name, path in paths.items()}
    read_set[str(construction)] = sha(construction_data)
    read_set[str(attribution_path)] = sha(attribution_data)
    read_set[str(drc_path)] = sha(drc_data)
    for path in (Path(__file__).resolve(), HERE / "audit_fag_rollback.py", HERE.parent / "compose_additions.py",
                 HERE.parent / "reconcile_dfm.py", Path(pcbtext.__file__).resolve()):
        read_set[str(path)] = sha(path.read_bytes())
    for path, expected in read_set.items():
        require(sha(Path(path).read_bytes()) == expected, "Read input changed: " + path)
    result = {"verdict": "PASS", "evidence_class": "Frozen-source exact whole donor-group rollback audit only",
              "candidate_path": str(paths["candidate"]), "candidate_sha256": sha(blobs["candidate"]),
              "source_path": str(SOURCE), "source_sha256": EXPECTED["source"], "audit": audit,
              "independent_raw_error_attribution": attribution_proof,
              "read_set_sha256": read_set, "native_launched": False, "board_adopted": False,
              "power_return_qualification": "OPEN; selected partial FIELD_A return donor is withdrawn; no replacement route/current claim",
              "limits": ["Fresh c05 native refill/DRC, exact r06 uncapped pad-partition/no-loss guard and source/native parity are still required",
                         "All four unsafe E1 source groups and the entire FAG donor are withdrawn; prospective detour/search diagnostics are not routed copper",
                         "Stored fills are inherited byte-exact and need independently frozen fresh fill/export for the final editable bundle",
                         "Full power/load/return/current sharing, SI, analog, isolation, DFM, warnings, unrouted and manufacturing qualification remain separate open gates"]}
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "candidate_sha256": result["candidate_sha256"],
                      "removed_total": audit["removed_total"], "receipt_sha256": sha(args.out.read_bytes()), "out": str(args.out)}))


if __name__ == "__main__":
    main()
