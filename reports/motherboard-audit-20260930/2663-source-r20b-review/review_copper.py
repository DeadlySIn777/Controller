"""Read-only exact native-pad copper obligations in saved working r14."""
import hashlib
import json
from pathlib import Path
import pcbnew

HERE = Path(__file__).resolve().parent


def main():
    path = HERE / "inputs/working-r14.kicad_pcb"
    board = pcbnew.LoadBoard(str(path))
    source = json.loads((HERE / "single-pad-semantic-classification.json").read_text(encoding="utf-8"))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    rows = []
    for record in source["rows"]:
        if record["category"] not in ("obsolete_dedicated_machine_status_input", "live_diagnostic_FPGA_output", "optional_unimplemented_PCIE_compute_endpoint"):
            continue
        ref, pin = record["ref"], record["pin"]
        pads = [p for p in fps[ref].Pads() if p.GetNumber() == pin]
        assert len(pads) == 1, (ref, pin)
        pad = pads[0]
        name, code = pad.GetNetname(), pad.GetNetCode()
        assert name == record["net"], (ref, pin, name, record["net"])
        tracks = [t for t in board.GetTracks() if t.GetNetCode() == code]
        zones = [z for z in board.Zones() if z.GetNetCode() == code]
        rows.append({"ref": ref, "pin": pin, "native_net": name, "pad_uuid": str(pad.m_Uuid),
                     "track_or_via_items": len(tracks), "zone_items": len(zones),
                     "zero_existing_copper": not tracks and not zones, "category": record["category"]})
    legacy = [r for r in rows if r["category"] == "obsolete_dedicated_machine_status_input"]
    assert len(legacy) == 7 and all(r["zero_existing_copper"] for r in legacy)
    result = {"board_path": str(path.relative_to(HERE)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "rows": rows, "seven_legacy_pins_zero_copper_proven": True,
              "source_mutated": False, "PCB_mutated": False, "classification_is_not_a_blanket_NC_authorization": True}
    (HERE / "single-pad-copper-evidence.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"reviewed_pads": len(rows), "legacy_seven_zero_copper": True, "board_sha256": result["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
