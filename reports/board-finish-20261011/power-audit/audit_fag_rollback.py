"""Independent exact-byte ownership audit for whole-FAG rollback; host only."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from compose_additions import inventory, pcbtext
from reconcile_dfm import children, kind

NET = "/motherboard_motors{slash}FIELD_GND"
BASE = HERE / "fag-r06/input/board.kicad_pcb"
DONOR = HERE / "fag-r06/candidate/board.kicad_pcb"
SOURCE = HERE.parent / "recovery-composite/e1/c04-four-net-e1-dfm.kicad_pcb"
EXPECTED = {
    "base": "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53",
    "donor": "a10803bbfa3aa5b7e1a859ca4c5a7b6481969c97dc038a66cef21f92e5f61789",
    "source": "abed2445e14ce438464a5e2f8d073eb71dc329a66fc5b882a97b6b5be6b12af7",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_rollback(base_data, donor_data, source_data, candidate_data, expected_count=261):
    base, donor, source, candidate = [inventory(data) for data in (base_data, donor_data, source_data, candidate_data)]
    require(base[0] == donor[0] and base[2] == donor[2] and base[5] == donor[5], "FAG donor changed non-copper definitions")
    require(all(donor[3].get(uuid) == chunk for uuid, chunk in base[3].items()), "FAG donor changed/removed older native items")
    owned = {uuid: chunk for uuid, chunk in donor[3].items() if uuid not in base[3]}
    require(len(owned) == expected_count, "Unexpected complete FAG donor item count")
    counts = {"segment": 0, "via": 0}
    for uuid, chunk in owned.items():
        item_kind = pcbtext.chunk_kind(chunk)
        require(item_kind in counts, "FAG ownership includes a non-segment/via")
        nodes = children(chunk)[1]
        fields = {kind(node): node for node in nodes}
        require(json.loads(fields[b"net"][5:-1]) == NET, "FAG ownership contains another net")
        require(fields[b"locked"] == b"(locked yes)", "FAG addition is not locked")
        if item_kind == "segment":
            require(pcbtext.chunk_layer(chunk) == "In3.Cu" and fields[b"width"] in {b"(width 0.3)", b"(width 0.8)"},
                    "Unexpected donor track layer/width")
        else:
            require(fields[b"size"] == b"(size 0.6)" and fields[b"drill"] == b"(drill 0.3)", "Unexpected donor via geometry")
        counts[item_kind] += 1
        require(source[3].get(uuid) == chunk, "c04 does not contain exact donor-owned item: " + uuid)
    if expected_count == 261:
        require(counts == {"segment": 253, "via": 8}, "Unexpected whole-FAG copper inventory")
    expected_data = source[0] + b"".join(chunk for chunk in source[1] if pcbtext.chunk_uuid(chunk) not in owned) + source[2]
    require(candidate_data == expected_data, "Rollback differs from exact deletion of all and only FAG donor chunks")
    require(set(source[3]) - set(candidate[3]) == set(owned), "Removed UUID ownership differs")
    require(not (set(candidate[3]) - set(source[3])), "Rollback added native items")
    require(all(candidate[3].get(uuid) == chunk for uuid, chunk in source[3].items() if uuid not in owned), "Protected source item changed")
    require(candidate[0] == source[0] and candidate[2] == source[2] and candidate[5] == source[5], "Non-copper/header/tail changed")
    return {"whole_FAG_donor_ownership": True, "removed_tracks": counts["segment"], "removed_vias": counts["via"],
            "removed_items": len(owned), "removed_item_uuids": sorted(owned),
            "protected_c04_items_retained": len(candidate[3]), "added_items": 0, "changed_retained_items": 0,
            "non_FAG_source_bytes_preserved": True, "header_tail_preserved": True,
            "electrical_qualification": "OPEN; selected partial 96mA return branch is withdrawn, with no replacement claimed"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--out", type=Path, default=HERE / "c05-fag-rollback-audit.json")
    args = ap.parse_args()
    paths = {"base": BASE, "donor": DONOR, "source": SOURCE, "candidate": args.candidate.resolve()}
    blobs = {name: path.read_bytes() for name, path in paths.items()}
    for name, expected in EXPECTED.items():
        require(sha(blobs[name]) == expected, "Frozen " + name + " board changed")
    proof = validate_rollback(blobs["base"], blobs["donor"], blobs["source"], blobs["candidate"])
    read_set = {str(path): sha(blobs[name]) for name, path in paths.items()}
    for path in (Path(__file__).resolve(), HERE.parent / "compose_additions.py", HERE.parent / "reconcile_dfm.py",
                 Path(pcbtext.__file__).resolve(), HERE / "fag-r06/final-proof.json"):
        read_set[str(path)] = sha(path.read_bytes())
    for path, expected in read_set.items():
        require(sha(Path(path).read_bytes()) == expected, "Audit input changed: " + path)
    result = {"verdict": "PASS", "evidence_class": "Frozen-source host rollback ownership audit only",
              "candidate": str(paths["candidate"]), "candidate_sha256": sha(blobs["candidate"]),
              "source": str(SOURCE), "source_sha256": EXPECTED["source"], "audit": proof,
              "read_set_sha256": read_set, "native_launched": False, "board_adopted": False,
              "limits": ["No native refill or DRC was run by this auditor; fresh c05 native measurements and uncapped exact r06 partition/no-loss guard are required",
                         "Whole-FAG rollback withdraws its selected three-join native gain and partial return branch; it does not finish power/return design",
                         "All c04 foreign/recovered/In3/indicator/DFM source items remain byte-exact; their independent qualification and final composite gates remain required",
                         "Stored fills are inherited as exact source bytes and require independent fresh native fill/export before final editable bundle"]}
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "candidate_sha256": result["candidate_sha256"], "audit_out": str(args.out),
                      "receipt_sha256": sha(args.out.read_bytes()), "removed_items": proof["removed_items"]}))


if __name__ == "__main__":
    main()
